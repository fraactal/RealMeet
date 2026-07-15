from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import (
    IntegrationConfigurationError,
    IntegrationDisabledError,
    IntegrationError,
    IntegrationExecutionInProgressError,
    IntegrationNotFoundError,
    IntegrationProviderUnsupportedError,
)
from app.models.audit_log import AuditLog
from app.models.appointment import Appointment, AppointmentStatus
from app.models.category import Category
from app.models.professional_profile import ProfessionalProfile, ProfessionalSpecialty
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminAppointmentListResponse,
    AdminAppointmentStatusUpdate,
    AdminProfessionalDetail,
    AdminProfessionalListItem,
    AdminProfessionalListResponse,
    AdminProfessionalUpdate,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdate,
    PageMeta,
)
from app.schemas.appointments import AppointmentAdminRead, AppointmentHistoryRead, AppointmentMeetingRead, AppointmentStatusUpdate
from app.schemas.categories import CategoryAdminRead, CategoryCreate, CategoryUpdate
from app.schemas.integrations import (
    IntegrationExecutionRead,
    IntegrationListResponse,
    IntegrationOperationResultRead,
    IntegrationPageMeta,
    IntegrationRead,
    IntegrationTestRequest,
    IntegrationCreate,
    IntegrationUpdate,
)
from app.schemas.specialties import SpecialtyAdminRead, SpecialtyCreate, SpecialtyUpdate
from app.services.catalog import CatalogService
from app.services.appointments import AppointmentService
from app.services.integrations import IntegrationService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/integrations", response_model=IntegrationListResponse)
def list_integrations(
    integration_type: IntegrationType | None = Query(default=None),
    provider: IntegrationProvider | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    integration_status: IntegrationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> IntegrationListResponse:
    items, total = IntegrationService(db).list_integrations(
        integration_type=integration_type,
        provider=provider,
        enabled=enabled,
        status=integration_status,
        page=page,
        page_size=page_size,
    )
    return IntegrationListResponse(
        items=[IntegrationRead.model_validate(item) for item in items],
        meta=_integration_page_meta(page, page_size, total),
    )


@router.post("/integrations", response_model=IntegrationRead)
def create_integration(
    payload: IntegrationCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).create_integration(payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.get("/integrations/{integration_id}", response_model=IntegrationRead)
def get_integration(integration_id: int, db: Session = Depends(get_db)) -> IntegrationRead:
    try:
        item = IntegrationService(db).get_integration(integration_id)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.patch("/integrations/{integration_id}", response_model=IntegrationRead)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).update_integration(integration_id, payload, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/validate", response_model=IntegrationOperationResultRead)
def validate_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).validate_configuration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.post("/integrations/{integration_id}/enable", response_model=IntegrationRead)
def enable_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).enable_integration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/disable", response_model=IntegrationRead)
def disable_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    try:
        item = IntegrationService(db).disable_integration(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return IntegrationRead.model_validate(item)


@router.post("/integrations/{integration_id}/health-check", response_model=IntegrationOperationResultRead)
def health_check_integration(
    integration_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).health_check(integration_id, admin_user)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.post("/integrations/{integration_id}/test", response_model=IntegrationOperationResultRead)
def test_integration(
    integration_id: int,
    payload: IntegrationTestRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> IntegrationOperationResultRead:
    try:
        result = IntegrationService(db).test_integration(integration_id, admin_user, idempotency_key=payload.idempotency_key)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return _operation_result(result)


@router.get("/integrations/{integration_id}/executions", response_model=list[IntegrationExecutionRead])
def list_integration_executions(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[IntegrationExecutionRead]:
    try:
        items = IntegrationService(db).list_executions(integration_id, limit=limit)
    except IntegrationError as exc:
        raise _integration_http_error(exc) from exc
    return [IntegrationExecutionRead.model_validate(item) for item in items]


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    query = select(User)
    count_query = select(func.count(User.id))
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term)))
    if role:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc(), User.id.desc())))
    return AdminUserListResponse(
        items=[_serialize_user_item(item) for item in items],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)) -> AdminUserDetail:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user_detail(user)


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserDetail:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(user, key, value)
    _audit(db, admin_user.id, "admin_user_updated", "User", str(user.id), {"fields": sorted(changes.keys())})
    db.commit()
    db.refresh(user)
    return _serialize_user_detail(user)


@router.get("/professionals", response_model=AdminProfessionalListResponse)
def list_professionals(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminProfessionalListResponse:
    query = select(ProfessionalProfile).join(User, ProfessionalProfile.user_id == User.id)
    count_query = select(func.count(ProfessionalProfile.id)).join(User, ProfessionalProfile.user_id == User.id)
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term), ProfessionalProfile.title.ilike(term)))
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if is_public is not None:
        conditions.append(ProfessionalProfile.is_public == is_public)
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(ProfessionalProfile.created_at.desc())))
    return AdminProfessionalListResponse(
        items=[_serialize_professional_item(item) for item in items],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/professionals/{professional_id}", response_model=AdminProfessionalDetail)
def get_professional(professional_id: int, db: Session = Depends(get_db)) -> AdminProfessionalDetail:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return _serialize_professional_detail(db, professional)


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


@router.patch("/professionals/{professional_id}", response_model=AdminProfessionalDetail)
def patch_professional(
    professional_id: int,
    payload: AdminProfessionalUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminProfessionalDetail:
    professional = db.get(ProfessionalProfile, professional_id)
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    changes = payload.model_dump(exclude_unset=True)
    user_is_active = changes.pop("user_is_active", None)
    for key, value in changes.items():
        setattr(professional, key, value)
    if user_is_active is not None:
        professional.user.is_active = user_is_active
    _audit(
        db,
        admin_user.id,
        "admin_professional_updated",
        "ProfessionalProfile",
        str(professional.id),
        {"fields": sorted([*changes.keys(), *([] if user_is_active is None else ["user_is_active"])])},
    )
    db.commit()
    db.refresh(professional)
    return _serialize_professional_detail(db, professional)


@router.get("/appointments", response_model=AdminAppointmentListResponse)
def list_appointments(
    status: AppointmentStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AdminAppointmentListResponse:
    service = AppointmentService(db)
    query = select(Appointment)
    count_query = select(func.count(Appointment.id))
    conditions = []
    if status:
        conditions.append(Appointment.status == status)
    if search:
        term = f"%{search.strip()}%"
        query = query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).join(User, ProfessionalProfile.user_id == User.id)
        count_query = count_query.join(ProfessionalProfile, Appointment.professional_id == ProfessionalProfile.id).join(User, ProfessionalProfile.user_id == User.id)
        conditions.append(or_(User.email.ilike(term), User.first_name.ilike(term), User.last_name.ilike(term)))
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size).order_by(Appointment.start_datetime.desc())))
    return AdminAppointmentListResponse(
        items=[_serialize_admin_appointment(item, service) for item in items],
        meta=_page_meta(page, page_size, total),
    )


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
    payload: AdminAppointmentStatusUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppointmentAdminRead:
    service = AppointmentService(db)
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    item = service.transition(appointment, user, payload.status, AppointmentStatusUpdate(reason=payload.reason))
    _audit(db, user.id, "admin_appointment_status_updated", "Appointment", str(appointment.id), {"status": payload.status.value})
    db.commit()
    db.refresh(item)
    return _serialize_admin_appointment(item, service)


def _integration_page_meta(page: int, page_size: int, total: int) -> IntegrationPageMeta:
    total_pages = max((total + page_size - 1) // page_size, 1)
    return IntegrationPageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


def _operation_result(result) -> IntegrationOperationResultRead:
    return IntegrationOperationResultRead(
        success=result.success,
        code=result.code,
        message=result.message,
        skipped=result.skipped,
        metadata=result.metadata,
        execution_id=result.execution_id,
        duration_ms=result.duration_ms,
    )


def _integration_http_error(exc: IntegrationError) -> HTTPException:
    if isinstance(exc, IntegrationNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, IntegrationConfigurationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    if isinstance(exc, (IntegrationProviderUnsupportedError, IntegrationDisabledError, IntegrationExecutionInProgressError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Integration operation failed")


def _serialize_user_item(user: User) -> AdminUserListItem:
    return AdminUserListItem(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _serialize_user_detail(user: User) -> AdminUserDetail:
    return AdminUserDetail(**_serialize_user_item(user).model_dump(), phone=user.phone, updated_at=user.updated_at)


def _serialize_professional_item(professional: ProfessionalProfile) -> AdminProfessionalListItem:
    return AdminProfessionalListItem(
        id=professional.id,
        user_id=professional.user_id,
        email=professional.user.email,
        full_name=f"{professional.user.first_name} {professional.user.last_name}",
        title=professional.title,
        category_id=professional.category_id,
        consultation_mode=professional.consultation_mode,
        is_public=professional.is_public,
        is_verified=professional.is_verified,
        user_is_active=professional.user.is_active,
        created_at=professional.created_at,
    )


def _serialize_professional_detail(db: Session, professional: ProfessionalProfile) -> AdminProfessionalDetail:
    specialties = list(
        db.scalars(
            select(Specialty.name)
            .join(ProfessionalSpecialty, ProfessionalSpecialty.specialty_id == Specialty.id)
            .where(ProfessionalSpecialty.professional_id == professional.id)
            .order_by(Specialty.name.asc())
        )
    )
    return AdminProfessionalDetail(
        **_serialize_professional_item(professional).model_dump(),
        bio=professional.bio,
        years_experience=professional.years_experience,
        session_duration_minutes=professional.session_duration_minutes,
        price=professional.price,
        city=professional.city,
        country=professional.country,
        specialties=specialties,
    )


def _page_meta(page: int, page_size: int, total: int) -> PageMeta:
    total_pages = max((total + page_size - 1) // page_size, 1)
    return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


def _audit(db: Session, user_id: int, action: str, entity_name: str, entity_id: str, metadata: dict) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            metadata_json=metadata,
            created_at=datetime.now(UTC),
        )
    )


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
