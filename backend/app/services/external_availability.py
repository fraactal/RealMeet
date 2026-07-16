from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calendars.conflicts import BLOCKING_AVAILABILITY
from app.calendars.contracts import BusyPeriod
from app.calendars.service import ExternalCalendarService
from app.models.external_calendar import CalendarConflictPolicy, ExternalCalendar, ExternalConflictFailurePolicy


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExternalAvailabilityResult:
    status: str
    busy_periods: list[BusyPeriod] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    checked: bool = False

    @property
    def provider_unavailable(self) -> bool:
        return bool(self.errors)


class ExternalAvailabilityUnavailable(Exception):
    pass


class ExternalAvailabilityConflict(Exception):
    pass


class ExternalAvailabilityService:
    def __init__(self, db: Session, calendar_service: ExternalCalendarService | None = None) -> None:
        self.db = db
        self.calendar_service = calendar_service or ExternalCalendarService(db)

    def filter_slots(self, professional_id: int, slots: list[dict], starts_at: datetime, ends_at: datetime) -> list[dict]:
        if not slots:
            return slots
        result = self.collect_busy_periods(professional_id, starts_at, ends_at)
        self._log(professional_id, starts_at, ends_at, result)
        if result.provider_unavailable and self._failure_policy(professional_id) == ExternalConflictFailurePolicy.fail_closed:
            return []
        if not result.busy_periods:
            return slots
        return [
            slot
            for slot in slots
            if not any(self._ranges_overlap(slot["start_datetime"], slot["end_datetime"], period.starts_at, period.ends_at) for period in result.busy_periods)
        ]

    def validate_range(self, professional_id: int, starts_at: datetime, ends_at: datetime) -> None:
        result = self.collect_busy_periods(professional_id, starts_at, ends_at)
        self._log(professional_id, starts_at, ends_at, result)
        failure_policy = self._failure_policy(professional_id)
        if result.provider_unavailable and failure_policy == ExternalConflictFailurePolicy.fail_closed:
            raise ExternalAvailabilityUnavailable()
        if any(self._ranges_overlap(starts_at, ends_at, period.starts_at, period.ends_at) for period in result.busy_periods):
            raise ExternalAvailabilityConflict()

    def collect_busy_periods(self, professional_id: int, starts_at: datetime, ends_at: datetime) -> ExternalAvailabilityResult:
        settings = self.calendar_service.get_settings(professional_id)
        if not settings.sync_enabled or settings.conflict_policy in {CalendarConflictPolicy.internal_only, CalendarConflictPolicy.disabled}:
            return ExternalAvailabilityResult(status="skipped")

        max_end = datetime.now(UTC) + timedelta(days=settings.lookahead_days)
        query_start = starts_at
        query_end = min(ends_at, max_end)
        if query_start >= query_end:
            return ExternalAvailabilityResult(status="outside_lookahead")

        calendars = list(
            self.db.scalars(
                select(ExternalCalendar).where(
                    ExternalCalendar.professional_id == professional_id,
                    ExternalCalendar.enabled.is_(True),
                    ExternalCalendar.read_enabled.is_(True),
                    ExternalCalendar.conflict_check_enabled.is_(True),
                )
            )
        )
        if not calendars:
            return ExternalAvailabilityResult(status="no_calendars")

        busy_periods: list[BusyPeriod] = []
        errors: list[str] = []
        for calendar in calendars:
            try:
                provider = self.calendar_service.registry.resolve(calendar.provider, integration_id=calendar.integration_id)
                periods = provider.list_busy_periods(calendar.external_calendar_id, query_start, query_end)
            except Exception as exc:  # Provider details are intentionally sanitized before leaving this service.
                errors.append(f"{calendar.provider.value}:{exc.__class__.__name__}")
                continue
            busy_periods.extend(period for period in periods if period.availability in BLOCKING_AVAILABILITY)

        if errors and busy_periods:
            status = "partial"
        elif errors:
            status = "provider_unavailable"
        else:
            status = "checked"
        return ExternalAvailabilityResult(status=status, busy_periods=busy_periods, errors=errors, checked=True)

    def _failure_policy(self, professional_id: int) -> ExternalConflictFailurePolicy:
        settings = self.calendar_service.get_settings(professional_id)
        return settings.external_conflict_failure_policy

    @staticmethod
    def _ranges_overlap(first_start: datetime, first_end: datetime, second_start: datetime, second_end: datetime) -> bool:
        return first_start < second_end and first_end > second_start

    @staticmethod
    def _log(professional_id: int, starts_at: datetime, ends_at: datetime, result: ExternalAvailabilityResult) -> None:
        logger.info(
            "external_calendar_availability_check professional_id=%s starts_at=%s ends_at=%s result=%s errors=%s",
            professional_id,
            starts_at.isoformat(),
            ends_at.isoformat(),
            result.status,
            len(result.errors),
        )
