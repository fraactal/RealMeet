from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class ExternalCalendarInfo:
    external_calendar_id: str
    name: str
    description: str | None
    timezone: str
    is_primary: bool = False


@dataclass(frozen=True)
class BusyPeriod:
    starts_at: datetime
    ends_at: datetime
    source_calendar_id: str
    external_event_id: str
    availability: str


@dataclass(frozen=True)
class ExternalCalendarEventInput:
    calendar_id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    description: str | None = None


@dataclass(frozen=True)
class ExternalCalendarEventResult:
    external_event_id: str
    calendar_id: str
    status: str


@dataclass(frozen=True)
class CalendarProviderHealth:
    healthy: bool
    code: str
    message: str


class ExternalCalendarProviderClient(Protocol):
    def list_calendars(self) -> list[ExternalCalendarInfo]: ...

    def list_busy_periods(self, calendar_id: str, starts_at: datetime, ends_at: datetime) -> list[BusyPeriod]: ...

    def create_event(self, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult: ...

    def update_event(self, external_event_id: str, payload: ExternalCalendarEventInput) -> ExternalCalendarEventResult: ...

    def delete_event(self, calendar_id: str, external_event_id: str) -> ExternalCalendarEventResult: ...

    def health_check(self) -> CalendarProviderHealth: ...
