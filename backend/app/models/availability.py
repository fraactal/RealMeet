import enum
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class AvailabilityBlockType(str, enum.Enum):
    blocked = "blocked"
    extra_available = "extra_available"


class AvailabilityRule(Base, TimestampMixin):
    __tablename__ = "availability_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    professional = relationship("ProfessionalProfile", back_populates="availability_rules")


class AvailabilityBlock(Base, TimestampMixin):
    __tablename__ = "availability_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id"), nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[AvailabilityBlockType] = mapped_column(
        Enum(AvailabilityBlockType, name="availability_block_type"),
        default=AvailabilityBlockType.blocked,
        nullable=False,
    )

    professional = relationship("ProfessionalProfile", back_populates="availability_blocks")
