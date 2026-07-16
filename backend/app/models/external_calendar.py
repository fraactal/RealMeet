import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class ExternalCalendarProvider(str, enum.Enum):
    fake = "fake"
    google_calendar = "google_calendar"
    microsoft_365 = "microsoft_365"


class ExternalCalendarSyncStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    disabled = "disabled"
    error = "error"


class CalendarConflictPolicy(str, enum.Enum):
    internal_only = "internal_only"
    external_busy_blocks = "external_busy_blocks"
    disabled = "disabled"


class ExternalConflictFailurePolicy(str, enum.Enum):
    fail_closed = "fail_closed"
    fail_open = "fail_open"


class ExternalCalendar(Base, TimestampMixin):
    __tablename__ = "external_calendars"
    __table_args__ = (
        UniqueConstraint("professional_id", "provider", "external_calendar_id", name="uq_external_calendar_professional_provider_external"),
        Index("ix_external_calendars_professional_id", "professional_id"),
        Index("ix_external_calendars_integration_id", "integration_id"),
        Index("ix_external_calendars_enabled", "enabled"),
        Index(
            "uq_external_calendar_primary_professional_provider",
            "professional_id",
            "provider",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False)
    integration_id: Mapped[int | None] = mapped_column(ForeignKey("integrations.id", ondelete="SET NULL"))
    provider: Mapped[ExternalCalendarProvider] = mapped_column(Enum(ExternalCalendarProvider, name="external_calendar_provider"), nullable=False)
    external_calendar_id: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="America/Santiago")
    read_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    write_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conflict_check_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sync_status: Mapped[ExternalCalendarSyncStatus] = mapped_column(
        Enum(ExternalCalendarSyncStatus, name="external_calendar_sync_status"),
        default=ExternalCalendarSyncStatus.pending,
        nullable=False,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_error_code: Mapped[str | None] = mapped_column(String(100))

    professional = relationship("ProfessionalProfile")
    integration = relationship("Integration")


class CalendarSyncSettings(Base, TimestampMixin):
    __tablename__ = "calendar_sync_settings"

    professional_id: Mapped[int] = mapped_column(ForeignKey("professional_profiles.id", ondelete="CASCADE"), primary_key=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conflict_policy: Mapped[CalendarConflictPolicy] = mapped_column(
        Enum(CalendarConflictPolicy, name="calendar_conflict_policy"),
        default=CalendarConflictPolicy.internal_only,
        nullable=False,
    )
    external_conflict_failure_policy: Mapped[ExternalConflictFailurePolicy] = mapped_column(
        Enum(ExternalConflictFailurePolicy, name="external_conflict_failure_policy"),
        default=ExternalConflictFailurePolicy.fail_closed,
        nullable=False,
    )
    lookback_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lookahead_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    default_external_calendar_id: Mapped[int | None] = mapped_column(ForeignKey("external_calendars.id", ondelete="SET NULL"))

    professional = relationship("ProfessionalProfile")
    default_external_calendar = relationship("ExternalCalendar")
