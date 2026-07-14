from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.category import Category
from app.schemas.categories import CategoryAdminRead, CategoryCreate, CategoryPublicRead, CategoryUpdate
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("", response_model=list[CategoryPublicRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryPublicRead]:
    items = CatalogService(db).list_categories(active_only=True)
    return [CategoryPublicRead.model_validate(item) for item in items]


@router.post("", response_model=CategoryAdminRead, dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    item = CatalogService(db).create_category(payload)
    return CategoryAdminRead.model_validate(item)


@router.patch("/{category_id}", response_model=CategoryAdminRead, dependencies=[Depends(require_admin)])
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryAdminRead:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    item = CatalogService(db).update_category(category, payload)
    return CategoryAdminRead.model_validate(item)
