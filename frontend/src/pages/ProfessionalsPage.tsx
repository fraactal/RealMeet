import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import { fetchCategories, fetchProfessional, fetchProfessionals, fetchSpecialties } from "../api/queries";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import type { ConsultationMode, ProfessionalSearchParams } from "../types";

const PAGE_SIZE = 6;

export function ProfessionalsPage() {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [specialtyId, setSpecialtyId] = useState("");
  const [consultationMode, setConsultationMode] = useState("");
  const [page, setPage] = useState(1);
  const [selectedProfessionalId, setSelectedProfessionalId] = useState<number | null>(null);

  const filters = useMemo<ProfessionalSearchParams>(
    () => ({
      search: search.trim() || undefined,
      category_id: categoryId ? Number(categoryId) : undefined,
      specialty_id: specialtyId ? Number(specialtyId) : undefined,
      consultation_mode: consultationMode ? (consultationMode as ConsultationMode) : undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [categoryId, consultationMode, page, search, specialtyId],
  );

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: fetchCategories,
    retry: false,
  });
  const specialtiesQuery = useQuery({
    queryKey: ["specialties", categoryId],
    queryFn: () => fetchSpecialties(categoryId ? Number(categoryId) : undefined),
    retry: false,
  });
  const professionalsQuery = useQuery({
    queryKey: ["professionals", filters],
    queryFn: () => fetchProfessionals(filters),
    retry: false,
  });
  const detailQuery = useQuery({
    queryKey: ["professional", selectedProfessionalId],
    queryFn: () => fetchProfessional(selectedProfessionalId ?? 0),
    enabled: selectedProfessionalId !== null,
    retry: false,
  });

  const resetPage = () => {
    setPage(1);
    setSelectedProfessionalId(null);
  };

  const clearFilters = () => {
    setSearch("");
    setCategoryId("");
    setSpecialtyId("");
    setConsultationMode("");
    resetPage();
  };

  const apiError = professionalsQuery.isError ? normalizeApiError(professionalsQuery.error) : null;
  const data = professionalsQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Profesionales disponibles</h1>
        <p className="text-slate-600">Busca por nombre, especialidad, categoria o modalidad de atencion.</p>
      </div>

      <Card>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <label className="space-y-1 text-sm font-medium text-slate-700 xl:col-span-2">
            Busqueda
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                resetPage();
              }}
              placeholder="Nombre, titulo o bio"
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>

          <label className="space-y-1 text-sm font-medium text-slate-700">
            Categoria
            <select
              value={categoryId}
              onChange={(event) => {
                setCategoryId(event.target.value);
                setSpecialtyId("");
                resetPage();
              }}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">Todas</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1 text-sm font-medium text-slate-700">
            Especialidad
            <select
              value={specialtyId}
              onChange={(event) => {
                setSpecialtyId(event.target.value);
                resetPage();
              }}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">Todas</option>
              {specialtiesQuery.data?.map((specialty) => (
                <option key={specialty.id} value={specialty.id}>
                  {specialty.name}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1 text-sm font-medium text-slate-700">
            Modalidad
            <select
              value={consultationMode}
              onChange={(event) => {
                setConsultationMode(event.target.value);
                resetPage();
              }}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">Todas</option>
              <option value="online">Online</option>
              <option value="presencial">Presencial</option>
              <option value="hybrid">Hibrida</option>
            </select>
          </label>
        </div>
        <div className="mt-4 flex items-center justify-between gap-3">
          <p className="text-sm text-slate-500">{data ? `${data.total} resultados` : "Cargando resultados"}</p>
          <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" onClick={clearFilters}>
            Limpiar filtros
          </button>
        </div>
      </Card>

      {apiError ? (
        <div className="space-y-4 rounded-xl border border-red-100 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-700">{apiError.message}</p>
          <button className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={() => void professionalsQuery.refetch()}>
            Reintentar
          </button>
        </div>
      ) : null}

      {professionalsQuery.isPending ? <p className="text-slate-500">Cargando profesionales...</p> : null}

      {!professionalsQuery.isPending && data?.items.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          No se encontraron profesionales con esos filtros.
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        {data?.items.map((professional) => (
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
            <p className="mt-4 line-clamp-3 text-sm text-slate-600">{professional.bio ?? "Sin biografia publicada."}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {professional.specialties.map((specialty) => (
                <span key={specialty.id} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  {specialty.name}
                </span>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 text-sm text-slate-500">
              <span>{professional.category.name}</span>
              <span>
                {professional.city ?? "Remoto"}
                {professional.country ? `, ${professional.country}` : ""}
              </span>
            </div>
            <button
              className="mt-4 rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
              onClick={() => setSelectedProfessionalId(professional.id)}
            >
              Ver detalle
            </button>
          </Card>
        ))}
      </div>

      {data && data.total_pages > 1 ? (
        <div className="flex items-center justify-center gap-3">
          <button
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(current - 1, 1))}
          >
            Anterior
          </button>
          <span className="text-sm text-slate-600">
            Pagina {data.page} de {data.total_pages}
          </span>
          <button
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
            disabled={page >= data.total_pages}
            onClick={() => setPage((current) => current + 1)}
          >
            Siguiente
          </button>
        </div>
      ) : null}

      {selectedProfessionalId !== null ? (
        <Card title="Detalle profesional">
          {detailQuery.isPending ? <p className="text-sm text-slate-500">Cargando detalle...</p> : null}
          {detailQuery.isError ? <p className="text-sm text-red-600">{normalizeApiError(detailQuery.error).message}</p> : null}
          {detailQuery.data ? (
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold text-ink">
                    {detailQuery.data.user.first_name} {detailQuery.data.user.last_name}
                  </h2>
                  <p className="text-slate-500">{detailQuery.data.title}</p>
                </div>
                <button className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700" onClick={() => setSelectedProfessionalId(null)}>
                  Cerrar
                </button>
              </div>
              <p className="text-sm leading-6 text-slate-600">{detailQuery.data.bio ?? "Sin biografia publicada."}</p>
              <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="font-semibold text-slate-700">Categoria</dt>
                  <dd className="text-slate-600">{detailQuery.data.category.name}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-700">Modalidad</dt>
                  <dd className="text-slate-600">{detailQuery.data.consultation_mode}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-700">Duracion</dt>
                  <dd className="text-slate-600">{detailQuery.data.session_duration_minutes} min</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-700">Experiencia</dt>
                  <dd className="text-slate-600">{detailQuery.data.years_experience ?? "No publicada"}</dd>
                </div>
              </dl>
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
