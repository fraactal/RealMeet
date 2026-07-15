from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.enums import IntegrationProvider
from app.models.audit_log import AuditLog
from app.models.integration import Integration
from app.models.user import User
from app.models.whatsapp import WhatsAppConsent, WhatsAppTemplate
from app.whatsapp.configuration import ensure_whatsapp_integration, validate_whatsapp_local_configuration, whatsapp_status
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppTemplateStatus,
)
from app.whatsapp.exceptions import WhatsAppNotFoundError, WhatsAppValidationError
from app.whatsapp.phone import normalize_phone, phone_hmac
from app.whatsapp.repositories import WhatsAppConsentRepository, WhatsAppTemplateRepository
from app.whatsapp.schemas import (
    WhatsAppConsentAdminCorrection,
    WhatsAppConsentGrant,
    WhatsAppTemplateCreate,
    WhatsAppTemplateUpdate,
)


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
