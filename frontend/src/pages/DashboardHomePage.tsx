import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchAdminMetrics, fetchClientDashboard, fetchProfessionalMetrics } from "../api/queries";
import { useAuthStore } from "../store/auth";
import { Card } from "../components/ui/Card";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, SectionCard } from "../components/ui";
import { AdminAppointmentCard } from "../components/admin/AdminAppointmentCard";
import { AdminMetricCard } from "../components/admin/AdminMetricCard";
import { AdminQuickActions } from "../components/admin/AdminQuickActions";
import { ClientAppointmentCard } from "../components/client/ClientAppointmentCard";
import { ClientQuickActions } from "../components/client/ClientQuickActions";
import { ClientStatSummary } from "../components/client/ClientStatSummary";
import { ProfessionalAppointmentCard } from "../components/professional/ProfessionalAppointmentCard";
import { ProfessionalConfigStatus, ProfessionalStatCard } from "../components/professional/ProfessionalStatCard";
import { ProfessionalQuickActions } from "../components/professional/ProfessionalQuickActions";
import { formatLongDate } from "../utils/dates";

export function DashboardHomePage() {
  const { user } = useAuthStore();
  const clientDashboardQuery = useQuery({
    queryKey: ["client-dashboard"],
    queryFn: fetchClientDashboard,
    enabled: user?.role === "client",
  });
  const professionalMetricsQuery = useQuery({
    queryKey: ["professional-metrics"],
    queryFn: fetchProfessionalMetrics,
    enabled: user?.role === "professional",
  });
  const adminMetricsQuery = useQuery({
    queryKey: ["admin-metrics"],
    queryFn: fetchAdminMetrics,
    enabled: user?.role === "admin",
  });

  if (user?.role === "client") {
    const data = clientDashboardQuery.data;

    if (clientDashboardQuery.isLoading) {
      return <LoadingState label="Cargando tus reservas" />;
    }

    if (clientDashboardQuery.isError || !data) {
      return <ErrorState title="No pudimos cargar tu inicio" message="Intenta nuevamente en unos minutos." />;
    }

    const nextAppointment = data.next_appointments[0];
    const recentAppointments = data.recent_appointments.slice(0, 3);

    return (
      <div className="space-y-6">
        <PageHeader
          title={`Hola, ${user.first_name}`}
          description={`${formatLongDate(new Date())}. Revisa tu proxima reserva o busca un profesional para agendar una nueva hora.`}
          actions={
            <Link to="/dashboard/professionals">
              <Button>Buscar profesionales</Button>
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1.35fr_0.8fr]">
          <SectionCard
            title="Proxima reserva"
            description="Tu siguiente hora confirmada o pendiente aparece primero para que tengas claro que viene."
            actions={
              <Link className="text-sm font-semibold text-brand-700 hover:text-brand-600" to="/dashboard/appointments">
                Ver todas
              </Link>
            }
          >
            {nextAppointment ? (
              <ClientAppointmentCard appointment={nextAppointment} emphasis />
            ) : (
              <EmptyState
                title="Aun no tienes reservas proximas"
                description="Cuando agendes una hora, veras aqui la fecha, el estado y la informacion disponible."
              >
                <Link to="/dashboard/professionals">
                  <Button className="mt-5">Buscar profesionales</Button>
                </Link>
              </EmptyState>
            )}
          </SectionCard>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <ClientStatSummary icon="calendar" label="Reservas futuras" value={data.upcoming_reservations} />
            <ClientStatSummary icon="clock" label="Pendientes" value={data.status_counts.pending} />
            <ClientStatSummary icon="check" label="Completadas" value={data.status_counts.completed} />
          </div>
        </div>

        <ClientQuickActions />

        <SectionCard title="Actividad reciente" description="Ultimas reservas registradas en tu cuenta.">
          <div className="space-y-3">
            {recentAppointments.map((appointment) => (
              <ClientAppointmentCard appointment={appointment} key={appointment.id} showMeeting={false} />
            ))}
            {recentAppointments.length === 0 ? (
              <EmptyState title="Todavia no hay historial" description="Tus reservas pasadas o canceladas apareceran en esta seccion." />
            ) : null}
          </div>
        </SectionCard>
      </div>
    );
  }

  if (user?.role === "professional") {
    const data = professionalMetricsQuery.data;

    if (professionalMetricsQuery.isLoading) {
      return <LoadingState label="Cargando tu resumen profesional" />;
    }

    if (professionalMetricsQuery.isError || !data) {
      return <ErrorState title="No pudimos cargar tu resumen" message="Intenta nuevamente en unos minutos." />;
    }

    const nextAppointment = data.next_appointments[0];
    const pendingItems = data.next_appointments.filter((appointment) => appointment.status === "pending").slice(0, 3);

    return (
      <div className="space-y-6">
        <PageHeader
          title={`Hola, ${user.first_name}`}
          description={`${formatLongDate(new Date())}. Revisa tu agenda, las reservas pendientes y la configuracion visible para clientes.`}
          actions={
            <Link to="/dashboard/professional/appointments">
              <Button>Ver reservas</Button>
            </Link>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[1.4fr_0.8fr]">
          <SectionCard
            title="Proxima actividad"
            description="La siguiente reserva disponible en tu agenda profesional."
            actions={
              <Link className="text-sm font-semibold text-brand-700 hover:text-brand-600" to="/dashboard/professional/appointments">
                Abrir agenda
              </Link>
            }
          >
            {nextAppointment ? (
              <ProfessionalAppointmentCard appointment={nextAppointment} />
            ) : (
              <EmptyState
                title="No tienes proximas reservas"
                description="Cuando un cliente agende una hora, aparecera aqui como prioridad de tu jornada."
              />
            )}
          </SectionCard>

          <div className="space-y-4">
            <ProfessionalConfigStatus
              title={data.is_public ? "Perfil visible" : "Perfil no publicado"}
              description={
                data.is_public
                  ? "Tu perfil puede aparecer en la busqueda publica."
                  : "Activa tu perfil publico cuando quieras recibir reservas desde el catalogo."
              }
              state={data.is_public ? "ready" : "attention"}
              action={
                <Link className="text-sm font-semibold" to="/dashboard/professional/catalog">
                  Revisar
                </Link>
              }
            />
            <ProfessionalConfigStatus
              title={data.availability_rules_count > 0 ? "Disponibilidad configurada" : "Sin disponibilidad semanal"}
              description={
                data.availability_rules_count > 0
                  ? `${data.availability_rules_count} reglas activas para calcular horarios disponibles.`
                  : "Agrega reglas semanales para que los clientes puedan encontrar horarios."
              }
              state={data.availability_rules_count > 0 ? "ready" : "attention"}
              action={
                <Link className="text-sm font-semibold" to="/dashboard/professional/availability">
                  Configurar
                </Link>
              }
            />
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <ProfessionalStatCard icon="calendar" label="Reservas de hoy" value={data.today_reservations} />
          <ProfessionalStatCard icon="clock" label="Proximas reservas" value={data.upcoming_reservations} />
          <ProfessionalStatCard icon="filter" label="Pendientes" value={data.pending_reservations} />
          <ProfessionalStatCard icon="users" label="Clientes unicos" value={data.unique_clients} />
        </div>

        <div className="grid gap-5 lg:grid-cols-[1fr_0.75fr]">
          <SectionCard title="Reservas que requieren atencion" description="Solicitudes pendientes o proximas que conviene revisar.">
            <div className="space-y-3">
              {pendingItems.map((appointment) => (
                <ProfessionalAppointmentCard appointment={appointment} key={appointment.id} />
              ))}
              {pendingItems.length === 0 ? (
                <EmptyState title="Sin reservas pendientes" description="No tienes solicitudes pendientes en este momento." />
              ) : null}
            </div>
          </SectionCard>
          <ProfessionalQuickActions />
        </div>
      </div>
    );
  }

  if (user?.role === "admin") {
    const data = adminMetricsQuery.data;

    if (adminMetricsQuery.isLoading) {
      return <LoadingState label="Cargando resumen administrativo" />;
    }

    if (adminMetricsQuery.isError || !data) {
      return <ErrorState title="No pudimos cargar el resumen administrativo" message="Intenta nuevamente en unos minutos." />;
    }

    const activeAppointments = data.pending_appointments + data.confirmed_appointments;
    const recentAppointments = data.recent_appointments.slice(0, 4);

    return (
      <div className="space-y-6">
        <PageHeader
          title={`Administracion RealMeet`}
          description={`${formatLongDate(new Date())}. Revisa el estado operativo general y abre las secciones de gestion.`}
          actions={
            <Link to="/dashboard/admin/manage">
              <Button>Ir al backoffice</Button>
            </Link>
          }
        />

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <AdminMetricCard description="Cuentas registradas en la plataforma." icon="users" label="Usuarios totales" value={data.total_users} />
          <AdminMetricCard description="Perfiles profesionales registrados." icon="user" label="Profesionales" value={data.total_professionals} />
          <AdminMetricCard description="Reservas pendientes o confirmadas." icon="calendar" label="Reservas activas" value={activeAppointments} />
          <AdminMetricCard description="Categorias y especialidades activas." icon="settings" label="Catalogo activo" value={`${data.active_categories}/${data.active_specialties}`} />
        </div>

        <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <SectionCard title="Distribucion de usuarios" description="Estado visible segun los conteos administrativos disponibles.">
            <div className="grid gap-3 sm:grid-cols-2">
              <AdminMetricCard icon="user" label="Clientes activos" value={data.active_clients} />
              <AdminMetricCard icon="users" label="Profesionales activos" value={data.active_professionals} />
              <AdminMetricCard icon="search" label="Profesionales publicos" value={data.public_professionals} />
              <AdminMetricCard icon="chart" label="Clientes registrados" value={data.total_clients} />
            </div>
          </SectionCard>

          <SectionCard title="Reservas por estado" description="Conteo operativo de reservas existentes.">
            <div className="space-y-3">
              {[
                ["Pendientes", data.pending_appointments],
                ["Confirmadas", data.confirmed_appointments],
                ["Completadas", data.completed_appointments],
                ["Canceladas", data.cancelled_appointments],
                ["No asistio", data.no_show_appointments],
              ].map(([label, value]) => (
                <div className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-3" key={label}>
                  <span className="text-sm font-semibold text-ink-700">{label}</span>
                  <span className="text-lg font-bold text-ink-900">{value}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <SectionCard title="Reservas recientes" description="Ultimas reservas registradas en el sistema.">
          <div className="space-y-3">
            {recentAppointments.map((appointment) => (
              <AdminAppointmentCard appointment={appointment} key={appointment.id} />
            ))}
            {recentAppointments.length === 0 ? (
              <EmptyState title="Sin reservas registradas" description="Cuando existan reservas, apareceran aqui como actividad reciente." />
            ) : null}
          </div>
        </SectionCard>

        <AdminQuickActions />
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
