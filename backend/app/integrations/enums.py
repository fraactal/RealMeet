import enum


class IntegrationType(str, enum.Enum):
    meeting = "meeting"
    calendar = "calendar"
    messaging = "messaging"
    email = "email"
    automation = "automation"
    webhook = "webhook"
    payment = "payment"


class IntegrationProvider(str, enum.Enum):
    mock = "mock"
    google_meet = "google_meet"
    google_calendar = "google_calendar"
    microsoft_365 = "microsoft_365"
    whatsapp_cloud = "whatsapp_cloud"
    twilio = "twilio"
    smtp = "smtp"
    n8n = "n8n"
    generic_webhook = "generic_webhook"
    mercado_pago = "mercado_pago"


class IntegrationStatus(str, enum.Enum):
    not_configured = "not_configured"
    configured = "configured"
    healthy = "healthy"
    error = "error"
    unsupported = "unsupported"


class IntegrationExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
