import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class AppointmentMeetingStatus(str, enum.Enum):
    pending = "pending"
    provisioning = "provisioning"
    ready = "ready"
    failed = "failed"
    fallback_ready = "fallback_ready"
    cancelled = "cancelled"
    not_required = "not_required"


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

    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile")
    client: Mapped["ClientProfile"] = relationship("ClientProfile")
    meeting_link: Mapped["AppointmentMeeting | None"] = relationship("AppointmentMeeting", back_populates="appointment", uselist=False)


class AppointmentMeeting(Base, TimestampMixin):
    __tablename__ = "appointment_meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False, unique=True)
    provider: Mapped[MeetingProvider | None] = mapped_column(Enum(MeetingProvider, name="meeting_provider"))
    status: Mapped[AppointmentMeetingStatus] = mapped_column(
        Enum(AppointmentMeetingStatus, name="appointment_meeting_status"),
        default=AppointmentMeetingStatus.pending,
        nullable=False,
    )
    meeting_url: Mapped[str | None] = mapped_column(String(500))
    external_meeting_id: Mapped[int | None] = mapped_column(ForeignKey("external_meetings.id"))
    external_reference: Mapped[str | None] = mapped_column(String(255))
    calendar_event_id: Mapped[str | None] = mapped_column(String(255))
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fallback_reason: Mapped[str | None] = mapped_column(String(120))
    error_code: Mapped[str | None] = mapped_column(String(120))
    error_message: Mapped[str | None] = mapped_column(String(500))
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    appointment: Mapped[Appointment] = relationship("Appointment", back_populates="meeting_link")


class AppointmentHistory(Base):
    __tablename__ = "appointment_histories"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
