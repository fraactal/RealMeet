import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  checkAdminExternalCalendarConflicts,
  createAdminExternalCalendar,
  disableAdminExternalCalendar,
  enableAdminExternalCalendar,
  fetchAdminAppointments,
  fetchAdminIntegrations,
  fetchAppointmentDocuments,
  fetchGoogleDocsTemplates,
  fetchAdminAvailableGoogleCalendars,
  fetchAdminCalendarSyncSettings,
  fetchAdminExternalCalendars,
  fetchAdminProfessionals,
  fetchAdminUsers,
  reconcileAdminAppointmentMeeting,
  reconcileAppointmentDocument,
  generateAppointmentDocument,
  retryAdminAppointmentMeetingCancel,
  retryAdminAppointmentMeetingCreate,
  retryAppointmentDocument,
  testAdminExternalCalendar,
  updateAdminCalendarSyncSettings,
  updateAdminProfessional,
  updateAdminUser,
} from "../api/queries";
import { AdminAppointmentCard } from "../components/admin/AdminAppointmentCard";
import { AdminPagination } from "../components/admin/AdminPagination";
import { AdminStatusPill } from "../components/admin/AdminStatusPill";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select, StatusBadge } from "../components/ui";
import type { Appointment, AppointmentGeneratedDocument, AppointmentStatus, ExternalCalendar, ExternalConflictFailurePolicy, GoogleDocsSharingPolicy, UserRole } from "../types";
import { formatDateTime } from "../utils/dates";
import { getAppointmentStatusLabel, getConsultationModeLabel, getRoleLabel } from "../utils/labels";

const PAGE_SIZE = 10;

export function AdminManagementPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [appointmentStatus, setAppointmentStatus] = useState("");
  const [usersPage, setUsersPage] = useState(1);
  const [professionalsPage, setProfessionalsPage] = useState(1);
  const [appointmentsPage, setAppointmentsPage] = useState(1);
  const [selectedProfessionalId, setSelectedProfessionalId] = useState<number | null>(null);
  const [selectedDocumentAppointmentId, setSelectedDocumentAppointmentId] = useState<number | null>(null);
  const [documentTemplateId, setDocumentTemplateId] = useState("");
  const [documentSharingPolicy, setDocumentSharingPolicy] = useState<GoogleDocsSharingPolicy>("private");
  const [adminConflictForm, setAdminConflictForm] = useState({ starts_at: "", ends_at: "" });

  const baseParams = useMemo(() => ({ search: search.trim() || undefined, page_size: PAGE_SIZE }), [search]);
  const usersQuery = useQuery({
    queryKey: ["admin-users", search, role, status, usersPage],
    queryFn: () =>
      fetchAdminUsers({
        ...baseParams,
        role: role || undefined,
        is_active: status === "" ? undefined : status === "active",
        page: usersPage,
      }),
  });
  const professionalsQuery = useQuery({
    queryKey: ["admin-professionals", search, status, professionalsPage],
    queryFn: () =>
      fetchAdminProfessionals({
        ...baseParams,
        is_active: status === "" ? undefined : status === "active",
        page: professionalsPage,
      }),
  });
  const appointmentsQuery = useQuery({
    queryKey: ["admin-appointments", search, appointmentStatus, appointmentsPage],
    queryFn: () =>
      fetchAdminAppointments({
        search: search.trim() || undefined,
        status: appointmentStatus || undefined,
        page: appointmentsPage,
        page_size: PAGE_SIZE,
      }),
  });
  const googleIntegrationsQuery = useQuery({
    queryKey: ["admin-google-integrations-for-docs"],
    queryFn: () => fetchAdminIntegrations({ provider: "google_meet", page_size: 10 }),
  });
  const googleIntegrationId = googleIntegrationsQuery.data?.items[0]?.id ?? null;
  const googleDocsTemplatesQuery = useQuery({
    queryKey: ["admin-google-docs-templates-for-appointments", googleIntegrationId],
    queryFn: () => fetchGoogleDocsTemplates(googleIntegrationId ?? 0),
    enabled: Boolean(googleIntegrationId),
  });
  const appointmentDocumentsQuery = useQuery({
    queryKey: ["admin-appointment-documents", selectedDocumentAppointmentId],
    queryFn: () => fetchAppointmentDocuments(selectedDocumentAppointmentId ?? 0),
    enabled: Boolean(selectedDocumentAppointmentId),
  });
  const effectiveProfessionalId = selectedProfessionalId ?? professionalsQuery.data?.items[0]?.id ?? null;
  const externalCalendarsQuery = useQuery({
    queryKey: ["admin-external-calendars", effectiveProfessionalId],
    queryFn: () => fetchAdminExternalCalendars(effectiveProfessionalId ?? 0),
    enabled: Boolean(effectiveProfessionalId),
  });
  const calendarSettingsQuery = useQuery({
    queryKey: ["admin-calendar-sync-settings", effectiveProfessionalId],
    queryFn: () => fetchAdminCalendarSyncSettings(effectiveProfessionalId ?? 0),
    enabled: Boolean(effectiveProfessionalId),
  });
  const adminAvailableGoogleQuery = useQuery({
    queryKey: ["admin-available-google-calendars", effectiveProfessionalId],
    queryFn: () => fetchAdminAvailableGoogleCalendars(effectiveProfessionalId ?? 0),
    enabled: false,
    retry: false,
  });
  const userMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => updateAdminUser(id, { is_active }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const professionalMutation = useMutation({
    mutationFn: ({ id, is_public, user_is_active }: { id: number; is_public?: boolean; user_is_active?: boolean }) =>
      updateAdminProfessional(id, { is_public, user_is_active }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-professionals"] }),
  });
  const meetingOperationMutation = useMutation({
    mutationFn: ({ id, operation }: { id: number; operation: "retry-create" | "retry-cancel" | "reconcile" }) => {
      if (operation === "retry-create") return retryAdminAppointmentMeetingCreate(id);
      if (operation === "retry-cancel") return retryAdminAppointmentMeetingCancel(id);
      return reconcileAdminAppointmentMeeting(id);
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-appointments"] }),
  });
  const refreshAppointmentDocuments = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-appointment-documents"] });
  };
  const generateDocumentMutation = useMutation({
    mutationFn: ({ appointmentId, templateId, sharingPolicy }: { appointmentId: number; templateId: number; sharingPolicy: GoogleDocsSharingPolicy }) =>
      generateAppointmentDocument(appointmentId, { template_id: templateId, sharing_policy: sharingPolicy, generation_request_id: `manual:${appointmentId}:${templateId}:${Date.now()}` }),
    onSuccess: refreshAppointmentDocuments,
  });
  const retryDocumentMutation = useMutation({
    mutationFn: ({ appointmentId, documentId }: { appointmentId: number; documentId: number }) => retryAppointmentDocument(appointmentId, documentId),
    onSuccess: refreshAppointmentDocuments,
  });
  const reconcileDocumentMutation = useMutation({
    mutationFn: ({ appointmentId, documentId }: { appointmentId: number; documentId: number }) => reconcileAppointmentDocument(appointmentId, documentId),
    onSuccess: refreshAppointmentDocuments,
  });
  const refreshAdminCalendars = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-external-calendars"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-calendar-sync-settings"] });
  };
  const createAdminCalendarMutation = useMutation({
    mutationFn: (professionalId: number) =>
      createAdminExternalCalendar(professionalId, {
        provider: "fake",
        external_calendar_id: `fake-admin-${professionalId}`,
        name: "Calendario fake admin",
        description: "Calendario fake creado desde backoffice.",
        timezone: "America/Santiago",
        read_enabled: true,
        write_enabled: false,
        conflict_check_enabled: true,
        is_primary: externalCalendarsQuery.data?.length === 0,
      }),
    onSuccess: refreshAdminCalendars,
  });
  const enableAdminCalendarMutation = useMutation({ mutationFn: ({ professionalId, calendarId }: { professionalId: number; calendarId: number }) => enableAdminExternalCalendar(professionalId, calendarId), onSuccess: refreshAdminCalendars });
  const disableAdminCalendarMutation = useMutation({ mutationFn: ({ professionalId, calendarId }: { professionalId: number; calendarId: number }) => disableAdminExternalCalendar(professionalId, calendarId), onSuccess: refreshAdminCalendars });
  const testAdminCalendarMutation = useMutation({ mutationFn: ({ professionalId, calendarId }: { professionalId: number; calendarId: number }) => testAdminExternalCalendar(professionalId, calendarId), onSuccess: refreshAdminCalendars });
  const updateAdminCalendarSettingsMutation = useMutation({
    mutationFn: ({ professionalId, policy }: { professionalId: number; policy: ExternalConflictFailurePolicy }) =>
      updateAdminCalendarSyncSettings(professionalId, { external_conflict_failure_policy: policy }),
    onSuccess: refreshAdminCalendars,
  });
  const registerAdminGoogleCalendarMutation = useMutation({
    mutationFn: ({ professionalId, calendar }: { professionalId: number; calendar: { external_calendar_id: string; name: string; timezone: string; is_primary: boolean } }) =>
      createAdminExternalCalendar(professionalId, {
        provider: "google_calendar",
        external_calendar_id: calendar.external_calendar_id,
        name: calendar.name,
        description: "Calendario Google registrado desde backoffice.",
        timezone: calendar.timezone,
        read_enabled: true,
        write_enabled: false,
        conflict_check_enabled: true,
        is_primary: calendar.is_primary,
      }),
    onSuccess: refreshAdminCalendars,
  });
  const adminConflictMutation = useMutation({
    mutationFn: (professionalId: number) =>
      checkAdminExternalCalendarConflicts(professionalId, {
        starts_at: new Date(adminConflictForm.starts_at).toISOString(),
        ends_at: new Date(adminConflictForm.ends_at).toISOString(),
      }),
  });

  const resetFilters = () => {
    setSearch("");
    setRole("");
    setStatus("");
    setAppointmentStatus("");
    setUsersPage(1);
    setProfessionalsPage(1);
    setAppointmentsPage(1);
  };

  const onSearchChange = (value: string) => {
    setSearch(value);
    setUsersPage(1);
    setProfessionalsPage(1);
    setAppointmentsPage(1);
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Backoffice" description="Gestion minima de usuarios, profesionales y reservas con los filtros disponibles." />

      <SectionCard title="Filtros" description="Estos filtros usan los parametros administrativos existentes.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div className="space-y-1 xl:col-span-2">
            <Label htmlFor="admin-search">Busqueda</Label>
            <Input id="admin-search" onChange={(event) => onSearchChange(event.target.value)} placeholder="Nombre o correo" value={search} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="admin-role">Rol usuario</Label>
            <Select
              id="admin-role"
              onChange={(event) => {
                setRole(event.target.value);
                setUsersPage(1);
              }}
              value={role}
            >
              <option value="">Todos los roles</option>
              {(["admin", "professional", "client"] as UserRole[]).map((item) => (
                <option key={item} value={item}>
                  {getRoleLabel(item)}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="admin-status">Estado usuario</Label>
            <Select
              id="admin-status"
              onChange={(event) => {
                setStatus(event.target.value);
                setUsersPage(1);
                setProfessionalsPage(1);
              }}
              value={status}
            >
              <option value="">Todos</option>
              <option value="active">Activos</option>
              <option value="inactive">Inactivos</option>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="appointment-status">Estado reserva</Label>
            <Select
              id="appointment-status"
              onChange={(event) => {
                setAppointmentStatus(event.target.value);
                setAppointmentsPage(1);
              }}
              value={appointmentStatus}
            >
              <option value="">Todos</option>
              {(["pending", "confirmed", "cancelled", "completed", "no_show"] as AppointmentStatus[]).map((item) => (
                <option key={item} value={item}>
                  {getAppointmentStatusLabel(item)}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <Button onClick={resetFilters} variant="secondary">
            Limpiar filtros
          </Button>
        </div>
      </SectionCard>

      <SectionCard title="Usuarios" description="Cuentas registradas y estado de acceso.">
        {usersQuery.isLoading ? <LoadingState label="Cargando usuarios" /> : null}
        {usersQuery.isError ? <ErrorState title="No pudimos cargar usuarios" message="Ajusta los filtros o intenta nuevamente." /> : null}
        {!usersQuery.isLoading && usersQuery.data?.items.length === 0 ? (
          <EmptyState title="No hay usuarios para estos filtros" description="Prueba limpiar los filtros o cambiar la busqueda." />
        ) : null}

        <div className="hidden overflow-hidden rounded-lg border border-slate-200 md:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Accion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {usersQuery.data?.items.map((user) => (
                <tr className="transition hover:bg-slate-50" key={user.id}>
                  <td className="px-4 py-4">
                    <p className="font-semibold text-ink-900">
                      {user.first_name} {user.last_name}
                    </p>
                    <p className="mt-1 break-all text-ink-500">{user.email}</p>
                  </td>
                  <td className="px-4 py-4">
                    <Badge label={getRoleLabel(user.role)} tone="neutral" />
                  </td>
                  <td className="px-4 py-4">
                    <AdminStatusPill active={user.is_active} />
                  </td>
                  <td className="px-4 py-4 text-right">
                    <Button
                      isLoading={userMutation.isPending}
                      onClick={() => userMutation.mutate({ id: user.id, is_active: !user.is_active })}
                      size="sm"
                      variant={user.is_active ? "secondary" : "primary"}
                    >
                      {user.is_active ? "Desactivar" : "Activar"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 md:hidden">
          {usersQuery.data?.items.map((user) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={user.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold text-ink-900">
                    {user.first_name} {user.last_name}
                  </h3>
                  <p className="mt-1 break-all text-sm text-ink-500">{user.email}</p>
                </div>
                <AdminStatusPill active={user.is_active} />
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                <Badge label={getRoleLabel(user.role)} tone="neutral" />
                <Button
                  isLoading={userMutation.isPending}
                  onClick={() => userMutation.mutate({ id: user.id, is_active: !user.is_active })}
                  size="sm"
                  variant="secondary"
                >
                  {user.is_active ? "Desactivar" : "Activar"}
                </Button>
              </div>
            </article>
          ))}
        </div>
        <AdminPagination meta={usersQuery.data?.meta} onPageChange={setUsersPage} />
      </SectionCard>

      <SectionCard title="Profesionales" description="Publicacion de perfiles y estado del usuario asociado.">
        {professionalsQuery.isLoading ? <LoadingState label="Cargando profesionales" /> : null}
        {professionalsQuery.isError ? <ErrorState title="No pudimos cargar profesionales" message="Ajusta los filtros o intenta nuevamente." /> : null}
        {!professionalsQuery.isLoading && professionalsQuery.data?.items.length === 0 ? (
          <EmptyState title="No hay profesionales para estos filtros" description="Prueba limpiar los filtros o cambiar la busqueda." />
        ) : null}

        <div className="hidden overflow-hidden rounded-lg border border-slate-200 md:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Profesional</th>
                <th className="px-4 py-3">Modalidad</th>
                <th className="px-4 py-3">Publicado</th>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {professionalsQuery.data?.items.map((professional) => (
                <tr className="transition hover:bg-slate-50" key={professional.id}>
                  <td className="px-4 py-4">
                    <p className="font-semibold text-ink-900">{professional.full_name}</p>
                    <p className="mt-1 break-all text-ink-500">{professional.title ?? professional.email}</p>
                  </td>
                  <td className="px-4 py-4">{getConsultationModeLabel(professional.consultation_mode)}</td>
                  <td className="px-4 py-4">
                    <AdminStatusPill active={professional.is_public} activeLabel="Publicado" inactiveLabel="Oculto" />
                  </td>
                  <td className="px-4 py-4">
                    <AdminStatusPill active={professional.user_is_active} />
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex justify-end gap-2">
                      <Button
                        isLoading={professionalMutation.isPending}
                        onClick={() => professionalMutation.mutate({ id: professional.id, is_public: !professional.is_public })}
                        size="sm"
                        variant="secondary"
                      >
                        {professional.is_public ? "Ocultar" : "Publicar"}
                      </Button>
                      <Button
                        isLoading={professionalMutation.isPending}
                        onClick={() => professionalMutation.mutate({ id: professional.id, user_is_active: !professional.user_is_active })}
                        size="sm"
                        variant="secondary"
                      >
                        {professional.user_is_active ? "Desactivar" : "Activar"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 md:hidden">
          {professionalsQuery.data?.items.map((professional) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={professional.id}>
              <h3 className="font-semibold text-ink-900">{professional.full_name}</h3>
              <p className="mt-1 break-all text-sm text-ink-500">{professional.title ?? professional.email}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge label={getConsultationModeLabel(professional.consultation_mode)} tone="info" />
                <AdminStatusPill active={professional.is_public} activeLabel="Publicado" inactiveLabel="Oculto" />
                <AdminStatusPill active={professional.user_is_active} />
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <Button
                  isLoading={professionalMutation.isPending}
                  onClick={() => professionalMutation.mutate({ id: professional.id, is_public: !professional.is_public })}
                  size="sm"
                  variant="secondary"
                >
                  {professional.is_public ? "Ocultar" : "Publicar"}
                </Button>
                <Button
                  isLoading={professionalMutation.isPending}
                  onClick={() => professionalMutation.mutate({ id: professional.id, user_is_active: !professional.user_is_active })}
                  size="sm"
                  variant="secondary"
                >
                  {professional.user_is_active ? "Desactivar" : "Activar"}
                </Button>
              </div>
            </article>
          ))}
        </div>
        <AdminPagination meta={professionalsQuery.data?.meta} onPageChange={setProfessionalsPage} />
      </SectionCard>

      <SectionCard title="Calendarios externos" description="Administracion acotada de calendarios externos por profesional.">
        <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <Label htmlFor="admin-calendar-professional">Profesional</Label>
            <Select id="admin-calendar-professional" value={effectiveProfessionalId ?? ""} onChange={(event) => setSelectedProfessionalId(Number(event.target.value))}>
              {professionalsQuery.data?.items.map((professional) => (
                <option key={professional.id} value={professional.id}>{professional.full_name}</option>
              ))}
            </Select>
          </div>
          <Button disabled={!effectiveProfessionalId} isLoading={createAdminCalendarMutation.isPending} onClick={() => effectiveProfessionalId && createAdminCalendarMutation.mutate(effectiveProfessionalId)}>Registrar fake</Button>
        </div>
        <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-ink-600">Los calendarios habilitados para lectura pueden bloquear disponibilidad y reservas cuando la politica del profesional lo permite. No se exponen detalles privados de eventos externos.</p>
        {externalCalendarsQuery.isLoading ? <LoadingState label="Cargando calendarios externos" /> : null}
        {externalCalendarsQuery.isError ? <ErrorState title="No pudimos cargar calendarios externos" /> : null}
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {externalCalendarsQuery.data?.map((calendar) => (
            <AdminExternalCalendarCard
              busy={enableAdminCalendarMutation.isPending || disableAdminCalendarMutation.isPending || testAdminCalendarMutation.isPending}
              calendar={calendar}
              key={calendar.id}
              onDisable={() => effectiveProfessionalId && disableAdminCalendarMutation.mutate({ professionalId: effectiveProfessionalId, calendarId: calendar.id })}
              onEnable={() => effectiveProfessionalId && enableAdminCalendarMutation.mutate({ professionalId: effectiveProfessionalId, calendarId: calendar.id })}
              onTest={() => effectiveProfessionalId && testAdminCalendarMutation.mutate({ professionalId: effectiveProfessionalId, calendarId: calendar.id })}
            />
          ))}
          {!externalCalendarsQuery.isLoading && externalCalendarsQuery.data?.length === 0 ? <EmptyState title="Sin calendarios externos" description="Registra un calendario fake para validar el flujo administrativo." /> : null}
        </div>
        {calendarSettingsQuery.data ? (
          <div className="mt-4 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[1fr_1fr] md:items-end">
            <p className="text-sm text-ink-600">Politica actual: {calendarSettingsQuery.data.conflict_policy}. Lookahead: {calendarSettingsQuery.data.lookahead_days} dias.</p>
            <div>
              <Label htmlFor="admin-failure-policy">Si Google no responde</Label>
              <Select
                id="admin-failure-policy"
                value={calendarSettingsQuery.data.external_conflict_failure_policy}
                onChange={(event) =>
                  effectiveProfessionalId &&
                  updateAdminCalendarSettingsMutation.mutate({ professionalId: effectiveProfessionalId, policy: event.target.value as ExternalConflictFailurePolicy })
                }
              >
                <option value="fail_closed">Bloquear nuevas reservas por seguridad</option>
                <option value="fail_open">Continuar usando solo RealMeet</option>
              </Select>
              <p className="mt-1 text-xs text-ink-500">Bloquear es mas seguro; continuar reduce interrupciones si el proveedor externo falla.</p>
            </div>
          </div>
        ) : null}
        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 className="font-semibold text-ink-900">Google disponible</h3>
              <p className="mt-1 text-sm text-ink-500">Consulta calendarios de la cuenta Google conectada. No se exponen tokens.</p>
            </div>
            <Button disabled={!effectiveProfessionalId} isLoading={adminAvailableGoogleQuery.isFetching} onClick={() => void adminAvailableGoogleQuery.refetch()} size="sm" variant="secondary">Buscar Google</Button>
          </div>
          {adminAvailableGoogleQuery.isError ? <ErrorState title="Google no conectado" /> : null}
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {adminAvailableGoogleQuery.data?.map((calendar) => (
              <article className="rounded-md border border-slate-200 bg-slate-50 p-3" key={calendar.external_calendar_id}>
                <p className="font-semibold text-ink-900">{calendar.name}</p>
                <p className="break-all text-sm text-ink-500">{calendar.external_calendar_id}</p>
                <Button className="mt-3" disabled={!effectiveProfessionalId} isLoading={registerAdminGoogleCalendarMutation.isPending} onClick={() => effectiveProfessionalId && registerAdminGoogleCalendarMutation.mutate({ professionalId: effectiveProfessionalId, calendar })} size="sm" variant="secondary">Registrar</Button>
              </article>
            ))}
          </div>
        </div>
        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="font-semibold text-ink-900">Probar conflicto externo</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
            <div>
              <Label htmlFor="admin-conflict-start">Inicio</Label>
              <Input id="admin-conflict-start" type="datetime-local" value={adminConflictForm.starts_at} onChange={(event) => setAdminConflictForm((current) => ({ ...current, starts_at: event.target.value }))} />
            </div>
            <div>
              <Label htmlFor="admin-conflict-end">Termino</Label>
              <Input id="admin-conflict-end" type="datetime-local" value={adminConflictForm.ends_at} onChange={(event) => setAdminConflictForm((current) => ({ ...current, ends_at: event.target.value }))} />
            </div>
            <Button disabled={!effectiveProfessionalId || !adminConflictForm.starts_at || !adminConflictForm.ends_at} isLoading={adminConflictMutation.isPending} onClick={() => effectiveProfessionalId && adminConflictMutation.mutate(effectiveProfessionalId)} size="sm" variant="secondary">Probar</Button>
          </div>
          {adminConflictMutation.data ? <p className="mt-3 text-sm text-ink-700">{adminConflictMutation.data.has_conflict ? "Conflicto detectado" : "Sin conflicto"} · {adminConflictMutation.data.status}</p> : null}
        </div>
      </SectionCard>

      <SectionCard title="Reservas" description="Reservas recientes y filtros por estado real.">
        {appointmentsQuery.isLoading ? <LoadingState label="Cargando reservas" /> : null}
        {appointmentsQuery.isError ? <ErrorState title="No pudimos cargar reservas" message="Ajusta los filtros o intenta nuevamente." /> : null}
        {!appointmentsQuery.isLoading && appointmentsQuery.data?.items.length === 0 ? (
          <EmptyState title="No hay reservas para estos filtros" description="Prueba limpiar los filtros o cambiar el estado." />
        ) : null}

        <div className="hidden overflow-hidden rounded-lg border border-slate-200 lg:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Modalidad</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Reunion</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Profesional</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {appointmentsQuery.data?.items.map((appointment) => (
                <tr className="transition hover:bg-slate-50" key={appointment.id}>
                  <td className="px-4 py-4 font-semibold text-ink-900">{formatDateTime(appointment.start_datetime)}</td>
                  <td className="px-4 py-4">{getConsultationModeLabel(appointment.consultation_mode)}</td>
                  <td className="px-4 py-4">
                    <StatusBadge status={appointment.status} />
                  </td>
                  <td className="px-4 py-4 text-ink-500">{appointment.meeting?.message ?? "Sin reunion"}</td>
                  <td className="px-4 py-4 text-ink-500">Cliente registrado</td>
                  <td className="px-4 py-4 text-ink-500">Profesional registrado</td>
                  <td className="px-4 py-4">
                    <MeetingAdminActions appointment={appointment} isLoading={meetingOperationMutation.isPending && meetingOperationMutation.variables?.id === appointment.id} onRun={(operation) => meetingOperationMutation.mutate({ id: appointment.id, operation })} />
                    <div className="mt-2 text-right"><Button onClick={() => setSelectedDocumentAppointmentId(appointment.id)} size="sm" variant="secondary">Documentos</Button></div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 lg:hidden">
          {appointmentsQuery.data?.items.map((appointment) => (
            <div className="space-y-2" key={appointment.id}>
              <AdminAppointmentCard appointment={appointment} />
              <MeetingAdminActions appointment={appointment} isLoading={meetingOperationMutation.isPending && meetingOperationMutation.variables?.id === appointment.id} onRun={(operation) => meetingOperationMutation.mutate({ id: appointment.id, operation })} />
              <Button onClick={() => setSelectedDocumentAppointmentId(appointment.id)} size="sm" variant="secondary">Documentos</Button>
            </div>
          ))}
        </div>
        <AdminPagination meta={appointmentsQuery.data?.meta} onPageChange={setAppointmentsPage} />
        {selectedDocumentAppointmentId ? (
          <AppointmentDocumentsPanel
            appointmentId={selectedDocumentAppointmentId}
            busy={generateDocumentMutation.isPending || retryDocumentMutation.isPending || reconcileDocumentMutation.isPending}
            documents={appointmentDocumentsQuery.data ?? []}
            onGenerate={() => documentTemplateId && generateDocumentMutation.mutate({ appointmentId: selectedDocumentAppointmentId, templateId: Number(documentTemplateId), sharingPolicy: documentSharingPolicy })}
            onReconcile={(documentId) => reconcileDocumentMutation.mutate({ appointmentId: selectedDocumentAppointmentId, documentId })}
            onRetry={(documentId) => retryDocumentMutation.mutate({ appointmentId: selectedDocumentAppointmentId, documentId })}
            onSelectTemplate={setDocumentTemplateId}
            onSharingPolicyChange={setDocumentSharingPolicy}
            selectedTemplateId={documentTemplateId}
            sharingPolicy={documentSharingPolicy}
            templates={googleDocsTemplatesQuery.data ?? []}
          />
        ) : null}
      </SectionCard>
    </div>
  );
}

function AdminExternalCalendarCard({ calendar, busy, onDisable, onEnable, onTest }: { calendar: ExternalCalendar; busy: boolean; onDisable: () => void; onEnable: () => void; onTest: () => void }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-ink-900">{calendar.name}</p>
          <p className="mt-1 text-sm text-ink-500">{calendar.provider} · {calendar.external_calendar_id}</p>
        </div>
        <Badge label={calendar.enabled ? "Habilitado" : "Deshabilitado"} tone={calendar.enabled ? "success" : "neutral"} />
      </div>
      <p className="mt-3 text-sm text-ink-600">Estado: {calendar.sync_status}. Timezone: {calendar.timezone}</p>
      {calendar.last_sync_error_code ? <p className="mt-2 text-sm text-danger-700">Error resumido: {calendar.last_sync_error_code}</p> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        {calendar.enabled ? <Button isLoading={busy} onClick={onDisable} size="sm" variant="secondary">Deshabilitar</Button> : <Button isLoading={busy} onClick={onEnable} size="sm">Habilitar</Button>}
        <Button isLoading={busy} onClick={onTest} size="sm" variant="secondary">Probar fake</Button>
      </div>
    </article>
  );
}

function AppointmentDocumentsPanel({
  appointmentId,
  templates,
  documents,
  selectedTemplateId,
  sharingPolicy,
  busy,
  onSelectTemplate,
  onSharingPolicyChange,
  onGenerate,
  onRetry,
  onReconcile,
}: {
  appointmentId: number;
  templates: Array<{ id: number; name: string; enabled: boolean; document_type: string }>;
  documents: AppointmentGeneratedDocument[];
  selectedTemplateId: string;
  sharingPolicy: GoogleDocsSharingPolicy;
  busy: boolean;
  onSelectTemplate: (value: string) => void;
  onSharingPolicyChange: (value: GoogleDocsSharingPolicy) => void;
  onGenerate: () => void;
  onRetry: (documentId: number) => void;
  onReconcile: (documentId: number) => void;
}) {
  return (
    <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-semibold text-ink-900">Documentos Google Docs</h3>
          <p className="mt-1 text-sm text-ink-500">Reserva #{appointmentId}. Generacion manual desde plantillas operativas.</p>
        </div>
        <Badge label={`${documents.length} documento(s)`} tone="info" />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_220px_auto] sm:items-end">
        <div>
          <Label htmlFor="appointment-doc-template">Plantilla</Label>
          <Select id="appointment-doc-template" value={selectedTemplateId} onChange={(event) => onSelectTemplate(event.target.value)}>
            <option value="">Seleccionar</option>
            {templates.filter((template) => template.enabled).map((template) => <option key={template.id} value={template.id}>{template.name} · {template.document_type}</option>)}
          </Select>
        </div>
        <div>
          <Label htmlFor="appointment-doc-sharing">Comparticion</Label>
          <Select id="appointment-doc-sharing" value={sharingPolicy} onChange={(event) => onSharingPolicyChange(event.target.value as GoogleDocsSharingPolicy)}>
            <option value="private">Privado</option>
            <option value="professional_only">Solo profesional</option>
            <option value="professional_and_client">Profesional y cliente</option>
          </Select>
        </div>
        <Button disabled={!selectedTemplateId} isLoading={busy} onClick={onGenerate}>Generar</Button>
      </div>
      <div className="mt-4 grid gap-3">
        {documents.length === 0 ? <EmptyState title="Sin documentos generados" /> : null}
        {documents.map((document) => (
          <article className="rounded-md border border-slate-200 bg-slate-50 p-3" key={document.id}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-semibold text-ink-900">{document.document_name}</p>
                <p className="text-sm text-ink-500">{document.status} · {document.sharing_status} · {formatDateTime(document.created_at)}</p>
                {document.last_error_message ? <p className="mt-1 text-sm text-danger-700">{document.last_error_message}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                {document.document_url ? <Button onClick={() => window.open(document.document_url ?? "", "_blank", "noopener,noreferrer")} size="sm" variant="secondary">Abrir</Button> : null}
                {["failed", "partially_generated", "reconcile_required"].includes(document.status) ? <Button isLoading={busy} onClick={() => onRetry(document.id)} size="sm" variant="secondary">Reintentar</Button> : null}
                <Button isLoading={busy} onClick={() => onReconcile(document.id)} size="sm" variant="secondary">Reconciliar</Button>
              </div>
            </div>
          </article>
        ))}
      </div>
      <p className="mt-3 text-xs text-ink-500">No se muestra contenido del documento ni se gestionan permisos publicos o writer.</p>
    </div>
  );
}

function MeetingAdminActions({
  appointment,
  isLoading,
  onRun,
}: {
  appointment: Appointment;
  isLoading: boolean;
  onRun: (operation: "retry-create" | "retry-cancel" | "reconcile") => void;
}) {
  const meeting = appointment.meeting;
  const canRetryCreate = appointment.status !== "cancelled" && (!meeting || meeting.status === "failed" || meeting.status === "pending");
  const canRetryCancel = appointment.status === "cancelled" && meeting && meeting.status !== "cancelled" && meeting.status !== "not_required";
  const canReconcile = Boolean(meeting);

  return (
    <div className="flex flex-wrap justify-end gap-2">
      {meeting?.join_url ? (
        <Button onClick={() => window.open(meeting.join_url ?? "", "_blank", "noopener,noreferrer")} size="sm" variant="secondary">
          Abrir
        </Button>
      ) : null}
      <Button disabled={!canRetryCreate || isLoading} isLoading={isLoading} onClick={() => onRun("retry-create")} size="sm" variant="secondary">
        Reintentar enlace
      </Button>
      <Button disabled={!canRetryCancel || isLoading} isLoading={isLoading} onClick={() => onRun("retry-cancel")} size="sm" variant="secondary">
        Reintentar cancelacion
      </Button>
      <Button disabled={!canReconcile || isLoading} isLoading={isLoading} onClick={() => onRun("reconcile")} size="sm" variant="secondary">
        Reconciliar
      </Button>
    </div>
  );
}
