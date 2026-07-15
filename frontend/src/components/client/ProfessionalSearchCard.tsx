import type { ProfessionalPublic } from "../../types";
import { getConsultationModeLabel } from "../../utils/labels";
import { Avatar, Badge, Button, Icon } from "../ui";

interface ProfessionalSearchCardProps {
  professional: ProfessionalPublic;
  onSelect: () => void;
}

export function ProfessionalSearchCard({ onSelect, professional }: ProfessionalSearchCardProps) {
  const fullName = `${professional.user.first_name} ${professional.user.last_name}`;
  const location = [professional.city, professional.country].filter(Boolean).join(", ");

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-3">
          <Avatar name={fullName} />
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-ink-900">{fullName}</h2>
            <p className="mt-1 text-sm text-ink-500">{professional.title ?? "Profesional registrado"}</p>
          </div>
        </div>
        <Badge className="self-start" label={getConsultationModeLabel(professional.consultation_mode)} tone="info" />
      </div>

      <p className="mt-4 line-clamp-3 text-sm leading-6 text-ink-600">{professional.bio ?? "Este profesional aun no publico una presentacion."}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge label={professional.category.name} tone="neutral" />
        {professional.specialties.slice(0, 4).map((specialty) => (
          <Badge key={specialty.id} label={specialty.name} tone="success" />
        ))}
      </div>

      <div className="mt-5 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="inline-flex items-center gap-2 text-sm text-ink-500">
          <Icon className="h-4 w-4" name="user" />
          {location || "Atencion remota o ubicacion no publicada"}
        </p>
        <Button className="w-full sm:w-auto" onClick={onSelect}>
          Ver perfil y horarios
        </Button>
      </div>
    </article>
  );
}
