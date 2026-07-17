from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_client, require_professional
from app.db.session import get_db
from app.models.appointment import AppointmentStatus
from app.models.user import UserRole
from app.schemas.appointments import (
    AppointmentAdminRead,
    AppointmentClientRead,
    AppointmentProfessionalRead,
    AppointmentCreate,
    AppointmentHistoryRead,
    AppointmentMeetingRead,
    AppointmentPaymentSummaryRead,
    AppointmentPrivateNotesUpdate,
    AppointmentProfessionalStatusUpdate,
    AppointmentStatusUpdate,
)
from app.services.appointments import AppointmentService
from app.payments.service import PaymentOrderService
from app.payments.transitions import ACTIVE_PAYMENT_STATUSES

router = APIRouter()


AppointmentActorRead = AppointmentClientRead | AppointmentProfessionalRead | AppointmentAdminRead


def serialize_appointment_for_user(appointment, user, service: AppointmentService) -> AppointmentActorRead:
    history = [AppointmentHistoryRead.model_validate(item) for item in service.list_history(appointment.id)]
    meeting = serialize_meeting(appointment, is_admin=user.role == UserRole.admin)
    payment = serialize_payment(appointment, service.db)
    data = {
        "id": appointment.id,
        "professional_id": appointment.professional_id,
        "client_id": appointment.client_id,
        "category_id": appointment.category_id,
        "specialty_id": appointment.specialty_id,
        "start_datetime": appointment.start_datetime,
        "end_datetime": appointment.end_datetime,
        "status": appointment.status,
        "consultation_mode": appointment.consultation_mode,
        "meeting_provider": appointment.meeting_provider.value if appointment.meeting_provider else None,
        "meeting_url": meeting.join_url if meeting else None,
        "meeting": meeting,
        "payment": payment,
        "cancellation_reason": appointment.cancellation_reason,
        "client_notes": appointment.client_notes,
        "history": history,
    }
    if user.role == UserRole.professional:
        return AppointmentProfessionalRead(**data, professional_private_notes=appointment.professional_private_notes)
    if user.role == UserRole.admin:
        return AppointmentAdminRead(**data)
    return AppointmentClientRead(**data)


def serialize_meeting(appointment, *, is_admin: bool = False) -> AppointmentMeetingRead | None:
    link = getattr(appointment, "meeting_link", None)
    if link:
        join_url = link.meeting_url if link.status.value in {"ready", "fallback_ready"} and appointment.status != AppointmentStatus.cancelled else None
        return AppointmentMeetingRead(
            provider=link.provider.value if link.provider else None,
            join_url=join_url,
            status=link.status.value,
            fallback_used=link.fallback_used,
            message=_meeting_message(link.status.value, link.fallback_used),
            error_code=link.error_code if is_admin else None,
            error_message=link.error_message if is_admin else None,
        )
    if not appointment.meeting_provider:
        if appointment.consultation_mode.value in {"online", "hybrid"} and appointment.status == AppointmentStatus.confirmed:
            return AppointmentMeetingRead(provider=None, join_url=None, status="pending", message="El enlace de reunion todavia esta siendo preparado.")
        return None
    is_cancelled = appointment.status == AppointmentStatus.cancelled
    return AppointmentMeetingRead(
        provider=appointment.meeting_provider.value,
        join_url=None if is_cancelled else appointment.meeting_url,
        status="inactive" if is_cancelled else "active",
        message="Reunion lista." if not is_cancelled else "Reunion cancelada.",
    )


def _meeting_message(status_value: str, fallback_used: bool) -> str:
    if status_value == "ready":
        return "Reunion lista."
    if status_value == "fallback_ready":
        return "Reunion simulada para entorno de prueba." if fallback_used else "Reunion lista."
    if status_value in {"pending", "provisioning"}:
        return "El enlace de reunion todavia esta siendo preparado."
    if status_value == "failed":
        return "No pudimos preparar el enlace todavia."
    if status_value == "cancelled":
        return "Reunion cancelada."
    if status_value == "not_required":
        return "No se requiere reunion automatica."
    return "Estado de reunion no disponible."


def serialize_payment(appointment, db) -> AppointmentPaymentSummaryRead | None:
    order = PaymentOrderService(db).latest_for_appointment(appointment.id)
    if not order:
        return None
    return AppointmentPaymentSummaryRead(
        order_id=order.id,
        status=order.status.value,
        amount=str(order.amount),
        currency=order.currency.value,
        expires_at=order.expires_at,
        checkout_available=order.status in ACTIVE_PAYMENT_STATUSES and order.provider.value == "fake",
    )


@router.post("", response_model=AppointmentClientRead, dependencies=[Depends(require_client)])
def create_appointment(payload: AppointmentCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AppointmentClientRead:
    service = AppointmentService(db)
    appointment = service.create(user, payload)
    return serialize_appointment_for_user(appointment, user, service)


@router.get("/me", response_model=list[AppointmentActorRead])
def list_my_appointments(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[AppointmentActorRead]:
    service = AppointmentService(db)
    items = service.list_for_user(user)
    return [serialize_appointment_for_user(item, user, service) for item in items]


@router.get("/professional/me", response_model=list[AppointmentProfessionalRead], dependencies=[Depends(require_professional)])
def list_professional_appointments(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[AppointmentProfessionalRead]:
    service = AppointmentService(db)
    items = service.list_for_user(user)
    return [serialize_appointment_for_user(item, user, service) for item in items]


@router.get("/{appointment_id}", response_model=AppointmentActorRead)
def get_appointment(appointment_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AppointmentActorRead:
    service = AppointmentService(db)
    item = service.get_for_actor(appointment_id, user)
    return serialize_appointment_for_user(item, user, service)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentActorRead)
def cancel_appointment(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentActorRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.cancel(appointment, user, payload)
    return serialize_appointment_for_user(item, user, service)


@router.patch("/professional/{appointment_id}/confirm", response_model=AppointmentProfessionalRead, dependencies=[Depends(require_professional)])
def confirm_appointment(
    appointment_id: int,
    payload: AppointmentProfessionalStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentProfessionalRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.transition(appointment, user, AppointmentStatus.confirmed, payload)
    return serialize_appointment_for_user(item, user, service)


@router.patch("/professional/{appointment_id}/complete", response_model=AppointmentProfessionalRead, dependencies=[Depends(require_professional)])
def complete_appointment(
    appointment_id: int,
    payload: AppointmentProfessionalStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentProfessionalRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.transition(appointment, user, AppointmentStatus.completed, payload)
    return serialize_appointment_for_user(item, user, service)


@router.patch("/professional/{appointment_id}/no-show", response_model=AppointmentProfessionalRead, dependencies=[Depends(require_professional)])
def mark_no_show_appointment(
    appointment_id: int,
    payload: AppointmentProfessionalStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentProfessionalRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.transition(appointment, user, AppointmentStatus.no_show, payload)
    return serialize_appointment_for_user(item, user, service)


@router.patch("/professional/{appointment_id}/cancel", response_model=AppointmentProfessionalRead, dependencies=[Depends(require_professional)])
def cancel_professional_appointment(
    appointment_id: int,
    payload: AppointmentProfessionalStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentProfessionalRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.cancel(appointment, user, payload)
    return serialize_appointment_for_user(item, user, service)


@router.patch(
    "/professional/{appointment_id}/private-notes",
    response_model=AppointmentProfessionalRead,
    dependencies=[Depends(require_professional)],
)
def update_private_notes(
    appointment_id: int,
    payload: AppointmentPrivateNotesUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentProfessionalRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.update_private_notes(appointment, user, payload)
    return serialize_appointment_for_user(item, user, service)
