from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.calendars.registry import ExternalCalendarProviderRegistry
from app.calendars.service import ExternalCalendarService
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.google_calendar import CalendarEventResult
from app.main import app
from app.models.appointment import Appointment, AppointmentExternalCalendarEvent, AppointmentHistory, AppointmentMeeting, AppointmentMeetingStatus, AppointmentStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.external_calendar import CalendarSyncSettings, ExternalCalendar, ExternalCalendarProvider
from app.models.integration import Integration, IntegrationCredential
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.services.appointment_calendar_sync import AppointmentCalendarSyncService


class FakeGoogleWriteClient:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.updated: list[dict] = []
        self.deleted: list[str] = []
        self.events: dict[str, CalendarEventResult] = {}
        self.fail_create = False
        self.fail_update = False
        self.fail_delete = False

    def list_calendars(self, *, access_token: str) -> list[dict]:
        return [{"id": "primary", "summary": "Primary", "timeZone": "America/Santiago", "primary": True, "accessRole": "owner"}]

    def freebusy(self, **kwargs) -> dict:
        return {"calendars": {"primary": {"busy": []}}}

    def create_plain_event(self, *, access_token: str, calendar_id: str, payload, send_updates: str) -> CalendarEventResult:
        if self.fail_create:
            raise RuntimeError("raw create payload")
        event_id = f"event-{len(self.created) + 1}"
        self.created.append({"calendar_id": calendar_id, "payload": payload})
        result = _event(event_id, calendar_id, payload.starts_at, payload.ends_at)
        self.events[event_id] = result
        return result

    def update_plain_event(self, *, access_token: str, calendar_id: str, event_id: str, payload, send_updates: str) -> CalendarEventResult:
        if self.fail_update:
            raise RuntimeError("raw update payload")
        self.updated.append({"calendar_id": calendar_id, "event_id": event_id, "payload": payload})
        result = _event(event_id, calendar_id, payload.starts_at, payload.ends_at)
        self.events[event_id] = result
        return result

    def get_event(self, *, access_token: str, calendar_id: str, event_id: str) -> CalendarEventResult:
        if event_id not in self.events:
            raise RuntimeError("missing")
        return self.events[event_id]

    def find_event_by_appointment_id(self, *, access_token: str, calendar_id: str, appointment_id: int) -> CalendarEventResult | None:
        return next(iter(self.events.values()), None)

    def delete_event(self, *, access_token: str, calendar_id: str, event_id: str, send_updates: str) -> None:
        if self.fail_delete:
            raise RuntimeError("raw delete payload")
        self.deleted.append(event_id)
        if event_id in self.events:
            event = self.events[event_id]
            self.events[event_id] = CalendarEventResult(event.event_id, event.html_link, event.hangout_link, event.conference_id, event.conference_status, "cancelled", event.start_at, event.end_at)

    def get_calendar(self, **kwargs) -> dict:
        return {"id": "primary"}

    def create_event(self, **kwargs):
        raise AssertionError("Google Meet create_event is not used by calendar sync tests")


@pytest.fixture()
def db_session() -> Iterator:
    object.__setattr__(settings, "google_token_encryption_key", Fernet.generate_key().decode())
    db = SessionLocal()
    _cleanup(db)
    try:
        yield db
    finally:
        db.rollback()
        _cleanup(db)
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def test_booking_with_write_enabled_google_calendar_creates_sanitized_event(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "create", ConsultationMode.presencial)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)

    link = _sync(db_session, client).sync_created(appointment, _admin(db_session, "create"))

    assert link is not None
    assert link.external_event_id == "event-1"
    assert link.status.value == "created"
    payload = client.created[0]["payload"]
    assert "RealMeet" in payload.title
    assert "ID de reserva" in payload.description
    assert "diagnostico" not in payload.description.lower()


def test_without_destination_or_read_only_calendar_no_event_is_created(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "no-destination", ConsultationMode.presencial)
    assert _sync(db_session, client).sync_created(appointment, _admin(db_session, "no-destination")) is None
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=False)
    assert _sync(db_session, client).sync_created(appointment, _admin(db_session, "read-only")) is None
    assert client.created == []


def test_link_is_persisted_and_idempotency_avoids_duplicate_create(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "idempotent", ConsultationMode.presencial)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)
    service = _sync(db_session, client)

    first = service.sync_created(appointment, _admin(db_session, "idempotent-a"))
    second = service.retry(appointment.id, _admin(db_session, "idempotent-b"))

    assert first.id == second.id
    assert len(client.created) == 1
    assert db_session.scalar(select(AppointmentExternalCalendarEvent).where(AppointmentExternalCalendarEvent.appointment_id == appointment.id))


def test_existing_google_meet_event_is_reused(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "meet", ConsultationMode.online, status=AppointmentStatus.confirmed)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)
    db_session.add(AppointmentMeeting(appointment_id=appointment.id, provider=MeetingProvider.google_meet, status=AppointmentMeetingStatus.ready, external_reference="meet-event", calendar_event_id="primary"))
    db_session.commit()
    db_session.refresh(appointment)

    link = _sync(db_session, client).sync_created(appointment, _admin(db_session, "meet"))

    assert link.external_event_id == "meet-event"
    assert client.created == []


def test_update_failure_keeps_internal_change_and_requires_reconcile(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "update-fail", ConsultationMode.presencial)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)
    service = _sync(db_session, client)
    service.sync_created(appointment, _admin(db_session, "update-fail-a"))
    appointment.start_datetime += timedelta(hours=1)
    appointment.end_datetime += timedelta(hours=1)
    db_session.commit()
    client.fail_update = True

    link = service.sync_updated(appointment, _admin(db_session, "update-fail-b"))

    assert appointment.start_datetime.hour == 10
    assert link.status.value == "reconcile_required"
    assert link.last_error_message == "El evento externo requiere revision manual."


def test_cancel_attempts_delete_and_failure_keeps_internal_cancellation(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "cancel", ConsultationMode.presencial)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)
    service = _sync(db_session, client)
    service.sync_created(appointment, _admin(db_session, "cancel-a"))
    appointment.status = AppointmentStatus.cancelled
    db_session.commit()
    link = service.sync_cancelled(appointment, _admin(db_session, "cancel-b"))
    assert link.status.value == "cancelled"
    assert client.deleted == ["event-1"]

    appointment2 = _appointment(db_session, profile.id, _client(db_session, "cancel-fail").id)
    service.sync_created(appointment2, _admin(db_session, "cancel-c"))
    appointment2.status = AppointmentStatus.cancelled
    db_session.commit()
    client.fail_delete = True
    failed = service.sync_cancelled(appointment2, _admin(db_session, "cancel-d"))
    assert failed.status.value == "reconcile_required"
    assert appointment2.status == AppointmentStatus.cancelled


def test_reconcile_detects_existing_and_missing_event(db_session) -> None:
    client = FakeGoogleWriteClient()
    _, profile, appointment = _setup(db_session, "reconcile", ConsultationMode.presencial)
    _external_calendar(db_session, profile.id, _integration(db_session).id, write_enabled=True)
    service = _sync(db_session, client)
    link = service.sync_created(appointment, _admin(db_session, "reconcile-a"))
    link.external_event_id = None
    db_session.commit()
    found = service.reconcile(appointment.id, _admin(db_session, "reconcile-b"))
    assert found.external_event_id == "event-1"

    client.events.clear()
    found.external_event_id = None
    db_session.commit()
    missing = service.reconcile(appointment.id, _admin(db_session, "reconcile-c"))
    assert missing.status.value == "reconcile_required"
    assert missing.last_error_code == "missing_external_event"


def test_professional_admin_and_client_permissions_for_manual_actions(api_client: TestClient, db_session) -> None:
    professional_user, profile, appointment = _setup(db_session, "api", ConsultationMode.presencial)
    client_user = _client_user(db_session, "api-client")
    admin = _admin(db_session, "api-admin")
    db_session.refresh(appointment)

    assert api_client.get(f"/api/v1/professionals/me/appointments/{appointment.id}/external-calendar", headers=_headers(professional_user)).status_code == 200
    assert api_client.post(f"/api/v1/professionals/me/appointments/{appointment.id}/external-calendar/retry", headers=_headers(client_user)).status_code == 403
    assert api_client.get(f"/api/v1/admin/appointments/{appointment.id}/external-calendar", headers=_headers(admin)).status_code == 200


def _event(event_id: str, calendar_id: str, starts_at: datetime, ends_at: datetime) -> CalendarEventResult:
    return CalendarEventResult(event_id, "https://calendar.google.test/event", None, None, "success", "confirmed", starts_at, ends_at)


def _cleanup(db) -> None:
    professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.title.like("Test 15.4%"))))
    user_ids = list(db.scalars(select(User.id).where(User.email.like("test-15-4-%@realmeet.local"))))
    appointment_ids = list(db.scalars(select(Appointment.id).where(Appointment.professional_id.in_(professional_ids)))) if professional_ids else []
    if appointment_ids:
        db.execute(delete(AppointmentExternalCalendarEvent).where(AppointmentExternalCalendarEvent.appointment_id.in_(appointment_ids)))
        db.execute(delete(AppointmentMeeting).where(AppointmentMeeting.appointment_id.in_(appointment_ids)))
        db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointment_ids)))
        db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
    if professional_ids:
        db.execute(delete(CalendarSyncSettings).where(CalendarSyncSettings.professional_id.in_(professional_ids)))
        db.execute(delete(ExternalCalendar).where(ExternalCalendar.professional_id.in_(professional_ids)))
        db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
    integration_ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 15.4%"))))
    if integration_ids:
        db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(integration_ids)))
        db.execute(delete(Integration).where(Integration.id.in_(integration_ids)))
    if user_ids:
        db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
        db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(user_ids)))
        db.execute(delete(User).where(User.id.in_(user_ids)))
    db.commit()


def _sync(db, client: FakeGoogleWriteClient) -> AppointmentCalendarSyncService:
    service = ExternalCalendarService(db, ExternalCalendarProviderRegistry(db, google_calendar_client=client))
    return AppointmentCalendarSyncService(db, service)


def _setup(db, suffix: str, mode: ConsultationMode, status: AppointmentStatus = AppointmentStatus.pending):
    professional_user = _user(db, UserRole.professional, suffix)
    profile = ProfessionalProfile(user_id=professional_user.id, title=f"Test 15.4 {suffix}", consultation_mode=mode, session_duration_minutes=60, is_public=True)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    client = _client(db, suffix)
    appointment = _appointment(db, profile.id, client.id, status=status)
    return professional_user, profile, appointment


def _appointment(db, professional_id: int, client_id: int, status: AppointmentStatus = AppointmentStatus.pending) -> Appointment:
    item = Appointment(professional_id=professional_id, client_id=client_id, start_datetime=datetime(2026, 7, 20, 9, tzinfo=UTC), end_datetime=datetime(2026, 7, 20, 10, tzinfo=UTC), status=status, consultation_mode=ConsultationMode.presencial)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _external_calendar(db, professional_id: int, integration_id: int, *, write_enabled: bool) -> ExternalCalendar:
    item = ExternalCalendar(professional_id=professional_id, integration_id=integration_id, provider=ExternalCalendarProvider.google_calendar, external_calendar_id="primary", name="Primary", timezone="America/Santiago", read_enabled=True, write_enabled=write_enabled, conflict_check_enabled=True, is_primary=True, enabled=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _integration(db) -> Integration:
    existing = db.scalar(select(Integration).where(Integration.name == "Test 15.4 Google"))
    if existing:
        return existing
    integration = Integration(name="Test 15.4 Google", integration_type=IntegrationType.meeting, provider=IntegrationProvider.google_meet, enabled=True, status=IntegrationStatus.healthy, config={"appointment_policy": "mock_only"})
    db.add(integration)
    db.flush()
    cipher = TokenCipher(settings.google_token_encryption_key)
    db.add(IntegrationCredential(integration_id=integration.id, credential_type="google_oauth", encrypted_access_token=cipher.encrypt("access-token"), encrypted_refresh_token=cipher.encrypt("refresh-token"), token_type="Bearer", expires_at=datetime.now(UTC) + timedelta(hours=1), scopes=["https://www.googleapis.com/auth/calendar.events"]))
    db.commit()
    db.refresh(integration)
    return integration


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(email=f"test-15-4-{suffix}-{role.value}@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Test", last_name=role.value.title(), role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _client_user(db, suffix: str) -> User:
    user = _user(db, UserRole.client, suffix)
    db.add(ClientProfile(user_id=user.id))
    db.commit()
    return user


def _client(db, suffix: str) -> ClientProfile:
    user = _client_user(db, suffix)
    profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
    assert profile is not None
    return profile


def _admin(db, suffix: str) -> User:
    return _user(db, UserRole.admin, suffix)


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
