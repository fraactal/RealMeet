class WhatsAppError(Exception):
    def __init__(self, message: str, *, code: str = "whatsapp_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class WhatsAppValidationError(WhatsAppError):
    pass


class WhatsAppNotFoundError(WhatsAppError):
    pass


class WhatsAppPermissionError(WhatsAppError):
    pass
