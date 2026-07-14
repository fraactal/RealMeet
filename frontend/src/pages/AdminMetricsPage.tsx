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
    ["Reservas", data.total_appointments],
  ];

  return (
    <div className="grid gap-5 md:grid-cols-2">
      {metrics.map(([label, value]) => (
        <Card key={label} title={label}>
          <p className="text-3xl font-semibold text-ink">{value}</p>
        </Card>
      ))}
    </div>
  );
}
