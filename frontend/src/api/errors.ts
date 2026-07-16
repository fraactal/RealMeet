import axios from "axios";

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "unavailable"
  | "invalid_credentials"
  | "unauthorized"
  | "server"
  | "unexpected";

export interface ApiErrorDetails {
  kind: ApiErrorKind;
  message: string;
  status?: number;
  debug?: string;
}

export function normalizeApiError(error: unknown): ApiErrorDetails {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (error.code === "ECONNABORTED") {
      return { kind: "timeout", message: "La API tardó demasiado en responder.", status, debug: error.message };
    }
    if (error.response) {
      const responseData = error.response.data as { detail?: string | { code?: string; message?: string } } | undefined;
      const detail = responseData?.detail;
      if (typeof detail === "object" && typeof detail.message === "string") {
        return { kind: status === 503 ? "unavailable" : "server", message: detail.message, status, debug: error.message };
      }
      if (status === 401) {
        return { kind: "invalid_credentials", message: "Credenciales inválidas.", status, debug: error.message };
      }
      if (status === 403) {
        return { kind: "unauthorized", message: "No tienes permisos para realizar esta acción.", status, debug: error.message };
      }
      if (status === 503) {
        return { kind: "unavailable", message: "La API está iniciando o la base de datos no está disponible.", status, debug: error.message };
      }
      return {
        kind: "server",
        message: "El backend respondió con un error inesperado.",
        status,
        debug: `${error.message} :: ${JSON.stringify(error.response.data)}`,
      };
    }
    if (error.request) {
      return {
        kind: "network",
        message: "No fue posible conectar con la API. Revisa Docker o la URL configurada.",
        debug: error.message,
      };
    }
  }

  return { kind: "unexpected", message: "Ocurrió un error inesperado.", debug: error instanceof Error ? error.message : String(error) };
}
