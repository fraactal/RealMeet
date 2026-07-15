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
  provider: string;
  join_url?: string | null;
  status: "active" | "inactive" | "unknown";
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

export interface IntegrationConfig {
  simulate_error?: boolean;
  health?: "healthy" | "error";
  response_delay_ms?: number;
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
