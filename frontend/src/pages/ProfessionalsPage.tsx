import { useQuery } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import { fetchProfessionals } from "../api/queries";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";

export function ProfessionalsPage() {
  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["professionals"],
    queryFn: fetchProfessionals,
    retry: false,
  });

  if (isPending || isFetching) {
    return <p className="text-slate-500">Cargando profesionales...</p>;
  }

  if (isError) {
    const apiError = normalizeApiError(error);
    if (import.meta.env.DEV) {
      console.error("[ProfessionalsPage]", apiError);
    }
    return (
      <div className="space-y-4">
        <p className="text-red-600">{apiError.message}</p>
        <button className="rounded-xl bg-ink px-4 py-2 text-white" onClick={() => void refetch()}>
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Profesionales disponibles</h1>
        <p className="text-slate-600">Listado publico del marketplace inicial del MVP.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        {data?.map((professional) => (
          <Card key={professional.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">
                  {professional.user.first_name} {professional.user.last_name}
                </h2>
                <p className="text-sm text-slate-500">{professional.title ?? "Profesional registrado"}</p>
              </div>
              <Badge label={professional.consultation_mode} />
            </div>
            <p className="mt-4 text-sm text-slate-600">{professional.bio ?? "Sin biografia publicada."}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {professional.specialties.map((specialty) => (
                <span key={specialty} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  {specialty}
                </span>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4 text-sm text-slate-500">
              <span>{professional.category_name ?? "Sin categoria"}</span>
              <span>{professional.city ?? "Remoto"} {professional.country ? `, ${professional.country}` : ""}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
