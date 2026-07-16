from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.calendars.conflicts import CalendarConflictService
from app.calendars.registry import ExternalCalendarProviderRegistry
from app.calendars.service import ExternalCalendarService
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.main import app
from app.models.external_calendar import CalendarSyncSettings, ExternalCalendar, ExternalCalendarProvider
from app.models.integration import Integration, IntegrationCredential
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole


class FakeGoogleCalendarClient:
    def __init__(self, *, busy: list[dict] | None = None, fail_calendar_id: str | None = None) -> None:
        self.busy = busy or []
        self.fail_calendar_id = fail_calendar_id
        self.freebusy_calls = 0

    def list_calendars(self, *, access_token: str) -> list[dict]:
        assert access_token == "access-token-not-real"
        return [
            {"id": "primary", "summary": "Primary", "timeZone": "America/Santiago", "primary": True, "accessRole": "owner"},
            {"id": "team", "summary": "Team", "description": "Equipo", "timeZone": "America/Santiago", "accessRole": "reader"},
        ]

    def freebusy(self, *, access_token: str, calendar_ids: list[str], time_min: datetime, time_max: datetime, timezone: str) -> dict:
        self.freebusy_calls += 1
        calendars = {}
        for calendar_id in calendar_ids:
            if calendar_id == self.fail_calendar_id:
                calendars[calendar_id] = {"errors": [{"reason": "backendError"}], "busy": []}
            else:
                calendars[calendar_id] = {"busy": self.busy}
        return {"calendars": calendars}

    def create_event(self, **kwargs):
        raise AssertionError("not used")

    def get_event(self, **kwargs):
        raise AssertionError("not used")

    def delete_event(self, **kwargs):
        raise AssertionError("not used")

    def get_calendar(self, **kwargs):
        raise AssertionError("not used")


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch) -> Iterator:
    object.__setattr__(settings, "google_token_encryption_key", Fernet.generate_key().decode())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.title.like("Test 15.2%"))))
        if professional_ids:
            db.execute(delete(CalendarSyncSettings).where(CalendarSyncSettings.professional_id.in_(professional_ids)))
            db.execute(delete(ExternalCalendar).where(ExternalCalendar.professional_id.in_(professional_ids)))
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
        integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 15.2%"))))
        if integration_ids:
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
            db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
        db.execute(delete(User).where(User.email.like("test-15-2-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-15-2-{suffix}-{role.value}@realmeet.local",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name=role.value,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _professional(db, suffix: str) -> tuple[User, ProfessionalProfile]:
    user = _user(db, UserRole.professional, suffix)
    profile = ProfessionalProfile(user_id=user.id, title=f"Test 15.2 {suffix}", consultation_mode=ConsultationMode.online, session_duration_minutes=60, is_public=True)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _google_integration(db) -> Integration:
    integration = Integration(
        name="Test 15.2 Google",
        integration_type=IntegrationType.meeting,
        provider=IntegrationProvider.google_meet,
        enabled=True,
        status=IntegrationStatus.configured,
        config={"calendar_id": "primary"},
    )
    db.add(integration)
    db.flush()
    cipher = TokenCipher(settings.google_token_encryption_key)
    db.add(
        IntegrationCredential(
            integration_id=integration.id,
            credential_type="google_oauth",
            encrypted_access_token=cipher.encrypt("access-token-not-real"),
            encrypted_refresh_token=cipher.encrypt("refresh-token-not-real"),
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=["https://www.googleapis.com/auth/calendar.events"],
        )
    )
    db.commit()
    db.refresh(integration)
    return integration


def _service(db, client: FakeGoogleCalendarClient) -> ExternalCalendarService:
    return ExternalCalendarService(db, ExternalCalendarProviderRegistry(db, google_calendar_client=client))


def _calendar_payload(integration_id: int, external_id: str = "primary") -> dict:
    return {
        "provider": "google_calendar",
        "integration_id": integration_id,
        "external_calendar_id": external_id,
        "name": "Google primary",
        "timezone": "America/Santiago",
        "read_enabled": True,
        "write_enabled": False,
        "conflict_check_enabled": True,
        "is_primary": True,
    }


def test_google_provider_lists_calendars_and_does_not_expose_tokens(db_session) -> None:
    integration = _google_integration(db_session)
    provider = ExternalCalendarProviderRegistry(db_session, google_calendar_client=FakeGoogleCalendarClient()).resolve(ExternalCalendarProvider.google_calendar, integration_id=integration.id)

    calendars = provider.list_calendars()

    assert calendars[0].external_calendar_id == "primary"
    assert "token" not in repr(calendars).lower()


def test_freebusy_maps_to_busy_period(db_session) -> None:
    integration = _google_integration(db_session)
    start = datetime(2026, 7, 20, 15, 0, tzinfo=UTC)
    client = FakeGoogleCalendarClient(busy=[{"start": start.isoformat(), "end": (start + timedelta(hours=1)).isoformat()}])
    provider = ExternalCalendarProviderRegistry(db_session, google_calendar_client=client).resolve(ExternalCalendarProvider.google_calendar, integration_id=integration.id)

    periods = provider.list_busy_periods("primary", start, start + timedelta(hours=2))

    assert periods[0].source_calendar_id == "primary"
    assert periods[0].availability == "busy"


def test_register_valid_google_calendar_and_reject_invalid_or_duplicate(db_session) -> None:
    _, profile = _professional(db_session, "register")
    integration = _google_integration(db_session)
    service = _service(db_session, FakeGoogleCalendarClient())

    created = service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id)))

    assert created.external_calendar_id == "primary"
    with pytest.raises(Exception):
        service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id, "missing")))
    with pytest.raises(Exception):
        service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id)))


def test_conflict_overlap_cases_and_adjacency(db_session) -> None:
    _, profile = _professional(db_session, "conflicts")
    integration = _google_integration(db_session)
    busy_start = datetime(2026, 7, 20, 15, 30, tzinfo=UTC)
    client = FakeGoogleCalendarClient(busy=[{"start": busy_start.isoformat(), "end": (busy_start + timedelta(hours=1)).isoformat()}])
    service = _service(db_session, client)
    service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id)))
    service.update_settings(profile.id, _settings({"sync_enabled": True, "conflict_policy": "external_busy_blocks"}))
    conflict_service = CalendarConflictService(db_session, service)

    partial = conflict_service.check(profile.id, starts_at=datetime(2026, 7, 20, 15, 0, tzinfo=UTC), ends_at=datetime(2026, 7, 20, 16, 0, tzinfo=UTC))
    contains_event = conflict_service.check(profile.id, starts_at=datetime(2026, 7, 20, 15, 0, tzinfo=UTC), ends_at=datetime(2026, 7, 20, 17, 0, tzinfo=UTC))
    event_contains = conflict_service.check(profile.id, starts_at=datetime(2026, 7, 20, 15, 45, tzinfo=UTC), ends_at=datetime(2026, 7, 20, 16, 0, tzinfo=UTC))
    adjacent = conflict_service.check(profile.id, starts_at=datetime(2026, 7, 20, 16, 30, tzinfo=UTC), ends_at=datetime(2026, 7, 20, 17, 0, tzinfo=UTC))

    assert partial.has_conflict is True
    assert contains_event.has_conflict is True
    assert event_contains.has_conflict is True
    assert adjacent.has_conflict is False


def test_no_conflict_when_no_busy_periods_and_policies_skip_google(db_session) -> None:
    _, profile = _professional(db_session, "policies")
    integration = _google_integration(db_session)
    client = FakeGoogleCalendarClient()
    service = _service(db_session, client)
    service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id)))
    conflict_service = CalendarConflictService(db_session, service)
    start = datetime(2026, 7, 20, 15, 0, tzinfo=UTC)

    service.update_settings(profile.id, _settings({"sync_enabled": True, "conflict_policy": "external_busy_blocks"}))
    no_busy = conflict_service.check(profile.id, starts_at=start, ends_at=start + timedelta(hours=1))
    service.update_settings(profile.id, _settings({"conflict_policy": "internal_only"}))
    internal = conflict_service.check(profile.id, starts_at=start, ends_at=start + timedelta(hours=1))
    service.update_settings(profile.id, _settings({"conflict_policy": "disabled"}))
    disabled = conflict_service.check(profile.id, starts_at=start, ends_at=start + timedelta(hours=1))

    assert no_busy.has_conflict is False
    assert internal.status == "external_check_skipped"
    assert disabled.status == "external_check_skipped"


def test_external_busy_blocks_consults_provider_and_partial_failure_is_summarized(db_session) -> None:
    _, profile = _professional(db_session, "partial")
    integration = _google_integration(db_session)
    client = FakeGoogleCalendarClient(fail_calendar_id="primary")
    service = _service(db_session, client)
    service.create_calendar(profile.id, _schema_create(_calendar_payload(integration.id)))
    service.update_settings(profile.id, _settings({"sync_enabled": True, "conflict_policy": "external_busy_blocks"}))
    start = datetime(2026, 7, 20, 15, 0, tzinfo=UTC)

    result = CalendarConflictService(db_session, service).check(profile.id, starts_at=start, ends_at=start + timedelta(hours=1))

    assert client.freebusy_calls == 1
    assert result.status == "unavailable"
    assert result.errors


def test_client_forbidden_professional_isolated_admin_allowed_and_google_not_connected(api_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    client_user = _user(db_session, UserRole.client, "client")
    professional_user, profile = _professional(db_session, "api")
    other_user, other_profile = _professional(db_session, "other")
    admin = _user(db_session, UserRole.admin, "admin")
    start = datetime(2026, 7, 20, 15, 0, tzinfo=UTC).isoformat()
    payload = {"starts_at": start, "ends_at": datetime(2026, 7, 20, 16, 0, tzinfo=UTC).isoformat()}

    assert api_client.post("/api/v1/professionals/me/external-calendars/conflicts/check", headers=_headers(client_user), json=payload).status_code == 403
    assert api_client.get(f"/api/v1/admin/professionals/{profile.id}/external-calendars/providers/google/available", headers=_headers(admin)).status_code == 400

    integration = _google_integration(db_session)

    def fake_list(self, provider, *, integration_id=None):
        return [{"external_calendar_id": "primary", "name": "Primary", "description": None, "timezone": "America/Santiago", "is_primary": True, "read_only": False}]

    monkeypatch.setattr(ExternalCalendarService, "list_available_calendars", fake_list)
    created = api_client.post("/api/v1/professionals/me/external-calendars", headers=_headers(professional_user), json=_calendar_payload(integration.id))
    assert created.status_code == 200
    assert api_client.get(f"/api/v1/professionals/me/external-calendars/{created.json()['id']}", headers=_headers(other_user)).status_code == 404
    assert api_client.post(f"/api/v1/admin/professionals/{profile.id}/external-calendars/conflicts/check", headers=_headers(admin), json=payload).status_code == 200


def test_professional_can_list_available_google_calendars_endpoint(api_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    professional_user, _ = _professional(db_session, "available")

    def fake_list(self, provider, *, integration_id=None):
        return [{"external_calendar_id": "primary", "name": "Primary", "description": None, "timezone": "America/Santiago", "is_primary": True, "read_only": False}]

    monkeypatch.setattr(ExternalCalendarService, "list_available_calendars", fake_list)
    response = api_client.get("/api/v1/professionals/me/external-calendars/providers/google/available", headers=_headers(professional_user))

    assert response.status_code == 200
    assert response.json()[0]["external_calendar_id"] == "primary"
    assert "token" not in response.text.lower()


def _schema_create(data: dict):
    from app.calendars.schemas import ExternalCalendarCreate

    return ExternalCalendarCreate(**data)


def _settings(data: dict):
    from app.calendars.schemas import CalendarSyncSettingsUpdate

    return CalendarSyncSettingsUpdate(**data)
