import { useQuery } from "@tanstack/react-query";

import { fetchAdminMetrics } from "../api/queries";
import { AdminAppointmentCard } from "../components/admin/AdminAppointmentCard";
import { AdminMetricCard } from "../components/admin/AdminMetricCard";
import { EmptyState, ErrorState, LoadingState, PageHeader, SectionCard } from "../components/ui";

export function AdminMetricsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["admin-metrics"], queryFn: fetchAdminMetrics });

  if (isLoading) {
    return <LoadingState label="Cargando metricas administrativas" />;
  }

  if (isError || !data) {
    return <ErrorState title="No pudimos cargar las metricas" message="Intenta nuevamente en unos minutos." />;
  }

  const platformMetrics = [
    { label: "Usuarios totales", value: data.total_users, icon: "users" as const, description: "Cuentas registradas." },
    { label: "Clientes", value: data.total_clients, icon: "user" as const, description: `${data.active_clients} activos.` },
    { label: "Profesionales", value: data.total_professionals, icon: "users" as const, description: `${data.active_professionals} activos.` },
    { label: "Reservas totales", value: data.total_appointments, icon: "calendar" as const, description: "Historial completo registrado." },
  ];

  const catalogMetrics = [
    { label: "Profesionales publicos", value: data.public_professionals, icon: "search" as const },
    { label: "Categorias activas", value: data.active_categories, icon: "settings" as const },
    { label: "Especialidades activas", value: data.active_specialties, icon: "filter" as const },
  ];

  const appointmentStatuses = [
    ["Pendientes", data.pending_appointments],
    ["Confirmadas", data.confirmed_appointments],
    ["Completadas", data.completed_appointments],
    ["Canceladas", data.cancelled_appointments],
    ["No asistio", data.no_show_appointments],
  ] as const;

  const maxStatusValue = Math.max(...appointmentStatuses.map(([, value]) => value), 1);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Metricas administrativas"
        description="Resumen operativo global con los indicadores disponibles actualmente."
      />

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {platformMetrics.map((metric) => (
          <AdminMetricCard description={metric.description} icon={metric.icon} key={metric.label} label={metric.label} value={metric.value} />
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_0.8fr]">
        <SectionCard title="Reservas por estado" description="Distribucion basada en estados reales del backend.">
          <div className="space-y-4">
            {appointmentStatuses.map(([label, value]) => (
              <div key={label}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-semibold text-ink-700">{label}</span>
                  <span className="font-bold text-ink-900">{value}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full bg-brand-700" style={{ width: `${Math.max((value / maxStatusValue) * 100, value > 0 ? 8 : 0)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Catalogo y publicacion" description="Disponibilidad administrativa visible para el marketplace.">
          <div className="grid gap-3">
            {catalogMetrics.map((metric) => (
              <AdminMetricCard icon={metric.icon} key={metric.label} label={metric.label} value={metric.value} />
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Reservas recientes" description="Actividad operativa mas reciente disponible en metricas.">
        <div className="space-y-3">
          {data.recent_appointments.map((item) => (
            <AdminAppointmentCard appointment={item} key={item.id} />
          ))}
          {data.recent_appointments.length === 0 ? (
            <EmptyState title="Sin reservas registradas" description="Las reservas recientes apareceran aqui cuando existan datos." />
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
