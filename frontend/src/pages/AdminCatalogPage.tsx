import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import {
  createAdminCategory,
  createAdminSpecialty,
  fetchAdminCategories,
  fetchAdminSpecialties,
  updateAdminCategory,
  updateAdminSpecialty,
} from "../api/queries";
import { AdminStatusPill } from "../components/admin/AdminStatusPill";
import { Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";

export function AdminCatalogPage() {
  const queryClient = useQueryClient();
  const categoriesQuery = useQuery({ queryKey: ["admin-categories"], queryFn: fetchAdminCategories });
  const specialtiesQuery = useQuery({ queryKey: ["admin-specialties"], queryFn: () => fetchAdminSpecialties() });
  const [categoryName, setCategoryName] = useState("");
  const [specialtyName, setSpecialtyName] = useState("");
  const [specialtyCategoryId, setSpecialtyCategoryId] = useState("");

  const refreshCatalog = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-specialties"] });
    void queryClient.invalidateQueries({ queryKey: ["categories"] });
    void queryClient.invalidateQueries({ queryKey: ["specialties"] });
  };

  const createCategoryMutation = useMutation({
    mutationFn: createAdminCategory,
    onSuccess: () => {
      setCategoryName("");
      refreshCatalog();
    },
  });
  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => updateAdminCategory(id, { is_active }),
    onSuccess: refreshCatalog,
  });
  const createSpecialtyMutation = useMutation({
    mutationFn: createAdminSpecialty,
    onSuccess: () => {
      setSpecialtyName("");
      refreshCatalog();
    },
  });
  const updateSpecialtyMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => updateAdminSpecialty(id, { is_active }),
    onSuccess: refreshCatalog,
  });

  if (categoriesQuery.isLoading || specialtiesQuery.isLoading) {
    return <LoadingState label="Cargando catalogo administrativo" />;
  }

  if (categoriesQuery.isError || specialtiesQuery.isError) {
    return <ErrorState title="No pudimos cargar el catalogo" message="Intenta nuevamente en unos minutos." />;
  }

  const categories = categoriesQuery.data ?? [];
  const specialties = specialtiesQuery.data ?? [];
  const mutationError =
    createCategoryMutation.error ?? updateCategoryMutation.error ?? createSpecialtyMutation.error ?? updateSpecialtyMutation.error;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Catalogo administrativo"
        description="Gestiona categorias y especialidades visibles en la busqueda de profesionales."
      />

      {mutationError ? <ErrorState title="No pudimos guardar el cambio" message={normalizeApiError(mutationError).message} /> : null}

      <div className="grid gap-5 xl:grid-cols-2">
        <SectionCard title="Categorias" description="Agrupan profesionales y especialidades del marketplace.">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
              <div className="space-y-1">
                <Label htmlFor="category-name">Nueva categoria</Label>
                <Input id="category-name" onChange={(event) => setCategoryName(event.target.value)} placeholder="Ej: Salud" value={categoryName} />
              </div>
              <div className="flex items-end">
                <Button
                  className="w-full sm:w-auto"
                  disabled={!categoryName.trim()}
                  isLoading={createCategoryMutation.isPending}
                  onClick={() => createCategoryMutation.mutate({ name: categoryName.trim(), is_active: true })}
                >
                  Crear
                </Button>
              </div>
            </div>
          </div>

          {categories.length === 0 ? (
            <EmptyState title="Aun no existen categorias" description="Crea la primera categoria para organizar el catalogo." />
          ) : null}

          <div className="mt-5 hidden overflow-hidden rounded-lg border border-slate-200 md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-ink-500">
                <tr>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Identificador</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3 text-right">Accion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {categories.map((category) => (
                  <tr className="transition hover:bg-slate-50" key={category.id}>
                    <td className="px-4 py-4 font-semibold text-ink-900">{category.name}</td>
                    <td className="px-4 py-4 text-ink-500">{category.slug}</td>
                    <td className="px-4 py-4">
                      <AdminStatusPill active={category.is_active} activeLabel="Activa" inactiveLabel="Inactiva" />
                    </td>
                    <td className="px-4 py-4 text-right">
                      <Button
                        isLoading={updateCategoryMutation.isPending}
                        onClick={() => updateCategoryMutation.mutate({ id: category.id, is_active: !category.is_active })}
                        size="sm"
                        variant="secondary"
                      >
                        {category.is_active ? "Desactivar" : "Activar"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-5 space-y-3 md:hidden">
            {categories.map((category) => (
              <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={category.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-ink-900">{category.name}</h3>
                    <p className="mt-1 text-sm text-ink-500">{category.slug}</p>
                  </div>
                  <AdminStatusPill active={category.is_active} activeLabel="Activa" inactiveLabel="Inactiva" />
                </div>
                <Button
                  className="mt-4 w-full"
                  isLoading={updateCategoryMutation.isPending}
                  onClick={() => updateCategoryMutation.mutate({ id: category.id, is_active: !category.is_active })}
                  size="sm"
                  variant="secondary"
                >
                  {category.is_active ? "Desactivar" : "Activar"}
                </Button>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Especialidades" description="Se asocian a una categoria existente.">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_1fr_auto]">
              <div className="space-y-1">
                <Label htmlFor="specialty-name">Nueva especialidad</Label>
                <Input
                  id="specialty-name"
                  onChange={(event) => setSpecialtyName(event.target.value)}
                  placeholder="Ej: Psicologia"
                  value={specialtyName}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="specialty-category">Categoria</Label>
                <Select id="specialty-category" onChange={(event) => setSpecialtyCategoryId(event.target.value)} value={specialtyCategoryId}>
                  <option value="">Selecciona categoria</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="flex items-end">
                <Button
                  className="w-full lg:w-auto"
                  disabled={!specialtyName.trim() || !specialtyCategoryId}
                  isLoading={createSpecialtyMutation.isPending}
                  onClick={() =>
                    createSpecialtyMutation.mutate({
                      name: specialtyName.trim(),
                      category_id: Number(specialtyCategoryId),
                      is_active: true,
                    })
                  }
                >
                  Crear
                </Button>
              </div>
            </div>
          </div>

          {specialties.length === 0 ? (
            <EmptyState title="Aun no existen especialidades" description="Crea especialidades asociadas a categorias activas." />
          ) : null}

          <div className="mt-5 hidden overflow-hidden rounded-lg border border-slate-200 md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-ink-500">
                <tr>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Categoria</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3 text-right">Accion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {specialties.map((specialty) => {
                  const category = categories.find((item) => item.id === specialty.category_id);
                  return (
                    <tr className="transition hover:bg-slate-50" key={specialty.id}>
                      <td className="px-4 py-4 font-semibold text-ink-900">{specialty.name}</td>
                      <td className="px-4 py-4 text-ink-500">{category?.name ?? "Categoria no disponible"}</td>
                      <td className="px-4 py-4">
                        <AdminStatusPill active={specialty.is_active} activeLabel="Activa" inactiveLabel="Inactiva" />
                      </td>
                      <td className="px-4 py-4 text-right">
                        <Button
                          isLoading={updateSpecialtyMutation.isPending}
                          onClick={() => updateSpecialtyMutation.mutate({ id: specialty.id, is_active: !specialty.is_active })}
                          size="sm"
                          variant="secondary"
                        >
                          {specialty.is_active ? "Desactivar" : "Activar"}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-5 space-y-3 md:hidden">
            {specialties.map((specialty) => {
              const category = categories.find((item) => item.id === specialty.category_id);
              return (
                <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={specialty.id}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-ink-900">{specialty.name}</h3>
                      <p className="mt-1 text-sm text-ink-500">{category?.name ?? "Categoria no disponible"}</p>
                    </div>
                    <AdminStatusPill active={specialty.is_active} activeLabel="Activa" inactiveLabel="Inactiva" />
                  </div>
                  <Button
                    className="mt-4 w-full"
                    isLoading={updateSpecialtyMutation.isPending}
                    onClick={() => updateSpecialtyMutation.mutate({ id: specialty.id, is_active: !specialty.is_active })}
                    size="sm"
                    variant="secondary"
                  >
                    {specialty.is_active ? "Desactivar" : "Activar"}
                  </Button>
                </article>
              );
            })}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
