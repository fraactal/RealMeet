from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.integrations.exceptions import IntegrationProviderExecutionError
from app.integrations.google_oauth import GoogleOAuthService
from app.integrations.google_workspace.enums import GoogleWorkspaceServiceKey
from app.integrations.google_workspace.sheets_exports import (
    GoogleSheetsAppointmentExportService,
    GoogleSheetsExportConfig,
    GoogleSheetsExportConfigCreate,
    GoogleSheetsExportExecution,
    GoogleSheetsExportMode,
    GoogleSheetsExportRunRequest,
    SHEETS_EXPORT_COLUMNS,
)
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import GoogleWorkspaceSettings, Integration, IntegrationCredential, IntegrationOAuthState
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate
from app.services.integrations import IntegrationService


class FakeSheetsClient:
    def __init__(self, *, missing_sheet: bool = False, headers: list[str] | None = None, fail_append: bool = False) -> None:
        self.missing_sheet = missing_sheet
        self.fail_append = fail_append
        self.rows: list[list[str]] = [headers] if headers is not None else []
        self.metadata_calls = 0

    def health_check(self, *, access_token: str) -> dict:
        del access_token
        return {"status": "authorized_not_resource_tested"}

    def get_spreadsheet_metadata(self, *, access_token: str, spreadsheet_id: str) -> dict:
        del access_token, spreadsheet_id
        self.metadata_calls += 1
        sheets = [] if self.missing_sheet else [{"title": "Reservas"}]
        return {"title": "RealMeet Reservas", "sheets": sheets}

    def get_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        del access_token, spreadsheet_id
        if "A1:N1" in range_name:
            return [self.rows[0]] if self.rows else []
        return [row[:] for row in self.rows]

    def update_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> None:
        del access_token, spreadsheet_id, range_name
        if self.rows:
            self.rows[0] = values[0]
        else:
            self.rows.append(values[0])

    def append_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> None:
        del access_token, spreadsheet_id, range_name
        if self.fail_append:
            raise IntegrationProviderExecutionError("Google Sheets no esta disponible", code="google_sheets_unavailable")
        if not self.rows:
            self.rows.append(SHEETS_EXPORT_COLUMNS)
        self.rows.extend([row[:] for row in values])

    def batch_update_values(self, *, access_token: str, spreadsheet_id: str, data: list[dict[str, object]]) -> None:
        del access_token, spreadsheet_id
        for item in data:
            range_name = str(item["range"])
            row_number = int(range_name.split("!A", 1)[1].split(":", 1)[0])
            self.rows[row_number - 1] = list(item["values"][0])  # type: ignore[index]


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 16.2%"))))
        config_ids = list(db.scalars(select(GoogleSheetsExportConfig.id).where(GoogleSheetsExportConfig.integration_id.in_(integration_ids)))) if integration_ids else []
        if config_ids:
            db.execute(delete(GoogleSheetsExportExecution).where(GoogleSheetsExportExecution.config_id.in_(config_ids)))
            db.execute(delete(GoogleSheetsExportConfig).where(GoogleSheetsExportConfig.id.in_(config_ids)))
        if integration_ids:
            db.execute(delete(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(integration_ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in integration_ids])))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        appointments = list(db.scalars(select(Appointment).where(Appointment.client_notes == "Test 16.2 clinical note")))
        if appointments:
            db.execute(delete(Appointment).where(Appointment.id.in_([item.id for item in appointments])))
        users = list(db.scalars(select(User).where(User.email.like("test-16-2-%@realmeet.local"))))
        profile_user_ids = [item.id for item in users]
        if profile_user_ids:
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.user_id.in_(profile_user_ids)))
            db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(profile_user_ids)))
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(profile_user_ids)))
            db.execute(delete(User).where(User.id.in_(profile_user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def oauth_settings():
    return settings.model_copy(update={"google_token_encryption_key": Fernet.generate_key().decode()})


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-16-2-{role.value}-{suffix}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name=role.value.title(),
        last_name=suffix,
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
            name=f"Test 16.2 {provider.value}",
            integration_type=IntegrationType.meeting,
            provider=provider,
            config={},
            secret_reference=None,
        ),
        admin,
    )
    db.refresh(integration)
    return integration


def _authorize_sheets(db, integration: Integration, oauth_settings, *, enabled: bool = True, scopes: list[str] | None = None) -> None:
    db.add(GoogleWorkspaceSettings(integration_id=integration.id, sheets_enabled=enabled, sheets_authorized=bool(scopes)))
    cipher = TokenCipher(oauth_settings.google_token_encryption_key)
    db.add(
        IntegrationCredential(
            integration_id=integration.id,
            credential_type="google_oauth",
            encrypted_access_token=cipher.encrypt("access-token-not-real"),
            encrypted_refresh_token=cipher.encrypt("refresh-token-not-real"),
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=scopes or [],
            external_account_email="sheets-admin@example.test",
        )
    )
    db.commit()


def _service(db, oauth_settings, fake: FakeSheetsClient) -> GoogleSheetsAppointmentExportService:
    return GoogleSheetsAppointmentExportService(db, oauth_service=GoogleOAuthService(db, app_settings=oauth_settings), sheets_client=fake)


def _payload(**overrides) -> GoogleSheetsExportConfigCreate:
    data = {
        "name": "Reservas Google Sheets",
        "spreadsheet_id": "spreadsheet_1234567890",
        "sheet_name": "Reservas",
        "export_mode": GoogleSheetsExportMode.upsert,
        "include_cancelled": False,
    }
    data.update(overrides)
    return GoogleSheetsExportConfigCreate(**data)


def _create_config(db, integration: Integration) -> GoogleSheetsExportConfig:
    item = GoogleSheetsExportConfig(integration_id=integration.id, **_payload().model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _create_profiles_and_appointments(db) -> tuple[Appointment, Appointment]:
    professional_user = _create_user(db, UserRole.professional, "export-prof")
    client_user = _create_user(db, UserRole.client, "export-client")
    professional = ProfessionalProfile(user_id=professional_user.id, consultation_mode=ConsultationMode.online, session_duration_minutes=45)
    client = ClientProfile(user_id=client_user.id)
    db.add_all([professional, client])
    db.commit()
    db.refresh(professional)
    db.refresh(client)
    start = datetime(2026, 7, 20, 14, 0, tzinfo=UTC)
    active = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        start_datetime=start,
        end_datetime=start + timedelta(minutes=45),
        status=AppointmentStatus.confirmed,
        consultation_mode=ConsultationMode.online,
        meeting_provider=MeetingProvider.google_meet,
        meeting_url="https://meet.google.com/test-safe",
        client_notes="Test 16.2 clinical note",
        professional_private_notes="diagnostico privado",
    )
    cancelled = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        start_datetime=start + timedelta(days=1),
        end_datetime=start + timedelta(days=1, minutes=45),
        status=AppointmentStatus.cancelled,
        consultation_mode=ConsultationMode.online,
        meeting_provider=MeetingProvider.google_meet,
        meeting_url="https://meet.google.com/cancelled-safe",
        client_notes="Test 16.2 clinical note",
    )
    db.add_all([active, cancelled])
    db.commit()
    db.refresh(active)
    db.refresh(cancelled)
    return active, cancelled


def test_admin_can_create_valid_config_and_roles_are_protected(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin")
    professional = _create_user(db_session, UserRole.professional, "professional")
    client = _create_user(db_session, UserRole.client, "client")
    integration = _create_integration(db_session, admin)
    _authorize_sheets(db_session, integration, oauth_settings, enabled=True, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace/sheets/exports"

    response = api_client.post(path, headers=_headers(admin), json=_payload().model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["spreadsheet_id"] == "spreadsheet_1234567890"
    assert api_client.get(path, headers=_headers(professional)).status_code == 403
    assert api_client.get(path, headers=_headers(client)).status_code == 403


def test_invalid_provider_disabled_scope_invalid_id_and_duplicate_rejected(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "checks")
    mock = _create_integration(db_session, admin, provider=IntegrationProvider.mock)
    google = _create_integration(db_session, admin)
    fake = FakeSheetsClient()

    with pytest.raises(Exception, match="spreadsheet_id"):
        _payload(spreadsheet_id="https://example.com/not-google")
    with pytest.raises(Exception, match="integracion Google"):
        _service(db_session, oauth_settings, fake).create_config(mock.id, _payload())
    _authorize_sheets(db_session, google, oauth_settings, enabled=False, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    with pytest.raises(Exception, match="deshabilitado"):
        _service(db_session, oauth_settings, fake).create_config(google.id, _payload())

    db_session.scalar(select(GoogleWorkspaceSettings).where(GoogleWorkspaceSettings.integration_id == google.id)).sheets_enabled = True
    credential = db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.integration_id == google.id))
    credential.scopes = []
    db_session.commit()
    with pytest.raises(Exception, match="autorizacion"):
        _service(db_session, oauth_settings, fake).create_config(google.id, _payload())

    credential.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    db_session.commit()
    _service(db_session, oauth_settings, fake).create_config(google.id, _payload())
    with pytest.raises(Exception, match="Ya existe"):
        _service(db_session, oauth_settings, fake).create_config(google.id, _payload())


def test_validate_sheet_headers_empty_missing_and_incompatible(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "validate")
    integration = _create_integration(db_session, admin)
    _authorize_sheets(db_session, integration, oauth_settings, enabled=True, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    config = _create_config(db_session, integration)
    fake = FakeSheetsClient()

    result = _service(db_session, oauth_settings, fake).validate_config(integration.id, config.id)

    assert result.valid is True
    assert result.spreadsheet["title"] == "RealMeet Reservas"
    assert result.headers["status"] == "created"
    assert fake.rows[0] == SHEETS_EXPORT_COLUMNS
    with pytest.raises(Exception, match="pestana"):
        _service(db_session, oauth_settings, FakeSheetsClient(missing_sheet=True)).validate_config(integration.id, config.id)
    with pytest.raises(Exception, match="encabezados incompatibles"):
        _service(db_session, oauth_settings, FakeSheetsClient(headers=["otro_id", "status"])).validate_config(integration.id, config.id)


def test_export_upsert_append_privacy_counts_and_retry(db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "run")
    integration = _create_integration(db_session, admin)
    _authorize_sheets(db_session, integration, oauth_settings, enabled=True, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    active, cancelled = _create_profiles_and_appointments(db_session)
    config = _create_config(db_session, integration)
    fake = FakeSheetsClient(headers=SHEETS_EXPORT_COLUMNS)
    service = _service(db_session, oauth_settings, fake)
    payload = GoogleSheetsExportRunRequest(
        starts_from=active.start_datetime - timedelta(hours=1),
        starts_to=cancelled.start_datetime + timedelta(hours=1),
        include_cancelled=False,
    )

    first = service.run_export(integration.id, config.id, payload, admin)
    second = service.run_export(integration.id, config.id, payload, admin)
    config.export_mode = GoogleSheetsExportMode.append_only
    db_session.commit()
    third = service.run_export(integration.id, config.id, payload, admin)

    assert first.inserted_records == 1
    assert first.updated_records == 0
    assert second.inserted_records == 0
    assert second.updated_records == 1
    assert third.skipped_records == 1
    assert len(fake.rows) == 2
    exported = " ".join(fake.rows[1])
    assert str(active.id) in exported
    assert str(cancelled.id) not in exported
    assert "clinical note" not in exported
    assert "diagnostico" not in exported
    assert "access-token" not in first.__dict__.__str__()

    failing_service = _service(db_session, oauth_settings, FakeSheetsClient(headers=SHEETS_EXPORT_COLUMNS, fail_append=True))
    config.export_mode = GoogleSheetsExportMode.upsert
    config.sheet_name = "Reservas"
    db_session.commit()
    failed = failing_service.run_export(integration.id, config.id, payload, admin)
    retried = service.retry_execution(integration.id, config.id, failed.id, admin)

    assert failed.status == "failed"
    assert failed.error_code == "google_sheets_unavailable"
    assert retried.id != failed.id
    assert len(fake.rows) == 2


def test_range_validation_and_tokens_not_returned(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _create_user(db_session, UserRole.admin, "range")
    integration = _create_integration(db_session, admin)
    _authorize_sheets(db_session, integration, oauth_settings, enabled=True, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    config = _create_config(db_session, integration)
    path = f"/api/v1/admin/integrations/{integration.id}/google/workspace/sheets/exports/{config.id}/run"

    response = api_client.post(
        path,
        headers=_headers(admin),
        json={
            "starts_from": "2026-07-31T00:00:00Z",
            "starts_to": "2026-07-01T00:00:00Z",
            "include_cancelled": True,
        },
    )

    assert response.status_code == 422
    assert "access-token" not in response.text
    assert "refresh-token" not in response.text
