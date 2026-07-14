import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchClientDashboard } from "../api/queries";
import { useAuthStore } from "../store/auth";
import { Card } from "../components/ui/Card";

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <Card title={label}>
      <p className="text-3xl font-semibold text-ink">{value}</p>
    </Card>
  );
}

export function DashboardHomePage() {
  const { user } = useAuthStore();
  const clientDashboardQuery = useQuery({
    queryKey: ["client-dashboard"],
    queryFn: fetchClientDashboard,
    enabled: user?.role === "client",
  });

  if (user?.role === "client") {
    const data = clientDashboardQuery.data;
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Resumen cliente</h1>
          <p className="text-slate-600">Tus reservas y proximas atenciones.</p>
        </div>
        {clientDashboardQuery.isLoading ? <p className="text-slate-500">Cargando resumen...</p> : null}
        {clientDashboardQuery.isError ? <p className="text-red-600">No fue posible obtener tu resumen.</p> : null}
        {data ? (
          <>
            <div className="grid gap-5 md:grid-cols-5">
              <Metric label="Proximas" value={data.upcoming_reservations} />
              <Metric label="Pendientes" value={data.status_counts.pending} />
              <Metric label="Confirmadas" value={data.status_counts.confirmed} />
              <Metric label="Completadas" value={data.status_counts.completed} />
              <Metric label="Canceladas" value={data.status_counts.cancelled} />
            </div>
            <div className="grid gap-5 lg:grid-cols-2">
              <Card title="Proximas reservas">
                <div className="space-y-3 text-sm">
                  {data.next_appointments.map((item) => (
                    <p key={item.id} className="rounded-xl border border-slate-100 p-3">
                      {new Date(item.start_datetime).toLocaleString()} - {item.status}
                    </p>
                  ))}
                  {data.next_appointments.length === 0 ? <p className="text-slate-500">No tienes proximas reservas.</p> : null}
                </div>
              </Card>
              <Card title="Ultimas reservas">
                <div className="space-y-3 text-sm">
                  {data.recent_appointments.map((item) => (
                    <p key={item.id} className="rounded-xl border border-slate-100 p-3">
                      {new Date(item.start_datetime).toLocaleString()} - {item.status}
                    </p>
                  ))}
                  {data.recent_appointments.length === 0 ? <p className="text-slate-500">Todavia no hay reservas.</p> : null}
                </div>
              </Card>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" to="/professionals">
                Buscar profesionales
              </Link>
              <Link className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" to="/dashboard/appointments">
                Ver reservas
              </Link>
            </div>
          </>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Resumen</h1>
        <p className="text-slate-600">Panel principal para el rol {user?.role}.</p>
      </div>
      <div className="grid gap-5 md:grid-cols-3">
        <Card title="Estado del MVP">
          <p className="text-sm text-slate-600">Autenticacion, reservas, metricas y base administrativa listas para evolucionar.</p>
        </Card>
        <Card title="Integraciones futuras">
          <p className="text-sm text-slate-600">Google Meet, Zoom, WhatsApp y pagos quedan desacoplados desde el backend.</p>
        </Card>
        <Card title="Entorno">
          <p className="text-sm text-slate-600">Docker Compose, PostgreSQL, migraciones Alembic y seed inicial documentados.</p>
        </Card>
      </div>
    </div>
  );
}
