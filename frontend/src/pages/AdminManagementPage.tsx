import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAdminAppointments,
  fetchAdminProfessionals,
  fetchAdminUsers,
  updateAdminProfessional,
  updateAdminUser,
} from "../api/queries";
import { AdminAppointmentCard } from "../components/admin/AdminAppointmentCard";
import { AdminPagination } from "../components/admin/AdminPagination";
import { AdminStatusPill } from "../components/admin/AdminStatusPill";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select, StatusBadge } from "../components/ui";
import type { AppointmentStatus, UserRole } from "../types";
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
  const userMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => updateAdminUser(id, { is_active }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const professionalMutation = useMutation({
    mutationFn: ({ id, is_public, user_is_active }: { id: number; is_public?: boolean; user_is_active?: boolean }) =>
      updateAdminProfessional(id, { is_public, user_is_active }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-professionals"] }),
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
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Profesional</th>
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
                  <td className="px-4 py-4 text-ink-500">Cliente registrado</td>
                  <td className="px-4 py-4 text-ink-500">Profesional registrado</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 lg:hidden">
          {appointmentsQuery.data?.items.map((appointment) => (
            <AdminAppointmentCard appointment={appointment} key={appointment.id} />
          ))}
        </div>
        <AdminPagination meta={appointmentsQuery.data?.meta} onPageChange={setAppointmentsPage} />
      </SectionCard>
    </div>
  );
}
