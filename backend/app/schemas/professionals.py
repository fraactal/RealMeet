from decimal import Decimal

from pydantic import BaseModel

from app.models.professional_profile import ConsultationMode, PaymentTiming
from app.schemas.common import ORMModel
from app.schemas.users import UserRead, UserSelfUpdate


class ProfessionalProfileCreate(BaseModel):
    category_id: int | None = None
    title: str | None = None
    bio: str | None = None
    professional_license: str | None = None
    years_experience: int | None = None
    consultation_mode: ConsultationMode = ConsultationMode.online
    session_duration_minutes: int = 60
    price: Decimal | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    is_public: bool = True
    specialty_ids: list[int] = []


class ProfessionalProfileUpdate(ProfessionalProfileCreate):
    pass


class ProfessionalProfileRead(ORMModel):
    id: int
    user_id: int
    category_id: int | None
    title: str | None
    bio: str | None
    professional_license: str | None
    years_experience: int | None
    consultation_mode: ConsultationMode
    session_duration_minutes: int
    price: Decimal | None
    address: str | None
    city: str | None
    country: str | None
    is_verified: bool
    is_public: bool


class ProfessionalSelfProfileRead(BaseModel):
    id: int
    user: UserRead
    title: str | None
    bio: str | None
    years_experience: int | None
    consultation_mode: ConsultationMode
    session_duration_minutes: int
    address: str | None
    city: str | None
    country: str | None


class ProfessionalSelfProfileUpdate(UserSelfUpdate):
    title: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    consultation_mode: ConsultationMode | None = None
    session_duration_minutes: int | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None


class ProfessionalSpecialtyRead(BaseModel):
    id: int
    name: str
    slug: str
    category_id: int
    category_name: str


class ProfessionalSpecialtyUpdate(BaseModel):
    specialty_ids: list[int]


class ProfessionalPublicUserRead(BaseModel):
    id: int
    first_name: str
    last_name: str


class ProfessionalPublicCategoryRead(BaseModel):
    id: int
    name: str
    slug: str


class ProfessionalPublicRead(BaseModel):
    id: int
    title: str | None
    bio: str | None
    years_experience: int | None
    consultation_mode: ConsultationMode
    session_duration_minutes: int
    price: Decimal | None
    payment_timing: PaymentTiming
    payment_amount: Decimal | None
    payment_currency: str
    payment_expiration_minutes: int
    city: str | None
    country: str | None
    user: ProfessionalPublicUserRead
    category: ProfessionalPublicCategoryRead
    specialties: list[ProfessionalSpecialtyRead] = []


class ProfessionalPublicSearchResponse(BaseModel):
    items: list[ProfessionalPublicRead]
    page: int
    page_size: int
    total: int
    total_pages: int


class ProfessionalPublicProfileRead(BaseModel):
    id: int
    title: str | None
    bio: str | None
    years_experience: int | None
    consultation_mode: ConsultationMode
    session_duration_minutes: int
    price: Decimal | None
    payment_timing: PaymentTiming
    payment_amount: Decimal | None
    payment_currency: str
    payment_expiration_minutes: int
    city: str | None
    country: str | None
    category_id: int | None
    is_public: bool


class ProfessionalPublicProfileUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    consultation_mode: ConsultationMode | None = None
    session_duration_minutes: int | None = None
    city: str | None = None
    country: str | None = None
    is_public: bool | None = None
