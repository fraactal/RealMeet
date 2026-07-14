from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.professional_profile import ProfessionalProfile, ProfessionalSpecialty
from app.models.user import User, UserRole
from app.schemas.professionals import ProfessionalProfileCreate, ProfessionalProfileUpdate


class ProfessionalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_profile(self, user: User, payload: ProfessionalProfileCreate | ProfessionalProfileUpdate) -> ProfessionalProfile:
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if not profile:
            profile = ProfessionalProfile(user_id=user.id)
            self.db.add(profile)
            self.db.flush()

        data = payload.model_dump(exclude={"specialty_ids"})
        for key, value in data.items():
            setattr(profile, key, value)

        self.db.query(ProfessionalSpecialty).filter(ProfessionalSpecialty.professional_id == profile.id).delete()
        for specialty_id in payload.specialty_ids:
            self.db.add(ProfessionalSpecialty(professional_id=profile.id, specialty_id=specialty_id))

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_public(self, search: str | None = None, category_id: int | None = None, specialty_id: int | None = None) -> list[ProfessionalProfile]:
        query = (
            select(ProfessionalProfile)
            .options(
                selectinload(ProfessionalProfile.user),
                selectinload(ProfessionalProfile.category),
                selectinload(ProfessionalProfile.specialties).selectinload(ProfessionalSpecialty.specialty),
            )
            .join(User, ProfessionalProfile.user_id == User.id)
            .where(User.role == UserRole.professional, ProfessionalProfile.is_public.is_(True), User.is_active.is_(True))
        )
        if search:
            like = f"%{search.lower()}%"
            query = query.where(
                func.lower(func.concat(User.first_name, " ", User.last_name)).ilike(like)
                | ProfessionalProfile.title.ilike(like)
            )
        if category_id:
            query = query.where(ProfessionalProfile.category_id == category_id)
        if specialty_id:
            query = query.join(ProfessionalSpecialty).where(ProfessionalSpecialty.specialty_id == specialty_id)
        return list(self.db.scalars(query).unique())
