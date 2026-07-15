from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import hmac
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.enums import IntegrationProvider
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User
from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate, WhatsAppWebhookEvent
from app.whatsapp.configuration import ensure_whatsapp_integration, parse_whatsapp_config, validate_whatsapp_local_configuration, whatsapp_status
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppTemplateStatus,
    WhatsAppWebhookEventType,
    WhatsAppWebhookProcessingStatus,
)
from app.whatsapp.exceptions import WhatsAppNotFoundError, WhatsAppValidationError
from app.whatsapp.phone import mask_phone_e164, normalize_phone, phone_hmac
from app.whatsapp.repositories import WhatsAppConsentRepository, WhatsAppTemplateRepository, WhatsAppWebhookEventRepository
from app.whatsapp.schemas import (
    WhatsAppConsentAdminCorrection,
    WhatsAppConsentGrant,
    WhatsAppTemplateCreate,
    WhatsAppTemplateUpdate,
)


logger = logging.getLogger("realmeet.whatsapp.webhook")
MAX_EVENTS_PER_WEBHOOK = 50


class WhatsAppConsentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.consents = WhatsAppConsentRepository(db)

    def list_for_user(self, user: User) -> list[WhatsAppConsent]:
        return list(self.consents.list_for_user(user.id))

    def grant_self_service(self, user: User, payload: WhatsAppConsentGrant) -> WhatsAppConsent:
        phone = normalize_phone(payload.phone)
        phone_hash = phone_hmac(phone.e164)
        consent = self.consents.get_by_user_phone_purpose(user.id, phone_hash, payload.purpose)
        now = datetime.now(UTC)
        if consent is None:
            consent = WhatsAppConsent(
                user_id=user.id,
                phone_e164=phone.e164,
                phone_hash=phone_hash,
                phone_masked=phone.masked,
                status=WhatsAppConsentStatus.granted,
                purpose=payload.purpose,
                source=WhatsAppConsentSource.self_service,
                consent_text_version=payload.consent_text_version,
                granted_at=now,
                revoked_at=None,
            )
            self.db.add(consent)
        else:
            consent.phone_e164 = phone.e164
            consent.phone_masked = phone.masked
            consent.status = WhatsAppConsentStatus.granted
            consent.source = WhatsAppConsentSource.self_service
            consent.consent_text_version = payload.consent_text_version
            consent.granted_at = now
            consent.revoked_at = None
            consent.source_reason = None
        self._audit(user.id, "whatsapp_consent_granted", "WhatsAppConsent", None, {"user_id": user.id, "purpose": payload.purpose.value, "source": "self_service"})
        self._commit()
        self.db.refresh(consent)
        return consent

    def revoke_self_service(self, user: User, purpose: WhatsAppConsentPurpose) -> WhatsAppConsent:
        items = [item for item in self.consents.list_for_user(user.id) if item.purpose == purpose and item.status == WhatsAppConsentStatus.granted]
        if not items:
            raise WhatsAppNotFoundError("No existe consentimiento activo para revocar", code="consent_not_found")
        consent = items[0]
        consent.status = WhatsAppConsentStatus.revoked
        consent.revoked_at = datetime.now(UTC)
        self._audit(user.id, "whatsapp_consent_revoked", "WhatsAppConsent", str(consent.id), {"user_id": user.id, "purpose": purpose.value})
        self._commit()
        self.db.refresh(consent)
        return consent

    def has_consent(self, user_id: int, phone: str, purpose: WhatsAppConsentPurpose) -> bool:
        normalized = normalize_phone(phone)
        found = self.consents.get_by_user_phone_purpose(user_id, phone_hmac(normalized.e164), purpose)
        return bool(found and found.status == WhatsAppConsentStatus.granted)

    def list_admin_summary(self, *, limit: int = 100, offset: int = 0) -> list[WhatsAppConsent]:
        return list(self.consents.list_admin(limit=limit, offset=offset))

    def admin_correction(self, admin_user: User, payload: WhatsAppConsentAdminCorrection) -> WhatsAppConsent:
        if self.db.get(User, payload.user_id) is None:
            raise WhatsAppNotFoundError("Usuario no encontrado", code="user_not_found")
        phone = normalize_phone(payload.phone)
        phone_hash = phone_hmac(phone.e164)
        consent = self.consents.get_by_user_phone_purpose(payload.user_id, phone_hash, payload.purpose)
        now = datetime.now(UTC)
        if consent is None:
            consent = WhatsAppConsent(
                user_id=payload.user_id,
                phone_e164=phone.e164,
                phone_hash=phone_hash,
                phone_masked=phone.masked,
                status=WhatsAppConsentStatus.granted,
                purpose=payload.purpose,
                source=WhatsAppConsentSource.admin_correction,
                consent_text_version=payload.consent_text_version,
                source_reason=payload.reason,
                granted_at=now,
            )
            self.db.add(consent)
        else:
            consent.status = WhatsAppConsentStatus.granted
            consent.source = WhatsAppConsentSource.admin_correction
            consent.consent_text_version = payload.consent_text_version
            consent.source_reason = payload.reason
            consent.granted_at = now
            consent.revoked_at = None
        self._audit(
            admin_user.id,
            "whatsapp_consent_admin_corrected",
            "WhatsAppConsent",
            str(consent.id) if consent.id else None,
            {"user_id": payload.user_id, "purpose": payload.purpose.value, "source": "admin_correction", "reason_recorded": True},
        )
        self._commit()
        self.db.refresh(consent)
        return consent

    def _audit(self, user_id: int | None, action: str, entity_name: str, entity_id: str | None, metadata: dict[str, Any]) -> None:
        self.db.add(AuditLog(user_id=user_id, action=action, entity_name=entity_name, entity_id=entity_id or "pending", metadata_json=metadata, created_at=datetime.now(UTC)))

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise


class WhatsAppTemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.templates = WhatsAppTemplateRepository(db)

    def status(self, integration: Integration) -> dict[str, Any]:
        return whatsapp_status(integration)

    def validate_local_configuration(self, integration: Integration, admin_user: User) -> dict[str, Any]:
        result = validate_whatsapp_local_configuration(integration)
        self._audit(admin_user.id, "whatsapp_config_validated", integration.id, {"result": "succeeded", "code": result["code"]})
        self._commit()
        return result

    def list_templates(self, integration: Integration) -> list[WhatsAppTemplate]:
        ensure_whatsapp_integration(integration)
        return list(self.templates.list_by_integration(integration.id))

    def get_template(self, integration: Integration, template_id: int) -> WhatsAppTemplate:
        ensure_whatsapp_integration(integration)
        template = self.templates.get(template_id)
        if not template or template.integration_id != integration.id:
            raise WhatsAppNotFoundError("Plantilla WhatsApp no encontrada", code="template_not_found")
        return template

    def create_template(self, integration: Integration, payload: WhatsAppTemplateCreate, admin_user: User) -> WhatsAppTemplate:
        ensure_whatsapp_integration(integration)
        self._ensure_provider_configurable(integration)
        template = WhatsAppTemplate(
            integration_id=integration.id,
            name=payload.name,
            language=payload.language,
            category=payload.category,
            status=WhatsAppTemplateStatus.draft,
            purpose=payload.purpose,
            components_schema=payload.components_schema.model_dump(),
        )
        self.templates.create(template)
        self._audit(admin_user.id, "whatsapp_template_created", integration.id, {"template_id": template.id, "purpose": template.purpose.value, "status": template.status.value})
        self._commit()
        self.db.refresh(template)
        return template

    def update_template(self, integration: Integration, template_id: int, payload: WhatsAppTemplateUpdate, admin_user: User) -> WhatsAppTemplate:
        template = self.get_template(integration, template_id)
        changes = payload.model_dump(exclude_unset=True)
        for field in ("name", "language", "purpose"):
            if field in changes:
                setattr(template, field, changes[field])
        if "components_schema" in changes and payload.components_schema is not None:
            template.components_schema = payload.components_schema.model_dump()
        self._audit(admin_user.id, "whatsapp_template_updated", integration.id, {"template_id": template.id, "fields": sorted(changes.keys())})
        self._commit()
        self.db.refresh(template)
        return template

    @staticmethod
    def _ensure_provider_configurable(integration: Integration) -> None:
        if integration.provider != IntegrationProvider.whatsapp_cloud:
            raise WhatsAppValidationError("Proveedor incorrecto para plantillas WhatsApp", code="wrong_whatsapp_provider")

    def _audit(self, user_id: int, action: str, integration_id: int, metadata: dict[str, Any]) -> None:
        self.db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                entity_name="Integration",
                entity_id=str(integration_id),
                metadata_json={"integration_id": integration_id, "provider": "whatsapp_cloud", **metadata},
                created_at=datetime.now(UTC),
            )
        )

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise


@dataclass(frozen=True)
class WhatsAppWebhookVerificationResult:
    success: bool
    challenge: str | None
    code: str
    message: str


@dataclass(frozen=True)
class WhatsAppWebhookReceiveResult:
    accepted: bool
    received_count: int
    stored_count: int
    duplicate_count: int
    ignored_count: int
    failed_count: int


class WhatsAppWebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = WhatsAppWebhookEventRepository(db)

    def verify_callback(self, *, mode: str | None, verify_token: str | None, challenge: str | None) -> WhatsAppWebhookVerificationResult:
        expected = settings.whatsapp_webhook_verify_token
        if not expected:
            raise WhatsAppValidationError("Webhook WhatsApp no configurado", code="webhook_verify_token_missing")
        if mode != "subscribe" or not challenge:
            raise WhatsAppValidationError("Solicitud de verificacion invalida", code="webhook_verify_invalid_request")
        if not verify_token or not hmac.compare_digest(verify_token, expected):
            self._audit_security("whatsapp_webhook_verify_rejected", {"reason": "invalid_token"})
            self._commit()
            raise WhatsAppValidationError("No pudimos verificar el webhook", code="webhook_verify_token_invalid")
        return WhatsAppWebhookVerificationResult(True, challenge, "webhook_verified", "Webhook verificado")

    def receive(self, *, raw_body: bytes, signature_header: str | None) -> WhatsAppWebhookReceiveResult:
        if not raw_body:
            raise WhatsAppValidationError("Body vacio", code="webhook_empty_body")
        if len(raw_body) > settings.whatsapp_webhook_max_body_bytes:
            logger.warning("whatsapp_webhook_rejected code=body_too_large size=%s", len(raw_body))
            raise WhatsAppValidationError("Body demasiado grande", code="webhook_body_too_large")
        signature_valid = self._verify_signature(raw_body, signature_header)
        payload_hash = hashlib.sha256(raw_body).hexdigest()
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WhatsAppValidationError("JSON invalido", code="webhook_invalid_json") from exc

        extracted = self._extract_events(payload, payload_hash=payload_hash, signature_valid=signature_valid)
        stored = duplicates = ignored = failed = 0
        now = datetime.now(UTC)
        for event in extracted:
            existing = self.events.get_by_event_key(event.event_key)
            if existing:
                existing.duplicate = True
                existing.received_count += 1
                existing.last_received_at = now
                existing.processing_status = WhatsAppWebhookProcessingStatus.duplicate
                duplicates += 1
                continue
            self.events.create(event)
            if event.processing_status == WhatsAppWebhookProcessingStatus.failed:
                failed += 1
            elif event.processing_status == WhatsAppWebhookProcessingStatus.ignored:
                ignored += 1
            else:
                stored += 1
        self._commit()
        logger.info("whatsapp_webhook_received events=%s stored=%s duplicates=%s ignored=%s failed=%s", len(extracted), stored, duplicates, ignored, failed)
        return WhatsAppWebhookReceiveResult(True, len(extracted), stored, duplicates, ignored, failed)

    def list_events(
        self,
        *,
        integration_id: int,
        event_type: WhatsAppWebhookEventType | None = None,
        processing_status: WhatsAppWebhookProcessingStatus | None = None,
        duplicate: bool | None = None,
        limit: int = 100,
    ) -> list[WhatsAppWebhookEvent]:
        return list(self.events.list_recent(integration_id=integration_id, event_type=event_type, processing_status=processing_status, duplicate=duplicate, limit=limit))

    def get_event(self, *, integration_id: int, event_id: int) -> WhatsAppWebhookEvent:
        event = self.events.get(event_id)
        if not event or event.integration_id != integration_id:
            raise WhatsAppNotFoundError("Evento WhatsApp no encontrado", code="webhook_event_not_found")
        return event

    def webhook_status(self, integration_id: int) -> dict[str, Any]:
        events = self.events.list_recent(integration_id=integration_id, limit=100)
        last = events[0] if events else None
        last_error = next((item.error_message for item in events if item.error_message), None)
        return {
            "integration_id": integration_id,
            "public_url": settings.whatsapp_webhook_public_url,
            "public_url_configured": bool(settings.whatsapp_webhook_public_url),
            "verify_token_configured": bool(settings.whatsapp_webhook_verify_token),
            "app_secret_configured": bool(settings.whatsapp_app_secret),
            "signature_required": settings.whatsapp_webhook_require_signature,
            "max_body_bytes": settings.whatsapp_webhook_max_body_bytes,
            "retention_days": settings.whatsapp_webhook_event_retention_days,
            "last_received_at": last.received_at if last else None,
            "recent_total": len(events),
            "last_error": last_error,
        }

    def _verify_signature(self, raw_body: bytes, signature_header: str | None) -> bool:
        if not settings.whatsapp_webhook_require_signature:
            return False
        app_secret = settings.whatsapp_app_secret
        if not app_secret:
            raise WhatsAppValidationError("Firma webhook requerida pero no configurada", code="webhook_app_secret_missing")
        if not signature_header:
            self._audit_security("whatsapp_webhook_signature_rejected", {"reason": "missing_signature"})
            self._commit()
            raise WhatsAppValidationError("Firma webhook requerida", code="webhook_signature_missing")
        prefix = "sha256="
        if not signature_header.startswith(prefix):
            self._audit_security("whatsapp_webhook_signature_rejected", {"reason": "invalid_prefix"})
            self._commit()
            raise WhatsAppValidationError("Firma webhook invalida", code="webhook_signature_invalid")
        calculated = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature_header[len(prefix) :], calculated):
            self._audit_security("whatsapp_webhook_signature_rejected", {"reason": "mismatch"})
            self._commit()
            raise WhatsAppValidationError("Firma webhook invalida", code="webhook_signature_invalid")
        return True

    def _extract_events(self, payload: Any, *, payload_hash: str, signature_valid: bool) -> list[WhatsAppWebhookEvent]:
        if not isinstance(payload, dict):
            raise WhatsAppValidationError("Payload webhook no reconocido", code="webhook_payload_unrecognized")
        object_type = _safe_str(payload.get("object"), max_length=80)
        extracted: list[WhatsAppWebhookEvent] = []
        entries = payload.get("entry") if isinstance(payload.get("entry"), list) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            changes = entry.get("changes") if isinstance(entry.get("changes"), list) else []
            for change in changes:
                if not isinstance(change, dict):
                    continue
                extracted.extend(self._events_from_change(change, object_type=object_type, payload_hash=payload_hash, signature_valid=signature_valid))
                if len(extracted) >= MAX_EVENTS_PER_WEBHOOK:
                    return extracted[:MAX_EVENTS_PER_WEBHOOK]
        if not extracted:
            extracted.append(self._unknown_event(object_type=object_type, field=None, payload_hash=payload_hash, signature_valid=signature_valid, value={}))
        return extracted

    def _events_from_change(self, change: dict[str, Any], *, object_type: str | None, payload_hash: str, signature_valid: bool) -> list[WhatsAppWebhookEvent]:
        field = _safe_str(change.get("field"), max_length=80)
        value = change.get("value") if isinstance(change.get("value"), dict) else {}
        metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        phone_number_id = _safe_str(metadata.get("phone_number_id"), max_length=80)
        integration_id, resolution_metadata = self._resolve_integration(phone_number_id)
        events: list[WhatsAppWebhookEvent] = []
        messages = value.get("messages") if isinstance(value.get("messages"), list) else []
        statuses = value.get("statuses") if isinstance(value.get("statuses"), list) else []
        for message in messages:
            if isinstance(message, dict):
                events.append(self._message_event(message, object_type, field, phone_number_id, integration_id, resolution_metadata, payload_hash, signature_valid))
        for item in statuses:
            if isinstance(item, dict):
                events.append(self._status_event(item, object_type, field, phone_number_id, integration_id, resolution_metadata, payload_hash, signature_valid))
        if events:
            return events
        if field == "message_template_status_update" or "message_template_id" in value:
            return [self._template_event(value, object_type, field, phone_number_id, integration_id, resolution_metadata, payload_hash, signature_valid)]
        return [self._unknown_event(object_type=object_type, field=field, payload_hash=payload_hash, signature_valid=signature_valid, value=value, phone_number_id=phone_number_id, integration_id=integration_id, resolution_metadata=resolution_metadata)]

    def _message_event(self, message: dict[str, Any], object_type: str | None, field: str | None, phone_number_id: str | None, integration_id: int | None, resolution_metadata: dict[str, Any], payload_hash: str, signature_valid: bool) -> WhatsAppWebhookEvent:
        external_id = _safe_str(message.get("id"), max_length=160)
        event_key = f"message:{external_id}" if external_id else f"message:unknown:{_stable_hash(_safe_minimal(message))}"
        return self._build_event(
            integration_id=integration_id,
            event_key=event_key,
            payload_hash=payload_hash,
            object_type=object_type,
            field=field,
            event_type=WhatsAppWebhookEventType.inbound_message,
            external_message_id=external_id,
            phone_number_id=phone_number_id,
            sender_phone_hash=_safe_phone_hash(_safe_str(message.get("from"), max_length=30)),
            recipient_phone_hash=None,
            status=None,
            occurred_at=_timestamp_to_datetime(message.get("timestamp")),
            processing_status=WhatsAppWebhookProcessingStatus.classified,
            signature_valid=signature_valid,
            safe_metadata={"message_type": _safe_str(message.get("type"), max_length=40), **resolution_metadata},
        )

    def _status_event(self, item: dict[str, Any], object_type: str | None, field: str | None, phone_number_id: str | None, integration_id: int | None, resolution_metadata: dict[str, Any], payload_hash: str, signature_valid: bool) -> WhatsAppWebhookEvent:
        external_id = _safe_str(item.get("id"), max_length=160)
        status_value = _safe_str(item.get("status"), max_length=40) or "unknown"
        timestamp = _safe_str(item.get("timestamp"), max_length=32) or "no-ts"
        event_key = f"status:{external_id}:{status_value}:{timestamp}" if external_id else f"status:unknown:{_stable_hash({'status': status_value, 'timestamp': timestamp})}"
        event_type = {
            "sent": WhatsAppWebhookEventType.message_sent,
            "delivered": WhatsAppWebhookEventType.message_delivered,
            "read": WhatsAppWebhookEventType.message_read,
            "failed": WhatsAppWebhookEventType.message_failed,
        }.get(status_value, WhatsAppWebhookEventType.unknown)
        errors = item.get("errors") if isinstance(item.get("errors"), list) else []
        first_error = errors[0] if errors and isinstance(errors[0], dict) else {}
        return self._build_event(
            integration_id=integration_id,
            event_key=event_key,
            payload_hash=payload_hash,
            object_type=object_type,
            field=field,
            event_type=event_type,
            external_message_id=external_id,
            phone_number_id=phone_number_id,
            sender_phone_hash=None,
            recipient_phone_hash=_safe_phone_hash(_safe_str(item.get("recipient_id"), max_length=30)),
            status=status_value,
            occurred_at=_timestamp_to_datetime(item.get("timestamp")),
            processing_status=WhatsAppWebhookProcessingStatus.classified if event_type != WhatsAppWebhookEventType.unknown else WhatsAppWebhookProcessingStatus.ignored,
            signature_valid=signature_valid,
            safe_metadata={"conversation_present": bool(item.get("conversation")), **resolution_metadata},
            error_code=_safe_str(first_error.get("code"), max_length=80),
            error_message=_safe_str(first_error.get("title"), max_length=300),
        )

    def _template_event(self, value: dict[str, Any], object_type: str | None, field: str | None, phone_number_id: str | None, integration_id: int | None, resolution_metadata: dict[str, Any], payload_hash: str, signature_valid: bool) -> WhatsAppWebhookEvent:
        stable = {"field": field, "template_id": value.get("message_template_id"), "event": value.get("event"), "phone_number_id": phone_number_id}
        return self._build_event(
            integration_id=integration_id,
            event_key=f"template:{_stable_hash(stable)}",
            payload_hash=payload_hash,
            object_type=object_type,
            field=field,
            event_type=WhatsAppWebhookEventType.template_status,
            external_message_id=_safe_str(value.get("message_template_id"), max_length=160),
            phone_number_id=phone_number_id,
            sender_phone_hash=None,
            recipient_phone_hash=None,
            status=_safe_str(value.get("event"), max_length=40),
            occurred_at=None,
            processing_status=WhatsAppWebhookProcessingStatus.classified,
            signature_valid=signature_valid,
            safe_metadata={"template_name": _safe_str(value.get("message_template_name"), max_length=120), **resolution_metadata},
        )

    def _unknown_event(self, *, object_type: str | None, field: str | None, payload_hash: str, signature_valid: bool, value: dict[str, Any], phone_number_id: str | None = None, integration_id: int | None = None, resolution_metadata: dict[str, Any] | None = None) -> WhatsAppWebhookEvent:
        stable = {"object": object_type, "field": field, "phone_number_id": phone_number_id, "keys": sorted(value.keys())[:20], "payload_hash": payload_hash}
        return self._build_event(
            integration_id=integration_id,
            event_key=f"unknown:{_stable_hash(stable)}",
            payload_hash=payload_hash,
            object_type=object_type,
            field=field,
            event_type=WhatsAppWebhookEventType.unknown,
            external_message_id=None,
            phone_number_id=phone_number_id,
            sender_phone_hash=None,
            recipient_phone_hash=None,
            status=None,
            occurred_at=None,
            processing_status=WhatsAppWebhookProcessingStatus.ignored,
            signature_valid=signature_valid,
            safe_metadata={"value_keys": sorted(value.keys())[:20], **(resolution_metadata or {})},
        )

    def _build_event(self, *, integration_id: int | None, event_key: str, payload_hash: str, object_type: str | None, field: str | None, event_type: WhatsAppWebhookEventType, external_message_id: str | None, phone_number_id: str | None, sender_phone_hash: str | None, recipient_phone_hash: str | None, status: str | None, occurred_at: datetime | None, processing_status: WhatsAppWebhookProcessingStatus, signature_valid: bool, safe_metadata: dict[str, Any], error_code: str | None = None, error_message: str | None = None) -> WhatsAppWebhookEvent:
        now = datetime.now(UTC)
        return WhatsAppWebhookEvent(
            integration_id=integration_id,
            event_key=event_key[:180],
            payload_hash=payload_hash,
            object_type=object_type,
            field=field,
            event_type=event_type,
            external_message_id=external_message_id,
            phone_number_id_masked=_mask_external_id(phone_number_id),
            phone_number_id_hash=_stable_hash({"phone_number_id": phone_number_id}) if phone_number_id else None,
            sender_phone_hash=sender_phone_hash,
            recipient_phone_hash=recipient_phone_hash,
            status=status,
            occurred_at=occurred_at,
            received_at=now,
            last_received_at=now,
            processed_at=now,
            processing_status=processing_status,
            signature_valid=signature_valid,
            duplicate=False,
            received_count=1,
            safe_metadata=safe_metadata,
            error_code=error_code,
            error_message=error_message,
        )

    def _resolve_integration(self, phone_number_id: str | None) -> tuple[int | None, dict[str, Any]]:
        if not phone_number_id:
            return None, {"integration_resolution": "missing_phone_number_id"}
        matches: list[Integration] = []
        for integration in self.db.scalars(select(Integration).where(Integration.provider == IntegrationProvider.whatsapp_cloud)):
            try:
                config = parse_whatsapp_config(integration.config or {})
            except WhatsAppValidationError:
                continue
            if config.phone_number_id == phone_number_id:
                matches.append(integration)
        if len(matches) == 1:
            return matches[0].id, {"integration_resolution": "matched"}
        if len(matches) > 1:
            self._audit_security("whatsapp_webhook_integration_duplicate", {"matches": len(matches)})
            return None, {"integration_resolution": "duplicate_configuration"}
        self._audit_security("whatsapp_webhook_integration_unresolved", {"reason": "unknown_phone_number_id"})
        return None, {"integration_resolution": "unresolved"}

    def _audit_security(self, action: str, metadata: dict[str, Any]) -> None:
        self.db.add(AuditLog(user_id=None, action=action, entity_name="WhatsAppWebhook", entity_id="public", metadata_json=metadata, created_at=datetime.now(UTC)))

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise


def serialize_webhook_event(event: WhatsAppWebhookEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "integration_id": event.integration_id,
        "event_key_partial": _partial(event.event_key),
        "payload_hash_partial": _partial(event.payload_hash),
        "object_type": event.object_type,
        "field": event.field,
        "event_type": event.event_type,
        "external_message_id_partial": _partial(event.external_message_id) if event.external_message_id else None,
        "phone_number_id_masked": event.phone_number_id_masked,
        "status": event.status,
        "occurred_at": event.occurred_at,
        "received_at": event.received_at,
        "last_received_at": event.last_received_at,
        "processed_at": event.processed_at,
        "processing_status": event.processing_status,
        "signature_valid": event.signature_valid,
        "duplicate": event.duplicate,
        "received_count": event.received_count,
        "safe_metadata": event.safe_metadata,
        "error_code": event.error_code,
        "error_message": event.error_message,
    }


def _safe_str(value: Any, *, max_length: int) -> str | None:
    if value is None:
        return None
    return str(value)[:max_length]


def _timestamp_to_datetime(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(str(value)), tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_minimal(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value.get(key) for key in ("id", "type", "timestamp") if key in value}


def _safe_phone_hash(value: str | None) -> str | None:
    if not value:
        return None
    try:
        normalized = normalize_phone(value)
        return phone_hmac(normalized.e164)
    except WhatsAppValidationError:
        return None


def _mask_external_id(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("+"):
        try:
            return mask_phone_e164(value)
        except WhatsAppValidationError:
            pass
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"


def _partial(value: str) -> str:
    if len(value) <= 12:
        return "****"
    return f"{value[:6]}...{value[-4:]}"
