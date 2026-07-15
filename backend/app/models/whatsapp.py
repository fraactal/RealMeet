from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin
from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppTemplateCategory,
    WhatsAppTemplatePurpose,
    WhatsAppTemplateStatus,
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
