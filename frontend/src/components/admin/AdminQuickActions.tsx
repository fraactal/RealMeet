import { Link } from "react-router-dom";

import { Button, Icon, SectionCard } from "../ui";

const actions = [
  {
    title: "Backoffice",
    description: "Gestiona usuarios, profesionales y reservas recientes.",
    href: "/dashboard/admin/manage",
    icon: "users" as const,
  },
  {
    title: "Catalogo",
    description: "Administra categorias y especialidades disponibles.",
    href: "/dashboard/admin/catalog",
    icon: "settings" as const,
  },
  {
    title: "Metricas",
    description: "Revisa el resumen operativo global.",
    href: "/dashboard/admin",
    icon: "chart" as const,
  },
];

export function AdminQuickActions() {
  return (
    <SectionCard title="Accesos administrativos" description="Abre las secciones operativas existentes.">
      <div className="grid gap-3 md:grid-cols-3">
        {actions.map((action) => (
          <Link className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:bg-brand-50/50" key={action.href} to={action.href}>
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-brand-100 text-brand-700">
              <Icon name={action.icon} />
            </span>
            <h3 className="mt-4 text-base font-semibold text-ink-900">{action.title}</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">{action.description}</p>
            <Button className="mt-4 w-full sm:w-auto" size="sm" variant="secondary">
              Abrir
            </Button>
          </Link>
        ))}
      </div>
    </SectionCard>
  );
}
