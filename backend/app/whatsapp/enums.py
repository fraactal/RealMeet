import enum


class WhatsAppConsentStatus(str, enum.Enum):
    not_granted = "not_granted"
    granted = "granted"
    revoked = "revoked"


class WhatsAppConsentPurpose(str, enum.Enum):
    appointment_transactional = "appointment_transactional"
    appointment_reminders = "appointment_reminders"
    appointment_updates = "appointment_updates"


class WhatsAppConsentSource(str, enum.Enum):
    self_service = "self_service"
    admin_correction = "admin_correction"
    imported = "imported"
    system_migration = "system_migration"


class WhatsAppTemplateStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    paused = "paused"
    disabled = "disabled"
    unknown = "unknown"


class WhatsAppTemplateCategory(str, enum.Enum):
    utility = "utility"
    authentication = "authentication"
    marketing = "marketing"
    unknown = "unknown"


class WhatsAppTemplatePurpose(str, enum.Enum):
    appointment_confirmation = "appointment_confirmation"
    appointment_reminder = "appointment_reminder"
    appointment_updated = "appointment_updated"
    appointment_cancelled = "appointment_cancelled"
    meeting_ready = "meeting_ready"
