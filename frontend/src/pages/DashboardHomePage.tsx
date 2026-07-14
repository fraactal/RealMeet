import { useAuthStore } from "../store/auth";
import { Card } from "../components/ui/Card";

export function DashboardHomePage() {
  const { user } = useAuthStore();

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
