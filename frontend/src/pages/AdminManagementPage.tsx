import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchAdminAppointments,
  fetchAdminProfessionals,
  fetchAdminUsers,
  updateAdminProfessional,
  updateAdminUser,
} from "../api/queries";
import { Card } from "../components/ui/Card";

export function AdminManagementPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const params = useMemo(() => ({ search: search || undefined, page_size: 10 }), [search]);
  const usersQuery = useQuery({
    queryKey: ["admin-users", search, role, status],
    queryFn: () =>
      fetchAdminUsers({
        ...params,
        role: role || undefined,
        is_active: status === "" ? undefined : status === "active",
      }),
  });
  const professionalsQuery = useQuery({
    queryKey: ["admin-professionals", search, status],
    queryFn: () =>
      fetchAdminProfessionals({
        ...params,
        is_active: status === "" ? undefined : status === "active",
      }),
  });
  const appointmentsQuery = useQuery({
    queryKey: ["admin-appointments", search],
    queryFn: () => fetchAdminAppointments({ search: search || undefined, page_size: 10 }),
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Backoffice admin</h1>
        <p className="text-slate-600">Gestion minima de usuarios, profesionales y reservas.</p>
      </div>

      <Card>
        <div className="grid gap-3 md:grid-cols-3">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar nombre o correo"
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <select value={role} onChange={(event) => setRole(event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">Todos los roles</option>
            <option value="admin">Admin</option>
            <option value="professional">Professional</option>
            <option value="client">Client</option>
          </select>
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">Todos los estados</option>
            <option value="active">Activos</option>
            <option value="inactive">Inactivos</option>
          </select>
        </div>
      </Card>

      <Card title="Usuarios">
        {usersQuery.isLoading ? <p className="text-sm text-slate-500">Cargando usuarios...</p> : null}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2">Usuario</th>
                <th className="py-2">Rol</th>
                <th className="py-2">Estado</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {usersQuery.data?.items.map((user) => (
                <tr key={user.id} className="border-t border-slate-100">
                  <td className="py-3">
                    <p className="font-medium text-slate-700">{user.first_name} {user.last_name}</p>
                    <p className="text-slate-500">{user.email}</p>
                  </td>
                  <td className="py-3 text-slate-500">{user.role}</td>
                  <td className="py-3 text-slate-500">{user.is_active ? "Activo" : "Inactivo"}</td>
                  <td className="py-3 text-right">
                    <button
                      className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                      onClick={() => userMutation.mutate({ id: user.id, is_active: !user.is_active })}
                    >
                      {user.is_active ? "Desactivar" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Profesionales">
        {professionalsQuery.isLoading ? <p className="text-sm text-slate-500">Cargando profesionales...</p> : null}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2">Profesional</th>
                <th className="py-2">Publicado</th>
                <th className="py-2">Usuario</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {professionalsQuery.data?.items.map((professional) => (
                <tr key={professional.id} className="border-t border-slate-100">
                  <td className="py-3">
                    <p className="font-medium text-slate-700">{professional.full_name}</p>
                    <p className="text-slate-500">{professional.title ?? professional.email}</p>
                  </td>
                  <td className="py-3 text-slate-500">{professional.is_public ? "Si" : "No"}</td>
                  <td className="py-3 text-slate-500">{professional.user_is_active ? "Activo" : "Inactivo"}</td>
                  <td className="py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                        onClick={() => professionalMutation.mutate({ id: professional.id, is_public: !professional.is_public })}
                      >
                        {professional.is_public ? "Ocultar" : "Publicar"}
                      </button>
                      <button
                        className="rounded-xl border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700"
                        onClick={() => professionalMutation.mutate({ id: professional.id, user_is_active: !professional.user_is_active })}
                      >
                        {professional.user_is_active ? "Desactivar" : "Activar"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Reservas recientes">
        {appointmentsQuery.isLoading ? <p className="text-sm text-slate-500">Cargando reservas...</p> : null}
        <div className="space-y-3 text-sm">
          {appointmentsQuery.data?.items.map((appointment) => (
            <div key={appointment.id} className="rounded-xl border border-slate-100 p-3">
              <p className="font-medium text-slate-700">Reserva #{appointment.id}</p>
              <p className="text-slate-500">
                {new Date(appointment.start_datetime).toLocaleString()} - {appointment.status}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
