import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchCategories,
  fetchProfessionalPublicProfile,
  fetchProfessionalSpecialties,
  fetchSpecialties,
  updateProfessionalPublicProfile,
  updateProfessionalSpecialties,
} from "../api/queries";
import { Card } from "../components/ui/Card";
import type { ConsultationMode, ProfessionalPublicProfileUpdate } from "../types";

export function ProfessionalCatalogPage() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery({ queryKey: ["professional-public-profile"], queryFn: fetchProfessionalPublicProfile });
  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: fetchCategories });
  const allSpecialtiesQuery = useQuery({ queryKey: ["specialties"], queryFn: () => fetchSpecialties() });
  const mySpecialtiesQuery = useQuery({ queryKey: ["professional-specialties"], queryFn: fetchProfessionalSpecialties });

  const [profileForm, setProfileForm] = useState({
    title: "",
    bio: "",
    years_experience: "",
    consultation_mode: "online" as ConsultationMode,
    session_duration_minutes: "60",
    city: "",
    country: "",
    category_id: "",
    is_public: true,
  });
  const [selectedSpecialties, setSelectedSpecialties] = useState<number[]>([]);

  useEffect(() => {
    if (!profileQuery.data) return;
    setProfileForm({
      title: profileQuery.data.title ?? "",
      bio: profileQuery.data.bio ?? "",
      years_experience: profileQuery.data.years_experience?.toString() ?? "",
      consultation_mode: profileQuery.data.consultation_mode,
      session_duration_minutes: profileQuery.data.session_duration_minutes.toString(),
      city: profileQuery.data.city ?? "",
      country: profileQuery.data.country ?? "",
      category_id: profileQuery.data.category_id?.toString() ?? "",
      is_public: profileQuery.data.is_public,
    });
  }, [profileQuery.data]);

  useEffect(() => {
    setSelectedSpecialties(mySpecialtiesQuery.data?.map((specialty) => specialty.id) ?? []);
  }, [mySpecialtiesQuery.data]);

  const filteredSpecialties = useMemo(() => {
    const categoryId = profileForm.category_id ? Number(profileForm.category_id) : null;
    return allSpecialtiesQuery.data?.filter((specialty) => !categoryId || specialty.category_id === categoryId) ?? [];
  }, [allSpecialtiesQuery.data, profileForm.category_id]);

  const profileMutation = useMutation({
    mutationFn: updateProfessionalPublicProfile,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["professional-public-profile"] }),
  });
  const specialtiesMutation = useMutation({
    mutationFn: updateProfessionalSpecialties,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["professional-specialties"] }),
  });

  const saveProfile = () => {
    const payload: ProfessionalPublicProfileUpdate = {
      title: profileForm.title || null,
      bio: profileForm.bio || null,
      years_experience: profileForm.years_experience ? Number(profileForm.years_experience) : null,
      consultation_mode: profileForm.consultation_mode,
      session_duration_minutes: profileForm.session_duration_minutes ? Number(profileForm.session_duration_minutes) : null,
      city: profileForm.city || null,
      country: profileForm.country || null,
      category_id: profileForm.category_id ? Number(profileForm.category_id) : null,
      is_public: profileForm.is_public,
    };
    profileMutation.mutate(payload);
  };

  const toggleSpecialty = (specialtyId: number) => {
    setSelectedSpecialties((current) =>
      current.includes(specialtyId) ? current.filter((id) => id !== specialtyId) : [...current, specialtyId],
    );
  };

  if (profileQuery.isLoading || categoriesQuery.isLoading || allSpecialtiesQuery.isLoading || mySpecialtiesQuery.isLoading) {
    return <p className="text-slate-500">Cargando catalogo profesional...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Catalogo profesional</h1>
        <p className="text-slate-600">Administra los datos publicos y especialidades visibles en busqueda.</p>
      </div>

      <Card title="Perfil publico">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Titulo
            <input
              value={profileForm.title}
              onChange={(event) => setProfileForm((current) => ({ ...current, title: event.target.value }))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Categoria
            <select
              value={profileForm.category_id}
              onChange={(event) => {
                setProfileForm((current) => ({ ...current, category_id: event.target.value }));
                setSelectedSpecialties([]);
              }}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="">Sin categoria</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700 md:col-span-2">
            Biografia
            <textarea
              value={profileForm.bio}
              onChange={(event) => setProfileForm((current) => ({ ...current, bio: event.target.value }))}
              rows={4}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Modalidad
            <select
              value={profileForm.consultation_mode}
              onChange={(event) =>
                setProfileForm((current) => ({ ...current, consultation_mode: event.target.value as ConsultationMode }))
              }
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            >
              <option value="online">Online</option>
              <option value="presencial">Presencial</option>
              <option value="hybrid">Hibrida</option>
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Duracion
            <input
              type="number"
              min={15}
              value={profileForm.session_duration_minutes}
              onChange={(event) => setProfileForm((current) => ({ ...current, session_duration_minutes: event.target.value }))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Ciudad
            <input
              value={profileForm.city}
              onChange={(event) => setProfileForm((current) => ({ ...current, city: event.target.value }))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>
          <label className="space-y-1 text-sm font-medium text-slate-700">
            Pais
            <input
              value={profileForm.country}
              onChange={(event) => setProfileForm((current) => ({ ...current, country: event.target.value }))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
            />
          </label>
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={profileForm.is_public}
              onChange={(event) => setProfileForm((current) => ({ ...current, is_public: event.target.checked }))}
            />
            Perfil publico
          </label>
        </div>
        <button className="mt-5 rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={saveProfile}>
          Guardar perfil
        </button>
      </Card>

      <Card title="Especialidades">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredSpecialties.map((specialty) => (
            <label key={specialty.id} className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <input type="checkbox" checked={selectedSpecialties.includes(specialty.id)} onChange={() => toggleSpecialty(specialty.id)} />
              {specialty.name}
            </label>
          ))}
        </div>
        <button
          className="mt-5 rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white"
          onClick={() => specialtiesMutation.mutate({ specialty_ids: selectedSpecialties })}
        >
          Guardar especialidades
        </button>
      </Card>
    </div>
  );
}
