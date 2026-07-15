from app.integrations.exceptions import IntegrationOperationUnsupportedError
from app.integrations.results import IntegrationResult
from app.models.integration import Integration


class GoogleMeetIntegrationProvider:
    provider = "google_meet"

    def validate_configuration(self, integration: Integration) -> IntegrationResult:
        return IntegrationResult.ok(
            code="google_meet_oauth_prepared",
            message="Google Meet queda preparado para autorizacion OAuth",
            metadata={"provider": self.provider},
        )

    def health_check(self, integration: Integration) -> IntegrationResult:
        raise IntegrationOperationUnsupportedError("Google Meet aun no ejecuta health checks reales", code="google_meet_not_operational")

    def execute(self, integration: Integration, operation: str, payload: dict | None = None) -> IntegrationResult:
        raise IntegrationOperationUnsupportedError("Google Meet aun no crea reuniones reales", code="google_meet_not_operational")
