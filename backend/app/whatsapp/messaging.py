from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationExecutionStatus, IntegrationStatus
from app.models.audit_log import AuditLog
from app.models.integration import Integration, IntegrationExecution
from app.models.user import User
from app.models.whatsapp import WhatsAppConsent, WhatsAppMessage, WhatsAppTemplate
from app.repositories.integration_execution_repository import IntegrationExecutionRepository
from app.schemas.integrations import IntegrationExecutionCreate
from app.whatsapp.cloud_client import HttpWhatsAppCloudClient, WhatsAppCloudClient, WhatsAppCloudClientError
from app.whatsapp.configuration import ensure_whatsapp_integration, parse_whatsapp_config
from app.whatsapp.enums import WhatsAppConsentPurpose, WhatsAppConsentStatus, WhatsAppMessageStatus, WhatsAppTemplateCategory, WhatsAppTemplateStatus, WhatsAppWebhookEventType
from app.whatsapp.exceptions import WhatsAppNotFoundError, WhatsAppValidationError
from app.whatsapp.repositories import WhatsAppConsentRepository, WhatsAppMessageRepository, WhatsAppTemplateRepository
from app.whatsapp.schemas import WhatsAppMessageRead, WhatsAppMessageSendRead, WhatsAppMessageSendRequest, WhatsAppTemplateSyncRead


STATE_RANK: dict[WhatsAppMessageStatus, int] = {
    WhatsAppMessageStatus.queued: 0,
    WhatsAppMessageStatus.accepted: 1,
    WhatsAppMessageStatus.sent: 2,
    WhatsAppMessageStatus.delivered: 3,
    WhatsAppMessageStatus.read: 4,
    WhatsAppMessageStatus.failed: 5,
    WhatsAppMessageStatus.cancelled: 5,
    WhatsAppMessageStatus.skipped: 5,
}


@dataclass(frozen=True)
class WhatsAppHealthResult:
    success: bool
    code: str
    message: str
    metadata: dict[str, Any]


class WhatsAppMessagingService:
    def __init__(self, db: Session, client: WhatsAppCloudClient | None = None) -> None:
        self.db = db
        self.client = client or HttpWhatsAppCloudClient()
        self.consents = WhatsAppConsentRepository(db)
        self.templates = WhatsAppTemplateRepository(db)
        self.messages = WhatsAppMessageRepository(db)
        self.executions = IntegrationExecutionRepository(db)

    def list_messages(self, integration: Integration, *, limit: int = 50) -> list[WhatsAppMessage]:
        ensure_whatsapp_integration(integration)
        return list(self.messages.list_by_integration(integration.id, limit=limit))

    def get_message(self, integration: Integration, message_id: int) -> WhatsAppMessage:
        ensure_whatsapp_integration(integration)
        message = self.messages.get(message_id)
        if not message or message.integration_id != integration.id:
            raise WhatsAppNotFoundError("Mensaje WhatsApp no encontrado", code="whatsapp_message_not_found")
        return message

    def health_check(self, integration: Integration, admin_user: User) -> WhatsAppHealthResult:
        config = self._ready_config(integration)
        token = self._resolve_access_token(config.secret_references.access_token)
        execution = self._create_execution(integration, operation="whatsapp_health_check", idempotency_key=f"whatsapp:health:{integration.id}:{datetime.now(UTC).isoformat()}")
        try:
            phone = self.client.get_phone_number(graph_api_version=config.graph_api_version, phone_number_id=config.phone_number_id, access_token=token)
            integration.status = IntegrationStatus.healthy
            integration.last_checked_at = datetime.now(UTC)
            integration.last_success_at = integration.last_checked_at
            integration.last_error_message = None
            self._finish_execution(execution, status=IntegrationExecutionStatus.succeeded, code="whatsapp_health_ok", metadata={"phone_number_id": _partial(phone.id)})
            self._audit(admin_user.id, "whatsapp_health_checked", integration.id, {"result": "succeeded"})
            result = WhatsAppHealthResult(True, "whatsapp_health_ok", "Health check WhatsApp exitoso", {"phone_number_id_partial": _partial(phone.id), "verified_name_present": bool(phone.verified_name)})
        except WhatsAppCloudClientError as exc:
            integration.status = IntegrationStatus.error
            integration.last_checked_at = datetime.now(UTC)
            integration.last_error_at = integration.last_checked_at
            integration.last_error_message = exc.message
            self._finish_execution(execution, status=IntegrationExecutionStatus.failed, code=exc.code, message=exc.message)
            self._audit(admin_user.id, "whatsapp_health_checked", integration.id, {"result": "failed", "code": exc.code})
            result = WhatsAppHealthResult(False, exc.code, exc.message, {})
        self._commit()
        return result

    def sync_templates(self, integration: Integration, admin_user: User) -> WhatsAppTemplateSyncRead:
        config = self._ready_config(integration)
        token = self._resolve_access_token(config.secret_references.access_token)
        execution = self._create_execution(integration, operation="whatsapp_template_sync", idempotency_key=f"whatsapp:sync:{integration.id}:{datetime.now(UTC).isoformat()}")
        updated = skipped = 0
        try:
            remote_templates = self.client.list_templates(graph_api_version=config.graph_api_version, waba_id=config.waba_id, access_token=token)
            for remote in remote_templates:
                local = self.templates.get_by_name_language(integration.id, remote.name, remote.language.replace("-", "_"))
                if local is None:
                    skipped += 1
                    continue
                local.status = _map_template_status(remote.status)
                local.category = _map_template_category(remote.category)
                local.external_template_id = remote.id
                local.last_synced_at = datetime.now(UTC)
                updated += 1
            self._finish_execution(execution, status=IntegrationExecutionStatus.succeeded, code="whatsapp_templates_synced", metadata={"updated": updated, "skipped": skipped})
            self._audit(admin_user.id, "whatsapp_templates_synced", integration.id, {"updated": updated, "skipped": skipped})
            result = WhatsAppTemplateSyncRead(success=True, code="whatsapp_templates_synced", message="Plantillas sincronizadas", synced_count=len(remote_templates), updated_count=updated, skipped_count=skipped)
        except WhatsAppCloudClientError as exc:
            self._finish_execution(execution, status=IntegrationExecutionStatus.failed, code=exc.code, message=exc.message)
            self._audit(admin_user.id, "whatsapp_templates_sync_failed", integration.id, {"code": exc.code})
            result = WhatsAppTemplateSyncRead(success=False, code=exc.code, message=exc.message, synced_count=0, updated_count=0, skipped_count=0)
        self._commit()
        return result

    def send_template(self, integration: Integration, payload: WhatsAppMessageSendRequest, admin_user: User) -> WhatsAppMessageSendRead:
        config = self._ready_config(integration)
        token = self._resolve_access_token(config.secret_references.access_token)
        consent = self._valid_consent(payload.consent_id, payload.purpose)
        template = self._valid_template(integration, payload.template_id, payload.purpose, payload.language)
        variables = self._valid_variables(template, payload.variables.safe_values())
        existing = self.messages.get_by_idempotency_key(integration.id, payload.idempotency_key)
        if existing:
            if existing.status in {WhatsAppMessageStatus.accepted, WhatsAppMessageStatus.sent, WhatsAppMessageStatus.delivered, WhatsAppMessageStatus.read}:
                return WhatsAppMessageSendRead(success=True, code="already_processed", message="Mensaje ya procesado", skipped=True, data=serialize_message(existing))
            if existing.status == WhatsAppMessageStatus.queued:
                raise WhatsAppValidationError("El mensaje ya esta en proceso", code="whatsapp_message_in_progress")
            message = existing
            message.attempt += 1
            message.status = WhatsAppMessageStatus.queued
            message.error_code = None
            message.error_message = None
        else:
            message = WhatsAppMessage(
                integration_id=integration.id,
                user_id=consent.user_id,
                template_id=template.id,
                purpose=payload.purpose,
                recipient_hash=consent.phone_hash,
                recipient_masked=consent.phone_masked,
                status=WhatsAppMessageStatus.queued,
                idempotency_key=payload.idempotency_key,
                attempt=1,
            )
            try:
                self.messages.create(message)
            except IntegrityError as exc:
                self.db.rollback()
                raise WhatsAppValidationError("El mensaje ya existe", code="whatsapp_message_conflict") from exc

        execution = self._create_execution(
            integration,
            operation="whatsapp_send_template",
            idempotency_key=f"whatsapp:send:{message.id}:attempt:{message.attempt}",
            entity_type="WhatsAppMessage",
            entity_id=str(message.id),
            metadata={"message_id": message.id, "template_id": template.id, "purpose": payload.purpose.value, "attempt": message.attempt},
        )
        try:
            result = self.client.send_template_message(
                graph_api_version=config.graph_api_version,
                phone_number_id=config.phone_number_id,
                access_token=token,
                to_e164=consent.phone_e164,
                template_name=template.name,
                language=template.language,
                body_variables=[variables[key] for key in _template_variable_keys(template)],
            )
            now = datetime.now(UTC)
            message.external_message_id = result.external_message_id
            message.status = WhatsAppMessageStatus.accepted
            message.accepted_at = now
            message.last_status_at = now
            message.error_code = None
            message.error_message = None
            self._finish_execution(execution, status=IntegrationExecutionStatus.succeeded, code="whatsapp_message_accepted", metadata={"message_id": message.id, "external_message_id_partial": _partial(result.external_message_id)})
            self._audit(admin_user.id, "whatsapp_message_accepted", integration.id, {"message_id": message.id, "template_id": template.id, "attempt": message.attempt})
            response = WhatsAppMessageSendRead(success=True, code="whatsapp_message_accepted", message="WhatsApp acepto el mensaje", data=serialize_message(message))
        except WhatsAppCloudClientError as exc:
            now = datetime.now(UTC)
            message.status = WhatsAppMessageStatus.failed
            message.failed_at = now
            message.last_status_at = now
            message.error_code = exc.code
            message.error_message = exc.message
            self._finish_execution(execution, status=IntegrationExecutionStatus.failed, code=exc.code, message=exc.message, metadata={"message_id": message.id})
            self._audit(admin_user.id, "whatsapp_message_failed", integration.id, {"message_id": message.id, "template_id": template.id, "attempt": message.attempt, "code": exc.code})
            response = WhatsAppMessageSendRead(success=False, code=exc.code, message=exc.message, data=serialize_message(message))
        self._commit()
        return response

    def retry_message(self, integration: Integration, message_id: int, admin_user: User) -> WhatsAppMessageSendRead:
        message = self.get_message(integration, message_id)
        if message.status != WhatsAppMessageStatus.failed:
            raise WhatsAppValidationError("Solo se pueden reintentar mensajes fallidos", code="whatsapp_retry_failed_only")
        return self.send_template(
            integration,
            WhatsAppMessageSendRequest(
                consent_id=self._consent_id_for_message(message),
                template_id=message.template_id,
                purpose=message.purpose,
                language=message.template.language,
                variables={},
                idempotency_key=message.idempotency_key,
                explicit_confirmation=True,
            ),
            admin_user,
        )

    def correlate_status(self, *, external_message_id: str | None, event_type: WhatsAppWebhookEventType, occurred_at: datetime | None, error_code: str | None = None, error_message: str | None = None) -> None:
        if not external_message_id:
            return
        message = self.messages.get_by_external_message_id(external_message_id)
        if not message:
            return
        target = {
            WhatsAppWebhookEventType.message_sent: WhatsAppMessageStatus.sent,
            WhatsAppWebhookEventType.message_delivered: WhatsAppMessageStatus.delivered,
            WhatsAppWebhookEventType.message_read: WhatsAppMessageStatus.read,
            WhatsAppWebhookEventType.message_failed: WhatsAppMessageStatus.failed,
        }.get(event_type)
        if target is None:
            return
        now = occurred_at or datetime.now(UTC)
        if target != WhatsAppMessageStatus.failed and STATE_RANK[target] < STATE_RANK.get(message.status, 0):
            message.last_status_at = now
            self.db.flush()
            return
        message.status = target
        message.last_status_at = now
        if target == WhatsAppMessageStatus.sent:
            message.sent_at = message.sent_at or now
        elif target == WhatsAppMessageStatus.delivered:
            message.delivered_at = message.delivered_at or now
        elif target == WhatsAppMessageStatus.read:
            message.read_at = message.read_at or now
        elif target == WhatsAppMessageStatus.failed:
            message.failed_at = message.failed_at or now
            message.error_code = error_code
            message.error_message = error_message
        self.db.flush()

    def _ready_config(self, integration: Integration):
        ensure_whatsapp_integration(integration)
        if not integration.enabled:
            raise WhatsAppValidationError("La integracion WhatsApp esta deshabilitada", code="integration_disabled")
        return parse_whatsapp_config(integration.config or {})

    def _resolve_access_token(self, reference: str | None) -> str:
        if not reference:
            raise WhatsAppValidationError("Referencia de token WhatsApp no configurada", code="whatsapp_token_reference_missing")
        token = os.environ.get(reference)
        if not token:
            raise WhatsAppValidationError("Token WhatsApp no disponible en entorno", code="whatsapp_token_missing")
        return token

    def _valid_consent(self, consent_id: int, purpose) -> WhatsAppConsent:
        consent = self.consents.get(consent_id)
        if not consent:
            raise WhatsAppNotFoundError("Consentimiento WhatsApp no encontrado", code="whatsapp_consent_not_found")
        if consent.status != WhatsAppConsentStatus.granted:
            raise WhatsAppValidationError("Consentimiento WhatsApp no activo", code="whatsapp_consent_not_granted")
        if consent.purpose != _consent_purpose_for_template(purpose):
            raise WhatsAppValidationError("Consentimiento no corresponde a la finalidad", code="whatsapp_consent_purpose_mismatch")
        return consent

    def _valid_template(self, integration: Integration, template_id: int, purpose, language: str) -> WhatsAppTemplate:
        template = self.templates.get(template_id)
        if not template or template.integration_id != integration.id:
            raise WhatsAppNotFoundError("Plantilla WhatsApp no encontrada", code="template_not_found")
        if template.category != WhatsAppTemplateCategory.utility:
            raise WhatsAppValidationError("Solo plantillas utility pueden enviarse", code="whatsapp_template_category_invalid")
        if template.status != WhatsAppTemplateStatus.approved:
            raise WhatsAppValidationError("La plantilla debe estar aprobada para envio real", code="whatsapp_template_not_approved")
        if template.purpose != purpose:
            raise WhatsAppValidationError("La plantilla no corresponde a la finalidad", code="whatsapp_template_purpose_mismatch")
        if template.language != language:
            raise WhatsAppValidationError("Idioma de plantilla no disponible", code="whatsapp_template_language_mismatch")
        return template

    def _valid_variables(self, template: WhatsAppTemplate, values: dict[str, str]) -> dict[str, str]:
        keys = _template_variable_keys(template)
        missing = [key for key in keys if key not in values]
        extra = [key for key in values if key not in keys]
        if missing:
            raise WhatsAppValidationError("Faltan variables requeridas", code="whatsapp_variables_missing")
        if extra:
            raise WhatsAppValidationError("Variables no permitidas", code="whatsapp_variables_extra")
        return values

    def _consent_id_for_message(self, message: WhatsAppMessage) -> int:
        consent = self.db.query(WhatsAppConsent).filter(
            WhatsAppConsent.user_id == message.user_id,
            WhatsAppConsent.phone_hash == message.recipient_hash,
            WhatsAppConsent.purpose == message.purpose,
            WhatsAppConsent.status == WhatsAppConsentStatus.granted,
        ).first()
        if not consent:
            raise WhatsAppValidationError("Consentimiento no disponible para reintento", code="whatsapp_consent_not_granted")
        return consent.id

    def _create_execution(self, integration: Integration, *, operation: str, idempotency_key: str, entity_type: str | None = None, entity_id: str | None = None, metadata: dict[str, Any] | None = None) -> IntegrationExecution:
        return self.executions.create(
            IntegrationExecutionCreate(
                integration_id=integration.id,
                operation=operation,
                entity_type=entity_type,
                entity_id=entity_id,
                idempotency_key=idempotency_key,
                status=IntegrationExecutionStatus.running,
                started_at=datetime.now(UTC),
                request_metadata={"provider": "whatsapp_cloud", "operation": operation, **(metadata or {})},
            )
        )

    def _finish_execution(self, execution: IntegrationExecution, *, status: IntegrationExecutionStatus, code: str, message: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        execution.status = status
        execution.finished_at = datetime.now(UTC)
        execution.response_metadata = {"code": code, **(metadata or {})}
        execution.error_code = None if status == IntegrationExecutionStatus.succeeded else code
        execution.error_message = message if status != IntegrationExecutionStatus.succeeded else None
        self.db.flush()

    def _audit(self, user_id: int, action: str, integration_id: int, metadata: dict[str, Any]) -> None:
        self.db.add(AuditLog(user_id=user_id, action=action, entity_name="Integration", entity_id=str(integration_id), metadata_json={"integration_id": integration_id, "provider": "whatsapp_cloud", **metadata}, created_at=datetime.now(UTC)))

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise


def serialize_message(message: WhatsAppMessage) -> WhatsAppMessageRead:
    return WhatsAppMessageRead(
        id=message.id,
        integration_id=message.integration_id,
        user_id=message.user_id,
        template_id=message.template_id,
        purpose=message.purpose,
        recipient_masked=message.recipient_masked,
        status=message.status,
        external_message_id_partial=_partial(message.external_message_id) if message.external_message_id else None,
        idempotency_key=message.idempotency_key,
        attempt=message.attempt,
        accepted_at=message.accepted_at,
        sent_at=message.sent_at,
        delivered_at=message.delivered_at,
        read_at=message.read_at,
        failed_at=message.failed_at,
        last_status_at=message.last_status_at,
        error_code=message.error_code,
        error_message=message.error_message,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


def _template_variable_keys(template: WhatsAppTemplate) -> list[str]:
    variables = template.components_schema.get("variables") if isinstance(template.components_schema, dict) else []
    return [str(item.get("key")) for item in variables if isinstance(item, dict) and item.get("required", True)]


def _map_template_status(value: str) -> WhatsAppTemplateStatus:
    return {
        "PENDING": WhatsAppTemplateStatus.pending,
        "APPROVED": WhatsAppTemplateStatus.approved,
        "REJECTED": WhatsAppTemplateStatus.rejected,
        "PAUSED": WhatsAppTemplateStatus.paused,
        "DISABLED": WhatsAppTemplateStatus.disabled,
    }.get(value.upper(), WhatsAppTemplateStatus.unknown)


def _map_template_category(value: str) -> WhatsAppTemplateCategory:
    return {
        "UTILITY": WhatsAppTemplateCategory.utility,
        "AUTHENTICATION": WhatsAppTemplateCategory.authentication,
        "MARKETING": WhatsAppTemplateCategory.marketing,
    }.get(value.upper(), WhatsAppTemplateCategory.unknown)


def _consent_purpose_for_template(purpose) -> WhatsAppConsentPurpose:
    if purpose.value == "appointment_reminder":
        return WhatsAppConsentPurpose.appointment_reminders
    if purpose.value in {"appointment_updated", "appointment_cancelled", "meeting_ready"}:
        return WhatsAppConsentPurpose.appointment_updates
    return WhatsAppConsentPurpose.appointment_transactional


def _partial(value: str) -> str:
    if len(value) <= 12:
        return "****"
    return f"{value[:6]}...{value[-4:]}"
