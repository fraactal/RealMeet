from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.integrations.enums import IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import IntegrationValidationError
from app.integrations.validation import validate_safe_metadata, validate_secret_reference
from app.schemas.common import ORMModel


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
            return validate_safe_metadata(value, field_name="config")
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        try:
            return validate_secret_reference(value)
        except IntegrationValidationError as exc:
            raise ValueError(str(exc)) from exc


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
            return validate_safe_metadata(value, field_name="config")
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
