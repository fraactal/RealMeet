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
import { normalizeApiError } from "../api/errors";
import { Avatar, Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select, Textarea } from "../components/ui";
import type { ConsultationMode, ProfessionalPublicProfileUpdate } from "../types";
import { getConsultationModeLabel } from "../utils/labels";

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
  const [profileSaved, setProfileSaved] = useState(false);
  const [specialtiesSaved, setSpecialtiesSaved] = useState(false);

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
    onSuccess: () => {
      setProfileSaved(true);
      void queryClient.invalidateQueries({ queryKey: ["professional-public-profile"] });
    },
  });
  const specialtiesMutation = useMutation({
    mutationFn: updateProfessionalSpecialties,
    onSuccess: () => {
      setSpecialtiesSaved(true);
      void queryClient.invalidateQueries({ queryKey: ["professional-specialties"] });
    },
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
    return <LoadingState label="Cargando tu perfil publico" />;
  }

  if (profileQuery.isError || categoriesQuery.isError || allSpecialtiesQuery.isError || mySpecialtiesQuery.isError) {
    return <ErrorState title="No pudimos cargar tu perfil" message="Intenta nuevamente antes de editar tu informacion publica." />;
  }

  const selectedCategory = categoriesQuery.data?.find((category) => category.id.toString() === profileForm.category_id);
  const completedFields = [
    profileForm.title,
    profileForm.bio,
    profileForm.category_id,
    profileForm.city,
    profileForm.country,
    profileForm.session_duration_minutes,
    selectedSpecialties.length > 0 ? "specialties" : "",
  ].filter(Boolean).length;
  const completion = Math.round((completedFields / 7) * 100);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Perfil publico profesional"
        description="Administra como te ven los clientes al buscar profesionales y revisar disponibilidad."
      />

      <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
        <SectionCard title="Vista previa" description="Resumen visible con los datos publicos disponibles.">
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <Avatar name={profileForm.title || "RealMeet"} size="lg" />
              <div>
                <p className="text-lg font-semibold text-ink-900">{profileForm.title || "Titulo profesional pendiente"}</p>
                <p className="text-sm text-ink-500">{selectedCategory?.name ?? "Categoria no definida"}</p>
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-ink-900">Completitud del perfil</p>
              <div className="mt-3 h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-brand-700" style={{ width: `${completion}%` }} />
              </div>
              <p className="mt-2 text-sm text-ink-500">
                {completion >= 80 ? "Perfil listo para una buena presentacion." : "Agrega datos basicos para mejorar tu presencia publica."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge label={profileForm.is_public ? "Visible" : "No publicado"} tone={profileForm.is_public ? "success" : "warning"} />
              <Badge label={getConsultationModeLabel(profileForm.consultation_mode)} tone="info" />
              {profileForm.session_duration_minutes ? <Badge label={`${profileForm.session_duration_minutes} min`} tone="neutral" /> : null}
            </div>
            <p className="text-sm leading-6 text-ink-700">{profileForm.bio || "Tu biografia ayudara a los clientes a entender tu enfoque profesional."}</p>
          </div>
        </SectionCard>

        <SectionCard title="Informacion publica" description="Datos principales que aparecen en tu perfil.">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="profile-title">Titulo</Label>
              <Input
                id="profile-title"
              value={profileForm.title}
              onChange={(event) => setProfileForm((current) => ({ ...current, title: event.target.value }))}
            />
            </div>
            <div>
              <Label htmlFor="profile-category">Categoria</Label>
              <Select
                id="profile-category"
              value={profileForm.category_id}
              onChange={(event) => {
                setProfileForm((current) => ({ ...current, category_id: event.target.value }));
                setSelectedSpecialties([]);
              }}
            >
              <option value="">Sin categoria</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
              </Select>
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="profile-bio">Biografia</Label>
              <Textarea
                id="profile-bio"
              value={profileForm.bio}
              onChange={(event) => setProfileForm((current) => ({ ...current, bio: event.target.value }))}
              rows={4}
            />
            </div>
            <div>
              <Label htmlFor="profile-mode">Modalidad</Label>
              <Select
                id="profile-mode"
              value={profileForm.consultation_mode}
              onChange={(event) =>
                setProfileForm((current) => ({ ...current, consultation_mode: event.target.value as ConsultationMode }))
              }
            >
              <option value="online">Online</option>
              <option value="presencial">Presencial</option>
              <option value="hybrid">Hibrida</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="profile-duration">Duracion de sesion</Label>
              <Input
                id="profile-duration"
              type="number"
              min={15}
              value={profileForm.session_duration_minutes}
              onChange={(event) => setProfileForm((current) => ({ ...current, session_duration_minutes: event.target.value }))}
            />
            </div>
            <div>
              <Label htmlFor="profile-city">Ciudad</Label>
              <Input
                id="profile-city"
              value={profileForm.city}
              onChange={(event) => setProfileForm((current) => ({ ...current, city: event.target.value }))}
            />
            </div>
            <div>
              <Label htmlFor="profile-country">Pais</Label>
              <Input
                id="profile-country"
              value={profileForm.country}
              onChange={(event) => setProfileForm((current) => ({ ...current, country: event.target.value }))}
            />
            </div>
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-3 text-sm font-medium text-ink-700">
              <input
              type="checkbox"
              checked={profileForm.is_public}
              onChange={(event) => setProfileForm((current) => ({ ...current, is_public: event.target.checked }))}
            />
              Perfil publico
            </label>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button isLoading={profileMutation.isPending} onClick={saveProfile}>
              Guardar perfil
            </Button>
            {profileSaved ? <p className="text-sm font-semibold text-success-700">Perfil guardado.</p> : null}
          </div>
          {profileMutation.isError ? <ErrorState message={normalizeApiError(profileMutation.error).message} title="No se pudo guardar el perfil" /> : null}
        </SectionCard>
      </div>

      <SectionCard title="Especialidades" description="Selecciona las areas que corresponden a tu categoria principal.">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filteredSpecialties.map((specialty) => (
            <label key={specialty.id} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-ink-700">
              <input type="checkbox" checked={selectedSpecialties.includes(specialty.id)} onChange={() => toggleSpecialty(specialty.id)} />
              {specialty.name}
            </label>
          ))}
          {filteredSpecialties.length === 0 ? (
            <div className="sm:col-span-2 lg:col-span-3">
              <EmptyState title="Sin especialidades disponibles" description="Selecciona una categoria para revisar sus especialidades." />
            </div>
          ) : null}
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Button
          isLoading={specialtiesMutation.isPending}
          onClick={() => specialtiesMutation.mutate({ specialty_ids: selectedSpecialties })}
        >
          Guardar especialidades
          </Button>
          {specialtiesSaved ? <p className="text-sm font-semibold text-success-700">Especialidades guardadas.</p> : null}
        </div>
        {specialtiesMutation.isError ? (
          <ErrorState message={normalizeApiError(specialtiesMutation.error).message} title="No se pudieron guardar las especialidades" />
        ) : null}
      </SectionCard>
    </div>
  );
}
