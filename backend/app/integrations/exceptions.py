class IntegrationValidationError(ValueError):
    """Raised when integration configuration or metadata is unsafe."""


class IntegrationError(Exception):
    default_message = "Integration error"

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.code = code or self.__class__.__name__


class IntegrationNotFoundError(IntegrationError):
    default_message = "Integration not found"


class IntegrationProviderUnsupportedError(IntegrationError):
    default_message = "Integration provider is not supported"


class IntegrationDisabledError(IntegrationError):
    default_message = "Integration is disabled"


class IntegrationConfigurationError(IntegrationError):
    default_message = "Integration configuration is invalid"


class IntegrationOperationUnsupportedError(IntegrationError):
    default_message = "Integration operation is not supported"


class IntegrationExecutionInProgressError(IntegrationError):
    default_message = "Integration execution is already in progress"


class IntegrationProviderExecutionError(IntegrationError):
    default_message = "Integration provider execution failed"


class IntegrationProviderUnexpectedError(IntegrationError):
    default_message = "Integration provider failed unexpectedly"
