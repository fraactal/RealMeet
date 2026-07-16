from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.calendars.contracts import ExternalCalendarEventInput
from app.calendars.providers.fake import FakeExternalCalendarProvider
from app.calendars.registry import ExternalCalendarProviderRegistry
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.external_calendar import CalendarSyncSettings, ExternalCalendar, ExternalCalendarProvider
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        professional_ids = list(db.scalars(select(ProfessionalProfile.id).where(ProfessionalProfile.title.like("Test 15.1%"))))
        if professional_ids:
            db.execute(delete(CalendarSyncSettings).where(CalendarSyncSettings.professional_id.in_(professional_ids)))
            db.execute(delete(ExternalCalendar).where(ExternalCalendar.professional_id.in_(professional_ids)))
            db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.id.in_(professional_ids)))
        db.execute(delete(User).where(User.email.like("test-15-1-%@realmeet.local")))
        db.commit()
        db.close()


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _create_user(db, role: UserRole, suffix: str) -> User:
    user = User(
        email=f"test-15-1-{suffix}-{role.value}@realmeet.local",
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


def _create_professional(db, suffix: str) -> tuple[User, ProfessionalProfile]:
    user = _create_user(db, UserRole.professional, suffix)
    profile = ProfessionalProfile(
        user_id=user.id,
        title=f"Test 15.1 {suffix}",
        consultation_mode=ConsultationMode.online,
        session_duration_minutes=60,
        is_public=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _calendar_payload(external_id: str = "fake-primary", *, is_primary: bool = False) -> dict:
    return {
        "provider": "fake",
        "external_calendar_id": external_id,
        "name": f"Calendario {external_id}",
        "description": "Calendario fake de prueba",
        "timezone": "America/Santiago",
        "read_enabled": True,
        "write_enabled": False,
        "conflict_check_enabled": True,
        "is_primary": is_primary,
    }


def test_professional_can_register_and_list_own_fake_calendar(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "owner")
    created = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload())
    listed = api_client.get("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user))

    assert created.status_code == 200
    assert created.json()["provider"] == "fake"
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_professional_cannot_access_other_professional_calendar(api_client: TestClient, db_session) -> None:
    owner, _ = _create_professional(db_session, "owner-other")
    other, _ = _create_professional(db_session, "other")
    created = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(owner), json=_calendar_payload("fake-owner"))

    response = api_client.get(f"/api/v1/professionals/me/external-calendars/{created.json()['id']}", headers=_auth_headers(other))

    assert response.status_code == 404


def test_client_receives_403(api_client: TestClient, db_session) -> None:
    client = _create_user(db_session, UserRole.client, "client")

    response = api_client.get("/api/v1/professionals/me/external-calendars", headers=_auth_headers(client))

    assert response.status_code == 403


def test_admin_can_manage_professional_calendar(api_client: TestClient, db_session) -> None:
    admin = _create_user(db_session, UserRole.admin, "admin")
    _, profile = _create_professional(db_session, "admin-target")

    created = api_client.post(f"/api/v1/admin/professionals/{profile.id}/external-calendars", headers=_auth_headers(admin), json=_calendar_payload("fake-admin", is_primary=True))
    disabled = api_client.post(f"/api/v1/admin/professionals/{profile.id}/external-calendars/{created.json()['id']}/disable", headers=_auth_headers(admin))
    tested = api_client.post(f"/api/v1/admin/professionals/{profile.id}/external-calendars/{created.json()['id']}/test", headers=_auth_headers(admin))

    assert created.status_code == 200
    assert disabled.json()["enabled"] is False
    assert tested.status_code == 200
    assert tested.json()["health"]["healthy"] is True


def test_invalid_timezone_and_duplicate_calendar_are_rejected(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "validation")
    invalid = _calendar_payload("fake-invalid")
    invalid["timezone"] = "No/SuchZone"

    assert api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=invalid).status_code == 422
    assert api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("fake-dup")).status_code == 200
    assert api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("fake-dup")).status_code == 409


def test_only_one_calendar_is_primary_per_provider_and_professional(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "primary")

    first = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("fake-primary-1", is_primary=True)).json()
    second = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("fake-primary-2", is_primary=True)).json()
    listed = api_client.get("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user)).json()

    first_after = next(item for item in listed if item["id"] == first["id"])
    second_after = next(item for item in listed if item["id"] == second["id"])
    assert first_after["is_primary"] is False
    assert second_after["is_primary"] is True


def test_fake_provider_operations() -> None:
    provider = FakeExternalCalendarProvider()
    start = datetime.now(UTC)
    payload = ExternalCalendarEventInput("fake-primary", "Test", start, start + timedelta(hours=1), "America/Santiago")

    assert len(provider.list_calendars()) >= 2
    assert provider.list_busy_periods("fake-primary", start, start + timedelta(hours=8))[0].availability == "busy"
    created = provider.create_event(payload)
    updated = provider.update_event(created.external_event_id, payload)
    deleted = provider.delete_event(payload.calendar_id, created.external_event_id)
    assert created.status == "created"
    assert updated.status == "updated"
    assert deleted.status == "deleted"
    assert provider.health_check().healthy is True


def test_fake_error_is_summarized(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "fake-error")
    created = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("fake-error")).json()

    response = api_client.post(f"/api/v1/professionals/me/external-calendars/{created['id']}/test", headers=_auth_headers(user), params={"simulate_error": True})

    assert response.status_code == 200
    assert response.json()["health"]["code"] == "fake_calendar_error"
    refreshed = api_client.get(f"/api/v1/professionals/me/external-calendars/{created['id']}", headers=_auth_headers(user)).json()
    assert refreshed["last_sync_error_code"] == "fake_calendar_error"


def test_settings_update_and_invalid_policy_rejected(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "settings")

    updated = api_client.patch(
        "/api/v1/professionals/me/calendar-sync-settings",
        headers=_auth_headers(user),
        json={"sync_enabled": True, "conflict_policy": "external_busy_blocks", "lookback_days": 7, "lookahead_days": 120},
    )
    invalid = api_client.patch("/api/v1/professionals/me/calendar-sync-settings", headers=_auth_headers(user), json={"conflict_policy": "unknown"})

    assert updated.status_code == 200
    assert updated.json()["conflict_policy"] == "external_busy_blocks"
    assert invalid.status_code == 422


def test_unimplemented_provider_returns_controlled_error(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "google")
    payload = _calendar_payload("google-primary")
    payload["provider"] = "google_calendar"

    response = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=payload)

    assert response.status_code == 400
    assert "not implemented" in response.json()["detail"]


def test_tokens_or_secrets_do_not_appear_in_responses(api_client: TestClient, db_session) -> None:
    user, _ = _create_professional(db_session, "safe")
    created = api_client.post("/api/v1/professionals/me/external-calendars", headers=_auth_headers(user), json=_calendar_payload("safe-calendar"))

    response_text = created.text.lower()

    assert created.status_code == 200
    assert "token" not in response_text
    assert "secret" not in response_text
    assert "refresh" not in response_text


def test_registry_rejects_unimplemented_provider() -> None:
    with pytest.raises(Exception):
        ExternalCalendarProviderRegistry().resolve(ExternalCalendarProvider.google_calendar)
