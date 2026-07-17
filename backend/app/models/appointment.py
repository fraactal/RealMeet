import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.models.professional_profile import ConsultationMode


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    pending_payment = "pending_payment"
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


class AppointmentNotificationEvent(str, enum.Enum):
    appointment_confirmed = "appointment_confirmed"
    appointment_updated = "appointment_updated"
    appointment_cancelled = "appointment_cancelled"
    appointment_reminder = "appointment_reminder"
    meeting_ready = "meeting_ready"


class AppointmentNotificationChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"


class AppointmentNotificationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    accepted = "accepted"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"
    fallback_sent = "fallback_sent"


class AppointmentExternalCalendarEventStatus(str, enum.Enum):
    pending = "pending"
    created = "created"
    updated = "updated"
    cancelled = "cancelled"
    failed = "failed"
    reconcile_required = "reconcile_required"


class AppointmentExternalCalendarSyncAction(str, enum.Enum):
    create = "create"
    update = "update"
    cancel = "cancel"
    none = "none"


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
    consultation_mode: Mapped[ConsultationMode] = mapped_column(Enum(ConsultationMode, name="consultation_mode"))
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
    external_calendar_events: Mapped[list["AppointmentExternalCalendarEvent"]] = relationship("AppointmentExternalCalendarEvent", back_populates="appointment")


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


class AppointmentExternalCalendarEvent(Base, TimestampMixin):
    __tablename__ = "appointment_external_calendar_events"
    __table_args__ = (
        UniqueConstraint("appointment_id", "external_calendar_id", name="uq_appointment_external_calendar_event"),
        Index("ix_appointment_external_calendar_events_appointment", "appointment_id"),
        Index("ix_appointment_external_calendar_events_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    external_calendar_id: Mapped[int] = mapped_column(ForeignKey("external_calendars.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[AppointmentExternalCalendarEventStatus] = mapped_column(
        Enum(AppointmentExternalCalendarEventStatus, name="appointment_external_calendar_event_status"),
        default=AppointmentExternalCalendarEventStatus.pending,
        nullable=False,
    )
    sync_action: Mapped[AppointmentExternalCalendarSyncAction] = mapped_column(
        Enum(AppointmentExternalCalendarSyncAction, name="appointment_external_calendar_sync_action"),
        default=AppointmentExternalCalendarSyncAction.create,
        nullable=False,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(120))
    last_error_message: Mapped[str | None] = mapped_column(String(500))

    appointment: Mapped[Appointment] = relationship("Appointment", back_populates="external_calendar_events")


class AppointmentNotification(Base, TimestampMixin):
    __tablename__ = "appointment_notifications"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_appointment_notifications_idempotency_key"),
        Index("ix_appointment_notifications_appointment_event", "appointment_id", "event_type"),
        Index("ix_appointment_notifications_status_scheduled", "status", "scheduled_for"),
        Index("ix_appointment_notifications_whatsapp_message", "whatsapp_message_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[AppointmentNotificationEvent] = mapped_column(
        Enum(AppointmentNotificationEvent, name="appointment_notification_event"),
        nullable=False,
    )
    channel: Mapped[AppointmentNotificationChannel] = mapped_column(
        Enum(AppointmentNotificationChannel, name="appointment_notification_channel"),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[AppointmentNotificationStatus] = mapped_column(
        Enum(AppointmentNotificationStatus, name="appointment_notification_status"),
        default=AppointmentNotificationStatus.pending,
        nullable=False,
    )
    whatsapp_message_id: Mapped[int | None] = mapped_column(ForeignKey("whatsapp_messages.id", ondelete="SET NULL"))
    email_reference: Mapped[str | None] = mapped_column(String(180))
    template_id: Mapped[int | None] = mapped_column(ForeignKey("whatsapp_templates.id"))
    recipient_masked: Mapped[str | None] = mapped_column(String(80))
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(220), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(String(300))

    appointment: Mapped[Appointment] = relationship("Appointment")
    whatsapp_message = relationship("WhatsAppMessage")
    template = relationship("WhatsAppTemplate")


class AppointmentHistory(Base):
    __tablename__ = "appointment_histories"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
