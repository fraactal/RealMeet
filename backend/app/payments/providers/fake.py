from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.payments.contracts import PaymentCreateInput, PaymentProviderError, PaymentProviderHealth, PaymentProviderResult, PaymentRefundInput, PaymentRefundProviderResult
from app.payments.enums import PaymentCurrency, PaymentOrderStatus


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
        return PaymentProviderResult(external_payment_id=external_payment_id, status=PaymentOrderStatus.refunded, provider_reference={"provider": "fake", "operation": "refund"})

    async def create_refund(self, payload: PaymentRefundInput) -> PaymentRefundProviderResult:
        external_id = "fake_ref_" + sha256(payload.idempotency_key.encode("utf-8")).hexdigest()[:24]
        reason = (payload.reason or "").lower()
        if "fail" in reason:
            raise PaymentProviderError("Fallo fake controlado.", code="fake_refund_failed")
        status = "rejected" if "reject" in reason else "processing" if "pending" in reason else "approved"
        return PaymentRefundProviderResult(external_refund_id=external_id, status=status, amount=payload.amount, currency=payload.currency, processed_at=datetime.now(UTC) if status == "approved" else None, provider_reference={"provider": "fake", "operation": "create_refund", "status": status})

    async def get_refund(self, external_payment_id: str, external_refund_id: str) -> PaymentRefundProviderResult:
        status = "rejected" if "reject" in external_refund_id else "failed" if "fail" in external_refund_id else "approved"
        return PaymentRefundProviderResult(external_refund_id=external_refund_id, status=status, amount=0, currency=PaymentCurrency.CLP, processed_at=datetime.now(UTC) if status == "approved" else None, provider_reference={"provider": "fake", "operation": "get_refund", "status": status})

    async def health_check(self) -> PaymentProviderHealth:
        return PaymentProviderHealth(healthy=True, code="payment_provider_fake_healthy", message="Fake payment provider is available.")
