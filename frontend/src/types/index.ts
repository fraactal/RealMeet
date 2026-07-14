export type UserRole = "admin" | "professional" | "client";

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
  consultation_mode: "online" | "presencial" | "hybrid";
  session_duration_minutes: number;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface ProfessionalSelfProfileUpdate extends UserSelfUpdate {
  title?: string | null;
  bio?: string | null;
  years_experience?: number | null;
  consultation_mode?: "online" | "presencial" | "hybrid" | null;
  session_duration_minutes?: number | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface ProfessionalPublic {
  id: number;
  title?: string | null;
  bio?: string | null;
  consultation_mode: "online" | "presencial" | "hybrid";
  session_duration_minutes: number;
  price?: number | null;
  city?: string | null;
  country?: string | null;
  category_name?: string | null;
  specialties: string[];
  user: User;
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
