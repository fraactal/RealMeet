import axios from "axios";

import { useAuthStore } from "../store/auth";

const apiBaseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:18000";

const api = axios.create({
  baseURL: `${apiBaseUrl}/api/v1`,
  timeout: 8000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("realmeet_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  },
);

export default api;
