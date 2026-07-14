import api from "./client";
import type {
  AdminMetrics,
  Appointment,
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

export async function fetchAdminMetrics(): Promise<AdminMetrics> {
  const { data } = await api.get("/admin/metrics");
  return data;
}
