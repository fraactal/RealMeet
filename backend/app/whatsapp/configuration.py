from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.validation import validate_safe_metadata, validate_secret_reference
from app.models.integration import Integration
from app.whatsapp.exceptions import WhatsAppValidationError


GRAPH_VERSION_PATTERN = re.compile(r"^v\d{1,2}\.\d{1,2}$")
LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}([_-][A-Z]{2})?$")
COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")


class WhatsAppSecretReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str | None = None
    app_secret: str | None = None
    verify_token: str | None = None
    phone_hmac_key: str | None = None

    @field_validator("access_token", "app_secret", "verify_token", "phone_hmac_key")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        return validate_secret_reference(value)


class WhatsAppIntegrationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    waba_id: str = Field(min_length=5, max_length=32)
    phone_number_id: str = Field(min_length=5, max_length=32)
    display_phone_number_masked: str = Field(min_length=6, max_length=40)
    graph_api_version: str = Field(min_length=4, max_length=8)
    default_language: str = Field(default="es_CL", min_length=2, max_length=10)
    country_code: str = Field(default="CL", min_length=2, max_length=2)
    secret_references: WhatsAppSecretReferences = Field(default_factory=WhatsAppSecretReferences)

    @field_validator("waba_id", "phone_number_id")
    @classmethod
    def validate_numeric_id(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Debe contener solo digitos")
        return value

    @field_validator("graph_api_version")
    @classmethod
    def validate_graph_version(cls, value: str) -> str:
        if not GRAPH_VERSION_PATTERN.fullmatch(value):
            raise ValueError("Debe usar formato vXX.X")
        return value

    @field_validator("default_language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        normalized = value.replace("-", "_")
        if not LANGUAGE_PATTERN.fullmatch(normalized):
            raise ValueError("Idioma invalido")
        return normalized

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        normalized = value.upper()
        if not COUNTRY_PATTERN.fullmatch(normalized):
            raise ValueError("Pais invalido")
        return normalized

    @field_validator("display_phone_number_masked")
    @classmethod
    def validate_masked_phone(cls, value: str) -> str:
        if "*" not in value:
            raise ValueError("El telefono visible debe estar enmascarado")
        if re.search(r"\d{5,}", value):
            raise ValueError("El telefono visible no puede exponer demasiados digitos continuos")
        return value

    @model_validator(mode="before")
    @classmethod
    def validate_safe_payload(cls, value: Any) -> Any:
        safe_value = value
        if isinstance(value, dict):
            safe_value = {key: nested for key, nested in value.items() if key != "secret_references"}
        try:
            validate_safe_metadata(safe_value, field_name="whatsapp_config")
        except Exception as exc:
            raise ValueError(str(exc)) from exc
        return value


def parse_whatsapp_config(config: dict[str, Any]) -> WhatsAppIntegrationConfig:
    try:
        return WhatsAppIntegrationConfig(**config)
    except Exception as exc:
        raise WhatsAppValidationError("La configuracion WhatsApp local necesita correcciones", code="whatsapp_config_invalid") from exc


def ensure_whatsapp_integration(integration: Integration) -> None:
    if integration.integration_type != IntegrationType.messaging or integration.provider != IntegrationProvider.whatsapp_cloud:
        raise WhatsAppValidationError("La integracion no corresponde a WhatsApp Cloud", code="wrong_whatsapp_integration")


def whatsapp_status(integration: Integration) -> dict[str, Any]:
    ensure_whatsapp_integration(integration)
    config = parse_whatsapp_config(integration.config or {})
    return {
        "integration_id": integration.id,
        "provider": integration.provider.value,
        "status": integration.status.value,
        "enabled": integration.enabled,
        "locally_configured": True,
        "operational_for_sending": False,
        "message": "Configuracion y consentimiento preparados. El envio de mensajes se habilitara en una etapa posterior.",
        "waba_id_partial": _partial(config.waba_id),
        "phone_number_id_partial": _partial(config.phone_number_id),
        "display_phone_number_masked": config.display_phone_number_masked,
        "graph_api_version": config.graph_api_version,
        "default_language": config.default_language,
        "country_code": config.country_code,
    }


def validate_whatsapp_local_configuration(integration: Integration) -> dict[str, Any]:
    ensure_whatsapp_integration(integration)
    config = parse_whatsapp_config(integration.config or {})
    integration.status = IntegrationStatus.configured
    return {
        "success": True,
        "code": "whatsapp_local_config_valid",
        "message": "Configuracion local WhatsApp valida. El envio aun no esta habilitado.",
        "metadata": {
            "provider": IntegrationProvider.whatsapp_cloud.value,
            "operational_for_sending": False,
            "secret_references": sorted(
                key
                for key, value in config.secret_references.model_dump().items()
                if value
            ),
        },
    }


def _partial(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"
