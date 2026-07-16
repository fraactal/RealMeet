import { useQuery } from "@tanstack/react-query";

import { fetchClientPaymentOrders, fetchProfessionalPaymentOrders } from "../api/queries";
import { Badge, EmptyState, ErrorState, LoadingState, PageHeader, SectionCard } from "../components/ui";
import { useAuthStore } from "../store/auth";
import type { PaymentOrder } from "../types";
import { formatDateTime } from "../utils/dates";
import { getPaymentOrderStatusLabel } from "../utils/labels";

export function PaymentsPage() {
  const user = useAuthStore((state) => state.user);
  const isProfessional = user?.role === "professional";
  const query = useQuery({
    queryKey: [isProfessional ? "professional-payment-orders" : "client-payment-orders"],
    queryFn: isProfessional ? fetchProfessionalPaymentOrders : fetchClientPaymentOrders,
  });

  if (query.isLoading) {
    return <LoadingState label="Cargando pagos" />;
  }
  if (query.isError) {
    return <ErrorState title="No pudimos cargar pagos" />;
  }

  const orders = query.data ?? [];
  return (
    <div className="space-y-6">
      <PageHeader title={isProfessional ? "Pagos de reservas" : "Mis pagos"} description="Consulta de ordenes de cobro vinculadas a reservas. En 17.1 no hay checkout publico." />
      <SectionCard title="Ordenes" description={isProfessional ? "Solo lectura de pagos asociados a tus reservas." : "Estado de tus ordenes de cobro."}>
        <div className="grid gap-3">
          {orders.map((order) => <PaymentCard key={order.id} order={order} />)}
          {orders.length === 0 ? <EmptyState title="Sin pagos registrados" description="Cuando exista una orden de cobro asociada a una reserva, aparecera aqui." /> : null}
        </div>
      </SectionCard>
    </div>
  );
}

function PaymentCard({ order }: { order: PaymentOrder }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-ink-900">Orden #{order.id}</h3>
            <Badge label={getPaymentOrderStatusLabel(order.status)} tone={order.status === "approved" ? "success" : order.status === "failed" || order.status === "rejected" ? "danger" : "neutral"} />
          </div>
          <p className="mt-1 text-sm text-ink-600">{order.description ?? "Orden de pago"} · CLP {Number(order.amount).toLocaleString("es-CL")}</p>
          <p className="mt-1 text-xs text-ink-500">Reserva {order.appointment_id ?? "sin vinculo"} · Creada {formatDateTime(order.created_at)}</p>
        </div>
        <div className="text-sm text-ink-600">
          {order.expires_at ? <p>Vence {formatDateTime(order.expires_at)}</p> : null}
          {order.paid_at ? <p>Pagada {formatDateTime(order.paid_at)}</p> : null}
          {order.cancelled_at ? <p>Cancelada {formatDateTime(order.cancelled_at)}</p> : null}
        </div>
      </div>
    </article>
  );
}
