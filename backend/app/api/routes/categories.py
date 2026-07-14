from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.category import Category
from app.models.user import UserRole
from app.schemas.categories import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    items = CatalogService(db).list_categories()
    return [CategoryRead.model_validate(item) for item in items]


@router.post("", response_model=CategoryRead, dependencies=[Depends(require_roles(UserRole.admin))])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    item = CatalogService(db).create_category(payload)
    return CategoryRead.model_validate(item)


@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_roles(UserRole.admin))])
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryRead:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    item = CatalogService(db).update_category(category, payload)
    return CategoryRead.model_validate(item)
