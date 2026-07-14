import api from "./client";
import type {
  AdminMetrics,
  Appointment,
  ClientSelfProfile,
  ClientSelfProfileUpdate,
  ProfessionalMetrics,
  ProfessionalPublic,
  ProfessionalSelfProfile,
  ProfessionalSelfProfileUpdate,
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

export async function fetchProfessionals(): Promise<ProfessionalPublic[]> {
  const { data } = await api.get("/professionals");
  return data;
}

export async function fetchMyAppointments(): Promise<Appointment[]> {
  const { data } = await api.get("/appointments/me");
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
