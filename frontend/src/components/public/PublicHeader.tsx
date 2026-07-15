import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { useAuthStore } from "../../store/auth";
import { Button, Icon } from "../ui";

const publicLinks = [
  { label: "Inicio", href: "/" },
  { label: "Profesionales", href: "/professionals" },
];

export function PublicHeader() {
  const { logout, user } = useAuthStore();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate("/login", { replace: true });
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <Link className="flex items-center gap-3" to="/">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-700 font-bold text-white">RM</span>
          <span>
            <span className="block text-lg font-bold text-ink-900">RealMeet</span>
            <span className="block text-xs font-semibold text-ink-500">Agenda profesional</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-semibold text-ink-600 md:flex" aria-label="Navegacion publica">
          {publicLinks.map((link) => (
            <NavLink className={({ isActive }) => (isActive ? "text-brand-700" : "hover:text-brand-700")} key={link.href} to={link.href}>
              {link.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <Link className="hover:text-brand-700" to="/dashboard">
                Dashboard
              </Link>
              <Button onClick={handleLogout} size="sm" variant="secondary">
                Salir
              </Button>
            </>
          ) : (
            <>
              <Link className="hover:text-brand-700" to="/register">
                Crear cuenta
              </Link>
              <Link to="/login">
                <Button size="sm">Iniciar sesion</Button>
              </Link>
            </>
          )}
        </nav>

        <button
          aria-expanded={isOpen}
          aria-label="Abrir menu"
          className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 bg-white text-ink-700 md:hidden"
          onClick={() => setIsOpen((current) => !current)}
          type="button"
        >
          <Icon name={isOpen ? "x" : "menu"} />
        </button>
      </div>

      {isOpen ? (
        <nav className="border-t border-slate-200 bg-white px-5 py-4 md:hidden" aria-label="Navegacion publica mobile">
          <div className="mx-auto grid max-w-7xl gap-2">
            {publicLinks.map((link) => (
              <Link className="rounded-md px-3 py-2 text-sm font-semibold text-ink-700 hover:bg-brand-50" key={link.href} onClick={() => setIsOpen(false)} to={link.href}>
                {link.label}
              </Link>
            ))}
            {user ? (
              <>
                <Link className="rounded-md px-3 py-2 text-sm font-semibold text-ink-700 hover:bg-brand-50" onClick={() => setIsOpen(false)} to="/dashboard">
                  Dashboard
                </Link>
                <Button className="mt-2" onClick={handleLogout} variant="secondary">
                  Salir
                </Button>
              </>
            ) : (
              <>
                <Link className="rounded-md px-3 py-2 text-sm font-semibold text-ink-700 hover:bg-brand-50" onClick={() => setIsOpen(false)} to="/register">
                  Crear cuenta
                </Link>
                <Link onClick={() => setIsOpen(false)} to="/login">
                  <Button className="mt-2 w-full">Iniciar sesion</Button>
                </Link>
              </>
            )}
          </div>
        </nav>
      ) : null}
    </header>
  );
}
