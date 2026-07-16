import httpx

from app.integrations.exceptions import IntegrationProviderExecutionError


class GoogleDocsClient:
    base_url = "https://docs.googleapis.com/v1/documents"

    def health_check(self, *, access_token: str) -> dict:
        return {"status": "authorized_not_resource_tested"}

    def get_document(self, *, access_token: str, document_id: str) -> dict:
        response = httpx.get(
            f"{self.base_url}/{document_id}",
            params={"fields": "documentId,title,body(content(paragraph(elements(textRun(content)))))"},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code == 404:
            raise IntegrationProviderExecutionError("Documento Google no encontrado", code="google_docs_template_not_found")
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Google Docs no esta disponible", code="google_docs_template_unavailable")
        data = response.json()
        return {"document_id": data.get("documentId"), "title": data.get("title"), "text": self._extract_text(data)}

    def batch_update_document(self, *, access_token: str, document_id: str, requests: list[dict]) -> None:
        response = httpx.post(
            f"{self.base_url}/{document_id}:batchUpdate",
            json={"requests": requests},
            headers=self._headers(access_token),
            timeout=10,
        )
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("No pudimos reemplazar variables en Google Docs", code="google_docs_replace_failed")

    def replace_all_text(self, *, access_token: str, document_id: str, replacements: dict[str, str]) -> None:
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": placeholder, "matchCase": True},
                    "replaceText": value,
                }
            }
            for placeholder, value in replacements.items()
        ]
        if requests:
            self.batch_update_document(access_token=access_token, document_id=document_id, requests=requests)

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    def _extract_text(self, data: dict) -> str:
        chunks: list[str] = []
        for content in ((data.get("body") or {}).get("content") or []):
            paragraph = content.get("paragraph") or {}
            for element in paragraph.get("elements") or []:
                text_run = element.get("textRun") or {}
                if text_run.get("content"):
                    chunks.append(str(text_run["content"]))
        return "".join(chunks)
