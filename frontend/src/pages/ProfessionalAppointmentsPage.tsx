import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import {
  cancelProfessionalAppointment,
  completeProfessionalAppointment,
  confirmProfessionalAppointment,
  fetchProfessionalAppointments,
  markNoShowProfessionalAppointment,
  updateAppointmentPrivateNotes,
} from "../api/queries";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import type { ProfessionalAppointment } from "../types";

type StatusAction = "confirm" | "cancel" | "complete" | "no_show";

function availableActions(appointment: ProfessionalAppointment): StatusAction[] {
  if (appointment.status === "pending") {
    return ["confirm", "cancel"];
  }
  if (appointment.status === "confirmed") {
    return ["complete", "no_show", "cancel"];
  }
  return [];
}

export function ProfessionalAppointmentsPage() {
  const queryClient = useQueryClient();
  const [notesDrafts, setNotesDrafts] = useState<Record<number, string>>({});
  const appointmentsQuery = useQuery({
    queryKey: ["professional-appointments"],
    queryFn: fetchProfessionalAppointments,
  });
  const actionMutation = useMutation({
    mutationFn: ({ appointmentId, action }: { appointmentId: number; action: StatusAction }) => {
      if (action === "confirm") {
        return confirmProfessionalAppointment(appointmentId, { reason: "Confirmada por profesional" });
      }
      if (action === "complete") {
        return completeProfessionalAppointment(appointmentId, { reason: "Completada por profesional" });
      }
      if (action === "no_show") {
        return markNoShowProfessionalAppointment(appointmentId, { reason: "Marcada como no show por profesional" });
      }
      return cancelProfessionalAppointment(appointmentId, { reason: "Cancelada por profesional" });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["professional-appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["my-appointments"] });
    },
  });
  const notesMutation = useMutation({
    mutationFn: ({ appointmentId, professional_private_notes }: { appointmentId: number; professional_private_notes: string }) =>
      updateAppointmentPrivateNotes(appointmentId, { professional_private_notes }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["professional-appointments"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Reservas profesionales</h1>
        <p className="text-slate-600">Gestiona estados e historial de tus reservas.</p>
      </div>

      <Card>
        {appointmentsQuery.isLoading ? <p className="text-slate-500">Cargando reservas...</p> : null}
        {appointmentsQuery.isError ? <p className="text-red-600">{normalizeApiError(appointmentsQuery.error).message}</p> : null}
        <div className="space-y-4">
          {appointmentsQuery.data?.map((appointment) => {
            const draft = notesDrafts[appointment.id] ?? appointment.professional_private_notes ?? "";
            return (
              <div key={appointment.id} className="space-y-4 rounded-2xl border border-slate-200 p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-ink">{new Date(appointment.start_datetime).toLocaleString()}</p>
                    <p className="text-sm text-slate-500">Reserva #{appointment.id} - Cliente #{appointment.client_id}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Badge label={appointment.status} />
                    {availableActions(appointment).map((action) => (
                      <button
                        key={action}
                        className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                        disabled={actionMutation.isPending}
                        onClick={() => actionMutation.mutate({ appointmentId: appointment.id, action })}
                      >
                        {action === "confirm" ? "Confirmar" : action === "complete" ? "Completar" : action === "no_show" ? "No show" : "Cancelar"}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="block space-y-2 text-sm font-medium text-slate-700">
                  Notas privadas
                  <textarea
                    value={draft}
                    onChange={(event) => setNotesDrafts((current) => ({ ...current, [appointment.id]: event.target.value }))}
                    rows={3}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal outline-none focus:border-brand"
                    placeholder="Notas de atencion"
                  />
                </label>
                <button
                  className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                  disabled={notesMutation.isPending}
                  onClick={() => notesMutation.mutate({ appointmentId: appointment.id, professional_private_notes: draft })}
                >
                  Guardar notas
                </button>
                {appointment.history?.length ? (
                  <div className="border-t border-slate-100 pt-3 text-sm text-slate-500">
                    <p className="font-semibold text-slate-700">Historial</p>
                    <div className="mt-2 space-y-1">
                      {appointment.history.map((item) => (
                        <p key={item.id}>
                          {new Date(item.created_at).toLocaleString()} - {item.old_status ?? "nuevo"} a {item.new_status}
                        </p>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
          {!appointmentsQuery.isLoading && appointmentsQuery.data?.length === 0 ? (
            <p className="text-slate-500">Todavia no tienes reservas asignadas.</p>
          ) : null}
        </div>
        {actionMutation.isError ? <p className="mt-4 text-sm text-red-600">{normalizeApiError(actionMutation.error).message}</p> : null}
        {notesMutation.isError ? <p className="mt-4 text-sm text-red-600">{normalizeApiError(notesMutation.error).message}</p> : null}
      </Card>
    </div>
  );
}
