from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.professional_profile import ConsultationMode, ProfessionalProfile, ProfessionalSpecialty
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.schemas.professionals import (
    ProfessionalPublicCategoryRead,
    ProfessionalPublicProfileRead,
    ProfessionalPublicProfileUpdate,
    ProfessionalPublicRead,
    ProfessionalPublicSearchResponse,
    ProfessionalPublicUserRead,
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

    def get_self_public_profile(self, user: User) -> ProfessionalPublicProfileRead:
        profile = self._get_or_create_profile(user)
        return self._serialize_public_profile_owner(profile)

    def update_self_public_profile(self, user: User, payload: ProfessionalPublicProfileUpdate) -> ProfessionalPublicProfileRead:
        profile = self._get_or_create_profile(user)
        data = payload.model_dump(exclude_unset=True)
        if "category_id" in data and data["category_id"] is not None:
            self._get_active_category_or_400(data["category_id"])
        for key, value in data.items():
            setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return self._serialize_public_profile_owner(profile)

    def search_public(
        self,
        search: str | None = None,
        category_id: int | None = None,
        specialty_id: int | None = None,
        consultation_mode: ConsultationMode | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProfessionalPublicSearchResponse:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        id_query = self._public_query(include_options=False).with_only_columns(ProfessionalProfile.id)
        id_query = self._apply_public_filters(
            id_query,
            search=search,
            category_id=category_id,
            specialty_id=specialty_id,
            consultation_mode=consultation_mode,
        )
        total = self.db.scalar(
            id_query.with_only_columns(func.count(func.distinct(ProfessionalProfile.id))).order_by(None)
        ) or 0
        total_pages = (total + page_size - 1) // page_size if total else 0
        page_ids = (
            id_query.distinct()
            .with_only_columns(ProfessionalProfile.id, User.last_name, User.first_name)
            .order_by(User.last_name.asc(), User.first_name.asc(), ProfessionalProfile.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .subquery()
        )
        query = (
            select(ProfessionalProfile)
            .join(page_ids, ProfessionalProfile.id == page_ids.c.id)
            .join(User, ProfessionalProfile.user_id == User.id)
            .options(*self._public_profile_options())
            .order_by(User.last_name.asc(), User.first_name.asc(), ProfessionalProfile.id.asc())
        )
        items = [self._serialize_public_profile(profile) for profile in self.db.scalars(query).unique()]
        return ProfessionalPublicSearchResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    def list_public(
        self,
        search: str | None = None,
        category_id: int | None = None,
        specialty_id: int | None = None,
        consultation_mode: ConsultationMode | None = None,
    ) -> list[ProfessionalPublicRead]:
        return self.search_public(
            search=search,
            category_id=category_id,
            specialty_id=specialty_id,
            consultation_mode=consultation_mode,
        ).items

    def _apply_public_filters(
        self,
        query,
        search: str | None = None,
        category_id: int | None = None,
        specialty_id: int | None = None,
        consultation_mode: ConsultationMode | None = None,
    ):
        if search:
            like = f"%{search.lower()}%"
            query = query.where(
                func.lower(func.concat(User.first_name, " ", User.last_name)).ilike(like)
                | ProfessionalProfile.title.ilike(like)
                | ProfessionalProfile.bio.ilike(like)
            )
        if category_id:
            query = query.where(ProfessionalProfile.category_id == category_id)
        if specialty_id:
            query = query.where(Specialty.id == specialty_id)
        if consultation_mode:
            query = query.where(ProfessionalProfile.consultation_mode == consultation_mode)
        return query

    def get_public(self, professional_id: int) -> ProfessionalPublicRead:
        profile = self.db.scalar(self._public_query().where(ProfessionalProfile.id == professional_id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")
        return self._serialize_public_profile(profile)

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

    def _get_active_category_or_400(self, category_id: int) -> Category:
        category = self.db.scalar(select(Category).where(Category.id == category_id, Category.is_active.is_(True)))
        if not category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
        return category

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

    def _public_profile_options(self):
        return (
            selectinload(ProfessionalProfile.user),
            selectinload(ProfessionalProfile.category),
            selectinload(ProfessionalProfile.specialties)
            .selectinload(ProfessionalSpecialty.specialty)
            .selectinload(Specialty.category),
        )

    def _public_query(self, include_options: bool = True):
        query = (
            select(ProfessionalProfile)
            .join(User, ProfessionalProfile.user_id == User.id)
            .join(Category, ProfessionalProfile.category_id == Category.id)
            .join(ProfessionalSpecialty, ProfessionalSpecialty.professional_id == ProfessionalProfile.id)
            .join(Specialty, ProfessionalSpecialty.specialty_id == Specialty.id)
            .where(
                User.role == UserRole.professional,
                User.is_active.is_(True),
                ProfessionalProfile.is_public.is_(True),
                ProfessionalProfile.title.is_not(None),
                func.length(func.trim(ProfessionalProfile.title)) > 0,
                Category.is_active.is_(True),
                Specialty.is_active.is_(True),
            )
        )
        if include_options:
            query = query.options(*self._public_profile_options())
        return query

    def _serialize_public_profile(self, profile: ProfessionalProfile) -> ProfessionalPublicRead:
        return ProfessionalPublicRead(
            id=profile.id,
            title=profile.title,
            bio=profile.bio,
            years_experience=profile.years_experience,
            consultation_mode=profile.consultation_mode,
            session_duration_minutes=profile.session_duration_minutes,
            city=profile.city,
            country=profile.country,
            user=ProfessionalPublicUserRead(
                id=profile.user.id,
                first_name=profile.user.first_name,
                last_name=profile.user.last_name,
            ),
            category=ProfessionalPublicCategoryRead(
                id=profile.category.id,
                name=profile.category.name,
                slug=profile.category.slug,
            ),
            specialties=self._serialize_specialties(profile),
        )

    @staticmethod
    def _serialize_public_profile_owner(profile: ProfessionalProfile) -> ProfessionalPublicProfileRead:
        return ProfessionalPublicProfileRead(
            id=profile.id,
            title=profile.title,
            bio=profile.bio,
            years_experience=profile.years_experience,
            consultation_mode=profile.consultation_mode,
            session_duration_minutes=profile.session_duration_minutes,
            city=profile.city,
            country=profile.country,
            category_id=profile.category_id,
            is_public=profile.is_public,
        )
