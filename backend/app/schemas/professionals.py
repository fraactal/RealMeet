from decimal import Decimal

from pydantic import BaseModel

from app.models.professional_profile import ConsultationMode
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


class ProfessionalPublicRead(BaseModel):
    id: int
    title: str | None
    bio: str | None
    consultation_mode: ConsultationMode
    session_duration_minutes: int
    price: Decimal | None
    city: str | None
    country: str | None
    user: UserRead
    category_name: str | None = None
    specialties: list[str] = []
