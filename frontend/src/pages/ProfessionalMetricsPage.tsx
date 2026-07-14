import { useQuery } from "@tanstack/react-query";

import { fetchProfessionalMetrics } from "../api/queries";
import { Card } from "../components/ui/Card";

export function ProfessionalMetricsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["professional-metrics"], queryFn: fetchProfessionalMetrics });

  if (isLoading) {
    return <p className="text-slate-500">Cargando metricas...</p>;
  }

  if (isError || !data) {
    return <p className="text-red-600">No fue posible obtener las metricas profesionales.</p>;
  }

  const metrics: Array<[string, number | string]> = [
    ["Reservas de hoy", data.today_reservations],
    ["Proximas reservas", data.upcoming_reservations],
    ["Pendientes", data.pending_reservations],
    ["Confirmadas", data.confirmed_reservations],
    ["Completadas del mes", data.monthly_completed],
    ["Completadas historicas", data.lifetime_completed],
    ["Clientes unicos", data.unique_clients],
    ["Canceladas", data.cancelled_reservations],
    ["No show", data.no_show_reservations],
    ["Tasa de cancelacion", `${data.cancellation_rate}%`],
    ["Reglas activas", data.availability_rules_count],
    ["Perfil publico", data.is_public ? "Si" : "No"],
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Metricas profesionales</h1>
        <p className="text-slate-600">Actividad y configuracion de tu perfil profesional.</p>
      </div>
      <div className="grid gap-5 md:grid-cols-3 xl:grid-cols-5">
        {metrics.map(([label, value]) => (
          <Card key={label} title={label}>
            <p className="text-3xl font-semibold text-ink">{value}</p>
          </Card>
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Proximas reservas">
          <div className="space-y-3 text-sm">
            {data.next_appointments.map((item) => (
              <p key={item.id} className="rounded-xl border border-slate-100 p-3">
                {new Date(item.start_datetime).toLocaleString()} - {item.status}
              </p>
            ))}
            {data.next_appointments.length === 0 ? <p className="text-slate-500">No hay proximas reservas.</p> : null}
          </div>
        </Card>
        <Card title="Actividad reciente">
          <div className="space-y-3 text-sm">
            {data.recent_appointments.map((item) => (
              <p key={item.id} className="rounded-xl border border-slate-100 p-3">
                {new Date(item.start_datetime).toLocaleString()} - {item.status}
              </p>
            ))}
            {data.recent_appointments.length === 0 ? <p className="text-slate-500">Sin actividad reciente.</p> : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
