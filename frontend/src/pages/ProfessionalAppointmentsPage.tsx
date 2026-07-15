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
import { ProfessionalAppointmentCard } from "../components/professional/ProfessionalAppointmentCard";
import { Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, StatusBadge, Textarea } from "../components/ui";
import type { AppointmentStatus, ProfessionalAppointment } from "../types";
import { formatDateTime } from "../utils/dates";
import { getAppointmentStatusLabel, getConsultationModeLabel, getMeetingStatusLabel } from "../utils/labels";

type StatusAction = "confirm" | "cancel" | "complete" | "no_show";
type StatusFilter = "all" | AppointmentStatus;

function availableActions(appointment: ProfessionalAppointment): StatusAction[] {
  if (appointment.status === "pending") {
    return ["confirm", "cancel"];
  }
  if (appointment.status === "confirmed") {
    return ["complete", "no_show", "cancel"];
  }
  return [];
}

function meetingLabel(appointment: ProfessionalAppointment): string {
  if (!appointment.meeting) {
    return appointment.consultation_mode === "presencial" ? "Atencion presencial" : "Reunion pendiente";
  }
  return appointment.meeting.status === "active" ? `Reunion disponible` : getMeetingStatusLabel(appointment.meeting.status);
}

const actionLabels: Record<StatusAction, string> = {
  confirm: "Confirmar",
  cancel: "Cancelar",
  complete: "Completar",
  no_show: "No asistio",
};

const filterOptions: Array<{ label: string; value: StatusFilter }> = [
  { label: "Todas", value: "all" },
  { label: "Pendientes", value: "pending" },
  { label: "Confirmadas", value: "confirmed" },
  { label: "Completadas", value: "completed" },
  { label: "Canceladas", value: "cancelled" },
  { label: "No asistio", value: "no_show" },
];

export function ProfessionalAppointmentsPage() {
  const queryClient = useQueryClient();
  const [notesDrafts, setNotesDrafts] = useState<Record<number, string>>({});
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
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

  const appointments = appointmentsQuery.data ?? [];
  const filteredAppointments = appointments.filter((appointment) => {
    const matchesStatus = statusFilter === "all" || appointment.status === statusFilter;
    const query = search.trim().toLowerCase();
    const matchesSearch =
      !query ||
      getAppointmentStatusLabel(appointment.status).toLowerCase().includes(query) ||
      getConsultationModeLabel(appointment.consultation_mode).toLowerCase().includes(query) ||
      meetingLabel(appointment).toLowerCase().includes(query);
    return matchesStatus && matchesSearch;
  });

  if (appointmentsQuery.isLoading) {
    return <LoadingState label="Cargando reservas profesionales" />;
  }

  if (appointmentsQuery.isError) {
    return <ErrorState title="No pudimos cargar tus reservas" message={normalizeApiError(appointmentsQuery.error).message} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reservas profesionales"
        description="Revisa solicitudes, confirma atenciones y conserva notas privadas sin perder contexto."
      />

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <Label htmlFor="appointment-search">Buscar en reservas</Label>
            <Input
              id="appointment-search"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Filtra por estado, modalidad o reunion"
              value={search}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {filterOptions.map((option) => (
              <Button
                key={option.value}
                onClick={() => setStatusFilter(option.value)}
                size="sm"
                variant={statusFilter === option.value ? "primary" : "secondary"}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <section>
        <div className="space-y-4">
          {filteredAppointments.map((appointment) => {
            const draft = notesDrafts[appointment.id] ?? appointment.professional_private_notes ?? "";
            return (
              <ProfessionalAppointmentCard
                actions={
                  <>
                    {appointment.meeting?.status === "active" && appointment.meeting.join_url ? (
                      <Button
                        onClick={() => void navigator.clipboard.writeText(appointment.meeting?.join_url ?? "")}
                        size="sm"
                        variant="secondary"
                      >
                        Copiar reunion
                      </Button>
                    ) : null}
                    {availableActions(appointment).map((action) => (
                      <Button
                        disabled={actionMutation.isPending}
                        key={action}
                        onClick={() => actionMutation.mutate({ appointmentId: appointment.id, action })}
                        size="sm"
                        variant={action === "cancel" ? "danger" : "secondary"}
                      >
                        {actionLabels[action]}
                      </Button>
                    ))}
                  </>
                }
                appointment={appointment}
                detail={
                  <div className="space-y-4">
                    <div className="grid gap-3 text-sm text-ink-700 md:grid-cols-3">
                      <div>
                        <p className="font-semibold text-ink-900">Horario</p>
                        <p>{formatDateTime(appointment.start_datetime)}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-ink-900">Modalidad</p>
                        <p>{getConsultationModeLabel(appointment.consultation_mode)}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-ink-900">Reunion</p>
                        <p>{meetingLabel(appointment)}</p>
                      </div>
                    </div>
                    <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <summary className="cursor-pointer text-sm font-semibold text-ink-900">Notas privadas e historial</summary>
                      <div className="mt-4 space-y-4">
                        <div>
                          <Label htmlFor={`notes-${appointment.id}`}>Notas privadas</Label>
                          <Textarea
                            id={`notes-${appointment.id}`}
                            onChange={(event) => setNotesDrafts((current) => ({ ...current, [appointment.id]: event.target.value }))}
                            placeholder="Notas privadas visibles solo para ti"
                            rows={3}
                            value={draft}
                          />
                          <Button
                            className="mt-3"
                            disabled={notesMutation.isPending}
                            onClick={() => notesMutation.mutate({ appointmentId: appointment.id, professional_private_notes: draft })}
                            size="sm"
                          >
                            Guardar notas
                          </Button>
                        </div>
                        {appointment.history?.length ? (
                          <div className="space-y-2 text-sm text-ink-700">
                            <p className="font-semibold text-ink-900">Historial</p>
                            {appointment.history.map((item) => (
                              <p key={item.id}>
                                {formatDateTime(item.created_at)} - {item.old_status ? getAppointmentStatusLabel(item.old_status) : "Nueva"} a{" "}
                                {getAppointmentStatusLabel(item.new_status)}
                              </p>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </details>
                  </div>
                }
                key={appointment.id}
              />
            );
          })}
          {appointments.length === 0 ? (
            <EmptyState title="Aun no tienes reservas" description="Cuando un cliente agende contigo, sus datos de agenda apareceran aqui." />
          ) : null}
          {appointments.length > 0 && filteredAppointments.length === 0 ? (
            <EmptyState title="Sin resultados para este filtro" description="Prueba con otro estado o borra la busqueda." />
          ) : null}
        </div>
        {actionMutation.isError ? <ErrorState message={normalizeApiError(actionMutation.error).message} title="No se pudo actualizar la reserva" /> : null}
        {notesMutation.isError ? <ErrorState message={normalizeApiError(notesMutation.error).message} title="No se pudieron guardar las notas" /> : null}
      </section>
    </div>
  );
}
