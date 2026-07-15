from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.integrations.enums import IntegrationProvider
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationOperationUnsupportedError, IntegrationProviderExecutionError
from app.integrations.results import IntegrationResult
from app.models.integration import Integration


class MockProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulate_error: bool = False
    health: Literal["healthy", "error"] = "healthy"
    response_delay_ms: int = Field(default=0, ge=0, le=250)


class MockIntegrationProvider:
    provider = IntegrationProvider.mock.value

    def validate_configuration(self, integration: Integration) -> IntegrationResult:
        self._parse_config(integration)
        return IntegrationResult.ok(
            code="mock_configuration_valid",
            message="Configuracion mock valida",
            metadata={"provider": self.provider},
        )

    def health_check(self, integration: Integration) -> IntegrationResult:
        config = self._parse_config(integration)
        if config.simulate_error or config.health == "error":
            raise IntegrationProviderExecutionError("Health check mock fallo de forma simulada", code="mock_health_error")
        return IntegrationResult.ok(
            code="mock_health_ok",
            message="Health check mock exitoso",
            metadata={"provider": self.provider, "health": config.health},
        )

    def execute(self, integration: Integration, operation: str, payload: dict[str, Any] | None = None) -> IntegrationResult:
        config = self._parse_config(integration)
        if operation != "test":
            raise IntegrationOperationUnsupportedError("Operacion mock no soportada", code="mock_operation_unsupported")
        if config.simulate_error:
            raise IntegrationProviderExecutionError("Prueba mock fallo de forma simulada", code="mock_test_error")
        return IntegrationResult.ok(
            code="mock_test_ok",
            message="Prueba mock completada",
            metadata={"provider": self.provider, "operation": "test"},
        )

    @staticmethod
    def _parse_config(integration: Integration) -> MockProviderConfig:
        try:
            return MockProviderConfig.model_validate(integration.config or {})
        except ValidationError as exc:
            raise IntegrationConfigurationError("Configuracion mock invalida", code="mock_config_invalid") from exc
