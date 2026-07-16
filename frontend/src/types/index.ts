export type UserRole = "admin" | "professional" | "client";
export type ConsultationMode = "online" | "presencial" | "hybrid";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  role: UserRole;
  is_active: boolean;
}

export interface UserSelfUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
}

export interface ClientRegisterPayload {
  user: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone?: string | null;
    role: "client";
  };
  client_profile?: {
    birth_date?: string | null;
    notes?: string | null;
  } | null;
}

export interface ClientSelfProfile {
  user: User;
  birth_date?: string | null;
  notes?: string | null;
}

export interface ClientSelfProfileUpdate extends UserSelfUpdate {
  birth_date?: string | null;
  notes?: string | null;
}

export interface ProfessionalSelfProfile {
  id: number;
  user: User;
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode: ConsultationMode;
  session_duration_minutes: number;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface ProfessionalSelfProfileUpdate extends UserSelfUpdate {
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode?: ConsultationMode | null;
  session_duration_minutes?: number | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface ProfessionalPublic {
  id: number;
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode: ConsultationMode;
  session_duration_minutes: number;
  city?: string | null;
  country?: string | null;
  category: ProfessionalPublicCategory;
  specialties: ProfessionalSpecialty[];
  user: ProfessionalPublicUser;
}

export interface ProfessionalPublicUser {
  id: number;
  first_name: string;
  last_name: string;
}

export interface ProfessionalPublicCategory {
  id: number;
  name: string;
  slug: string;
}

export interface ProfessionalSpecialty {
  id: number;
  name: string;
  slug: string;
  category_id: number;
  category_name: string;
}

export interface ProfessionalSpecialtyUpdate {
  specialty_ids: number[];
}

export interface ProfessionalPublicProfile {
  id: number;
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode: ConsultationMode;
  session_duration_minutes: number;
  city?: string | null;
  country?: string | null;
  category_id?: number | null;
  is_public: boolean;
}

export interface ProfessionalPublicProfileUpdate {
  category_id?: number | null;
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode?: ConsultationMode | null;
  session_duration_minutes?: number | null;
  city?: string | null;
  country?: string | null;
  is_public?: boolean | null;
}

export interface ProfessionalSearchParams {
  search?: string;
  category_id?: number;
  specialty_id?: number;
  consultation_mode?: ConsultationMode;
  page?: number;
  page_size?: number;
}

export interface ProfessionalSearchResponse {
  items: ProfessionalPublic[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface CategoryPublic {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

export interface CategoryAdmin extends CategoryPublic {
  is_active: boolean;
}

export interface CategoryWrite {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface SpecialtyPublic {
  id: number;
  category_id: number;
  name: string;
  slug: string;
  description?: string | null;
}

export interface SpecialtyAdmin extends SpecialtyPublic {
  is_active: boolean;
}

export interface SpecialtyWrite {
  category_id?: number;
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

export type AvailabilityBlockType = "blocked" | "extra_available";

export interface AvailabilityRule {
  id: number;
  professional_id: number;
  weekday: number;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface AvailabilityRuleWrite {
  weekday?: number;
  start_time?: string;
  end_time?: string;
  is_active?: boolean;
}

export interface AvailabilityBlock {
  id: number;
  professional_id: number;
  start_datetime: string;
  end_datetime: string;
  reason?: string | null;
  type: AvailabilityBlockType;
}

export interface AvailabilityBlockWrite {
  start_datetime?: string;
  end_datetime?: string;
  reason?: string | null;
  type?: AvailabilityBlockType;
}

export interface AvailableSlot {
  start_datetime: string;
  end_datetime: string;
}

export interface AvailabilityResponse {
  professional_id: number;
  start_datetime: string;
  end_datetime: string;
  slots: AvailableSlot[];
}

export type AppointmentStatus = "pending" | "confirmed" | "cancelled" | "completed" | "no_show";

export interface AppointmentHistory {
  id: number;
  appointment_id: number;
  changed_by_user_id: number;
  old_status?: string | null;
  new_status: string;
  comment?: string | null;
  created_at: string;
}

export interface AppointmentCreate {
  professional_id: number;
  specialty_id?: number | null;
  start_datetime: string;
  client_notes?: string | null;
}

export interface AppointmentMeeting {
  provider?: string | null;
  join_url?: string | null;
  status: "active" | "inactive" | "unknown" | "pending" | "provisioning" | "ready" | "failed" | "fallback_ready" | "cancelled" | "not_required";
  fallback_used?: boolean;
  message?: string | null;
  error_code?: string | null;
  error_message?: string | null;
}

export interface Appointment {
  id: number;
  professional_id: number;
  client_id: number;
  category_id?: number | null;
  specialty_id?: number | null;
  start_datetime: string;
  end_datetime: string;
  status: AppointmentStatus;
  consultation_mode?: ConsultationMode;
  meeting_provider?: string | null;
  meeting_url?: string | null;
  meeting?: AppointmentMeeting | null;
  cancellation_reason?: string | null;
  client_notes?: string | null;
  history?: AppointmentHistory[];
}

export interface ProfessionalAppointment extends Appointment {
  professional_private_notes?: string | null;
}

export interface AppointmentStatusUpdate {
  reason?: string | null;
}

export interface AppointmentProfessionalStatusUpdate extends AppointmentStatusUpdate {
  professional_private_notes?: string | null;
}

export interface AppointmentPrivateNotesUpdate {
  professional_private_notes?: string | null;
}

export interface ProfessionalMetrics {
  today_reservations: number;
  upcoming_reservations: number;
  pending_reservations: number;
  confirmed_reservations: number;
  monthly_completed: number;
  lifetime_completed: number;
  unique_clients: number;
  cancelled_reservations: number;
  no_show_reservations: number;
  cancellation_rate: number;
  estimated_month_income: number;
  status_counts: StatusCounts;
  recent_appointments: DashboardAppointment[];
  next_appointments: DashboardAppointment[];
  is_public: boolean;
  availability_rules_count: number;
}

export interface AdminMetrics {
  total_users: number;
  active_clients: number;
  active_professionals: number;
  total_professionals: number;
  total_clients: number;
  public_professionals: number;
  total_appointments: number;
  pending_appointments: number;
  confirmed_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  no_show_appointments: number;
  active_categories: number;
  active_specialties: number;
  recent_appointments: DashboardAppointment[];
}

export interface StatusCounts {
  pending: number;
  confirmed: number;
  cancelled: number;
  completed: number;
  no_show: number;
}

export interface DashboardAppointment {
  id: number;
  start_datetime: string;
  end_datetime: string;
  status: AppointmentStatus;
  consultation_mode: ConsultationMode;
}

export interface ClientDashboard {
  upcoming_reservations: number;
  status_counts: StatusCounts;
  recent_appointments: DashboardAppointment[];
  next_appointments: DashboardAppointment[];
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AdminUserListItem {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AdminUserDetail extends AdminUserListItem {
  phone?: string | null;
  updated_at: string;
}

export interface AdminUserUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  is_active?: boolean | null;
}

export interface AdminUserListResponse {
  items: AdminUserListItem[];
  meta: PageMeta;
}

export interface AdminProfessionalListItem {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  title?: string | null;
  category_id?: number | null;
  consultation_mode: ConsultationMode;
  is_public: boolean;
  is_verified: boolean;
  user_is_active: boolean;
  created_at: string;
}

export interface AdminProfessionalDetail extends AdminProfessionalListItem {
  bio?: string | null;
  years_experience?: number | null;
  session_duration_minutes: number;
  price?: string | null;
  city?: string | null;
  country?: string | null;
  specialties: string[];
}

export interface AdminProfessionalUpdate {
  category_id?: number | null;
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode?: ConsultationMode | null;
  session_duration_minutes?: number | null;
  price?: string | null;
  city?: string | null;
  country?: string | null;
  is_verified?: boolean | null;
  is_public?: boolean | null;
  user_is_active?: boolean | null;
}

export interface AdminProfessionalListResponse {
  items: AdminProfessionalListItem[];
  meta: PageMeta;
}

export interface AdminAppointmentListResponse {
  items: Appointment[];
  meta: PageMeta;
}

export type IntegrationType = "meeting" | "calendar" | "messaging" | "email" | "automation" | "webhook";
export type IntegrationProvider =
  | "mock"
  | "google_meet"
  | "google_calendar"
  | "microsoft_365"
  | "whatsapp_cloud"
  | "twilio"
  | "smtp"
  | "n8n"
  | "generic_webhook";
export type IntegrationStatus = "not_configured" | "configured" | "healthy" | "error" | "unsupported";
export type IntegrationExecutionStatus = "pending" | "running" | "succeeded" | "failed" | "skipped";
export type WebhookEventType =
  | "appointment.created"
  | "appointment.updated"
  | "appointment.cancelled"
  | "appointment.confirmed"
  | "meeting.ready"
  | "notification.sent"
  | "notification.failed"
  | "client.created"
  | "professional.created"
  | "webhook.test"
  | "n8n.workflow.test";
export type WebhookDeliveryStatus = "pending" | "sending" | "succeeded" | "failed" | "skipped";

export interface IntegrationConfig {
  simulate_error?: boolean;
  health?: "healthy" | "error";
  response_delay_ms?: number;
  calendar_id?: string;
  default_timezone?: string;
  send_updates?: "none" | "all" | "externalOnly";
  appointment_policy?: "mock_only" | "google_preferred" | "google_required" | "disabled";
  fallback_provider?: "mock";
  include_appointment_attendees?: boolean;
  waba_id?: string;
  phone_number_id?: string;
  display_phone_number_masked?: string;
  graph_api_version?: string;
  default_language?: string;
  country_code?: string;
  secret_references?: WhatsAppSecretReferences;
  notification_policy?: WhatsAppNotificationPolicyValue;
  fallback_channel?: "email";
  reminder_enabled?: boolean;
  reminder_minutes_before?: number;
  template_mapping?: Partial<Record<WhatsAppTemplatePurpose, number>>;
  base_url?: string;
  environment?: string;
}

export interface WhatsAppSecretReferences {
  access_token?: string | null;
  app_secret?: string | null;
  verify_token?: string | null;
  phone_hmac_key?: string | null;
}

export interface Integration {
  id: number;
  name: string;
  integration_type: IntegrationType;
  provider: IntegrationProvider;
  enabled: boolean;
  status: IntegrationStatus;
  config: IntegrationConfig;
  secret_reference?: string | null;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error_at?: string | null;
  last_error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationExecution {
  id: number;
  integration_id: number;
  operation: string;
  entity_type?: string | null;
  entity_id?: string | null;
  idempotency_key: string;
  status: IntegrationExecutionStatus;
  attempt: number;
  error_code?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
}

export interface IntegrationOperationResult {
  success: boolean;
  code: string;
  message: string;
  skipped: boolean;
  metadata: Record<string, string | number | boolean | null>;
  execution_id?: number | null;
  duration_ms: number;
}

export interface IntegrationListResponse {
  items: Integration[];
  meta: PageMeta;
}

export interface IntegrationCreatePayload {
  name: string;
  integration_type: IntegrationType;
  provider: IntegrationProvider;
  config: IntegrationConfig;
  secret_reference?: string | null;
}

export interface IntegrationUpdatePayload {
  name?: string;
  config?: IntegrationConfig;
  secret_reference?: string | null;
}

export interface IntegrationTestPayload {
  idempotency_key: string;
}

export interface WebhookSubscription {
  id: number;
  integration_id: number;
  name: string;
  target_url: string;
  event_types: WebhookEventType[];
  secret_reference: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookSubscriptionWrite {
  integration_id: number;
  name: string;
  target_url: string;
  event_types: WebhookEventType[];
  secret_reference: string;
}

export interface WebhookSubscriptionUpdate {
  name?: string;
  target_url?: string;
  event_types?: WebhookEventType[];
  secret_reference?: string;
}

export interface WebhookDelivery {
  id: number;
  subscription_id: number;
  event_id: string;
  event_type: WebhookEventType;
  status: WebhookDeliveryStatus;
  attempt: number;
  idempotency_key: string;
  response_status?: number | null;
  duration_ms?: number | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WebhookTestResult {
  success: boolean;
  delivery_id?: number | null;
  status: WebhookDeliveryStatus;
  message: string;
}

export interface N8nWorkflow {
  id: number;
  integration_id: number;
  subscription_id: number;
  name: string;
  description?: string | null;
  webhook_path: string;
  event_types: WebhookEventType[];
  enabled: boolean;
  secret_reference: string;
  last_triggered_at?: string | null;
  last_success_at?: string | null;
  last_error_at?: string | null;
  last_error_code?: string | null;
  created_at: string;
  updated_at: string;
}

export interface N8nWorkflowWrite {
  name: string;
  description?: string | null;
  webhook_path: string;
  event_types: WebhookEventType[];
  secret_reference: string;
}

export type ExternalCalendarProvider = "fake" | "google_calendar" | "microsoft_365";
export type ExternalCalendarSyncStatus = "pending" | "active" | "disabled" | "error";
export type CalendarConflictPolicy = "internal_only" | "external_busy_blocks" | "disabled";
export type ExternalConflictFailurePolicy = "fail_closed" | "fail_open";

export interface ExternalCalendar {
  id: number;
  professional_id: number;
  integration_id?: number | null;
  provider: ExternalCalendarProvider;
  external_calendar_id: string;
  name: string;
  description?: string | null;
  timezone: string;
  read_enabled: boolean;
  write_enabled: boolean;
  conflict_check_enabled: boolean;
  is_primary: boolean;
  enabled: boolean;
  sync_status: ExternalCalendarSyncStatus;
  last_synced_at?: string | null;
  last_sync_error_at?: string | null;
  last_sync_error_code?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExternalCalendarWrite {
  provider: ExternalCalendarProvider;
  integration_id?: number | null;
  external_calendar_id: string;
  name: string;
  description?: string | null;
  timezone: string;
  read_enabled: boolean;
  write_enabled: boolean;
  conflict_check_enabled: boolean;
  is_primary: boolean;
}

export interface ExternalCalendarUpdate {
  name?: string;
  description?: string | null;
  timezone?: string;
  read_enabled?: boolean;
  write_enabled?: boolean;
  conflict_check_enabled?: boolean;
  is_primary?: boolean;
}

export interface CalendarSyncSettings {
  professional_id: number;
  sync_enabled: boolean;
  conflict_policy: CalendarConflictPolicy;
  external_conflict_failure_policy: ExternalConflictFailurePolicy;
  lookback_days: number;
  lookahead_days: number;
  default_external_calendar_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface CalendarSyncSettingsUpdate {
  sync_enabled?: boolean;
  conflict_policy?: CalendarConflictPolicy;
  external_conflict_failure_policy?: ExternalConflictFailurePolicy;
  lookback_days?: number;
  lookahead_days?: number;
  default_external_calendar_id?: number | null;
}

export interface ExternalCalendarTestResult {
  health: { healthy: boolean; code: string; message: string };
  calendars: Array<{ external_calendar_id: string; name: string; description?: string | null; timezone: string; is_primary: boolean; read_only: boolean }>;
  busy_periods: Array<{ starts_at: string; ends_at: string; source_calendar_id: string; external_event_id: string; availability: string }>;
  created_event_id?: string | null;
  deleted_event_id?: string | null;
}

export interface AvailableExternalCalendar {
  external_calendar_id: string;
  name: string;
  description?: string | null;
  timezone: string;
  is_primary: boolean;
  read_only: boolean;
}

export interface CalendarConflictCheckPayload {
  starts_at: string;
  ends_at: string;
}

export interface CalendarConflictCheckResult {
  has_conflict: boolean;
  status: "checked" | "partial" | "unavailable" | "external_check_skipped";
  candidate: { starts_at: string; ends_at: string };
  conflicts: Array<{ calendar_id: number; external_calendar_id: string; starts_at: string; ends_at: string; availability: string }>;
  errors: string[];
}

export type AppointmentExternalCalendarEventStatus = "pending" | "created" | "updated" | "cancelled" | "failed" | "reconcile_required";
export type AppointmentExternalCalendarSyncAction = "create" | "update" | "cancel" | "none";

export interface AppointmentExternalCalendarEvent {
  id: number;
  appointment_id: number;
  external_calendar_id: number;
  provider: string;
  status: AppointmentExternalCalendarEventStatus;
  sync_action: AppointmentExternalCalendarSyncAction;
  last_synced_at?: string | null;
  last_error_at?: string | null;
  last_error_code?: string | null;
  last_error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AutomationExample {
  key: string;
  name: string;
  description: string;
  recommended_event_types: WebhookEventType[];
  required_n8n_credentials: string[];
  workflow_filename: string;
}

export interface AutomationExampleDetail {
  example: AutomationExample;
  workflow: Record<string, unknown>;
}

export interface GoogleOAuthAuthorizationUrl {
  authorization_url: string;
  state_expires_at: string;
}

export interface GoogleOAuthStatus {
  status: "not_connected" | "pending" | "connected" | "expired" | "revoked" | "error";
  provider: "google_meet";
  connected: boolean;
  external_account_email?: string | null;
  external_account_id?: string | null;
  scopes: string[];
  authorized_at?: string | null;
  expires_at?: string | null;
  last_refresh_at?: string | null;
  revoked_at?: string | null;
  last_error_message?: string | null;
}

export interface GoogleOAuthDisconnectResult {
  success: boolean;
  status: string;
  message: string;
}

export type GoogleWorkspaceServiceKey = "calendar" | "meet" | "sheets" | "drive" | "docs";
export type GoogleWorkspaceHealthStatus =
  | "healthy"
  | "authorized_not_resource_tested"
  | "authorization_required"
  | "disabled"
  | "unavailable"
  | "error";

export interface GoogleWorkspaceSettingsUpdate {
  calendar_enabled?: boolean;
  meet_enabled?: boolean;
  sheets_enabled?: boolean;
  drive_enabled?: boolean;
  docs_enabled?: boolean;
}

export interface GoogleWorkspaceOAuthStartPayload {
  services: GoogleWorkspaceServiceKey[];
}

export interface GoogleWorkspaceOAuthStartResult {
  authorization_url: string;
  state_expires_at: string;
  services: GoogleWorkspaceServiceKey[];
  scopes: string[];
}

export interface GoogleWorkspaceServiceDefinition {
  key: GoogleWorkspaceServiceKey;
  name: string;
  description: string;
  required_scopes: string[];
  optional_scopes: string[];
  implemented: boolean;
  health_check_supported: boolean;
}

export interface GoogleWorkspaceAccount {
  email?: string | null;
  name?: string | null;
  granted_scopes: string[];
  token_expires_at?: string | null;
  connection_status: string;
}

export interface GoogleWorkspaceServiceStatus {
  service: GoogleWorkspaceServiceKey;
  enabled: boolean;
  authorized: boolean;
  status: GoogleWorkspaceHealthStatus;
  checked_at?: string | null;
  last_error_code?: string | null;
}

export interface GoogleWorkspaceStatus {
  integration_id: number;
  account: GoogleWorkspaceAccount;
  catalog: GoogleWorkspaceServiceDefinition[];
  services: GoogleWorkspaceServiceStatus[];
}

export interface GoogleMeetMeeting {
  provider: string;
  external_event_id: string;
  external_calendar_id: string;
  meeting_url?: string | null;
  html_link?: string | null;
  conference_id?: string | null;
  status: string;
  start_at: string;
  end_at: string;
  created_at?: string | null;
  metadata: Record<string, string | number | boolean | null>;
}

export interface GoogleMeetMeetingCreatePayload {
  title: string;
  description?: string | null;
  start_at: string;
  end_at: string;
  timezone: string;
  attendees: string[];
  idempotency_key: string;
  send_updates: "none" | "all" | "externalOnly";
}

export interface GoogleMeetMeetingCancelPayload {
  idempotency_key: string;
  send_updates: "none" | "all" | "externalOnly";
}

export type WhatsAppConsentStatus = "not_granted" | "granted" | "revoked";
export type WhatsAppConsentPurpose = "appointment_transactional" | "appointment_reminders" | "appointment_updates";
export type WhatsAppConsentSource = "self_service" | "admin_correction" | "imported" | "system_migration";
export type WhatsAppTemplateStatus = "draft" | "pending" | "approved" | "rejected" | "paused" | "disabled" | "unknown";
export type WhatsAppTemplateCategory = "utility" | "authentication" | "marketing" | "unknown";
export type WhatsAppTemplatePurpose = "appointment_confirmation" | "appointment_reminder" | "appointment_updated" | "appointment_cancelled" | "meeting_ready";
export type WhatsAppWebhookEventType = "inbound_message" | "message_sent" | "message_delivered" | "message_read" | "message_failed" | "template_status" | "unknown";
export type WhatsAppWebhookProcessingStatus = "received" | "classified" | "ignored" | "duplicate" | "failed";
export type WhatsAppMessageStatus = "queued" | "accepted" | "sent" | "delivered" | "read" | "failed" | "cancelled" | "skipped";

export interface WhatsAppIntegrationStatus {
  integration_id: number;
  provider: string;
  status: string;
  enabled: boolean;
  locally_configured: boolean;
  operational_for_sending: boolean;
  message: string;
  waba_id_partial: string;
  phone_number_id_partial: string;
  display_phone_number_masked: string;
  graph_api_version: string;
  default_language: string;
  country_code: string;
}

export interface WhatsAppValidationResult {
  success: boolean;
  code: string;
  message: string;
  metadata: Record<string, string | number | boolean | string[] | null>;
}

export interface WhatsAppWebhookStatus {
  integration_id: number;
  public_url?: string | null;
  public_url_configured: boolean;
  verify_token_configured: boolean;
  app_secret_configured: boolean;
  signature_required: boolean;
  max_body_bytes: number;
  retention_days: number;
  last_received_at?: string | null;
  recent_total: number;
  last_error?: string | null;
}

export interface WhatsAppWebhookEvent {
  id: number;
  integration_id?: number | null;
  event_key_partial: string;
  payload_hash_partial: string;
  object_type?: string | null;
  field?: string | null;
  event_type: WhatsAppWebhookEventType;
  external_message_id_partial?: string | null;
  phone_number_id_masked?: string | null;
  status?: string | null;
  occurred_at?: string | null;
  received_at: string;
  last_received_at?: string | null;
  processed_at?: string | null;
  processing_status: WhatsAppWebhookProcessingStatus;
  signature_valid: boolean;
  duplicate: boolean;
  received_count: number;
  safe_metadata: Record<string, string | number | boolean | null | string[]>;
  error_code?: string | null;
  error_message?: string | null;
}

export interface WhatsAppTemplateVariable {
  key: "client_name" | "professional_name" | "appointment_date" | "appointment_time" | "appointment_modality" | "meeting_url" | "platform_name";
  required: boolean;
  sensitive: false;
}

export interface WhatsAppTemplateComponentsSchema {
  variables: WhatsAppTemplateVariable[];
}

export interface WhatsAppTemplate {
  id: number;
  integration_id: number;
  name: string;
  language: string;
  category: WhatsAppTemplateCategory;
  status: WhatsAppTemplateStatus;
  purpose: WhatsAppTemplatePurpose;
  components_schema: WhatsAppTemplateComponentsSchema;
  external_template_id?: string | null;
  last_synced_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppTemplateWrite {
  name?: string;
  language?: string;
  category?: "utility";
  purpose?: WhatsAppTemplatePurpose;
  components_schema?: WhatsAppTemplateComponentsSchema;
}

export interface WhatsAppConsentSummary {
  id: number;
  user_id: number;
  phone_masked: string;
  status: WhatsAppConsentStatus;
  purpose: WhatsAppConsentPurpose;
  source: WhatsAppConsentSource;
  granted_at?: string | null;
  revoked_at?: string | null;
  created_at: string;
}

export interface WhatsAppConsentCorrectionPayload {
  user_id: number;
  phone: string;
  purpose: WhatsAppConsentPurpose;
  consent_text_version: string;
  reason: string;
}

export interface WhatsAppHealthCheckResult {
  success: boolean;
  code: string;
  message: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface WhatsAppTemplateSyncResult {
  success: boolean;
  code: string;
  message: string;
  synced_count: number;
  updated_count: number;
  skipped_count: number;
}

export interface WhatsAppMessageVariables {
  client_name?: string | null;
  professional_name?: string | null;
  appointment_date?: string | null;
  appointment_time?: string | null;
  appointment_modality?: string | null;
  meeting_url?: string | null;
  platform_name?: string | null;
}

export interface WhatsAppMessageSendPayload {
  consent_id: number;
  template_id: number;
  purpose: WhatsAppTemplatePurpose;
  language: string;
  variables: WhatsAppMessageVariables;
  idempotency_key: string;
  explicit_confirmation: boolean;
}

export interface WhatsAppMessage {
  id: number;
  integration_id: number;
  user_id?: number | null;
  template_id: number;
  purpose: WhatsAppTemplatePurpose;
  recipient_masked: string;
  status: WhatsAppMessageStatus;
  external_message_id_partial?: string | null;
  idempotency_key: string;
  attempt: number;
  accepted_at?: string | null;
  sent_at?: string | null;
  delivered_at?: string | null;
  read_at?: string | null;
  failed_at?: string | null;
  last_status_at?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppMessageSendResult {
  success: boolean;
  code: string;
  message: string;
  skipped: boolean;
  data: WhatsAppMessage;
}

export type WhatsAppNotificationPolicyValue =
  | "email_only"
  | "whatsapp_preferred"
  | "whatsapp_required"
  | "email_and_whatsapp"
  | "notifications_disabled";

export interface WhatsAppNotificationPolicy {
  integration_id: number;
  notification_policy: WhatsAppNotificationPolicyValue;
  fallback_channel: "email";
  reminder_enabled: boolean;
  reminder_minutes_before: number;
  default_language: string;
  template_mapping: Partial<Record<WhatsAppTemplatePurpose, number>>;
}

export interface AppointmentNotification {
  id: number;
  appointment_id: number;
  user_id?: number | null;
  event_type: "appointment_confirmed" | "appointment_updated" | "appointment_cancelled" | "appointment_reminder" | "meeting_ready";
  channel: "email" | "whatsapp";
  purpose: WhatsAppTemplatePurpose;
  status: "pending" | "processing" | "accepted" | "sent" | "delivered" | "read" | "failed" | "skipped" | "cancelled" | "fallback_sent";
  whatsapp_message_id?: number | null;
  email_reference?: string | null;
  template_id?: number | null;
  recipient_masked?: string | null;
  fallback_used: boolean;
  idempotency_key: string;
  attempt: number;
  scheduled_for?: string | null;
  sent_at?: string | null;
  failed_at?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}
