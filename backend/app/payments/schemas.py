from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.payments.enums import PaymentCurrency, PaymentOrderStatus, PaymentProviderKey
from app.schemas.admin import PageMeta
from app.schemas.common import ORMModel


class PaymentOrderCreate(BaseModel):
    appointment_id: int | None = None
    client_id: int | None = None
    professional_id: int | None = None
    specialty_id: int | None = None
    provider: PaymentProviderKey = PaymentProviderKey.fake
    amount: Decimal | None = None
    currency: PaymentCurrency = PaymentCurrency.CLP
    description: str | None = Field(default=None, max_length=255)
    expires_at: datetime | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("payment_amount_must_be_positive")
        if value != value.to_integral_value():
            raise ValueError("payment_currency_clp_requires_integer_amount")
        return value


class PaymentOrderSubmit(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=220)


class PaymentOrderCancel(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class PaymentOrderPublicRead(ORMModel):
    id: int
    appointment_id: int | None
    description: str | None
    amount: Decimal
    currency: PaymentCurrency
    status: PaymentOrderStatus
    expires_at: datetime | None
    paid_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime


class PaymentCheckoutRead(BaseModel):
    id: int
    appointment_id: int | None
    description: str | None
    amount: Decimal
    currency: PaymentCurrency
    status: PaymentOrderStatus
    expires_at: datetime | None
    checkout_available: bool
    test_environment: bool = True
    message: str


class PaymentCheckoutAction(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaymentOrderAdminRead(PaymentOrderPublicRead):
    client_id: int | None
    professional_id: int | None
    specialty_id: int | None
    provider: PaymentProviderKey
    external_payment_id: str | None
    idempotency_key: str | None
    request_fingerprint: str | None
    rejected_at: datetime | None
    failed_at: datetime | None
    last_error_code: str | None
    last_error_message: str | None
    created_by_user_id: int | None
    updated_at: datetime


class PaymentOrderStatusHistoryRead(ORMModel):
    id: int
    payment_order_id: int
    previous_status: str | None
    new_status: str
    reason_code: str | None
    reason_summary: str | None
    changed_by_user_id: int | None
    provider_reference: dict | None
    created_at: datetime


class PaymentOrderListResponse(BaseModel):
    items: list[PaymentOrderAdminRead]
    meta: PageMeta


class PaymentProviderHealthRead(BaseModel):
    provider: PaymentProviderKey
    healthy: bool
    code: str
    message: str


class PaymentReconcileRead(BaseModel):
    result: str
    payment_order: PaymentOrderAdminRead
