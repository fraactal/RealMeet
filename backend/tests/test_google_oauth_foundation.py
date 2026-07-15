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
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationError
from app.integrations.google_oauth import GoogleAccountInfo, GoogleOAuthService, GoogleTokenResponse
from app.main import app
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationCredential, IntegrationOAuthState
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService


class FakeGoogleOAuthClient:
    def __init__(self, *, revoke_fails: bool = False, refresh_token: str | None = "refresh-token-not-real") -> None:
        self.revoke_fails = revoke_fails
        self.refresh_token = refresh_token
        self.exchange_calls = 0
        self.refresh_calls = 0
        self.revoke_calls = 0

    def build_authorization_url(self, *, state: str, settings) -> str:
        return f"https://accounts.google.test/oauth?state={state}&redirect_uri={settings.google_oauth_redirect_uri}"

    def exchange_code(self, *, code: str, settings) -> GoogleTokenResponse:
        self.exchange_calls += 1
        if code == "bad-code":
            raise IntegrationError("No pudimos intercambiar el codigo OAuth", code="google_oauth_exchange_failed")
        return GoogleTokenResponse(
            access_token="access-token-not-real",
            refresh_token=self.refresh_token,
            token_type="Bearer",
            expires_in=3600,
            scopes=settings.google_oauth_scopes,
        )

    def refresh_access_token(self, *, refresh_token: str, settings) -> GoogleTokenResponse:
        self.refresh_calls += 1
        return GoogleTokenResponse(
            access_token="new-access-token-not-real",
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=7200,
            scopes=settings.google_oauth_scopes,
        )

    def revoke_token(self, *, token: str, settings) -> None:
        self.revoke_calls += 1
        if self.revoke_fails:
            raise IntegrationError("remote revoke failed", code="google_oauth_revoke_failed")

    def fetch_account_info(self, *, access_token: str) -> GoogleAccountInfo:
        return GoogleAccountInfo(account_id="google-account-123", email="admin-google@example.test")


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 12.1%"))))
        if integration_ids:
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        users = list(db.scalars(select(User).where(User.email.like("test-12-1-%@realmeet.local"))))
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
        email=f"test-12-1-{role.value}@realmeet.local",
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
            name=f"Test 12.1 {provider.value}",
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


def test_backend_starts_without_google_settings_and_authorize_errors_controlled(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)

    response = api_client.post(f"/api/v1/admin/integrations/{integration.id}/oauth/google/authorize", headers=_headers(admin))

    assert response.status_code == 422
    assert "Google OAuth no esta configurado" in response.text


def test_authorization_url_uses_minimal_scopes_and_configured_redirect(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)

    url, expires_at = GoogleOAuthService(db_session, app_settings=oauth_settings).authorization_url(integration.id, admin)
    query = parse_qs(urlparse(url).query)

    assert query["scope"] == ["https://www.googleapis.com/auth/calendar.events"]
    assert query["redirect_uri"] == [oauth_settings.google_oauth_redirect_uri]
    assert query["access_type"] == ["offline"]
    assert expires_at > datetime.now(UTC)


def test_state_valid_tampered_expired_and_reused(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    fake = FakeGoogleOAuthClient()
    service = GoogleOAuthService(db_session, oauth_client=fake, app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)
    state = _state_from_url(url)

    credential = service.callback(code="valid-code", state=state)
    assert credential.external_account_email == "admin-google@example.test"

    with pytest.raises(IntegrationError):
        service.callback(code="valid-code", state=state)
    with pytest.raises(IntegrationError):
        service.callback(code="valid-code", state=f"{state}tampered")

    expired_service = GoogleOAuthService(
        db_session,
        oauth_client=fake,
        app_settings=oauth_settings,
        now=datetime.now(UTC) - timedelta(hours=2),
    )
    expired_url, _ = expired_service.authorization_url(integration.id, admin)
    with pytest.raises(IntegrationError):
        GoogleOAuthService(db_session, oauth_client=fake, app_settings=oauth_settings).callback(code="valid-code", state=_state_from_url(expired_url))


def test_tokens_are_encrypted_and_api_status_never_returns_tokens(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    service = GoogleOAuthService(db_session, oauth_client=FakeGoogleOAuthClient(), app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)
    credential = service.callback(code="valid-code", state=_state_from_url(url))

    assert credential.encrypted_access_token is not None
    assert "access-token-not-real" not in credential.encrypted_access_token
    assert TokenCipher(oauth_settings.google_token_encryption_key).decrypt(credential.encrypted_access_token) == "access-token-not-real"
    status_data = service.status(integration.id)
    assert "token" not in str(status_data).lower()


def test_missing_encryption_key_errors_controlled() -> None:
    with pytest.raises(IntegrationConfigurationError):
        TokenCipher(None)


def test_callback_failure_does_not_store_credential(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    service = GoogleOAuthService(db_session, oauth_client=FakeGoogleOAuthClient(), app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)

    with pytest.raises(IntegrationError):
        service.callback(code="bad-code", state=_state_from_url(url))

    assert db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id)) is None


def test_refresh_and_disconnect_clear_tokens_even_when_remote_revoke_fails(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    fake = FakeGoogleOAuthClient(revoke_fails=True)
    service = GoogleOAuthService(db_session, oauth_client=fake, app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)
    credential = service.callback(code="valid-code", state=_state_from_url(url))

    refreshed = service.refresh(integration.id, admin)
    assert refreshed.last_refresh_at is not None
    assert fake.refresh_calls == 1

    service.disconnect(integration.id, admin)
    db_session.refresh(credential)
    assert credential.revoked_at is not None
    assert credential.encrypted_access_token is None
    assert credential.encrypted_refresh_token is None
    assert fake.revoke_calls == 1


def test_refresh_without_refresh_token_fails_safely(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)
    service = GoogleOAuthService(db_session, oauth_client=FakeGoogleOAuthClient(refresh_token=None), app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)
    service.callback(code="valid-code", state=_state_from_url(url))

    with pytest.raises(IntegrationError):
        service.refresh(integration.id, admin)


def test_admin_oauth_endpoints_authorization_and_provider_checks(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    client = _create_user(db_session, UserRole.client)
    professional = _create_user(db_session, UserRole.professional)
    google = _create_integration(db_session, admin)
    mock = _create_integration(db_session, admin, provider=IntegrationProvider.mock)

    assert api_client.get(f"/api/v1/admin/integrations/{google.id}/oauth/status").status_code == 401
    assert api_client.get(f"/api/v1/admin/integrations/{google.id}/oauth/status", headers=_headers(client)).status_code == 403
    assert api_client.get(f"/api/v1/admin/integrations/{google.id}/oauth/status", headers=_headers(professional)).status_code == 403
    assert api_client.get(f"/api/v1/admin/integrations/{google.id}/oauth/status", headers=_headers(admin)).status_code == 200
    assert api_client.post(f"/api/v1/admin/integrations/{mock.id}/oauth/google/authorize", headers=_headers(admin)).status_code == 409


def test_google_meet_cannot_be_enabled_as_operational_provider(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin)
    integration = _create_integration(db_session, admin)

    response = api_client.post(f"/api/v1/admin/integrations/{integration.id}/enable", headers=_headers(admin))

    assert response.status_code == 409
