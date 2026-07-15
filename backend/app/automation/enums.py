import enum


class WebhookEventType(str, enum.Enum):
    appointment_created = "appointment.created"
    appointment_updated = "appointment.updated"
    appointment_cancelled = "appointment.cancelled"
    appointment_confirmed = "appointment.confirmed"
    meeting_ready = "meeting.ready"
    notification_sent = "notification.sent"
    notification_failed = "notification.failed"
    client_created = "client.created"
    professional_created = "professional.created"
    webhook_test = "webhook.test"


class WebhookDeliveryStatus(str, enum.Enum):
    pending = "pending"
    sending = "sending"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
