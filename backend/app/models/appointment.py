import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.models.professional_profile import ConsultationMode


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class MeetingProvider(str, enum.Enum):
    mock = "mock"
    google_meet = "google_meet"
    zoom = "zoom"
    manual = "manual"


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    specialty_id: Mapped[int | None] = mapped_column(ForeignKey("specialties.id"))
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.pending,
        nullable=False,
    )
    consultation_mode: Mapped[ConsultationMode] = mapped_column(Enum(ConsultationMode, name="appointment_consultation_mode"))
    meeting_provider: Mapped[MeetingProvider | None] = mapped_column(Enum(MeetingProvider, name="meeting_provider"))
    meeting_url: Mapped[str | None] = mapped_column(String(255))
    external_meeting_id: Mapped[str | None] = mapped_column(String(120))
    calendar_event_id: Mapped[str | None] = mapped_column(String(120))
    cancellation_reason: Mapped[str | None] = mapped_column(String(255))
    client_notes: Mapped[str | None] = mapped_column(Text)
    professional_private_notes: Mapped[str | None] = mapped_column(Text)


class AppointmentHistory(Base):
    __tablename__ = "appointment_histories"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
