from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.google_oauth import GoogleAccountInfo, GoogleOAuthService, GoogleTokenResponse
from app.integrations.google_workspace.enums import GoogleWorkspaceHealthStatus, GoogleWorkspaceServiceKey
from app.integrations.google_workspace.scopes import DRIVE_SCOPES, services_to_scopes
from app.integrations.google_workspace.service import GoogleWorkspaceService
from app.main import app
from app.models.audit_log import AuditLog
from app.models.integration import GoogleWorkspaceSettings, Integration, IntegrationCredential, IntegrationOAuthState
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService


class FakeGoogleOAuthClient:
    def __init__(self, *, scopes: list[str] | None = None, refresh_token: str | None = "refresh-token-not-real") -> None:
        self.scopes = scopes or ["https://www.googleapis.com/auth/calendar.events"]
        self.refresh_token = refresh_token
        self.authorization_scopes: list[str] = []
        self.incremental = False

    def build_authorization_url(
        self,
        *,
        state: str,
        settings,
        scopes: list[str] | None = None,
        incremental: bool = False,
        prompt_consent: bool = True,
    ) -> str:
        del prompt_consent
        self.authorization_scopes = scopes or settings.google_oauth_scopes
        self.incremental = incremental
        return f"https://accounts.google.test/oauth?state={state}&scope={' '.join(self.authorization_scopes)}"

    def exchange_code(self, *, code: str, settings) -> GoogleTokenResponse:
        del code, settings
        return GoogleTokenResponse(
            access_token="access-token-not-real",
            refresh_token=self.refresh_token,
            token_type="Bearer",
            expires_in=3600,
            scopes=self.scopes,
        )

    def refresh_access_token(self, *, refresh_token: str, settings) -> GoogleTokenResponse:
        del settings
        return GoogleTokenResponse("new-access-token-not-real", refresh_token, "Bearer", 3600, self.scopes)

    def revoke_token(self, *, token: str, settings) -> None:
        del token, settings

    def fetch_account_info(self, *, access_token: str) -> GoogleAccountInfo:
        del access_token
        return GoogleAccountInfo(account_id="workspace-account-123", email="workspace-admin@example.test")


class FakeDriveClient:
    def __init__(self) -> None:
        self.calls = 0

    def health_check(self, *, access_token: str) -> dict:
        assert access_token == "access-token-not-real"
        self.calls += 1
        return {"status": "healthy", "email": "workspace-admin@example.test"}


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 16.1%"))))
        if integration_ids:
            db.execute(delete(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        users = list(db.scalars(select(User).where(User.email.like("test-16-1-%@realmeet.local"))))
        user_ids = [item.id for item in users]
        if user_ids:
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def oauth_settings():
    return settings.model_copy(
        update={
            "google_oauth_client_id": "fake-client-id.apps.googleusercontent.com",
            "google_oauth_client_secret": "fake-client-secret",
            "google_oauth_redirect_uri": "http://localhost:18000/api/v1/admin/integrations/oauth/google/callback",
            "google_oauth_scopes": ["https://www.googleapis.com/auth/calendar.events"],
            "google_oauth_state_ttl_seconds": 600,
            "google_token_encryption_key": Fernet.generate_key().decode(),
        }
    )


def _create_user(db, role: UserRole) -> User:
    user = User(
        email=f"test-16-1-{role.value}-{datetime.now(UTC).timestamp()}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=role.value.title(),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _create_integration(db, admin: User, *, provider: IntegrationProvider = IntegrationProvider.google_meet) -> Integration:
    integration = IntegrationService(db).create_integration(
        IntegrationCreate(
            name=f"Test 16.1 {provider.value}",
            integration_type=IntegrationType.meeting,
            provider=provider,
            config={},
            secret_reference=None,
        ),
        admin,
    )
    db.refresh(integration)
    return integration


def _state_from_url(url: str) -> str:
    return parse_qs(urlparse(url).query)["state"][0]


def _add_credential(db, integration: Integration, oauth_settings, scopes: list[str]) -> IntegrationCredential:
    cipher = TokenCipher(oauth_settings.google_token_encryption_key)
    credential = IntegrationCredential(
        integration_id=integration.id,
        credential_type="google_oauth",
        encrypted_access_token=cipher.encrypt("access-token-not-real"),
        encrypted_refresh_token=cipher.encrypt("refresh-token-not-real"),
        token_type="Bearer",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        scopes=scopes,
        external_account_email="workspace-admin@example.test",
        external_account_id="workspace-account-123",
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


def test_workspace_catalog_uses_incremental_and_minimal_scopes() -> None:
    scopes = services_to_scopes([GoogleWorkspaceServiceKey.drive, GoogleWorkspaceServiceKey.docs])

    assert "https://www.googleapis.com/auth/drive.file" in scopes
    assert "https://www.googleapis.com/auth/drive" not in scopes
    assert "https://www.googleapis.com/auth/documents" in scopes
    assert scopes.count("openid") == 1
    assert DRIVE_SCOPES == ["https://www.googleapis.com/auth/drive.file"]


def test_workspace_admin_endpoints_are_role_protected(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    client = _create_user(db_session, UserRole.client)
    professional = _create_user(db_session, UserRole.professional)
    integration = _create_integration(db_session, admin)

    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace"

    assert api_client.get(path).status_code == 401
    assert api_client.get(path, headers=_headers(client)).status_code == 403
    assert api_client.get(path, headers=_headers(professional)).status_code == 403
    response = api_client.get(path, headers=_headers(admin))
    assert response.status_code == 200
    assert "encrypted_access_token" not in response.text
    assert "refresh-token" not in response.text


def test_incremental_oauth_tracks_requested_services_and_dedupes_scopes(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    _add_credential(db_session, integration, oauth_settings, ["https://www.googleapis.com/auth/calendar.events"])
    fake = FakeGoogleOAuthClient()
    service = GoogleWorkspaceService(
        db_session,
        oauth_service=GoogleOAuthService(db_session, oauth_client=fake, app_settings=oauth_settings),
    )

    url, expires_at, scopes = service.start_oauth(integration.id, admin, [GoogleWorkspaceServiceKey.calendar, GoogleWorkspaceServiceKey.drive])
    state_row = db_session.scalar(select(IntegrationOAuthState).where(IntegrationOAuthState.integration_id == integration.id))

    assert expires_at > datetime.now(UTC)
    assert "state=" in url
    assert fake.incremental is True
    assert fake.authorization_scopes.count("https://www.googleapis.com/auth/calendar.events") == 1
    assert "https://www.googleapis.com/auth/drive.file" in fake.authorization_scopes
    assert scopes.count("https://www.googleapis.com/auth/calendar.events") == 1
    assert state_row is not None
    assert state_row.requested_services == ["calendar", "drive"]


def test_callback_preserves_refresh_token_and_syncs_authorized_services(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    existing = _add_credential(db_session, integration, oauth_settings, ["https://www.googleapis.com/auth/calendar.events"])
    old_refresh = existing.encrypted_refresh_token
    fake = FakeGoogleOAuthClient(
        scopes=[
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/drive.file",
        ],
        refresh_token=None,
    )
    oauth = GoogleOAuthService(db_session, oauth_client=fake, app_settings=oauth_settings)
    url, _ = oauth.incremental_authorization_url(
        integration.id,
        admin,
        services=["drive"],
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )

    credential = oauth.callback(code="valid-code", state=_state_from_url(url))
    workspace = db_session.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == integration.id))

    assert credential.encrypted_refresh_token == old_refresh
    assert credential.external_account_email == "workspace-admin@example.test"
    assert workspace is not None
    assert workspace.calendar_authorized is True
    assert workspace.meet_authorized is True
    assert workspace.drive_authorized is True
    assert workspace.sheets_authorized is False


def test_service_status_distinguishes_enabled_authorized_and_disabled(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    _add_credential(db_session, integration, oauth_settings, ["https://www.googleapis.com/auth/calendar.events"])
    service = GoogleWorkspaceService(db_session)

    status_data = service.status(integration.id)
    by_service = {item.service: item for item in status_data.services}

    assert by_service[GoogleWorkspaceServiceKey.calendar].status == GoogleWorkspaceHealthStatus.healthy
    assert by_service[GoogleWorkspaceServiceKey.meet].authorized is True
    assert by_service[GoogleWorkspaceServiceKey.drive].status == GoogleWorkspaceHealthStatus.disabled
    assert by_service[GoogleWorkspaceServiceKey.sheets].enabled is False


def test_drive_health_uses_existing_token_and_never_exposes_secret(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    _add_credential(
        db_session,
        integration,
        oauth_settings,
        ["https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/drive.file"],
    )
    service = GoogleWorkspaceService(
        db_session,
        oauth_service=GoogleOAuthService(db_session, oauth_client=FakeGoogleOAuthClient(), app_settings=oauth_settings),
        drive_client=FakeDriveClient(),
    )

    service.set_service_enabled(integration.id, GoogleWorkspaceServiceKey.drive, True)
    result = service.health(integration.id, GoogleWorkspaceServiceKey.drive)
    drive = next(item for item in result.services if item.service == GoogleWorkspaceServiceKey.drive)

    assert drive.status == GoogleWorkspaceHealthStatus.healthy
    assert "access-token-not-real" not in result.model_dump_json()
    assert "refresh-token-not-real" not in result.model_dump_json()


def test_non_google_integration_rejected_for_workspace(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin, provider=IntegrationProvider.mock)

    response = api_client.get(f"/api/v1/admin/integrations/{integration.id}/google/workspace", headers=_headers(admin))

    assert response.status_code == 409
    assert "Google Workspace" in response.text
