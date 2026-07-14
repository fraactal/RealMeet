from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.specialty import Specialty
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.schemas.specialties import SpecialtyCreate, SpecialtyUpdate
from app.utils.strings import slugify


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self) -> list[Category]:
        return list(self.db.scalars(select(Category).order_by(Category.name)))

    def create_category(self, payload: CategoryCreate) -> Category:
        category = Category(name=payload.name, slug=slugify(payload.name), description=payload.description, is_active=payload.is_active)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(self, category: Category, payload: CategoryUpdate) -> Category:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["slug"] = slugify(data["name"])
        for key, value in data.items():
            setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_specialties(self, category_id: int | None = None) -> list[Specialty]:
        query = select(Specialty).order_by(Specialty.name)
        if category_id:
            query = query.where(Specialty.category_id == category_id)
        return list(self.db.scalars(query))

    def create_specialty(self, payload: SpecialtyCreate) -> Specialty:
        specialty = Specialty(
            category_id=payload.category_id,
            name=payload.name,
            slug=slugify(payload.name),
            description=payload.description,
            is_active=payload.is_active,
        )
        self.db.add(specialty)
        self.db.commit()
        self.db.refresh(specialty)
        return specialty

    def update_specialty(self, specialty: Specialty, payload: SpecialtyUpdate) -> Specialty:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["slug"] = slugify(data["name"])
        for key, value in data.items():
            setattr(specialty, key, value)
        self.db.commit()
        self.db.refresh(specialty)
        return specialty
