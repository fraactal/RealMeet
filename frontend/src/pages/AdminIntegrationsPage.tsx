import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAdminIntegration,
  disableAdminIntegration,
  enableAdminIntegration,
  fetchAdminIntegrationExecutions,
  fetchAdminIntegrations,
  healthCheckAdminIntegration,
  testAdminIntegration,
  updateAdminIntegration,
  validateAdminIntegration,
} from "../api/queries";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type {
  Integration,
  IntegrationConfig,
  IntegrationCreatePayload,
  IntegrationExecution,
  IntegrationExecutionStatus,
  IntegrationOperationResult,
  IntegrationProvider,
  IntegrationStatus,
  IntegrationType,
  IntegrationUpdatePayload,
} from "../types";
import { formatDateTime } from "../utils/dates";
import {
  getIntegrationExecutionStatusLabel,
  getIntegrationProviderLabel,
  getIntegrationStatusLabel,
  getIntegrationTypeLabel,
} from "../utils/labels";

const INTEGRATION_TYPES: IntegrationType[] = ["meeting", "calendar", "messaging", "email", "automation", "webhook"];
const INTEGRATION_PROVIDERS: IntegrationProvider[] = [
  "mock",
  "google_meet",
  "google_calendar",
  "microsoft_365",
  "whatsapp_cloud",
  "twilio",
  "smtp",
  "n8n",
  "generic_webhook",
];
const INTEGRATION_STATUSES: IntegrationStatus[] = ["not_configured", "configured", "healthy", "error", "unsupported"];
const SUPPORTED_PROVIDERS: IntegrationProvider[] = ["mock"];
const PAGE_SIZE = 20;

interface FormState {
  id?: number;
  name: string;
  integration_type: IntegrationType;
  provider: IntegrationProvider;
  secret_reference: string;
  simulate_error: boolean;
  health: "healthy" | "error";
  response_delay_ms: number;
}

const emptyForm: FormState = {
  name: "",
  integration_type: "automation",
  provider: "mock",
  secret_reference: "",
  simulate_error: false,
  health: "healthy",
  response_delay_ms: 0,
};

export function AdminIntegrationsPage() {
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState("");
  const [providerFilter, setProviderFilter] = useState("");
  const [enabledFilter, setEnabledFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [testKeyById, setTestKeyById] = useState<Record<number, string>>({});
  const [lastResult, setLastResult] = useState<IntegrationOperationResult | null>(null);

  const integrationsQuery = useQuery({
    queryKey: ["admin-integrations", typeFilter, providerFilter, enabledFilter, statusFilter],
    queryFn: () =>
      fetchAdminIntegrations({
        integration_type: (typeFilter || undefined) as IntegrationType | undefined,
        provider: (providerFilter || undefined) as IntegrationProvider | undefined,
        enabled: enabledFilter === "" ? undefined : enabledFilter === "enabled",
        status: (statusFilter || undefined) as IntegrationStatus | undefined,
        page_size: PAGE_SIZE,
      }),
  });

  const selectedIntegration = useMemo(
    () => integrationsQuery.data?.items.find((item) => item.id === selectedId) ?? integrationsQuery.data?.items[0] ?? null,
    [integrationsQuery.data?.items, selectedId],
  );

  const executionsQuery = useQuery({
    queryKey: ["admin-integration-executions", selectedIntegration?.id],
    queryFn: () => fetchAdminIntegrationExecutions(selectedIntegration?.id ?? 0),
    enabled: Boolean(selectedIntegration?.id),
  });

  const refreshIntegrations = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-integrations"] });
    if (selectedIntegration?.id) {
      void queryClient.invalidateQueries({ queryKey: ["admin-integration-executions", selectedIntegration.id] });
    }
  };

  const createMutation = useMutation({
    mutationFn: (payload: IntegrationCreatePayload) => createAdminIntegration(payload),
    onSuccess: (item) => {
      setFormOpen(false);
      setSelectedId(item.id);
      setLastResult(null);
      refreshIntegrations();
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: IntegrationUpdatePayload }) => updateAdminIntegration(id, payload),
    onSuccess: (item) => {
      setFormOpen(false);
      setSelectedId(item.id);
      refreshIntegrations();
    },
  });
  const validateMutation = useOperationMutation((id) => validateAdminIntegration(id), setLastResult, refreshIntegrations);
  const enableMutation = useMutation({
    mutationFn: (id: number) => enableAdminIntegration(id),
    onSuccess: (item) => {
      setSelectedId(item.id);
      refreshIntegrations();
    },
  });
  const disableMutation = useMutation({
    mutationFn: (id: number) => disableAdminIntegration(id),
    onSuccess: (item) => {
      setSelectedId(item.id);
      refreshIntegrations();
    },
  });
  const healthMutation = useOperationMutation((id) => healthCheckAdminIntegration(id), setLastResult, refreshIntegrations);
  const testMutation = useMutation({
    mutationFn: ({ id, idempotency_key }: { id: number; idempotency_key: string }) => testAdminIntegration(id, { idempotency_key }),
    onSuccess: (result) => {
      setLastResult(result);
      refreshIntegrations();
    },
  });

  const openCreate = () => {
    setForm(emptyForm);
    setFormOpen(true);
  };

  const openEdit = (integration: Integration) => {
    setForm({
      id: integration.id,
      name: integration.name,
      integration_type: integration.integration_type,
      provider: integration.provider,
      secret_reference: integration.secret_reference ?? "",
      simulate_error: integration.config.simulate_error ?? false,
      health: integration.config.health ?? "healthy",
      response_delay_ms: integration.config.response_delay_ms ?? 0,
    });
    setFormOpen(true);
  };

  const saveForm = () => {
    const config = buildConfig(form);
    if (form.id) {
      updateMutation.mutate({
        id: form.id,
        payload: {
          name: form.name.trim(),
          config,
          secret_reference: form.secret_reference.trim() || null,
        },
      });
      return;
    }

    createMutation.mutate({
      name: form.name.trim(),
      integration_type: form.integration_type,
      provider: form.provider,
      config,
      secret_reference: form.secret_reference.trim() || null,
    });
  };

  const generateTestKey = (integrationId: number) => {
    setTestKeyById((current) => ({ ...current, [integrationId]: `manual:test:${Date.now()}` }));
  };

  const errorMessage =
    getMutationError(createMutation.error) ??
    getMutationError(updateMutation.error) ??
    getMutationError(validateMutation.error) ??
    getMutationError(enableMutation.error) ??
    getMutationError(disableMutation.error) ??
    getMutationError(healthMutation.error) ??
    getMutationError(testMutation.error);

  return (
    <div className="space-y-6">
      <PageHeader title="Integraciones" description="Gestiona la base administrativa para proveedores externos futuros y pruebas mock internas." />

      <SectionCard
        title="Integraciones configuradas"
        description="Solo el proveedor mock esta disponible para ejecucion en esta etapa. Los demas proveedores se habilitaran en modulos posteriores."
        actions={<Button onClick={openCreate}>Crear integracion</Button>}
      >
        <div className="grid gap-4 md:grid-cols-4">
          <FilterSelect label="Tipo" value={typeFilter} onChange={setTypeFilter}>
            {INTEGRATION_TYPES.map((type) => (
              <option key={type} value={type}>
                {getIntegrationTypeLabel(type)}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect label="Proveedor" value={providerFilter} onChange={setProviderFilter}>
            {INTEGRATION_PROVIDERS.map((provider) => (
              <option key={provider} value={provider}>
                {getIntegrationProviderLabel(provider)}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect label="Habilitacion" value={enabledFilter} onChange={setEnabledFilter}>
            <option value="enabled">Habilitadas</option>
            <option value="disabled">Deshabilitadas</option>
          </FilterSelect>
          <FilterSelect label="Estado" value={statusFilter} onChange={setStatusFilter}>
            {INTEGRATION_STATUSES.map((status) => (
              <option key={status} value={status}>
                {getIntegrationStatusLabel(status)}
              </option>
            ))}
          </FilterSelect>
        </div>

        {integrationsQuery.isLoading ? <div className="mt-5"><LoadingState label="Cargando integraciones" /></div> : null}
        {integrationsQuery.isError ? <div className="mt-5"><ErrorState title="No pudimos cargar las integraciones" message="Intenta nuevamente o revisa el estado del backend." /></div> : null}
        {!integrationsQuery.isLoading && integrationsQuery.data?.items.length === 0 ? (
          <div className="mt-5">
            <EmptyState title="Aun no hay integraciones configuradas" description="Crea una integracion mock para validar la base operativa sin conectar proveedores externos." actionLabel="Crear integracion de prueba" onAction={openCreate} />
          </div>
        ) : null}

        <div className="mt-5 hidden overflow-hidden rounded-lg border border-slate-200 xl:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Proveedor</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Ultimo chequeo</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {integrationsQuery.data?.items.map((integration) => (
                <IntegrationRow
                  key={integration.id}
                  integration={integration}
                  isSelected={selectedIntegration?.id === integration.id}
                  onSelect={() => setSelectedId(integration.id)}
                  onEdit={() => openEdit(integration)}
                  onValidate={() => validateMutation.mutate(integration.id)}
                  onEnable={() => enableMutation.mutate(integration.id)}
                  onDisable={() => disableMutation.mutate(integration.id)}
                  loading={isActionLoading(integration.id, validateMutation, enableMutation, disableMutation)}
                />
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-5 grid gap-3 xl:hidden">
          {integrationsQuery.data?.items.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              isSelected={selectedIntegration?.id === integration.id}
              onSelect={() => setSelectedId(integration.id)}
              onEdit={() => openEdit(integration)}
              onValidate={() => validateMutation.mutate(integration.id)}
              onEnable={() => enableMutation.mutate(integration.id)}
              onDisable={() => disableMutation.mutate(integration.id)}
              loading={isActionLoading(integration.id, validateMutation, enableMutation, disableMutation)}
            />
          ))}
        </div>
      </SectionCard>

      {errorMessage ? <ErrorState title="No pudimos completar la accion" message={errorMessage} /> : null}
      {lastResult ? <OperationResultPanel result={lastResult} /> : null}

      {selectedIntegration ? (
        <SectionCard title="Gestion operativa" description="Ejecuta acciones seguras sobre la integracion seleccionada y revisa sus ejecuciones recientes.">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-ink-900">{selectedIntegration.name}</h3>
                  <p className="mt-1 text-sm text-ink-500">
                    {getIntegrationTypeLabel(selectedIntegration.integration_type)} · {getIntegrationProviderLabel(selectedIntegration.provider)}
                  </p>
                </div>
                <IntegrationStatusBadges integration={selectedIntegration} />
              </div>
              <div className="mt-4 grid gap-3 text-sm text-ink-600 sm:grid-cols-3">
                <InfoItem label="Ultimo chequeo" value={formatOptionalDate(selectedIntegration.last_checked_at)} />
                <InfoItem label="Ultimo exito" value={formatOptionalDate(selectedIntegration.last_success_at)} />
                <InfoItem label="Ultimo error" value={selectedIntegration.last_error_message ?? "Sin errores"} />
              </div>
              {!isSupportedProvider(selectedIntegration.provider) ? (
                <p className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-600">Proveedor aun no soportado. Puedes revisar o editar su configuracion, pero no habilitarlo ni ejecutar pruebas.</p>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={() => openEdit(selectedIntegration)} variant="secondary">Editar</Button>
                {selectedIntegration.enabled && isSupportedProvider(selectedIntegration.provider) ? (
                  <>
                    <Button isLoading={healthMutation.isPending} onClick={() => healthMutation.mutate(selectedIntegration.id)} variant="secondary">Health check</Button>
                    <Button isLoading={disableMutation.isPending} onClick={() => window.confirm("La configuracion se conservara, pero la integracion no podra ejecutar pruebas ni chequeos.") && disableMutation.mutate(selectedIntegration.id)} variant="secondary">Deshabilitar</Button>
                  </>
                ) : null}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="text-base font-semibold text-ink-900">Prueba mock</h3>
              <p className="mt-1 text-sm leading-6 text-ink-500">Reutilizar la misma clave evita ejecutar dos veces la misma operacion.</p>
              <div className="mt-4 space-y-2">
                <Label htmlFor="idempotency-key">Clave idempotente</Label>
                <Input
                  id="idempotency-key"
                  value={testKeyById[selectedIntegration.id] ?? ""}
                  onChange={(event) => setTestKeyById((current) => ({ ...current, [selectedIntegration.id]: event.target.value }))}
                  placeholder="manual:test:timestamp"
                />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={() => generateTestKey(selectedIntegration.id)} variant="secondary">Generar clave</Button>
                <Button
                  disabled={!selectedIntegration.enabled || selectedIntegration.provider !== "mock" || !(testKeyById[selectedIntegration.id] ?? "").trim()}
                  isLoading={testMutation.isPending}
                  onClick={() => testMutation.mutate({ id: selectedIntegration.id, idempotency_key: (testKeyById[selectedIntegration.id] ?? "").trim() })}
                >
                  Ejecutar prueba
                </Button>
              </div>
              {selectedIntegration.provider !== "mock" ? <p className="mt-3 text-sm text-ink-500">La prueba manual solo esta disponible para mock interno.</p> : null}
              {!selectedIntegration.enabled ? <p className="mt-3 text-sm text-ink-500">Habilita la integracion para ejecutar pruebas o health checks.</p> : null}
            </div>
          </div>

          <div className="mt-5">
            <h3 className="mb-3 text-base font-semibold text-ink-900">Ejecuciones recientes</h3>
            {executionsQuery.isLoading ? <LoadingState label="Cargando ejecuciones" /> : null}
            {executionsQuery.isError ? <ErrorState title="No pudimos cargar ejecuciones" message="Intenta nuevamente." /> : null}
            {!executionsQuery.isLoading && executionsQuery.data?.length === 0 ? <EmptyState title="Esta integracion todavia no registra ejecuciones" /> : null}
            <IntegrationExecutionList items={executionsQuery.data ?? []} />
          </div>
        </SectionCard>
      ) : null}

      {formOpen ? (
        <IntegrationFormModal
          form={form}
          isSaving={createMutation.isPending || updateMutation.isPending}
          onChange={setForm}
          onClose={() => setFormOpen(false)}
          onSave={saveForm}
        />
      ) : null}
    </div>
  );
}

function useOperationMutation(
  mutationFn: (id: number) => Promise<IntegrationOperationResult>,
  setLastResult: (result: IntegrationOperationResult) => void,
  onSuccess: () => void,
) {
  return useMutation({
    mutationFn,
    onSuccess: (result) => {
      setLastResult(result);
      onSuccess();
    },
  });
}

function buildConfig(form: FormState): IntegrationConfig {
  if (form.provider !== "mock") {
    return {};
  }
  return {
    simulate_error: form.simulate_error,
    health: form.health,
    response_delay_ms: Number(form.response_delay_ms) || 0,
  };
}

function isSupportedProvider(provider: IntegrationProvider): boolean {
  return SUPPORTED_PROVIDERS.includes(provider);
}

function IntegrationStatusBadges({ integration }: { integration: Integration }) {
  const tone: "success" | "danger" | "neutral" | "warning" = integration.status === "healthy" || integration.status === "configured" ? "success" : integration.status === "error" ? "danger" : integration.status === "unsupported" ? "neutral" : "warning";
  return (
    <div className="flex flex-wrap gap-2">
      <Badge label={getIntegrationStatusLabel(integration.status)} tone={tone} />
      <Badge label={integration.enabled ? "Habilitada" : "Deshabilitada"} tone={integration.enabled ? "info" : "neutral"} />
    </div>
  );
}

function IntegrationRow(props: IntegrationItemProps) {
  const { integration, isSelected, onSelect, onEdit, onValidate, onEnable, onDisable, loading } = props;
  return (
    <tr className={isSelected ? "bg-brand-50/60" : "transition hover:bg-slate-50"}>
      <td className="px-4 py-4">
        <button className="text-left font-semibold text-ink-900 hover:text-brand-700" onClick={onSelect} type="button">{integration.name}</button>
        <p className="mt-1 text-xs text-ink-500">{isSupportedProvider(integration.provider) ? "Disponible para pruebas" : "Proximamente"}</p>
      </td>
      <td className="px-4 py-4">{getIntegrationTypeLabel(integration.integration_type)}</td>
      <td className="px-4 py-4">{getIntegrationProviderLabel(integration.provider)}</td>
      <td className="px-4 py-4"><IntegrationStatusBadges integration={integration} /></td>
      <td className="px-4 py-4 text-ink-500">{formatOptionalDate(integration.last_checked_at)}</td>
      <td className="px-4 py-4">
        <IntegrationActions integration={integration} loading={loading} onDisable={onDisable} onEdit={onEdit} onEnable={onEnable} onValidate={onValidate} />
      </td>
    </tr>
  );
}

interface IntegrationItemProps {
  integration: Integration;
  isSelected: boolean;
  loading: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onValidate: () => void;
  onEnable: () => void;
  onDisable: () => void;
}

function IntegrationCard(props: IntegrationItemProps) {
  const { integration, isSelected, onSelect, onEdit, onValidate, onEnable, onDisable, loading } = props;
  return (
    <article className={["rounded-lg border bg-white p-4 shadow-sm", isSelected ? "border-brand-300" : "border-slate-200"].join(" ")}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <button className="text-left font-semibold text-ink-900 hover:text-brand-700" onClick={onSelect} type="button">{integration.name}</button>
          <p className="mt-1 text-sm text-ink-500">{getIntegrationTypeLabel(integration.integration_type)} · {getIntegrationProviderLabel(integration.provider)}</p>
        </div>
        <IntegrationStatusBadges integration={integration} />
      </div>
      <div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-2">
        <InfoItem label="Ultimo chequeo" value={formatOptionalDate(integration.last_checked_at)} />
        <InfoItem label="Ultimo error" value={integration.last_error_message ?? "Sin errores"} />
      </div>
      <div className="mt-4"><IntegrationActions integration={integration} loading={loading} onDisable={onDisable} onEdit={onEdit} onEnable={onEnable} onValidate={onValidate} /></div>
    </article>
  );
}

function IntegrationActions({ integration, loading, onDisable, onEdit, onEnable, onValidate }: Omit<IntegrationItemProps, "isSelected" | "onSelect">) {
  const supported = isSupportedProvider(integration.provider);
  return (
    <div className="flex flex-wrap justify-end gap-2">
      <Button onClick={onEdit} size="sm" variant="secondary">Editar</Button>
      {supported ? <Button isLoading={loading} onClick={onValidate} size="sm" variant="secondary">Validar</Button> : <Button disabled size="sm" title="Proveedor aun no soportado" variant="secondary">Proximamente</Button>}
      {supported && !integration.enabled ? <Button isLoading={loading} onClick={() => window.confirm("La integracion comenzara a estar disponible para operaciones futuras. En este modulo solo mock tiene ejecucion real.") && onEnable()} size="sm">Habilitar</Button> : null}
      {supported && integration.enabled ? <Button isLoading={loading} onClick={() => window.confirm("La configuracion se conservara, pero la integracion no podra ejecutar pruebas ni chequeos.") && onDisable()} size="sm" variant="secondary">Deshabilitar</Button> : null}
    </div>
  );
}

function IntegrationFormModal({ form, isSaving, onChange, onClose, onSave }: { form: FormState; isSaving: boolean; onChange: (form: FormState) => void; onClose: () => void; onSave: () => void }) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const editing = Boolean(form.id);
  return (
    <div className="fixed inset-0 z-50 flex items-end bg-ink-900/40 p-3 sm:items-center sm:justify-center" role="dialog" aria-modal="true" aria-labelledby="integration-form-title">
      <div className="max-h-[92vh] w-full overflow-y-auto rounded-lg bg-white p-5 shadow-xl sm:max-w-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="integration-form-title" className="text-lg font-semibold text-ink-900">{editing ? "Editar integracion" : "Crear integracion"}</h2>
            <p className="mt-1 text-sm text-ink-500">RealMeet no almacena credenciales directamente en esta seccion.</p>
          </div>
          <Button onClick={onClose} variant="ghost">Cerrar</Button>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="Nombre" id="integration-name">
            <Input id="integration-name" value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} />
          </Field>
          <Field label="Tipo" id="integration-type">
            <Select id="integration-type" disabled={editing} value={form.integration_type} onChange={(event) => onChange({ ...form, integration_type: event.target.value as IntegrationType })}>
              {INTEGRATION_TYPES.map((type) => <option key={type} value={type}>{getIntegrationTypeLabel(type)}</option>)}
            </Select>
          </Field>
          <Field label="Proveedor" id="integration-provider">
            <Select id="integration-provider" disabled={editing} value={form.provider} onChange={(event) => onChange({ ...form, provider: event.target.value as IntegrationProvider })}>
              {INTEGRATION_PROVIDERS.map((provider) => <option disabled={provider !== "mock"} key={provider} value={provider}>{getIntegrationProviderLabel(provider)}{provider !== "mock" ? " - Proximamente" : ""}</option>)}
            </Select>
          </Field>
          <Field label="Referencia de secreto" id="integration-secret">
            <Input id="integration-secret" value={form.secret_reference} onChange={(event) => onChange({ ...form, secret_reference: event.target.value })} placeholder="WHATSAPP_ACCESS_TOKEN" />
          </Field>
        </div>
        <p className="mt-3 text-sm leading-6 text-ink-500">Ingresa solo el nombre de la variable de entorno que contiene la credencial. No ingreses aqui el token, contrasena o secreto real.</p>
        {form.provider === "mock" ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-ink-900">Configuracion mock</h3>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
                <input checked={form.simulate_error} onChange={(event) => onChange({ ...form, simulate_error: event.target.checked })} type="checkbox" />
                Simular error
              </label>
              <Field label="Estado health" id="mock-health">
                <Select id="mock-health" value={form.health} onChange={(event) => onChange({ ...form, health: event.target.value as "healthy" | "error" })}>
                  <option value="healthy">Saludable</option>
                  <option value="error">Error controlado</option>
                </Select>
              </Field>
              <Field label="Delay simulado ms" id="mock-delay">
                <Input id="mock-delay" min={0} max={250} type="number" value={form.response_delay_ms} onChange={(event) => onChange({ ...form, response_delay_ms: Number(event.target.value) })} />
              </Field>
            </div>
          </div>
        ) : (
          <p className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-ink-600">La configuracion especifica de este proveedor estara disponible en una proxima etapa.</p>
        )}
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button onClick={onClose} variant="secondary">Cancelar</Button>
          <Button disabled={!form.name.trim()} isLoading={isSaving} onClick={onSave}>{editing ? "Guardar cambios" : "Crear integracion"}</Button>
        </div>
      </div>
    </div>
  );
}

function IntegrationExecutionList({ items }: { items: IntegrationExecution[] }) {
  if (items.length === 0) return null;
  return (
    <>
      <div className="hidden overflow-hidden rounded-lg border border-slate-200 lg:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-ink-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Operacion</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Intento</th><th className="px-4 py-3">Duracion</th><th className="px-4 py-3">Error</th></tr></thead>
          <tbody className="divide-y divide-slate-100 bg-white">{items.map((item) => <ExecutionCells item={item} key={item.id} />)}</tbody>
        </table>
      </div>
      <div className="grid gap-3 lg:hidden">{items.map((item) => <ExecutionCard item={item} key={item.id} />)}</div>
    </>
  );
}

function ExecutionCells({ item }: { item: IntegrationExecution }) {
  return <tr><td className="px-4 py-3">{formatDateTime(item.created_at)}</td><td className="px-4 py-3">{item.operation}</td><td className="px-4 py-3"><ExecutionBadge status={item.status} /></td><td className="px-4 py-3">{item.attempt}</td><td className="px-4 py-3">{durationText(item)}</td><td className="px-4 py-3 text-ink-500">{item.error_message ?? item.error_code ?? "Sin error"}</td></tr>;
}

function ExecutionCard({ item }: { item: IntegrationExecution }) {
  return <article className="rounded-lg border border-slate-200 bg-white p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-ink-900">{item.operation}</p><p className="mt-1 text-sm text-ink-500">{formatDateTime(item.created_at)}</p></div><ExecutionBadge status={item.status} /></div><div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-2"><InfoItem label="Intento" value={String(item.attempt)} /><InfoItem label="Duracion" value={durationText(item)} /><InfoItem label="Entidad" value={item.entity_type && item.entity_id ? `${item.entity_type} ${item.entity_id}` : "Sin entidad"} /><InfoItem label="Error" value={item.error_message ?? item.error_code ?? "Sin error"} /></div></article>;
}

function ExecutionBadge({ status }: { status: IntegrationExecutionStatus }) {
  const tone: "success" | "danger" | "info" | "neutral" | "warning" = status === "succeeded" ? "success" : status === "failed" ? "danger" : status === "running" ? "info" : status === "skipped" ? "neutral" : "warning";
  return <Badge label={getIntegrationExecutionStatusLabel(status)} tone={tone} />;
}

function OperationResultPanel({ result }: { result: IntegrationOperationResult }) {
  const title = result.skipped ? "Operacion ya procesada" : result.success ? "Operacion completada" : "Operacion fallida";
  return <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"><p className="font-semibold text-ink-900">{title}</p><p className="mt-1 text-sm text-ink-600">{translateResultMessage(result)}</p><p className="mt-2 text-xs text-ink-500">Duracion: {result.duration_ms} ms{result.execution_id ? ` · Ejecucion ${result.execution_id}` : ""}</p></div>;
}

function translateResultMessage(result: IntegrationOperationResult): string {
  if (result.code === "already_processed") return "La misma clave idempotente ya fue procesada.";
  if (result.code === "mock_configuration_valid") return "Configuracion valida.";
  if (result.code === "mock_health_ok") return "Health check completado correctamente.";
  if (result.code === "mock_test_ok") return "Prueba mock completada.";
  if (result.code.includes("error")) return "La operacion reporto un error controlado.";
  return result.message;
}

function Field({ children, id, label }: { children: ReactNode; id: string; label: string }) {
  return <div className="space-y-1"><Label htmlFor={id}>{label}</Label>{children}</div>;
}

function FilterSelect({ children, label, onChange, value }: { children: ReactNode; label: string; onChange: (value: string) => void; value: string }) {
  const id = `filter-${label.toLowerCase().split(" ").join("-")}`;
  return <Field id={id} label={label}><Select id={id} value={value} onChange={(event) => onChange(event.target.value)}><option value="">Todos</option>{children}</Select></Field>;
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs font-semibold uppercase text-ink-400">{label}</p><p className="mt-1 break-words text-ink-700">{value}</p></div>;
}

function formatOptionalDate(value?: string | null): string {
  return value ? formatDateTime(value) : "Sin registro";
}

function durationText(item: IntegrationExecution): string {
  if (!item.started_at || !item.finished_at) return "Sin duracion";
  const duration = Math.max(new Date(item.finished_at).getTime() - new Date(item.started_at).getTime(), 0);
  return `${duration} ms`;
}

function getMutationError(error: unknown): string | null {
  if (!error || typeof error !== "object") return null;
  const maybe = error as { response?: { data?: { detail?: string } } };
  const detail = maybe.response?.data?.detail;
  if (detail?.includes("proveedor")) return "Este proveedor todavia no esta soportado.";
  if (detail?.includes("deshabilitada")) return "La integracion esta deshabilitada.";
  if (detail?.includes("Configuracion") || detail?.includes("configuracion")) return "La configuracion necesita correcciones.";
  return detail ?? "No pudimos completar la accion solicitada.";
}

function isActionLoading(
  id: number,
  ...mutations: Array<{ isPending: boolean; variables?: number }>
): boolean {
  return mutations.some((mutation) => mutation.isPending && mutation.variables === id);
}
