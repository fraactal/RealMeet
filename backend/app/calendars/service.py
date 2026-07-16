from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.calendars.contracts import ExternalCalendarEventInput
from app.calendars.registry import ExternalCalendarProviderRegistry
from app.calendars.schemas import CalendarSyncSettingsUpdate, ExternalCalendarCreate, ExternalCalendarTestRead, ExternalCalendarUpdate
from app.models.external_calendar import (
    CalendarConflictPolicy,
    CalendarSyncSettings,
    ExternalCalendar,
    ExternalCalendarProvider,
    ExternalCalendarSyncStatus,
    ExternalConflictFailurePolicy,
)
from app.models.integration import Integration
from app.integrations.enums import IntegrationProvider
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User


class ExternalCalendarService:
    def __init__(self, db: Session, registry: ExternalCalendarProviderRegistry | None = None) -> None:
        self.db = db
        self.registry = registry or ExternalCalendarProviderRegistry(db)

    def get_professional_for_user(self, user: User) -> ProfessionalProfile:
        profile = self.db.scalar(select(ProfessionalProfile).where(ProfessionalProfile.user_id == user.id))
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
        return profile

    def list_calendars(self, professional_id: int) -> list[ExternalCalendar]:
        self._require_professional(professional_id)
        return list(self.db.scalars(select(ExternalCalendar).where(ExternalCalendar.professional_id == professional_id).order_by(ExternalCalendar.created_at.desc(), ExternalCalendar.id.desc())))

    def create_calendar(self, professional_id: int, payload: ExternalCalendarCreate) -> ExternalCalendar:
        self._require_professional(professional_id)
        integration_id = payload.integration_id
        if payload.provider == ExternalCalendarProvider.google_calendar and integration_id is None:
            integration_id = self._default_google_integration_id()
        self._validate_provider(payload.provider, integration_id)
        self._validate_integration(integration_id)
        if payload.provider == ExternalCalendarProvider.google_calendar:
            self._validate_google_calendar_exists(integration_id, payload.external_calendar_id)
        item = ExternalCalendar(
            professional_id=professional_id,
            integration_id=integration_id,
            provider=payload.provider,
            external_calendar_id=payload.external_calendar_id,
            name=payload.name,
            description=payload.description,
            timezone=payload.timezone,
            read_enabled=payload.read_enabled,
            write_enabled=payload.write_enabled,
            conflict_check_enabled=payload.conflict_check_enabled,
            is_primary=payload.is_primary,
            enabled=True,
            sync_status=ExternalCalendarSyncStatus.pending,
        )
        self.db.add(item)
        if item.is_primary:
            self._clear_primary(professional_id, item.provider)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="External calendar already exists for this professional and provider") from exc
        self.db.refresh(item)
        return item

    def get_calendar(self, professional_id: int, calendar_id: int) -> ExternalCalendar:
        item = self.db.get(ExternalCalendar, calendar_id)
        if not item or item.professional_id != professional_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External calendar not found")
        return item

    def update_calendar(self, professional_id: int, calendar_id: int, payload: ExternalCalendarUpdate) -> ExternalCalendar:
        item = self.get_calendar(professional_id, calendar_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("is_primary") is True:
            self._clear_primary(professional_id, item.provider, exclude_id=item.id)
        for field, value in data.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def set_enabled(self, professional_id: int, calendar_id: int, enabled: bool) -> ExternalCalendar:
        item = self.get_calendar(professional_id, calendar_id)
        item.enabled = enabled
        item.sync_status = ExternalCalendarSyncStatus.pending if enabled else ExternalCalendarSyncStatus.disabled
        self.db.commit()
        self.db.refresh(item)
        return item

    def test_calendar(self, professional_id: int, calendar_id: int, *, simulate_error: bool = False) -> ExternalCalendarTestRead:
        item = self.get_calendar(professional_id, calendar_id)
        provider = self.registry.resolve(item.provider, integration_id=item.integration_id, simulate_error=simulate_error)
        health = provider.health_check()
        if not health.healthy:
            item.sync_status = ExternalCalendarSyncStatus.error
            item.last_sync_error_at = datetime.now(UTC)
            item.last_sync_error_code = health.code
            self.db.commit()
            return ExternalCalendarTestRead(health=asdict(health))
        now = datetime.now(UTC)
        calendars = provider.list_calendars()
        busy_periods = provider.list_busy_periods(item.external_calendar_id, now, now + timedelta(hours=8))
        created = provider.create_event(
            ExternalCalendarEventInput(
                calendar_id=item.external_calendar_id,
                title="RealMeet fake calendar test",
                starts_at=now + timedelta(days=1),
                ends_at=now + timedelta(days=1, hours=1),
                timezone=item.timezone,
            )
        )
        deleted = provider.delete_event(item.external_calendar_id, created.external_event_id)
        item.sync_status = ExternalCalendarSyncStatus.active
        item.last_synced_at = datetime.now(UTC)
        item.last_sync_error_code = None
        self.db.commit()
        return ExternalCalendarTestRead(
            health=asdict(health),
            calendars=[asdict(calendar) for calendar in calendars],
            busy_periods=[asdict(period) for period in busy_periods],
            created_event_id=created.external_event_id,
            deleted_event_id=deleted.external_event_id,
        )

    def get_settings(self, professional_id: int) -> CalendarSyncSettings:
        self._require_professional(professional_id)
        settings = self.db.get(CalendarSyncSettings, professional_id)
        if settings:
            return settings
        settings = CalendarSyncSettings(
            professional_id=professional_id,
            sync_enabled=False,
            conflict_policy=CalendarConflictPolicy.internal_only,
            external_conflict_failure_policy=ExternalConflictFailurePolicy.fail_closed,
            lookback_days=0,
            lookahead_days=90,
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def update_settings(self, professional_id: int, payload: CalendarSyncSettingsUpdate) -> CalendarSyncSettings:
        settings = self.get_settings(professional_id)
        data = payload.model_dump(exclude_unset=True)
        default_id = data.get("default_external_calendar_id")
        if default_id is not None:
            self.get_calendar(professional_id, default_id)
        for field, value in data.items():
            setattr(settings, field, value)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def _clear_primary(self, professional_id: int, provider: ExternalCalendarProvider, exclude_id: int | None = None) -> None:
        query = select(ExternalCalendar).where(ExternalCalendar.professional_id == professional_id, ExternalCalendar.provider == provider, ExternalCalendar.is_primary.is_(True))
        if exclude_id is not None:
            query = query.where(ExternalCalendar.id != exclude_id)
        for item in self.db.scalars(query):
            item.is_primary = False

    def _require_professional(self, professional_id: int) -> ProfessionalProfile:
        profile = self.db.get(ProfessionalProfile, professional_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")
        return profile

    def list_available_calendars(self, provider: ExternalCalendarProvider, *, integration_id: int | None = None) -> list[dict]:
        if provider == ExternalCalendarProvider.google_calendar and integration_id is None:
            integration_id = self._default_google_integration_id()
        client = self.registry.resolve(provider, integration_id=integration_id)
        return [asdict(calendar) for calendar in client.list_calendars()]

    def _validate_provider(self, provider: ExternalCalendarProvider, integration_id: int | None = None) -> None:
        self.registry.resolve(provider, integration_id=integration_id)

    def _validate_integration(self, integration_id: int | None) -> None:
        if integration_id is None:
            return
        if not self.db.get(Integration, integration_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    def _validate_google_calendar_exists(self, integration_id: int | None, external_calendar_id: str) -> None:
        available = self.list_available_calendars(ExternalCalendarProvider.google_calendar, integration_id=integration_id)
        if external_calendar_id not in {item["external_calendar_id"] for item in available}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google calendar is not available for this integration")

    def _default_google_integration_id(self) -> int:
        integration = self.db.scalar(select(Integration).where(Integration.provider == IntegrationProvider.google_meet).order_by(Integration.id.asc()))
        if not integration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Calendar is not connected")
        return integration.id
