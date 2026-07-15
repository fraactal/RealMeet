import type { AppointmentStatus, ConsultationMode, UserRole } from "../types";

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
