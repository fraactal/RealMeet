from app.integrations.contracts import IntegrationProvider as IntegrationProviderContract
from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationProviderUnsupportedError
from app.integrations.providers.mock import MockIntegrationProvider


class IntegrationProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[IntegrationProvider, IntegrationProviderContract] = {}

    def register(self, provider: IntegrationProvider, implementation: IntegrationProviderContract) -> None:
        self._providers[provider] = implementation

    def is_supported(self, provider: IntegrationProvider) -> bool:
        return provider in self._providers

    def get(self, provider: IntegrationProvider) -> IntegrationProviderContract:
        implementation = self._providers.get(provider)
        if not implementation:
            raise IntegrationProviderUnsupportedError("El proveedor aun no esta soportado", code="provider_unsupported")
        return implementation


provider_registry = IntegrationProviderRegistry()
provider_registry.register(IntegrationProvider.mock, MockIntegrationProvider())
