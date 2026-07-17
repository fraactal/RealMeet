import type {
  AppointmentStatus,
  ConsultationMode,
  IntegrationExecutionStatus,
  IntegrationProvider,
  IntegrationStatus,
  IntegrationType,
  PaymentOrderStatus,
  PaymentTiming,
  UserRole,
  WhatsAppConsentPurpose,
  WhatsAppConsentSource,
  WhatsAppConsentStatus,
  WhatsAppMessageStatus,
  WhatsAppNotificationPolicyValue,
  WhatsAppTemplatePurpose,
  WhatsAppTemplateStatus,
  WhatsAppWebhookEventType,
  WhatsAppWebhookProcessingStatus,
} from "../types";

export type MeetingStatus = "active" | "inactive" | "pending" | "provisioning" | "ready" | "failed" | "fallback_ready" | "cancelled" | "not_required" | "unknown";

export const appointmentStatusLabels: Record<AppointmentStatus, string> = {
  pending: "Pendiente",
  pending_payment: "Pendiente de pago",
  confirmed: "Confirmada",
  cancelled: "Cancelada",
  completed: "Completada",
  no_show: "No asistio",
};

export const roleLabels: Record<UserRole, string> = {
  admin: "Administrador",
  professional: "Profesional",
  client: "Cliente",
};

const consultationModeLabels: Record<string, string> = {
  online: "Online",
  in_person: "Presencial",
  presencial: "Presencial",
  hybrid: "Hibrida",
};

export const meetingStatusLabels: Record<MeetingStatus, string> = {
  active: "Reunion disponible",
  inactive: "Reunion inactiva",
  pending: "Reunion pendiente",
  provisioning: "Preparando enlace",
  ready: "Reunion lista",
  failed: "Enlace pendiente",
  fallback_ready: "Reunion simulada",
  cancelled: "Reunion cancelada",
  not_required: "Sin reunion automatica",
  unknown: "Estado de reunion no disponible",
};

export function getAppointmentStatusLabel(status: AppointmentStatus | string): string {
  return appointmentStatusLabels[status as AppointmentStatus] ?? status;
}

export function getConsultationModeLabel(mode?: ConsultationMode | string | null): string {
  if (!mode) {
    return "Sin modalidad";
  }

  return consultationModeLabels[mode] ?? mode;
}

export function getRoleLabel(role?: UserRole | string | null): string {
  if (!role) {
    return "Usuario";
  }

  return roleLabels[role as UserRole] ?? role;
}

export function getMeetingStatusLabel(status?: MeetingStatus | string | null): string {
  if (!status) {
    return meetingStatusLabels.unknown;
  }

  return meetingStatusLabels[status as MeetingStatus] ?? status;
}

export const integrationTypeLabels: Record<IntegrationType, string> = {
  meeting: "Reuniones",
  calendar: "Calendario",
  messaging: "Mensajeria",
  email: "Correo",
  automation: "Automatizacion",
  webhook: "Webhook",
};

export const integrationProviderLabels: Record<IntegrationProvider, string> = {
  mock: "Mock interno",
  google_meet: "Google Meet",
  google_calendar: "Google Calendar",
  microsoft_365: "Microsoft 365",
  whatsapp_cloud: "WhatsApp Cloud API",
  twilio: "Twilio",
  smtp: "SMTP",
  n8n: "n8n",
  generic_webhook: "Webhook generico",
};

export const integrationStatusLabels: Record<IntegrationStatus, string> = {
  not_configured: "Sin configurar",
  configured: "Configurada",
  healthy: "Saludable",
  error: "Con error",
  unsupported: "No soportada",
};

export const integrationExecutionStatusLabels: Record<IntegrationExecutionStatus, string> = {
  pending: "Pendiente",
  running: "En ejecucion",
  succeeded: "Exitosa",
  failed: "Fallida",
  skipped: "Omitida",
};

export function getIntegrationTypeLabel(value: IntegrationType | string): string {
  return integrationTypeLabels[value as IntegrationType] ?? value;
}

export function getIntegrationProviderLabel(value: IntegrationProvider | string): string {
  return integrationProviderLabels[value as IntegrationProvider] ?? value;
}

export function getIntegrationStatusLabel(value: IntegrationStatus | string): string {
  return integrationStatusLabels[value as IntegrationStatus] ?? value;
}

export function getIntegrationExecutionStatusLabel(value: IntegrationExecutionStatus | string): string {
  return integrationExecutionStatusLabels[value as IntegrationExecutionStatus] ?? value;
}

export const whatsappConsentStatusLabels: Record<WhatsAppConsentStatus, string> = {
  not_granted: "No otorgado",
  granted: "Otorgado",
  revoked: "Revocado",
};

export const whatsappConsentPurposeLabels: Record<WhatsAppConsentPurpose, string> = {
  appointment_transactional: "Mensajes transaccionales",
  appointment_reminders: "Recordatorios",
  appointment_updates: "Actualizaciones de reserva",
};

export const whatsappConsentSourceLabels: Record<WhatsAppConsentSource, string> = {
  self_service: "Otorgado por el usuario",
  admin_correction: "Correccion administrativa",
  imported: "Importado",
  system_migration: "Migracion del sistema",
};

export const whatsappTemplateStatusLabels: Record<WhatsAppTemplateStatus, string> = {
  draft: "Borrador",
  pending: "Pendiente",
  approved: "Aprobada",
  rejected: "Rechazada",
  paused: "Pausada",
  disabled: "Deshabilitada",
  unknown: "Desconocida",
};

export const whatsappTemplatePurposeLabels: Record<WhatsAppTemplatePurpose, string> = {
  appointment_confirmation: "Confirmacion de reserva",
  appointment_reminder: "Recordatorio de reserva",
  appointment_updated: "Reserva actualizada",
  appointment_cancelled: "Reserva cancelada",
  meeting_ready: "Enlace de reunion listo",
};

export const whatsappWebhookEventTypeLabels: Record<WhatsAppWebhookEventType, string> = {
  inbound_message: "Mensaje entrante",
  message_sent: "Mensaje enviado",
  message_delivered: "Entregado",
  message_read: "Leido",
  message_failed: "Fallido",
  template_status: "Estado de plantilla",
  unknown: "Desconocido",
};

export const whatsappWebhookProcessingStatusLabels: Record<WhatsAppWebhookProcessingStatus, string> = {
  received: "Recibido",
  classified: "Clasificado",
  ignored: "Ignorado",
  duplicate: "Duplicado",
  failed: "Fallido",
};

export const whatsappMessageStatusLabels: Record<WhatsAppMessageStatus, string> = {
  queued: "En cola",
  accepted: "Aceptado",
  sent: "Enviado",
  delivered: "Entregado",
  read: "Leido",
  failed: "Fallido",
  cancelled: "Cancelado",
  skipped: "Omitido",
};

export const whatsappNotificationPolicyLabels: Record<WhatsAppNotificationPolicyValue, string> = {
  email_only: "Solo correo",
  whatsapp_preferred: "Preferir WhatsApp y usar correo como respaldo",
  whatsapp_required: "Solo WhatsApp",
  email_and_whatsapp: "Correo y WhatsApp",
  notifications_disabled: "Notificaciones deshabilitadas",
};

export const appointmentNotificationEventLabels: Record<string, string> = {
  appointment_confirmed: "Reserva confirmada",
  appointment_updated: "Reserva actualizada",
  appointment_cancelled: "Reserva cancelada",
  appointment_reminder: "Recordatorio",
  meeting_ready: "Enlace de reunion listo",
};

export const appointmentNotificationStatusLabels: Record<string, string> = {
  pending: "Pendiente",
  processing: "En proceso",
  accepted: "Aceptada",
  sent: "Enviada",
  delivered: "Entregada",
  read: "Leida",
  failed: "Fallida",
  skipped: "Omitida",
  cancelled: "Cancelada",
  fallback_sent: "Fallback enviado",
};

export const whatsappVariableLabels: Record<string, string> = {
  client_name: "Nombre del cliente",
  professional_name: "Nombre del profesional",
  appointment_date: "Fecha de la reserva",
  appointment_time: "Hora de la reserva",
  appointment_modality: "Modalidad",
  meeting_url: "Enlace de reunion",
  platform_name: "Nombre de la plataforma",
};

export function getWhatsAppConsentStatusLabel(value: WhatsAppConsentStatus | string): string {
  return whatsappConsentStatusLabels[value as WhatsAppConsentStatus] ?? value;
}

export function getWhatsAppConsentPurposeLabel(value: WhatsAppConsentPurpose | string): string {
  return whatsappConsentPurposeLabels[value as WhatsAppConsentPurpose] ?? value;
}

export function getWhatsAppConsentSourceLabel(value: WhatsAppConsentSource | string): string {
  return whatsappConsentSourceLabels[value as WhatsAppConsentSource] ?? value;
}

export function getWhatsAppTemplateStatusLabel(value: WhatsAppTemplateStatus | string): string {
  return whatsappTemplateStatusLabels[value as WhatsAppTemplateStatus] ?? value;
}

export function getWhatsAppTemplatePurposeLabel(value: WhatsAppTemplatePurpose | string): string {
  return whatsappTemplatePurposeLabels[value as WhatsAppTemplatePurpose] ?? value;
}

export function getWhatsAppWebhookEventTypeLabel(value: WhatsAppWebhookEventType | string): string {
  return whatsappWebhookEventTypeLabels[value as WhatsAppWebhookEventType] ?? value;
}

export function getWhatsAppWebhookProcessingStatusLabel(value: WhatsAppWebhookProcessingStatus | string): string {
  return whatsappWebhookProcessingStatusLabels[value as WhatsAppWebhookProcessingStatus] ?? value;
}

export function getWhatsAppMessageStatusLabel(value: WhatsAppMessageStatus | string): string {
  return whatsappMessageStatusLabels[value as WhatsAppMessageStatus] ?? value;
}

export function getWhatsAppNotificationPolicyLabel(value: WhatsAppNotificationPolicyValue | string): string {
  return whatsappNotificationPolicyLabels[value as WhatsAppNotificationPolicyValue] ?? value;
}

export function getAppointmentNotificationEventLabel(value: string): string {
  return appointmentNotificationEventLabels[value] ?? value;
}

export function getAppointmentNotificationStatusLabel(value: string): string {
  return appointmentNotificationStatusLabels[value] ?? value;
}

export function getWebhookEventTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    "appointment.created": "Reserva creada",
    "appointment.updated": "Reserva actualizada",
    "appointment.cancelled": "Reserva cancelada",
    "appointment.confirmed": "Reserva confirmada",
    "meeting.ready": "Reunion lista",
    "payment.order.created": "Orden de pago creada",
    "payment.approved": "Pago aprobado",
    "payment.rejected": "Pago rechazado",
    "payment.expired": "Pago expirado",
    "document.generated": "Documento generado",
    "notification.sent": "Notificacion enviada",
    "notification.failed": "Notificacion fallida",
    "client.created": "Cliente creado",
    "professional.created": "Profesional creado",
    "webhook.test": "Prueba webhook",
    "n8n.workflow.test": "Prueba workflow n8n",
  };
  return labels[value] ?? value;
}

export function getWebhookDeliveryStatusLabel(value: string): string {
  const labels: Record<string, string> = {
    pending: "Pendiente",
    sending: "Enviando",
    succeeded: "Exitosa",
    failed: "Fallida",
    skipped: "Omitida",
  };
  return labels[value] ?? value;
}

export const paymentOrderStatusLabels: Record<PaymentOrderStatus, string> = {
  draft: "Borrador",
  pending: "Pendiente",
  requires_action: "Requiere accion",
  approved: "Aprobado",
  rejected: "Rechazado",
  cancelled: "Cancelado",
  expired: "Expirado",
  failed: "Fallido",
  refunded: "Reembolsado",
};

export function getPaymentOrderStatusLabel(value: PaymentOrderStatus | string): string {
  return paymentOrderStatusLabels[value as PaymentOrderStatus] ?? value;
}

export const paymentTimingLabels: Record<PaymentTiming, string> = {
  no_payment: "No requiere pago",
  pay_before_confirmation: "Pago antes de confirmar",
  pay_after_confirmation: "Pago despues de confirmar",
};

export function getPaymentTimingLabel(value: PaymentTiming | string): string {
  return paymentTimingLabels[value as PaymentTiming] ?? value;
}
