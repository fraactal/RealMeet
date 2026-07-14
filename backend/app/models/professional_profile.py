import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class ConsultationMode(str, enum.Enum):
    online = "online"
    presencial = "presencial"
    hybrid = "hybrid"


class ProfessionalProfile(Base, TimestampMixin):
    __tablename__ = "professional_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    title: Mapped[str | None] = mapped_column(String(140))
    bio: Mapped[str | None] = mapped_column(Text)
    professional_license: Mapped[str | None] = mapped_column(String(80))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    consultation_mode: Mapped[ConsultationMode] = mapped_column(
        Enum(ConsultationMode, name="consultation_mode"),
        default=ConsultationMode.online,
        nullable=False,
    )
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="professional_profile")
    category = relationship("Category", back_populates="professionals")
    specialties = relationship("ProfessionalSpecialty", back_populates="professional", cascade="all, delete-orphan")
    availability_rules = relationship("AvailabilityRule", back_populates="professional", cascade="all, delete-orphan")
    availability_blocks = relationship("AvailabilityBlock", back_populates="professional", cascade="all, delete-orphan")


class ProfessionalSpecialty(Base):
    __tablename__ = "professional_specialties"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id"), nullable=False)
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id"), nullable=False)

    professional = relationship("ProfessionalProfile", back_populates="specialties")
    specialty = relationship("Specialty", back_populates="professional_links")
