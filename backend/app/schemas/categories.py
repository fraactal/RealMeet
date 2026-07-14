from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryPublicRead(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None


class CategoryAdminRead(ORMModel):
    id: int
    name: str
    slug: str
    description: str | None
    is_active: bool


CategoryRead = CategoryAdminRead
