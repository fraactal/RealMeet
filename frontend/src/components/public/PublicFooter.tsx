import { Link } from "react-router-dom";

export function PublicFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white/80">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-base font-bold text-ink-900">RealMeet</p>
          <p className="mt-1 max-w-xl text-sm leading-6 text-ink-500">
            Plataforma para buscar profesionales, revisar disponibilidad y administrar reservas desde una experiencia simple.
          </p>
        </div>
        <nav className="flex flex-wrap gap-4 text-sm font-semibold text-ink-600" aria-label="Enlaces publicos">
          <Link className="hover:text-brand-700" to="/professionals">
            Profesionales
          </Link>
          <Link className="hover:text-brand-700" to="/login">
            Iniciar sesion
          </Link>
          <Link className="hover:text-brand-700" to="/register">
            Crear cuenta
          </Link>
        </nav>
      </div>
    </footer>
  );
}
