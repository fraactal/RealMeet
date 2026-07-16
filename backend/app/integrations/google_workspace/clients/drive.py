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
