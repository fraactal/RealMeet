from typing import Any, Protocol

from app.integrations.results import IntegrationResult
from app.models.integration import Integration


class IntegrationProvider(Protocol):
    provider: str

    def validate_configuration(self, integration: Integration) -> IntegrationResult:
        ...

    def health_check(self, integration: Integration) -> IntegrationResult:
        ...

    def execute(self, integration: Integration, operation: str, payload: dict[str, Any] | None = None) -> IntegrationResult:
        ...
