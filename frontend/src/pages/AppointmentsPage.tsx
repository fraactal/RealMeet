import { useQuery } from "@tanstack/react-query";

import { fetchMyAppointments } from "../api/queries";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";

export function AppointmentsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["my-appointments"], queryFn: fetchMyAppointments });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Mis reservas</h1>
        <p className="text-slate-600">Historial y agenda del usuario autenticado.</p>
      </div>
      <Card>
        {isLoading ? <p className="text-slate-500">Cargando reservas...</p> : null}
        {isError ? <p className="text-red-600">No fue posible obtener las reservas.</p> : null}
        <div className="space-y-4">
          {data?.map((appointment) => (
            <div key={appointment.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-semibold text-ink">{new Date(appointment.start_datetime).toLocaleString()}</p>
                <p className="text-sm text-slate-500">Reserva #{appointment.id}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge label={appointment.status} />
                {appointment.meeting_url ? (
                  <a className="text-sm font-medium text-brand" href={appointment.meeting_url} target="_blank" rel="noreferrer">
                    Abrir reunion
                  </a>
                ) : null}
              </div>
            </div>
          ))}
          {!isLoading && data?.length === 0 ? <p className="text-slate-500">Todavia no hay reservas para este usuario.</p> : null}
        </div>
      </Card>
    </div>
  );
}
