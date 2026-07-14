from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.specialty import Specialty
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.schemas.specialties import SpecialtyCreate, SpecialtyUpdate
from app.utils.strings import slugify


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_categories(self, *, active_only: bool = False) -> list[Category]:
        query = select(Category).order_by(Category.name, Category.id)
        if active_only:
            query = query.where(Category.is_active.is_(True))
        return list(self.db.scalars(query))

    def create_category(self, payload: CategoryCreate) -> Category:
        slug = slugify(payload.name)
        self._ensure_unique_category(slug=slug)
        category = Category(name=payload.name.strip(), slug=slug, description=payload.description, is_active=payload.is_active)
        self.db.add(category)
        self._commit_or_duplicate("Category already exists")
        self.db.refresh(category)
        return category

    def update_category(self, category: Category, payload: CategoryUpdate) -> Category:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["name"] = data["name"].strip()
            data["slug"] = slugify(data["name"])
            self._ensure_unique_category(slug=data["slug"], exclude_id=category.id)
        for key, value in data.items():
            setattr(category, key, value)
        self._commit_or_duplicate("Category already exists")
        self.db.refresh(category)
        return category

    def list_specialties(self, category_id: int | None = None, *, active_only: bool = False) -> list[Specialty]:
        query = select(Specialty).join(Category).order_by(Specialty.name, Specialty.id)
        if category_id:
            query = query.where(Specialty.category_id == category_id)
        if active_only:
            query = query.where(Specialty.is_active.is_(True), Category.is_active.is_(True))
        return list(self.db.scalars(query))

    def create_specialty(self, payload: SpecialtyCreate) -> Specialty:
        self._get_category_or_404(payload.category_id)
        slug = slugify(payload.name)
        self._ensure_unique_specialty(slug=slug)
        specialty = Specialty(
            category_id=payload.category_id,
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            is_active=payload.is_active,
        )
        self.db.add(specialty)
        self._commit_or_duplicate("Specialty already exists")
        self.db.refresh(specialty)
        return specialty

    def update_specialty(self, specialty: Specialty, payload: SpecialtyUpdate) -> Specialty:
        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data:
            self._get_category_or_404(data["category_id"])
        if "name" in data:
            data["name"] = data["name"].strip()
            data["slug"] = slugify(data["name"])
            self._ensure_unique_specialty(slug=data["slug"], exclude_id=specialty.id)
        for key, value in data.items():
            setattr(specialty, key, value)
        self._commit_or_duplicate("Specialty already exists")
        self.db.refresh(specialty)
        return specialty

    def _get_category_or_404(self, category_id: int) -> Category:
        category = self.db.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    def _ensure_unique_category(self, *, slug: str, exclude_id: int | None = None) -> None:
        query = select(Category).where(Category.slug == slug)
        if exclude_id is not None:
            query = query.where(Category.id != exclude_id)
        if self.db.scalar(query):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    def _ensure_unique_specialty(self, *, slug: str, exclude_id: int | None = None) -> None:
        query = select(Specialty).where(Specialty.slug == slug)
        if exclude_id is not None:
            query = query.where(Specialty.id != exclude_id)
        if self.db.scalar(query):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specialty already exists")

    def _commit_or_duplicate(self, duplicate_detail: str) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=duplicate_detail) from exc
