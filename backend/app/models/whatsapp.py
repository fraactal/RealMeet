from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppMessageStatus,
    WhatsAppTemplateCategory,
    WhatsAppTemplatePurpose,
    WhatsAppTemplateStatus,
    WhatsAppWebhookEventType,
    WhatsAppWebhookProcessingStatus,
)


class WhatsAppConsent(Base, TimestampMixin):
    __tablename__ = "whatsapp_consents"
    __table_args__ = (
        UniqueConstraint("user_id", "phone_hash", "purpose", name="uq_whatsapp_consents_user_phone_purpose"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    phone_masked: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[WhatsAppConsentStatus] = mapped_column(
        Enum(WhatsAppConsentStatus, name="whatsapp_consent_status"),
        default=WhatsAppConsentStatus.granted,
        nullable=False,
    )
    purpose: Mapped[WhatsAppConsentPurpose] = mapped_column(Enum(WhatsAppConsentPurpose, name="whatsapp_consent_purpose"), nullable=False)
    source: Mapped[WhatsAppConsentSource] = mapped_column(Enum(WhatsAppConsentSource, name="whatsapp_consent_source"), nullable=False)
    consent_text_version: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reason: Mapped[str | None] = mapped_column(String(300))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User")


class WhatsAppTemplate(Base, TimestampMixin):
    __tablename__ = "whatsapp_templates"
    __table_args__ = (
        UniqueConstraint("integration_id", "name", "language", name="uq_whatsapp_templates_integration_name_language"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[WhatsAppTemplateCategory] = mapped_column(Enum(WhatsAppTemplateCategory, name="whatsapp_template_category"), nullable=False)
    status: Mapped[WhatsAppTemplateStatus] = mapped_column(
        Enum(WhatsAppTemplateStatus, name="whatsapp_template_status"),
        default=WhatsAppTemplateStatus.draft,
        nullable=False,
    )
    purpose: Mapped[WhatsAppTemplatePurpose] = mapped_column(Enum(WhatsAppTemplatePurpose, name="whatsapp_template_purpose"), nullable=False)
    components_schema: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    external_template_id: Mapped[str | None] = mapped_column(String(120))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    integration = relationship("Integration")


class WhatsAppMessage(Base, TimestampMixin):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        UniqueConstraint("integration_id", "idempotency_key", name="uq_whatsapp_messages_integration_idempotency"),
        Index("ix_whatsapp_messages_external_message_id", "external_message_id"),
        Index("ix_whatsapp_messages_status_created_at", "status", "created_at"),
        Index("ix_whatsapp_messages_integration_created_at", "integration_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int] = mapped_column(ForeignKey("integrations.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    template_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_templates.id"), nullable=False)
    purpose: Mapped[WhatsAppTemplatePurpose] = mapped_column(Enum(WhatsAppTemplatePurpose, name="whatsapp_template_purpose"), nullable=False)
    recipient_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_masked: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[WhatsAppMessageStatus] = mapped_column(
        Enum(WhatsAppMessageStatus, name="whatsapp_message_status"),
        default=WhatsAppMessageStatus.queued,
        nullable=False,
    )
    external_message_id: Mapped[str | None] = mapped_column(String(160))
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    attempt: Mapped[int] = mapped_column(nullable=False, default=1)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(300))

    integration = relationship("Integration")
    user = relationship("User")
    template = relationship("WhatsAppTemplate")


class WhatsAppWebhookEvent(Base):
    __tablename__ = "whatsapp_webhook_events"
    __table_args__ = (UniqueConstraint("event_key", name="uq_whatsapp_webhook_events_event_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    integration_id: Mapped[int | None] = mapped_column(ForeignKey("integrations.id"))
    event_key: Mapped[str] = mapped_column(String(180), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(80))
    field: Mapped[str | None] = mapped_column(String(80))
    event_type: Mapped[WhatsAppWebhookEventType] = mapped_column(Enum(WhatsAppWebhookEventType, name="whatsapp_webhook_event_type"), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(160))
    phone_number_id_masked: Mapped[str | None] = mapped_column(String(40))
    phone_number_id_hash: Mapped[str | None] = mapped_column(String(64))
    sender_phone_hash: Mapped[str | None] = mapped_column(String(64))
    recipient_phone_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(40))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[WhatsAppWebhookProcessingStatus] = mapped_column(
        Enum(WhatsAppWebhookProcessingStatus, name="whatsapp_webhook_processing_status"),
        nullable=False,
    )
    signature_valid: Mapped[bool] = mapped_column(nullable=False, default=False)
    duplicate: Mapped[bool] = mapped_column(nullable=False, default=False)
    received_count: Mapped[int] = mapped_column(nullable=False, default=1)
    safe_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    integration = relationship("Integration")
