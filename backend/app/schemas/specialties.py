from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SpecialtyBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True


class SpecialtyCreate(SpecialtyBase):
    pass


class SpecialtyUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SpecialtyPublicRead(ORMModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: str | None


class SpecialtyAdminRead(ORMModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: str | None
    is_active: bool


SpecialtyRead = SpecialtyAdminRead
