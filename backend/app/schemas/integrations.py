from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import IntegrationValidationError
from app.integrations.validation import validate_safe_metadata, validate_secret_reference
from app.schemas.common import ORMModel
from app.whatsapp.configuration import parse_whatsapp_config
from app.automation.n8n import validate_n8n_config


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IntegrationCreate(StrictBaseModel):
    name: str = Field(min_length=1, max_length=120)
    integration_type: IntegrationType
    provider: IntegrationProvider
    config: dict[str, Any] = Field(default_factory=dict)
    secret_reference: str | None = Field(default=None, max_length=128)

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            safe_value = {key: nested for key, nested in value.items() if key != "secret_references"}
            validate_safe_metadata(safe_value, field_name="config")
            if isinstance(value.get("secret_references"), dict):
                for reference in value["secret_references"].values():
                    validate_secret_reference(reference)
            return value
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        try:
            return validate_secret_reference(value)
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def validate_provider_specific_config(self) -> "IntegrationCreate":
        if self.provider == IntegrationProvider.whatsapp_cloud:
            if self.integration_type != IntegrationType.messaging:
                raise ValueError("whatsapp_cloud requires integration_type messaging")
            parse_whatsapp_config(self.config)
        if self.provider == IntegrationProvider.n8n:
            if self.integration_type != IntegrationType.automation:
                raise ValueError("n8n requires integration_type automation")
            try:
                validate_n8n_config(self.config)
            except Exception as exc:
                detail = getattr(exc, "detail", str(exc))
                raise ValueError(str(detail)) from exc
        if self.provider == IntegrationProvider.mercado_pago:
            if self.integration_type != IntegrationType.payment:
                raise ValueError("mercado_pago requires integration_type payment")
        return self


class IntegrationUpdate(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    config: dict[str, Any] | None = None
    secret_reference: str | None = Field(default=None, max_length=128)

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        try:
            safe_value = {key: nested for key, nested in value.items() if key != "secret_references"}
            validate_safe_metadata(safe_value, field_name="config")
            if isinstance(value.get("secret_references"), dict):
                for reference in value["secret_references"].values():
                    validate_secret_reference(reference)
            return value
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        try:
            return validate_secret_reference(value)
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc


class IntegrationRead(ORMModel):
    id: int
    name: str
    integration_type: IntegrationType
    provider: IntegrationProvider
    enabled: bool
    status: IntegrationStatus
    config: dict[str, Any]
    secret_reference: str | None
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime


class IntegrationPageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class IntegrationListResponse(BaseModel):
    items: list[IntegrationRead]
    meta: IntegrationPageMeta


class IntegrationOperationResultRead(BaseModel):
    success: bool
    code: str
    message: str
    skipped: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_id: int | None = None
    duration_ms: int = 0


class IntegrationTestRequest(StrictBaseModel):
    idempotency_key: str = Field(min_length=1, max_length=180)


class IntegrationExecutionCreate(StrictBaseModel):
    integration_id: int
    operation: str = Field(min_length=1, max_length=120)
    entity_type: str | None = Field(default=None, max_length=80)
    entity_id: str | None = Field(default=None, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=180)
    status: IntegrationExecutionStatus = IntegrationExecutionStatus.pending
    attempt: int = Field(default=1, ge=1)
    request_metadata: dict[str, Any] | None = None
    response_metadata: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, max_length=80)
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @field_validator("request_metadata", "response_metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any] | None, info) -> dict[str, Any] | None:
        if value is None:
            return None
        try:
            return validate_safe_metadata(value, field_name=info.field_name)
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc


class IntegrationExecutionRead(ORMModel):
    id: int
    integration_id: int
    operation: str
    entity_type: str | None
    entity_id: str | None
    idempotency_key: str
    status: IntegrationExecutionStatus
    attempt: int
    request_metadata: dict[str, Any] | None
    response_metadata: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class GoogleOAuthAuthorizationUrlRead(BaseModel):
    authorization_url: str
    state_expires_at: datetime


class GoogleOAuthCallbackRead(BaseModel):
    success: bool
    status: str
    message: str
    redirect_url: str | None = None


class GoogleOAuthStatusRead(BaseModel):
    status: str
    provider: IntegrationProvider
    connected: bool
    external_account_email: str | None = None
    external_account_id: str | None = None
    scopes: list[str] = Field(default_factory=list)
    authorized_at: datetime | None = None
    expires_at: datetime | None = None
    last_refresh_at: datetime | None = None
    revoked_at: datetime | None = None
    last_error_message: str | None = None


class GoogleOAuthDisconnectRead(BaseModel):
    success: bool
    status: str
    message: str


class GoogleMeetMeetingCreate(StrictBaseModel):
    title: str = Field(default="Prueba de integracion RealMeet", min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    start_at: datetime
    end_at: datetime
    timezone: str = Field(default="America/Santiago", min_length=1, max_length=80)
    attendees: list[str] = Field(default_factory=list, max_length=10)
    idempotency_key: str = Field(min_length=1, max_length=180)
    send_updates: str = Field(default="none", pattern="^(none|all|externalOnly)$")

    @model_validator(mode="after")
    def validate_interval(self) -> "GoogleMeetMeetingCreate":
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("start_at and end_at must include timezone")
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be before end_at")
        normalized = [item.lower() for item in self.attendees]
        if len(set(normalized)) != len(normalized):
            raise ValueError("attendees must be unique")
        if any("@" not in item or len(item) > 254 for item in self.attendees):
            raise ValueError("attendees must be valid emails")
        return self


class GoogleMeetMeetingCancel(StrictBaseModel):
    idempotency_key: str = Field(min_length=1, max_length=180)
    send_updates: str = Field(default="none", pattern="^(none|all|externalOnly)$")


class GoogleMeetMeetingRead(BaseModel):
    provider: str
    external_event_id: str
    external_calendar_id: str
    meeting_url: str | None = None
    html_link: str | None = None
    conference_id: str | None = None
    status: str
    start_at: datetime
    end_at: datetime
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
