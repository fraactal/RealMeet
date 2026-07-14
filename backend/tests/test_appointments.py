from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.appointment import AppointmentStatus
from app.schemas.appointments import AppointmentAdminRead, AppointmentClientRead, AppointmentProfessionalRead
from app.services.appointments import AppointmentService


def _appointment(status: AppointmentStatus, starts_in_minutes: int = 60):
    return SimpleNamespace(
        id=1,
        status=status,
        start_datetime=datetime.now(UTC) + timedelta(minutes=starts_in_minutes),
    )


def _read_payload() -> dict:
    start = datetime.now(UTC) + timedelta(days=1)
    return {
        "id": 1,
        "professional_id": 2,
        "client_id": 3,
        "category_id": 4,
        "specialty_id": None,
        "start_datetime": start,
        "end_datetime": start + timedelta(hours=1),
        "status": AppointmentStatus.pending,
        "consultation_mode": "online",
        "meeting_provider": "mock",
        "meeting_url": "https://meet.example.local/abc",
        "external_meeting_id": None,
        "calendar_event_id": None,
        "cancellation_reason": None,
        "client_notes": None,
        "history": [],
    }


def test_client_and_admin_appointment_contracts_do_not_expose_private_notes() -> None:
    client_payload = AppointmentClientRead(**_read_payload()).model_dump()
    admin_payload = AppointmentAdminRead(**_read_payload()).model_dump()

    assert "professional_private_notes" not in client_payload
    assert "professional_private_notes" not in admin_payload


def test_professional_appointment_contract_can_expose_private_notes() -> None:
    payload = AppointmentProfessionalRead(**_read_payload(), professional_private_notes="Clinical context").model_dump()

    assert payload["professional_private_notes"] == "Clinical context"


def test_professional_status_transition_rejects_invalid_flow() -> None:
    appointment = _appointment(AppointmentStatus.cancelled)

    with pytest.raises(HTTPException) as exc_info:
        AppointmentService._ensure_professional_transition(appointment, AppointmentStatus.completed)

    assert exc_info.value.status_code == 400


def test_professional_status_transition_allows_pending_to_confirmed() -> None:
    AppointmentService._ensure_professional_transition(_appointment(AppointmentStatus.pending), AppointmentStatus.confirmed)


def test_professional_status_transition_allows_confirmed_to_no_show() -> None:
    AppointmentService._ensure_professional_transition(_appointment(AppointmentStatus.confirmed), AppointmentStatus.no_show)


def test_client_cannot_cancel_past_appointment() -> None:
    with pytest.raises(HTTPException) as exc_info:
        AppointmentService._ensure_client_can_cancel(_appointment(AppointmentStatus.pending, starts_in_minutes=-5))

    assert exc_info.value.status_code == 400
