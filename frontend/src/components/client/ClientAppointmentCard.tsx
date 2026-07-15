import type { ReactNode } from "react";

import type { Appointment, DashboardAppointment } from "../../types";
import { formatDateTime, formatLongDate, formatTime } from "../../utils/dates";
import { getConsultationModeLabel, getMeetingStatusLabel } from "../../utils/labels";
import { Button } from "../ui/Button";
import { Icon } from "../ui/Icon";
import { StatusBadge } from "../ui/StatusBadge";

type ClientAppointment = Appointment | DashboardAppointment;

interface ClientAppointmentCardProps {
  appointment: ClientAppointment;
  actions?: ReactNode;
  emphasis?: boolean;
  showMeeting?: boolean;
}

function getMeetingLabel(appointment: ClientAppointment): string {
  if (!("meeting" in appointment) || !appointment.meeting) {
    return appointment.consultation_mode === "presencial" ? "Atencion presencial" : "Reunion pendiente";
  }

  return getMeetingStatusLabel(appointment.meeting.status);
}

export function ClientAppointmentCard({ actions, appointment, emphasis = false, showMeeting = true }: ClientAppointmentCardProps) {
  const hasMeetingLink = "meeting" in appointment && appointment.meeting?.status === "active" && appointment.meeting.join_url;

  return (
    <article
      className={
        emphasis
          ? "rounded-lg border border-brand-200 bg-brand-50/60 p-5 shadow-soft"
          : "rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      }
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={appointment.status} />
            <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-xs font-semibold text-ink-600 ring-1 ring-slate-200">
              <Icon className="h-4 w-4" name="clock" />
              {getConsultationModeLabel(appointment.consultation_mode)}
            </span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-ink-900">{formatLongDate(appointment.start_datetime)}</h3>
            <p className="mt-1 text-sm font-medium text-ink-600">
              {formatTime(appointment.start_datetime)} a {formatTime(appointment.end_datetime)}
            </p>
          </div>
          <dl className="grid gap-2 text-sm text-ink-500 sm:grid-cols-2">
            <div>
              <dt className="font-semibold text-ink-700">Profesional</dt>
              <dd>Profesional seleccionado</dd>
            </div>
            <div>
              <dt className="font-semibold text-ink-700">Reserva</dt>
              <dd>{formatDateTime(appointment.start_datetime)}</dd>
            </div>
            {showMeeting ? (
              <div className="sm:col-span-2">
                <dt className="font-semibold text-ink-700">Reunion</dt>
                <dd>{getMeetingLabel(appointment)}</dd>
              </div>
            ) : null}
          </dl>
        </div>
        <div className="flex flex-wrap gap-2 md:justify-end">
          {hasMeetingLink ? (
            <a href={appointment.meeting?.join_url ?? undefined} rel="noreferrer" target="_blank">
              <Button size="sm">Abrir reunion</Button>
            </a>
          ) : null}
          {actions}
        </div>
      </div>
    </article>
  );
}

export function ClientAppointmentDateLine({ appointment }: { appointment: ClientAppointment }) {
  return (
    <span>
      {formatLongDate(appointment.start_datetime)}, {formatTime(appointment.start_datetime)}
    </span>
  );
}
