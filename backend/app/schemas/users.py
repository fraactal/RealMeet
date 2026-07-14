from datetime import date, datetime

from pydantic import BaseModel

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    role: UserRole


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class UserSelfUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class UserRead(ORMModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClientProfileCreate(BaseModel):
    birth_date: date | None = None
    notes: str | None = None


class ClientSelfProfileRead(BaseModel):
    user: UserRead
    birth_date: date | None
    notes: str | None


class ClientSelfProfileUpdate(UserSelfUpdate):
    birth_date: date | None = None
    notes: str | None = None
