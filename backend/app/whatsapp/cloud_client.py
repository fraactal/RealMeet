from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from app.core.config import settings


class WhatsAppCloudClientError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class WhatsAppPhoneNumberInfo:
    id: str
    display_phone_number: str | None
    verified_name: str | None


@dataclass(frozen=True)
class WhatsAppRemoteTemplate:
    id: str | None
    name: str
    language: str
    category: str
    status: str


@dataclass(frozen=True)
class WhatsAppSendResult:
    external_message_id: str
    raw_status: str | None = None


class WhatsAppCloudClient(Protocol):
    def get_phone_number(self, *, graph_api_version: str, phone_number_id: str, access_token: str) -> WhatsAppPhoneNumberInfo:
        ...

    def list_templates(self, *, graph_api_version: str, waba_id: str, access_token: str) -> list[WhatsAppRemoteTemplate]:
        ...

    def send_template_message(
        self,
        *,
        graph_api_version: str,
        phone_number_id: str,
        access_token: str,
        to_e164: str,
        template_name: str,
        language: str,
        body_variables: list[str],
    ) -> WhatsAppSendResult:
        ...


class HttpWhatsAppCloudClient:
    base_url = "https://graph.facebook.com"

    def __init__(self) -> None:
        timeout = httpx.Timeout(
            settings.whatsapp_http_total_timeout_seconds,
            connect=settings.whatsapp_http_connect_timeout_seconds,
            read=settings.whatsapp_http_read_timeout_seconds,
        )
        self._client = httpx.Client(timeout=timeout)

    def get_phone_number(self, *, graph_api_version: str, phone_number_id: str, access_token: str) -> WhatsAppPhoneNumberInfo:
        url = self._url(graph_api_version, phone_number_id)
        response = self._request("GET", url, access_token=access_token, params={"fields": "id,display_phone_number,verified_name"})
        return WhatsAppPhoneNumberInfo(
            id=str(response.get("id") or phone_number_id),
            display_phone_number=response.get("display_phone_number"),
            verified_name=response.get("verified_name"),
        )

    def list_templates(self, *, graph_api_version: str, waba_id: str, access_token: str) -> list[WhatsAppRemoteTemplate]:
        url = self._url(graph_api_version, f"{waba_id}/message_templates")
        response = self._request("GET", url, access_token=access_token, params={"fields": "id,name,language,category,status"})
        data = response.get("data") if isinstance(response.get("data"), list) else []
        return [
            WhatsAppRemoteTemplate(
                id=str(item.get("id")) if item.get("id") else None,
                name=str(item.get("name") or ""),
                language=str(item.get("language") or ""),
                category=str(item.get("category") or "UNKNOWN"),
                status=str(item.get("status") or "UNKNOWN"),
            )
            for item in data
            if isinstance(item, dict) and item.get("name") and item.get("language")
        ]

    def send_template_message(
        self,
        *,
        graph_api_version: str,
        phone_number_id: str,
        access_token: str,
        to_e164: str,
        template_name: str,
        language: str,
        body_variables: list[str],
    ) -> WhatsAppSendResult:
        components = []
        if body_variables:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": value} for value in body_variables],
                }
            )
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164.lstrip("+"),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components,
            },
        }
        response = self._request("POST", self._url(graph_api_version, f"{phone_number_id}/messages"), access_token=access_token, json=payload)
        messages = response.get("messages") if isinstance(response.get("messages"), list) else []
        first = messages[0] if messages and isinstance(messages[0], dict) else {}
        external_id = first.get("id")
        if not external_id:
            raise WhatsAppCloudClientError("Respuesta invalida de WhatsApp", code="whatsapp_invalid_response")
        return WhatsAppSendResult(external_message_id=str(external_id), raw_status=str(first.get("message_status")) if first.get("message_status") else None)

    def _request(self, method: str, url: str, *, access_token: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, url, headers={"Authorization": f"Bearer {access_token}"}, **kwargs)
        except httpx.TimeoutException as exc:
            raise WhatsAppCloudClientError("Timeout de WhatsApp Cloud", code="whatsapp_timeout") from exc
        except httpx.HTTPError as exc:
            raise WhatsAppCloudClientError("Error temporal de WhatsApp Cloud", code="whatsapp_http_error") from exc
        if response.status_code >= 400:
            raise self._error_from_response(response)
        try:
            data = response.json()
        except ValueError as exc:
            raise WhatsAppCloudClientError("Respuesta invalida de WhatsApp", code="whatsapp_invalid_response", status_code=response.status_code) from exc
        if not isinstance(data, dict):
            raise WhatsAppCloudClientError("Respuesta invalida de WhatsApp", code="whatsapp_invalid_response", status_code=response.status_code)
        return data

    def _error_from_response(self, response: httpx.Response) -> WhatsAppCloudClientError:
        code = "whatsapp_provider_error"
        message = "WhatsApp Cloud rechazo la operacion"
        try:
            body = response.json()
        except ValueError:
            body = {}
        error = body.get("error") if isinstance(body, dict) and isinstance(body.get("error"), dict) else {}
        meta_code = str(error.get("code") or "")
        if response.status_code == 401:
            code = "whatsapp_token_invalid"
            message = "Token WhatsApp invalido"
        elif response.status_code == 403:
            code = "whatsapp_permission_denied"
            message = "Permisos insuficientes para WhatsApp Cloud"
        elif response.status_code == 404:
            code = "whatsapp_resource_not_found"
            message = "Recurso WhatsApp no encontrado"
        elif response.status_code == 429 or meta_code in {"4", "80007", "130429", "131048"}:
            code = "whatsapp_rate_limited"
            message = "WhatsApp Cloud aplico rate limit"
        elif response.status_code >= 500:
            code = "whatsapp_temporary_error"
            message = "WhatsApp Cloud no esta disponible temporalmente"
        return WhatsAppCloudClientError(message, code=code, status_code=response.status_code)

    def _url(self, graph_api_version: str, path: str) -> str:
        safe_version = quote(graph_api_version.strip(), safe="")
        safe_path = "/".join(quote(part, safe="") for part in path.strip("/").split("/"))
        return f"{self.base_url}/{safe_version}/{safe_path}"


class FakeWhatsAppCloudClient:
    def __init__(self, *, fail_code: str | None = None, templates: list[WhatsAppRemoteTemplate] | None = None) -> None:
        self.fail_code = fail_code
        self.templates = templates or [
            WhatsAppRemoteTemplate(id="tmpl_fake_1", name="appointment_confirmation_13_1c", language="es_CL", category="UTILITY", status="APPROVED")
        ]
        self.sent_payloads: list[dict[str, Any]] = []

    def get_phone_number(self, *, graph_api_version: str, phone_number_id: str, access_token: str) -> WhatsAppPhoneNumberInfo:
        self._maybe_fail()
        return WhatsAppPhoneNumberInfo(id=phone_number_id, display_phone_number="+56 9 **** 5678", verified_name="RealMeet Demo")

    def list_templates(self, *, graph_api_version: str, waba_id: str, access_token: str) -> list[WhatsAppRemoteTemplate]:
        self._maybe_fail()
        return self.templates

    def send_template_message(
        self,
        *,
        graph_api_version: str,
        phone_number_id: str,
        access_token: str,
        to_e164: str,
        template_name: str,
        language: str,
        body_variables: list[str],
    ) -> WhatsAppSendResult:
        self._maybe_fail()
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language}, "components": body_variables},
            "url": f"https://graph.facebook.com/{graph_api_version}/{phone_number_id}/messages",
        }
        self.sent_payloads.append(payload)
        return WhatsAppSendResult(external_message_id=f"wamid.fake.{len(self.sent_payloads)}", raw_status="accepted")

    def _maybe_fail(self) -> None:
        if self.fail_code == "rate_limit":
            raise WhatsAppCloudClientError("Rate limit WhatsApp", code="whatsapp_rate_limited", status_code=429)
        if self.fail_code == "timeout":
            raise WhatsAppCloudClientError("Timeout WhatsApp", code="whatsapp_timeout")
        if self.fail_code:
            raise WhatsAppCloudClientError("Error fake WhatsApp", code=self.fail_code)
