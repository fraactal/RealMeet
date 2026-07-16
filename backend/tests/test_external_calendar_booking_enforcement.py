from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.calendars.contracts import BusyPeriod
from app.calendars.providers.fake import FakeExternalCalendarProvider
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.appointment import Appointment, AppointmentHistory
from app.models.availability import AvailabilityRule
from app.models.client_profile import ClientProfile
from app.models.external_calendar import CalendarSyncSettings, ExternalCalendar
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.calendars.schemas import CalendarSyncSettingsUpdate
from app.services.availability import AvailabilityService
from app.services.external_availability import ExternalAvailabilityConflict, ExternalAvailabilityService, ExternalAvailabilityUnavailable


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.title.like("Test 15.3%"))))
        client_ids = list(db.scalars(select(ClientProfile.id).join(User).where(User.email.like("test-15-3-%@realmeet.local"))))
        if client_ids:
            appointment_ids = list(db.scalars(select(Appointment.id).where(Appointment.client_id.in_(client_ids))))
            if appointment_ids:
                db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointment_ids)))
                db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
            db.execute(delete(ClientProfile).where(ClientProfile.id.in_(client_ids)))
        if professional_ids:
            appointment_ids = list(db.scalars(select(Appointment.id).where(Appointment.professional_id.in_(professional_ids))))
            if appointment_ids:
                db.execute(delete(AppointmentHistory).where(AppointmentHistory.appointment_id.in_(appointment_ids)))
                db.execute(delete(Appointment).where(Appointment.id.in_(appointment_ids)))
            db.execute(delete(CalendarSyncSettings).where(CalendarSyncSettings.professional_id.in_(professional_ids)))
            db.execute(delete(ExternalCalendar).where(ExternalCalendar.professional_id.in_(professional_ids)))
            db.execute(delete(AvailabilityRule).where(AvailabilityRule.professional_id.in_(professional_ids)))
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
        db.execute(delete(User).where(User.email.like("test-15-3-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def test_internal_only_and_disabled_do_not_consult_provider(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    _, profile = _professional(db_session, "skip")
    _rule(db_session, profile.id, weekday=0)
    _calendar(db_session, profile.id)
    calls = {"count": 0}

    def fail_if_called(self, calendar_id, starts_at, ends_at):
        calls["count"] += 1
        return []

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", fail_if_called)
    service = AvailabilityService(db_session)
    start = datetime(2026, 7, 20, 9, tzinfo=UTC)

    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="internal_only")
    assert service.list_slots(profile, start, start + timedelta(hours=3))
    _settings(db_session, profile.id, conflict_policy="disabled")
    assert service.list_slots(profile, start, start + timedelta(hours=3))
    assert calls["count"] == 0


def test_external_busy_blocks_filters_slots_and_keeps_adjacent_or_free(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    _, profile = _professional(db_session, "filter")
    _rule(db_session, profile.id, weekday=0)
    _calendar(db_session, profile.id)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks")

    def busy(self, calendar_id, starts_at, ends_at):
        return [
            BusyPeriod(datetime(2026, 7, 20, 10, tzinfo=UTC), datetime(2026, 7, 20, 11, tzinfo=UTC), calendar_id, None, "busy"),
            BusyPeriod(datetime(2026, 7, 20, 12, tzinfo=UTC), datetime(2026, 7, 20, 13, tzinfo=UTC), calendar_id, None, "free"),
        ]

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", busy)
    slots = AvailabilityService(db_session).list_slots(profile, datetime(2026, 7, 20, 9, tzinfo=UTC), datetime(2026, 7, 20, 13, tzinfo=UTC))

    assert [slot["start_datetime"].hour for slot in slots] == [9, 11, 12]


@pytest.mark.parametrize("availability", ["busy", "tentative", "out_of_office"])
def test_blocking_external_availability_rejects_candidate(db_session, monkeypatch: pytest.MonkeyPatch, availability: str) -> None:
    _, profile = _professional(db_session, f"block-{availability}")
    _calendar(db_session, profile.id)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks")

    def periods(self, calendar_id, starts_at, ends_at):
        return [BusyPeriod(starts_at + timedelta(minutes=15), starts_at + timedelta(minutes=45), calendar_id, None, availability)]

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", periods)
    with pytest.raises(ExternalAvailabilityConflict):
        ExternalAvailabilityService(db_session).validate_range(profile.id, datetime(2026, 7, 20, 9, tzinfo=UTC), datetime(2026, 7, 20, 10, tzinfo=UTC))


def test_fail_closed_blocks_provider_errors_and_fail_open_allows(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    _, profile = _professional(db_session, "failure-policy")
    _calendar(db_session, profile.id)

    def unavailable(self, calendar_id, starts_at, ends_at):
        raise RuntimeError("raw provider details")

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", unavailable)
    start = datetime(2026, 7, 20, 9, tzinfo=UTC)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks", external_conflict_failure_policy="fail_closed")
    with pytest.raises(ExternalAvailabilityUnavailable):
        ExternalAvailabilityService(db_session).validate_range(profile.id, start, start + timedelta(hours=1))

    _settings(db_session, profile.id, external_conflict_failure_policy="fail_open")
    ExternalAvailabilityService(db_session).validate_range(profile.id, start, start + timedelta(hours=1))


def test_partial_failure_follows_failure_policy(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    _, profile = _professional(db_session, "partial")
    _calendar(db_session, profile.id, external_id="ok")
    _calendar(db_session, profile.id, external_id="fails")
    start = datetime(2026, 7, 20, 9, tzinfo=UTC)

    def partially_unavailable(self, calendar_id, starts_at, ends_at):
        if calendar_id == "fails":
            raise RuntimeError("provider down")
        return [BusyPeriod(starts_at + timedelta(hours=3), starts_at + timedelta(hours=4), calendar_id, None, "busy")]

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", partially_unavailable)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks", external_conflict_failure_policy="fail_closed")
    with pytest.raises(ExternalAvailabilityUnavailable):
        ExternalAvailabilityService(db_session).validate_range(profile.id, start, start + timedelta(hours=1))

    _settings(db_session, profile.id, external_conflict_failure_policy="fail_open")
    ExternalAvailabilityService(db_session).validate_range(profile.id, start, start + timedelta(hours=1))


def test_booking_rechecks_external_availability_and_returns_sanitized_409(api_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    client_user = _client(db_session, "conflict")
    _, profile = _professional(db_session, "booking-conflict")
    _rule(db_session, profile.id, weekday=0)
    _calendar(db_session, profile.id)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks")
    calls = {"count": 0}

    def conflict(self, calendar_id, starts_at, ends_at):
        calls["count"] += 1
        return [BusyPeriod(starts_at + timedelta(minutes=10), starts_at + timedelta(minutes=50), calendar_id, "private-event-id", "busy")]

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", conflict)
    response = api_client.post(
        "/api/v1/appointments",
        headers=_headers(client_user),
        json={"professional_id": profile.id, "specialty_id": None, "start_datetime": datetime(2026, 7, 20, 9, tzinfo=UTC).isoformat()},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "external_calendar_conflict"
    assert "private-event-id" not in response.text
    assert calls["count"] >= 1


def test_booking_without_external_conflict_is_created(api_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    client_user = _client(db_session, "created")
    _, profile = _professional(db_session, "booking-ok")
    _rule(db_session, profile.id, weekday=0)
    _calendar(db_session, profile.id)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks")

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", lambda self, calendar_id, starts_at, ends_at: [])
    response = api_client.post(
        "/api/v1/appointments",
        headers=_headers(client_user),
        json={"professional_id": profile.id, "specialty_id": None, "start_datetime": datetime(2026, 7, 20, 9, tzinfo=UTC).isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["professional_id"] == profile.id


def test_fail_closed_provider_error_returns_sanitized_503(api_client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    client_user = _client(db_session, "unavailable")
    _, profile = _professional(db_session, "provider-unavailable")
    _rule(db_session, profile.id, weekday=0)
    _calendar(db_session, profile.id)
    _settings(db_session, profile.id, sync_enabled=True, conflict_policy="external_busy_blocks", external_conflict_failure_policy="fail_closed")

    monkeypatch.setattr(FakeExternalCalendarProvider, "list_busy_periods", lambda self, calendar_id, starts_at, ends_at: (_ for _ in ()).throw(RuntimeError("token raw")))
    response = api_client.post(
        "/api/v1/appointments",
        headers=_headers(client_user),
        json={"professional_id": profile.id, "specialty_id": None, "start_datetime": datetime(2026, 7, 20, 9, tzinfo=UTC).isoformat()},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "external_calendar_unavailable"
    assert "token raw" not in response.text


def test_professional_can_update_failure_policy_and_invalid_value_is_rejected(api_client: TestClient, db_session) -> None:
    user, profile = _professional(db_session, "settings")

    default_settings = api_client.get("/api/v1/professionals/me/calendar-sync-settings", headers=_headers(user))
    updated = api_client.patch("/api/v1/professionals/me/calendar-sync-settings", headers=_headers(user), json={"external_conflict_failure_policy": "fail_open"})
    invalid = api_client.patch("/api/v1/professionals/me/calendar-sync-settings", headers=_headers(user), json={"external_conflict_failure_policy": "unsafe"})

    assert default_settings.status_code == 200
    assert default_settings.json()["external_conflict_failure_policy"] == "fail_closed"
    assert updated.status_code == 200
    assert updated.json()["professional_id"] == profile.id
    assert updated.json()["external_conflict_failure_policy"] == "fail_open"
    assert invalid.status_code == 422


def _user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-15-3-{suffix}-{role.value}@realmeet.local",
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


def _client(db, suffix: str) -> User:
    user = _user(db, UserRole.client, suffix)
    db.add(ClientProfile(user_id=user.id))
    db.commit()
    return user


def _professional(db, suffix: str) -> tuple[User, ProfessionalProfile]:
    user = _user(db, UserRole.professional, suffix)
    profile = ProfessionalProfile(
        user_id=user.id,
        title=f"Test 15.3 {suffix}",
        consultation_mode=ConsultationMode.online,
        session_duration_minutes=60,
        is_public=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _rule(db, professional_id: int, *, weekday: int) -> None:
    db.add(AvailabilityRule(professional_id=professional_id, weekday=weekday, start_time=time(9, 0), end_time=time(13, 0), is_active=True))
    db.commit()


def _calendar(db, professional_id: int, *, external_id: str = "fake-primary") -> ExternalCalendar:
    item = ExternalCalendar(
        professional_id=professional_id,
        provider="fake",
        external_calendar_id=external_id,
        name=f"Calendar {external_id}",
        timezone="America/Santiago",
        read_enabled=True,
        write_enabled=False,
        conflict_check_enabled=True,
        enabled=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _settings(db, professional_id: int, **data) -> CalendarSyncSettings:
    from app.calendars.service import ExternalCalendarService

    service = ExternalCalendarService(db)
    settings = service.update_settings(professional_id, CalendarSyncSettingsUpdate(**data))
    db.refresh(settings)
    return settings


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
