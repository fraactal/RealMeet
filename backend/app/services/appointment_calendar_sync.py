from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.calendars.contracts import ExternalCalendarEventInput
from app.calendars.service import ExternalCalendarService
from app.models.appointment import (
    Appointment,
    AppointmentExternalCalendarEvent,
    AppointmentExternalCalendarEventStatus,
    AppointmentExternalCalendarSyncAction,
    AppointmentMeetingStatus,
    AppointmentStatus,
    MeetingProvider,
)
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.external_calendar import CalendarSyncSettings, ExternalCalendar
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User


class AppointmentCalendarSyncService:
    def __init__(self, db: Session, calendar_service: ExternalCalendarService | None = None) -> None:
        self.db = db
        self.calendar_service = calendar_service or ExternalCalendarService(db)

    def get_status(self, appointment_id: int) -> AppointmentExternalCalendarEvent | None:
        return self.db.scalar(
            select(AppointmentExternalCalendarEvent)
            .where(AppointmentExternalCalendarEvent.appointment_id == appointment_id)
            .order_by(AppointmentExternalCalendarEvent.created_at.desc(), AppointmentExternalCalendarEvent.id.desc())
        )

    def sync_created(self, appointment: Appointment, actor: User) -> AppointmentExternalCalendarEvent | None:
        target = self._target_calendar(appointment.professional_id)
        if not target:
            return None
        if self._should_wait_for_google_meet(appointment):
            return self._ensure_link(appointment, target, AppointmentExternalCalendarSyncAction.create)
        link = self._ensure_link(appointment, target, AppointmentExternalCalendarSyncAction.create)
        return self._create_or_update(appointment, target, link, actor, allow_meeting_reuse=True)

    def sync_updated(self, appointment: Appointment, actor: User) -> AppointmentExternalCalendarEvent | None:
        link = self.get_status(appointment.id)
        if not link:
            return self.sync_created(appointment, actor)
        target = self.db.get(ExternalCalendar, link.external_calendar_id)
        if not target or not target.enabled or not target.write_enabled:
            return link
        if appointment.status == AppointmentStatus.cancelled:
            return self.sync_cancelled(appointment, actor)
        link.sync_action = AppointmentExternalCalendarSyncAction.update
        return self._create_or_update(appointment, target, link, actor, allow_meeting_reuse=True)

    def sync_cancelled(self, appointment: Appointment, actor: User) -> AppointmentExternalCalendarEvent | None:
        link = self.get_status(appointment.id)
        if not link:
            return None
        target = self.db.get(ExternalCalendar, link.external_calendar_id)
        if not target or not link.external_event_id:
            return link
        try:
            provider = self.calendar_service.registry.resolve(target.provider, integration_id=target.integration_id)
            provider.delete_event(target.external_calendar_id, link.external_event_id)
            link.status = AppointmentExternalCalendarEventStatus.cancelled
            link.sync_action = AppointmentExternalCalendarSyncAction.none
            link.last_synced_at = self._now()
            self._clear_error(link)
            self._audit(actor, "appointment_external_calendar_cancelled", appointment, {"provider": target.provider.value})
        except Exception as exc:  # noqa: BLE001 - internal cancellation must remain source of truth.
            self._mark_error(link, "external_calendar_cancel_failed", exc, AppointmentExternalCalendarSyncAction.cancel)
            self._audit(actor, "appointment_external_calendar_cancel_failed", appointment, {"provider": target.provider.value, "error": exc.__class__.__name__})
        self.db.commit()
        self.db.refresh(link)
        return link

    def retry(self, appointment_id: int, actor: User) -> AppointmentExternalCalendarEvent | None:
        appointment = self._appointment(appointment_id)
        link = self.get_status(appointment.id)
        if not link:
            return self.sync_created(appointment, actor)
        if link.sync_action == AppointmentExternalCalendarSyncAction.cancel or appointment.status == AppointmentStatus.cancelled:
            return self.sync_cancelled(appointment, actor)
        if link.sync_action == AppointmentExternalCalendarSyncAction.update:
            return self.sync_updated(appointment, actor)
        return self.sync_created(appointment, actor)

    def reconcile(self, appointment_id: int, actor: User) -> AppointmentExternalCalendarEvent | None:
        appointment = self._appointment(appointment_id)
        link = self.get_status(appointment.id)
        target = self.db.get(ExternalCalendar, link.external_calendar_id) if link else self._target_calendar(appointment.professional_id)
        if not target:
            return link
        link = link or self._ensure_link(appointment, target, AppointmentExternalCalendarSyncAction.create)
        try:
            provider = self.calendar_service.registry.resolve(target.provider, integration_id=target.integration_id)
            event = provider.get_event(target.external_calendar_id, link.external_event_id) if link.external_event_id else None
            if not event:
                event = provider.find_event_by_appointment_id(target.external_calendar_id, appointment.id)
            if not event:
                link.status = AppointmentExternalCalendarEventStatus.reconcile_required
                link.sync_action = AppointmentExternalCalendarSyncAction.create
                link.last_error_code = "missing_external_event"
                link.last_error_message = "No se encontro el evento externo asociado."
                link.last_error_at = self._now()
            else:
                link.external_event_id = event.external_event_id
                link.status = AppointmentExternalCalendarEventStatus.cancelled if event.status == "cancelled" else AppointmentExternalCalendarEventStatus.updated
                link.sync_action = AppointmentExternalCalendarSyncAction.none
                link.last_synced_at = self._now()
                self._clear_error(link)
            self._audit(actor, "appointment_external_calendar_reconciled", appointment, {"result": link.status.value, "provider": target.provider.value})
        except Exception as exc:  # noqa: BLE001
            self._mark_error(link, "external_calendar_reconcile_failed", exc, AppointmentExternalCalendarSyncAction.update)
        self.db.commit()
        self.db.refresh(link)
        return link

    def _create_or_update(
        self,
        appointment: Appointment,
        target: ExternalCalendar,
        link: AppointmentExternalCalendarEvent,
        actor: User,
        *,
        allow_meeting_reuse: bool,
    ) -> AppointmentExternalCalendarEvent:
        try:
            if allow_meeting_reuse and self._link_google_meet_event(appointment, target, link):
                self._audit(actor, "appointment_external_calendar_reused_meet_event", appointment, {"provider": target.provider.value})
            else:
                provider = self.calendar_service.registry.resolve(target.provider, integration_id=target.integration_id)
                payload = self._payload(appointment, target)
                if link.external_event_id:
                    result = provider.update_event(link.external_event_id, payload)
                    link.status = AppointmentExternalCalendarEventStatus.updated
                else:
                    result = provider.create_event(payload)
                    link.status = AppointmentExternalCalendarEventStatus.created
                link.external_event_id = result.external_event_id
            link.sync_action = AppointmentExternalCalendarSyncAction.none
            link.last_synced_at = self._now()
            self._clear_error(link)
        except Exception as exc:  # noqa: BLE001
            action = AppointmentExternalCalendarSyncAction.update if link.external_event_id else AppointmentExternalCalendarSyncAction.create
            self._mark_error(link, "external_calendar_sync_failed", exc, action)
            self._audit(actor, "appointment_external_calendar_sync_failed", appointment, {"provider": target.provider.value, "error": exc.__class__.__name__})
        self.db.commit()
        self.db.refresh(link)
        return link

    def _target_calendar(self, professional_id: int) -> ExternalCalendar | None:
        settings = self.db.get(CalendarSyncSettings, professional_id)
        if settings and settings.default_external_calendar_id:
            item = self.db.get(ExternalCalendar, settings.default_external_calendar_id)
            if item and item.professional_id == professional_id and item.enabled and item.write_enabled:
                return item
        return self.db.scalar(
            select(ExternalCalendar)
            .where(
                ExternalCalendar.professional_id == professional_id,
                ExternalCalendar.enabled.is_(True),
                ExternalCalendar.write_enabled.is_(True),
                ExternalCalendar.is_primary.is_(True),
            )
            .order_by(ExternalCalendar.id.asc())
        )

    def _ensure_link(
        self,
        appointment: Appointment,
        target: ExternalCalendar,
        action: AppointmentExternalCalendarSyncAction,
    ) -> AppointmentExternalCalendarEvent:
        link = self.db.scalar(
            select(AppointmentExternalCalendarEvent).where(
                AppointmentExternalCalendarEvent.appointment_id == appointment.id,
                AppointmentExternalCalendarEvent.external_calendar_id == target.id,
            )
        )
        if link:
            return link
        link = AppointmentExternalCalendarEvent(
            appointment_id=appointment.id,
            external_calendar_id=target.id,
            provider=target.provider.value,
            status=AppointmentExternalCalendarEventStatus.pending,
            sync_action=action,
        )
        self.db.add(link)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            link = self.db.scalar(
                select(AppointmentExternalCalendarEvent).where(
                    AppointmentExternalCalendarEvent.appointment_id == appointment.id,
                    AppointmentExternalCalendarEvent.external_calendar_id == target.id,
                )
            )
            if not link:
                raise
        self.db.refresh(link)
        return link

    def _link_google_meet_event(self, appointment: Appointment, target: ExternalCalendar, link: AppointmentExternalCalendarEvent) -> bool:
        meeting = appointment.meeting_link
        if (
            not meeting
            or meeting.provider != MeetingProvider.google_meet
            or meeting.status not in {AppointmentMeetingStatus.ready, AppointmentMeetingStatus.fallback_ready}
            or not meeting.external_reference
            or meeting.calendar_event_id != target.external_calendar_id
        ):
            return False
        link.external_event_id = meeting.external_reference
        link.status = AppointmentExternalCalendarEventStatus.updated
        return True

    def _should_wait_for_google_meet(self, appointment: Appointment) -> bool:
        if appointment.consultation_mode.value not in {"online", "hybrid"} or appointment.status != AppointmentStatus.pending:
            return False
        try:
            from app.services.meeting_provisioning import MeetingProvisioningService

            decision = MeetingProvisioningService(self.db).resolve()
            return decision.provider == MeetingProvider.google_meet
        except Exception:
            return False

    @staticmethod
    def _payload(appointment: Appointment, target: ExternalCalendar) -> ExternalCalendarEventInput:
        client = appointment.client.user if appointment.client and appointment.client.user else None
        professional = appointment.professional.user if appointment.professional and appointment.professional.user else None
        client_name = f"{client.first_name} {client.last_name}".strip() if client else "cliente"
        attendees = [email for email in [professional.email if professional else None, client.email if client else None] if email]
        return ExternalCalendarEventInput(
            calendar_id=target.external_calendar_id,
            title=f"RealMeet - Sesion con {client_name}",
            description=f"Reserva generada por RealMeet.\nID de reserva: {appointment.id}",
            starts_at=appointment.start_datetime,
            ends_at=appointment.end_datetime,
            timezone=target.timezone,
            attendees=attendees,
            appointment_id=appointment.id,
        )

    def _appointment(self, appointment_id: int) -> Appointment:
        appointment = self.db.scalar(
            select(Appointment)
            .options(
                selectinload(Appointment.meeting_link),
                selectinload(Appointment.professional).selectinload(ProfessionalProfile.user),
                selectinload(Appointment.client).selectinload(ClientProfile.user),
            )
            .where(Appointment.id == appointment_id)
        )
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        return appointment

    def _mark_error(
        self,
        link: AppointmentExternalCalendarEvent,
        code: str,
        exc: Exception,
        action: AppointmentExternalCalendarSyncAction,
    ) -> None:
        link.status = AppointmentExternalCalendarEventStatus.reconcile_required
        link.sync_action = action
        link.last_error_at = self._now()
        link.last_error_code = code
        link.last_error_message = "El evento externo requiere revision manual."

    @staticmethod
    def _clear_error(link: AppointmentExternalCalendarEvent) -> None:
        link.last_error_at = None
        link.last_error_code = None
        link.last_error_message = None

    def _audit(self, actor: User, action: str, appointment: Appointment, metadata: dict) -> None:
        self.db.add(AuditLog(user_id=actor.id, action=action, entity_name="Appointment", entity_id=str(appointment.id), metadata_json={"appointment_id": appointment.id, **metadata}, created_at=self._now()))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
