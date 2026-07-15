from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.automation.enums import WebhookEventType
from app.automation.n8n import N8N_ALLOWED_EVENTS, validate_webhook_path
from app.integrations.validation import validate_secret_reference


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class N8nWorkflowCreate(StrictBaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    webhook_path: str = Field(min_length=1, max_length=240)
    event_types: list[WebhookEventType] = Field(min_length=1)
    secret_reference: str = Field(min_length=3, max_length=128)

    @field_validator("webhook_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return validate_webhook_path(value)

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        return validate_secret_reference(value) or value

    @model_validator(mode="after")
    def validate_events(self) -> "N8nWorkflowCreate":
        if len(set(self.event_types)) != len(self.event_types):
            raise ValueError("event_types must be unique")
        if any(event not in N8N_ALLOWED_EVENTS for event in self.event_types):
            raise ValueError("unsupported n8n event type")
        return self


class N8nWorkflowUpdate(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    webhook_path: str | None = Field(default=None, min_length=1, max_length=240)
    event_types: list[WebhookEventType] | None = None
    secret_reference: str | None = Field(default=None, min_length=3, max_length=128)

    @field_validator("webhook_path")
    @classmethod
    def validate_path(cls, value: str | None) -> str | None:
        return validate_webhook_path(value) if value is not None else None

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        return validate_secret_reference(value)

    @field_validator("event_types")
    @classmethod
    def validate_events(cls, value: list[WebhookEventType] | None) -> list[WebhookEventType] | None:
        if value is not None and (not value or len(set(value)) != len(value) or any(event not in N8N_ALLOWED_EVENTS for event in value)):
            raise ValueError("event_types must be supported, non-empty and unique")
        return value


class N8nWorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    subscription_id: int
    name: str
    description: str | None
    webhook_path: str
    event_types: list[str]
    enabled: bool
    secret_reference: str
    last_triggered_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_code: str | None
    created_at: datetime
    updated_at: datetime
