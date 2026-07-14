from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.specialty import Specialty
from app.schemas.specialties import SpecialtyAdminRead, SpecialtyCreate, SpecialtyPublicRead, SpecialtyUpdate
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("", response_model=list[SpecialtyPublicRead])
def list_specialties(category_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[SpecialtyPublicRead]:
    items = CatalogService(db).list_specialties(category_id=category_id, active_only=True)
    return [SpecialtyPublicRead.model_validate(item) for item in items]


@router.post("", response_model=SpecialtyAdminRead, dependencies=[Depends(require_admin)])
def create_specialty(payload: SpecialtyCreate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    item = CatalogService(db).create_specialty(payload)
    return SpecialtyAdminRead.model_validate(item)


@router.patch("/{specialty_id}", response_model=SpecialtyAdminRead, dependencies=[Depends(require_admin)])
def update_specialty(specialty_id: int, payload: SpecialtyUpdate, db: Session = Depends(get_db)) -> SpecialtyAdminRead:
    specialty = db.get(Specialty, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Specialty not found")
    item = CatalogService(db).update_specialty(specialty, payload)
    return SpecialtyAdminRead.model_validate(item)
