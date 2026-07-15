from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.whatsapp.enums import (
    WhatsAppConsentPurpose,
    WhatsAppConsentSource,
    WhatsAppConsentStatus,
    WhatsAppTemplateCategory,
    WhatsAppTemplatePurpose,
    WhatsAppTemplateStatus,
    WhatsAppWebhookEventType,
    WhatsAppWebhookProcessingStatus,
)


ALLOWED_TEMPLATE_VARIABLES = {
    "client_name",
    "professional_name",
    "appointment_date",
    "appointment_time",
    "appointment_modality",
    "meeting_url",
    "platform_name",
}
FORBIDDEN_TEMPLATE_VARIABLES = {
    "diagnosis",
    "medical_history",
    "private_notes",
    "appointment_reason",
    "rut",
    "password",
    "token",
    "secret",
    "payment_data",
}


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WhatsAppConsentGrant(StrictBaseModel):
    phone: str = Field(min_length=8, max_length=40)
    purpose: WhatsAppConsentPurpose
    consent_text_version: str = Field(min_length=1, max_length=40)
    explicit_confirmation: bool

    @model_validator(mode="after")
    def require_confirmation(self) -> "WhatsAppConsentGrant":
        if not self.explicit_confirmation:
            raise ValueError("El consentimiento requiere confirmacion explicita")
        return self


class WhatsAppConsentAdminCorrection(StrictBaseModel):
    user_id: int = Field(gt=0)
    phone: str = Field(min_length=8, max_length=40)
    purpose: WhatsAppConsentPurpose
    consent_text_version: str = Field(min_length=1, max_length=40)
    reason: str = Field(min_length=8, max_length=300)


class WhatsAppConsentRead(BaseModel):
    id: int
    user_id: int
    phone_masked: str
    status: WhatsAppConsentStatus
    purpose: WhatsAppConsentPurpose
    source: WhatsAppConsentSource
    consent_text_version: str
    granted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppConsentSummary(BaseModel):
    id: int
    user_id: int
    phone_masked: str
    status: WhatsAppConsentStatus
    purpose: WhatsAppConsentPurpose
    source: WhatsAppConsentSource
    granted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppVariableDefinition(StrictBaseModel):
    key: str = Field(min_length=1, max_length=80)
    required: bool = True
    sensitive: bool = False

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        normalized = value.strip()
        if normalized in FORBIDDEN_TEMPLATE_VARIABLES:
            raise ValueError("Variable no permitida")
        if normalized not in ALLOWED_TEMPLATE_VARIABLES:
            raise ValueError("Variable fuera del catalogo permitido")
        return normalized

    @model_validator(mode="after")
    def reject_sensitive(self) -> "WhatsAppVariableDefinition":
        if self.sensitive:
            raise ValueError("No se permiten variables sensibles en 13.1A")
        return self


class WhatsAppComponentsSchema(StrictBaseModel):
    variables: list[WhatsAppVariableDefinition] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_unique_variables(self) -> "WhatsAppComponentsSchema":
        keys = [item.key for item in self.variables]
        if len(keys) != len(set(keys)):
            raise ValueError("Las variables deben ser unicas")
        return self


class WhatsAppTemplateCreate(StrictBaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9_]+$")
    language: str = Field(default="es_CL", min_length=2, max_length=10)
    category: WhatsAppTemplateCategory = WhatsAppTemplateCategory.utility
    purpose: WhatsAppTemplatePurpose
    components_schema: WhatsAppComponentsSchema = Field(default_factory=WhatsAppComponentsSchema)

    @field_validator("category")
    @classmethod
    def only_utility(cls, value: WhatsAppTemplateCategory) -> WhatsAppTemplateCategory:
        if value != WhatsAppTemplateCategory.utility:
            raise ValueError("Solo se permiten plantillas utility en 13.1A")
        return value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.replace("-", "_")


class WhatsAppTemplateUpdate(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120, pattern=r"^[a-z0-9_]+$")
    language: str | None = Field(default=None, min_length=2, max_length=10)
    purpose: WhatsAppTemplatePurpose | None = None
    components_schema: WhatsAppComponentsSchema | None = None

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        return value.replace("-", "_") if value else value


class WhatsAppTemplateRead(BaseModel):
    id: int
    integration_id: int
    name: str
    language: str
    category: WhatsAppTemplateCategory
    status: WhatsAppTemplateStatus
    purpose: WhatsAppTemplatePurpose
    components_schema: dict[str, Any]
    external_template_id: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppIntegrationStatusRead(BaseModel):
    integration_id: int
    provider: str
    status: str
    enabled: bool
    locally_configured: bool
    operational_for_sending: bool
    message: str
    waba_id_partial: str
    phone_number_id_partial: str
    display_phone_number_masked: str
    graph_api_version: str
    default_language: str
    country_code: str


class WhatsAppValidationRead(BaseModel):
    success: bool
    code: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WhatsAppWebhookEventRead(BaseModel):
    id: int
    integration_id: int | None
    event_key_partial: str
    payload_hash_partial: str
    object_type: str | None
    field: str | None
    event_type: WhatsAppWebhookEventType
    external_message_id_partial: str | None
    phone_number_id_masked: str | None
    status: str | None
    occurred_at: datetime | None
    received_at: datetime
    last_received_at: datetime | None
    processed_at: datetime | None
    processing_status: WhatsAppWebhookProcessingStatus
    signature_valid: bool
    duplicate: bool
    received_count: int
    safe_metadata: dict[str, Any]
    error_code: str | None
    error_message: str | None


class WhatsAppWebhookStatusRead(BaseModel):
    integration_id: int
    public_url_configured: bool
    verify_token_configured: bool
    app_secret_configured: bool
    signature_required: bool
    max_body_bytes: int
    retention_days: int
    last_received_at: datetime | None
    recent_total: int
    last_error: str | None = None


class WhatsAppWebhookReceiveRead(BaseModel):
    accepted: bool
    received_count: int
    stored_count: int
    duplicate_count: int
    ignored_count: int
    failed_count: int
