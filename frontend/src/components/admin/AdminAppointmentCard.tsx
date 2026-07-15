import type { Appointment, DashboardAppointment } from "../../types";
import { formatDateTime, formatTime } from "../../utils/dates";
import { getConsultationModeLabel } from "../../utils/labels";
import { Icon, StatusBadge } from "../ui";

type AdminAppointment = Appointment | DashboardAppointment;

interface AdminAppointmentCardProps {
  appointment: AdminAppointment;
}

export function AdminAppointmentCard({ appointment }: AdminAppointmentCardProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={appointment.status} />
            <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-xs font-semibold text-ink-600 ring-1 ring-slate-200">
              <Icon className="h-4 w-4" name="clock" />
              {getConsultationModeLabel(appointment.consultation_mode)}
            </span>
          </div>
          <h3 className="mt-3 text-base font-semibold text-ink-900">{formatDateTime(appointment.start_datetime)}</h3>
          <p className="mt-1 text-sm text-ink-500">
            {formatTime(appointment.start_datetime)} a {formatTime(appointment.end_datetime)}
          </p>
        </div>
        <dl className="grid gap-2 text-sm text-ink-500 sm:grid-cols-2 md:text-right">
          <div>
            <dt className="font-semibold text-ink-700">Cliente</dt>
            <dd>Cliente registrado</dd>
          </div>
          <div>
            <dt className="font-semibold text-ink-700">Profesional</dt>
            <dd>Profesional registrado</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}
