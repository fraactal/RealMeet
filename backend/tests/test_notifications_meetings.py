from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.emails.service import EmailService
from app.meetings.mock import MockMeetingProvider
from app.models.appointment import AppointmentStatus
from app.notifications.service import AppointmentNotificationService
from app.schemas.appointments import AppointmentClientRead, AppointmentMeetingRead
from app.services.appointments import AppointmentService


def _appointment(**overrides):
    start = datetime.now(UTC) + timedelta(days=1)
    data = {
        "id": 1,
        "professional_id": 2,
        "client_id": 3,
        "start_datetime": start,
        "end_datetime": start + timedelta(hours=1),
        "status": AppointmentStatus.confirmed,
        "consultation_mode": SimpleNamespace(value="online"),
        "meeting_url": "http://localhost:15173/mock-meeting/mock-1",
        "cancellation_reason": None,
        "professional_private_notes": "private clinical note",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_mock_meeting_provider_creates_local_development_url() -> None:
    provider = MockMeetingProvider("http://localhost:15173/mock-meeting")
    payload = provider.create_meeting("Demo Professional", datetime(2026, 7, 15, 9, 0, tzinfo=UTC))

    assert payload.provider == "mock"
    assert payload.url.startswith("http://localhost:15173/mock-meeting/")
    assert payload.external_id is not None
    assert payload.status == "active"


def test_presential_appointment_does_not_create_meeting_payload() -> None:
    professional = SimpleNamespace(
        consultation_mode=SimpleNamespace(value="presencial"),
        user=SimpleNamespace(first_name="Demo", last_name="Professional"),
    )

    assert AppointmentService._create_meeting_payload(professional, datetime.now(UTC) + timedelta(days=1)) is None


def test_client_contract_contains_safe_meeting_object_without_private_notes() -> None:
    start = datetime.now(UTC) + timedelta(days=1)
    payload = AppointmentClientRead(
        id=1,
        professional_id=2,
        client_id=3,
        category_id=None,
        specialty_id=None,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        status=AppointmentStatus.confirmed,
        consultation_mode="online",
        meeting_provider="mock",
        meeting_url="http://localhost:15173/mock-meeting/mock-1",
        meeting=AppointmentMeetingRead(provider="mock", join_url="http://localhost:15173/mock-meeting/mock-1", status="active"),
        cancellation_reason=None,
        client_notes=None,
        history=[],
    ).model_dump()

    assert payload["meeting"]["provider"] == "mock"
    assert payload["meeting"]["status"] == "active"
    assert "professional_private_notes" not in payload
    assert "external_meeting_id" not in payload


def test_notification_body_does_not_include_private_notes() -> None:
    context = SimpleNamespace(
        professional_name="Demo Professional",
        client_name="Demo Client",
    )
    body = AppointmentNotificationService._build_body(_appointment(), context, "Reserva confirmada", include_meeting=True)

    assert "private clinical note" not in body
    assert "http://localhost:15173/mock-meeting/mock-1" in body


def test_notification_service_tolerates_unexpected_failure() -> None:
    class FailingDb:
        def scalar(self, *_):
            raise RuntimeError("db unavailable")

    AppointmentNotificationService(FailingDb()).notify_created(_appointment())


def test_email_log_mode_does_not_raise(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    from app.core.config import settings

    caplog.set_level("INFO", logger="realmeet.email")
    monkeypatch.setattr(settings, "email_mode", "log")
    monkeypatch.setattr(settings, "smtp_host", None)

    sent = EmailService().send("Subject", "client@example.test", "Body")

    assert sent is True
    assert "email_notification_logged" in caplog.text
