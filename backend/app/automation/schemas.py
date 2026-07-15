from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.automation.enums import WebhookDeliveryStatus, WebhookEventType
from app.integrations.validation import validate_secret_reference


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WebhookSubscriptionCreate(StrictBaseModel):
    integration_id: int
    name: str = Field(min_length=1, max_length=120)
    target_url: str = Field(min_length=1, max_length=500)
    event_types: list[WebhookEventType] = Field(min_length=1)
    secret_reference: str = Field(min_length=3, max_length=128)

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        return validate_secret_reference(value) or value

    @model_validator(mode="after")
    def validate_unique_events(self) -> "WebhookSubscriptionCreate":
        if len(set(self.event_types)) != len(self.event_types):
            raise ValueError("event_types must be unique")
        return self


class WebhookSubscriptionUpdate(StrictBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    target_url: str | None = Field(default=None, min_length=1, max_length=500)
    event_types: list[WebhookEventType] | None = None
    secret_reference: str | None = Field(default=None, min_length=3, max_length=128)

    @field_validator("secret_reference")
    @classmethod
    def validate_reference(cls, value: str | None) -> str | None:
        return validate_secret_reference(value)

    @field_validator("event_types")
    @classmethod
    def validate_events(cls, value: list[WebhookEventType] | None) -> list[WebhookEventType] | None:
        if value is not None and (not value or len(set(value)) != len(value)):
            raise ValueError("event_types must be non-empty and unique")
        return value


class WebhookSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration_id: int
    name: str
    target_url: str
    event_types: list[str]
    secret_reference: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    event_id: str
    event_type: str
    status: WebhookDeliveryStatus
    attempt: int
    idempotency_key: str
    response_status: int | None
    duration_ms: int | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class WebhookTestResult(BaseModel):
    success: bool
    delivery_id: int | None = None
    status: WebhookDeliveryStatus
    message: str
