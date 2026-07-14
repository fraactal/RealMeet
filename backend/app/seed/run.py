from datetime import time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.availability import AvailabilityRule
from app.models.category import Category
from app.models.client_profile import ClientProfile
from app.models.professional_profile import ConsultationMode, ProfessionalProfile, ProfessionalSpecialty
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.utils.strings import slugify

logger = get_logger("realmeet.seed")


def get_or_create_user(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
    phone: str,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        logger.info("seed_user_exists email=%s role=%s", email, user.role.value)
        return user

    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone=phone,
    )
    db.add(user)
    db.flush()
    logger.info("seed_user_created email=%s role=%s", email, role.value)
    return user


def get_or_create_category(db: Session, *, name: str, description: str) -> Category:
    slug = slugify(name)
    category = db.scalar(select(Category).where(Category.slug == slug))
    if category:
        logger.info("seed_category_exists slug=%s", slug)
        return category

    category = Category(name=name, slug=slug, description=description)
    db.add(category)
    db.flush()
    logger.info("seed_category_created slug=%s", slug)
    return category


def get_or_create_specialty(db: Session, *, category_id: int, name: str) -> Specialty:
    slug = slugify(name)
    specialty = db.scalar(select(Specialty).where(Specialty.slug == slug))
    if specialty:
        logger.info("seed_specialty_exists slug=%s", slug)
        return specialty

    specialty = Specialty(category_id=category_id, name=name, slug=slug)
    db.add(specialty)
    db.flush()
    logger.info("seed_specialty_created slug=%s", slug)
    return specialty


def ensure_client_profile(db: Session, *, user: User) -> None:
    profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id))
    if profile:
        logger.info("seed_client_profile_exists user_id=%s", user.id)
        return

    db.add(ClientProfile(user_id=user.id, notes="Cliente demo"))
    db.flush()
    logger.info("seed_client_profile_created user_id=%s", user.id)


def ensure_professional_specialty(db: Session, *, professional_id: int, specialty_id: int) -> None:
    link = db.scalar(
        select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == professional_id,
            ProfessionalSpecialty.specialty_id == specialty_id,
        )
    )
    if link:
        logger.info("seed_professional_specialty_exists professional_id=%s specialty_id=%s", professional_id, specialty_id)
        return

    db.add(ProfessionalSpecialty(professional_id=professional_id, specialty_id=specialty_id))
    logger.info("seed_professional_specialty_created professional_id=%s specialty_id=%s", professional_id, specialty_id)


def ensure_availability_rule(db: Session, *, professional_id: int, weekday: int) -> None:
    existing = db.scalar(
        select(AvailabilityRule).where(
            AvailabilityRule.professional_id == professional_id,
            AvailabilityRule.weekday == weekday,
            AvailabilityRule.start_time == time(hour=9, minute=0),
            AvailabilityRule.end_time == time(hour=17, minute=0),
        )
    )
    if existing:
        logger.info("seed_availability_rule_exists professional_id=%s weekday=%s", professional_id, weekday)
        return

    db.add(
        AvailabilityRule(
            professional_id=professional_id,
            weekday=weekday,
            start_time=time(hour=9, minute=0),
            end_time=time(hour=17, minute=0),
            is_active=True,
        )
    )
    logger.info("seed_availability_rule_created professional_id=%s weekday=%s", professional_id, weekday)


def seed() -> None:
    db = SessionLocal()
    try:
        admin = get_or_create_user(
            db,
            email="admin@realmeet.local",
            password="Admin123!",
            first_name="Admin",
            last_name="RealMeet",
            role=UserRole.admin,
            phone="+56000000001",
        )
        client = get_or_create_user(
            db,
            email="client@realmeet.local",
            password="Client123!",
            first_name="Claudia",
            last_name="Paredes",
            role=UserRole.client,
            phone="+56000000002",
        )
        professional_user = get_or_create_user(
            db,
            email="professional@realmeet.local",
            password="Professional123!",
            first_name="Matias",
            last_name="Rojas",
            role=UserRole.professional,
            phone="+56000000003",
        )
        _ = admin

        ensure_client_profile(db, user=client)

        health = get_or_create_category(db, name="Salud", description="Servicios de salud")
        legal = get_or_create_category(db, name="Legal", description="Servicios legales")

        specialties = [
            get_or_create_specialty(db, category_id=health.id, name="Psicologia"),
            get_or_create_specialty(db, category_id=health.id, name="Medicina General"),
            get_or_create_specialty(db, category_id=health.id, name="Nutricion"),
            get_or_create_specialty(db, category_id=legal.id, name="Derecho Laboral"),
            get_or_create_specialty(db, category_id=legal.id, name="Derecho Familiar"),
            get_or_create_specialty(db, category_id=legal.id, name="Derecho Civil"),
        ]

        professional = db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == professional_user.id))
        if professional:
            logger.info("seed_professional_profile_exists user_id=%s professional_id=%s", professional_user.id, professional.id)
        else:
            professional = ProfessionalProfile(
                user_id=professional_user.id,
                category_id=health.id,
                title="Psicologo Clinico",
                bio="Profesional demo orientado a sesiones online y seguimiento inicial.",
                professional_license="PSI-001",
                years_experience=8,
                consultation_mode=ConsultationMode.hybrid,
                session_duration_minutes=60,
                price=Decimal("45000.00"),
                city="Santiago",
                country="Chile",
                is_verified=True,
                is_public=True,
            )
            db.add(professional)
            db.flush()
            logger.info("seed_professional_profile_created user_id=%s professional_id=%s", professional_user.id, professional.id)

        ensure_professional_specialty(db, professional_id=professional.id, specialty_id=specialties[0].id)
        ensure_professional_specialty(db, professional_id=professional.id, specialty_id=specialties[2].id)

        for weekday in range(0, 5):
            ensure_availability_rule(db, professional_id=professional.id, weekday=weekday)

        db.commit()
        logger.info("seed_completed")
    except Exception:
        db.rollback()
        logger.exception("seed_failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
