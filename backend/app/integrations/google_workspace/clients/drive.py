import httpx

from app.integrations.exceptions import IntegrationProviderExecutionError


class GoogleDriveClient:
    base_url = "https://www.googleapis.com/drive/v3"

    def health_check(self, *, access_token: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/about",
            params={"fields": "user(emailAddress,displayName)"},
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=10,
        )
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Drive no respondio correctamente", code="google_drive_unavailable")
        data = response.json()
        user = data.get("user") or {}
        return {"email": user.get("emailAddress"), "name": user.get("displayName")}

    def get_file_metadata(self, *, access_token: str, file_id: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/files/{file_id}",
            params={"fields": "id,name,mimeType,trashed,webViewLink"},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code == 404:
            raise IntegrationProviderExecutionError("Documento Google no encontrado", code="google_docs_template_not_found")
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Drive no esta disponible", code="google_docs_template_unavailable")
        data = response.json()
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "mime_type": data.get("mimeType"),
            "trashed": bool(data.get("trashed")),
            "web_view_link": data.get("webViewLink"),
        }

    def get_folder_metadata(self, *, access_token: str, folder_id: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/files/{folder_id}",
            params={"fields": "id,name,mimeType,trashed"},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code == 404:
            raise IntegrationProviderExecutionError("Carpeta Google Drive no encontrada", code="google_drive_folder_not_found")
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Drive no esta disponible", code="google_drive_unavailable")
        data = response.json()
        if data.get("mimeType") != "application/vnd.google-apps.folder" or data.get("trashed"):
            raise IntegrationProviderExecutionError("Carpeta Google Drive no encontrada", code="google_drive_folder_not_found")
        return {"id": data.get("id"), "name": data.get("name")}

    def copy_file(self, *, access_token: str, file_id: str, name: str, app_properties: dict[str, str] | None = None) -> dict:
        response = httpx.post(
            f"{self.base_url}/files/{file_id}/copy",
            params={"fields": "id,name,mimeType,webViewLink"},
            json={"name": name, "appProperties": app_properties or {}},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos copiar la plantilla Google Docs", code="google_docs_copy_failed")
        data = response.json()
        return {"id": data.get("id"), "name": data.get("name"), "mime_type": data.get("mimeType"), "web_view_link": data.get("webViewLink")}

    def move_file(self, *, access_token: str, file_id: str, folder_id: str) -> None:
        response = httpx.patch(
            f"{self.base_url}/files/{file_id}",
            params={"addParents": folder_id, "fields": "id,parents"},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos mover el documento a la carpeta destino", code="google_drive_folder_not_found")

    def create_permission(self, *, access_token: str, file_id: str, email: str, role: str = "reader") -> dict:
        if role != "reader":
            raise IntegrationProviderExecutionError("Solo se permiten permisos reader", code="google_drive_share_failed")
        response = httpx.post(
            f"{self.base_url}/files/{file_id}/permissions",
            params={"sendNotificationEmail": "false", "fields": "id,role,emailAddress,type"},
            json={"type": "user", "role": "reader", "emailAddress": email},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos compartir el documento", code="google_drive_share_failed")
        data = response.json()
        return {"id": data.get("id"), "role": data.get("role"), "email": data.get("emailAddress"), "type": data.get("type")}

    def delete_permission(self, *, access_token: str, file_id: str, permission_id: str) -> None:
        response = httpx.delete(f"{self.base_url}/files/{file_id}/permissions/{permission_id}", headers=self._headers(access_token), timeout=10)
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos remover el permiso", code="google_drive_share_failed")

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
