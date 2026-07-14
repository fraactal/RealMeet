import { Link, Outlet } from "react-router-dom";

import { Navbar } from "../components/Navbar";
import { useAuthStore } from "../store/auth";

export function DashboardLayout() {
  const { user } = useAuthStore();

  return (
    <div>
      <Navbar />
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="mb-4 text-sm uppercase tracking-wide text-slate-500">Panel</p>
          <div className="mb-6">
            <p className="font-semibold text-ink">{user?.first_name} {user?.last_name}</p>
            <p className="text-sm text-slate-500">{user?.role}</p>
          </div>
          <nav className="flex flex-col gap-3 text-sm font-medium text-slate-600">
            <Link to="/dashboard">Resumen</Link>
            <Link to="/dashboard/appointments">Reservas</Link>
            {user?.role === "professional" ? <Link to="/dashboard/professional">Metricas profesional</Link> : null}
            {user?.role === "professional" ? <Link to="/dashboard/professional/catalog">Catalogo profesional</Link> : null}
            {user?.role === "professional" ? <Link to="/dashboard/professional/availability">Disponibilidad</Link> : null}
            {user?.role === "admin" ? <Link to="/dashboard/admin">Metricas admin</Link> : null}
            {user?.role === "admin" ? <Link to="/dashboard/admin/catalog">Catalogo admin</Link> : null}
          </nav>
        </aside>
        <section>
          <Outlet />
        </section>
      </div>
    </div>
  );
}
