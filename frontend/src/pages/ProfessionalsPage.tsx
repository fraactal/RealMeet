import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { normalizeApiError } from "../api/errors";
import {
  createAppointment,
  fetchCategories,
  fetchProfessional,
  fetchProfessionalAvailability,
  fetchProfessionals,
  fetchSpecialties,
} from "../api/queries";
import { PublicProfessionalCard } from "../components/public/PublicProfessionalCard";
import { SlotPicker } from "../components/client/SlotPicker";
import { Avatar, Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import { useAuthStore } from "../store/auth";
import type { AvailableSlot, ConsultationMode, ProfessionalSearchParams } from "../types";
import { formatLongDate, formatTime } from "../utils/dates";
import { getConsultationModeLabel } from "../utils/labels";

const PAGE_SIZE = 6;
const today = new Date().toISOString().slice(0, 10);

export function ProfessionalsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [specialtyId, setSpecialtyId] = useState("");
  const [consultationMode, setConsultationMode] = useState("");
  const [page, setPage] = useState(1);
  const [selectedProfessionalId, setSelectedProfessionalId] = useState<number | null>(null);
  const [availabilityDate, setAvailabilityDate] = useState(today);
  const [selectedSlot, setSelectedSlot] = useState<AvailableSlot | null>(null);
  const [bookingMessage, setBookingMessage] = useState<string | null>(null);

  useEffect(() => {
    document.title = "Profesionales | RealMeet";
  }, []);

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
  const availabilityQuery = useQuery({
    queryKey: ["professional-availability", selectedProfessionalId, availabilityDate],
    queryFn: () => fetchProfessionalAvailability(selectedProfessionalId ?? 0, availabilityDate),
    enabled: selectedProfessionalId !== null,
    retry: false,
  });
  const bookingMutation = useMutation({
    mutationFn: (slot: AvailableSlot) =>
      createAppointment({
        professional_id: selectedProfessionalId ?? 0,
        specialty_id: specialtyId ? Number(specialtyId) : null,
        start_datetime: slot.start_datetime,
      }),
    onSuccess: () => {
      setBookingMessage("Reserva creada correctamente. Puedes revisarla en Mis reservas.");
      setSelectedSlot(null);
      void queryClient.invalidateQueries({ queryKey: ["my-appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["client-dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["professional-availability", selectedProfessionalId, availabilityDate] });
    },
    onError: (error) => {
      setBookingMessage(normalizeApiError(error).message);
    },
  });

  const resetSelection = () => {
    setSelectedProfessionalId(null);
    setSelectedSlot(null);
    setBookingMessage(null);
  };

  const resetPage = () => {
    setPage(1);
    resetSelection();
  };

  const clearFilters = () => {
    setSearch("");
    setCategoryId("");
    setSpecialtyId("");
    setConsultationMode("");
    resetPage();
  };

  const data = professionalsQuery.data;
  const canBook = user?.role === "client";
  const isPublicVisitor = !user;
  const selectedProfessional = detailQuery.data;
  const selectedFullName = selectedProfessional
    ? `${selectedProfessional.user.first_name} ${selectedProfessional.user.last_name}`
    : "Profesional seleccionado";
  const selectedLocation = selectedProfessional ? [selectedProfessional.city, selectedProfessional.country].filter(Boolean).join(", ") : "";

  return (
    <div className="space-y-6">
      <PageHeader
        title={isPublicVisitor ? "Profesionales disponibles" : "Buscar profesionales"}
        description={
          isPublicVisitor
            ? "Explora perfiles publicados, revisa disponibilidad y crea tu cuenta cuando quieras continuar con una reserva."
            : "Encuentra profesionales publicados, revisa su informacion disponible y elige un horario para reservar."
        }
      />

      <SectionCard title="Filtros" description="Ajusta la busqueda con los filtros disponibles actualmente.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div className="space-y-1 xl:col-span-2">
            <Label htmlFor="professional-search">Busqueda</Label>
            <Input
              id="professional-search"
              onChange={(event) => {
                setSearch(event.target.value);
                resetPage();
              }}
              placeholder="Nombre, titulo o presentacion"
              value={search}
            />
          </div>

          <div className="space-y-1">
            <Label htmlFor="category-filter">Categoria</Label>
            <Select
              id="category-filter"
              onChange={(event) => {
                setCategoryId(event.target.value);
                setSpecialtyId("");
                resetPage();
              }}
              value={categoryId}
            >
              <option value="">Todas</option>
              {categoriesQuery.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1">
            <Label htmlFor="specialty-filter">Especialidad</Label>
            <Select
              id="specialty-filter"
              onChange={(event) => {
                setSpecialtyId(event.target.value);
                resetPage();
              }}
              value={specialtyId}
            >
              <option value="">Todas</option>
              {specialtiesQuery.data?.map((specialty) => (
                <option key={specialty.id} value={specialty.id}>
                  {specialty.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1">
            <Label htmlFor="mode-filter">Modalidad</Label>
            <Select
              id="mode-filter"
              onChange={(event) => {
                setConsultationMode(event.target.value);
                resetPage();
              }}
              value={consultationMode}
            >
              <option value="">Todas</option>
              <option value="online">Online</option>
              <option value="presencial">Presencial</option>
              <option value="hybrid">Hibrida</option>
            </Select>
          </div>
        </div>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-ink-500">{data ? `${data.total} profesionales encontrados` : "Buscando profesionales"}</p>
          <Button onClick={clearFilters} variant="secondary">
            Limpiar filtros
          </Button>
        </div>
      </SectionCard>

      {professionalsQuery.isError ? (
        <ErrorState title="No pudimos cargar los profesionales" message="Intenta ajustar la busqueda o reintentar en unos minutos." />
      ) : null}

      {professionalsQuery.isPending ? <LoadingState label="Cargando profesionales" /> : null}

      {!professionalsQuery.isPending && data?.items.length === 0 ? (
        <EmptyState title="No encontramos profesionales con esos filtros" description="Intenta ampliar la busqueda o limpiar los filtros." />
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        {data?.items.map((professional) => (
          <PublicProfessionalCard
            key={professional.id}
            onSelect={() => {
              setSelectedProfessionalId(professional.id);
              setAvailabilityDate(today);
              setSelectedSlot(null);
              setBookingMessage(null);
            }}
            professional={professional}
          />
        ))}
      </div>

      {data && data.total_pages > 1 ? (
        <div className="flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
          <Button disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))} variant="secondary">
            Anterior
          </Button>
          <span className="text-center text-sm text-ink-500">
            Pagina {data.page} de {data.total_pages}
          </span>
          <Button disabled={page >= data.total_pages} onClick={() => setPage((current) => current + 1)} variant="secondary">
            Siguiente
          </Button>
        </div>
      ) : null}

      {selectedProfessionalId !== null ? (
        <SectionCard
          title="Perfil profesional"
          description="Revisa la informacion publica antes de seleccionar un horario."
          actions={
            <Button onClick={resetSelection} variant="secondary">
              Cerrar
            </Button>
          }
        >
          {detailQuery.isPending ? <LoadingState label="Cargando perfil profesional" /> : null}
          {detailQuery.isError ? (
            <ErrorState title="No pudimos cargar el perfil" message="Intenta seleccionar nuevamente al profesional." />
          ) : null}
          {selectedProfessional ? (
            <div className="space-y-6">
              <div className="flex flex-col gap-4 border-b border-slate-100 pb-5 md:flex-row md:items-start md:justify-between">
                <div className="flex gap-4">
                  <Avatar name={selectedFullName} />
                  <div>
                    <h2 className="text-2xl font-semibold text-ink-900">{selectedFullName}</h2>
                    <p className="mt-1 text-sm text-ink-500">{selectedProfessional.title ?? "Profesional registrado"}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge label={selectedProfessional.category.name} tone="neutral" />
                      <Badge label={getConsultationModeLabel(selectedProfessional.consultation_mode)} tone="info" />
                    </div>
                  </div>
                </div>
                <dl className="grid gap-3 text-sm text-ink-500 sm:grid-cols-3 md:text-right">
                  <div>
                    <dt className="font-semibold text-ink-700">Duracion</dt>
                    <dd>{selectedProfessional.session_duration_minutes} min</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink-700">Experiencia</dt>
                    <dd>{selectedProfessional.years_experience ? `${selectedProfessional.years_experience} anos` : "No publicada"}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-ink-700">Ubicacion</dt>
                    <dd>{selectedLocation || "No publicada"}</dd>
                  </div>
                </dl>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
                <div className="space-y-5">
                  <div>
                    <h3 className="text-base font-semibold text-ink-900">Presentacion</h3>
                    <p className="mt-2 text-sm leading-6 text-ink-600">
                      {selectedProfessional.bio ?? "Este profesional aun no publico una presentacion."}
                    </p>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-ink-900">Especialidades</h3>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedProfessional.specialties.map((specialty) => (
                        <Badge key={specialty.id} label={specialty.name} tone="success" />
                      ))}
                      {selectedProfessional.specialties.length === 0 ? <p className="text-sm text-ink-500">Sin especialidades publicadas.</p> : null}
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div className="space-y-1">
                      <Label htmlFor="availability-date">Fecha</Label>
                      <Input
                        id="availability-date"
                        min={today}
                        onChange={(event) => {
                          setAvailabilityDate(event.target.value);
                          setSelectedSlot(null);
                          setBookingMessage(null);
                        }}
                        type="date"
                        value={availabilityDate}
                      />
                    </div>
                    <p className="text-sm text-ink-500">
                      {canBook ? "Elige un horario disponible." : "Inicia sesion o crea tu cuenta para confirmar una reserva."}
                    </p>
                  </div>

                  <div className="mt-5 space-y-4">
                    {availabilityQuery.isPending ? <LoadingState label="Cargando horarios disponibles" /> : null}
                    {availabilityQuery.isError ? (
                      <ErrorState title="No pudimos cargar los horarios" message="Intenta seleccionar otra fecha." />
                    ) : null}
                    {availabilityQuery.data && availabilityQuery.data.slots.length === 0 ? (
                      <EmptyState title="No hay horarios disponibles" description="Prueba con otra fecha para revisar nuevas opciones." />
                    ) : null}
                    {availabilityQuery.data && availabilityQuery.data.slots.length > 0 ? (
                      <SlotPicker
                        disabled={!canBook}
                        isPending={bookingMutation.isPending}
                        onSelect={(slot) => {
                          setSelectedSlot(slot);
                          setBookingMessage(null);
                        }}
                        selectedSlotStart={selectedSlot?.start_datetime}
                        slots={availabilityQuery.data.slots}
                      />
                    ) : null}
                  </div>

                  {selectedSlot ? (
                    <div className="mt-5 rounded-lg border border-brand-200 bg-white p-4">
                      <h3 className="text-base font-semibold text-ink-900">Confirma tu reserva</h3>
                      <dl className="mt-3 space-y-2 text-sm text-ink-600">
                        <div className="flex justify-between gap-4">
                          <dt className="font-semibold text-ink-800">Profesional</dt>
                          <dd className="text-right">{selectedFullName}</dd>
                        </div>
                        <div className="flex justify-between gap-4">
                          <dt className="font-semibold text-ink-800">Fecha</dt>
                          <dd className="text-right">{formatLongDate(selectedSlot.start_datetime)}</dd>
                        </div>
                        <div className="flex justify-between gap-4">
                          <dt className="font-semibold text-ink-800">Hora</dt>
                          <dd className="text-right">
                            {formatTime(selectedSlot.start_datetime)} a {formatTime(selectedSlot.end_datetime)}
                          </dd>
                        </div>
                        <div className="flex justify-between gap-4">
                          <dt className="font-semibold text-ink-800">Modalidad</dt>
                          <dd className="text-right">{getConsultationModeLabel(selectedProfessional.consultation_mode)}</dd>
                        </div>
                      </dl>
                      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                        <Button
                          className="w-full sm:w-auto"
                          disabled={!canBook}
                          isLoading={bookingMutation.isPending}
                          onClick={() => {
                            setBookingMessage(null);
                            bookingMutation.mutate(selectedSlot);
                          }}
                        >
                          {canBook ? "Confirmar reserva" : "Inicia sesion para reservar"}
                        </Button>
                        {!canBook ? (
                          <Link className="w-full sm:w-auto" to="/register">
                            <Button className="w-full" variant="secondary">
                              Crear cuenta
                            </Button>
                          </Link>
                        ) : null}
                        <Button className="w-full sm:w-auto" onClick={() => setSelectedSlot(null)} variant="secondary">
                          Elegir otro horario
                        </Button>
                      </div>
                    </div>
                  ) : !canBook && availabilityQuery.data && availabilityQuery.data.slots.length > 0 ? (
                    <div className="mt-5 rounded-lg border border-brand-200 bg-white p-4">
                      <h3 className="text-base font-semibold text-ink-900">Continua con una cuenta</h3>
                      <p className="mt-2 text-sm leading-6 text-ink-500">
                        Puedes revisar horarios disponibles. Para confirmar una reserva necesitas iniciar sesion o crear una cuenta cliente.
                      </p>
                      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                        <Link className="w-full sm:w-auto" to="/login">
                          <Button className="w-full">Iniciar sesion</Button>
                        </Link>
                        <Link className="w-full sm:w-auto" to="/register">
                          <Button className="w-full" variant="secondary">
                            Crear cuenta
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ) : null}

                  {bookingMessage ? <p className="mt-4 text-sm font-semibold text-ink-700">{bookingMessage}</p> : null}
                </div>
              </div>
            </div>
          ) : null}
        </SectionCard>
      ) : null}
    </div>
  );
}
