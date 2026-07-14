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
    AppointmentProfessionalStatusUpdate,
    AppointmentStatusUpdate,
)
from app.services.appointments import AppointmentService

router = APIRouter()


AppointmentActorRead = AppointmentClientRead | AppointmentProfessionalRead | AppointmentAdminRead


def serialize_appointment_for_user(appointment, user) -> AppointmentActorRead:
    if user.role == UserRole.professional:
        return AppointmentProfessionalRead.model_validate(appointment)
    if user.role == UserRole.admin:
        return AppointmentAdminRead.model_validate(appointment)
    return AppointmentClientRead.model_validate(appointment)


@router.post("", response_model=AppointmentClientRead, dependencies=[Depends(require_client)])
def create_appointment(payload: AppointmentCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AppointmentClientRead:
    appointment = AppointmentService(db).create(user, payload)
    return AppointmentClientRead.model_validate(appointment)


@router.get("/me", response_model=list[AppointmentActorRead])
def list_my_appointments(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[AppointmentActorRead]:
    items = AppointmentService(db).list_for_user(user)
    return [serialize_appointment_for_user(item, user) for item in items]


@router.get("/{appointment_id}", response_model=AppointmentActorRead)
def get_appointment(appointment_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)) -> AppointmentActorRead:
    item = AppointmentService(db).get_for_actor(appointment_id, user)
    return serialize_appointment_for_user(item, user)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentActorRead)
def cancel_appointment(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentActorRead:
    service = AppointmentService(db)
    appointment = service.get_for_actor(appointment_id, user)
    item = service.transition(appointment, user, AppointmentStatus.cancelled, payload)
    return serialize_appointment_for_user(item, user)


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
    return AppointmentProfessionalRead.model_validate(item)


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
    return AppointmentProfessionalRead.model_validate(item)
