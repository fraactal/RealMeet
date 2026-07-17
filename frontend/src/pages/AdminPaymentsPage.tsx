import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelAdminPaymentOrder,
  createAdminPaymentOrder,
  fakeApprovePaymentOrder,
  fakeExpirePaymentOrder,
  fakeFailPaymentOrder,
  fakeRejectPaymentOrder,
  fetchAdminPaymentOrderHistory,
  fetchAdminPaymentOrders,
  healthCheckPaymentProvider,
  reconcileAdminPaymentOrder,
  submitAdminPaymentOrder,
} from "../api/queries";
import { AdminPagination } from "../components/admin/AdminPagination";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type { AdminPaymentOrder, PaymentOrderCreatePayload, PaymentOrderStatus, PaymentProvider } from "../types";
import { formatDateTime } from "../utils/dates";
import { getPaymentOrderStatusLabel } from "../utils/labels";

const PAGE_SIZE = 10;
const paymentStatuses: PaymentOrderStatus[] = ["draft", "pending", "requires_action", "approved", "rejected", "cancelled", "expired", "failed", "refunded"];

export function AdminPaymentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<"" | PaymentOrderStatus>("");
  const [provider, setProvider] = useState<"" | PaymentProvider>("fake");
  const [search, setSearch] = useState("");
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [form, setForm] = useState({ appointment_id: "", client_id: "", professional_id: "", amount: "", description: "" });

  const params = useMemo(
    () => ({ page, page_size: PAGE_SIZE, status: status || undefined, provider: provider || undefined, search: search.trim() || undefined }),
    [page, provider, search, status],
  );
  const ordersQuery = useQuery({ queryKey: ["admin-payment-orders", params], queryFn: () => fetchAdminPaymentOrders(params) });
  const historyQuery = useQuery({
    queryKey: ["admin-payment-order-history", selectedOrderId],
    queryFn: () => fetchAdminPaymentOrderHistory(selectedOrderId ?? 0),
    enabled: Boolean(selectedOrderId),
  });
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-payment-orders"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-payment-order-history"] });
  };
  const createMutation = useMutation({
    mutationFn: () => {
      const payload: PaymentOrderCreatePayload = {
        appointment_id: form.appointment_id ? Number(form.appointment_id) : null,
        client_id: form.client_id ? Number(form.client_id) : null,
        professional_id: form.professional_id ? Number(form.professional_id) : null,
        provider: "fake",
        currency: "CLP",
        amount: form.amount || null,
        description: form.description || null,
      };
      return createAdminPaymentOrder(payload);
    },
    onSuccess: (order) => {
      setSelectedOrderId(order.id);
      refresh();
    },
  });
  const operationMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "submit" | "approve" | "reject" | "cancel" | "expire" | "fail" | "reconcile" }) => {
      if (action === "submit") return submitAdminPaymentOrder(id);
      if (action === "approve") return fakeApprovePaymentOrder(id);
      if (action === "reject") return fakeRejectPaymentOrder(id);
      if (action === "cancel") return cancelAdminPaymentOrder(id);
      if (action === "expire") return fakeExpirePaymentOrder(id);
      if (action === "reconcile") return reconcileAdminPaymentOrder(id).then((result) => result.payment_order);
      return fakeFailPaymentOrder(id);
    },
    onSuccess: refresh,
  });
  const healthMutation = useMutation({ mutationFn: () => healthCheckPaymentProvider("fake") });

  return (
    <div className="space-y-6">
      <PageHeader title="Pagos" description="Ordenes de cobro internas con provider fake para validacion operativa." />

      <SectionCard title="Crear orden fake" description="Puedes asociar una reserva y derivar el precio del profesional, o indicar un monto manual para pruebas administrativas.">
        <div className="grid gap-3 md:grid-cols-5">
          <div>
            <Label htmlFor="pay-appointment">Reserva</Label>
            <Input id="pay-appointment" inputMode="numeric" value={form.appointment_id} onChange={(event) => setForm((current) => ({ ...current, appointment_id: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="pay-client">Cliente</Label>
            <Input id="pay-client" inputMode="numeric" value={form.client_id} onChange={(event) => setForm((current) => ({ ...current, client_id: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="pay-professional">Profesional</Label>
            <Input id="pay-professional" inputMode="numeric" value={form.professional_id} onChange={(event) => setForm((current) => ({ ...current, professional_id: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="pay-amount">Monto CLP</Label>
            <Input id="pay-amount" inputMode="numeric" placeholder="35000" value={form.amount} onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))} />
          </div>
          <div>
            <Label htmlFor="pay-description">Descripcion</Label>
            <Input id="pay-description" value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button isLoading={createMutation.isPending} onClick={() => createMutation.mutate()}>Crear orden fake</Button>
          <Button isLoading={healthMutation.isPending} onClick={() => healthMutation.mutate()} variant="secondary">Health fake</Button>
        </div>
        {healthMutation.data ? <p className="mt-3 text-sm text-ink-600">{healthMutation.data.code}: {healthMutation.data.message}</p> : null}
        {createMutation.isError ? <ErrorState title="No se pudo crear la orden" /> : null}
      </SectionCard>

      <SectionCard title="Filtros" description="Listado administrativo paginado.">
        <div className="grid gap-3 md:grid-cols-3">
          <Input placeholder="Buscar descripcion o referencia" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
          <Select value={status} onChange={(event) => { setStatus(event.target.value as "" | PaymentOrderStatus); setPage(1); }}>
            <option value="">Todos los estados</option>
            {paymentStatuses.map((item) => <option key={item} value={item}>{getPaymentOrderStatusLabel(item)}</option>)}
          </Select>
          <Select value={provider} onChange={(event) => { setProvider(event.target.value as "" | PaymentProvider); setPage(1); }}>
            <option value="">Todos los providers</option>
            <option value="fake">Fake</option>
            <option value="mercado_pago">Mercado Pago</option>
            <option value="stripe">Stripe</option>
          </Select>
        </div>
      </SectionCard>

      <SectionCard title="Ordenes" description="Las simulaciones fake no modifican reservas en 17.1.">
        {ordersQuery.isLoading ? <LoadingState label="Cargando pagos" /> : null}
        {ordersQuery.isError ? <ErrorState title="No pudimos cargar pagos" /> : null}
        {!ordersQuery.isLoading && ordersQuery.data?.items.length === 0 ? <EmptyState title="Sin ordenes de pago" /> : null}
        <div className="grid gap-3">
          {ordersQuery.data?.items.map((order) => (
            <PaymentAdminCard
              busy={operationMutation.isPending && operationMutation.variables?.id === order.id}
              key={order.id}
              onHistory={() => setSelectedOrderId(order.id)}
              onRun={(action) => operationMutation.mutate({ id: order.id, action })}
              order={order}
            />
          ))}
        </div>
        <AdminPagination meta={ordersQuery.data?.meta} onPageChange={setPage} />
      </SectionCard>

      {selectedOrderId ? (
        <SectionCard title={`Historial orden #${selectedOrderId}`}>
          {historyQuery.isLoading ? <LoadingState label="Cargando historial" /> : null}
          <div className="space-y-2">
            {historyQuery.data?.map((item) => (
              <div className="rounded-md border border-slate-200 bg-white p-3 text-sm" key={item.id}>
                <p className="font-semibold text-ink-900">{item.previous_status ?? "Nueva"} a {getPaymentOrderStatusLabel(item.new_status)}</p>
                <p className="text-ink-500">{formatDateTime(item.created_at)} · {item.reason_code}</p>
                {item.reason_summary ? <p className="mt-1 text-ink-600">{item.reason_summary}</p> : null}
              </div>
            ))}
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}

function PaymentAdminCard({ order, busy, onRun, onHistory }: { order: AdminPaymentOrder; busy: boolean; onRun: (action: "submit" | "approve" | "reject" | "cancel" | "expire" | "fail" | "reconcile") => void; onHistory: () => void }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-ink-900">Orden #{order.id}</h3>
            <Badge label={getPaymentOrderStatusLabel(order.status)} tone={order.status === "approved" ? "success" : order.status === "failed" || order.status === "rejected" ? "danger" : "neutral"} />
            <Badge label={order.provider} tone="info" />
          </div>
          <p className="mt-1 text-sm text-ink-600">{order.description ?? "Sin descripcion"} · CLP {Number(order.amount).toLocaleString("es-CL")}</p>
          <p className="mt-1 text-xs text-ink-500">Reserva {order.appointment_id ?? "sin vinculo"} · Cliente {order.client_id ?? "-"} · Profesional {order.professional_id ?? "-"}</p>
          {order.last_error_message ? <p className="mt-2 text-sm text-danger-700">{order.last_error_code}: {order.last_error_message}</p> : null}
        </div>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          <Button isLoading={busy} onClick={() => onRun("submit")} size="sm" variant="secondary">Submit</Button>
          <Button isLoading={busy} onClick={() => onRun("approve")} size="sm" variant="secondary">Aprobar</Button>
          <Button isLoading={busy} onClick={() => onRun("reject")} size="sm" variant="secondary">Rechazar</Button>
          <Button isLoading={busy} onClick={() => onRun("cancel")} size="sm" variant="secondary">Cancelar</Button>
          <Button isLoading={busy} onClick={() => onRun("expire")} size="sm" variant="secondary">Expirar</Button>
          <Button isLoading={busy} onClick={() => onRun("fail")} size="sm" variant="secondary">Fallar</Button>
          <Button isLoading={busy} onClick={() => onRun("reconcile")} size="sm" variant="secondary">Reconciliar</Button>
          <Button onClick={onHistory} size="sm">Historial</Button>
        </div>
      </div>
    </article>
  );
}
