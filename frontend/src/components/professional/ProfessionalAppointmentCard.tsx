import type { ReactNode } from "react";

import { Button, Card, Icon, StatusBadge } from "../ui";
import type { DashboardAppointment, ProfessionalAppointment } from "../../types";
import { formatDateTime, formatLongDate, formatTime } from "../../utils/dates";
import { getAppointmentStatusLabel, getConsultationModeLabel, getMeetingStatusLabel } from "../../utils/labels";

type AppointmentLike = DashboardAppointment | ProfessionalAppointment;

interface ProfessionalAppointmentCardProps {
  appointment: AppointmentLike;
  actions?: ReactNode;
  detail?: ReactNode;
}

function hasMeeting(appointment: AppointmentLike): appointment is ProfessionalAppointment {
  return "meeting" in appointment;
}

export function ProfessionalAppointmentCard({ actions, appointment, detail }: ProfessionalAppointmentCardProps) {
  const meeting = hasMeeting(appointment) ? appointment.meeting : null;

  return (
    <Card className="p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={appointment.status} />
            {appointment.consultation_mode ? (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {getConsultationModeLabel(appointment.consultation_mode)}
              </span>
            ) : null}
            {meeting ? (
              <span className="rounded-full bg-info-100 px-3 py-1 text-xs font-semibold text-info-700">
                {getMeetingStatusLabel(meeting.status)}
              </span>
            ) : null}
          </div>
          <div>
            <p className="text-lg font-semibold text-ink-900">{formatLongDate(appointment.start_datetime)}</p>
            <p className="mt-1 flex items-center gap-2 text-sm font-medium text-ink-700">
              <Icon className="h-4 w-4" name="clock" />
              {formatTime(appointment.start_datetime)} - {formatTime(appointment.end_datetime)}
            </p>
          </div>
          <p className="text-sm text-ink-500">
            {meeting?.message ?? (hasMeeting(appointment) ? "Cliente registrado" : getAppointmentStatusLabel(appointment.status))}
          </p>
        </div>
        {actions ? <div className="flex flex-wrap gap-2 lg:justify-end">{actions}</div> : null}
      </div>
      {detail ? <div className="mt-4 border-t border-slate-100 pt-4">{detail}</div> : null}
    </Card>
  );
}

export function AppointmentLinkButton({ href, label }: { href?: string | null; label: string }) {
  if (!href) {
    return null;
  }

  return (
    <Button onClick={() => window.open(href, "_blank", "noopener,noreferrer")} size="sm" variant="secondary">
      {label}
    </Button>
  );
}

export function AppointmentDateLine({ appointment }: { appointment: AppointmentLike }) {
  return <span>{formatDateTime(appointment.start_datetime)}</span>;
}
