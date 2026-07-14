from pydantic import BaseModel

from app.schemas.common import ORMModel


class CategoryBase(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryRead(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None
    is_active: bool
