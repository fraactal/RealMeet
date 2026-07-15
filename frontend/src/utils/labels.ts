import type { AppointmentStatus, ConsultationMode, IntegrationExecutionStatus, IntegrationProvider, IntegrationStatus, IntegrationType, UserRole } from "../types";

export type MeetingStatus = "active" | "inactive" | "pending" | "unknown";

export const appointmentStatusLabels: Record<AppointmentStatus, string> = {
  pending: "Pendiente",
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
