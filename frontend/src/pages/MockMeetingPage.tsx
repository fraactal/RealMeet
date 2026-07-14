import { Link, useParams } from "react-router-dom";

import { Card } from "../components/ui/Card";

export function MockMeetingPage() {
  const { meetingId } = useParams();

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <Card>
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-ink">Reunion de demostracion</h1>
            <p className="text-slate-600">Este enlace pertenece al proveedor mock de RealMeet.</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-500">ID de reunion</p>
            <p className="mt-1 break-all font-mono text-sm text-ink">{meetingId}</p>
          </div>
          <p className="text-sm leading-6 text-slate-600">
            No hay videollamada real, audio, chat ni WebRTC en este modulo. Las integraciones reales se incorporaran en una fase posterior.
          </p>
          <Link className="inline-flex rounded-xl bg-ink px-4 py-2 text-sm font-semibold text-white" to="/dashboard/appointments">
            Volver a reservas
          </Link>
        </div>
      </Card>
    </div>
  );
}
