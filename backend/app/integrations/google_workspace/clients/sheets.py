import httpx

from app.integrations.exceptions import IntegrationProviderExecutionError


class GoogleSheetsClient:
    base_url = "https://sheets.googleapis.com/v4/spreadsheets"

    def health_check(self, *, access_token: str) -> dict:
        return {"status": "authorized_not_resource_tested"}

    def get_spreadsheet_metadata(self, *, access_token: str, spreadsheet_id: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/{spreadsheet_id}",
            params={"fields": "properties.title,sheets.properties.title"},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code == 404:
            raise IntegrationProviderExecutionError("No pudimos acceder al spreadsheet indicado", code="google_spreadsheet_not_found")
        if response.status_code == 403:
            raise IntegrationProviderExecutionError("Google Sheets requiere autorizacion", code="google_sheets_not_authorized")
        if response.status_code == 429:
            raise IntegrationProviderExecutionError("Google Sheets limito temporalmente la operacion", code="google_sheets_rate_limited")
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Sheets no esta disponible", code="google_sheets_unavailable")
        data = response.json()
        return {
            "title": (data.get("properties") or {}).get("title"),
            "sheets": [{"title": ((item.get("properties") or {}).get("title"))} for item in data.get("sheets", [])],
        }

    def get_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        response = httpx.get(
            f"{self.base_url}/{spreadsheet_id}/values/{range_name}",
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Sheets no esta disponible", code="google_sheets_unavailable")
        return response.json().get("values", [])

    def update_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> None:
        response = httpx.put(
            f"{self.base_url}/{spreadsheet_id}/values/{range_name}",
            params={"valueInputOption": "RAW"},
            json={"values": values},
            headers=self._headers(access_token),
            timeout=10,
        )
        self._raise_write_error(response)

    def append_sheet_values(self, *, access_token: str, spreadsheet_id: str, range_name: str, values: list[list[str]]) -> None:
        response = httpx.post(
            f"{self.base_url}/{spreadsheet_id}/values/{range_name}:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": values},
            headers=self._headers(access_token),
            timeout=10,
        )
        self._raise_write_error(response)

    def batch_update_values(self, *, access_token: str, spreadsheet_id: str, data: list[dict[str, object]]) -> None:
        response = httpx.post(
            f"{self.base_url}/{spreadsheet_id}/values:batchUpdate",
            json={"valueInputOption": "RAW", "data": data},
            headers=self._headers(access_token),
            timeout=10,
        )
        self._raise_write_error(response)

    def _raise_write_error(self, response: httpx.Response) -> None:
        if response.status_code == 403:
            raise IntegrationProviderExecutionError("Google Sheets requiere autorizacion", code="google_sheets_not_authorized")
        if response.status_code == 429:
            raise IntegrationProviderExecutionError("Google Sheets limito temporalmente la operacion", code="google_sheets_rate_limited")
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos completar la exportacion", code="google_sheets_export_failed")

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
