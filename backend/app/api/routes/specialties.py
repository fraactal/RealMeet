from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.specialty import Specialty
from app.models.user import UserRole
from app.schemas.specialties import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("", response_model=list[SpecialtyRead])
def list_specialties(category_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[SpecialtyRead]:
    items = CatalogService(db).list_specialties(category_id=category_id)
    return [SpecialtyRead.model_validate(item) for item in items]


@router.post("", response_model=SpecialtyRead, dependencies=[Depends(require_roles(UserRole.admin))])
def create_specialty(payload: SpecialtyCreate, db: Session = Depends(get_db)) -> SpecialtyRead:
    item = CatalogService(db).create_specialty(payload)
    return SpecialtyRead.model_validate(item)


@router.patch("/{specialty_id}", response_model=SpecialtyRead, dependencies=[Depends(require_roles(UserRole.admin))])
def update_specialty(specialty_id: int, payload: SpecialtyUpdate, db: Session = Depends(get_db)) -> SpecialtyRead:
    specialty = db.get(Specialty, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    item = CatalogService(db).update_specialty(specialty, payload)
    return SpecialtyRead.model_validate(item)
