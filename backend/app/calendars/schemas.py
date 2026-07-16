from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.external_calendar import CalendarConflictPolicy, ExternalCalendarProvider, ExternalCalendarSyncStatus


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExternalCalendarCreate(StrictBaseModel):
    provider: ExternalCalendarProvider = ExternalCalendarProvider.fake
    integration_id: int | None = None
    external_calendar_id: str = Field(min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=300)
    timezone: str = Field(default="America/Santiago", max_length=80)
    read_enabled: bool = True
    write_enabled: bool = False
    conflict_check_enabled: bool = True
    is_primary: bool = False

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid timezone") from exc
        return value

    @field_validator("external_calendar_id")
    @classmethod
    def validate_external_id(cls, value: str) -> str:
        lowered = value.lower()
        if any(item in lowered for item in ["secret", "token", "password", "credential"]):
            raise ValueError("external_calendar_id cannot contain secret material")
        return value


class ExternalCalendarUpdate(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=300)
    timezone: str | None = Field(default=None, max_length=80)
    read_enabled: bool | None = None
    write_enabled: bool | None = None
    conflict_check_enabled: bool | None = None
    is_primary: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid timezone") from exc
        return value


class ExternalCalendarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    professional_id: int
    integration_id: int | None
    provider: ExternalCalendarProvider
    external_calendar_id: str
    name: str
    description: str | None
    timezone: str
    read_enabled: bool
    write_enabled: bool
    conflict_check_enabled: bool
    is_primary: bool
    enabled: bool
    sync_status: ExternalCalendarSyncStatus
    last_synced_at: datetime | None
    last_sync_error_at: datetime | None
    last_sync_error_code: str | None
    created_at: datetime
    updated_at: datetime


class CalendarSyncSettingsUpdate(StrictBaseModel):
    sync_enabled: bool | None = None
    conflict_policy: CalendarConflictPolicy | None = None
    lookback_days: int | None = Field(default=None, ge=0, le=30)
    lookahead_days: int | None = Field(default=None, ge=1, le=365)
    default_external_calendar_id: int | None = None


class CalendarSyncSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    professional_id: int
    sync_enabled: bool
    conflict_policy: CalendarConflictPolicy
    lookback_days: int
    lookahead_days: int
    default_external_calendar_id: int | None
    created_at: datetime
    updated_at: datetime


class CalendarProviderHealthRead(BaseModel):
    healthy: bool
    code: str
    message: str


class ExternalCalendarInfoRead(BaseModel):
    external_calendar_id: str
    name: str
    description: str | None
    timezone: str
    is_primary: bool
    read_only: bool = False


class BusyPeriodRead(BaseModel):
    starts_at: datetime
    ends_at: datetime
    source_calendar_id: str
    external_event_id: str
    availability: str


class ExternalCalendarTestRead(BaseModel):
    health: CalendarProviderHealthRead
    calendars: list[ExternalCalendarInfoRead] = Field(default_factory=list)
    busy_periods: list[BusyPeriodRead] = Field(default_factory=list)
    created_event_id: str | None = None
    deleted_event_id: str | None = None


class CalendarConflictCheckRequest(StrictBaseModel):
    starts_at: datetime
    ends_at: datetime


class CalendarConflictItemRead(BaseModel):
    calendar_id: int
    external_calendar_id: str
    starts_at: datetime
    ends_at: datetime
    availability: str


class CalendarConflictCheckRead(BaseModel):
    has_conflict: bool
    status: str
    candidate: dict[str, datetime]
    conflicts: list[CalendarConflictItemRead] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
