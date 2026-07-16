from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calendars.schemas import CalendarConflictCheckRead
from app.calendars.service import ExternalCalendarService
from app.models.external_calendar import CalendarConflictPolicy, ExternalCalendar


BLOCKING_AVAILABILITY = {"busy", "tentative", "out_of_office"}


class CalendarConflictService:
    def __init__(self, db: Session, calendar_service: ExternalCalendarService | None = None) -> None:
        self.db = db
        self.calendar_service = calendar_service or ExternalCalendarService(db)

    def check(self, professional_id: int, *, starts_at, ends_at) -> CalendarConflictCheckRead:
        if starts_at.tzinfo is None or ends_at.tzinfo is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Datetime values must be timezone-aware")
        if starts_at >= ends_at:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="starts_at must be before ends_at")
        if ends_at - starts_at > timedelta(days=31):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Conflict check range is too large")

        settings = self.calendar_service.get_settings(professional_id)
        candidate = {"starts_at": starts_at, "ends_at": ends_at}
        if not settings.sync_enabled or settings.conflict_policy in {CalendarConflictPolicy.internal_only, CalendarConflictPolicy.disabled}:
            return CalendarConflictCheckRead(has_conflict=False, status="external_check_skipped", candidate=candidate)

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
        conflicts = []
        errors = []
        for calendar in calendars:
            try:
                provider = self.calendar_service.registry.resolve(calendar.provider, integration_id=calendar.integration_id)
                periods = provider.list_busy_periods(calendar.external_calendar_id, starts_at, ends_at)
            except HTTPException as exc:
                errors.append(f"{calendar.external_calendar_id}: {exc.detail}")
                continue
            for period in periods:
                if period.availability not in BLOCKING_AVAILABILITY:
                    continue
                if starts_at < period.ends_at and ends_at > period.starts_at:
                    conflicts.append(
                        {
                            "calendar_id": calendar.id,
                            "external_calendar_id": calendar.external_calendar_id,
                            "starts_at": period.starts_at,
                            "ends_at": period.ends_at,
                            "availability": period.availability,
                        }
                    )
        status_value = "partial" if errors else "checked"
        if errors and not conflicts:
            status_value = "unavailable"
        return CalendarConflictCheckRead(has_conflict=bool(conflicts), status=status_value, candidate=candidate, conflicts=conflicts, errors=errors)
