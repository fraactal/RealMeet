from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.payments.contracts import PaymentCreateInput, PaymentProviderError, PaymentProviderHealth, PaymentProviderResult
from app.payments.enums import PaymentOrderStatus


class FakePaymentProvider:
    provider = "fake"

    async def create_payment(self, payload: PaymentCreateInput) -> PaymentProviderResult:
        external_id = "fake_pay_" + sha256(payload.idempotency_key.encode("utf-8")).hexdigest()[:24]
        return PaymentProviderResult(
            external_payment_id=external_id,
            status=PaymentOrderStatus.pending,
            expires_at=payload.expires_at or datetime.now(UTC) + timedelta(minutes=30),
            provider_reference={"provider": "fake", "operation": "create"},
        )

    async def get_payment(self, external_payment_id: str) -> PaymentProviderResult:
        return PaymentProviderResult(
            external_payment_id=external_payment_id,
            status=PaymentOrderStatus.pending,
            provider_reference={"provider": "fake", "operation": "get"},
        )

    async def cancel_payment(self, external_payment_id: str) -> PaymentProviderResult:
        return PaymentProviderResult(
            external_payment_id=external_payment_id,
            status=PaymentOrderStatus.cancelled,
            provider_reference={"provider": "fake", "operation": "cancel"},
        )

    async def refund_payment(self, external_payment_id: str) -> PaymentProviderResult:
        raise PaymentProviderError("Refunds are not implemented in 17.1.", code="payment_refund_not_implemented")

    async def health_check(self) -> PaymentProviderHealth:
        return PaymentProviderHealth(healthy=True, code="payment_provider_fake_healthy", message="Fake payment provider is available.")
