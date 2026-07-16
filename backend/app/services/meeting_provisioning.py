from dataclasses import dataclass
from datetime import UTC, datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import IntegrationError
from app.integrations.meeting_contracts import MeetingAttendee, MeetingCreateRequest
from app.meetings.mock import MockMeetingProvider
from app.models.appointment import Appointment, AppointmentMeeting, AppointmentMeetingStatus, MeetingProvider
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import ExternalMeeting, Integration
from app.models.professional_profile import ConsultationMode, ProfessionalProfile
from app.models.user import User
from app.services.google_meet import GoogleMeetService

logger = logging.getLogger("realmeet.meetings.provisioning")

MEETING_POLICIES = {"mock_only", "google_preferred", "google_required", "disabled"}
DEFAULT_POLICY = "mock_only"


@dataclass(frozen=True)
class MeetingProvisioningDecision:
    policy: str
    provider: MeetingProvider | None
    integration: Integration | None
    fallback_allowed: bool
    reason: str | None = None


class MeetingProvisioningService:
    def __init__(self, db: Session, *, google_service: GoogleMeetService | None = None) -> None:
        self.db = db
        self.google_service = google_service or GoogleMeetService(db)

    def provision_for_appointment(self, appointment: Appointment, actor: User) -> AppointmentMeeting | None:
        if not self._requires_meeting(appointment):
            return self._mark_not_required(appointment, actor)

        link = self._ensure_link(appointment)
        if link.status in {AppointmentMeetingStatus.ready, AppointmentMeetingStatus.fallback_ready, AppointmentMeetingStatus.not_required}:
            return link
        if link.status == AppointmentMeetingStatus.provisioning:
            return link

        decision = self.resolve()
        if decision.policy == "disabled":
            return self._mark_not_required(appointment, actor)
        if decision.provider == MeetingProvider.mock:
            return self._provision_mock(appointment, actor, fallback_used=False, fallback_reason=decision.reason)
        if decision.provider == MeetingProvider.google_meet and decision.integration:
            return self._provision_google(appointment, actor, decision)
        if decision.policy == "google_preferred" and decision.fallback_allowed:
            return self._provision_mock(appointment, actor, fallback_used=True, fallback_reason=decision.reason or "google_unavailable")
        return self._mark_failed(appointment, actor, "google_meet_unavailable", "No pudimos preparar el enlace todavia.")

    def cancel_for_appointment(self, appointment: Appointment, actor: User) -> AppointmentMeeting | None:
        link = self._get_link(appointment.id)
        if not link:
            return None
        if link.status in {AppointmentMeetingStatus.cancelled, AppointmentMeetingStatus.not_required}:
            return link
        if link.provider == MeetingProvider.google_meet and link.external_reference:
            try:
                integration = self._google_integration()
                if not integration:
                    raise RuntimeError("google integration missing")
                self.google_service.cancel_meeting(
                    integration.id,
                    link.external_reference,
                    actor,
                    idempotency_key=f"appointment:{appointment.id}:meeting:cancel",
                    send_updates=(integration.config or {}).get("send_updates", "none"),
                )
            except Exception as exc:  # noqa: BLE001 - appointment cancellation must remain committed.
                link.status = AppointmentMeetingStatus.failed
                link.error_code = "meeting_cancel_sync_failed"
                link.error_message = "La reserva fue cancelada, pero la reunion externa requiere revision administrativa."
                link.last_attempt_at = self._now()
                self._audit(actor, "appointment_meeting_cancel_failed", appointment, {"provider": link.provider.value if link.provider else None, "error": exc.__class__.__name__})
                self._sync_appointment_fields(appointment, link)
                self.db.commit()
                return link
        link.status = AppointmentMeetingStatus.cancelled
        link.cancelled_at = self._now()
        link.meeting_url = None
        link.error_code = None
        link.error_message = None
        self._sync_appointment_fields(appointment, link)
        self._audit(actor, "appointment_meeting_cancelled", appointment, {"provider": link.provider.value if link.provider else None})
        self.db.commit()
        return link

    def retry_create(self, appointment_id: int, actor: User) -> AppointmentMeeting:
        appointment = self._appointment(appointment_id)
        link = self._ensure_link(appointment)
        if link.status not in {AppointmentMeetingStatus.failed, AppointmentMeetingStatus.pending}:
            return link
        link.status = AppointmentMeetingStatus.pending
        link.error_code = None
        link.error_message = None
        self.db.commit()
        self.db.refresh(appointment)
        return self.provision_for_appointment(appointment, actor) or link

    def retry_cancel(self, appointment_id: int, actor: User) -> AppointmentMeeting:
        appointment = self._appointment(appointment_id)
        return self.cancel_for_appointment(appointment, actor) or self._ensure_link(appointment)

    def reconcile(self, appointment_id: int, actor: User) -> AppointmentMeeting:
        appointment = self._appointment(appointment_id)
        link = self._ensure_link(appointment)
        if link.provider != MeetingProvider.google_meet or not link.external_reference:
            self._audit(actor, "appointment_meeting_reconciled", appointment, {"result": "local_only", "provider": link.provider.value if link.provider else None})
            return link
        integration = self._google_integration()
        if not integration:
            link.status = AppointmentMeetingStatus.failed
            link.error_code = "google_integration_missing"
            link.error_message = "La integracion Google Meet no esta disponible."
            self.db.commit()
            return link
        try:
            result = self.google_service.get_meeting(integration.id, link.external_reference, actor)
            if result.status == "cancelled":
                link.status = AppointmentMeetingStatus.cancelled
                link.cancelled_at = self._now()
            elif result.meeting_url:
                link.status = AppointmentMeetingStatus.ready
                link.meeting_url = result.meeting_url
            else:
                link.status = AppointmentMeetingStatus.failed
                link.error_code = "google_meet_url_missing"
                link.error_message = "Google no devolvio un enlace Meet valido."
            self._sync_appointment_fields(appointment, link)
            self._audit(actor, "appointment_meeting_reconciled", appointment, {"result": "succeeded", "provider": "google_meet"})
            self.db.commit()
            if link.status == AppointmentMeetingStatus.ready:
                self._notify_meeting_ready(appointment.id)
            return link
        except IntegrationError as exc:
            link.status = AppointmentMeetingStatus.failed
            link.error_code = exc.code
            link.error_message = "La reunion externa requiere revision administrativa."
            self._sync_appointment_fields(appointment, link)
            self._audit(actor, "appointment_meeting_reconciled", appointment, {"result": "failed", "code": exc.code})
            self.db.commit()
            return link

    def resolve(self) -> MeetingProvisioningDecision:
        integration = self._google_integration()
        config = integration.config if integration else {}
        policy = str(config.get("appointment_policy") or DEFAULT_POLICY)
        if policy not in MEETING_POLICIES:
            policy = DEFAULT_POLICY
        if policy == "disabled":
            return MeetingProvisioningDecision(policy, None, integration, False, "disabled")
        if policy == "mock_only":
            return MeetingProvisioningDecision(policy, MeetingProvider.mock, integration, False, "mock_policy")
        if not integration:
            return MeetingProvisioningDecision(policy, None, None, policy == "google_preferred", "google_integration_missing")
        if not integration.enabled:
            return MeetingProvisioningDecision(policy, None, integration, policy == "google_preferred", "google_disabled")
        if integration.status != IntegrationStatus.healthy:
            return MeetingProvisioningDecision(policy, None, integration, policy == "google_preferred", "google_not_healthy")
        return MeetingProvisioningDecision(policy, MeetingProvider.google_meet, integration, policy == "google_preferred")

    def _provision_google(self, appointment: Appointment, actor: User, decision: MeetingProvisioningDecision) -> AppointmentMeeting:
        link = self._start_attempt(appointment, MeetingProvider.google_meet)
        integration = decision.integration
        assert integration is not None
        try:
            result = self.google_service.create_meeting(integration.id, self._google_request(appointment, integration), actor)
            external = self._external_meeting(integration.id, result.external_event_id)
            if external:
                external.appointment_id = appointment.id
            link.provider = MeetingProvider.google_meet
            link.status = AppointmentMeetingStatus.ready
            link.meeting_url = result.meeting_url
            link.external_meeting_id = external.id if external else None
            link.external_reference = result.external_event_id
            link.calendar_event_id = result.external_calendar_id
            link.fallback_used = False
            link.fallback_reason = None
            link.error_code = None
            link.error_message = None
            self._sync_appointment_fields(appointment, link)
            self._audit(actor, "appointment_meeting_provisioned", appointment, {"provider": "google_meet", "fallback": False})
            self.db.commit()
            self._notify_meeting_ready(appointment.id)
            return link
        except IntegrationError as exc:
            if decision.policy == "google_preferred" and decision.fallback_allowed:
                self.db.rollback()
                appointment = self._appointment(appointment.id)
                return self._provision_mock(appointment, actor, fallback_used=True, fallback_reason=exc.code)
            return self._mark_failed(appointment, actor, exc.code, "No pudimos preparar el enlace todavia.")

    def _provision_mock(self, appointment: Appointment, actor: User, *, fallback_used: bool, fallback_reason: str | None) -> AppointmentMeeting:
        link = self._start_attempt(appointment, MeetingProvider.mock)
        professional = appointment.professional
        payload = MockMeetingProvider(settings.mock_meeting_base_url).create_meeting(
            professional_name=f"{professional.user.first_name} {professional.user.last_name}" if professional and professional.user else "RealMeet",
            starts_at=appointment.start_datetime,
        )
        link.provider = MeetingProvider.mock
        link.status = AppointmentMeetingStatus.fallback_ready if fallback_used else AppointmentMeetingStatus.ready
        link.meeting_url = payload.url
        link.external_reference = payload.external_id
        link.calendar_event_id = payload.calendar_event_id
        link.fallback_used = fallback_used
        link.fallback_reason = fallback_reason
        link.error_code = None
        link.error_message = None
        self._sync_appointment_fields(appointment, link)
        self._audit(actor, "appointment_meeting_provisioned", appointment, {"provider": "mock", "fallback": fallback_used, "reason": fallback_reason})
        self.db.commit()
        self._notify_meeting_ready(appointment.id)
        return link

    def _mark_not_required(self, appointment: Appointment, actor: User) -> AppointmentMeeting:
        link = self._ensure_link(appointment)
        link.provider = None
        link.status = AppointmentMeetingStatus.not_required
        link.meeting_url = None
        link.error_code = None
        link.error_message = None
        self._sync_appointment_fields(appointment, link)
        self._audit(actor, "appointment_meeting_not_required", appointment, {"reason": "policy_or_mode"})
        self.db.commit()
        return link

    def _mark_failed(self, appointment: Appointment, actor: User, code: str, message: str) -> AppointmentMeeting:
        link = self._ensure_link(appointment)
        link.status = AppointmentMeetingStatus.failed
        link.error_code = code
        link.error_message = message
        link.last_attempt_at = self._now()
        self._sync_appointment_fields(appointment, link)
        self._audit(actor, "appointment_meeting_failed", appointment, {"code": code})
        self.db.commit()
        return link

    def _start_attempt(self, appointment: Appointment, provider: MeetingProvider) -> AppointmentMeeting:
        link = self._ensure_link(appointment)
        link.status = AppointmentMeetingStatus.provisioning
        link.provider = provider
        link.attempt += 1
        link.last_attempt_at = self._now()
        self.db.commit()
        self.db.refresh(appointment)
        return link

    def _google_request(self, appointment: Appointment, integration: Integration) -> MeetingCreateRequest:
        config = integration.config or {}
        timezone = str(config.get("default_timezone") or "America/Santiago")
        attendees = []
        if config.get("include_appointment_attendees") is True:
            emails = [appointment.client.user.email if appointment.client and appointment.client.user else None, appointment.professional.user.email if appointment.professional and appointment.professional.user else None]
            attendees = [MeetingAttendee(email=email) for email in emails if email]
        return MeetingCreateRequest(
            title="Sesion agendada en RealMeet",
            description="Reunion generada por RealMeet para una reserva confirmada.",
            start_at=appointment.start_datetime,
            end_at=appointment.end_datetime,
            timezone=timezone,
            attendees=attendees,
            idempotency_key=f"appointment:{appointment.id}:meeting:create",
            send_updates=str(config.get("send_updates") or "none"),
            entity_type="appointment",
            entity_id=str(appointment.id),
        )

    def _ensure_link(self, appointment: Appointment) -> AppointmentMeeting:
        link = self._get_link(appointment.id)
        if link:
            return link
        link = AppointmentMeeting(appointment_id=appointment.id, status=AppointmentMeetingStatus.pending)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def _get_link(self, appointment_id: int) -> AppointmentMeeting | None:
        return self.db.scalar(select(AppointmentMeeting).where(AppointmentMeeting.appointment_id == appointment_id))

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
            raise ValueError("Appointment not found")
        return appointment

    def _google_integration(self) -> Integration | None:
        return self.db.scalar(
            select(Integration)
            .where(Integration.provider == IntegrationProvider.google_meet, Integration.integration_type == IntegrationType.meeting)
            .order_by(Integration.enabled.desc(), Integration.updated_at.desc(), Integration.id.desc())
        )

    def _external_meeting(self, integration_id: int, external_event_id: str) -> ExternalMeeting | None:
        return self.db.scalar(select(ExternalMeeting).where(ExternalMeeting.integration_id == integration_id, ExternalMeeting.external_event_id == external_event_id))

    @staticmethod
    def _requires_meeting(appointment: Appointment) -> bool:
        mode = appointment.consultation_mode
        value = mode.value if isinstance(mode, ConsultationMode) else str(mode)
        return value in {"online", "hybrid"}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _sync_appointment_fields(self, appointment: Appointment, link: AppointmentMeeting) -> None:
        appointment.meeting_provider = link.provider
        appointment.meeting_url = link.meeting_url if link.status in {AppointmentMeetingStatus.ready, AppointmentMeetingStatus.fallback_ready} else None
        appointment.external_meeting_id = link.external_reference
        appointment.calendar_event_id = link.calendar_event_id

    def _audit(self, actor: User, action: str, appointment: Appointment, metadata: dict) -> None:
        self.db.add(
            AuditLog(
                user_id=actor.id,
                action=action,
                entity_name="Appointment",
                entity_id=str(appointment.id),
                metadata_json={"appointment_id": appointment.id, **metadata},
                created_at=self._now(),
            )
        )

    def _notify_meeting_ready(self, appointment_id: int) -> None:
        try:
            from app.notifications.service import AppointmentNotificationService

            appointment = self._appointment(appointment_id)
            AppointmentNotificationService(self.db).notify_meeting_ready(appointment)
            try:
                from app.integrations.google_workspace.document_automation import DocumentAutomationEventType, DocumentAutomationService

                DocumentAutomationService(self.db).handle_appointment_event(DocumentAutomationEventType.meeting_ready, appointment)
            except Exception as exc:  # noqa: BLE001 - automation failures must not affect meeting provisioning.
                self.db.rollback()
                logger.warning("appointment_meeting_ready_document_automation_failed appointment_id=%s error=%s", appointment_id, exc.__class__.__name__)
        except Exception as exc:  # noqa: BLE001 - notification failures must not affect meeting provisioning.
            logger.warning("appointment_meeting_ready_notification_failed appointment_id=%s error=%s", appointment_id, exc.__class__.__name__)
