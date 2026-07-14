from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.professional_profile import ProfessionalProfile, ProfessionalSpecialty
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.schemas.professionals import (
    ProfessionalProfileCreate,
    ProfessionalProfileUpdate,
    ProfessionalSpecialtyRead,
    ProfessionalSpecialtyUpdate,
    ProfessionalSelfProfileRead,
    ProfessionalSelfProfileUpdate,
)
from app.schemas.users import UserRead


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

    def get_self_profile(self, user: User) -> ProfessionalSelfProfileRead:
        profile = self._get_or_create_profile(user)
        return self._serialize_self_profile(user, profile)

    def upsert_self_profile(self, user: User, payload: ProfessionalSelfProfileUpdate) -> ProfessionalSelfProfileRead:
        profile = self._get_or_create_profile(user)
        data = payload.model_dump(exclude_unset=True)
        for key in ("first_name", "last_name", "phone"):
            if key in data:
                setattr(user, key, data[key])
        for key in (
            "title",
            "bio",
            "years_experience",
            "consultation_mode",
            "session_duration_minutes",
            "address",
            "city",
            "country",
        ):
            if key in data:
                setattr(profile, key, data[key])
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(profile)
        return self._serialize_self_profile(user, profile)

    def list_self_specialties(self, user: User) -> list[ProfessionalSpecialtyRead]:
        profile = self._get_or_create_profile(user)
        profile = self._get_profile_with_specialties(profile.id)
        return self._serialize_specialties(profile)

    def update_self_specialties(self, user: User, payload: ProfessionalSpecialtyUpdate) -> list[ProfessionalSpecialtyRead]:
        profile = self._get_or_create_profile(user)
        specialty_ids = payload.specialty_ids
        if len(specialty_ids) != len(set(specialty_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate specialties are not allowed")

        specialties = self._get_active_specialties_or_400(specialty_ids)
        self.db.query(ProfessionalSpecialty).filter(ProfessionalSpecialty.professional_id == profile.id).delete()
        for specialty in specialties:
            self.db.add(ProfessionalSpecialty(professional_id=profile.id, specialty_id=specialty.id))
        self.db.commit()
        profile = self._get_profile_with_specialties(profile.id)
        return self._serialize_specialties(profile)

    def _get_or_create_profile(self, user: User) -> ProfessionalProfile:
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if profile:
            return profile
        profile = ProfessionalProfile(user_id=user.id)
        self.db.add(profile)
        self.db.flush()
        return profile

    @staticmethod
    def _serialize_self_profile(user: User, profile: ProfessionalProfile) -> ProfessionalSelfProfileRead:
        return ProfessionalSelfProfileRead(
            id=profile.id,
            user=UserRead.model_validate(user),
            title=profile.title,
            bio=profile.bio,
            years_experience=profile.years_experience,
            consultation_mode=profile.consultation_mode,
            session_duration_minutes=profile.session_duration_minutes,
            address=profile.address,
            city=profile.city,
            country=profile.country,
        )

    def _get_profile_with_specialties(self, profile_id: int) -> ProfessionalProfile:
        return self.db.scalar(
            select(ProfessionalProfile)
            .where(ProfessionalProfile.id == profile_id)
            .options(
                selectinload(ProfessionalProfile.specialties)
                .selectinload(ProfessionalSpecialty.specialty)
                .selectinload(Specialty.category)
            )
        )

    def _get_active_specialties_or_400(self, specialty_ids: list[int]) -> list[Specialty]:
        if not specialty_ids:
            return []
        specialties = list(
            self.db.scalars(
                select(Specialty)
                .where(Specialty.id.in_(specialty_ids), Specialty.is_active.is_(True))
                .options(selectinload(Specialty.category))
            )
        )
        if len(specialties) != len(specialty_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specialty not found or inactive")
        inactive_category = next((specialty for specialty in specialties if not specialty.category.is_active), None)
        if inactive_category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specialty category is inactive")
        by_id = {specialty.id: specialty for specialty in specialties}
        return [by_id[specialty_id] for specialty_id in specialty_ids]

    @staticmethod
    def _serialize_specialties(profile: ProfessionalProfile) -> list[ProfessionalSpecialtyRead]:
        items = []
        for link in sorted(profile.specialties, key=lambda item: item.specialty.name):
            specialty = link.specialty
            if not specialty.is_active or not specialty.category.is_active:
                continue
            items.append(
                ProfessionalSpecialtyRead(
                    id=specialty.id,
                    name=specialty.name,
                    slug=specialty.slug,
                    category_id=specialty.category_id,
                    category_name=specialty.category.name,
                )
            )
        return items

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
