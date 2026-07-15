import { Link } from "react-router-dom";

import { Icon, SectionCard } from "../ui";

const actions = [
  { label: "Revisar reservas", to: "/dashboard/professional/appointments", icon: "calendar" as const },
  { label: "Configurar disponibilidad", to: "/dashboard/professional/availability", icon: "clock" as const },
  { label: "Editar perfil publico", to: "/dashboard/professional/catalog", icon: "user" as const },
  { label: "Ver metricas", to: "/dashboard/professional", icon: "chart" as const },
];

export function ProfessionalQuickActions() {
  return (
    <SectionCard title="Acciones rapidas" description="Atajos a las tareas habituales de tu operacion diaria.">
      <div className="grid gap-3 sm:grid-cols-2">
        {actions.map((action) => (
          <Link
            className="flex min-h-11 items-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-ink-900 transition hover:bg-slate-50"
            key={action.to}
            to={action.to}
          >
              <Icon name={action.icon} />
              {action.label}
          </Link>
        ))}
      </div>
    </SectionCard>
  );
}
