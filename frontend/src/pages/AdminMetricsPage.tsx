import { useQuery } from "@tanstack/react-query";

import { fetchAdminMetrics } from "../api/queries";
import { Card } from "../components/ui/Card";

export function AdminMetricsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["admin-metrics"], queryFn: fetchAdminMetrics });

  if (isLoading) {
    return <p className="text-slate-500">Cargando metricas...</p>;
  }

  if (isError || !data) {
    return <p className="text-red-600">No fue posible obtener las metricas globales.</p>;
  }

  const metrics: Array<[string, number]> = [
    ["Usuarios", data.total_users],
    ["Profesionales", data.total_professionals],
    ["Clientes", data.total_clients],
    ["Clientes activos", data.active_clients],
    ["Profesionales activos", data.active_professionals],
    ["Profesionales publicos", data.public_professionals],
    ["Reservas", data.total_appointments],
    ["Pendientes", data.pending_appointments],
    ["Confirmadas", data.confirmed_appointments],
    ["Completadas", data.completed_appointments],
    ["Canceladas", data.cancelled_appointments],
    ["No show", data.no_show_appointments],
    ["Categorias activas", data.active_categories],
    ["Especialidades activas", data.active_specialties],
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Metricas admin</h1>
        <p className="text-slate-600">Resumen operativo global del MVP.</p>
      </div>
      <div className="grid gap-5 md:grid-cols-3 xl:grid-cols-5">
        {metrics.map(([label, value]) => (
          <Card key={label} title={label}>
            <p className="text-3xl font-semibold text-ink">{value}</p>
          </Card>
        ))}
      </div>
      <Card title="Reservas recientes">
        <div className="space-y-3 text-sm">
          {data.recent_appointments.map((item) => (
            <p key={item.id} className="rounded-xl border border-slate-100 p-3">
              {new Date(item.start_datetime).toLocaleString()} - {item.status}
            </p>
          ))}
          {data.recent_appointments.length === 0 ? <p className="text-slate-500">Sin reservas registradas.</p> : null}
        </div>
      </Card>
    </div>
  );
}
