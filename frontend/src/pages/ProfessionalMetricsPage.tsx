import { useQuery } from "@tanstack/react-query";

import { fetchProfessionalMetrics } from "../api/queries";
import { ProfessionalAppointmentCard } from "../components/professional/ProfessionalAppointmentCard";
import { ProfessionalStatCard } from "../components/professional/ProfessionalStatCard";
import { EmptyState, ErrorState, LoadingState, PageHeader, SectionCard } from "../components/ui";

export function ProfessionalMetricsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["professional-metrics"], queryFn: fetchProfessionalMetrics });

  if (isLoading) {
    return <LoadingState label="Cargando metricas profesionales" />;
  }

  if (isError || !data) {
    return <ErrorState title="No pudimos cargar las metricas" message="Intenta nuevamente en unos minutos." />;
  }

  const primaryMetrics = [
    { label: "Reservas de hoy", value: data.today_reservations, icon: "calendar" as const },
    { label: "Proximas reservas", value: data.upcoming_reservations, icon: "clock" as const },
    { label: "Atenciones del mes", value: data.monthly_completed, icon: "check" as const },
    { label: "Clientes unicos", value: data.unique_clients, icon: "users" as const },
  ];

  const secondaryMetrics = [
    { label: "Pendientes", value: data.pending_reservations },
    { label: "Confirmadas", value: data.confirmed_reservations },
    { label: "Completadas historicas", value: data.lifetime_completed },
    { label: "Canceladas", value: data.cancelled_reservations },
    { label: "No asistio", value: data.no_show_reservations },
    { label: "Tasa de cancelacion", value: `${data.cancellation_rate}%` },
    { label: "Reglas de disponibilidad", value: data.availability_rules_count },
    { label: "Perfil publico", value: data.is_public ? "Visible" : "No publicado" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Metricas profesionales"
        description="Actividad y configuracion de tu operacion diaria con datos actuales de reservas y perfil."
      />

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {primaryMetrics.map((metric) => (
          <ProfessionalStatCard icon={metric.icon} key={metric.label} label={metric.label} value={metric.value} />
        ))}
      </div>

      <SectionCard title="Resumen operativo" description="Indicadores complementarios para revisar carga y configuracion.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {secondaryMetrics.map((metric) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={metric.label}>
              <p className="text-sm font-semibold text-ink-700">{metric.label}</p>
              <p className="mt-2 text-2xl font-bold text-ink-900">{metric.value}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="grid gap-5 lg:grid-cols-2">
        <SectionCard title="Proximas reservas" description="Actividad futura registrada en tu agenda.">
          <div className="space-y-3">
            {data.next_appointments.map((item) => (
              <ProfessionalAppointmentCard appointment={item} key={item.id} />
            ))}
            {data.next_appointments.length === 0 ? (
              <EmptyState title="Sin proximas reservas" description="Aun no tienes reservas futuras registradas." />
            ) : null}
          </div>
        </SectionCard>
        <SectionCard title="Actividad reciente" description="Ultimos movimientos visibles para tu perfil.">
          <div className="space-y-3">
            {data.recent_appointments.map((item) => (
              <ProfessionalAppointmentCard appointment={item} key={item.id} />
            ))}
            {data.recent_appointments.length === 0 ? (
              <EmptyState title="Sin actividad reciente" description="Cuando existan reservas o cambios, apareceran aqui." />
            ) : null}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
