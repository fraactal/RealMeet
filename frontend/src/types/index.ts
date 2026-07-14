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

export interface Appointment {
  id: number;
  professional_id: number;
  client_id: number;
  start_datetime: string;
  end_datetime: string;
  status: "pending" | "confirmed" | "cancelled" | "completed" | "no_show";
  meeting_url?: string | null;
  client_notes?: string | null;
}

export interface ProfessionalMetrics {
  today_reservations: number;
  upcoming_reservations: number;
  monthly_completed: number;
  lifetime_completed: number;
  unique_clients: number;
  cancelled_reservations: number;
  cancellation_rate: number;
  estimated_month_income: number;
}

export interface AdminMetrics {
  total_users: number;
  total_professionals: number;
  total_clients: number;
  total_appointments: number;
}
