import { Link } from "react-router-dom";

import { useAuthStore } from "../store/auth";

export function Navbar() {
  const { user, logout } = useAuthStore();

  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="text-xl font-bold tracking-tight text-brand">
          RealMeet
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
          <Link to="/professionals">Profesionales</Link>
          {user ? (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <button className="rounded-full bg-ink px-4 py-2 text-white" onClick={logout}>
                Salir
              </button>
            </>
          ) : (
            <Link to="/login" className="rounded-full bg-ink px-4 py-2 text-white">
              Ingresar
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
