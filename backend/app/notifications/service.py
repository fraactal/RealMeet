from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.emails.service import EmailService, email_service
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.models.appointment import (
    Appointment,
    AppointmentMeetingStatus,
    AppointmentNotification,
    AppointmentNotificationChannel,
    AppointmentNotificationEvent,
    AppointmentNotificationStatus,
    AppointmentStatus,
)
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.integration import Integration
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentStatus,
    WhatsAppMessageStatus,
    WhatsAppTemplateCategory,
    WhatsAppTemplatePurpose,
    WhatsAppTemplateStatus,
)
from app.whatsapp.exceptions import WhatsAppError, WhatsAppValidationError
from app.whatsapp.messaging import WhatsAppMessagingService
from app.whatsapp.phone import normalize_phone, phone_hmac
from app.whatsapp.schemas import WhatsAppMessageSendRequest, WhatsAppMessageVariables

logger = logging.getLogger("realmeet.notifications")

CHANNEL_POLICIES = {"email_only", "whatsapp_preferred", "whatsapp_required", "email_and_whatsapp", "notifications_disabled"}
DEFAULT_POLICY = "email_only"
DEFAULT_LANGUAGE = "es_CL"

EVENT_PURPOSE: dict[AppointmentNotificationEvent, WhatsAppTemplatePurpose] = {
    AppointmentNotificationEvent.appointment_confirmed: WhatsAppTemplatePurpose.appointment_confirmation,
    AppointmentNotificationEvent.appointment_updated: WhatsAppTemplatePurpose.appointment_updated,
    AppointmentNotificationEvent.appointment_cancelled: WhatsAppTemplatePurpose.appointment_cancelled,
    AppointmentNotificationEvent.appointment_reminder: WhatsAppTemplatePurpose.appointment_reminder,
    AppointmentNotificationEvent.meeting_ready: WhatsAppTemplatePurpose.meeting_ready,
}

CONSENT_PURPOSE: dict[AppointmentNotificationEvent, WhatsAppConsentPurpose] = {
    AppointmentNotificationEvent.appointment_confirmed: WhatsAppConsentPurpose.appointment_transactional,
    AppointmentNotificationEvent.appointment_updated: WhatsAppConsentPurpose.appointment_updates,
    AppointmentNotificationEvent.appointment_cancelled: WhatsAppConsentPurpose.appointment_updates,
    AppointmentNotificationEvent.appointment_reminder: WhatsAppConsentPurpose.appointment_reminders,
    AppointmentNotificationEvent.meeting_ready: WhatsAppConsentPurpose.appointment_updates,
}


@dataclass(frozen=True)
class AppointmentNotificationContext:
    appointment: Appointment
    client: User
    professional: User
    professional_name: str
    client_name: str


@dataclass(frozen=True)
class NotificationPolicy:
    policy: str
    fallback_channel: str
    reminder_enabled: bool
    reminder_minutes_before: int
    default_language: str
    template_mapping: dict[str, int]


class AppointmentNotificationService:
    def __init__(self, db: Session, mailer: EmailService = email_service, whatsapp_service: WhatsAppMessagingService | None = None) -> None:
        self.db = db
        self.mailer = mailer
        self.whatsapp_service = whatsapp_service or WhatsAppMessagingService(db)

    def notify_created(self, appointment: Appointment) -> None:
        # Pending reservations keep legacy email behavior only; WhatsApp starts at confirmed lifecycle events.
        self._send_legacy_professional_email(appointment, "Reserva creada en RealMeet", "Reserva creada", include_meeting=False)

    def notify_confirmed(self, appointment: Appointment) -> None:
        self.dispatch(AppointmentNotificationEvent.appointment_confirmed, appointment.id)
        if self._meeting_ready(appointment):
            self.dispatch(AppointmentNotificationEvent.meeting_ready, appointment.id)

    def notify_cancelled(self, appointment: Appointment) -> None:
        self.dispatch(AppointmentNotificationEvent.appointment_cancelled, appointment.id)

    def notify_updated(self, appointment: Appointment, *, version: str) -> None:
        self.dispatch(AppointmentNotificationEvent.appointment_updated, appointment.id, version=version)

    def notify_meeting_ready(self, appointment: Appointment) -> None:
        if self._meeting_ready(appointment):
            self.dispatch(AppointmentNotificationEvent.meeting_ready, appointment.id)

    def dispatch(
        self,
        event_type: AppointmentNotificationEvent,
        appointment_id: int,
        *,
        version: str = "v1",
        scheduled_for: datetime | None = None,
    ) -> list[AppointmentNotification]:
        try:
            return self._dispatch(event_type, appointment_id, version=version, scheduled_for=scheduled_for)
        except Exception as exc:  # noqa: BLE001 - external notifications must not break appointments.
            logger.warning("appointment_notification_unhandled appointment_id=%s event=%s error=%s", appointment_id, event_type.value, exc.__class__.__name__)
            self.db.rollback()
            return []

    def schedule_due_reminders(self, *, now: datetime | None = None, limit: int = 50) -> list[AppointmentNotification]:
        now = now or datetime.now(UTC)
        integration = self._whatsapp_integration()
        policy = self._policy(integration)
        if not policy.reminder_enabled:
            return []
        window_end = now + timedelta(minutes=policy.reminder_minutes_before)
        appointments = list(
            self.db.scalars(
                select(Appointment)
                .options(selectinload(Appointment.client).selectinload(ClientProfile.user))
                .where(
                    Appointment.status == AppointmentStatus.confirmed,
                    Appointment.start_datetime > now,
                    Appointment.start_datetime <= window_end,
                )
                .order_by(Appointment.start_datetime.asc(), Appointment.id.asc())
                .limit(limit)
            )
        )
        created: list[AppointmentNotification] = []
        for appointment in appointments:
            version = appointment.start_datetime.astimezone(UTC).isoformat()
            created.extend(self.dispatch(AppointmentNotificationEvent.appointment_reminder, appointment.id, version=version, scheduled_for=appointment.start_datetime))
        return created

    def list_notifications(self, *, appointment_id: int | None = None, limit: int = 100, offset: int = 0) -> list[AppointmentNotification]:
        query = (
            select(AppointmentNotification)
            .options(selectinload(AppointmentNotification.whatsapp_message), selectinload(AppointmentNotification.template))
            .order_by(AppointmentNotification.created_at.desc(), AppointmentNotification.id.desc())
            .offset(offset)
            .limit(limit)
        )
        if appointment_id is not None:
            query = query.where(AppointmentNotification.appointment_id == appointment_id)
        return list(self.db.scalars(query))

    def get_notification(self, notification_id: int) -> AppointmentNotification | None:
        return self.db.get(AppointmentNotification, notification_id)

    def retry(self, notification_id: int, actor: User) -> AppointmentNotification:
        notification = self._require_notification(notification_id)
        if notification.status not in {AppointmentNotificationStatus.failed, AppointmentNotificationStatus.processing}:
            raise WhatsAppValidationError("Solo se pueden reintentar notificaciones fallidas o inciertas", code="notification_retry_not_allowed")
        appointment = self._appointment(notification.appointment_id)
        notification.attempt += 1
        notification.status = AppointmentNotificationStatus.pending
        notification.error_code = None
        notification.error_message = None
        self.db.commit()
        if notification.channel == AppointmentNotificationChannel.whatsapp:
            self._send_whatsapp(notification, appointment, self._context(appointment), self._whatsapp_integration(), self._policy(self._whatsapp_integration()), actor=actor)
        else:
            self._send_email(notification, appointment, self._context(appointment), fallback=False)
        return notification

    def reconcile(self, notification_id: int, actor: User) -> AppointmentNotification:
        notification = self._require_notification(notification_id)
        message = notification.whatsapp_message
        if message:
            self._sync_from_whatsapp_message(notification, message.status.value, message.error_code, message.error_message)
            self._audit(actor.id, "appointment_notification_reconciled", notification, {"result": "whatsapp_message"})
            self.db.commit()
        return notification

    def cancel_pending(self, notification_id: int, actor: User) -> AppointmentNotification:
        notification = self._require_notification(notification_id)
        if notification.status not in {AppointmentNotificationStatus.pending, AppointmentNotificationStatus.processing}:
            raise WhatsAppValidationError("Solo se pueden cancelar notificaciones pendientes", code="notification_cancel_not_allowed")
        notification.status = AppointmentNotificationStatus.cancelled
        notification.error_code = None
        notification.error_message = None
        self._audit(actor.id, "appointment_notification_cancelled", notification, {"channel": notification.channel.value})
        self.db.commit()
        return notification

    def sync_whatsapp_status(self, whatsapp_message_id: int, status_value: str, error_code: str | None, error_message: str | None) -> None:
        notification = self.db.scalar(select(AppointmentNotification).where(AppointmentNotification.whatsapp_message_id == whatsapp_message_id))
        if not notification:
            return
        self._sync_from_whatsapp_message(notification, status_value, error_code, error_message)
        self.db.flush()

    def _dispatch(
        self,
        event_type: AppointmentNotificationEvent,
        appointment_id: int,
        *,
        version: str,
        scheduled_for: datetime | None,
    ) -> list[AppointmentNotification]:
        appointment = self._appointment(appointment_id)
        context = self._context(appointment)
        integration = self._whatsapp_integration()
        policy = self._policy(integration)
        if policy.policy == "notifications_disabled":
            notification = self._ensure_notification(appointment, context.client.id, event_type, AppointmentNotificationChannel.email, version, scheduled_for)
            notification.status = AppointmentNotificationStatus.skipped
            notification.error_code = "notifications_disabled"
            self.db.commit()
            return [notification]

        created: list[AppointmentNotification] = []
        if policy.policy in {"whatsapp_preferred", "whatsapp_required", "email_and_whatsapp"}:
            whatsapp = self._ensure_notification(appointment, context.client.id, event_type, AppointmentNotificationChannel.whatsapp, version, scheduled_for)
            created.append(self._send_whatsapp(whatsapp, appointment, context, integration, policy))
            if policy.policy == "email_and_whatsapp":
                email = self._ensure_notification(appointment, context.client.id, event_type, AppointmentNotificationChannel.email, version, scheduled_for)
                created.append(self._send_email(email, appointment, context, fallback=False))
            elif policy.policy == "whatsapp_preferred" and self._should_fallback(whatsapp):
                email = self._ensure_notification(appointment, context.client.id, event_type, AppointmentNotificationChannel.email, version, scheduled_for)
                created.append(self._send_email(email, appointment, context, fallback=True))
        if policy.policy == "email_only":
            email = self._ensure_notification(appointment, context.client.id, event_type, AppointmentNotificationChannel.email, version, scheduled_for)
            created.append(self._send_email(email, appointment, context, fallback=False))

        self._send_legacy_professional_email(appointment, self._subject(event_type), self._label(event_type), include_meeting=event_type in {AppointmentNotificationEvent.appointment_confirmed, AppointmentNotificationEvent.meeting_ready})
        return created

    def _send_whatsapp(
        self,
        notification: AppointmentNotification,
        appointment: Appointment,
        context: AppointmentNotificationContext,
        integration: Integration | None,
        policy: NotificationPolicy,
        *,
        actor: User | None = None,
    ) -> AppointmentNotification:
        if notification.status in {AppointmentNotificationStatus.accepted, AppointmentNotificationStatus.sent, AppointmentNotificationStatus.delivered, AppointmentNotificationStatus.read}:
            return notification
        if not integration or not integration.enabled or integration.status not in {IntegrationStatus.configured, IntegrationStatus.healthy}:
            return self._skip_or_fail(notification, "integration_not_available", "Integracion WhatsApp no disponible", required=policy.policy == "whatsapp_required")
        try:
            phone = normalize_phone(context.client.phone or "", default_country_code=str((integration.config or {}).get("country_code") or "CL"))
            consent = self._consent(context.client.id, phone.e164, CONSENT_PURPOSE[notification.event_type])
            if not consent:
                return self._skip_or_fail(notification, "consent_not_granted", "Consentimiento WhatsApp ausente o revocado", required=policy.policy == "whatsapp_required")
            template = self._template(integration, notification.event_type, policy)
            if not template:
                return self._skip_or_fail(notification, "template_not_available", "Plantilla WhatsApp aprobada no disponible", required=policy.policy == "whatsapp_required")
            variables = self._variables_for_template(appointment, context, template)
            notification.template_id = template.id
            notification.recipient_masked = consent.phone_masked
            notification.status = AppointmentNotificationStatus.processing
            self.db.commit()
            result = self.whatsapp_service.send_template(
                integration,
                WhatsAppMessageSendRequest(
                    consent_id=consent.id,
                    template_id=template.id,
                    purpose=template.purpose,
                    language=template.language,
                    variables=WhatsAppMessageVariables(**variables),
                    idempotency_key=notification.idempotency_key,
                    explicit_confirmation=True,
                ),
                actor or context.client,
            )
            notification.whatsapp_message_id = result.data.id
            if result.data.status == WhatsAppMessageStatus.accepted:
                notification.status = AppointmentNotificationStatus.accepted
                notification.sent_at = result.data.accepted_at
                notification.error_code = None
                notification.error_message = None
            elif result.data.status == WhatsAppMessageStatus.failed:
                notification.status = AppointmentNotificationStatus.processing if result.data.error_code == "whatsapp_timeout" else AppointmentNotificationStatus.failed
                notification.failed_at = result.data.failed_at
                notification.error_code = "delivery_unknown" if result.data.error_code == "whatsapp_timeout" else result.data.error_code
                notification.error_message = result.data.error_message
            self._audit((actor or context.client).id, "appointment_notification_created", notification, {"channel": "whatsapp", "status": notification.status.value})
            self.db.commit()
            return notification
        except WhatsAppError as exc:
            return self._skip_or_fail(notification, exc.code, exc.message, required=policy.policy == "whatsapp_required")

    def _send_email(
        self,
        notification: AppointmentNotification,
        appointment: Appointment,
        context: AppointmentNotificationContext,
        *,
        fallback: bool,
    ) -> AppointmentNotification:
        if notification.status in {AppointmentNotificationStatus.sent, AppointmentNotificationStatus.fallback_sent}:
            return notification
        body = self._build_email_body(appointment, context, self._label(notification.event_type), notification.event_type in {AppointmentNotificationEvent.appointment_confirmed, AppointmentNotificationEvent.meeting_ready})
        sent = self.mailer.send(subject=self._subject(notification.event_type), recipient=context.client.email, body=body)
        now = datetime.now(UTC)
        notification.fallback_used = fallback
        notification.email_reference = notification.idempotency_key
        if sent:
            notification.status = AppointmentNotificationStatus.fallback_sent if fallback else AppointmentNotificationStatus.sent
            notification.sent_at = now
            notification.error_code = None
            notification.error_message = None
        else:
            notification.status = AppointmentNotificationStatus.failed
            notification.failed_at = now
            notification.error_code = "smtp_unavailable"
            notification.error_message = "No pudimos enviar el email transaccional."
        self._audit(context.client.id, "appointment_notification_created", notification, {"channel": "email", "fallback": fallback, "status": notification.status.value})
        self.db.commit()
        return notification

    def _ensure_notification(
        self,
        appointment: Appointment,
        user_id: int,
        event_type: AppointmentNotificationEvent,
        channel: AppointmentNotificationChannel,
        version: str,
        scheduled_for: datetime | None,
    ) -> AppointmentNotification:
        key = self._idempotency_key(appointment, event_type, version, channel)
        existing = self.db.scalar(select(AppointmentNotification).where(AppointmentNotification.idempotency_key == key))
        if existing:
            return existing
        notification = AppointmentNotification(
            appointment_id=appointment.id,
            user_id=user_id,
            event_type=event_type,
            channel=channel,
            purpose=EVENT_PURPOSE[event_type].value,
            status=AppointmentNotificationStatus.pending,
            idempotency_key=key,
            scheduled_for=scheduled_for,
        )
        self.db.add(notification)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return self.db.scalar(select(AppointmentNotification).where(AppointmentNotification.idempotency_key == key))
        self.db.refresh(notification)
        return notification

    def _appointment(self, appointment_id: int) -> Appointment:
        appointment = self.db.scalar(
            select(Appointment)
            .options(
                selectinload(Appointment.client).selectinload(ClientProfile.user),
                selectinload(Appointment.professional).selectinload(ProfessionalProfile.user),
                selectinload(Appointment.meeting_link),
            )
            .where(Appointment.id == appointment_id)
        )
        if not appointment:
            raise WhatsAppValidationError("Reserva no encontrada", code="appointment_not_found")
        return appointment

    def _context(self, appointment: Appointment) -> AppointmentNotificationContext:
        if not appointment.client or not appointment.client.user or not appointment.professional or not appointment.professional.user:
            raise WhatsAppValidationError("Contexto de reserva incompleto", code="appointment_context_missing")
        client = appointment.client.user
        professional = appointment.professional.user
        return AppointmentNotificationContext(
            appointment=appointment,
            client=client,
            professional=professional,
            professional_name=f"{professional.first_name} {professional.last_name}",
            client_name=f"{client.first_name} {client.last_name}",
        )

    def _whatsapp_integration(self) -> Integration | None:
        return self.db.scalar(
            select(Integration)
            .where(Integration.provider == IntegrationProvider.whatsapp_cloud, Integration.integration_type == IntegrationType.messaging)
            .order_by(Integration.enabled.desc(), Integration.updated_at.desc(), Integration.id.desc())
        )

    def _policy(self, integration: Integration | None) -> NotificationPolicy:
        config = integration.config if integration else {}
        policy = str(config.get("notification_policy") or DEFAULT_POLICY)
        if policy not in CHANNEL_POLICIES:
            policy = DEFAULT_POLICY
        reminder_minutes = int(config.get("reminder_minutes_before") or 1440)
        mapping = config.get("template_mapping") if isinstance(config.get("template_mapping"), dict) else {}
        return NotificationPolicy(
            policy=policy,
            fallback_channel=str(config.get("fallback_channel") or "email"),
            reminder_enabled=bool(config.get("reminder_enabled", True)),
            reminder_minutes_before=max(reminder_minutes, 1),
            default_language=str(config.get("default_language") or DEFAULT_LANGUAGE).replace("-", "_"),
            template_mapping={str(key): int(value) for key, value in mapping.items() if str(value).isdigit() or isinstance(value, int)},
        )

    def _consent(self, user_id: int, phone_e164: str, purpose: WhatsAppConsentPurpose) -> WhatsAppConsent | None:
        phone_hash = phone_hmac(phone_e164)
        return self.db.scalar(
            select(WhatsAppConsent).where(
                WhatsAppConsent.user_id == user_id,
                WhatsAppConsent.phone_hash == phone_hash,
                WhatsAppConsent.purpose == purpose,
                WhatsAppConsent.status == WhatsAppConsentStatus.granted,
            )
        )

    def _template(self, integration: Integration, event_type: AppointmentNotificationEvent, policy: NotificationPolicy) -> WhatsAppTemplate | None:
        purpose = EVENT_PURPOSE[event_type]
        mapped_id = policy.template_mapping.get(purpose.value)
        conditions = [
            WhatsAppTemplate.integration_id == integration.id,
            WhatsAppTemplate.purpose == purpose,
            WhatsAppTemplate.category == WhatsAppTemplateCategory.utility,
            WhatsAppTemplate.status == WhatsAppTemplateStatus.approved,
            WhatsAppTemplate.language == policy.default_language,
        ]
        if mapped_id:
            conditions.append(WhatsAppTemplate.id == mapped_id)
        return self.db.scalar(select(WhatsAppTemplate).where(*conditions).order_by(WhatsAppTemplate.updated_at.desc(), WhatsAppTemplate.id.desc()))

    def _variables(self, appointment: Appointment, context: AppointmentNotificationContext) -> dict[str, str | None]:
        start = appointment.start_datetime.astimezone(UTC)
        return {
            "client_name": context.client.first_name,
            "professional_name": context.professional_name,
            "appointment_date": start.strftime("%d-%m-%Y"),
            "appointment_time": start.strftime("%H:%M"),
            "appointment_modality": appointment.consultation_mode.value,
            "meeting_url": appointment.meeting_url if appointment.meeting_url else None,
            "platform_name": "RealMeet",
        }

    def _variables_for_template(self, appointment: Appointment, context: AppointmentNotificationContext, template: WhatsAppTemplate) -> dict[str, str | None]:
        values = self._variables(appointment, context)
        schema = template.components_schema if isinstance(template.components_schema, dict) else {}
        variables = schema.get("variables") if isinstance(schema.get("variables"), list) else []
        keys = [str(item.get("key")) for item in variables if isinstance(item, dict) and item.get("key")]
        return {key: values.get(key) for key in keys}

    def _idempotency_key(self, appointment: Appointment, event_type: AppointmentNotificationEvent, version: str, channel: AppointmentNotificationChannel) -> str:
        slug = event_type.value.replace("appointment_", "").replace("_", "-")
        return f"appointment:{appointment.id}:{slug}:{version}:{channel.value}"

    def _skip_or_fail(self, notification: AppointmentNotification, code: str, message: str, *, required: bool) -> AppointmentNotification:
        notification.status = AppointmentNotificationStatus.failed if required else AppointmentNotificationStatus.skipped
        notification.failed_at = datetime.now(UTC) if required else None
        notification.error_code = code
        notification.error_message = message
        self.db.commit()
        return notification

    def _should_fallback(self, whatsapp: AppointmentNotification) -> bool:
        return whatsapp.status in {AppointmentNotificationStatus.failed, AppointmentNotificationStatus.skipped} and whatsapp.error_code != "delivery_unknown"

    def _sync_from_whatsapp_message(self, notification: AppointmentNotification, status_value: str, error_code: str | None, error_message: str | None) -> None:
        target = {
            "accepted": AppointmentNotificationStatus.accepted,
            "sent": AppointmentNotificationStatus.sent,
            "delivered": AppointmentNotificationStatus.delivered,
            "read": AppointmentNotificationStatus.read,
            "failed": AppointmentNotificationStatus.failed,
            "cancelled": AppointmentNotificationStatus.cancelled,
            "skipped": AppointmentNotificationStatus.skipped,
        }.get(status_value)
        if target is None:
            return
        rank = {
            AppointmentNotificationStatus.pending: 0,
            AppointmentNotificationStatus.processing: 1,
            AppointmentNotificationStatus.accepted: 2,
            AppointmentNotificationStatus.sent: 3,
            AppointmentNotificationStatus.delivered: 4,
            AppointmentNotificationStatus.read: 5,
            AppointmentNotificationStatus.failed: 6,
            AppointmentNotificationStatus.cancelled: 6,
            AppointmentNotificationStatus.skipped: 6,
            AppointmentNotificationStatus.fallback_sent: 6,
        }
        if rank[target] < rank.get(notification.status, 0):
            return
        notification.status = target
        if target == AppointmentNotificationStatus.failed:
            notification.failed_at = datetime.now(UTC)
            notification.error_code = error_code
            notification.error_message = error_message

    def _send_legacy_professional_email(self, appointment: Appointment, subject: str, event_label: str, *, include_meeting: bool) -> None:
        try:
            context = self._context(appointment)
            body = self._build_email_body(appointment, context, event_label, include_meeting)
            self.mailer.send(subject=subject, recipient=context.professional.email, body=body)
        except Exception as exc:  # noqa: BLE001 - professional email compatibility must not break reservation.
            logger.warning("appointment_professional_email_failed appointment_id=%s error=%s", appointment.id, exc.__class__.__name__)

    @staticmethod
    def _build_email_body(appointment: Appointment, context: AppointmentNotificationContext, event_label: str, include_meeting: bool) -> str:
        lines = [
            event_label,
            "",
            f"Reserva #{appointment.id}",
            f"Profesional: {context.professional_name}",
            f"Cliente: {context.client_name}",
            f"Inicio: {appointment.start_datetime.isoformat()}",
            f"Termino: {appointment.end_datetime.isoformat()}",
            f"Modalidad: {appointment.consultation_mode.value}",
            f"Estado: {appointment.status.value}",
        ]
        if appointment.status == AppointmentStatus.cancelled and appointment.cancellation_reason:
            lines.append(f"Motivo de cancelacion: {appointment.cancellation_reason}")
        if include_meeting and appointment.status != AppointmentStatus.cancelled:
            if appointment.meeting_url:
                provider = getattr(appointment, "meeting_provider", None)
                provider_value = getattr(provider, "value", provider)
                label = "Reunion simulada para entorno de prueba:" if str(provider_value) == "mock" else "Reunion:"
                lines.extend(["", label, appointment.meeting_url])
            else:
                lines.extend(["", "El enlace de reunion todavia esta siendo preparado."])
        return "\n".join(lines)

    @staticmethod
    def _subject(event_type: AppointmentNotificationEvent) -> str:
        return {
            AppointmentNotificationEvent.appointment_confirmed: "Reserva confirmada en RealMeet",
            AppointmentNotificationEvent.appointment_updated: "Reserva actualizada en RealMeet",
            AppointmentNotificationEvent.appointment_cancelled: "Reserva cancelada en RealMeet",
            AppointmentNotificationEvent.appointment_reminder: "Recordatorio de reserva en RealMeet",
            AppointmentNotificationEvent.meeting_ready: "Enlace de reunion disponible en RealMeet",
        }[event_type]

    @staticmethod
    def _label(event_type: AppointmentNotificationEvent) -> str:
        return {
            AppointmentNotificationEvent.appointment_confirmed: "Reserva confirmada",
            AppointmentNotificationEvent.appointment_updated: "Reserva actualizada",
            AppointmentNotificationEvent.appointment_cancelled: "Reserva cancelada",
            AppointmentNotificationEvent.appointment_reminder: "Recordatorio de reserva",
            AppointmentNotificationEvent.meeting_ready: "Enlace de reunion disponible",
        }[event_type]

    @staticmethod
    def _meeting_ready(appointment: Appointment) -> bool:
        link = getattr(appointment, "meeting_link", None)
        if link and link.status in {AppointmentMeetingStatus.ready, AppointmentMeetingStatus.fallback_ready} and link.meeting_url:
            return True
        return bool(appointment.meeting_url)

    def _require_notification(self, notification_id: int) -> AppointmentNotification:
        notification = self.get_notification(notification_id)
        if not notification:
            raise WhatsAppValidationError("Notificacion no encontrada", code="notification_not_found")
        return notification

    def _audit(self, user_id: int, action: str, notification: AppointmentNotification, metadata: dict[str, Any]) -> None:
        self.db.add(
            AuditLog(
                user_id=None if action == "appointment_notification_created" else user_id,
                action=action,
                entity_name="AppointmentNotification",
                entity_id=str(notification.id),
                metadata_json={"appointment_id": notification.appointment_id, "notification_id": notification.id, **metadata},
                created_at=datetime.now(UTC),
            )
        )
