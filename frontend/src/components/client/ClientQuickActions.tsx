import { Link } from "react-router-dom";

import { Button, Icon, SectionCard } from "../ui";

const actions = [
  {
    title: "Buscar profesionales",
    description: "Explora perfiles publicados y encuentra un horario disponible.",
    href: "/dashboard/professionals",
    icon: "search" as const,
    primary: true,
  },
  {
    title: "Ver mis reservas",
    description: "Revisa proximas horas, historial y acciones disponibles.",
    href: "/dashboard/appointments",
    icon: "calendar" as const,
    primary: false,
  },
];

export function ClientQuickActions() {
  return (
    <SectionCard title="Acciones principales" description="Continua desde los flujos mas habituales.">
      <div className="grid gap-3 sm:grid-cols-2">
        {actions.map((action) => (
          <Link
            className="group rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:bg-brand-50/50"
            key={action.href}
            to={action.href}
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-100 text-brand-700">
              <Icon name={action.icon} />
            </span>
            <h3 className="mt-4 text-base font-semibold text-ink-900">{action.title}</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">{action.description}</p>
            <Button className="mt-4 w-full sm:w-auto" size="sm" variant={action.primary ? "primary" : "secondary"}>
              Abrir
            </Button>
          </Link>
        ))}
      </div>
    </SectionCard>
  );
}
