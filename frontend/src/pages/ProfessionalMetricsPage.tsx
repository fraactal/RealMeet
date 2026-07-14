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
    ["Completadas del mes", data.monthly_completed],
    ["Completadas historicas", data.lifetime_completed],
    ["Clientes unicos", data.unique_clients],
    ["Canceladas", data.cancelled_reservations],
    ["Tasa de cancelacion", `${data.cancellation_rate}%`],
    ["Ingreso estimado mes", `$${data.estimated_month_income}`],
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
