from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.professional_profile import ProfessionalProfile, ProfessionalSpecialty
from app.models.user import UserRole
from app.schemas.professionals import ProfessionalProfileCreate, ProfessionalProfileRead, ProfessionalProfileUpdate, ProfessionalPublicRead
from app.schemas.users import UserRead
from app.services.professionals import ProfessionalService

router = APIRouter()


@router.get("", response_model=list[ProfessionalPublicRead])
def list_professionals(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    specialty_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProfessionalPublicRead]:
    items = ProfessionalService(db).list_public(search=search, category_id=category_id, specialty_id=specialty_id)
    return [
        ProfessionalPublicRead(
            id=item.id,
            title=item.title,
            bio=item.bio,
            consultation_mode=item.consultation_mode,
            session_duration_minutes=item.session_duration_minutes,
            price=item.price,
            city=item.city,
            country=item.country,
            user=UserRead.model_validate(item.user),
            category_name=item.category.name if item.category else None,
            specialties=[link.specialty.name for link in item.specialties],
        )
        for item in items
    ]


@router.get("/{professional_id}", response_model=ProfessionalPublicRead)
def get_professional(professional_id: int, db: Session = Depends(get_db)) -> ProfessionalPublicRead:
    item = db.get(ProfessionalProfile, professional_id)
    if not item or not item.user.is_active:
        raise HTTPException(status_code=404, detail="Professional not found")
    return ProfessionalPublicRead(
        id=item.id,
        title=item.title,
        bio=item.bio,
        consultation_mode=item.consultation_mode,
        session_duration_minutes=item.session_duration_minutes,
        price=item.price,
        city=item.city,
        country=item.country,
        user=UserRead.model_validate(item.user),
        category_name=item.category.name if item.category else None,
        specialties=[link.specialty.name for link in item.specialties],
    )


@router.post("/profile", response_model=ProfessionalProfileRead, dependencies=[Depends(require_roles(UserRole.professional))])
def create_profile(payload: ProfessionalProfileCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalProfileRead:
    profile = ProfessionalService(db).upsert_profile(user, payload)
    return ProfessionalProfileRead.model_validate(profile)


@router.get("/me/profile", response_model=ProfessionalProfileRead, dependencies=[Depends(require_roles(UserRole.professional))])
def get_my_profile(user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalProfileRead:
    profile = db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfessionalProfileRead.model_validate(profile)


@router.patch("/me/profile", response_model=ProfessionalProfileRead, dependencies=[Depends(require_roles(UserRole.professional))])
def update_profile(payload: ProfessionalProfileUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> ProfessionalProfileRead:
    profile = ProfessionalService(db).upsert_profile(user, payload)
    return ProfessionalProfileRead.model_validate(profile)
