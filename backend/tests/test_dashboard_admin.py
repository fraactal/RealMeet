from datetime import UTC, datetime, timedelta

from app.models.appointment import AppointmentStatus
from app.schemas.admin import AdminProfessionalUpdate, AdminUserListResponse, PageMeta
from app.schemas.appointments import AppointmentAdminRead
from app.schemas.metrics import ClientDashboard, ProfessionalMetrics, StatusCounts
from app.services.metrics import MetricsService


def test_client_dashboard_contract_handles_empty_data() -> None:
    payload = ClientDashboard(
        upcoming_reservations=0,
        status_counts=StatusCounts(),
        recent_appointments=[],
        next_appointments=[],
    )

    assert payload.status_counts.pending == 0
    assert payload.next_appointments == []


def test_professional_metrics_contract_includes_real_statuses() -> None:
    payload = ProfessionalMetrics(
        today_reservations=0,
        upcoming_reservations=0,
        pending_reservations=1,
        confirmed_reservations=2,
        monthly_completed=3,
        lifetime_completed=4,
        unique_clients=5,
        cancelled_reservations=6,
        no_show_reservations=7,
        cancellation_rate=0.0,
        estimated_month_income=0.0,
        status_counts=StatusCounts(pending=1, confirmed=2, completed=3, cancelled=4, no_show=5),
        recent_appointments=[],
        next_appointments=[],
        is_public=True,
        availability_rules_count=2,
    )

    assert payload.status_counts.no_show == 5
    assert payload.is_public is True


def test_metrics_empty_status_counts_uses_all_appointment_states() -> None:
    counts = MetricsService._empty_status_counts()

    assert set(counts) == {"pending", "confirmed", "cancelled", "completed", "no_show"}


def test_admin_professional_update_rejects_mass_assignment_fields() -> None:
    payload = AdminProfessionalUpdate.model_validate(
        {
            "title": "Nueva descripcion",
            "user_id": 999,
            "role": "admin",
            "professional_private_notes": "not allowed",
            "password_hash": "secret",
        }
    )

    data = payload.model_dump(exclude_unset=True)

    assert data == {"title": "Nueva descripcion"}


def test_admin_appointment_contract_excludes_private_notes() -> None:
    start = datetime.now(UTC) + timedelta(days=1)
    payload = AppointmentAdminRead(
        id=1,
        professional_id=1,
        client_id=1,
        category_id=None,
        specialty_id=None,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
        status=AppointmentStatus.pending,
        consultation_mode="online",
        meeting_provider="mock",
        meeting_url=None,
        meeting=None,
        cancellation_reason=None,
        client_notes=None,
        history=[],
    ).model_dump()

    assert "professional_private_notes" not in payload


def test_admin_list_response_is_paginated() -> None:
    response = AdminUserListResponse(items=[], meta=PageMeta(page=1, page_size=20, total=0, total_pages=1))

    assert response.meta.page == 1
    assert response.items == []
