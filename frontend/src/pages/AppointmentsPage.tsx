import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import { cancelAppointment, fetchMyAppointments } from "../api/queries";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import type { Appointment } from "../types";

function canCancel(appointment: Appointment): boolean {
  return ["pending", "confirmed"].includes(appointment.status) && new Date(appointment.start_datetime).getTime() > Date.now();
}

function meetingLabel(appointment: Appointment): string {
  if (!appointment.meeting) {
    return appointment.consultation_mode === "presencial" ? "Atencion presencial" : "Reunion pendiente";
  }
  if (appointment.meeting.status !== "active") {
    return "Reunion inactiva";
  }
  return `Reunion ${appointment.meeting.provider}`;
}

export function AppointmentsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["my-appointments"], queryFn: fetchMyAppointments });
  const cancelMutation = useMutation({
    mutationFn: (appointmentId: number) => cancelAppointment(appointmentId, { reason: "Cancelada por el usuario" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["my-appointments"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Mis reservas</h1>
        <p className="text-slate-600">Historial y agenda del usuario autenticado.</p>
      </div>
      <Card>
        {isLoading ? <p className="text-slate-500">Cargando reservas...</p> : null}
        {isError ? <p className="text-red-600">No fue posible obtener las reservas.</p> : null}
        <div className="space-y-4">
          {data?.map((appointment) => (
            <div key={appointment.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-semibold text-ink">{new Date(appointment.start_datetime).toLocaleString()}</p>
                <p className="text-sm text-slate-500">
                  Reserva #{appointment.id} - {appointment.consultation_mode ?? "modalidad no informada"}
                </p>
                <p className="text-sm text-slate-500">{meetingLabel(appointment)}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge label={appointment.status} />
                {appointment.meeting?.status === "active" && appointment.meeting.join_url ? (
                  <a className="text-sm font-medium text-brand" href={appointment.meeting.join_url} target="_blank" rel="noreferrer">
                    Abrir reunion
                  </a>
                ) : null}
                {canCancel(appointment) ? (
                  <button
                    className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                    disabled={cancelMutation.isPending}
                    onClick={() => cancelMutation.mutate(appointment.id)}
                  >
                    Cancelar
                  </button>
                ) : null}
              </div>
            </div>
          ))}
          {!isLoading && data?.length === 0 ? <p className="text-slate-500">Todavia no hay reservas para este usuario.</p> : null}
        </div>
        {cancelMutation.isError ? <p className="mt-4 text-sm text-red-600">{normalizeApiError(cancelMutation.error).message}</p> : null}
      </Card>
    </div>
  );
}
