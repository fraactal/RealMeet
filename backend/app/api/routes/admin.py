from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.category import Category
from app.models.professional_profile import ProfessionalProfile
from app.models.specialty import Specialty
from app.models.user import User
from app.schemas.appointments import AppointmentAdminRead, AppointmentHistoryRead, AppointmentMeetingRead, AppointmentStatusUpdate
from app.schemas.categories import CategoryAdminRead, CategoryCreate, CategoryUpdate
from app.schemas.professionals import ProfessionalProfileRead
from app.schemas.specialties import SpecialtyAdminRead, SpecialtyCreate, SpecialtyUpdate
from app.schemas.users import UserRead, UserUpdate
from app.services.catalog import CatalogService
from app.services.appointments import AppointmentService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserRead])
def list_users(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[UserRead]:
    items = list(db.scalars(select(User).offset(offset).limit(limit).order_by(User.created_at.desc())))
    return [UserRead.model_validate(item) for item in items]


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/professionals", response_model=list[ProfessionalProfileRead])
def list_professionals(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[ProfessionalProfileRead]:
    items = list(db.scalars(select(ProfessionalProfile).offset(offset).limit(limit).order_by(ProfessionalProfile.created_at.desc())))
    return [ProfessionalProfileRead.model_validate(item) for item in items]


@router.get("/categories", response_model=list[CategoryAdminRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryAdminRead]:
    items = CatalogService(db).list_categories(active_only=False)
    return [CategoryAdminRead.model_validate(item) for item in items]


@router.post("/categories", response_model=CategoryAdminRead)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    item = CatalogService(db).create_category(payload)
    return CategoryAdminRead.model_validate(item)


@router.patch("/categories/{category_id}", response_model=CategoryAdminRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    item = CatalogService(db).update_category(category, payload)
    return CategoryAdminRead.model_validate(item)


@router.get("/specialties", response_model=list[SpecialtyAdminRead])
def list_specialties(category_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[SpecialtyAdminRead]:
    items = CatalogService(db).list_specialties(category_id=category_id, active_only=False)
    return [SpecialtyAdminRead.model_validate(item) for item in items]


@router.post("/specialties", response_model=SpecialtyAdminRead)
def create_specialty(payload: SpecialtyCreate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    item = CatalogService(db).create_specialty(payload)
    return SpecialtyAdminRead.model_validate(item)


@router.patch("/specialties/{specialty_id}", response_model=SpecialtyAdminRead)
def update_specialty(specialty_id: int, payload: SpecialtyUpdate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    specialty = db.get(Specialty, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    item = CatalogService(db).update_specialty(specialty, payload)
    return SpecialtyAdminRead.model_validate(item)


@router.patch("/professionals/{professional_id}", response_model=ProfessionalProfileRead)
def patch_professional(professional_id: int, payload: dict, db: Session = Depends(get_db)) -> ProfessionalProfileRead:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    for key, value in payload.items():
        if hasattr(professional, key):
            setattr(professional, key, value)
    db.commit()
    db.refresh(professional)
    return ProfessionalProfileRead.model_validate(professional)


@router.get("/appointments", response_model=list[AppointmentAdminRead])
def list_appointments(limit: int = Query(default=20, le=100), offset: int = Query(default=0), db: Session = Depends(get_db)) -> list[AppointmentAdminRead]:
    service = AppointmentService(db)
    items = list(db.scalars(select(Appointment).offset(offset).limit(limit).order_by(Appointment.start_datetime.desc())))
    return [_serialize_admin_appointment(item, service) for item in items]


@router.get("/appointments/{appointment_id}", response_model=AppointmentAdminRead)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)) -> AppointmentAdminRead:
    service = AppointmentService(db)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _serialize_admin_appointment(appointment, service)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentAdminRead)
def update_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    payload: AppointmentStatusUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    service = AppointmentService(db)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    item = service.transition(appointment, user, new_status, payload)
    return _serialize_admin_appointment(item, service)


def _serialize_admin_appointment(appointment: Appointment, service: AppointmentService) -> AppointmentAdminRead:
    meeting = _serialize_meeting(appointment)
    return AppointmentAdminRead(
        id=appointment.id,
        professional_id=appointment.professional_id,
        client_id=appointment.client_id,
        category_id=appointment.category_id,
        specialty_id=appointment.specialty_id,
        start_datetime=appointment.start_datetime,
        end_datetime=appointment.end_datetime,
        status=appointment.status,
        consultation_mode=appointment.consultation_mode,
        meeting_provider=appointment.meeting_provider.value if appointment.meeting_provider else None,
        meeting_url=meeting.join_url if meeting else None,
        meeting=meeting,
        cancellation_reason=appointment.cancellation_reason,
        client_notes=appointment.client_notes,
        history=[AppointmentHistoryRead.model_validate(item) for item in service.list_history(appointment.id)],
    )


def _serialize_meeting(appointment: Appointment) -> AppointmentMeetingRead | None:
    if not appointment.meeting_provider:
        return None
    is_cancelled = appointment.status == AppointmentStatus.cancelled
    return AppointmentMeetingRead(
        provider=appointment.meeting_provider.value,
        join_url=None if is_cancelled else appointment.meeting_url,
        status="inactive" if is_cancelled else "active",
    )
