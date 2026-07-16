from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.integrations.crypto import TokenCipher
from app.integrations.enums import IntegrationProvider, IntegrationType
from app.integrations.google_calendar import CalendarEventResult
from app.integrations.google_oauth import GoogleOAuthService, GoogleTokenResponse, GoogleAccountInfo
from app.integrations.meeting_contracts import MeetingAttendee, MeetingCreateRequest
from app.main import app
from app.models.audit_log import AuditLog
from app.models.integration import ExternalMeeting, Integration, IntegrationCredential, IntegrationExecution, IntegrationOAuthState
from app.models.user import User, UserRole
from app.schemas.integrations import IntegrationCreate
from app.services.google_meet import GoogleMeetService
from app.services.integrations import IntegrationService


class FakeOAuthClient:
    def build_authorization_url(
        self,
        *,
        state: str,
        settings,
        scopes: list[str] | None = None,
        incremental: bool = False,
        prompt_consent: bool = True,
    ) -> str:
        del settings, scopes, incremental, prompt_consent
        return f"https://accounts.google.test/oauth?state={state}"

    def exchange_code(self, *, code: str, settings) -> GoogleTokenResponse:
        return GoogleTokenResponse("access-token-not-real", "refresh-token-not-real", "Bearer", 3600, settings.google_oauth_scopes)

    def refresh_access_token(self, *, refresh_token: str, settings) -> GoogleTokenResponse:
        return GoogleTokenResponse("new-access-token-not-real", refresh_token, "Bearer", 3600, settings.google_oauth_scopes)

    def revoke_token(self, *, token: str, settings) -> None:
        return None

    def fetch_account_info(self, *, access_token: str) -> GoogleAccountInfo:
        return GoogleAccountInfo("account-1", "admin-google@example.test")


class FakeCalendarClient:
    def __init__(self, *, pending_once: bool = False, fail_create: bool = False) -> None:
        self.created_bodies: list[dict] = []
        self.create_calls = 0
        self.get_calls = 0
        self.delete_calls = 0
        self.pending_once = pending_once
        self.fail_create = fail_create
        self.deleted: set[str] = set()

    def create_event(self, *, access_token: str, calendar_id: str, request: MeetingCreateRequest, request_id: str) -> CalendarEventResult:
        self.create_calls += 1
        assert access_token.endswith("token-not-real")
        self.created_bodies.append({"calendar_id": calendar_id, "request_id": request_id, "send_updates": request.send_updates, "title": request.title, "attendees": [item.email for item in request.attendees]})
        if self.fail_create:
            from app.integrations.exceptions import IntegrationProviderExecutionError

            raise IntegrationProviderExecutionError("Google Calendar rechazo la operacion", code="google_calendar_error")
        status = "pending" if self.pending_once else "success"
        return CalendarEventResult("event-123", "https://calendar.google.com/event?eid=abc", None if self.pending_once else "https://meet.google.com/abc-defg-hij", "abc-defg-hij", status, "confirmed", request.start_at, request.end_at)

    def get_event(self, *, access_token: str, calendar_id: str, event_id: str) -> CalendarEventResult:
        self.get_calls += 1
        start = datetime.now(UTC) + timedelta(hours=1)
        end = start + timedelta(minutes=30)
        return CalendarEventResult(event_id, "https://calendar.google.com/event?eid=abc", "https://meet.google.com/abc-defg-hij", "abc-defg-hij", "success", "confirmed", start, end)

    def delete_event(self, *, access_token: str, calendar_id: str, event_id: str, send_updates: str) -> None:
        self.delete_calls += 1
        self.deleted.add(event_id)

    def get_calendar(self, *, access_token: str, calendar_id: str) -> dict:
        self.get_calls += 1
        return {"id": calendar_id, "summary": "Primary"}


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        ids = list(db.scalars(select(Integration.id).where(Integration.name.like("Test 12.2%"))))
        if ids:
            db.execute(delete(IntegrationExecution).where(IntegrationExecution.integration_id.in_(ids)))
            db.execute(delete(ExternalMeeting).where(ExternalMeeting.integration_id.in_(ids)))
            db.execute(delete(IntegrationOAuthState).where(IntegrationOAuthState.integration_id.in_(ids)))
            db.execute(delete(IntegrationCredential).where(IntegrationCredential.integration_id.in_(ids)))
            db.execute(delete(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id.in_([str(item) for item in ids])))
            db.execute(delete(Integration).where(Integration.id.in_(ids)))
        users = list(db.scalars(select(User).where(User.email.like("test-12-2-%@realmeet.local"))))
        user_ids = [item.id for item in users]
        if user_ids:
            db.execute(delete(AuditLog).where(AuditLog.user_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
        db.close()


@pytest.fixture()
def oauth_settings():
    return settings.model_copy(
        update={
            "google_oauth_client_id": "fake-client",
            "google_oauth_client_secret": "fake-secret",
            "google_oauth_redirect_uri": "http://localhost/callback",
            "google_oauth_scopes": ["https://www.googleapis.com/auth/calendar.events"],
            "google_token_encryption_key": Fernet.generate_key().decode(),
        }
    )


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(app)


def _user(db, role: UserRole) -> User:
    user = User(email=f"test-12-2-{role.value}@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Test", last_name=role.value, role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


def _integration(db, admin: User, oauth_settings) -> Integration:
    integration = IntegrationService(db).create_integration(
        IntegrationCreate(name="Test 12.2 Google Meet", integration_type=IntegrationType.meeting, provider=IntegrationProvider.google_meet, config={"calendar_id": "primary", "send_updates": "none", "default_timezone": "America/Santiago"}, secret_reference=None),
        admin,
    )
    service = GoogleOAuthService(db, oauth_client=FakeOAuthClient(), app_settings=oauth_settings)
    url, _ = service.authorization_url(integration.id, admin)
    state = url.split("state=")[1]
    service.callback(code="ok", state=state)
    integration.enabled = True
    db.commit()
    db.refresh(integration)
    return integration


def _request(key: str = "meeting:test:1") -> MeetingCreateRequest:
    start = datetime.now(UTC) + timedelta(hours=1)
    return MeetingCreateRequest(title="Prueba de integracion RealMeet", description="Reunion programada mediante RealMeet.", start_at=start, end_at=start + timedelta(minutes=30), timezone="America/Santiago", attendees=[MeetingAttendee("safe@example.com")], idempotency_key=key, send_updates="none")


def test_google_meet_create_persists_reference_and_uses_calendar_contract(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    calendar = FakeCalendarClient()

    result = GoogleMeetService(db_session, calendar_client=calendar, app_settings=oauth_settings).create_meeting(integration.id, _request(), admin)

    assert result.meeting_url == "https://meet.google.com/abc-defg-hij"
    assert result.external_event_id == "event-123"
    assert calendar.create_calls == 1
    assert calendar.created_bodies[0]["calendar_id"] == "primary"
    assert calendar.created_bodies[0]["send_updates"] == "none"
    assert calendar.created_bodies[0]["request_id"].startswith("realmeet-")
    assert db_session.scalar(select(ExternalMeeting).where(ExternalMeeting.external_event_id == "event-123")) is not None


def test_idempotency_avoids_second_google_creation(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    calendar = FakeCalendarClient()
    service = GoogleMeetService(db_session, calendar_client=calendar, app_settings=oauth_settings)

    first = service.create_meeting(integration.id, _request("meeting:test:idempotent"), admin)
    second = service.create_meeting(integration.id, _request("meeting:test:idempotent"), admin)

    assert first.external_event_id == second.external_event_id
    assert calendar.create_calls == 1


def test_pending_conference_gets_polled(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    calendar = FakeCalendarClient(pending_once=True)

    result = GoogleMeetService(db_session, calendar_client=calendar, app_settings=oauth_settings).create_meeting(integration.id, _request("meeting:test:pending"), admin)

    assert result.meeting_url == "https://meet.google.com/abc-defg-hij"
    assert calendar.get_calls >= 1


def test_health_check_does_not_create_event(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    calendar = FakeCalendarClient()

    result = GoogleMeetService(db_session, calendar_client=calendar, app_settings=oauth_settings).health_check(integration, admin)

    assert result.status == "healthy"
    assert calendar.create_calls == 0
    assert calendar.get_calls == 1


def test_cancel_is_idempotent_and_updates_local_status(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    calendar = FakeCalendarClient()
    service = GoogleMeetService(db_session, calendar_client=calendar, app_settings=oauth_settings)
    created = service.create_meeting(integration.id, _request("meeting:test:cancel"), admin)

    cancelled = service.cancel_meeting(integration.id, created.external_event_id, admin, idempotency_key="meeting:test:cancel:cancel")
    repeated = service.cancel_meeting(integration.id, created.external_event_id, admin, idempotency_key="meeting:test:cancel:cancel")

    assert cancelled.status == "cancelled"
    assert repeated.status == "cancelled"
    assert calendar.delete_calls == 1


def test_expired_token_refreshes_before_calendar_call(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)
    credential = db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id))
    assert credential is not None
    credential.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    GoogleMeetService(db_session, calendar_client=FakeCalendarClient(), oauth_client=FakeOAuthClient(), app_settings=oauth_settings).create_meeting(integration.id, _request("meeting:test:refresh"), admin)

    db_session.refresh(credential)
    assert TokenCipher(oauth_settings.google_token_encryption_key).decrypt(credential.encrypted_access_token) == "new-access-token-not-real"


def test_api_authorization_and_validation(api_client: TestClient, db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    client = _user(db_session, UserRole.client)
    professional = _user(db_session, UserRole.professional)
    integration = _integration(db_session, admin, oauth_settings)
    payload = {"title": "Prueba", "start_at": "2026-07-15T18:00:00Z", "end_at": "2026-07-15T18:30:00Z", "timezone": "America/Santiago", "idempotency_key": "meeting:test:api", "extra": True}

    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/meetings", json=payload).status_code == 401
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/meetings", json=payload, headers=_headers(client)).status_code == 403
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/meetings", json=payload, headers=_headers(professional)).status_code == 403
    assert api_client.post(f"/api/v1/admin/integrations/{integration.id}/meetings", json=payload, headers=_headers(admin)).status_code == 422


def test_mock_provider_still_rejected_for_meeting_endpoint(api_client: TestClient, db_session) -> None:
    admin = _user(db_session, UserRole.admin)
    mock = IntegrationService(db_session).create_integration(IntegrationCreate(name="Test 12.2 mock", integration_type=IntegrationType.automation, provider=IntegrationProvider.mock, config={"simulate_error": False}, secret_reference=None), admin)
    payload = {"title": "Prueba", "start_at": "2026-07-15T18:00:00Z", "end_at": "2026-07-15T18:30:00Z", "timezone": "America/Santiago", "idempotency_key": "meeting:test:mock"}

    assert api_client.post(f"/api/v1/admin/integrations/{mock.id}/meetings", json=payload, headers=_headers(admin)).status_code == 422


def test_audit_log_does_not_store_tokens_or_meet_url(db_session, oauth_settings) -> None:
    admin = _user(db_session, UserRole.admin)
    integration = _integration(db_session, admin, oauth_settings)

    GoogleMeetService(db_session, calendar_client=FakeCalendarClient(), app_settings=oauth_settings).create_meeting(integration.id, _request("meeting:test:audit"), admin)

    logs = list(db_session.scalars(select(AuditLog).where(AuditLog.entity_name == "Integration", AuditLog.entity_id == str(integration.id))))
    text = str([log.metadata_json for log in logs])
    assert "access-token" not in text
    assert "meet.google.com" not in text
