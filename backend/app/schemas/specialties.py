from pydantic import BaseModel

from app.schemas.common import ORMModel


class SpecialtyBase(BaseModel):
    category_id: int
    name: str
    description: str | None = None
    is_active: bool = True


class SpecialtyCreate(SpecialtyBase):
    pass


class SpecialtyUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SpecialtyRead(ORMModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: str | None
    is_active: bool
