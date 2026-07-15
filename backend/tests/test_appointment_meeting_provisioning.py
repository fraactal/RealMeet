from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import IntegrationProviderExecutionError
from app.integrations.meeting_contracts import MeetingResult
from app.models.appointment import Appointment, AppointmentMeeting, AppointmentMeetingStatus, AppointmentStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.client_profile import ClientProfile
from app.models.integration import Integration
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User, UserRole
from app.schemas.appointments import AppointmentClientRead, AppointmentMeetingRead
from app.services.meeting_provisioning import MeetingProvisioningService


@pytest.fixture()
def db_session() -> Iterator:
    db = SessionLocal()
    _cleanup(db)
    try:
        yield db
    finally:
        _cleanup(db)
        db.close()


class FakeGoogleMeetService:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.created = 0
        self.cancelled = 0

    def create_meeting(self, integration_id: int, request, admin_user) -> MeetingResult:
        self.created += 1
        if self.fail:
            raise IntegrationProviderExecutionError("Google fallo de forma controlada", code="google_test_failed")
        return MeetingResult(
            provider="google_meet",
            external_event_id=f"event-{request.entity_id}",
            external_calendar_id="primary",
            meeting_url="https://meet.google.com/abc-defg-hij",
            html_link=None,
            conference_id="abc-defg-hij",
            status="active",
            start_at=request.start_at,
            end_at=request.end_at,
        )

    def cancel_meeting(self, *_args, **_kwargs) -> MeetingResult:
        self.cancelled += 1
        return MeetingResult(
            provider="google_meet",
            external_event_id="event-cancelled",
            external_calendar_id="primary",
            meeting_url=None,
            html_link=None,
            conference_id=None,
            status="cancelled",
            start_at=datetime.now(UTC),
            end_at=datetime.now(UTC),
        )

    def get_meeting(self, *_args, **_kwargs) -> MeetingResult:
        return MeetingResult(
            provider="google_meet",
            external_event_id="event-reconciled",
            external_calendar_id="primary",
            meeting_url="https://meet.google.com/abc-defg-hij",
            html_link=None,
            conference_id="abc-defg-hij",
            status="active",
            start_at=datetime.now(UTC),
            end_at=datetime.now(UTC),
        )


def test_mock_only_policy_uses_mock(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    service = MeetingProvisioningService(db_session)

    link = service.provision_for_appointment(appointment, actor)

    assert link is not None
    assert link.provider == MeetingProvider.mock
    assert link.status == AppointmentMeetingStatus.ready
    assert link.fallback_used is False
    assert appointment.meeting_url and "/mock-meeting/" in appointment.meeting_url


def test_google_preferred_uses_healthy_google(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="google_preferred", status=IntegrationStatus.healthy)
    fake = FakeGoogleMeetService()

    link = MeetingProvisioningService(db_session, google_service=fake).provision_for_appointment(appointment, actor)

    assert link.provider == MeetingProvider.google_meet
    assert link.status == AppointmentMeetingStatus.ready
    assert link.meeting_url == "https://meet.google.com/abc-defg-hij"
    assert fake.created == 1


def test_google_preferred_falls_back_to_mock_on_controlled_failure(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="google_preferred", status=IntegrationStatus.healthy)

    link = MeetingProvisioningService(db_session, google_service=FakeGoogleMeetService(fail=True)).provision_for_appointment(appointment, actor)

    assert link.provider == MeetingProvider.mock
    assert link.status == AppointmentMeetingStatus.fallback_ready
    assert link.fallback_used is True
    assert link.fallback_reason == "google_test_failed"


def test_google_required_keeps_appointment_and_marks_meeting_failed(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="google_required", status=IntegrationStatus.healthy)

    link = MeetingProvisioningService(db_session, google_service=FakeGoogleMeetService(fail=True)).provision_for_appointment(appointment, actor)

    db_session.refresh(appointment)
    assert appointment.status == AppointmentStatus.confirmed
    assert link.status == AppointmentMeetingStatus.failed
    assert link.provider == MeetingProvider.google_meet
    assert appointment.meeting_url is None


def test_disabled_policy_creates_not_required_state(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="disabled", status=IntegrationStatus.healthy)

    link = MeetingProvisioningService(db_session).provision_for_appointment(appointment, actor)

    assert link.status == AppointmentMeetingStatus.not_required
    assert link.provider is None
    assert appointment.meeting_url is None


def test_idempotency_returns_existing_ready_link(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="google_preferred", status=IntegrationStatus.healthy)
    fake = FakeGoogleMeetService()
    service = MeetingProvisioningService(db_session, google_service=fake)

    first = service.provision_for_appointment(appointment, actor)
    second = service.provision_for_appointment(appointment, actor)

    assert first.id == second.id
    assert fake.created == 1


def test_cancel_google_is_best_effort_and_idempotent(db_session) -> None:
    actor, appointment = _appointment_graph(db_session)
    _google_integration(db_session, policy="google_preferred", status=IntegrationStatus.healthy)
    fake = FakeGoogleMeetService()
    service = MeetingProvisioningService(db_session, google_service=fake)
    service.provision_for_appointment(appointment, actor)

    first = service.cancel_for_appointment(appointment, actor)
    second = service.cancel_for_appointment(appointment, actor)

    assert first.status == AppointmentMeetingStatus.cancelled
    assert second.status == AppointmentMeetingStatus.cancelled
    assert fake.cancelled == 1


def test_client_contract_does_not_expose_external_or_internal_error() -> None:
    payload = AppointmentClientRead(
        id=1,
        professional_id=2,
        client_id=3,
        category_id=None,
        specialty_id=None,
        start_datetime=datetime.now(UTC) + timedelta(days=1),
        end_datetime=datetime.now(UTC) + timedelta(days=1, hours=1),
        status=AppointmentStatus.confirmed,
        consultation_mode="online",
        meeting_provider="google_meet",
        meeting_url=None,
        meeting=AppointmentMeetingRead(provider="google_meet", join_url=None, status="failed", fallback_used=False, message="No pudimos preparar el enlace todavia."),
        cancellation_reason=None,
        client_notes=None,
        history=[],
    ).model_dump()

    assert "external_event_id" not in str(payload)
    assert payload["meeting"]["error_code"] is None
    assert payload["meeting"]["message"] == "No pudimos preparar el enlace todavia."


def _appointment_graph(db) -> tuple[User, Appointment]:
    category = Category(name="Test 12.3 Category", slug="test-12-3-category")
    client_user = User(email="test-12-3-client@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Client", last_name="Test", role=UserRole.client, is_active=True)
    professional_user = User(email="test-12-3-pro@realmeet.local", password_hash=hash_password("Secret123!"), first_name="Pro", last_name="Test", role=UserRole.professional, is_active=True)
    db.add_all([category, client_user, professional_user])
    db.flush()
    client = ClientProfile(user_id=client_user.id)
    professional = ProfessionalProfile(user_id=professional_user.id, category_id=category.id, consultation_mode=ConsultationMode.online, session_duration_minutes=60, is_public=True)
    db.add_all([client, professional])
    db.flush()
    appointment = Appointment(
        professional_id=professional.id,
        client_id=client.id,
        category_id=category.id,
        start_datetime=datetime.now(UTC) + timedelta(days=2),
        end_datetime=datetime.now(UTC) + timedelta(days=2, hours=1),
        status=AppointmentStatus.confirmed,
        consultation_mode=ConsultationMode.online,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return client_user, appointment


def _google_integration(db, *, policy: str, status: IntegrationStatus) -> Integration:
    integration = Integration(
        name="Test 12.3 Google Meet",
        integration_type=IntegrationType.meeting,
        provider=IntegrationProvider.google_meet,
        enabled=True,
        status=status,
        config={
            "calendar_id": "primary",
            "default_timezone": "America/Santiago",
            "send_updates": "none",
            "appointment_policy": policy,
            "fallback_provider": "mock",
        },
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def _cleanup(db) -> None:
    appointments = list(db.scalars(select(Appointment.id).join(ClientProfile, Appointment.client_id == ClientProfile.id).join(User, ClientProfile.user_id == User.id).where(User.email.like("test-12-3-%"))))
    if appointments:
        db.execute(delete(AppointmentMeeting).where(AppointmentMeeting.appointment_id.in_(appointments)))
        db.execute(delete(Appointment).where(Appointment.id.in_(appointments)))
    db.execute(delete(AuditLog).where(AuditLog.entity_id.in_([str(item) for item in appointments])))
    db.execute(delete(Integration).where(Integration.name.like("Test 12.3%")))
    db.execute(delete(ProfessionalProfile).where(ProfessionalProfile.user_id.in_(select(User.id).where(User.email.like("test-12-3-%")))))
    db.execute(delete(ClientProfile).where(ClientProfile.user_id.in_(select(User.id).where(User.email.like("test-12-3-%")))))
    db.execute(delete(User).where(User.email.like("test-12-3-%")))
    db.execute(delete(Category).where(Category.slug == "test-12-3-category"))
    db.commit()
