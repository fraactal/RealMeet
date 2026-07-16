from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.payments.enums import PaymentCurrency, PaymentOrderStatus


@dataclass(frozen=True)
class PaymentCreateInput:
    amount: Decimal
    currency: PaymentCurrency
    description: str
    idempotency_key: str
    expires_at: datetime | None = None


@dataclass(frozen=True)
class PaymentProviderResult:
    external_payment_id: str
    status: PaymentOrderStatus
    checkout_url: str | None = None
    expires_at: datetime | None = None
    provider_reference: dict[str, str | int | bool | None] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentProviderHealth:
    healthy: bool
    code: str
    message: str


class PaymentProviderError(Exception):
    def __init__(self, message: str, *, code: str = "payment_provider_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class PaymentProvider(Protocol):
    async def create_payment(self, payload: PaymentCreateInput) -> PaymentProviderResult: ...

    async def get_payment(self, external_payment_id: str) -> PaymentProviderResult: ...

    async def cancel_payment(self, external_payment_id: str) -> PaymentProviderResult: ...

    async def refund_payment(self, external_payment_id: str) -> PaymentProviderResult: ...

    async def health_check(self) -> PaymentProviderHealth: ...
