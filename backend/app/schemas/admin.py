from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus
from app.models.professional_profile import ConsultationMode
from app.models.user import UserRole
from app.schemas.appointments import AppointmentAdminRead


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class AdminUserListItem(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserDetail(AdminUserListItem):
    phone: str | None
    updated_at: datetime


class AdminUserUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    meta: PageMeta


class AdminProfessionalListItem(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str
    title: str | None
    category_id: int | None
    consultation_mode: ConsultationMode
    is_public: bool
    is_verified: bool
    user_is_active: bool
    created_at: datetime


class AdminProfessionalDetail(AdminProfessionalListItem):
    bio: str | None
    years_experience: int | None
    session_duration_minutes: int
    price: Decimal | None
    city: str | None
    country: str | None
    specialties: list[str]


class AdminProfessionalUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = Field(default=None, max_length=140)
    bio: str | None = None
    years_experience: int | None = None
    consultation_mode: ConsultationMode | None = None
    session_duration_minutes: int | None = Field(default=None, ge=15, le=240)
    price: Decimal | None = None
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    is_verified: bool | None = None
    is_public: bool | None = None
    user_is_active: bool | None = None


class AdminProfessionalListResponse(BaseModel):
    items: list[AdminProfessionalListItem]
    meta: PageMeta


class AdminAppointmentListResponse(BaseModel):
    items: list[AppointmentAdminRead]
    meta: PageMeta


class AdminAppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    reason: str | None = Field(default=None, max_length=255)
