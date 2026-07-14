from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_professional
from app.db.session import get_db
from app.schemas.professionals import (
    ProfessionalPublicProfileRead,
    ProfessionalPublicProfileUpdate,
    ProfessionalPublicRead,
    ProfessionalSpecialtyRead,
    ProfessionalSpecialtyUpdate,
    ProfessionalSelfProfileRead,
    ProfessionalSelfProfileUpdate,
)
from app.services.professionals import ProfessionalService

router = APIRouter()


@router.get("", response_model=list[ProfessionalPublicRead])
def list_professionals(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    specialty_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProfessionalPublicRead]:
    return ProfessionalService(db).list_public(search=search, category_id=category_id, specialty_id=specialty_id)


@router.get("/{professional_id}", response_model=ProfessionalPublicRead)
def get_professional(professional_id: int, db: Session = Depends(get_db)) -> ProfessionalPublicRead:
    return ProfessionalService(db).get_public(professional_id)


@router.post("/profile", response_model=ProfessionalSelfProfileRead, dependencies=[Depends(require_professional)])
def create_profile(
    payload: ProfessionalSelfProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfessionalSelfProfileRead:
    return ProfessionalService(db).upsert_self_profile(user, payload)


@router.get("/me/profile", response_model=ProfessionalSelfProfileRead, dependencies=[Depends(require_professional)])
def get_my_profile(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalSelfProfileRead:
    return ProfessionalService(db).get_self_profile(user)


@router.patch("/me/profile", response_model=ProfessionalSelfProfileRead, dependencies=[Depends(require_professional)])
def update_profile(
    payload: ProfessionalSelfProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfessionalSelfProfileRead:
    return ProfessionalService(db).upsert_self_profile(user, payload)


@router.get("/me/specialties", response_model=list[ProfessionalSpecialtyRead], dependencies=[Depends(require_professional)])
def list_my_specialties(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProfessionalSpecialtyRead]:
    return ProfessionalService(db).list_self_specialties(user)


@router.patch("/me/specialties", response_model=list[ProfessionalSpecialtyRead], dependencies=[Depends(require_professional)])
def update_my_specialties(
    payload: ProfessionalSpecialtyUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProfessionalSpecialtyRead]:
    return ProfessionalService(db).update_self_specialties(user, payload)


@router.get("/me/public-profile", response_model=ProfessionalPublicProfileRead, dependencies=[Depends(require_professional)])
def get_my_public_profile(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalPublicProfileRead:
    return ProfessionalService(db).get_self_public_profile(user)


@router.patch("/me/public-profile", response_model=ProfessionalPublicProfileRead, dependencies=[Depends(require_professional)])
def update_my_public_profile(
    payload: ProfessionalPublicProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfessionalPublicProfileRead:
    return ProfessionalService(db).update_self_public_profile(user, payload)
