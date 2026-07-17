import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { approveClientPaymentCheckout, fetchClientPaymentCheckout, fetchClientPaymentOrders, fetchProfessionalPaymentOrders, rejectClientPaymentCheckout } from "../api/queries";
import { Badge, Button, EmptyState, ErrorState, LoadingState, PageHeader, SectionCard } from "../components/ui";
import { useAuthStore } from "../store/auth";
import type { PaymentOrder } from "../types";
import { formatDateTime } from "../utils/dates";
import { getPaymentOrderStatusLabel } from "../utils/labels";

export function PaymentsPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const isProfessional = user?.role === "professional";
  const [selectedCheckoutId, setSelectedCheckoutId] = useState<number | null>(null);
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
      <PageHeader title={isProfessional ? "Pagos de reservas" : "Mis pagos"} description="Consulta de ordenes de cobro vinculadas a reservas y checkout fake de prueba." />
      <SectionCard title="Ordenes" description={isProfessional ? "Solo lectura de pagos asociados a tus reservas." : "Estado de tus ordenes de cobro."}>
        <div className="grid gap-3">
          {orders.map((order) => <PaymentCard key={order.id} order={order} onCheckout={!isProfessional && order.status !== "approved" ? () => setSelectedCheckoutId(order.id) : undefined} />)}
          {orders.length === 0 ? <EmptyState title="Sin pagos registrados" description="Cuando exista una orden de cobro asociada a una reserva, aparecera aqui." /> : null}
        </div>
      </SectionCard>
      {selectedCheckoutId ? (
        <CheckoutPanel
          onClose={() => setSelectedCheckoutId(null)}
          onDone={() => {
            setSelectedCheckoutId(null);
            void queryClient.invalidateQueries({ queryKey: ["client-payment-orders"] });
            void queryClient.invalidateQueries({ queryKey: ["my-appointments"] });
          }}
          paymentOrderId={selectedCheckoutId}
        />
      ) : null}
    </div>
  );
}

function PaymentCard({ order, onCheckout }: { order: PaymentOrder; onCheckout?: () => void }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-ink-900">Orden #{order.id}</h3>
            <Badge label={getPaymentOrderStatusLabel(order.status)} tone={order.status === "approved" ? "success" : order.status === "failed" || order.status === "rejected" ? "danger" : "neutral"} />
          </div>
          <p className="mt-1 text-sm text-ink-600">{order.description ?? "Orden de pago"} - CLP {Number(order.amount).toLocaleString("es-CL")}</p>
          <p className="mt-1 text-xs text-ink-500">Reserva {order.appointment_id ?? "sin vinculo"} - Creada {formatDateTime(order.created_at)}</p>
        </div>
        <div className="text-sm text-ink-600">
          {order.expires_at ? <p>Vence {formatDateTime(order.expires_at)}</p> : null}
          {order.paid_at ? <p>Pagada {formatDateTime(order.paid_at)}</p> : null}
          {order.cancelled_at ? <p>Cancelada {formatDateTime(order.cancelled_at)}</p> : null}
          {onCheckout ? <Button className="mt-3" onClick={onCheckout} size="sm">Continuar al pago</Button> : null}
        </div>
      </div>
    </article>
  );
}

function CheckoutPanel({ paymentOrderId, onClose, onDone }: { paymentOrderId: number; onClose: () => void; onDone: () => void }) {
  const checkoutQuery = useQuery({ queryKey: ["client-payment-checkout", paymentOrderId], queryFn: () => fetchClientPaymentCheckout(paymentOrderId) });
  const approveMutation = useMutation({ mutationFn: () => approveClientPaymentCheckout(paymentOrderId), onSuccess: onDone });
  const rejectMutation = useMutation({ mutationFn: () => rejectClientPaymentCheckout(paymentOrderId), onSuccess: onDone });
  const checkout = checkoutQuery.data;
  return (
    <SectionCard title="Checkout fake" description="Entorno de prueba - no se realizara un cobro real.">
      {checkoutQuery.isLoading ? <LoadingState label="Cargando checkout" /> : null}
      {checkoutQuery.isError ? <ErrorState title="Checkout no disponible" /> : null}
      {checkout ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="font-semibold text-ink-900">{checkout.description ?? `Orden #${checkout.id}`}</p>
            <p className="mt-1 text-sm text-ink-600">CLP {Number(checkout.amount).toLocaleString("es-CL")} - {getPaymentOrderStatusLabel(checkout.status)}</p>
            {checkout.expires_at ? <p className="mt-1 text-sm text-ink-500">Vence {formatDateTime(checkout.expires_at)}</p> : null}
            <p className="mt-3 text-sm text-ink-600">{checkout.message}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button disabled={!checkout.checkout_available} isLoading={approveMutation.isPending} onClick={() => approveMutation.mutate()}>Simular pago aprobado</Button>
            <Button disabled={!checkout.checkout_available} isLoading={rejectMutation.isPending} onClick={() => rejectMutation.mutate()} variant="secondary">Simular pago rechazado</Button>
            <Button onClick={onClose} variant="secondary">Cerrar</Button>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
