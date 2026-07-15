import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import { cancelAppointment, fetchMe, fetchMyAppointments, fetchMyWhatsAppConsents, grantMyWhatsAppConsent, revokeMyWhatsAppConsent } from "../api/queries";
import { ClientAppointmentCard } from "../components/client/ClientAppointmentCard";
import { Badge, Button, EmptyState, ErrorState, Input, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type { Appointment, AppointmentStatus, WhatsAppConsentPurpose } from "../types";
import { getAppointmentStatusLabel, getWhatsAppConsentPurposeLabel } from "../utils/labels";

function canCancel(appointment: Appointment): boolean {
  return ["pending", "confirmed"].includes(appointment.status) && new Date(appointment.start_datetime).getTime() > Date.now();
}

type ReservationView = "upcoming" | "history" | "cancelled" | "all";

function isUpcoming(appointment: Appointment): boolean {
  return ["pending", "confirmed"].includes(appointment.status) && new Date(appointment.start_datetime).getTime() > Date.now();
}

export function AppointmentsPage() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<ReservationView>("upcoming");
  const [statusFilter, setStatusFilter] = useState<"" | AppointmentStatus>("");
  const { data, isLoading, isError } = useQuery({ queryKey: ["my-appointments"], queryFn: fetchMyAppointments });
  const meQuery = useQuery({ queryKey: ["me"], queryFn: fetchMe });
  const consentsQuery = useQuery({ queryKey: ["my-whatsapp-consents"], queryFn: fetchMyWhatsAppConsents });
  const [consentPhone, setConsentPhone] = useState("");
  const [confirmedConsentText, setConfirmedConsentText] = useState(false);
  const cancelMutation = useMutation({
    mutationFn: (appointmentId: number) => cancelAppointment(appointmentId, { reason: "Cancelada por el usuario" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["my-appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["client-dashboard"] });
    },
  });
  const grantConsentMutation = useMutation({
    mutationFn: (purpose: WhatsAppConsentPurpose) =>
      grantMyWhatsAppConsent({
        phone: consentPhone.trim() || meQuery.data?.phone || "",
        purpose,
        consent_text_version: "wa-transactional-v1",
        explicit_confirmation: confirmedConsentText,
      }),
    onSuccess: () => {
      setConfirmedConsentText(false);
      void queryClient.invalidateQueries({ queryKey: ["my-whatsapp-consents"] });
    },
  });
  const revokeConsentMutation = useMutation({
    mutationFn: (purpose: WhatsAppConsentPurpose) => revokeMyWhatsAppConsent(purpose),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["my-whatsapp-consents"] }),
  });

  const appointments = data ?? [];
  const filteredAppointments = useMemo(() => {
    return appointments.filter((appointment) => {
      const matchesStatus = statusFilter ? appointment.status === statusFilter : true;
      if (!matchesStatus) {
        return false;
      }
      if (view === "upcoming") {
        return isUpcoming(appointment);
      }
      if (view === "history") {
        return !isUpcoming(appointment) && appointment.status !== "cancelled";
      }
      if (view === "cancelled") {
        return appointment.status === "cancelled";
      }
      return true;
    });
  }, [appointments, statusFilter, view]);

  const upcomingCount = appointments.filter(isUpcoming).length;
  const historyCount = appointments.filter((appointment) => !isUpcoming(appointment) && appointment.status !== "cancelled").length;
  const cancelledCount = appointments.filter((appointment) => appointment.status === "cancelled").length;

  if (isLoading) {
    return <LoadingState label="Cargando tus reservas" />;
  }

  if (isError) {
    return <ErrorState title="No pudimos cargar tus reservas" message="Intenta nuevamente en unos minutos." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mis reservas"
        description="Revisa tus proximas horas, historial y acciones disponibles segun el estado de cada reserva."
      />

      <SectionCard title="Preferencias de notificacion" description="WhatsApp es opcional y solo se usa para mensajes transaccionales de tus reservas si otorgas consentimiento.">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
          <div>
            <Input
              aria-label="Telefono para consentimiento WhatsApp"
              placeholder={meQuery.data?.phone ?? "+56912345678"}
              value={consentPhone}
              onChange={(event) => setConsentPhone(event.target.value)}
            />
            <label className="mt-3 flex items-start gap-2 text-sm font-semibold text-ink-700">
              <input checked={confirmedConsentText} onChange={(event) => setConfirmedConsentText(event.target.checked)} type="checkbox" />
              <span>Autorizo a RealMeet a enviarme por WhatsApp confirmaciones, cambios y recordatorios relacionados con mis reservas. Puedo revocar esta autorizacion en cualquier momento.</span>
            </label>
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            {(["appointment_transactional", "appointment_updates", "appointment_reminders"] as WhatsAppConsentPurpose[]).map((purpose) => {
              const consent = consentsQuery.data?.find((item) => item.purpose === purpose && item.status === "granted");
              return (
                <div className="min-w-44 rounded-lg border border-slate-200 bg-white p-3" key={purpose}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-ink-900">{getWhatsAppConsentPurposeLabel(purpose)}</p>
                    <Badge label={consent ? "Activo" : "No otorgado"} tone={consent ? "success" : "neutral"} />
                  </div>
                  {consent ? (
                    <Button className="mt-3 w-full" isLoading={revokeConsentMutation.isPending} onClick={() => revokeConsentMutation.mutate(purpose)} size="sm" variant="secondary">Revocar</Button>
                  ) : (
                    <Button className="mt-3 w-full" disabled={!confirmedConsentText || !(consentPhone.trim() || meQuery.data?.phone)} isLoading={grantConsentMutation.isPending} onClick={() => grantConsentMutation.mutate(purpose)} size="sm">Otorgar</Button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        {grantConsentMutation.isError || revokeConsentMutation.isError ? <ErrorState title="No pudimos actualizar el consentimiento" message="Revisa el telefono informado e intenta nuevamente." /> : null}
      </SectionCard>

      <SectionCard>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="grid gap-2 sm:grid-cols-3">
            {[
              { label: "Proximas", value: "upcoming" as const, count: upcomingCount },
              { label: "Historial", value: "history" as const, count: historyCount },
              { label: "Canceladas", value: "cancelled" as const, count: cancelledCount },
            ].map((item) => (
              <button
                className={`rounded-md border px-4 py-3 text-left text-sm font-semibold transition ${
                  view === item.value ? "border-brand-700 bg-brand-50 text-brand-700" : "border-slate-200 bg-white text-ink-600 hover:bg-slate-50"
                }`}
                key={item.value}
                onClick={() => setView(item.value)}
                type="button"
              >
                {item.label}
                <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-xs text-ink-500 ring-1 ring-slate-200">{item.count}</span>
              </button>
            ))}
          </div>
          <div className="w-full lg:w-64">
            <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "" | AppointmentStatus)}>
              <option value="">Todos los estados</option>
              {(["pending", "confirmed", "cancelled", "completed", "no_show"] as AppointmentStatus[]).map((status) => (
                <option key={status} value={status}>
                  {getAppointmentStatusLabel(status)}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </SectionCard>

      {cancelMutation.isError ? (
        <ErrorState title="No pudimos cancelar la reserva" message={normalizeApiError(cancelMutation.error).message} />
      ) : null}

      <SectionCard title="Reservas" description="Las acciones disponibles dependen del estado y la fecha de cada hora.">
        <div className="space-y-3">
          {filteredAppointments.map((appointment) => (
            <ClientAppointmentCard
              actions={
                canCancel(appointment) ? (
                  <Button
                    isLoading={cancelMutation.isPending}
                    onClick={() => cancelMutation.mutate(appointment.id)}
                    size="sm"
                    variant="secondary"
                  >
                    Cancelar
                  </Button>
                ) : (
                  <span className="rounded-md bg-slate-100 px-3 py-2 text-xs font-semibold text-ink-500">Sin acciones disponibles</span>
                )
              }
              appointment={appointment}
              key={appointment.id}
            />
          ))}
          {filteredAppointments.length === 0 ? (
            <EmptyState
              title={appointments.length === 0 ? "Aun no tienes reservas" : "No hay reservas para esta vista"}
              description={
                appointments.length === 0
                  ? "Cuando agendes con un profesional, tus horas apareceran aqui."
                  : "Prueba con otra categoria o limpia el filtro de estado."
              }
            />
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
