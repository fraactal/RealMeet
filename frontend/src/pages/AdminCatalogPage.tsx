import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAdminCategory,
  createAdminSpecialty,
  fetchAdminCategories,
  fetchAdminSpecialties,
  updateAdminCategory,
  updateAdminSpecialty,
} from "../api/queries";
import { Card } from "../components/ui/Card";

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
    return <p className="text-slate-500">Cargando catalogo...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Catalogo administrativo</h1>
        <p className="text-slate-600">Gestion minima de categorias y especialidades del marketplace.</p>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="Categorias">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={categoryName}
              onChange={(event) => setCategoryName(event.target.value)}
              placeholder="Nueva categoria"
              className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
            <button
              className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
              onClick={() => createCategoryMutation.mutate({ name: categoryName.trim(), is_active: true })}
              disabled={!categoryName.trim()}
            >
              Crear
            </button>
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Nombre</th>
                  <th className="py-2">Slug</th>
                  <th className="py-2">Estado</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {categoriesQuery.data?.map((category) => (
                  <tr key={category.id} className="border-t border-slate-100">
                    <td className="py-3 font-medium text-slate-700">{category.name}</td>
                    <td className="py-3 text-slate-500">{category.slug}</td>
                    <td className="py-3 text-slate-500">{category.is_active ? "Activa" : "Inactiva"}</td>
                    <td className="py-3 text-right">
                      <button
                        className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                        onClick={() => updateCategoryMutation.mutate({ id: category.id, is_active: !category.is_active })}
                      >
                        {category.is_active ? "Desactivar" : "Activar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Especialidades">
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
            <input
              value={specialtyName}
              onChange={(event) => setSpecialtyName(event.target.value)}
              placeholder="Nueva especialidad"
              className="min-w-0 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
            <select
              value={specialtyCategoryId}
              onChange={(event) => setSpecialtyCategoryId(event.target.value)}
              className="min-w-0 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">Categoria</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <button
              className="rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
              onClick={() =>
                createSpecialtyMutation.mutate({
                  name: specialtyName.trim(),
                  category_id: Number(specialtyCategoryId),
                  is_active: true,
                })
              }
              disabled={!specialtyName.trim() || !specialtyCategoryId}
            >
              Crear
            </button>
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="py-2">Nombre</th>
                  <th className="py-2">Categoria</th>
                  <th className="py-2">Estado</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {specialtiesQuery.data?.map((specialty) => {
                  const category = categoriesQuery.data?.find((item) => item.id === specialty.category_id);
                  return (
                    <tr key={specialty.id} className="border-t border-slate-100">
                      <td className="py-3 font-medium text-slate-700">{specialty.name}</td>
                      <td className="py-3 text-slate-500">{category?.name ?? specialty.category_id}</td>
                      <td className="py-3 text-slate-500">{specialty.is_active ? "Activa" : "Inactiva"}</td>
                      <td className="py-3 text-right">
                        <button
                          className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                          onClick={() => updateSpecialtyMutation.mutate({ id: specialty.id, is_active: !specialty.is_active })}
                        >
                          {specialty.is_active ? "Desactivar" : "Activar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
