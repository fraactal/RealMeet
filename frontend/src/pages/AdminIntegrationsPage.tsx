import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createGoogleOAuthAuthorizationUrl,
  createGoogleMeetMeeting,
  createGoogleDocsAutomationRule,
  createGoogleDocsTemplate,
  createGoogleSheetsExport,
  createAdminIntegration,
  createN8nWorkflow,
  createWebhookSubscription,
  createWhatsAppConsentCorrection,
  createWhatsAppTemplate,
  cancelAppointmentNotification,
  cancelGoogleMeetMeeting,
  disableAdminIntegration,
  disableN8nWorkflow,
  disableWebhookSubscription,
  disconnectGoogleOAuth,
  disableGoogleWorkspaceService,
  disableGoogleDocsAutomationRule,
  disableGoogleDocsTemplate,
  enableAdminIntegration,
  enableGoogleWorkspaceService,
  enableGoogleDocsAutomationRule,
  enableGoogleDocsTemplate,
  enableN8nWorkflow,
  enableWebhookSubscription,
  fetchAutomationExample,
  fetchAutomationExamples,
  fetchAdminIntegrationExecutions,
  fetchAdminIntegrations,
  fetchN8nWorkflows,
  fetchWebhookDeliveries,
  fetchWebhookSubscriptions,
  fetchGoogleOAuthStatus,
  fetchGoogleDocsAutomationExecutions,
  fetchGoogleDocsAutomationRules,
  fetchGoogleDocsTemplates,
  fetchGoogleDocsVariables,
  fetchGoogleSheetsExportExecutions,
  fetchGoogleSheetsExports,
  fetchGoogleWorkspaceStatus,
  fetchWhatsAppConsents,
  fetchWhatsAppNotificationPolicy,
  fetchWhatsAppStatus,
  fetchWhatsAppTemplates,
  fetchWhatsAppWebhookEvents,
  fetchWhatsAppWebhookStatus,
  fetchWhatsAppMessages,
  fetchAppointmentNotifications,
  healthCheckAdminIntegration,
  healthCheckGoogleWorkspace,
  healthCheckGoogleWorkspaceService,
  healthCheckWhatsApp,
  refreshGoogleOAuth,
  retryWhatsAppMessage,
  retryAppointmentNotification,
  retryWebhookDelivery,
  reconcileAppointmentNotification,
  reconcileGoogleDocsAutomationExecution,
  retryGoogleSheetsExportExecution,
  retryGoogleDocsAutomationExecution,
  sendWhatsAppMessage,
  startGoogleWorkspaceOAuth,
  testAdminIntegration,
  testGoogleDocsAutomationRule,
  testN8nWorkflow,
  testWebhookSubscription,
  updateAdminIntegration,
  updateGoogleDocsTemplate,
  updateGoogleDocsAutomationRule,
  updateGoogleSheetsExport,
  updateWebhookSubscription,
  updateWhatsAppNotificationPolicy,
  updateWhatsAppTemplate,
  syncWhatsAppTemplates,
  validateAdminIntegration,
  validateGoogleDocsTemplate,
  validateGoogleSheetsExport,
  validateWhatsAppConfiguration,
  runGoogleSheetsExport,
} from "../api/queries";
import { WhatsAppFoundationPanel } from "../components/admin/integrations/WhatsAppFoundationPanel";
import { Badge, Button, EmptyState, ErrorState, Input, Label, LoadingState, PageHeader, SectionCard, Select } from "../components/ui";
import type {
  Integration,
  AutomationExample,
  AutomationExampleDetail,
  IntegrationConfig,
  IntegrationCreatePayload,
  IntegrationExecution,
  IntegrationExecutionStatus,
  IntegrationOperationResult,
  IntegrationProvider,
  IntegrationStatus,
  IntegrationType,
  IntegrationUpdatePayload,
  WebhookDelivery,
  WebhookDeliveryStatus,
  WebhookEventType,
  WebhookSubscription,
  WebhookSubscriptionWrite,
  N8nWorkflow,
  N8nWorkflowWrite,
  GoogleOAuthStatus,
  GoogleSheetsExportConfig,
  GoogleSheetsExportConfigWrite,
  GoogleSheetsExportExecution,
  GoogleSheetsExportMode,
  GoogleSheetsExportValidation,
  GoogleDocsDocumentType,
  DocumentAutomationEmailRecipientPolicy,
  DocumentAutomationExecution,
  DocumentAutomationEventType,
  GoogleDocsAutomationRule,
  GoogleDocsAutomationRuleWrite,
  GoogleDocsSharingPolicy,
  GoogleDocsTemplate,
  GoogleDocsTemplateVariable,
  GoogleDocsTemplateValidation,
  GoogleDocsTemplateWrite,
  GoogleWorkspaceServiceKey,
  GoogleWorkspaceStatus,
  GoogleMeetMeeting,
  GoogleMeetMeetingCreatePayload,
  WhatsAppConsentCorrectionPayload,
  WhatsAppMessageSendPayload,
  WhatsAppNotificationPolicy,
  WhatsAppNotificationPolicyValue,
  WhatsAppTemplateWrite,
  WhatsAppValidationResult,
} from "../types";
import { formatDateTime } from "../utils/dates";
import {
  getIntegrationExecutionStatusLabel,
  getIntegrationProviderLabel,
  getIntegrationStatusLabel,
  getIntegrationTypeLabel,
  getWebhookDeliveryStatusLabel,
  getWebhookEventTypeLabel,
} from "../utils/labels";

const INTEGRATION_TYPES: IntegrationType[] = ["meeting", "calendar", "messaging", "email", "automation", "webhook", "payment"];
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
  "mercado_pago",
];
const INTEGRATION_STATUSES: IntegrationStatus[] = ["not_configured", "configured", "healthy", "error", "unsupported"];
const SUPPORTED_PROVIDERS: IntegrationProvider[] = ["mock", "mercado_pago"];
const CONFIGURABLE_PROVIDERS: IntegrationProvider[] = ["mock", "google_meet", "whatsapp_cloud", "generic_webhook", "n8n", "mercado_pago"];
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
  calendar_id: string;
  default_timezone: string;
  send_updates: "none" | "all" | "externalOnly";
  appointment_policy: "mock_only" | "google_preferred" | "google_required" | "disabled";
  include_appointment_attendees: boolean;
  waba_id: string;
  phone_number_id: string;
  display_phone_number_masked: string;
  graph_api_version: string;
  default_language: string;
  country_code: string;
  whatsapp_access_token_ref: string;
  whatsapp_app_secret_ref: string;
  whatsapp_verify_token_ref: string;
  whatsapp_phone_hmac_key_ref: string;
  notification_policy: WhatsAppNotificationPolicyValue;
  reminder_enabled: boolean;
  reminder_minutes_before: number;
  n8n_base_url: string;
  n8n_environment: string;
  mercado_pago_environment: "sandbox" | "production";
  mercado_pago_access_token_ref: string;
  mercado_pago_webhook_secret_ref: string;
  mercado_pago_notification_url: string;
  mercado_pago_success_url: string;
  mercado_pago_pending_url: string;
  mercado_pago_failure_url: string;
}

const emptyForm: FormState = {
  name: "",
  integration_type: "automation",
  provider: "mock",
  secret_reference: "",
  simulate_error: false,
  health: "healthy",
  response_delay_ms: 0,
  calendar_id: "primary",
  default_timezone: "America/Santiago",
  send_updates: "none",
  appointment_policy: "mock_only",
  include_appointment_attendees: false,
  waba_id: "",
  phone_number_id: "",
  display_phone_number_masked: "",
  graph_api_version: "v20.0",
  default_language: "es_CL",
  country_code: "CL",
  whatsapp_access_token_ref: "",
  whatsapp_app_secret_ref: "",
  whatsapp_verify_token_ref: "",
  whatsapp_phone_hmac_key_ref: "",
  notification_policy: "email_only",
  reminder_enabled: true,
  reminder_minutes_before: 1440,
  n8n_base_url: "https://automation.example.com",
  n8n_environment: "staging",
  mercado_pago_environment: "sandbox",
  mercado_pago_access_token_ref: "",
  mercado_pago_webhook_secret_ref: "",
  mercado_pago_notification_url: "http://localhost:18000/api/v1/webhooks/mercado-pago",
  mercado_pago_success_url: "http://localhost:15173/payments/success",
  mercado_pago_pending_url: "http://localhost:15173/payments/pending",
  mercado_pago_failure_url: "http://localhost:15173/payments/failure",
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
  const [googleMeetingResult, setGoogleMeetingResult] = useState<GoogleMeetMeeting | null>(null);
  const [selectedSheetsExportId, setSelectedSheetsExportId] = useState<number | null>(null);
  const [googleSheetsValidation, setGoogleSheetsValidation] = useState<GoogleSheetsExportValidation | null>(null);
  const [googleSheetsExecution, setGoogleSheetsExecution] = useState<GoogleSheetsExportExecution | null>(null);
  const [selectedDocsTemplateId, setSelectedDocsTemplateId] = useState<number | null>(null);
  const [googleDocsValidation, setGoogleDocsValidation] = useState<GoogleDocsTemplateValidation | null>(null);
  const [selectedAutomationRuleId, setSelectedAutomationRuleId] = useState<number | null>(null);
  const [automationTestAppointmentId, setAutomationTestAppointmentId] = useState("");
  const [whatsappValidationResult, setWhatsappValidationResult] = useState<WhatsAppValidationResult | null>(null);

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
  const googleOAuthStatusQuery = useQuery({
    queryKey: ["admin-google-oauth-status", selectedIntegration?.id],
    queryFn: () => fetchGoogleOAuthStatus(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const googleWorkspaceQuery = useQuery({
    queryKey: ["admin-google-workspace", selectedIntegration?.id],
    queryFn: () => fetchGoogleWorkspaceStatus(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const googleSheetsExportsQuery = useQuery({
    queryKey: ["admin-google-sheets-exports", selectedIntegration?.id],
    queryFn: () => fetchGoogleSheetsExports(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const selectedSheetsExport = useMemo(
    () => googleSheetsExportsQuery.data?.find((item) => item.id === selectedSheetsExportId) ?? googleSheetsExportsQuery.data?.[0] ?? null,
    [googleSheetsExportsQuery.data, selectedSheetsExportId],
  );
  const googleSheetsExecutionsQuery = useQuery({
    queryKey: ["admin-google-sheets-export-executions", selectedIntegration?.id, selectedSheetsExport?.id],
    queryFn: () => fetchGoogleSheetsExportExecutions(selectedIntegration?.id ?? 0, selectedSheetsExport?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet" && Boolean(selectedSheetsExport?.id),
  });
  const googleDocsTemplatesQuery = useQuery({
    queryKey: ["admin-google-docs-templates", selectedIntegration?.id],
    queryFn: () => fetchGoogleDocsTemplates(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const googleDocsVariablesQuery = useQuery({
    queryKey: ["admin-google-docs-variables", selectedIntegration?.id],
    queryFn: () => fetchGoogleDocsVariables(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const selectedDocsTemplate = useMemo(
    () => googleDocsTemplatesQuery.data?.find((item) => item.id === selectedDocsTemplateId) ?? googleDocsTemplatesQuery.data?.[0] ?? null,
    [googleDocsTemplatesQuery.data, selectedDocsTemplateId],
  );
  const googleDocsAutomationRulesQuery = useQuery({
    queryKey: ["admin-google-docs-automation-rules", selectedIntegration?.id],
    queryFn: () => fetchGoogleDocsAutomationRules(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const selectedAutomationRule = useMemo(
    () => googleDocsAutomationRulesQuery.data?.find((item) => item.id === selectedAutomationRuleId) ?? googleDocsAutomationRulesQuery.data?.[0] ?? null,
    [googleDocsAutomationRulesQuery.data, selectedAutomationRuleId],
  );
  const googleDocsAutomationExecutionsQuery = useQuery({
    queryKey: ["admin-google-docs-automation-executions", selectedIntegration?.id],
    queryFn: () => fetchGoogleDocsAutomationExecutions(selectedIntegration?.id ?? 0),
    enabled: selectedIntegration?.provider === "google_meet",
  });
  const whatsappEnabled = selectedIntegration?.provider === "whatsapp_cloud";
  const whatsappStatusQuery = useQuery({
    queryKey: ["admin-whatsapp-status", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppStatus(selectedIntegration?.id ?? 0),
    enabled: whatsappEnabled,
  });
  const whatsappWebhookStatusQuery = useQuery({
    queryKey: ["admin-whatsapp-webhook-status", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppWebhookStatus(selectedIntegration?.id ?? 0),
    enabled: whatsappEnabled,
  });
  const whatsappWebhookEventsQuery = useQuery({
    queryKey: ["admin-whatsapp-webhook-events", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppWebhookEvents(selectedIntegration?.id ?? 0, { limit: 20 }),
    enabled: whatsappEnabled,
  });
  const whatsappTemplatesQuery = useQuery({
    queryKey: ["admin-whatsapp-templates", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppTemplates(selectedIntegration?.id ?? 0),
    enabled: whatsappEnabled,
  });
  const whatsappConsentsQuery = useQuery({
    queryKey: ["admin-whatsapp-consents"],
    queryFn: () => fetchWhatsAppConsents(),
    enabled: whatsappEnabled,
  });
  const whatsappMessagesQuery = useQuery({
    queryKey: ["admin-whatsapp-messages", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppMessages(selectedIntegration?.id ?? 0),
    enabled: whatsappEnabled,
  });
  const whatsappPolicyQuery = useQuery({
    queryKey: ["admin-whatsapp-notification-policy", selectedIntegration?.id],
    queryFn: () => fetchWhatsAppNotificationPolicy(selectedIntegration?.id ?? 0),
    enabled: whatsappEnabled,
  });
  const appointmentNotificationsQuery = useQuery({
    queryKey: ["admin-appointment-notifications", selectedIntegration?.id],
    queryFn: () => fetchAppointmentNotifications({ limit: 50 }),
    enabled: whatsappEnabled,
  });
  const webhookSubscriptionsQuery = useQuery({
    queryKey: ["admin-webhook-subscriptions"],
    queryFn: fetchWebhookSubscriptions,
  });
  const webhookDeliveriesQuery = useQuery({
    queryKey: ["admin-webhook-deliveries"],
    queryFn: () => fetchWebhookDeliveries({ limit: 30 }),
  });
  const automationExamplesQuery = useQuery({
    queryKey: ["admin-automation-examples"],
    queryFn: fetchAutomationExamples,
  });
  const n8nEnabled = selectedIntegration?.provider === "n8n";
  const n8nWorkflowsQuery = useQuery({
    queryKey: ["admin-n8n-workflows", selectedIntegration?.id],
    queryFn: () => fetchN8nWorkflows(selectedIntegration?.id ?? 0),
    enabled: n8nEnabled,
  });

  const refreshIntegrations = () => {
    void queryClient.invalidateQueries({ queryKey: ["admin-integrations"] });
    if (selectedIntegration?.id) {
      void queryClient.invalidateQueries({ queryKey: ["admin-integration-executions", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-oauth-status", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-workspace", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-sheets-exports", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-sheets-export-executions", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-docs-templates", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-docs-variables", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-docs-automation-rules", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-google-docs-automation-executions", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-status", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-webhook-status", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-webhook-events", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-templates", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-consents"] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-messages", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-whatsapp-notification-policy", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-appointment-notifications", selectedIntegration.id] });
      void queryClient.invalidateQueries({ queryKey: ["admin-n8n-workflows", selectedIntegration.id] });
    }
    void queryClient.invalidateQueries({ queryKey: ["admin-webhook-subscriptions"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-webhook-deliveries"] });
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
  const googleAuthorizeMutation = useMutation({
    mutationFn: (id: number) => createGoogleOAuthAuthorizationUrl(id),
    onSuccess: (result) => {
      window.location.assign(result.authorization_url);
    },
  });
  const googleRefreshMutation = useMutation({
    mutationFn: (id: number) => refreshGoogleOAuth(id),
    onSuccess: () => refreshIntegrations(),
  });
  const googleDisconnectMutation = useMutation({
    mutationFn: (id: number) => disconnectGoogleOAuth(id),
    onSuccess: () => refreshIntegrations(),
  });
  const googleWorkspaceOAuthMutation = useMutation({
    mutationFn: ({ id, services }: { id: number; services: GoogleWorkspaceServiceKey[] }) => startGoogleWorkspaceOAuth(id, { services }),
    onSuccess: (result) => {
      window.location.assign(result.authorization_url);
    },
  });
  const googleWorkspaceHealthMutation = useMutation({
    mutationFn: (id: number) => healthCheckGoogleWorkspace(id),
    onSuccess: () => refreshIntegrations(),
  });
  const googleWorkspaceServiceHealthMutation = useMutation({
    mutationFn: ({ id, service }: { id: number; service: GoogleWorkspaceServiceKey }) => healthCheckGoogleWorkspaceService(id, service),
    onSuccess: () => refreshIntegrations(),
  });
  const googleWorkspaceEnableMutation = useMutation({
    mutationFn: ({ id, service }: { id: number; service: GoogleWorkspaceServiceKey }) => enableGoogleWorkspaceService(id, service),
    onSuccess: () => refreshIntegrations(),
  });
  const googleWorkspaceDisableMutation = useMutation({
    mutationFn: ({ id, service }: { id: number; service: GoogleWorkspaceServiceKey }) => disableGoogleWorkspaceService(id, service),
    onSuccess: () => refreshIntegrations(),
  });
  const createGoogleSheetsExportMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GoogleSheetsExportConfigWrite }) => createGoogleSheetsExport(id, payload),
    onSuccess: (item) => {
      setSelectedSheetsExportId(item.id);
      refreshIntegrations();
    },
  });
  const updateGoogleSheetsExportMutation = useMutation({
    mutationFn: ({ id, configId, payload }: { id: number; configId: number; payload: Partial<GoogleSheetsExportConfigWrite> }) => updateGoogleSheetsExport(id, configId, payload),
    onSuccess: (item) => {
      setSelectedSheetsExportId(item.id);
      refreshIntegrations();
    },
  });
  const validateGoogleSheetsExportMutation = useMutation({
    mutationFn: ({ id, configId }: { id: number; configId: number }) => validateGoogleSheetsExport(id, configId),
    onSuccess: (result) => {
      setGoogleSheetsValidation(result);
      refreshIntegrations();
    },
  });
  const runGoogleSheetsExportMutation = useMutation({
    mutationFn: ({ id, configId, payload }: { id: number; configId: number; payload: Parameters<typeof runGoogleSheetsExport>[2] }) => runGoogleSheetsExport(id, configId, payload),
    onSuccess: (result) => {
      setGoogleSheetsExecution(result);
      refreshIntegrations();
    },
  });
  const retryGoogleSheetsExportMutation = useMutation({
    mutationFn: ({ id, configId, executionId }: { id: number; configId: number; executionId: number }) => retryGoogleSheetsExportExecution(id, configId, executionId),
    onSuccess: (result) => {
      setGoogleSheetsExecution(result);
      refreshIntegrations();
    },
  });
  const createGoogleDocsTemplateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GoogleDocsTemplateWrite }) => createGoogleDocsTemplate(id, payload),
    onSuccess: (item) => {
      setSelectedDocsTemplateId(item.id);
      refreshIntegrations();
    },
  });
  const updateGoogleDocsTemplateMutation = useMutation({
    mutationFn: ({ id, templateId, payload }: { id: number; templateId: number; payload: Partial<GoogleDocsTemplateWrite> }) => updateGoogleDocsTemplate(id, templateId, payload),
    onSuccess: (item) => {
      setSelectedDocsTemplateId(item.id);
      refreshIntegrations();
    },
  });
  const validateGoogleDocsTemplateMutation = useMutation({
    mutationFn: ({ id, templateId }: { id: number; templateId: number }) => validateGoogleDocsTemplate(id, templateId),
    onSuccess: (result) => {
      setGoogleDocsValidation(result);
      refreshIntegrations();
    },
  });
  const enableGoogleDocsTemplateMutation = useMutation({
    mutationFn: ({ id, templateId }: { id: number; templateId: number }) => enableGoogleDocsTemplate(id, templateId),
    onSuccess: () => refreshIntegrations(),
  });
  const disableGoogleDocsTemplateMutation = useMutation({
    mutationFn: ({ id, templateId }: { id: number; templateId: number }) => disableGoogleDocsTemplate(id, templateId),
    onSuccess: () => refreshIntegrations(),
  });
  const createGoogleDocsAutomationRuleMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GoogleDocsAutomationRuleWrite }) => createGoogleDocsAutomationRule(id, payload),
    onSuccess: (item) => {
      setSelectedAutomationRuleId(item.id);
      refreshIntegrations();
    },
  });
  const updateGoogleDocsAutomationRuleMutation = useMutation({
    mutationFn: ({ id, ruleId, payload }: { id: number; ruleId: number; payload: Partial<GoogleDocsAutomationRuleWrite> }) => updateGoogleDocsAutomationRule(id, ruleId, payload),
    onSuccess: (item) => {
      setSelectedAutomationRuleId(item.id);
      refreshIntegrations();
    },
  });
  const enableGoogleDocsAutomationRuleMutation = useMutation({
    mutationFn: ({ id, ruleId }: { id: number; ruleId: number }) => enableGoogleDocsAutomationRule(id, ruleId),
    onSuccess: () => refreshIntegrations(),
  });
  const disableGoogleDocsAutomationRuleMutation = useMutation({
    mutationFn: ({ id, ruleId }: { id: number; ruleId: number }) => disableGoogleDocsAutomationRule(id, ruleId),
    onSuccess: () => refreshIntegrations(),
  });
  const testGoogleDocsAutomationRuleMutation = useMutation({
    mutationFn: ({ id, ruleId, appointmentId }: { id: number; ruleId: number; appointmentId: number }) =>
      testGoogleDocsAutomationRule(id, ruleId, { appointment_id: appointmentId, event_id: `manual:${ruleId}:${appointmentId}` }),
    onSuccess: () => refreshIntegrations(),
  });
  const retryGoogleDocsAutomationExecutionMutation = useMutation({
    mutationFn: ({ id, executionId }: { id: number; executionId: number }) => retryGoogleDocsAutomationExecution(id, executionId),
    onSuccess: () => refreshIntegrations(),
  });
  const reconcileGoogleDocsAutomationExecutionMutation = useMutation({
    mutationFn: ({ id, executionId }: { id: number; executionId: number }) => reconcileGoogleDocsAutomationExecution(id, executionId),
    onSuccess: () => refreshIntegrations(),
  });
  const createGoogleMeetingMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: GoogleMeetMeetingCreatePayload }) => createGoogleMeetMeeting(id, payload),
    onSuccess: (result) => {
      setGoogleMeetingResult(result);
      refreshIntegrations();
    },
  });
  const cancelGoogleMeetingMutation = useMutation({
    mutationFn: ({ id, externalEventId }: { id: number; externalEventId: string }) =>
      cancelGoogleMeetMeeting(id, externalEventId, { idempotency_key: `meeting:test:cancel:${externalEventId}:${Date.now()}`, send_updates: "none" }),
    onSuccess: (result) => {
      setGoogleMeetingResult(result);
      refreshIntegrations();
    },
  });
  const whatsappValidateMutation = useMutation({
    mutationFn: (id: number) => validateWhatsAppConfiguration(id),
    onSuccess: (result) => {
      setWhatsappValidationResult(result);
      refreshIntegrations();
    },
  });
  const createWhatsAppTemplateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Required<WhatsAppTemplateWrite> }) => createWhatsAppTemplate(id, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const updateWhatsAppTemplateMutation = useMutation({
    mutationFn: ({ id, templateId, payload }: { id: number; templateId: number; payload: WhatsAppTemplateWrite }) => updateWhatsAppTemplate(id, templateId, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const createWhatsAppConsentCorrectionMutation = useMutation({
    mutationFn: (payload: WhatsAppConsentCorrectionPayload) => createWhatsAppConsentCorrection(payload),
    onSuccess: () => refreshIntegrations(),
  });
  const whatsappHealthMutation = useMutation({
    mutationFn: (id: number) => healthCheckWhatsApp(id),
    onSuccess: () => refreshIntegrations(),
  });
  const whatsappSyncTemplatesMutation = useMutation({
    mutationFn: (id: number) => syncWhatsAppTemplates(id),
    onSuccess: () => refreshIntegrations(),
  });
  const whatsappSendMessageMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: WhatsAppMessageSendPayload }) => sendWhatsAppMessage(id, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const whatsappRetryMessageMutation = useMutation({
    mutationFn: ({ id, messageId }: { id: number; messageId: number }) => retryWhatsAppMessage(id, messageId),
    onSuccess: () => refreshIntegrations(),
  });
  const whatsappPolicyMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: WhatsAppNotificationPolicy }) => updateWhatsAppNotificationPolicy(id, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const retryNotificationMutation = useMutation({
    mutationFn: (notificationId: number) => retryAppointmentNotification(notificationId),
    onSuccess: () => refreshIntegrations(),
  });
  const reconcileNotificationMutation = useMutation({
    mutationFn: (notificationId: number) => reconcileAppointmentNotification(notificationId),
    onSuccess: () => refreshIntegrations(),
  });
  const cancelNotificationMutation = useMutation({
    mutationFn: (notificationId: number) => cancelAppointmentNotification(notificationId),
    onSuccess: () => refreshIntegrations(),
  });
  const createWebhookSubscriptionMutation = useMutation({
    mutationFn: (payload: WebhookSubscriptionWrite) => createWebhookSubscription(payload),
    onSuccess: () => refreshIntegrations(),
  });
  const updateWebhookSubscriptionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<WebhookSubscriptionWrite> }) => updateWebhookSubscription(id, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const enableWebhookSubscriptionMutation = useMutation({
    mutationFn: (id: number) => enableWebhookSubscription(id),
    onSuccess: () => refreshIntegrations(),
  });
  const disableWebhookSubscriptionMutation = useMutation({
    mutationFn: (id: number) => disableWebhookSubscription(id),
    onSuccess: () => refreshIntegrations(),
  });
  const testWebhookSubscriptionMutation = useMutation({
    mutationFn: (id: number) => testWebhookSubscription(id),
    onSuccess: () => refreshIntegrations(),
  });
  const retryWebhookDeliveryMutation = useMutation({
    mutationFn: (id: number) => retryWebhookDelivery(id),
    onSuccess: () => refreshIntegrations(),
  });
  const createN8nWorkflowMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: N8nWorkflowWrite }) => createN8nWorkflow(id, payload),
    onSuccess: () => refreshIntegrations(),
  });
  const enableN8nWorkflowMutation = useMutation({
    mutationFn: ({ id, workflowId }: { id: number; workflowId: number }) => enableN8nWorkflow(id, workflowId),
    onSuccess: () => refreshIntegrations(),
  });
  const disableN8nWorkflowMutation = useMutation({
    mutationFn: ({ id, workflowId }: { id: number; workflowId: number }) => disableN8nWorkflow(id, workflowId),
    onSuccess: () => refreshIntegrations(),
  });
  const testN8nWorkflowMutation = useMutation({
    mutationFn: ({ id, workflowId }: { id: number; workflowId: number }) => testN8nWorkflow(id, workflowId),
    onSuccess: () => refreshIntegrations(),
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
      calendar_id: integration.config.calendar_id ?? "primary",
      default_timezone: integration.config.default_timezone ?? "America/Santiago",
      send_updates: integration.config.send_updates ?? "none",
      appointment_policy: integration.config.appointment_policy ?? "mock_only",
      include_appointment_attendees: integration.config.include_appointment_attendees ?? false,
      waba_id: integration.config.waba_id ?? "",
      phone_number_id: integration.config.phone_number_id ?? "",
      display_phone_number_masked: integration.config.display_phone_number_masked ?? "",
      graph_api_version: integration.config.graph_api_version ?? "v20.0",
      default_language: integration.config.default_language ?? "es_CL",
      country_code: integration.config.country_code ?? "CL",
      whatsapp_access_token_ref: integration.config.secret_references?.access_token ?? "",
      whatsapp_app_secret_ref: integration.config.secret_references?.app_secret ?? "",
      whatsapp_verify_token_ref: integration.config.secret_references?.verify_token ?? "",
      whatsapp_phone_hmac_key_ref: integration.config.secret_references?.phone_hmac_key ?? "",
      notification_policy: integration.config.notification_policy ?? "email_only",
      reminder_enabled: integration.config.reminder_enabled ?? true,
      reminder_minutes_before: integration.config.reminder_minutes_before ?? 1440,
      n8n_base_url: integration.config.base_url ?? "https://automation.example.com",
      n8n_environment: integration.config.environment ?? "staging",
      mercado_pago_environment: integration.config.environment === "production" ? "production" : "sandbox",
      mercado_pago_access_token_ref: integration.config.access_token_reference ?? "",
      mercado_pago_webhook_secret_ref: integration.config.webhook_secret_reference ?? "",
      mercado_pago_notification_url: integration.config.notification_url ?? "http://localhost:18000/api/v1/webhooks/mercado-pago",
      mercado_pago_success_url: integration.config.success_url ?? "http://localhost:15173/payments/success",
      mercado_pago_pending_url: integration.config.pending_url ?? "http://localhost:15173/payments/pending",
      mercado_pago_failure_url: integration.config.failure_url ?? "http://localhost:15173/payments/failure",
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
    getMutationError(testMutation.error) ??
    getMutationError(googleAuthorizeMutation.error) ??
    getMutationError(googleRefreshMutation.error) ??
    getMutationError(googleDisconnectMutation.error) ??
    getMutationError(createGoogleMeetingMutation.error) ??
    getMutationError(cancelGoogleMeetingMutation.error) ??
    getMutationError(whatsappValidateMutation.error) ??
    getMutationError(createWhatsAppTemplateMutation.error) ??
    getMutationError(updateWhatsAppTemplateMutation.error) ??
    getMutationError(createWhatsAppConsentCorrectionMutation.error) ??
    getMutationError(whatsappHealthMutation.error) ??
    getMutationError(whatsappSyncTemplatesMutation.error) ??
    getMutationError(whatsappSendMessageMutation.error) ??
    getMutationError(whatsappRetryMessageMutation.error) ??
    getMutationError(whatsappPolicyMutation.error) ??
    getMutationError(retryNotificationMutation.error) ??
    getMutationError(reconcileNotificationMutation.error) ??
    getMutationError(cancelNotificationMutation.error) ??
    getMutationError(createWebhookSubscriptionMutation.error) ??
    getMutationError(updateWebhookSubscriptionMutation.error) ??
    getMutationError(enableWebhookSubscriptionMutation.error) ??
    getMutationError(disableWebhookSubscriptionMutation.error) ??
    getMutationError(testWebhookSubscriptionMutation.error) ??
    getMutationError(retryWebhookDeliveryMutation.error) ??
    getMutationError(createN8nWorkflowMutation.error) ??
    getMutationError(enableN8nWorkflowMutation.error) ??
    getMutationError(disableN8nWorkflowMutation.error) ??
    getMutationError(testN8nWorkflowMutation.error);

  return (
    <div className="space-y-6">
      <PageHeader title="Integraciones" description="Gestiona la base administrativa para proveedores externos futuros y pruebas mock internas." />

      <SectionCard
        title="Integraciones configuradas"
        description="Mock esta disponible para pruebas internas. Google Meet queda en preparacion OAuth y no crea reuniones reales en esta etapa."
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
              {selectedIntegration.provider === "google_meet" ? (
                <p className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-600">Conexion Google en preparacion. La autorizacion OAuth queda lista para 12.2, pero RealMeet todavia no crea reuniones reales.</p>
              ) : null}
              {selectedIntegration.provider === "whatsapp_cloud" ? (
                <p className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-600">WhatsApp queda preparado para configuracion, webhooks, plantillas y consentimiento. El envio real se habilitara en un submodulo posterior.</p>
              ) : null}
              {!isSupportedProvider(selectedIntegration.provider) && selectedIntegration.provider !== "google_meet" && selectedIntegration.provider !== "whatsapp_cloud" && selectedIntegration.provider !== "n8n" ? (
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
              {selectedIntegration.provider === "google_meet" ? (
                <GoogleOAuthPanel
                  integration={selectedIntegration}
                  isAuthorizing={googleAuthorizeMutation.isPending}
                  isDisconnecting={googleDisconnectMutation.isPending}
                  isRefreshing={googleRefreshMutation.isPending}
                  onAuthorize={() => googleAuthorizeMutation.mutate(selectedIntegration.id)}
                  onDisconnect={() => window.confirm("Se desconectara localmente la cuenta Google. La integracion se conserva y no se borran ejecuciones.") && googleDisconnectMutation.mutate(selectedIntegration.id)}
                  onRefresh={() => googleRefreshMutation.mutate(selectedIntegration.id)}
                  onEnableGoogle={() => enableMutation.mutate(selectedIntegration.id)}
                  onHealthCheck={() => healthMutation.mutate(selectedIntegration.id)}
                  onCreateMeeting={(payload) => createGoogleMeetingMutation.mutate({ id: selectedIntegration.id, payload })}
                  onCancelMeeting={(externalEventId) => window.confirm("Se cancelara el evento real en Google Calendar si existe. Esta accion no afecta reservas.") && cancelGoogleMeetingMutation.mutate({ id: selectedIntegration.id, externalEventId })}
                  meetingResult={googleMeetingResult}
                  meetingBusy={createGoogleMeetingMutation.isPending || cancelGoogleMeetingMutation.isPending}
                  status={googleOAuthStatusQuery.data}
                  statusLoading={googleOAuthStatusQuery.isLoading}
                />
              ) : null}
              {selectedIntegration.provider === "google_meet" ? (
                <GoogleWorkspacePanel
                  busy={
                    googleWorkspaceOAuthMutation.isPending ||
                    googleWorkspaceHealthMutation.isPending ||
                    googleWorkspaceServiceHealthMutation.isPending ||
                    googleWorkspaceEnableMutation.isPending ||
                    googleWorkspaceDisableMutation.isPending ||
                    createGoogleSheetsExportMutation.isPending ||
                    updateGoogleSheetsExportMutation.isPending ||
                    validateGoogleSheetsExportMutation.isPending ||
                    runGoogleSheetsExportMutation.isPending ||
                    retryGoogleSheetsExportMutation.isPending
                    || createGoogleDocsTemplateMutation.isPending
                    || updateGoogleDocsTemplateMutation.isPending
                    || validateGoogleDocsTemplateMutation.isPending
                    || enableGoogleDocsTemplateMutation.isPending
                    || disableGoogleDocsTemplateMutation.isPending
                    || createGoogleDocsAutomationRuleMutation.isPending
                    || updateGoogleDocsAutomationRuleMutation.isPending
                    || enableGoogleDocsAutomationRuleMutation.isPending
                    || disableGoogleDocsAutomationRuleMutation.isPending
                    || testGoogleDocsAutomationRuleMutation.isPending
                    || retryGoogleDocsAutomationExecutionMutation.isPending
                    || reconcileGoogleDocsAutomationExecutionMutation.isPending
                  }
                  automationExecutions={googleDocsAutomationExecutionsQuery.data ?? []}
                  automationRules={googleDocsAutomationRulesQuery.data ?? []}
                  automationTestAppointmentId={automationTestAppointmentId}
                  docsTemplates={googleDocsTemplatesQuery.data ?? []}
                  docsVariables={googleDocsVariablesQuery.data ?? []}
                  exports={googleSheetsExportsQuery.data ?? []}
                  executions={googleSheetsExecutionsQuery.data ?? []}
                  loading={googleWorkspaceQuery.isLoading}
                  onAuthorize={(services) => googleWorkspaceOAuthMutation.mutate({ id: selectedIntegration.id, services })}
                  onCreateExport={(payload) => createGoogleSheetsExportMutation.mutate({ id: selectedIntegration.id, payload })}
                  onCreateAutomationRule={(payload) => createGoogleDocsAutomationRuleMutation.mutate({ id: selectedIntegration.id, payload })}
                  onCreateTemplate={(payload) => createGoogleDocsTemplateMutation.mutate({ id: selectedIntegration.id, payload })}
                  onDisableAutomationRule={(ruleId) => disableGoogleDocsAutomationRuleMutation.mutate({ id: selectedIntegration.id, ruleId })}
                  onDisableService={(service) => googleWorkspaceDisableMutation.mutate({ id: selectedIntegration.id, service })}
                  onDisableTemplate={(templateId) => disableGoogleDocsTemplateMutation.mutate({ id: selectedIntegration.id, templateId })}
                  onEnableService={(service) => googleWorkspaceEnableMutation.mutate({ id: selectedIntegration.id, service })}
                  onEnableAutomationRule={(ruleId) => enableGoogleDocsAutomationRuleMutation.mutate({ id: selectedIntegration.id, ruleId })}
                  onEnableTemplate={(templateId) => enableGoogleDocsTemplateMutation.mutate({ id: selectedIntegration.id, templateId })}
                  onHealthAll={() => googleWorkspaceHealthMutation.mutate(selectedIntegration.id)}
                  onHealthService={(service) => googleWorkspaceServiceHealthMutation.mutate({ id: selectedIntegration.id, service })}
                  onRetryExport={(executionId) => selectedSheetsExport && retryGoogleSheetsExportMutation.mutate({ id: selectedIntegration.id, configId: selectedSheetsExport.id, executionId })}
                  onRetryAutomationExecution={(executionId) => retryGoogleDocsAutomationExecutionMutation.mutate({ id: selectedIntegration.id, executionId })}
                  onRunExport={(configId, payload) => runGoogleSheetsExportMutation.mutate({ id: selectedIntegration.id, configId, payload })}
                  onAutomationTestAppointmentIdChange={setAutomationTestAppointmentId}
                  onReconcileAutomationExecution={(executionId) => reconcileGoogleDocsAutomationExecutionMutation.mutate({ id: selectedIntegration.id, executionId })}
                  onSelectExport={setSelectedSheetsExportId}
                  onSelectAutomationRule={setSelectedAutomationRuleId}
                  onSelectTemplate={setSelectedDocsTemplateId}
                  onTestAutomationRule={(ruleId, appointmentId) => testGoogleDocsAutomationRuleMutation.mutate({ id: selectedIntegration.id, ruleId, appointmentId })}
                  onUpdateTemplate={(templateId, payload) => updateGoogleDocsTemplateMutation.mutate({ id: selectedIntegration.id, templateId, payload })}
                  onUpdateAutomationRule={(ruleId, payload) => updateGoogleDocsAutomationRuleMutation.mutate({ id: selectedIntegration.id, ruleId, payload })}
                  onUpdateExport={(configId, payload) => updateGoogleSheetsExportMutation.mutate({ id: selectedIntegration.id, configId, payload })}
                  onValidateTemplate={(templateId) => validateGoogleDocsTemplateMutation.mutate({ id: selectedIntegration.id, templateId })}
                  onValidateExport={(configId) => validateGoogleSheetsExportMutation.mutate({ id: selectedIntegration.id, configId })}
                  selectedExport={selectedSheetsExport}
                  selectedAutomationRule={selectedAutomationRule}
                  selectedTemplate={selectedDocsTemplate}
                  status={googleWorkspaceQuery.data}
                  validation={googleSheetsValidation}
                  docsValidation={googleDocsValidation}
                  lastExecution={googleSheetsExecution}
                />
              ) : null}
              {selectedIntegration.provider === "whatsapp_cloud" ? (
                <WhatsAppFoundationPanel
                  integration={selectedIntegration}
                  status={whatsappStatusQuery.data}
                  webhookStatus={whatsappWebhookStatusQuery.data}
                  templates={whatsappTemplatesQuery.data ?? []}
                  consents={whatsappConsentsQuery.data ?? []}
                  events={whatsappWebhookEventsQuery.data ?? []}
                  messages={whatsappMessagesQuery.data ?? []}
                  notificationPolicy={whatsappPolicyQuery.data}
                  appointmentNotifications={appointmentNotificationsQuery.data ?? []}
                  loading={whatsappStatusQuery.isLoading || whatsappWebhookStatusQuery.isLoading || whatsappTemplatesQuery.isLoading || whatsappConsentsQuery.isLoading || whatsappWebhookEventsQuery.isLoading || whatsappMessagesQuery.isLoading || whatsappPolicyQuery.isLoading || appointmentNotificationsQuery.isLoading}
                  error={whatsappStatusQuery.isError || whatsappWebhookStatusQuery.isError || whatsappTemplatesQuery.isError || whatsappConsentsQuery.isError || whatsappWebhookEventsQuery.isError || whatsappMessagesQuery.isError || whatsappPolicyQuery.isError || appointmentNotificationsQuery.isError}
                  validationResult={whatsappValidationResult}
                  validating={whatsappValidateMutation.isPending}
                  templateSaving={createWhatsAppTemplateMutation.isPending || updateWhatsAppTemplateMutation.isPending}
                  correctionSaving={createWhatsAppConsentCorrectionMutation.isPending}
                  healthBusy={whatsappHealthMutation.isPending}
                  syncBusy={whatsappSyncTemplatesMutation.isPending}
                  sendBusy={whatsappSendMessageMutation.isPending}
                  retryBusy={whatsappRetryMessageMutation.isPending}
                  policySaving={whatsappPolicyMutation.isPending}
                  notificationBusy={retryNotificationMutation.isPending || reconcileNotificationMutation.isPending || cancelNotificationMutation.isPending}
                  onValidate={() => whatsappValidateMutation.mutate(selectedIntegration.id)}
                  onHealthCheck={() => whatsappHealthMutation.mutate(selectedIntegration.id)}
                  onSyncTemplates={() => whatsappSyncTemplatesMutation.mutate(selectedIntegration.id)}
                  onCreateTemplate={(payload) => createWhatsAppTemplateMutation.mutate({ id: selectedIntegration.id, payload })}
                  onUpdateTemplate={(templateId, payload) => updateWhatsAppTemplateMutation.mutate({ id: selectedIntegration.id, templateId, payload })}
                  onCreateConsentCorrection={(payload) => createWhatsAppConsentCorrectionMutation.mutate(payload)}
                  onSendMessage={(payload) => whatsappSendMessageMutation.mutate({ id: selectedIntegration.id, payload })}
                  onRetryMessage={(messageId) => whatsappRetryMessageMutation.mutate({ id: selectedIntegration.id, messageId })}
                  onUpdateNotificationPolicy={(payload) => whatsappPolicyMutation.mutate({ id: selectedIntegration.id, payload })}
                  onRetryNotification={(notificationId) => retryNotificationMutation.mutate(notificationId)}
                  onReconcileNotification={(notificationId) => reconcileNotificationMutation.mutate(notificationId)}
                  onCancelNotification={(notificationId) => cancelNotificationMutation.mutate(notificationId)}
                  onRefresh={refreshIntegrations}
                />
              ) : null}
              {selectedIntegration.provider === "n8n" ? (
                <N8nWorkflowPanel
                  integration={selectedIntegration}
                  workflows={n8nWorkflowsQuery.data ?? []}
                  deliveries={webhookDeliveriesQuery.data ?? []}
                  loading={n8nWorkflowsQuery.isLoading}
                  busy={createN8nWorkflowMutation.isPending || enableN8nWorkflowMutation.isPending || disableN8nWorkflowMutation.isPending || testN8nWorkflowMutation.isPending}
                  onCreate={(payload) => createN8nWorkflowMutation.mutate({ id: selectedIntegration.id, payload })}
                  onEnable={(workflowId) => enableN8nWorkflowMutation.mutate({ id: selectedIntegration.id, workflowId })}
                  onDisable={(workflowId) => disableN8nWorkflowMutation.mutate({ id: selectedIntegration.id, workflowId })}
                  onTest={(workflowId) => testN8nWorkflowMutation.mutate({ id: selectedIntegration.id, workflowId })}
                />
              ) : null}
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

      <OutboundWebhooksPanel
        integrations={integrationsQuery.data?.items ?? []}
        subscriptions={webhookSubscriptionsQuery.data ?? []}
        deliveries={webhookDeliveriesQuery.data ?? []}
        loading={webhookSubscriptionsQuery.isLoading || webhookDeliveriesQuery.isLoading}
        busy={
          createWebhookSubscriptionMutation.isPending ||
          updateWebhookSubscriptionMutation.isPending ||
          enableWebhookSubscriptionMutation.isPending ||
          disableWebhookSubscriptionMutation.isPending ||
          testWebhookSubscriptionMutation.isPending ||
          retryWebhookDeliveryMutation.isPending
        }
        onCreate={(payload) => createWebhookSubscriptionMutation.mutate(payload)}
        onEnable={(id) => enableWebhookSubscriptionMutation.mutate(id)}
        onDisable={(id) => disableWebhookSubscriptionMutation.mutate(id)}
        onTest={(id) => testWebhookSubscriptionMutation.mutate(id)}
        onRetry={(id) => retryWebhookDeliveryMutation.mutate(id)}
      />

      <AutomationExamplesPanel examples={automationExamplesQuery.data ?? []} loading={automationExamplesQuery.isLoading} />

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
  if (form.provider === "google_meet") {
    return {
      calendar_id: form.calendar_id || "primary",
      default_timezone: form.default_timezone || "America/Santiago",
      send_updates: form.send_updates,
      appointment_policy: form.appointment_policy,
      fallback_provider: "mock",
      include_appointment_attendees: form.include_appointment_attendees,
    };
  }
  if (form.provider === "whatsapp_cloud") {
    return {
      waba_id: form.waba_id.trim(),
      phone_number_id: form.phone_number_id.trim(),
      display_phone_number_masked: form.display_phone_number_masked.trim(),
      graph_api_version: form.graph_api_version.trim() || "v20.0",
      default_language: form.default_language.trim() || "es_CL",
      country_code: form.country_code.trim().toUpperCase() || "CL",
      secret_references: {
        access_token: form.whatsapp_access_token_ref.trim() || null,
        app_secret: form.whatsapp_app_secret_ref.trim() || null,
        verify_token: form.whatsapp_verify_token_ref.trim() || null,
        phone_hmac_key: form.whatsapp_phone_hmac_key_ref.trim() || null,
      },
      notification_policy: form.notification_policy,
      fallback_channel: "email",
      reminder_enabled: form.reminder_enabled,
      reminder_minutes_before: Number(form.reminder_minutes_before) || 1440,
    };
  }
  if (form.provider === "n8n") {
    return {
      base_url: form.n8n_base_url.trim(),
      environment: form.n8n_environment.trim() || "staging",
    };
  }
  if (form.provider === "mercado_pago") {
    return {
      environment: form.mercado_pago_environment,
      country: "CL",
      currency: "CLP",
      notification_url: form.mercado_pago_notification_url.trim(),
      success_url: form.mercado_pago_success_url.trim(),
      pending_url: form.mercado_pago_pending_url.trim(),
      failure_url: form.mercado_pago_failure_url.trim(),
      auto_return: "approved",
      access_token_reference: form.mercado_pago_access_token_ref.trim(),
      webhook_secret_reference: form.mercado_pago_webhook_secret_ref.trim(),
    };
  }
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

function isConfigurableProvider(provider: IntegrationProvider): boolean {
  return CONFIGURABLE_PROVIDERS.includes(provider);
}

function providerStageText(provider: IntegrationProvider): string {
  if (provider === "mock") return "Disponible para pruebas";
  if (provider === "google_meet") return "Disponible para OAuth y reservas segun politica";
  if (provider === "whatsapp_cloud") return "Mensajeria transaccional segun consentimiento";
  if (provider === "generic_webhook") return "Disponible como contenedor de webhooks salientes";
  if (provider === "n8n") return "Disponible para workflows n8n firmados";
  if (provider === "mercado_pago") return "Checkout Pro sandbox mediante referencias secretas";
  return "Proximamente";
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
        <p className="mt-1 text-xs text-ink-500">{providerStageText(integration.provider)}</p>
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
      {supported || integration.provider === "google_meet" || integration.provider === "n8n" ? <Button isLoading={loading} onClick={onValidate} size="sm" variant="secondary">Validar</Button> : <Button disabled size="sm" title="Proveedor aun no soportado" variant="secondary">Proximamente</Button>}
      {supported && !integration.enabled ? <Button isLoading={loading} onClick={() => window.confirm("La integracion comenzara a estar disponible para operaciones futuras. En este modulo solo mock tiene ejecucion real.") && onEnable()} size="sm">Habilitar</Button> : null}
      {supported && integration.enabled ? <Button isLoading={loading} onClick={() => window.confirm("La configuracion se conservara, pero la integracion no podra ejecutar pruebas ni chequeos.") && onDisable()} size="sm" variant="secondary">Deshabilitar</Button> : null}
      {integration.provider === "google_meet" ? <Button disabled size="sm" title="Google Meet todavia no crea reuniones reales" variant="secondary">OAuth</Button> : null}
    </div>
  );
}

function GoogleOAuthPanel({
  integration,
  isAuthorizing,
  isDisconnecting,
  isRefreshing,
  onAuthorize,
  onDisconnect,
  onRefresh,
  onEnableGoogle,
  onHealthCheck,
  onCreateMeeting,
  onCancelMeeting,
  meetingResult,
  meetingBusy,
  status,
  statusLoading,
}: {
  integration: Integration;
  isAuthorizing: boolean;
  isDisconnecting: boolean;
  isRefreshing: boolean;
  onAuthorize: () => void;
  onDisconnect: () => void;
  onRefresh: () => void;
  onEnableGoogle: () => void;
  onHealthCheck: () => void;
  onCreateMeeting: (payload: GoogleMeetMeetingCreatePayload) => void;
  onCancelMeeting: (externalEventId: string) => void;
  meetingResult: GoogleMeetMeeting | null;
  meetingBusy: boolean;
  status?: GoogleOAuthStatus;
  statusLoading: boolean;
}) {
  const connected = status?.connected ?? false;
  const start = new Date(Date.now() + 60 * 60 * 1000);
  const end = new Date(Date.now() + 90 * 60 * 1000);
  const [title, setTitle] = useState("Prueba de integracion RealMeet");
  const [startAt, setStartAt] = useState(toDatetimeLocal(start));
  const [endAt, setEndAt] = useState(toDatetimeLocal(end));
  const [timezone, setTimezone] = useState("America/Santiago");
  const [attendees, setAttendees] = useState("");
  const [sendUpdates, setSendUpdates] = useState<"none" | "all" | "externalOnly">("none");
  const [idempotencyKey, setIdempotencyKey] = useState(`meeting:test:${Date.now()}`);
  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Conexion Google OAuth</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">La autorizacion queda preparada, pero RealMeet todavia no crea reuniones reales en este submodulo.</p>
        </div>
        <Badge label={statusLoading ? "Revisando" : getGoogleOAuthStatusLabel(status?.status ?? "not_connected")} tone={connected ? "success" : status?.status === "error" ? "danger" : "warning"} />
      </div>
      <div className="mt-4 grid gap-3 text-sm text-ink-600 sm:grid-cols-2">
        <InfoItem label="Cuenta autorizada" value={status?.external_account_email ?? "Sin cuenta conectada"} />
        <InfoItem label="Expiracion token" value={formatOptionalDate(status?.expires_at)} />
        <InfoItem label="Ultimo refresh" value={formatOptionalDate(status?.last_refresh_at)} />
        <InfoItem label="Scopes" value={status?.scopes?.join(", ") || "Sin scopes conectados"} />
      </div>
      {status?.last_error_message ? <p className="mt-3 rounded-md border border-danger-200 bg-danger-50 p-3 text-sm text-danger-700">{status.last_error_message}</p> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        {!connected ? <Button isLoading={isAuthorizing} onClick={onAuthorize}>Conectar con Google</Button> : null}
        {connected ? <Button isLoading={isRefreshing} onClick={onRefresh} variant="secondary">Refrescar token</Button> : null}
        {connected && !integration.enabled ? <Button onClick={onEnableGoogle}>Habilitar pruebas Google</Button> : null}
        {connected && integration.enabled ? <Button onClick={onHealthCheck} variant="secondary">Health check Google</Button> : null}
        {connected ? <Button isLoading={isDisconnecting} onClick={onDisconnect} variant="secondary">Desconectar</Button> : null}
      </div>
      {connected && integration.enabled ? (
        <div className="mt-5 rounded-lg border border-warning-200 bg-warning-50 p-4">
          <h4 className="font-semibold text-ink-900">Crear reunion de prueba</h4>
          <p className="mt-1 text-sm leading-6 text-ink-600">Esta operacion crea un evento real en la cuenta Google conectada. Todavia no se utiliza automaticamente en las reservas.</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Field id="google-meet-title" label="Titulo">
              <Input id="google-meet-title" value={title} onChange={(event) => setTitle(event.target.value)} />
            </Field>
            <Field id="google-meet-timezone" label="Zona horaria">
              <Input id="google-meet-timezone" value={timezone} onChange={(event) => setTimezone(event.target.value)} />
            </Field>
            <Field id="google-meet-start" label="Inicio">
              <Input id="google-meet-start" type="datetime-local" value={startAt} onChange={(event) => setStartAt(event.target.value)} />
            </Field>
            <Field id="google-meet-end" label="Termino">
              <Input id="google-meet-end" type="datetime-local" value={endAt} onChange={(event) => setEndAt(event.target.value)} />
            </Field>
            <Field id="google-meet-attendees" label="Asistentes opcionales">
              <Input id="google-meet-attendees" value={attendees} onChange={(event) => setAttendees(event.target.value)} placeholder="correo@example.com, otro@example.com" />
            </Field>
            <Field id="google-meet-send-updates" label="Notificaciones Google">
              <Select id="google-meet-send-updates" value={sendUpdates} onChange={(event) => setSendUpdates(event.target.value as "none" | "all" | "externalOnly")}>
                <option value="none">No enviar invitaciones</option>
                <option value="externalOnly">Solo externos</option>
                <option value="all">Enviar a todos</option>
              </Select>
            </Field>
            <Field id="google-meet-idempotency" label="Clave idempotente">
              <Input id="google-meet-idempotency" value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} />
            </Field>
          </div>
          {sendUpdates !== "none" ? <p className="mt-3 text-sm font-semibold text-warning-700">Esta opcion puede enviar invitaciones reales desde Google Calendar.</p> : null}
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              isLoading={meetingBusy}
              onClick={() => {
                if (!window.confirm("Confirmas crear un evento real en la cuenta Google conectada?")) return;
                onCreateMeeting({
                  title,
                  start_at: new Date(startAt).toISOString(),
                  end_at: new Date(endAt).toISOString(),
                  timezone,
                  attendees: attendees.split(",").map((item) => item.trim()).filter(Boolean),
                  idempotency_key: idempotencyKey,
                  send_updates: sendUpdates,
                });
              }}
            >
              Crear reunion de prueba
            </Button>
            {meetingResult?.external_event_id && meetingResult.status !== "cancelled" ? <Button isLoading={meetingBusy} onClick={() => onCancelMeeting(meetingResult.external_event_id)} variant="secondary">Cancelar prueba</Button> : null}
          </div>
          {meetingResult ? (
            <div className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-ink-700">
              <p className="font-semibold">Resultado: {meetingResult.status}</p>
              <p>Evento: {meetingResult.external_event_id}</p>
              {meetingResult.meeting_url ? <a className="text-brand-700 underline" href={meetingResult.meeting_url} rel="noreferrer" target="_blank">Abrir enlace Meet</a> : <p>Meet pendiente o no disponible.</p>}
            </div>
          ) : null}
        </div>
      ) : null}
      <p className="mt-3 text-xs text-ink-500">Integracion #{integration.id}. No se muestran tokens, codigos OAuth ni secretos.</p>
    </div>
  );
}

function GoogleWorkspacePanel({
  status,
  exports,
  selectedExport,
  executions,
  validation,
  lastExecution,
  docsTemplates,
  automationRules,
  selectedAutomationRule,
  automationExecutions,
  automationTestAppointmentId,
  selectedTemplate,
  docsVariables,
  docsValidation,
  loading,
  busy,
  onAuthorize,
  onCreateExport,
  onUpdateExport,
  onValidateExport,
  onRunExport,
  onRetryExport,
  onSelectExport,
  onCreateTemplate,
  onUpdateTemplate,
  onValidateTemplate,
  onEnableTemplate,
  onDisableTemplate,
  onSelectTemplate,
  onCreateAutomationRule,
  onUpdateAutomationRule,
  onEnableAutomationRule,
  onDisableAutomationRule,
  onSelectAutomationRule,
  onTestAutomationRule,
  onRetryAutomationExecution,
  onReconcileAutomationExecution,
  onAutomationTestAppointmentIdChange,
  onEnableService,
  onDisableService,
  onHealthService,
  onHealthAll,
}: {
  status?: GoogleWorkspaceStatus;
  exports: GoogleSheetsExportConfig[];
  selectedExport: GoogleSheetsExportConfig | null;
  executions: GoogleSheetsExportExecution[];
  validation: GoogleSheetsExportValidation | null;
  lastExecution: GoogleSheetsExportExecution | null;
  docsTemplates: GoogleDocsTemplate[];
  automationRules: GoogleDocsAutomationRule[];
  selectedAutomationRule: GoogleDocsAutomationRule | null;
  automationExecutions: DocumentAutomationExecution[];
  automationTestAppointmentId: string;
  selectedTemplate: GoogleDocsTemplate | null;
  docsVariables: GoogleDocsTemplateVariable[];
  docsValidation: GoogleDocsTemplateValidation | null;
  loading: boolean;
  busy: boolean;
  onAuthorize: (services: GoogleWorkspaceServiceKey[]) => void;
  onCreateExport: (payload: GoogleSheetsExportConfigWrite) => void;
  onUpdateExport: (configId: number, payload: Partial<GoogleSheetsExportConfigWrite>) => void;
  onValidateExport: (configId: number) => void;
  onRunExport: (configId: number, payload: { starts_from: string; starts_to: string; include_cancelled?: boolean | null }) => void;
  onRetryExport: (executionId: number) => void;
  onSelectExport: (configId: number | null) => void;
  onCreateTemplate: (payload: GoogleDocsTemplateWrite) => void;
  onUpdateTemplate: (templateId: number, payload: Partial<GoogleDocsTemplateWrite>) => void;
  onValidateTemplate: (templateId: number) => void;
  onEnableTemplate: (templateId: number) => void;
  onDisableTemplate: (templateId: number) => void;
  onSelectTemplate: (templateId: number | null) => void;
  onCreateAutomationRule: (payload: GoogleDocsAutomationRuleWrite) => void;
  onUpdateAutomationRule: (ruleId: number, payload: Partial<GoogleDocsAutomationRuleWrite>) => void;
  onEnableAutomationRule: (ruleId: number) => void;
  onDisableAutomationRule: (ruleId: number) => void;
  onSelectAutomationRule: (ruleId: number | null) => void;
  onTestAutomationRule: (ruleId: number, appointmentId: number) => void;
  onRetryAutomationExecution: (executionId: number) => void;
  onReconcileAutomationExecution: (executionId: number) => void;
  onAutomationTestAppointmentIdChange: (value: string) => void;
  onEnableService: (service: GoogleWorkspaceServiceKey) => void;
  onDisableService: (service: GoogleWorkspaceServiceKey) => void;
  onHealthService: (service: GoogleWorkspaceServiceKey) => void;
  onHealthAll: () => void;
}) {
  if (loading) {
    return <LoadingState label="Cargando permisos Google Workspace" />;
  }
  if (!status) {
    return <ErrorState title="No pudimos cargar Google Workspace" message="Reintenta desde el panel de integraciones." />;
  }
  const servicesNeedingAuth = status.services.filter((service) => service.enabled && !service.authorized).map((service) => service.service);
  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Google Workspace</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">
            Permisos incrementales para Calendar, Meet, Sheets, Drive y Docs. RealMeet reutiliza la misma autorizacion Google y no muestra tokens.
          </p>
        </div>
        <Badge label={status.account.email ? "Cuenta conectada" : "Sin cuenta"} tone={status.account.email ? "success" : "warning"} />
      </div>
      <div className="mt-4 grid gap-3 text-sm text-ink-600 sm:grid-cols-2">
        <InfoItem label="Cuenta" value={status.account.email ?? "Sin cuenta Google conectada"} />
        <InfoItem label="Scopes concedidos" value={status.account.granted_scopes.length ? `${status.account.granted_scopes.length} permisos` : "Sin permisos"} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={servicesNeedingAuth.length === 0} isLoading={busy} onClick={() => onAuthorize(servicesNeedingAuth)}>
          Autorizar permisos pendientes
        </Button>
        <Button isLoading={busy} onClick={onHealthAll} variant="secondary">Health check Workspace</Button>
      </div>
      <p className="mt-3 rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">
        Activar un servicio solo prepara su uso dentro de RealMeet. Sheets, Drive y Docs quedan como base tecnica; la generacion de documentos o exportaciones se implementara despues.
      </p>
      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {status.services.map((service) => {
          const definition = status.catalog.find((item) => item.key === service.service);
          const canHealth = service.enabled && service.authorized && definition?.health_check_supported;
          return (
            <article className="rounded-lg border border-slate-200 bg-slate-50 p-4" key={service.service}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h4 className="font-semibold text-ink-900">{definition?.name ?? getGoogleWorkspaceServiceLabel(service.service)}</h4>
                  <p className="mt-1 text-sm leading-6 text-ink-500">{definition?.description ?? "Servicio Google Workspace."}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge label={getGoogleWorkspaceStatusLabel(service.status)} tone={getGoogleWorkspaceStatusTone(service.status)} />
                  <Badge label={service.enabled ? "Habilitado" : "Deshabilitado"} tone={service.enabled ? "success" : "neutral"} />
                  <Badge label={service.authorized ? "Autorizado" : "Sin permiso"} tone={service.authorized ? "success" : "warning"} />
                </div>
              </div>
              <div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-2">
                <InfoItem label="Ultimo chequeo" value={formatOptionalDate(service.checked_at)} />
                <InfoItem label="Ultimo error" value={service.last_error_code ? getGoogleWorkspaceErrorLabel(service.last_error_code) : "Sin error"} />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {service.enabled ? (
                  <Button isLoading={busy} onClick={() => onDisableService(service.service)} size="sm" variant="secondary">Deshabilitar</Button>
                ) : (
                  <Button isLoading={busy} onClick={() => onEnableService(service.service)} size="sm" variant="secondary">Habilitar</Button>
                )}
                {!service.authorized ? <Button isLoading={busy} onClick={() => onAuthorize([service.service])} size="sm">Autorizar</Button> : null}
                <Button disabled={!canHealth} isLoading={busy} onClick={() => onHealthService(service.service)} size="sm" title={canHealth ? undefined : "Requiere servicio habilitado y autorizado"} variant="secondary">
                  Health check
                </Button>
              </div>
              <p className="mt-3 text-xs text-ink-500">Scopes: {definition?.required_scopes.join(", ") ?? "Sin scopes declarados"}</p>
            </article>
          );
        })}
      </div>
      <GoogleSheetsExportsPanel
        busy={busy}
        executions={executions}
        exports={exports}
        lastExecution={lastExecution}
        onCreate={onCreateExport}
        onRetry={onRetryExport}
        onRun={onRunExport}
        onSelect={onSelectExport}
        onUpdate={onUpdateExport}
        onValidate={onValidateExport}
        selectedExport={selectedExport}
        sheetsReady={Boolean(status.services.find((service) => service.service === "sheets" && service.enabled && service.authorized))}
        validation={validation}
      />
      <GoogleDocsTemplatesPanel
        busy={busy}
        docsReady={Boolean(status.services.find((service) => service.service === "docs" && service.enabled && service.authorized)) && Boolean(status.services.find((service) => service.service === "drive" && service.enabled && service.authorized))}
        onCreate={onCreateTemplate}
        onDisable={onDisableTemplate}
        onEnable={onEnableTemplate}
        onSelect={onSelectTemplate}
        onUpdate={onUpdateTemplate}
        onValidate={onValidateTemplate}
        selectedTemplate={selectedTemplate}
        templates={docsTemplates}
        validation={docsValidation}
        variables={docsVariables}
      />
      <GoogleDocsAutomationPanel
        busy={busy}
        docsReady={Boolean(status.services.find((service) => service.service === "docs" && service.enabled && service.authorized)) && Boolean(status.services.find((service) => service.service === "drive" && service.enabled && service.authorized))}
        executions={automationExecutions}
        onAppointmentIdChange={onAutomationTestAppointmentIdChange}
        onCreate={onCreateAutomationRule}
        onDisable={onDisableAutomationRule}
        onEnable={onEnableAutomationRule}
        onReconcile={onReconcileAutomationExecution}
        onRetry={onRetryAutomationExecution}
        onSelect={onSelectAutomationRule}
        onTest={onTestAutomationRule}
        onUpdate={onUpdateAutomationRule}
        rules={automationRules}
        selectedRule={selectedAutomationRule}
        templates={docsTemplates}
        testAppointmentId={automationTestAppointmentId}
      />
    </div>
  );
}

function GoogleDocsTemplatesPanel({
  templates,
  selectedTemplate,
  variables,
  validation,
  docsReady,
  busy,
  onCreate,
  onUpdate,
  onValidate,
  onEnable,
  onDisable,
  onSelect,
}: {
  templates: GoogleDocsTemplate[];
  selectedTemplate: GoogleDocsTemplate | null;
  variables: GoogleDocsTemplateVariable[];
  validation: GoogleDocsTemplateValidation | null;
  docsReady: boolean;
  busy: boolean;
  onCreate: (payload: GoogleDocsTemplateWrite) => void;
  onUpdate: (templateId: number, payload: Partial<GoogleDocsTemplateWrite>) => void;
  onValidate: (templateId: number) => void;
  onEnable: (templateId: number) => void;
  onDisable: (templateId: number) => void;
  onSelect: (templateId: number | null) => void;
}) {
  const [name, setName] = useState("Plantilla operacional RealMeet");
  const [description, setDescription] = useState("Documento operativo generado desde una reserva.");
  const [documentType, setDocumentType] = useState<GoogleDocsDocumentType>("appointment_summary");
  const [sourceDocumentId, setSourceDocumentId] = useState("");
  const [destinationFolderId, setDestinationFolderId] = useState("");
  const [sharingPolicy, setSharingPolicy] = useState<GoogleDocsSharingPolicy>("private");
  const [allowedVariables, setAllowedVariables] = useState<string[]>(["appointment_id", "appointment_status", "appointment_start", "professional_name", "client_name", "meeting_url", "generated_at"]);
  const active = selectedTemplate;

  useEffect(() => {
    if (!active) return;
    setName(active.name);
    setDescription(active.description ?? "");
    setDocumentType(active.document_type);
    setSourceDocumentId(active.source_document_id);
    setDestinationFolderId(active.destination_folder_id ?? "");
    setSharingPolicy(active.sharing_policy);
    setAllowedVariables(active.allowed_variables);
  }, [active]);

  const payload: GoogleDocsTemplateWrite = {
    name: name.trim(),
    description: description.trim() || null,
    document_type: documentType,
    source_document_id: sourceDocumentId.trim(),
    destination_folder_id: destinationFolderId.trim() || null,
    enabled: true,
    allowed_variables: allowedVariables,
    sharing_policy: sharingPolicy,
  };

  function toggleVariable(key: string) {
    setAllowedVariables((current) => (current.includes(key) ? current.filter((item) => item !== key) : [...current, key]));
  }

  return (
    <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Plantillas Google Docs</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">Registra plantillas operativas y variables permitidas. No se admiten variables clinicas.</p>
        </div>
        <Badge label={docsReady ? "Docs y Drive listos" : "Requiere Docs y Drive"} tone={docsReady ? "success" : "warning"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field id="docs-template-name" label="Nombre"><Input id="docs-template-name" value={name} onChange={(event) => setName(event.target.value)} /></Field>
        <Field id="docs-template-type" label="Tipo"><Select id="docs-template-type" value={documentType} onChange={(event) => setDocumentType(event.target.value as GoogleDocsDocumentType)}><option value="appointment_summary">Resumen de reserva</option><option value="appointment_confirmation">Confirmacion</option><option value="pre_session_instructions">Instrucciones previas</option><option value="post_session_instructions">Instrucciones posteriores</option><option value="administrative_receipt">Comprobante administrativo</option><option value="custom_operational">Operativo personalizado</option></Select></Field>
        <Field id="docs-source-id" label="Documento fuente ID"><Input id="docs-source-id" value={sourceDocumentId} onChange={(event) => setSourceDocumentId(event.target.value)} placeholder="Google Docs ID" /></Field>
        <Field id="docs-folder-id" label="Carpeta destino opcional"><Input id="docs-folder-id" value={destinationFolderId} onChange={(event) => setDestinationFolderId(event.target.value)} placeholder="Google Drive folder ID" /></Field>
        <Field id="docs-sharing-policy" label="Comparticion"><Select id="docs-sharing-policy" value={sharingPolicy} onChange={(event) => setSharingPolicy(event.target.value as GoogleDocsSharingPolicy)}><option value="private">Privado</option><option value="professional_only">Solo profesional</option><option value="professional_and_client">Profesional y cliente</option></Select></Field>
        <Field id="docs-description" label="Descripcion"><Input id="docs-description" value={description} onChange={(event) => setDescription(event.target.value)} /></Field>
      </div>
      <div className="mt-4">
        <p className="mb-2 text-sm font-semibold text-ink-700">Variables permitidas</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {variables.map((variable) => (
            <label className="flex items-start gap-2 rounded-md border border-slate-200 bg-white p-2 text-sm text-ink-700" key={variable.key}>
              <input checked={allowedVariables.includes(variable.key)} onChange={() => toggleVariable(variable.key)} type="checkbox" />
              <span><span className="font-semibold">{variable.placeholder}</span><span className="block text-ink-500">{variable.label}</span></span>
            </label>
          ))}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!docsReady || !payload.name || !payload.source_document_id || allowedVariables.length === 0} isLoading={busy} onClick={() => (active ? onUpdate(active.id, payload) : onCreate(payload))}>{active ? "Guardar plantilla" : "Crear plantilla"}</Button>
        {active ? <Button isLoading={busy} onClick={() => onValidate(active.id)} variant="secondary">Validar plantilla</Button> : null}
        {active && active.enabled ? <Button isLoading={busy} onClick={() => onDisable(active.id)} variant="secondary">Deshabilitar</Button> : null}
        {active && !active.enabled ? <Button isLoading={busy} onClick={() => onEnable(active.id)} variant="secondary">Habilitar</Button> : null}
      </div>
      {templates.length > 0 ? <div className="mt-5 grid gap-2">{templates.map((item) => <button className={`rounded-md border p-3 text-left text-sm ${active?.id === item.id ? "border-brand-300 bg-white" : "border-slate-200 bg-white"}`} key={item.id} onClick={() => onSelect(item.id)} type="button"><span className="font-semibold text-ink-900">{item.name}</span><span className="ml-2 text-ink-500">{item.document_type} · {item.enabled ? "habilitada" : "deshabilitada"}</span></button>)}</div> : null}
      {validation ? <p className="mt-4 rounded-md border border-success-200 bg-success-50 p-3 text-sm text-success-700">Validacion correcta: {validation.document.name ?? "Documento"} · variables: {validation.placeholders.length}</p> : null}
      <p className="mt-4 text-xs text-ink-500">No se muestran ni almacenan contenidos completos, tokens, notas clinicas, diagnosticos ni historial medico.</p>
    </div>
  );
}

function GoogleDocsAutomationPanel({
  templates,
  rules,
  selectedRule,
  executions,
  docsReady,
  busy,
  testAppointmentId,
  onAppointmentIdChange,
  onCreate,
  onUpdate,
  onEnable,
  onDisable,
  onSelect,
  onTest,
  onRetry,
  onReconcile,
}: {
  templates: GoogleDocsTemplate[];
  rules: GoogleDocsAutomationRule[];
  selectedRule: GoogleDocsAutomationRule | null;
  executions: DocumentAutomationExecution[];
  docsReady: boolean;
  busy: boolean;
  testAppointmentId: string;
  onAppointmentIdChange: (value: string) => void;
  onCreate: (payload: GoogleDocsAutomationRuleWrite) => void;
  onUpdate: (ruleId: number, payload: Partial<GoogleDocsAutomationRuleWrite>) => void;
  onEnable: (ruleId: number) => void;
  onDisable: (ruleId: number) => void;
  onSelect: (ruleId: number | null) => void;
  onTest: (ruleId: number, appointmentId: number) => void;
  onRetry: (executionId: number) => void;
  onReconcile: (executionId: number) => void;
}) {
  const enabledTemplates = templates.filter((item) => item.enabled);
  const [name, setName] = useState("Automatizacion documental");
  const [description, setDescription] = useState("Genera documentos operativos desde eventos de reserva.");
  const [templateId, setTemplateId] = useState<number | "">(enabledTemplates[0]?.id ?? "");
  const [eventType, setEventType] = useState<DocumentAutomationEventType>("appointment.created");
  const [sharingPolicy, setSharingPolicy] = useState<GoogleDocsSharingPolicy>("private");
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailPolicy, setEmailPolicy] = useState<DocumentAutomationEmailRecipientPolicy>("none");
  const [n8nEnabled, setN8nEnabled] = useState(false);
  const active = selectedRule;

  useEffect(() => {
    if (!active) return;
    setName(active.name);
    setDescription(active.description ?? "");
    setTemplateId(active.template_id);
    setEventType(active.event_type);
    setSharingPolicy(active.sharing_policy);
    setEmailEnabled(active.email_delivery_enabled);
    setEmailPolicy(active.email_recipient_policy);
    setN8nEnabled(active.n8n_event_enabled);
  }, [active]);

  useEffect(() => {
    if (!templateId && enabledTemplates[0]) setTemplateId(enabledTemplates[0].id);
  }, [enabledTemplates, templateId]);

  const payload: GoogleDocsAutomationRuleWrite = {
    template_id: Number(templateId),
    name: name.trim(),
    description: description.trim() || null,
    event_type: eventType,
    enabled: false,
    sharing_policy: sharingPolicy,
    email_delivery_enabled: emailEnabled,
    email_recipient_policy: emailEnabled ? emailPolicy : "none",
    n8n_event_enabled: n8nEnabled,
  };
  const appointmentId = Number(testAppointmentId);

  return (
    <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Automatizacion documental</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">Reglas sincronas y best-effort para generar documentos no clinicos, enviar email opcional y emitir document.generated.</p>
        </div>
        <Badge label={docsReady ? "Disponible" : "Requiere Docs y Drive"} tone={docsReady ? "success" : "warning"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field id="docs-automation-name" label="Nombre"><Input id="docs-automation-name" value={name} onChange={(event) => setName(event.target.value)} /></Field>
        <Field id="docs-automation-template" label="Plantilla"><Select id="docs-automation-template" value={templateId} onChange={(event) => setTemplateId(Number(event.target.value))}>{enabledTemplates.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Field>
        <Field id="docs-automation-event" label="Evento"><Select id="docs-automation-event" value={eventType} onChange={(event) => setEventType(event.target.value as DocumentAutomationEventType)}><option value="appointment.created">Reserva creada</option><option value="appointment.confirmed">Reserva confirmada</option><option value="appointment.cancelled">Reserva cancelada</option><option value="meeting.ready">Meeting listo</option></Select></Field>
        <Field id="docs-automation-sharing" label="Comparticion"><Select id="docs-automation-sharing" value={sharingPolicy} onChange={(event) => setSharingPolicy(event.target.value as GoogleDocsSharingPolicy)}><option value="private">Privado</option><option value="professional_only">Solo profesional</option><option value="professional_and_client">Profesional y cliente</option></Select></Field>
        <Field id="docs-automation-email-policy" label="Destinatarios email"><Select disabled={!emailEnabled} id="docs-automation-email-policy" value={emailPolicy} onChange={(event) => setEmailPolicy(event.target.value as DocumentAutomationEmailRecipientPolicy)}><option value="none">Sin email</option><option value="professional">Profesional</option><option value="client">Cliente</option><option value="professional_and_client">Profesional y cliente</option></Select></Field>
        <Field id="docs-automation-description" label="Descripcion"><Input id="docs-automation-description" value={description} onChange={(event) => setDescription(event.target.value)} /></Field>
        <label className="flex items-center gap-2 text-sm font-semibold text-ink-700"><input checked={emailEnabled} onChange={(event) => setEmailEnabled(event.target.checked)} type="checkbox" /> Enviar email minimo</label>
        <label className="flex items-center gap-2 text-sm font-semibold text-ink-700"><input checked={n8nEnabled} onChange={(event) => setN8nEnabled(event.target.checked)} type="checkbox" /> Emitir document.generated</label>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!docsReady || !payload.name || !payload.template_id || (payload.email_delivery_enabled && payload.email_recipient_policy === "none")} isLoading={busy} onClick={() => (active ? onUpdate(active.id, payload) : onCreate(payload))}>{active ? "Guardar regla" : "Crear regla"}</Button>
        {active && active.enabled ? <Button isLoading={busy} onClick={() => onDisable(active.id)} variant="secondary">Deshabilitar regla</Button> : null}
        {active && !active.enabled ? <Button isLoading={busy} onClick={() => onEnable(active.id)} variant="secondary">Habilitar regla</Button> : null}
      </div>
      {rules.length ? (
        <div className="mt-5 grid gap-2">
          {rules.map((item) => (
            <button className={`rounded-md border p-3 text-left text-sm ${active?.id === item.id ? "border-brand-300 bg-white" : "border-slate-200 bg-white"}`} key={item.id} onClick={() => onSelect(item.id)} type="button">
              <span className="font-semibold text-ink-900">{item.name}</span>
              <span className="ml-2 text-ink-500">{getDocumentAutomationEventLabel(item.event_type)} · {item.enabled ? "habilitada" : "deshabilitada"}</span>
            </button>
          ))}
        </div>
      ) : <EmptyState title="Sin reglas documentales" description="Crea una regla para automatizar documentos operativos." />}
      {active ? (
        <div className="mt-5 rounded-md border border-slate-200 bg-white p-3">
          <p className="text-sm font-semibold text-ink-900">Prueba manual controlada</p>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <Input aria-label="ID de reserva para prueba" inputMode="numeric" value={testAppointmentId} onChange={(event) => onAppointmentIdChange(event.target.value)} placeholder="ID reserva" />
            <Button disabled={!appointmentId} isLoading={busy} onClick={() => onTest(active.id, appointmentId)} variant="secondary">Ejecutar prueba</Button>
          </div>
        </div>
      ) : null}
      <div className="mt-5">
        <h4 className="text-sm font-semibold text-ink-900">Ejecuciones recientes</h4>
        {executions.length ? (
          <div className="mt-2 grid gap-2">
            {executions.slice(0, 8).map((item) => (
              <article className="rounded-md border border-slate-200 bg-white p-3 text-sm" key={item.id}>
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div><span className="font-semibold text-ink-900">{getDocumentAutomationEventLabel(item.event_type)}</span><span className="ml-2 text-ink-500">Reserva #{item.appointment_id}</span></div>
                  <div className="flex flex-wrap gap-2"><Badge label={getDocumentAutomationStatusLabel(item.status)} tone={getDocumentAutomationStatusTone(item.status)} /><Badge label={`Email: ${getDocumentAutomationEmailLabel(item.email_status)}`} tone="neutral" /><Badge label={`n8n: ${getDocumentAutomationN8nLabel(item.n8n_status)}`} tone="neutral" /></div>
                </div>
                <p className="mt-2 text-xs text-ink-500">{formatOptionalDate(item.finished_at ?? item.started_at ?? item.created_at)} · Documento {item.generated_document_id ? `#${item.generated_document_id}` : "pendiente"}</p>
                {item.error_message ? <p className="mt-2 text-xs text-danger-700">{item.error_message}</p> : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button disabled={!["failed", "partially_succeeded", "reconcile_required"].includes(item.status)} isLoading={busy} onClick={() => onRetry(item.id)} size="sm" variant="secondary">Retry</Button>
                  <Button isLoading={busy} onClick={() => onReconcile(item.id)} size="sm" variant="secondary">Reconcile</Button>
                </div>
              </article>
            ))}
          </div>
        ) : <EmptyState title="Sin ejecuciones documentales" description="Las ejecuciones apareceran cuando una regla procese un evento o una prueba manual." />}
      </div>
      <p className="mt-4 text-xs text-ink-500">Los emails no adjuntan documentos. n8n recibe solo payload minimo, sin contenido documental, tokens ni datos clinicos.</p>
    </div>
  );
}

function GoogleSheetsExportsPanel({
  exports,
  selectedExport,
  executions,
  validation,
  lastExecution,
  sheetsReady,
  busy,
  onCreate,
  onUpdate,
  onValidate,
  onRun,
  onRetry,
  onSelect,
}: {
  exports: GoogleSheetsExportConfig[];
  selectedExport: GoogleSheetsExportConfig | null;
  executions: GoogleSheetsExportExecution[];
  validation: GoogleSheetsExportValidation | null;
  lastExecution: GoogleSheetsExportExecution | null;
  sheetsReady: boolean;
  busy: boolean;
  onCreate: (payload: GoogleSheetsExportConfigWrite) => void;
  onUpdate: (configId: number, payload: Partial<GoogleSheetsExportConfigWrite>) => void;
  onValidate: (configId: number) => void;
  onRun: (configId: number, payload: { starts_from: string; starts_to: string; include_cancelled?: boolean | null }) => void;
  onRetry: (executionId: number) => void;
  onSelect: (configId: number | null) => void;
}) {
  const [name, setName] = useState("Reservas RealMeet");
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [sheetName, setSheetName] = useState("Reservas");
  const [mode, setMode] = useState<GoogleSheetsExportMode>("upsert");
  const [includeCancelled, setIncludeCancelled] = useState(false);
  const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
  const end = new Date(Date.now() + 24 * 60 * 60 * 1000);
  const [startsFrom, setStartsFrom] = useState(toDatetimeLocal(start));
  const [startsTo, setStartsTo] = useState(toDatetimeLocal(end));
  const active = selectedExport;

  useEffect(() => {
    if (!active) return;
    setName(active.name);
    setSpreadsheetId(active.spreadsheet_id);
    setSheetName(active.sheet_name);
    setMode(active.export_mode);
    setIncludeCancelled(active.include_cancelled);
  }, [active]);

  const payload: GoogleSheetsExportConfigWrite = {
    name: name.trim(),
    spreadsheet_id: spreadsheetId.trim(),
    sheet_name: sheetName.trim(),
    enabled: true,
    export_mode: mode,
    include_cancelled: includeCancelled,
  };

  return (
    <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Exportaciones a Google Sheets</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">Exportacion manual de reservas con columnas estandar. RealMeet sigue siendo la fuente de verdad.</p>
        </div>
        <Badge label={sheetsReady ? "Sheets listo" : "Requiere Sheets"} tone={sheetsReady ? "success" : "warning"} />
      </div>
      <p className="mt-3 text-sm text-ink-600">Usa solo el ID del spreadsheet. En una URL de Google Sheets corresponde al texto entre <span className="font-semibold">/d/</span> y <span className="font-semibold">/edit</span>.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field id="sheets-export-name" label="Nombre">
          <Input id="sheets-export-name" value={name} onChange={(event) => setName(event.target.value)} />
        </Field>
        <Field id="sheets-export-spreadsheet" label="Spreadsheet ID">
          <Input id="sheets-export-spreadsheet" value={spreadsheetId} onChange={(event) => setSpreadsheetId(event.target.value)} placeholder="1abcDEFghi_jklMNop" />
        </Field>
        <Field id="sheets-export-sheet" label="Pestana">
          <Input id="sheets-export-sheet" value={sheetName} onChange={(event) => setSheetName(event.target.value)} />
        </Field>
        <Field id="sheets-export-mode" label="Modo">
          <Select id="sheets-export-mode" value={mode} onChange={(event) => setMode(event.target.value as GoogleSheetsExportMode)}>
            <option value="upsert">Actualizar o insertar</option>
            <option value="append_only">Solo agregar nuevas</option>
          </Select>
        </Field>
        <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
          <input checked={includeCancelled} onChange={(event) => setIncludeCancelled(event.target.checked)} type="checkbox" />
          Incluir reservas canceladas
        </label>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={!sheetsReady || !payload.name || !payload.spreadsheet_id || !payload.sheet_name} isLoading={busy} onClick={() => (active ? onUpdate(active.id, payload) : onCreate(payload))}>
          {active ? "Guardar configuracion" : "Crear configuracion"}
        </Button>
        {active ? <Button isLoading={busy} onClick={() => onValidate(active.id)} variant="secondary">Validar acceso</Button> : null}
      </div>
      {exports.length > 0 ? (
        <div className="mt-5 grid gap-2">
          {exports.map((item) => (
            <button className={`rounded-md border p-3 text-left text-sm ${active?.id === item.id ? "border-brand-300 bg-white" : "border-slate-200 bg-white"}`} key={item.id} onClick={() => onSelect(item.id)} type="button">
              <span className="font-semibold text-ink-900">{item.name}</span>
              <span className="ml-2 text-ink-500">{item.sheet_name} · {getGoogleSheetsExportModeLabel(item.export_mode)}</span>
            </button>
          ))}
        </div>
      ) : null}
      {validation ? <p className="mt-4 rounded-md border border-success-200 bg-success-50 p-3 text-sm text-success-700">Validacion correcta: {validation.spreadsheet.title ?? "Spreadsheet"} / {validation.sheet.name ?? "Pestana"} ({validation.headers.status}).</p> : null}
      {active ? (
        <div className="mt-5 rounded-lg border border-slate-200 bg-white p-4">
          <h4 className="font-semibold text-ink-900">Exportacion manual</h4>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Field id="sheets-run-from" label="Desde">
              <Input id="sheets-run-from" type="datetime-local" value={startsFrom} onChange={(event) => setStartsFrom(event.target.value)} />
            </Field>
            <Field id="sheets-run-to" label="Hasta">
              <Input id="sheets-run-to" type="datetime-local" value={startsTo} onChange={(event) => setStartsTo(event.target.value)} />
            </Field>
          </div>
          <Button className="mt-4" isLoading={busy} onClick={() => onRun(active.id, { starts_from: new Date(startsFrom).toISOString(), starts_to: new Date(startsTo).toISOString(), include_cancelled: includeCancelled })}>
            Ejecutar exportacion
          </Button>
          {lastExecution ? <GoogleSheetsExecutionSummary execution={lastExecution} /> : null}
        </div>
      ) : null}
      <div className="mt-5 space-y-3">
        <h4 className="font-semibold text-ink-900">Historial reciente</h4>
        {executions.length === 0 ? <EmptyState title="Sin ejecuciones registradas" /> : null}
        {executions.map((execution) => (
          <article className="rounded-lg border border-slate-200 bg-white p-3 text-sm" key={execution.id}>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-semibold text-ink-900">{getGoogleSheetsExecutionStatusLabel(execution.status)}</p>
                <p className="text-ink-500">{formatOptionalDate(execution.created_at)} · {formatDateTime(execution.range_start)} a {formatDateTime(execution.range_end)}</p>
              </div>
              <Badge label={getGoogleSheetsExecutionStatusLabel(execution.status)} tone={execution.status === "succeeded" ? "success" : execution.status === "failed" ? "danger" : "warning"} />
            </div>
            <GoogleSheetsExecutionSummary execution={execution} compact />
            {execution.status === "failed" || execution.status === "partially_succeeded" ? <Button className="mt-3" isLoading={busy} onClick={() => onRetry(execution.id)} size="sm" variant="secondary">Reintentar</Button> : null}
          </article>
        ))}
      </div>
      <p className="mt-4 text-xs text-ink-500">No se exportan notas, diagnosticos, historial medico, telefonos, tokens ni configuraciones internas.</p>
    </div>
  );
}

function GoogleSheetsExecutionSummary({ execution, compact = false }: { execution: GoogleSheetsExportExecution; compact?: boolean }) {
  return (
    <div className={`grid gap-2 text-sm text-ink-600 ${compact ? "mt-3 sm:grid-cols-5" : "mt-4 sm:grid-cols-5"}`}>
      <InfoItem label="Total" value={String(execution.total_records)} />
      <InfoItem label="Insertadas" value={String(execution.inserted_records)} />
      <InfoItem label="Actualizadas" value={String(execution.updated_records)} />
      <InfoItem label="Omitidas" value={String(execution.skipped_records)} />
      <InfoItem label="Fallidas" value={String(execution.failed_records)} />
      {execution.error_message ? <div className="sm:col-span-5"><InfoItem label="Error" value={execution.error_message} /></div> : null}
    </div>
  );
}

const WEBHOOK_EVENTS: WebhookEventType[] = [
  "appointment.created",
  "appointment.cancelled",
  "appointment.updated",
  "appointment.confirmed",
  "meeting.ready",
  "notification.sent",
  "notification.failed",
  "client.created",
  "professional.created",
];

const N8N_EVENTS: WebhookEventType[] = ["appointment.created", "appointment.cancelled", "meeting.ready", "notification.failed"];

function N8nWorkflowPanel({
  integration,
  workflows,
  deliveries,
  loading,
  busy,
  onCreate,
  onEnable,
  onDisable,
  onTest,
}: {
  integration: Integration;
  workflows: N8nWorkflow[];
  deliveries: WebhookDelivery[];
  loading: boolean;
  busy: boolean;
  onCreate: (payload: N8nWorkflowWrite) => void;
  onEnable: (workflowId: number) => void;
  onDisable: (workflowId: number) => void;
  onTest: (workflowId: number) => void;
}) {
  const [name, setName] = useState("Workflow operativo RealMeet");
  const [description, setDescription] = useState("Recibe eventos operativos firmados desde RealMeet.");
  const [path, setPath] = useState("webhook/realmeet");
  const [secretReference, setSecretReference] = useState("REALMEET_N8N_WEBHOOK_SECRET");
  const [events, setEvents] = useState<WebhookEventType[]>(["appointment.created", "appointment.cancelled"]);

  function toggleEvent(eventType: WebhookEventType) {
    setEvents((current) => (current.includes(eventType) ? current.filter((item) => item !== eventType) : [...current, eventType]));
  }

  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink-900">Workflows n8n</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">RealMeet dispara webhooks firmados. Los workflows se configuran y ejecutan fuera de RealMeet.</p>
        </div>
        <Badge label={integration.config.environment ?? "staging"} tone="info" />
      </div>
      <div className="mt-4 grid gap-3 text-sm text-ink-600 sm:grid-cols-2">
        <InfoItem label="Base URL" value={integration.config.base_url ?? "No configurada"} />
        <InfoItem label="Workflows registrados" value={String(workflows.length)} />
      </div>

      <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <h4 className="font-semibold text-ink-900">Crear workflow</h4>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field id="n8n-workflow-name" label="Nombre">
            <Input id="n8n-workflow-name" value={name} onChange={(event) => setName(event.target.value)} />
          </Field>
          <Field id="n8n-workflow-path" label="Webhook path">
            <Input id="n8n-workflow-path" value={path} onChange={(event) => setPath(event.target.value)} placeholder="webhook/realmeet" />
          </Field>
          <Field id="n8n-workflow-secret" label="Referencia de secreto">
            <Input id="n8n-workflow-secret" value={secretReference} onChange={(event) => setSecretReference(event.target.value)} placeholder="REALMEET_N8N_WEBHOOK_SECRET" />
          </Field>
          <Field id="n8n-workflow-description" label="Descripcion">
            <Input id="n8n-workflow-description" value={description} onChange={(event) => setDescription(event.target.value)} />
          </Field>
        </div>
        <div className="mt-4">
          <p className="mb-2 text-sm font-semibold text-ink-700">Eventos</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {N8N_EVENTS.map((eventType) => (
              <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white p-2 text-sm text-ink-700" key={eventType}>
                <input checked={events.includes(eventType)} onChange={() => toggleEvent(eventType)} type="checkbox" />
                {getWebhookEventTypeLabel(eventType)}
              </label>
            ))}
          </div>
        </div>
        <Button
          className="mt-4"
          disabled={!name.trim() || !path.trim() || !secretReference.trim() || events.length === 0}
          isLoading={busy}
          onClick={() =>
            onCreate({
              name: name.trim(),
              description: description.trim() || null,
              webhook_path: path.trim(),
              event_types: events,
              secret_reference: secretReference.trim(),
            })
          }
        >
          Crear workflow
        </Button>
      </div>

      <div className="mt-5 space-y-3">
        <h4 className="font-semibold text-ink-900">Workflows registrados</h4>
        {loading ? <LoadingState label="Cargando workflows n8n" /> : null}
        {!loading && workflows.length === 0 ? <EmptyState title="No hay workflows n8n registrados" /> : null}
        {workflows.map((workflow) => (
          <article className="rounded-lg border border-slate-200 bg-white p-4" key={workflow.id}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-semibold text-ink-900">{workflow.name}</p>
                <p className="mt-1 text-sm text-ink-500">{workflow.description ?? "Sin descripcion"}</p>
              </div>
              <Badge label={workflow.enabled ? "Habilitado" : "Deshabilitado"} tone={workflow.enabled ? "success" : "neutral"} />
            </div>
            <div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-3">
              <InfoItem label="Path" value={workflow.webhook_path} />
              <InfoItem label="Ultimo exito" value={formatOptionalDate(workflow.last_success_at)} />
              <InfoItem label="Ultimo error" value={workflow.last_error_code ?? "Sin error"} />
            </div>
            <p className="mt-3 text-xs text-ink-500">Eventos: {workflow.event_types.map(getWebhookEventTypeLabel).join(", ")}</p>
            <p className="mt-1 text-xs text-ink-500">Referencia de secreto configurada. El valor no se muestra ni se almacena en RealMeet.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {workflow.enabled ? (
                <Button isLoading={busy} onClick={() => onDisable(workflow.id)} size="sm" variant="secondary">Deshabilitar</Button>
              ) : (
                <Button isLoading={busy} onClick={() => onEnable(workflow.id)} size="sm">Habilitar</Button>
              )}
              <Button disabled={!workflow.enabled} isLoading={busy} onClick={() => onTest(workflow.id)} size="sm" variant="secondary">Probar workflow</Button>
            </div>
            <N8nWorkflowDeliveries deliveries={deliveries.filter((delivery) => delivery.subscription_id === workflow.subscription_id).slice(0, 5)} />
          </article>
        ))}
      </div>
    </div>
  );
}

function N8nWorkflowDeliveries({ deliveries }: { deliveries: WebhookDelivery[] }) {
  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="text-sm font-semibold text-ink-800">Entregas recientes</p>
      {deliveries.length === 0 ? <p className="mt-2 text-sm text-ink-500">Este workflow todavia no registra entregas.</p> : null}
      <div className="mt-2 space-y-2">
        {deliveries.map((delivery) => (
          <div className="grid gap-1 rounded-md bg-white p-2 text-xs text-ink-600 sm:grid-cols-4" key={delivery.id}>
            <span>{getWebhookEventTypeLabel(delivery.event_type)}</span>
            <span>{getWebhookDeliveryStatusLabel(delivery.status)}</span>
            <span>Intento {delivery.attempt}</span>
            <span>{formatOptionalDate(delivery.updated_at)}</span>
            {delivery.error_code ? <span className="sm:col-span-4">Error: {delivery.error_code}</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function AutomationExamplesPanel({ examples, loading }: { examples: AutomationExample[]; loading: boolean }) {
  const [selected, setSelected] = useState<AutomationExampleDetail | null>(null);
  const [error, setError] = useState("");
  const exampleMutation = useMutation({
    mutationFn: (key: string) => fetchAutomationExample(key),
    onSuccess: (detail) => {
      setSelected(detail);
      setError("");
    },
    onError: () => setError("No pudimos obtener el workflow de ejemplo."),
  });

  function downloadWorkflow(detail: AutomationExampleDetail) {
    const blob = new Blob([JSON.stringify(detail.workflow, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = detail.example.workflow_filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <SectionCard title="Ejemplos de automatizacion" description="Workflows n8n importables para casos operativos comunes. Deben importarse y revisarse dentro de n8n.">
      {loading ? <LoadingState label="Cargando ejemplos de automatizacion" /> : null}
      {error ? <ErrorState title={error} /> : null}
      {!loading && examples.length === 0 ? <EmptyState title="No hay ejemplos disponibles" /> : null}
      <div className="grid gap-3 lg:grid-cols-3">
        {examples.map((example) => (
          <article className="rounded-lg border border-slate-200 bg-white p-4" key={example.key}>
            <div className="flex h-full flex-col gap-3">
              <div>
                <h3 className="font-semibold text-ink-900">{example.name}</h3>
                <p className="mt-1 text-sm leading-6 text-ink-500">{example.description}</p>
              </div>
              <div className="space-y-2 text-xs text-ink-600">
                <p><span className="font-semibold">Eventos:</span> {example.recommended_event_types.map(getWebhookEventTypeLabel).join(", ")}</p>
                <p><span className="font-semibold">Credenciales n8n:</span> {example.required_n8n_credentials.join(", ")}</p>
                <p><span className="font-semibold">Archivo:</span> {example.workflow_filename}</p>
              </div>
              <div className="mt-auto flex flex-wrap gap-2">
                <Button isLoading={exampleMutation.isPending} onClick={() => exampleMutation.mutate(example.key)} size="sm" variant="secondary">Ver JSON</Button>
              </div>
            </div>
          </article>
        ))}
      </div>
      {selected ? (
        <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 className="font-semibold text-ink-900">{selected.example.name}</h3>
              <p className="mt-1 text-sm text-ink-500">Importa este JSON en n8n y reemplaza los placeholders antes de habilitarlo.</p>
            </div>
            <Button onClick={() => downloadWorkflow(selected)} size="sm">Descargar JSON</Button>
          </div>
          <pre className="mt-4 max-h-96 overflow-auto rounded-md bg-ink-900 p-3 text-xs text-white">{JSON.stringify(selected.workflow, null, 2)}</pre>
        </div>
      ) : null}
      <p className="mt-4 text-xs leading-5 text-ink-500">Los ejemplos no contienen credenciales y no deben usarse en produccion sin revisar seguridad, autenticacion, permisos y manejo de errores.</p>
    </SectionCard>
  );
}

function OutboundWebhooksPanel({
  integrations,
  subscriptions,
  deliveries,
  loading,
  busy,
  onCreate,
  onEnable,
  onDisable,
  onTest,
  onRetry,
}: {
  integrations: Integration[];
  subscriptions: WebhookSubscription[];
  deliveries: WebhookDelivery[];
  loading: boolean;
  busy: boolean;
  onCreate: (payload: WebhookSubscriptionWrite) => void;
  onEnable: (id: number) => void;
  onDisable: (id: number) => void;
  onTest: (id: number) => void;
  onRetry: (id: number) => void;
}) {
  const webhookIntegrations = integrations.filter((item) => item.provider === "generic_webhook" || item.provider === "n8n");
  const [integrationId, setIntegrationId] = useState("");
  const [name, setName] = useState("Webhook operativo RealMeet");
  const [targetUrl, setTargetUrl] = useState("https://example.com/webhook");
  const [secretReference, setSecretReference] = useState("REALMEET_WEBHOOK_SECRET");
  const [events, setEvents] = useState<WebhookEventType[]>(["appointment.created", "appointment.cancelled"]);

  useEffect(() => {
    if (!integrationId && webhookIntegrations[0]) {
      setIntegrationId(String(webhookIntegrations[0].id));
    }
  }, [integrationId, webhookIntegrations]);

  function toggleEvent(eventType: WebhookEventType) {
    setEvents((current) => (current.includes(eventType) ? current.filter((item) => item !== eventType) : [...current, eventType]));
  }

  return (
    <SectionCard title="Webhooks salientes" description="Emite eventos operativos firmados hacia sistemas externos. n8n y workflows concretos se implementaran en submodulos posteriores.">
      {loading ? <LoadingState label="Cargando webhooks salientes" /> : null}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-base font-semibold text-ink-900">Nueva suscripcion</h3>
          <p className="mt-1 text-sm leading-6 text-ink-500">Usa solo referencias de secretos. RealMeet firma cada payload con HMAC-SHA256.</p>
          {webhookIntegrations.length === 0 ? (
            <p className="mt-4 rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-700">Crea primero una integracion `Webhook generico` o `n8n` como contenedor administrativo.</p>
          ) : (
            <div className="mt-4 grid gap-3">
              <Field id="webhook-integration" label="Integracion contenedora">
                <Select id="webhook-integration" value={integrationId} onChange={(event) => setIntegrationId(event.target.value)}>
                  {webhookIntegrations.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} · {getIntegrationProviderLabel(item.provider)}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field id="webhook-name" label="Nombre">
                <Input id="webhook-name" value={name} onChange={(event) => setName(event.target.value)} />
              </Field>
              <Field id="webhook-url" label="URL destino">
                <Input id="webhook-url" value={targetUrl} onChange={(event) => setTargetUrl(event.target.value)} placeholder="https://example.com/webhook" />
              </Field>
              <Field id="webhook-secret" label="Referencia de secreto">
                <Input id="webhook-secret" value={secretReference} onChange={(event) => setSecretReference(event.target.value)} placeholder="REALMEET_WEBHOOK_SECRET" />
              </Field>
              <div>
                <p className="mb-2 text-sm font-semibold text-ink-700">Eventos</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {WEBHOOK_EVENTS.map((eventType) => (
                    <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white p-2 text-sm text-ink-700" key={eventType}>
                      <input checked={events.includes(eventType)} onChange={() => toggleEvent(eventType)} type="checkbox" />
                      {getWebhookEventTypeLabel(eventType)}
                    </label>
                  ))}
                </div>
              </div>
              <Button
                disabled={!integrationId || !name.trim() || !targetUrl.trim() || !secretReference.trim() || events.length === 0}
                isLoading={busy}
                onClick={() =>
                  onCreate({
                    integration_id: Number(integrationId),
                    name: name.trim(),
                    target_url: targetUrl.trim(),
                    event_types: events,
                    secret_reference: secretReference.trim(),
                  })
                }
              >
                Crear suscripcion
              </Button>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="text-base font-semibold text-ink-900">Suscripciones</h3>
          {subscriptions.length === 0 ? <EmptyState title="No hay suscripciones webhook" description="Crea una suscripcion para probar eventos operativos firmados." /> : null}
          {subscriptions.map((subscription) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={subscription.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink-900">{subscription.name}</p>
                  <p className="mt-1 break-all text-sm text-ink-500">{subscription.target_url}</p>
                </div>
                <Badge label={subscription.enabled ? "Habilitada" : "Deshabilitada"} tone={subscription.enabled ? "success" : "neutral"} />
              </div>
              <p className="mt-3 text-xs text-ink-500">Eventos: {subscription.event_types.map(getWebhookEventTypeLabel).join(", ")}</p>
              <p className="mt-1 text-xs text-ink-500">Secreto: {subscription.secret_reference}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {subscription.enabled ? (
                  <Button isLoading={busy} onClick={() => onDisable(subscription.id)} size="sm" variant="secondary">Deshabilitar</Button>
                ) : (
                  <Button isLoading={busy} onClick={() => onEnable(subscription.id)} size="sm">Habilitar</Button>
                )}
                <Button disabled={!subscription.enabled} isLoading={busy} onClick={() => onTest(subscription.id)} size="sm" variant="secondary">Enviar test</Button>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <h3 className="mb-3 text-base font-semibold text-ink-900">Ultimas entregas</h3>
        {deliveries.length === 0 ? <EmptyState title="Todavia no hay entregas webhook" /> : null}
        <div className="grid gap-3">
          {deliveries.map((delivery) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={delivery.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="font-semibold text-ink-900">{getWebhookEventTypeLabel(delivery.event_type)}</p>
                  <p className="mt-1 text-sm text-ink-500">{formatDateTime(delivery.created_at)} · intento {delivery.attempt}</p>
                </div>
                <WebhookDeliveryBadge status={delivery.status} />
              </div>
              <div className="mt-3 grid gap-2 text-sm text-ink-600 sm:grid-cols-4">
                <InfoItem label="HTTP" value={delivery.response_status ? String(delivery.response_status) : "Sin respuesta"} />
                <InfoItem label="Duracion" value={delivery.duration_ms != null ? `${delivery.duration_ms} ms` : "Sin duracion"} />
                <InfoItem label="Error" value={delivery.error_message ?? delivery.error_code ?? "Sin error"} />
                <InfoItem label="Idempotencia" value={delivery.idempotency_key} />
              </div>
              {delivery.status === "failed" ? <Button className="mt-3" isLoading={busy} onClick={() => onRetry(delivery.id)} size="sm" variant="secondary">Reintentar</Button> : null}
            </article>
          ))}
        </div>
      </div>
    </SectionCard>
  );
}

function WebhookDeliveryBadge({ status }: { status: WebhookDeliveryStatus }) {
  const tone: "success" | "danger" | "info" | "neutral" | "warning" = status === "succeeded" ? "success" : status === "failed" ? "danger" : status === "sending" ? "info" : status === "skipped" ? "neutral" : "warning";
  return <Badge label={getWebhookDeliveryStatusLabel(status)} tone={tone} />;
}

function getGoogleOAuthStatusLabel(status: GoogleOAuthStatus["status"]): string {
  const labels: Record<GoogleOAuthStatus["status"], string> = {
    not_connected: "Sin conectar",
    pending: "Pendiente",
    connected: "Conectada",
    expired: "Expirada",
    revoked: "Revocada",
    error: "Con error",
  };
  return labels[status];
}

function getGoogleWorkspaceServiceLabel(service: GoogleWorkspaceServiceKey): string {
  const labels: Record<GoogleWorkspaceServiceKey, string> = {
    calendar: "Google Calendar",
    meet: "Google Meet",
    sheets: "Google Sheets",
    drive: "Google Drive",
    docs: "Google Docs",
  };
  return labels[service];
}

function getGoogleWorkspaceStatusLabel(status: GoogleWorkspaceStatus["services"][number]["status"]): string {
  const labels: Record<GoogleWorkspaceStatus["services"][number]["status"], string> = {
    healthy: "Saludable",
    authorized_not_resource_tested: "Autorizado sin recurso probado",
    authorization_required: "Requiere autorizacion",
    disabled: "Deshabilitado",
    unavailable: "No disponible",
    error: "Con error",
  };
  return labels[status];
}

function getGoogleWorkspaceStatusTone(status: GoogleWorkspaceStatus["services"][number]["status"]): "success" | "danger" | "info" | "neutral" | "warning" {
  if (status === "healthy" || status === "authorized_not_resource_tested") return "success";
  if (status === "authorization_required") return "warning";
  if (status === "disabled") return "neutral";
  if (status === "unavailable" || status === "error") return "danger";
  return "info";
}

function getGoogleWorkspaceErrorLabel(code: string): string {
  const labels: Record<string, string> = {
    authorization_required: "Falta autorizar permisos",
    google_workspace_unavailable: "Google Workspace no disponible",
    google_drive_unavailable: "Google Drive no disponible",
    google_oauth_not_connected: "Cuenta Google no conectada",
    google_refresh_token_missing: "Falta refresh token",
  };
  return labels[code] ?? "Error controlado";
}

function getGoogleSheetsExportModeLabel(mode: GoogleSheetsExportMode): string {
  return mode === "upsert" ? "Actualizar o insertar" : "Solo agregar nuevas";
}

function getGoogleSheetsExecutionStatusLabel(status: GoogleSheetsExportExecution["status"]): string {
  const labels: Record<GoogleSheetsExportExecution["status"], string> = {
    pending: "Pendiente",
    running: "En ejecucion",
    succeeded: "Exitosa",
    partially_succeeded: "Parcial",
    failed: "Fallida",
  };
  return labels[status];
}

function getDocumentAutomationEventLabel(eventType: DocumentAutomationEventType): string {
  const labels: Record<DocumentAutomationEventType, string> = {
    "appointment.created": "Reserva creada",
    "appointment.confirmed": "Reserva confirmada",
    "appointment.cancelled": "Reserva cancelada",
    "meeting.ready": "Meeting listo",
  };
  return labels[eventType];
}

function getDocumentAutomationStatusLabel(status: DocumentAutomationExecution["status"]): string {
  const labels: Record<DocumentAutomationExecution["status"], string> = {
    pending: "Pendiente",
    running: "En ejecucion",
    succeeded: "Exitosa",
    partially_succeeded: "Parcial",
    failed: "Fallida",
    reconcile_required: "Requiere reconcile",
  };
  return labels[status];
}

function getDocumentAutomationStatusTone(status: DocumentAutomationExecution["status"]): "success" | "danger" | "info" | "neutral" | "warning" {
  if (status === "succeeded") return "success";
  if (status === "failed" || status === "reconcile_required") return "danger";
  if (status === "partially_succeeded") return "warning";
  if (status === "running") return "info";
  return "neutral";
}

function getDocumentAutomationEmailLabel(status: DocumentAutomationExecution["email_status"]): string {
  const labels: Record<DocumentAutomationExecution["email_status"], string> = {
    not_requested: "No solicitado",
    sent: "Enviado",
    failed: "Fallido",
    skipped: "Omitido",
  };
  return labels[status];
}

function getDocumentAutomationN8nLabel(status: DocumentAutomationExecution["n8n_status"]): string {
  const labels: Record<DocumentAutomationExecution["n8n_status"], string> = {
    not_requested: "No solicitado",
    delivered: "Entregado",
    failed: "Fallido",
    skipped: "Omitido",
  };
  return labels[status];
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
            <Select
              id="integration-provider"
              disabled={editing}
              value={form.provider}
              onChange={(event) => {
                const provider = event.target.value as IntegrationProvider;
                onChange({
                  ...form,
                  provider,
                  integration_type:
                    provider === "google_meet"
                      ? "meeting"
                      : provider === "whatsapp_cloud"
                        ? "messaging"
                        : provider === "n8n"
                          ? "automation"
                          : provider === "generic_webhook"
                            ? "webhook"
                            : provider === "mercado_pago"
                              ? "payment"
                              : form.integration_type,
                });
              }}
            >
              {INTEGRATION_PROVIDERS.map((provider) => <option disabled={!isConfigurableProvider(provider)} key={provider} value={provider}>{getIntegrationProviderLabel(provider)}{provider === "google_meet" ? " - OAuth y reservas" : provider === "whatsapp_cloud" ? " - Fundacion sin envio" : provider === "generic_webhook" ? " - Webhooks salientes" : provider === "n8n" ? " - Workflows firmados" : provider === "mercado_pago" ? " - Checkout Pro" : !isConfigurableProvider(provider) ? " - Proximamente" : ""}</option>)}
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
        ) : null}
        {form.provider === "google_meet" ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-ink-900">Politica de reuniones para nuevas reservas</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">Cambiar esta politica afecta nuevas reservas confirmadas. No reprocesa automaticamente reservas anteriores.</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Politica" id="google-policy">
                <Select id="google-policy" value={form.appointment_policy} onChange={(event) => onChange({ ...form, appointment_policy: event.target.value as FormState["appointment_policy"] })}>
                  <option value="mock_only">Solo simulacion</option>
                  <option value="google_preferred">Preferir Google Meet con fallback</option>
                  <option value="google_required">Exigir Google Meet</option>
                  <option value="disabled">No crear reunion automaticamente</option>
                </Select>
              </Field>
              <Field label="Calendar ID" id="google-calendar-id">
                <Input id="google-calendar-id" value={form.calendar_id} onChange={(event) => onChange({ ...form, calendar_id: event.target.value })} />
              </Field>
              <Field label="Zona horaria" id="google-default-timezone">
                <Input id="google-default-timezone" value={form.default_timezone} onChange={(event) => onChange({ ...form, default_timezone: event.target.value })} />
              </Field>
              <Field label="Notificaciones Google" id="google-send-updates-config">
                <Select id="google-send-updates-config" value={form.send_updates} onChange={(event) => onChange({ ...form, send_updates: event.target.value as FormState["send_updates"] })}>
                  <option value="none">No enviar invitaciones</option>
                  <option value="externalOnly">Solo externos</option>
                  <option value="all">Enviar a todos</option>
                </Select>
              </Field>
              <label className="flex items-center gap-2 text-sm font-semibold text-ink-700 sm:col-span-2">
                <input checked={form.include_appointment_attendees} onChange={(event) => onChange({ ...form, include_appointment_attendees: event.target.checked })} type="checkbox" />
                Incluir emails de cliente y profesional en el evento Google
              </label>
            </div>
            {form.send_updates !== "none" ? <p className="mt-3 text-sm font-semibold text-warning-700">Esta opcion puede enviar invitaciones reales desde Google Calendar.</p> : null}
          </div>
        ) : form.provider === "n8n" ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-ink-900">Configuracion n8n</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">RealMeet puede activar workflows de n8n mediante eventos firmados. Los workflows se configuran y ejecutan fuera de RealMeet.</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Base URL n8n" id="n8n-base-url">
                <Input id="n8n-base-url" value={form.n8n_base_url} onChange={(event) => onChange({ ...form, n8n_base_url: event.target.value })} placeholder="https://automation.example.com" />
              </Field>
              <Field label="Ambiente" id="n8n-environment">
                <Input id="n8n-environment" value={form.n8n_environment} onChange={(event) => onChange({ ...form, n8n_environment: event.target.value })} placeholder="staging" />
              </Field>
            </div>
            <p className="mt-3 text-sm font-semibold text-warning-700">No pegues tokens, credenciales, headers ni URLs con secretos. Define cada workflow con un path relativo.</p>
          </div>
        ) : form.provider === "mercado_pago" ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-ink-900">Configuracion Mercado Pago Checkout Pro</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">Usa credenciales de prueba por referencia. RealMeet redirige a Mercado Pago y verifica el pago desde backend.</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Ambiente" id="mp-environment">
                <Select id="mp-environment" value={form.mercado_pago_environment} onChange={(event) => onChange({ ...form, mercado_pago_environment: event.target.value as FormState["mercado_pago_environment"] })}>
                  <option value="sandbox">Sandbox</option>
                  <option value="production">Produccion bloqueada</option>
                </Select>
              </Field>
              <Field label="Ref. access token" id="mp-access-token-ref">
                <Input id="mp-access-token-ref" value={form.mercado_pago_access_token_ref} onChange={(event) => onChange({ ...form, mercado_pago_access_token_ref: event.target.value })} placeholder="MERCADO_PAGO_ACCESS_TOKEN" />
              </Field>
              <Field label="Ref. webhook secret" id="mp-webhook-secret-ref">
                <Input id="mp-webhook-secret-ref" value={form.mercado_pago_webhook_secret_ref} onChange={(event) => onChange({ ...form, mercado_pago_webhook_secret_ref: event.target.value })} placeholder="MERCADO_PAGO_WEBHOOK_SECRET" />
              </Field>
              <Field label="Notification URL" id="mp-notification-url">
                <Input id="mp-notification-url" value={form.mercado_pago_notification_url} onChange={(event) => onChange({ ...form, mercado_pago_notification_url: event.target.value })} />
              </Field>
              <Field label="Success URL" id="mp-success-url">
                <Input id="mp-success-url" value={form.mercado_pago_success_url} onChange={(event) => onChange({ ...form, mercado_pago_success_url: event.target.value })} />
              </Field>
              <Field label="Pending URL" id="mp-pending-url">
                <Input id="mp-pending-url" value={form.mercado_pago_pending_url} onChange={(event) => onChange({ ...form, mercado_pago_pending_url: event.target.value })} />
              </Field>
              <Field label="Failure URL" id="mp-failure-url">
                <Input id="mp-failure-url" value={form.mercado_pago_failure_url} onChange={(event) => onChange({ ...form, mercado_pago_failure_url: event.target.value })} />
              </Field>
            </div>
            <p className="mt-3 text-sm font-semibold text-warning-700">No pegues access tokens ni secretos. Produccion real queda fuera de 17.3.</p>
          </div>
        ) : form.provider === "whatsapp_cloud" ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold text-ink-900">Configuracion local WhatsApp</h3>
            <p className="mt-1 text-sm leading-6 text-ink-500">Estos campos preparan WhatsApp Cloud sin conectar Meta ni enviar mensajes reales.</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="WABA ID" id="wa-waba-id">
                <Input id="wa-waba-id" value={form.waba_id} onChange={(event) => onChange({ ...form, waba_id: event.target.value })} placeholder="123456789012345" />
              </Field>
              <Field label="Phone number ID" id="wa-phone-id">
                <Input id="wa-phone-id" value={form.phone_number_id} onChange={(event) => onChange({ ...form, phone_number_id: event.target.value })} placeholder="987654321098765" />
              </Field>
              <Field label="Telefono visible enmascarado" id="wa-display-phone">
                <Input id="wa-display-phone" value={form.display_phone_number_masked} onChange={(event) => onChange({ ...form, display_phone_number_masked: event.target.value })} placeholder="+56 9 **** 5678" />
              </Field>
              <Field label="Graph API version" id="wa-graph-version">
                <Input id="wa-graph-version" value={form.graph_api_version} onChange={(event) => onChange({ ...form, graph_api_version: event.target.value })} placeholder="v20.0" />
              </Field>
              <Field label="Idioma por defecto" id="wa-language">
                <Input id="wa-language" value={form.default_language} onChange={(event) => onChange({ ...form, default_language: event.target.value })} placeholder="es_CL" />
              </Field>
              <Field label="Pais" id="wa-country">
                <Input id="wa-country" maxLength={2} value={form.country_code} onChange={(event) => onChange({ ...form, country_code: event.target.value.toUpperCase() })} placeholder="CL" />
              </Field>
              <Field label="Ref. access token" id="wa-access-token-ref">
                <Input id="wa-access-token-ref" value={form.whatsapp_access_token_ref} onChange={(event) => onChange({ ...form, whatsapp_access_token_ref: event.target.value })} placeholder="WHATSAPP_ACCESS_TOKEN" />
              </Field>
              <Field label="Ref. app secret" id="wa-app-secret-ref">
                <Input id="wa-app-secret-ref" value={form.whatsapp_app_secret_ref} onChange={(event) => onChange({ ...form, whatsapp_app_secret_ref: event.target.value })} placeholder="WHATSAPP_APP_SECRET" />
              </Field>
              <Field label="Ref. verify token" id="wa-verify-token-ref">
                <Input id="wa-verify-token-ref" value={form.whatsapp_verify_token_ref} onChange={(event) => onChange({ ...form, whatsapp_verify_token_ref: event.target.value })} placeholder="WHATSAPP_VERIFY_TOKEN" />
              </Field>
              <Field label="Ref. phone HMAC key" id="wa-hmac-key-ref">
                <Input id="wa-hmac-key-ref" value={form.whatsapp_phone_hmac_key_ref} onChange={(event) => onChange({ ...form, whatsapp_phone_hmac_key_ref: event.target.value })} placeholder="WHATSAPP_PHONE_HMAC_KEY" />
              </Field>
              <Field label="Politica de notificaciones" id="wa-notification-policy">
                <Select id="wa-notification-policy" value={form.notification_policy} onChange={(event) => onChange({ ...form, notification_policy: event.target.value as WhatsAppNotificationPolicyValue })}>
                  <option value="email_only">Solo correo</option>
                  <option value="whatsapp_preferred">Preferir WhatsApp y usar correo como respaldo</option>
                  <option value="whatsapp_required">Solo WhatsApp</option>
                  <option value="email_and_whatsapp">Correo y WhatsApp</option>
                  <option value="notifications_disabled">Notificaciones deshabilitadas</option>
                </Select>
              </Field>
              <Field label="Minutos antes del recordatorio" id="wa-reminder-minutes">
                <Input id="wa-reminder-minutes" min={15} max={10080} type="number" value={form.reminder_minutes_before} onChange={(event) => onChange({ ...form, reminder_minutes_before: Number(event.target.value) })} />
              </Field>
              <label className="flex items-center gap-2 text-sm font-semibold text-ink-700 sm:col-span-2">
                <input checked={form.reminder_enabled} onChange={(event) => onChange({ ...form, reminder_enabled: event.target.checked })} type="checkbox" />
                Activar recordatorio transaccional automatico
              </label>
            </div>
            <p className="mt-3 text-sm font-semibold text-warning-700">No pegues tokens ni credenciales reales. Usa solo nombres de variables de entorno.</p>
          </div>
        ) : form.provider !== "mock" ? (
          <p className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-ink-600">La configuracion especifica de este proveedor estara disponible en una proxima etapa.</p>
        ) : null}
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

function toDatetimeLocal(value: Date): string {
  const offset = value.getTimezoneOffset();
  const local = new Date(value.getTime() - offset * 60 * 1000);
  return local.toISOString().slice(0, 16);
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
