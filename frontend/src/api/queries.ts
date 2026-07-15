import api from "./client";
import type {
  AdminMetrics,
  AdminAppointmentListResponse,
  AdminProfessionalListResponse,
  AdminProfessionalUpdate,
  AdminUserListResponse,
  AdminUserUpdate,
  Appointment,
  AppointmentNotification,
  AppointmentCreate,
  AppointmentPrivateNotesUpdate,
  AppointmentProfessionalStatusUpdate,
  AppointmentStatusUpdate,
  AvailabilityBlock,
  AvailabilityBlockWrite,
  AvailabilityResponse,
  AvailabilityRule,
  AvailabilityRuleWrite,
  CategoryAdmin,
  CategoryPublic,
  CategoryWrite,
  ClientSelfProfile,
  ClientSelfProfileUpdate,
  ClientRegisterPayload,
  ClientDashboard,
  GoogleOAuthAuthorizationUrl,
  GoogleOAuthDisconnectResult,
  GoogleOAuthStatus,
  GoogleMeetMeeting,
  GoogleMeetMeetingCancelPayload,
  GoogleMeetMeetingCreatePayload,
  Integration,
  IntegrationCreatePayload,
  IntegrationExecution,
  IntegrationListResponse,
  IntegrationOperationResult,
  IntegrationProvider,
  IntegrationStatus,
  IntegrationTestPayload,
  IntegrationType,
  IntegrationUpdatePayload,
  WebhookDelivery,
  WebhookSubscription,
  WebhookSubscriptionUpdate,
  WebhookSubscriptionWrite,
  WebhookTestResult,
  WhatsAppConsentCorrectionPayload,
  WhatsAppConsentPurpose,
  WhatsAppConsentSummary,
  WhatsAppHealthCheckResult,
  WhatsAppIntegrationStatus,
  WhatsAppMessage,
  WhatsAppMessageSendPayload,
  WhatsAppMessageSendResult,
  WhatsAppNotificationPolicy,
  WhatsAppTemplate,
  WhatsAppTemplateSyncResult,
  WhatsAppTemplateWrite,
  WhatsAppValidationResult,
  WhatsAppWebhookEvent,
  WhatsAppWebhookEventType,
  WhatsAppWebhookProcessingStatus,
  WhatsAppWebhookStatus,
  ProfessionalMetrics,
  ProfessionalAppointment,
  ProfessionalPublicProfile,
  ProfessionalPublicProfileUpdate,
  ProfessionalPublic,
  ProfessionalSearchParams,
  ProfessionalSearchResponse,
  ProfessionalSelfProfile,
  ProfessionalSelfProfileUpdate,
  ProfessionalSpecialty,
  ProfessionalSpecialtyUpdate,
  SpecialtyAdmin,
  SpecialtyPublic,
  SpecialtyWrite,
  User,
  UserSelfUpdate,
} from "../types";

export async function login(email: string, password: string): Promise<string> {
  const { data } = await api.post("/auth/login", { email, password });
  return data.access_token;
}

export async function registerClient(payload: ClientRegisterPayload): Promise<User> {
  const { data } = await api.post("/auth/register-client", payload);
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function updateMe(payload: UserSelfUpdate): Promise<User> {
  const { data } = await api.patch("/users/me", payload);
  return data;
}

export async function fetchClientSelfProfile(): Promise<ClientSelfProfile> {
  const { data } = await api.get("/users/me/profile");
  return data;
}

export async function updateClientSelfProfile(payload: ClientSelfProfileUpdate): Promise<ClientSelfProfile> {
  const { data } = await api.patch("/users/me/profile", payload);
  return data;
}

export async function fetchProfessionalSelfProfile(): Promise<ProfessionalSelfProfile> {
  const { data } = await api.get("/professionals/me/profile");
  return data;
}

export async function updateProfessionalSelfProfile(
  payload: ProfessionalSelfProfileUpdate,
): Promise<ProfessionalSelfProfile> {
  const { data } = await api.patch("/professionals/me/profile", payload);
  return data;
}

export async function fetchCategories(): Promise<CategoryPublic[]> {
  const { data } = await api.get("/categories");
  return data;
}

export async function fetchAdminCategories(): Promise<CategoryAdmin[]> {
  const { data } = await api.get("/admin/categories");
  return data;
}

export async function createAdminCategory(payload: CategoryWrite): Promise<CategoryAdmin> {
  const { data } = await api.post("/admin/categories", payload);
  return data;
}

export async function updateAdminCategory(categoryId: number, payload: CategoryWrite): Promise<CategoryAdmin> {
  const { data } = await api.patch(`/admin/categories/${categoryId}`, payload);
  return data;
}

export async function fetchSpecialties(categoryId?: number): Promise<SpecialtyPublic[]> {
  const { data } = await api.get("/specialties", { params: categoryId ? { category_id: categoryId } : undefined });
  return data;
}

export async function fetchAdminSpecialties(categoryId?: number): Promise<SpecialtyAdmin[]> {
  const { data } = await api.get("/admin/specialties", { params: categoryId ? { category_id: categoryId } : undefined });
  return data;
}

export async function createAdminSpecialty(payload: SpecialtyWrite): Promise<SpecialtyAdmin> {
  const { data } = await api.post("/admin/specialties", payload);
  return data;
}

export async function updateAdminSpecialty(specialtyId: number, payload: SpecialtyWrite): Promise<SpecialtyAdmin> {
  const { data } = await api.patch(`/admin/specialties/${specialtyId}`, payload);
  return data;
}

export async function fetchProfessionals(params: ProfessionalSearchParams = {}): Promise<ProfessionalSearchResponse> {
  const { data } = await api.get("/professionals", { params });
  return data;
}

export async function fetchProfessional(professionalId: number): Promise<ProfessionalPublic> {
  const { data } = await api.get(`/professionals/${professionalId}`);
  return data;
}

export async function fetchProfessionalPublicProfile(): Promise<ProfessionalPublicProfile> {
  const { data } = await api.get("/professionals/me/public-profile");
  return data;
}

export async function updateProfessionalPublicProfile(
  payload: ProfessionalPublicProfileUpdate,
): Promise<ProfessionalPublicProfile> {
  const { data } = await api.patch("/professionals/me/public-profile", payload);
  return data;
}

export async function fetchProfessionalSpecialties(): Promise<ProfessionalSpecialty[]> {
  const { data } = await api.get("/professionals/me/specialties");
  return data;
}

export async function updateProfessionalSpecialties(payload: ProfessionalSpecialtyUpdate): Promise<ProfessionalSpecialty[]> {
  const { data } = await api.patch("/professionals/me/specialties", payload);
  return data;
}

export async function fetchAvailabilityRules(): Promise<AvailabilityRule[]> {
  const { data } = await api.get("/professionals/me/availability-rules");
  return data;
}

export async function createAvailabilityRule(payload: AvailabilityRuleWrite): Promise<AvailabilityRule> {
  const { data } = await api.post("/professionals/me/availability-rules", payload);
  return data;
}

export async function updateAvailabilityRule(ruleId: number, payload: AvailabilityRuleWrite): Promise<AvailabilityRule> {
  const { data } = await api.patch(`/professionals/me/availability-rules/${ruleId}`, payload);
  return data;
}

export async function deleteAvailabilityRule(ruleId: number): Promise<void> {
  await api.delete(`/professionals/me/availability-rules/${ruleId}`);
}

export async function fetchAvailabilityBlocks(): Promise<AvailabilityBlock[]> {
  const { data } = await api.get("/professionals/me/availability-blocks");
  return data;
}

export async function createAvailabilityBlock(payload: AvailabilityBlockWrite): Promise<AvailabilityBlock> {
  const { data } = await api.post("/professionals/me/availability-blocks", payload);
  return data;
}

export async function updateAvailabilityBlock(blockId: number, payload: AvailabilityBlockWrite): Promise<AvailabilityBlock> {
  const { data } = await api.patch(`/professionals/me/availability-blocks/${blockId}`, payload);
  return data;
}

export async function deleteAvailabilityBlock(blockId: number): Promise<void> {
  await api.delete(`/professionals/me/availability-blocks/${blockId}`);
}

export async function fetchProfessionalAvailability(professionalId: number, date: string): Promise<AvailabilityResponse> {
  const { data } = await api.get(`/professionals/${professionalId}/availability`, { params: { date } });
  return data;
}

export async function fetchMyAppointments(): Promise<Appointment[]> {
  const { data } = await api.get("/appointments/me");
  return data;
}

export async function createAppointment(payload: AppointmentCreate): Promise<Appointment> {
  const { data } = await api.post("/appointments", payload);
  return data;
}

export async function cancelAppointment(appointmentId: number, payload: AppointmentStatusUpdate): Promise<Appointment> {
  const { data } = await api.patch(`/appointments/${appointmentId}/cancel`, payload);
  return data;
}

export async function fetchProfessionalAppointments(): Promise<ProfessionalAppointment[]> {
  const { data } = await api.get("/appointments/professional/me");
  return data;
}

export async function confirmProfessionalAppointment(
  appointmentId: number,
  payload: AppointmentProfessionalStatusUpdate,
): Promise<ProfessionalAppointment> {
  const { data } = await api.patch(`/appointments/professional/${appointmentId}/confirm`, payload);
  return data;
}

export async function completeProfessionalAppointment(
  appointmentId: number,
  payload: AppointmentProfessionalStatusUpdate,
): Promise<ProfessionalAppointment> {
  const { data } = await api.patch(`/appointments/professional/${appointmentId}/complete`, payload);
  return data;
}

export async function markNoShowProfessionalAppointment(
  appointmentId: number,
  payload: AppointmentProfessionalStatusUpdate,
): Promise<ProfessionalAppointment> {
  const { data } = await api.patch(`/appointments/professional/${appointmentId}/no-show`, payload);
  return data;
}

export async function cancelProfessionalAppointment(
  appointmentId: number,
  payload: AppointmentProfessionalStatusUpdate,
): Promise<ProfessionalAppointment> {
  const { data } = await api.patch(`/appointments/professional/${appointmentId}/cancel`, payload);
  return data;
}

export async function updateAppointmentPrivateNotes(
  appointmentId: number,
  payload: AppointmentPrivateNotesUpdate,
): Promise<ProfessionalAppointment> {
  const { data } = await api.patch(`/appointments/professional/${appointmentId}/private-notes`, payload);
  return data;
}

export async function fetchProfessionalMetrics(): Promise<ProfessionalMetrics> {
  const { data } = await api.get("/professional/metrics");
  return data;
}

export async function fetchClientDashboard(): Promise<ClientDashboard> {
  const { data } = await api.get("/client/metrics");
  return data;
}

export async function fetchAdminMetrics(): Promise<AdminMetrics> {
  const { data } = await api.get("/admin/metrics");
  return data;
}

export async function fetchAdminUsers(params: {
  search?: string;
  role?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
} = {}): Promise<AdminUserListResponse> {
  const { data } = await api.get("/admin/users", { params });
  return data;
}

export async function updateAdminUser(userId: number, payload: AdminUserUpdate) {
  const { data } = await api.patch(`/admin/users/${userId}`, payload);
  return data;
}

export async function fetchAdminProfessionals(params: {
  search?: string;
  is_active?: boolean;
  is_public?: boolean;
  page?: number;
  page_size?: number;
} = {}): Promise<AdminProfessionalListResponse> {
  const { data } = await api.get("/admin/professionals", { params });
  return data;
}

export async function updateAdminProfessional(professionalId: number, payload: AdminProfessionalUpdate) {
  const { data } = await api.patch(`/admin/professionals/${professionalId}`, payload);
  return data;
}

export async function fetchAdminAppointments(params: {
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<AdminAppointmentListResponse> {
  const { data } = await api.get("/admin/appointments", { params });
  return data;
}

export async function retryAdminAppointmentMeetingCreate(appointmentId: number): Promise<Appointment> {
  const { data } = await api.post(`/admin/appointments/${appointmentId}/meeting/retry-create`);
  return data;
}

export async function retryAdminAppointmentMeetingCancel(appointmentId: number): Promise<Appointment> {
  const { data } = await api.post(`/admin/appointments/${appointmentId}/meeting/retry-cancel`);
  return data;
}

export async function reconcileAdminAppointmentMeeting(appointmentId: number): Promise<Appointment> {
  const { data } = await api.post(`/admin/appointments/${appointmentId}/meeting/reconcile`);
  return data;
}

export async function fetchAdminIntegrations(params: {
  integration_type?: IntegrationType;
  provider?: IntegrationProvider;
  enabled?: boolean;
  status?: IntegrationStatus;
  page?: number;
  page_size?: number;
} = {}): Promise<IntegrationListResponse> {
  const { data } = await api.get("/admin/integrations", { params });
  return data;
}

export async function fetchAdminIntegration(integrationId: number): Promise<Integration> {
  const { data } = await api.get(`/admin/integrations/${integrationId}`);
  return data;
}

export async function createAdminIntegration(payload: IntegrationCreatePayload): Promise<Integration> {
  const { data } = await api.post("/admin/integrations", payload);
  return data;
}

export async function updateAdminIntegration(integrationId: number, payload: IntegrationUpdatePayload): Promise<Integration> {
  const { data } = await api.patch(`/admin/integrations/${integrationId}`, payload);
  return data;
}

export async function validateAdminIntegration(integrationId: number): Promise<IntegrationOperationResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/validate`);
  return data;
}

export async function enableAdminIntegration(integrationId: number): Promise<Integration> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/enable`);
  return data;
}

export async function disableAdminIntegration(integrationId: number): Promise<Integration> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/disable`);
  return data;
}

export async function healthCheckAdminIntegration(integrationId: number): Promise<IntegrationOperationResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/health-check`);
  return data;
}

export async function testAdminIntegration(integrationId: number, payload: IntegrationTestPayload): Promise<IntegrationOperationResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/test`, payload);
  return data;
}

export async function fetchAdminIntegrationExecutions(integrationId: number): Promise<IntegrationExecution[]> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/executions`);
  return data;
}

export async function fetchWebhookSubscriptions(): Promise<WebhookSubscription[]> {
  const { data } = await api.get("/admin/webhook-subscriptions");
  return data;
}

export async function createWebhookSubscription(payload: WebhookSubscriptionWrite): Promise<WebhookSubscription> {
  const { data } = await api.post("/admin/webhook-subscriptions", payload);
  return data;
}

export async function updateWebhookSubscription(subscriptionId: number, payload: WebhookSubscriptionUpdate): Promise<WebhookSubscription> {
  const { data } = await api.patch(`/admin/webhook-subscriptions/${subscriptionId}`, payload);
  return data;
}

export async function enableWebhookSubscription(subscriptionId: number): Promise<WebhookSubscription> {
  const { data } = await api.post(`/admin/webhook-subscriptions/${subscriptionId}/enable`);
  return data;
}

export async function disableWebhookSubscription(subscriptionId: number): Promise<WebhookSubscription> {
  const { data } = await api.post(`/admin/webhook-subscriptions/${subscriptionId}/disable`);
  return data;
}

export async function testWebhookSubscription(subscriptionId: number): Promise<WebhookTestResult> {
  const { data } = await api.post(`/admin/webhook-subscriptions/${subscriptionId}/test`);
  return data;
}

export async function fetchWebhookDeliveries(params: { subscription_id?: number; limit?: number } = {}): Promise<WebhookDelivery[]> {
  const { data } = await api.get("/admin/webhook-deliveries", { params });
  return data;
}

export async function retryWebhookDelivery(deliveryId: number): Promise<WebhookDelivery> {
  const { data } = await api.post(`/admin/webhook-deliveries/${deliveryId}/retry`);
  return data;
}

export async function fetchGoogleOAuthStatus(integrationId: number): Promise<GoogleOAuthStatus> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/oauth/status`);
  return data;
}

export async function createGoogleOAuthAuthorizationUrl(integrationId: number): Promise<GoogleOAuthAuthorizationUrl> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/oauth/google/authorize`);
  return data;
}

export async function refreshGoogleOAuth(integrationId: number): Promise<GoogleOAuthStatus> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/oauth/refresh`);
  return data;
}

export async function disconnectGoogleOAuth(integrationId: number): Promise<GoogleOAuthDisconnectResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/oauth/disconnect`);
  return data;
}

export async function createGoogleMeetMeeting(integrationId: number, payload: GoogleMeetMeetingCreatePayload): Promise<GoogleMeetMeeting> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/meetings`, payload);
  return data;
}

export async function fetchGoogleMeetMeeting(integrationId: number, externalEventId: string): Promise<GoogleMeetMeeting> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/meetings/${encodeURIComponent(externalEventId)}`);
  return data;
}

export async function cancelGoogleMeetMeeting(integrationId: number, externalEventId: string, payload: GoogleMeetMeetingCancelPayload): Promise<GoogleMeetMeeting> {
  const { data } = await api.delete(`/admin/integrations/${integrationId}/meetings/${encodeURIComponent(externalEventId)}`, { data: payload });
  return data;
}

export async function fetchWhatsAppStatus(integrationId: number): Promise<WhatsAppIntegrationStatus> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/status`);
  return data;
}

export async function validateWhatsAppConfiguration(integrationId: number): Promise<WhatsAppValidationResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/validate`);
  return data;
}

export async function fetchWhatsAppWebhookStatus(integrationId: number): Promise<WhatsAppWebhookStatus> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/webhook-status`);
  return data;
}

export async function fetchWhatsAppWebhookEvents(
  integrationId: number,
  params: { event_type?: WhatsAppWebhookEventType; processing_status?: WhatsAppWebhookProcessingStatus; duplicate?: boolean; limit?: number } = {},
): Promise<WhatsAppWebhookEvent[]> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/webhook-events`, { params });
  return data;
}

export async function fetchWhatsAppWebhookEvent(integrationId: number, eventId: number): Promise<WhatsAppWebhookEvent> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/webhook-events/${eventId}`);
  return data;
}

export async function fetchWhatsAppTemplates(integrationId: number): Promise<WhatsAppTemplate[]> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/templates`);
  return data;
}

export async function createWhatsAppTemplate(integrationId: number, payload: Required<WhatsAppTemplateWrite>): Promise<WhatsAppTemplate> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/templates`, payload);
  return data;
}

export async function updateWhatsAppTemplate(integrationId: number, templateId: number, payload: WhatsAppTemplateWrite): Promise<WhatsAppTemplate> {
  const { data } = await api.patch(`/admin/integrations/${integrationId}/whatsapp/templates/${templateId}`, payload);
  return data;
}

export async function syncWhatsAppTemplates(integrationId: number): Promise<WhatsAppTemplateSyncResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/templates/sync`);
  return data;
}

export async function healthCheckWhatsApp(integrationId: number): Promise<WhatsAppHealthCheckResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/health-check`);
  return data;
}

export async function fetchWhatsAppMessages(integrationId: number): Promise<WhatsAppMessage[]> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/messages`, { params: { limit: 50 } });
  return data;
}

export async function sendWhatsAppMessage(integrationId: number, payload: WhatsAppMessageSendPayload): Promise<WhatsAppMessageSendResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/messages`, payload);
  return data;
}

export async function retryWhatsAppMessage(integrationId: number, messageId: number): Promise<WhatsAppMessageSendResult> {
  const { data } = await api.post(`/admin/integrations/${integrationId}/whatsapp/messages/${messageId}/retry`);
  return data;
}

export async function fetchWhatsAppNotificationPolicy(integrationId: number): Promise<WhatsAppNotificationPolicy> {
  const { data } = await api.get(`/admin/integrations/${integrationId}/whatsapp/notification-policy`);
  return data;
}

export async function updateWhatsAppNotificationPolicy(integrationId: number, payload: WhatsAppNotificationPolicy): Promise<WhatsAppNotificationPolicy> {
  const { data } = await api.patch(`/admin/integrations/${integrationId}/whatsapp/notification-policy`, {
    notification_policy: payload.notification_policy,
    fallback_channel: payload.fallback_channel,
    reminder_enabled: payload.reminder_enabled,
    reminder_minutes_before: payload.reminder_minutes_before,
    default_language: payload.default_language,
    template_mapping: payload.template_mapping,
  });
  return data;
}

export async function fetchAppointmentNotifications(params: { appointment_id?: number; limit?: number; offset?: number } = {}): Promise<AppointmentNotification[]> {
  const { data } = await api.get("/admin/appointment-notifications", { params });
  return data;
}

export async function retryAppointmentNotification(notificationId: number): Promise<AppointmentNotification> {
  const { data } = await api.post(`/admin/appointment-notifications/${notificationId}/retry`);
  return data;
}

export async function reconcileAppointmentNotification(notificationId: number): Promise<AppointmentNotification> {
  const { data } = await api.post(`/admin/appointment-notifications/${notificationId}/reconcile`);
  return data;
}

export async function cancelAppointmentNotification(notificationId: number): Promise<AppointmentNotification> {
  const { data } = await api.post(`/admin/appointment-notifications/${notificationId}/cancel`);
  return data;
}

export async function fetchWhatsAppConsents(): Promise<WhatsAppConsentSummary[]> {
  const { data } = await api.get("/admin/whatsapp/consents");
  return data;
}

export async function createWhatsAppConsentCorrection(payload: WhatsAppConsentCorrectionPayload): Promise<WhatsAppConsentSummary> {
  const { data } = await api.post("/admin/whatsapp/consents/corrections", payload);
  return data;
}

export async function fetchMyWhatsAppConsents(): Promise<WhatsAppConsentSummary[]> {
  const { data } = await api.get("/users/me/whatsapp-consents");
  return data;
}

export async function grantMyWhatsAppConsent(payload: {
  phone: string;
  purpose: WhatsAppConsentPurpose;
  consent_text_version: string;
  explicit_confirmation: boolean;
}): Promise<WhatsAppConsentSummary> {
  const { data } = await api.post("/users/me/whatsapp-consents", payload);
  return data;
}

export async function revokeMyWhatsAppConsent(purpose: WhatsAppConsentPurpose): Promise<WhatsAppConsentSummary> {
  const { data } = await api.delete(`/users/me/whatsapp-consents/${purpose}`);
  return data;
}
