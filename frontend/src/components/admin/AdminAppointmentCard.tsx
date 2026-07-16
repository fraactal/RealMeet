import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAdminAppointmentExternalCalendar,
  reconcileAdminAppointmentExternalCalendar,
  retryAdminAppointmentExternalCalendar,
} from "../../api/queries";
import type { Appointment, DashboardAppointment } from "../../types";
import { formatDateTime, formatTime } from "../../utils/dates";
import { getConsultationModeLabel, getIntegrationProviderLabel, getMeetingStatusLabel } from "../../utils/labels";
import { Button, Icon, StatusBadge } from "../ui";

type AdminAppointment = Appointment | DashboardAppointment;

interface AdminAppointmentCardProps {
  appointment: AdminAppointment;
}

export function AdminAppointmentCard({ appointment }: AdminAppointmentCardProps) {
  const meeting = "meeting" in appointment ? appointment.meeting : null;

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
          {meeting ? (
            <div className="sm:col-span-2">
              <dt className="font-semibold text-ink-700">Reunion</dt>
              <dd>
                {getMeetingStatusLabel(meeting.status)}
                {meeting.provider ? ` - ${getIntegrationProviderLabel(meeting.provider)}` : ""}
                {meeting.fallback_used ? " - fallback" : ""}
              </dd>
              {meeting.error_message ? <dd className="text-danger-600">{meeting.error_message}</dd> : null}
            </div>
          ) : null}
        </dl>
      </div>
      {"id" in appointment ? <AdminExternalCalendarSync appointmentId={appointment.id} /> : null}
    </article>
  );
}

function AdminExternalCalendarSync({ appointmentId }: { appointmentId: number }) {
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ["admin-appointment-external-calendar", appointmentId],
    queryFn: () => fetchAdminAppointmentExternalCalendar(appointmentId),
  });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin-appointment-external-calendar", appointmentId] });
  const retryMutation = useMutation({ mutationFn: () => retryAdminAppointmentExternalCalendar(appointmentId), onSuccess: refresh });
  const reconcileMutation = useMutation({ mutationFn: () => reconcileAdminAppointmentExternalCalendar(appointmentId), onSuccess: refresh });
  const item = statusQuery.data;
  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-semibold text-ink-900">Calendario externo</p>
          {statusQuery.isLoading ? <p className="text-ink-500">Cargando estado...</p> : null}
          {!statusQuery.isLoading && !item ? <p className="text-ink-500">Sin evento externo vinculado.</p> : null}
          {item ? (
            <div className="mt-1 text-ink-600">
              <p>{externalCalendarStatusLabel(item.status)} · {item.provider}</p>
              {item.last_synced_at ? <p>Ultima sincronizacion: {formatDateTime(item.last_synced_at)}</p> : null}
              {item.last_error_message ? <p className="text-danger-600">{item.last_error_message}</p> : null}
            </div>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button isLoading={retryMutation.isPending} onClick={() => retryMutation.mutate()} size="sm" variant="secondary">Reintentar</Button>
          <Button isLoading={reconcileMutation.isPending} onClick={() => reconcileMutation.mutate()} size="sm" variant="secondary">Reconciliar</Button>
        </div>
      </div>
    </div>
  );
}

function externalCalendarStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "Pendiente",
    created: "Sincronizado",
    updated: "Actualizado",
    cancelled: "Cancelado",
    failed: "Con error",
    reconcile_required: "Requiere revision",
  };
  return labels[status] ?? "Estado no disponible";
}
