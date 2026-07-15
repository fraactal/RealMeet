import { useEffect, useMemo, useState, type ReactNode } from "react";

import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, Select } from "../../ui";
import type {
  Integration,
  WhatsAppConsentCorrectionPayload,
  WhatsAppConsentPurpose,
  WhatsAppConsentSummary,
  WhatsAppIntegrationStatus,
  WhatsAppTemplate,
  WhatsAppTemplatePurpose,
  WhatsAppTemplateVariable,
  WhatsAppTemplateWrite,
  WhatsAppValidationResult,
  WhatsAppWebhookEvent,
  WhatsAppWebhookStatus,
} from "../../../types";
import { formatDateTime } from "../../../utils/dates";
import {
  getWhatsAppConsentPurposeLabel,
  getWhatsAppConsentSourceLabel,
  getWhatsAppConsentStatusLabel,
  getWhatsAppTemplatePurposeLabel,
  getWhatsAppTemplateStatusLabel,
  getWhatsAppWebhookEventTypeLabel,
  getWhatsAppWebhookProcessingStatusLabel,
  whatsappVariableLabels,
} from "../../../utils/labels";

const TEMPLATE_VARIABLES: WhatsAppTemplateVariable["key"][] = [
  "client_name",
  "professional_name",
  "appointment_date",
  "appointment_time",
  "appointment_modality",
  "meeting_url",
  "platform_name",
];

const TEMPLATE_PURPOSES: WhatsAppTemplatePurpose[] = [
  "appointment_confirmation",
  "appointment_reminder",
  "appointment_updated",
  "appointment_cancelled",
  "meeting_ready",
];

const CONSENT_PURPOSES: WhatsAppConsentPurpose[] = [
  "appointment_transactional",
  "appointment_reminders",
  "appointment_updates",
];

interface WhatsAppFoundationPanelProps {
  integration: Integration;
  status?: WhatsAppIntegrationStatus;
  webhookStatus?: WhatsAppWebhookStatus;
  templates: WhatsAppTemplate[];
  consents: WhatsAppConsentSummary[];
  events: WhatsAppWebhookEvent[];
  loading: boolean;
  error: boolean;
  validationResult?: WhatsAppValidationResult | null;
  validating: boolean;
  templateSaving: boolean;
  correctionSaving: boolean;
  onValidate: () => void;
  onCreateTemplate: (payload: Required<WhatsAppTemplateWrite>) => void;
  onUpdateTemplate: (templateId: number, payload: WhatsAppTemplateWrite) => void;
  onCreateConsentCorrection: (payload: WhatsAppConsentCorrectionPayload) => void;
  onRefresh: () => void;
}

interface TemplateFormState {
  id?: number;
  name: string;
  language: string;
  purpose: WhatsAppTemplatePurpose;
  variables: WhatsAppTemplateVariable["key"][];
}

interface ConsentCorrectionState {
  user_id: string;
  phone: string;
  purpose: WhatsAppConsentPurpose;
  consent_text_version: string;
  reason: string;
  explicit_confirmation: boolean;
}

const emptyTemplateForm: TemplateFormState = {
  name: "",
  language: "es_CL",
  purpose: "appointment_confirmation",
  variables: ["client_name", "professional_name", "appointment_date", "appointment_time"],
};

const emptyConsentCorrection: ConsentCorrectionState = {
  user_id: "",
  phone: "",
  purpose: "appointment_transactional",
  consent_text_version: "wa-consent-v1",
  reason: "",
  explicit_confirmation: false,
};

export function WhatsAppFoundationPanel({
  integration,
  status,
  webhookStatus,
  templates,
  consents,
  events,
  loading,
  error,
  validationResult,
  validating,
  templateSaving,
  correctionSaving,
  onValidate,
  onCreateTemplate,
  onUpdateTemplate,
  onCreateConsentCorrection,
  onRefresh,
}: WhatsAppFoundationPanelProps) {
  const [templateForm, setTemplateForm] = useState<TemplateFormState | null>(null);
  const [consentFormOpen, setConsentFormOpen] = useState(false);
  const [consentForm, setConsentForm] = useState<ConsentCorrectionState>(emptyConsentCorrection);
  const [selectedEvent, setSelectedEvent] = useState<WhatsAppWebhookEvent | null>(null);
  const secretReferences = integration.config.secret_references ?? {};
  const webhookUrl = webhookStatus?.public_url ?? "";

  const configuredRefs = useMemo(
    () =>
      [
        ["Access token", secretReferences.access_token],
        ["App secret", secretReferences.app_secret],
        ["Verify token", secretReferences.verify_token],
        ["Phone HMAC key", secretReferences.phone_hmac_key],
      ] as const,
    [secretReferences.access_token, secretReferences.app_secret, secretReferences.phone_hmac_key, secretReferences.verify_token],
  );

  const saveTemplate = () => {
    if (!templateForm?.name.trim()) return;
    const payload: Required<WhatsAppTemplateWrite> = {
      name: templateForm.name.trim(),
      language: templateForm.language.trim() || "es_CL",
      category: "utility",
      purpose: templateForm.purpose,
      components_schema: {
        variables: templateForm.variables.map((key) => ({ key, required: true, sensitive: false })),
      },
    };
    if (templateForm.id) {
      onUpdateTemplate(templateForm.id, payload);
      setTemplateForm(null);
      return;
    }
    onCreateTemplate(payload);
    setTemplateForm(null);
  };

  const saveConsentCorrection = () => {
    const userId = Number(consentForm.user_id);
    if (!userId || !consentForm.phone.trim() || !consentForm.reason.trim() || !consentForm.explicit_confirmation) return;
    onCreateConsentCorrection({
      user_id: userId,
      phone: consentForm.phone.trim(),
      purpose: consentForm.purpose,
      consent_text_version: consentForm.consent_text_version.trim() || "wa-consent-v1",
      reason: consentForm.reason.trim(),
    });
    setConsentFormOpen(false);
  };

  return (
    <div className="mt-5 space-y-5 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Fundacion WhatsApp Cloud</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">
            Configuracion local, webhooks, plantillas y consentimientos. El envio real de mensajes queda fuera de 13.1.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge label="Sin envio" tone="neutral" />
          <Badge label={status?.locally_configured ? "Config local valida" : "Config local pendiente"} tone={status?.locally_configured ? "success" : "warning"} />
          <Badge label={status?.operational_for_sending ? "Envio operativo" : "Envio no habilitado"} tone={status?.operational_for_sending ? "success" : "neutral"} />
        </div>
      </div>

      {loading ? <LoadingState label="Cargando fundamento WhatsApp" /> : null}
      {error ? <ErrorState title="No pudimos cargar WhatsApp" message="Revisa la configuracion local o intenta nuevamente." /> : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Configuracion segura">
          <div className="grid gap-3 text-sm text-ink-600 sm:grid-cols-2 xl:grid-cols-1">
            <Info label="WABA ID" value={status?.waba_id_partial ?? maskId(integration.config.waba_id)} />
            <Info label="Phone number ID" value={status?.phone_number_id_partial ?? maskId(integration.config.phone_number_id)} />
            <Info label="Telefono visible" value={status?.display_phone_number_masked ?? integration.config.display_phone_number_masked ?? "No configurado"} />
            <Info label="Graph API" value={status?.graph_api_version ?? integration.config.graph_api_version ?? "No configurada"} />
            <Info label="Idioma" value={status?.default_language ?? integration.config.default_language ?? "es_CL"} />
            <Info label="Pais" value={status?.country_code ?? integration.config.country_code ?? "CL"} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button isLoading={validating} onClick={onValidate} variant="secondary">Validar configuracion</Button>
            <Button onClick={onRefresh} variant="ghost">Actualizar</Button>
          </div>
          {validationResult ? (
            <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-ink-600">
              <p className="font-semibold text-ink-900">{validationResult.success ? "Configuracion valida" : "La configuracion necesita correcciones"}</p>
              <p className="mt-1">{validationResult.message}</p>
            </div>
          ) : null}
        </Panel>

        <Panel title="Referencias de secretos">
          <p className="text-sm leading-6 text-ink-500">Solo se muestran nombres de variables de entorno. No ingreses tokens, passwords ni secretos reales.</p>
          <div className="mt-3 space-y-2">
            {configuredRefs.map(([label, value]) => (
              <div key={label} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold uppercase text-ink-500">{label}</p>
                <p className="mt-1 break-all text-sm font-semibold text-ink-800">{value || "No configurada"}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Webhook">
          <div className="grid gap-3 text-sm text-ink-600">
            <Info label="URL publica" value={webhookStatus?.public_url_configured ? "Configurada" : "No configurada"} />
            <Info label="Verify token" value={webhookStatus?.verify_token_configured ? "Configurado" : "No configurado"} />
            <Info label="App secret" value={webhookStatus?.app_secret_configured ? "Configurado" : "No configurado"} />
            <Info label="Firma requerida" value={webhookStatus?.signature_required ? "Si" : "No"} />
            <Info label="Retencion eventos" value={webhookStatus ? `${webhookStatus.retention_days} dias` : "No disponible"} />
            <Info label="Ultimo evento" value={webhookStatus?.last_received_at ? formatDateTime(webhookStatus.last_received_at) : "Sin eventos"} />
          </div>
          {webhookUrl ? (
            <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3">
              <p className="break-all text-sm text-ink-700">{webhookUrl}</p>
              <Button className="mt-3" onClick={() => void navigator.clipboard?.writeText(webhookUrl)} size="sm" variant="secondary">Copiar URL</Button>
            </div>
          ) : (
            <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-ink-500">Configura la URL publica mediante variables de entorno del backend.</p>
          )}
        </Panel>
      </div>

      <Panel title="Plantillas locales">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-6 text-ink-500">Catalogo local utility preparado para futuras aprobaciones en Meta. No sincroniza ni envia mensajes.</p>
          <Button onClick={() => setTemplateForm(emptyTemplateForm)} variant="secondary">Crear plantilla</Button>
        </div>
        {templates.length === 0 ? <div className="mt-4"><EmptyState title="Aun no hay plantillas locales" /></div> : null}
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {templates.map((template) => (
            <article className="rounded-lg border border-slate-200 bg-slate-50 p-4" key={template.id}>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="font-semibold text-ink-900">{template.name}</p>
                  <p className="mt-1 text-sm text-ink-500">{getWhatsAppTemplatePurposeLabel(template.purpose)} · {template.language}</p>
                </div>
                <Badge label={getWhatsAppTemplateStatusLabel(template.status)} tone={template.status === "approved" ? "success" : template.status === "rejected" ? "danger" : "neutral"} />
              </div>
              <p className="mt-3 text-sm text-ink-600">Variables: {template.components_schema.variables?.map((item) => whatsappVariableLabels[item.key] ?? item.key).join(", ") || "Sin variables"}</p>
              <Button className="mt-3" onClick={() => setTemplateForm(templateToForm(template))} size="sm" variant="secondary">Editar local</Button>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Consentimientos">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-6 text-ink-500">Resumen administrativo con telefonos enmascarados. Las correcciones requieren motivo.</p>
          <Button onClick={() => { setConsentForm(emptyConsentCorrection); setConsentFormOpen(true); }} variant="secondary">Registrar correccion</Button>
        </div>
        {consents.length === 0 ? <div className="mt-4"><EmptyState title="Aun no hay consentimientos WhatsApp" /></div> : null}
        <div className="mt-4 hidden overflow-hidden rounded-lg border border-slate-200 lg:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500"><tr><th className="px-4 py-3">Usuario</th><th className="px-4 py-3">Telefono</th><th className="px-4 py-3">Proposito</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Origen</th><th className="px-4 py-3">Fecha</th></tr></thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {consents.map((consent) => (
                <tr key={consent.id}><td className="px-4 py-3">{consent.user_id}</td><td className="px-4 py-3">{consent.phone_masked}</td><td className="px-4 py-3">{getWhatsAppConsentPurposeLabel(consent.purpose)}</td><td className="px-4 py-3">{getWhatsAppConsentStatusLabel(consent.status)}</td><td className="px-4 py-3">{getWhatsAppConsentSourceLabel(consent.source)}</td><td className="px-4 py-3">{formatDateTime(consent.created_at)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 grid gap-3 lg:hidden">
          {consents.map((consent) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={consent.id}>
              <div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-ink-900">Usuario {consent.user_id}</p><p className="text-sm text-ink-500">{consent.phone_masked}</p></div><Badge label={getWhatsAppConsentStatusLabel(consent.status)} tone={consent.status === "granted" ? "success" : "neutral"} /></div>
              <div className="mt-3 grid gap-2 text-sm text-ink-600"><Info label="Proposito" value={getWhatsAppConsentPurposeLabel(consent.purpose)} /><Info label="Origen" value={getWhatsAppConsentSourceLabel(consent.source)} /><Info label="Fecha" value={formatDateTime(consent.created_at)} /></div>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Eventos webhook recientes">
        {events.length === 0 ? <EmptyState title="No hay eventos webhook recientes" /> : null}
        <div className="hidden overflow-hidden rounded-lg border border-slate-200 lg:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-ink-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Duplicado</th><th className="px-4 py-3">Telefono</th><th className="px-4 py-3 text-right">Detalle</th></tr></thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {events.map((event) => (
                <tr key={event.id}><td className="px-4 py-3">{formatDateTime(event.received_at)}</td><td className="px-4 py-3">{getWhatsAppWebhookEventTypeLabel(event.event_type)}</td><td className="px-4 py-3">{getWhatsAppWebhookProcessingStatusLabel(event.processing_status)}</td><td className="px-4 py-3">{event.duplicate ? "Si" : "No"}</td><td className="px-4 py-3">{event.phone_number_id_masked ?? "No disponible"}</td><td className="px-4 py-3 text-right"><Button onClick={() => setSelectedEvent(event)} size="sm" variant="ghost">Ver</Button></td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="grid gap-3 lg:hidden">
          {events.map((event) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={event.id}>
              <div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-ink-900">{getWhatsAppWebhookEventTypeLabel(event.event_type)}</p><p className="text-sm text-ink-500">{formatDateTime(event.received_at)}</p></div><Badge label={getWhatsAppWebhookProcessingStatusLabel(event.processing_status)} tone={event.processing_status === "failed" ? "danger" : event.processing_status === "duplicate" ? "neutral" : "info"} /></div>
              <div className="mt-3 grid gap-2 text-sm text-ink-600"><Info label="Duplicado" value={event.duplicate ? "Si" : "No"} /><Info label="Firma" value={event.signature_valid ? "Valida" : "No validada"} /><Info label="Telefono" value={event.phone_number_id_masked ?? "No disponible"} /></div>
              <Button className="mt-3" onClick={() => setSelectedEvent(event)} size="sm" variant="secondary">Ver detalle</Button>
            </article>
          ))}
        </div>
      </Panel>

      {templateForm ? (
        <TemplateDialog
          form={templateForm}
          isSaving={templateSaving}
          onChange={setTemplateForm}
          onClose={() => setTemplateForm(null)}
          onSave={saveTemplate}
        />
      ) : null}
      {consentFormOpen ? (
        <ConsentCorrectionDialog
          form={consentForm}
          isSaving={correctionSaving}
          onChange={setConsentForm}
          onClose={() => setConsentFormOpen(false)}
          onSave={saveConsentCorrection}
        />
      ) : null}
      {selectedEvent ? <EventDetailDialog event={selectedEvent} onClose={() => setSelectedEvent(null)} /> : null}
    </div>
  );
}

function Panel({ children, title }: { children: ReactNode; title: string }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-4"><h4 className="text-sm font-semibold text-ink-900">{title}</h4><div className="mt-3">{children}</div></section>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs font-semibold uppercase text-ink-500">{label}</p><p className="mt-1 break-words text-sm text-ink-800">{value}</p></div>;
}

function templateToForm(template: WhatsAppTemplate): TemplateFormState {
  return {
    id: template.id,
    name: template.name,
    language: template.language,
    purpose: template.purpose,
    variables: template.components_schema.variables?.map((item) => item.key) ?? [],
  };
}

function maskId(value?: string | null): string {
  if (!value) return "No configurado";
  if (value.length <= 4) return "****";
  return `${value.slice(0, 2)}***${value.slice(-2)}`;
}

function TemplateDialog({ form, isSaving, onChange, onClose, onSave }: { form: TemplateFormState; isSaving: boolean; onChange: (form: TemplateFormState) => void; onClose: () => void; onSave: () => void }) {
  useEscape(onClose);
  const toggleVariable = (key: WhatsAppTemplateVariable["key"]) => {
    onChange({
      ...form,
      variables: form.variables.includes(key) ? form.variables.filter((item) => item !== key) : [...form.variables, key],
    });
  };
  return (
    <Dialog title={form.id ? "Editar plantilla local" : "Crear plantilla local"} onClose={onClose}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="wa-template-name" label="Nombre tecnico">
          <Input id="wa-template-name" value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} placeholder="appointment_confirmation_cl" />
        </Field>
        <Field id="wa-template-language" label="Idioma">
          <Input id="wa-template-language" value={form.language} onChange={(event) => onChange({ ...form, language: event.target.value })} placeholder="es_CL" />
        </Field>
        <Field id="wa-template-purpose" label="Proposito">
          <Select id="wa-template-purpose" value={form.purpose} onChange={(event) => onChange({ ...form, purpose: event.target.value as WhatsAppTemplatePurpose })}>
            {TEMPLATE_PURPOSES.map((purpose) => <option key={purpose} value={purpose}>{getWhatsAppTemplatePurposeLabel(purpose)}</option>)}
          </Select>
        </Field>
        <div>
          <Label>Categoria</Label>
          <p className="mt-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-ink-600">Utility</p>
        </div>
      </div>
      <div className="mt-4">
        <Label>Variables permitidas</Label>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {TEMPLATE_VARIABLES.map((key) => (
            <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm font-semibold text-ink-700" key={key}>
              <input checked={form.variables.includes(key)} onChange={() => toggleVariable(key)} type="checkbox" />
              {whatsappVariableLabels[key] ?? key}
            </label>
          ))}
        </div>
      </div>
      <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button onClick={onClose} variant="secondary">Cancelar</Button>
        <Button disabled={!form.name.trim()} isLoading={isSaving} onClick={onSave}>{form.id ? "Guardar" : "Crear"}</Button>
      </div>
    </Dialog>
  );
}

function ConsentCorrectionDialog({ form, isSaving, onChange, onClose, onSave }: { form: ConsentCorrectionState; isSaving: boolean; onChange: (form: ConsentCorrectionState) => void; onClose: () => void; onSave: () => void }) {
  useEscape(onClose);
  return (
    <Dialog title="Correccion administrativa de consentimiento" onClose={onClose}>
      <p className="text-sm leading-6 text-ink-500">Usa esta accion solo para corregir un consentimiento ya verificado fuera de la aplicacion. No ingreses datos sensibles en el motivo.</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Field id="wa-consent-user" label="ID usuario">
          <Input id="wa-consent-user" min={1} type="number" value={form.user_id} onChange={(event) => onChange({ ...form, user_id: event.target.value })} />
        </Field>
        <Field id="wa-consent-phone" label="Telefono">
          <Input id="wa-consent-phone" value={form.phone} onChange={(event) => onChange({ ...form, phone: event.target.value })} placeholder="+56912345678" />
        </Field>
        <Field id="wa-consent-purpose" label="Proposito">
          <Select id="wa-consent-purpose" value={form.purpose} onChange={(event) => onChange({ ...form, purpose: event.target.value as WhatsAppConsentPurpose })}>
            {CONSENT_PURPOSES.map((purpose) => <option key={purpose} value={purpose}>{getWhatsAppConsentPurposeLabel(purpose)}</option>)}
          </Select>
        </Field>
        <Field id="wa-consent-version" label="Version texto">
          <Input id="wa-consent-version" value={form.consent_text_version} onChange={(event) => onChange({ ...form, consent_text_version: event.target.value })} />
        </Field>
        <Field id="wa-consent-reason" label="Motivo">
          <Input id="wa-consent-reason" value={form.reason} onChange={(event) => onChange({ ...form, reason: event.target.value })} placeholder="Correccion solicitada por soporte" />
        </Field>
        <label className="flex items-center gap-2 text-sm font-semibold text-ink-700 sm:pt-7">
          <input checked={form.explicit_confirmation} onChange={(event) => onChange({ ...form, explicit_confirmation: event.target.checked })} type="checkbox" />
          Confirmo que existe respaldo del consentimiento
        </label>
      </div>
      <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button onClick={onClose} variant="secondary">Cancelar</Button>
        <Button disabled={!form.user_id || !form.phone.trim() || !form.reason.trim() || !form.explicit_confirmation} isLoading={isSaving} onClick={onSave}>Registrar correccion</Button>
      </div>
    </Dialog>
  );
}

function EventDetailDialog({ event, onClose }: { event: WhatsAppWebhookEvent; onClose: () => void }) {
  useEscape(onClose);
  const metadata = Object.entries(event.safe_metadata ?? {}).slice(0, 8);
  return (
    <Dialog title="Detalle seguro de evento webhook" onClose={onClose}>
      <div className="grid gap-3 text-sm text-ink-600 sm:grid-cols-2">
        <Info label="Tipo" value={getWhatsAppWebhookEventTypeLabel(event.event_type)} />
        <Info label="Procesamiento" value={getWhatsAppWebhookProcessingStatusLabel(event.processing_status)} />
        <Info label="Recibido" value={formatDateTime(event.received_at)} />
        <Info label="Ocurrido" value={event.occurred_at ? formatDateTime(event.occurred_at) : "No informado"} />
        <Info label="Firma" value={event.signature_valid ? "Valida" : "No validada"} />
        <Info label="Duplicado" value={event.duplicate ? `Si (${event.received_count})` : "No"} />
        <Info label="Mensaje externo" value={event.external_message_id_partial ?? "No disponible"} />
        <Info label="Payload" value={event.payload_hash_partial} />
      </div>
      {event.error_message ? <p className="mt-4 rounded-md border border-danger-100 bg-danger-50 p-3 text-sm text-danger-700">{event.error_message}</p> : null}
      <div className="mt-4">
        <p className="text-sm font-semibold text-ink-900">Metadata segura</p>
        {metadata.length === 0 ? <p className="mt-2 text-sm text-ink-500">Sin metadata adicional.</p> : null}
        <div className="mt-2 grid gap-2">
          {metadata.map(([key, value]) => <Info key={key} label={key} value={Array.isArray(value) ? value.join(", ") : String(value)} />)}
        </div>
      </div>
    </Dialog>
  );
}

function Dialog({ children, onClose, title }: { children: ReactNode; onClose: () => void; title: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end bg-ink-900/40 p-3 sm:items-center sm:justify-center" role="dialog" aria-modal="true" aria-labelledby="whatsapp-dialog-title">
      <div className="max-h-[92vh] w-full overflow-y-auto rounded-lg bg-white p-5 shadow-xl sm:max-w-2xl">
        <div className="flex items-start justify-between gap-4">
          <h2 id="whatsapp-dialog-title" className="text-lg font-semibold text-ink-900">{title}</h2>
          <Button onClick={onClose} variant="ghost">Cerrar</Button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}

function Field({ children, id, label }: { children: ReactNode; id: string; label: string }) {
  return <div className="space-y-1"><Label htmlFor={id}>{label}</Label>{children}</div>;
}

function useEscape(onClose: () => void) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);
}
