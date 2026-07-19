from app.payments.contracts import PaymentProvider
from app.payments.enums import PaymentProviderKey
from app.payments.providers.fake import FakePaymentProvider


class PaymentProviderNotImplementedError(Exception):
    code = "payment_provider_not_implemented"

    def __init__(self, provider: PaymentProviderKey) -> None:
        self.provider = provider
        super().__init__(f"Payment provider {provider.value} is not implemented.")


class PaymentProviderRegistry:
    def resolve(self, provider: PaymentProviderKey) -> PaymentProvider:
        if provider == PaymentProviderKey.fake:
            return FakePaymentProvider()
        raise PaymentProviderNotImplementedError(provider)


payment_provider_registry = PaymentProviderRegistry()
