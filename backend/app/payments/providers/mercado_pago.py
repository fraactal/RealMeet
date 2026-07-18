from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import hmac
import os
from time import monotonic
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.integrations.enums import IntegrationProvider, IntegrationStatus, IntegrationType
from app.integrations.exceptions import IntegrationConfigurationError, IntegrationProviderExecutionError
from app.integrations.results import IntegrationResult
from app.models.integration import Integration
from app.payments.enums import PaymentCurrency, PaymentOrderStatus


MERCADO_PAGO_API_URL = "https://api.mercadopago.com"
SENSITIVE_CONFIG_KEYS = {"access_token", "token", "client_secret", "secret", "authorization"}


@dataclass(frozen=True)
class MercadoPagoPreferenceResult:
    preference_id: str
    init_point: str | None
    sandbox_init_point: str | None
    status: str | None
    provider_reference: dict[str, str | int | bool | None]


@dataclass(frozen=True)
class MercadoPagoPaymentResult:
    payment_id: str
    status: str
    status_detail: str | None
    external_reference: str | None
    preference_id: str | None
    metadata_payment_order_id: int | None
    metadata_appointment_id: int | None
    provider_reference: dict[str, str | int | bool | None]


@dataclass(frozen=True)
class MercadoPagoRefundResult:
    external_refund_id: str
    status: str
    amount: Decimal
    currency: PaymentCurrency
    provider_reference: dict[str, str | int | bool | None]
    processed_at: datetime | None = None

@dataclass(frozen=True)
class MercadoPagoHealthResult:
    healthy: bool
    code: str
    message: str
    metadata: dict[str, str | int | bool | None]
    duration_ms: int = 0


class MercadoPagoClient:
    def __init__(self, access_token: str, *, base_url: str = MERCADO_PAGO_API_URL, timeout_seconds: float = 10.0) -> None:
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)

    def create_preference(self, payload: dict[str, Any], *, idempotency_key: str) -> MercadoPagoPreferenceResult:
        started = monotonic()
        response = httpx.post(
            f"{self.base_url}/checkout/preferences",
            headers=self._headers(idempotency_key),
            json=payload,
            timeout=self.timeout,
        )
        data = self._json_or_error(response)
        return MercadoPagoPreferenceResult(
            preference_id=str(data.get("id") or ""),
            init_point=data.get("init_point"),
            sandbox_init_point=data.get("sandbox_init_point"),
            status=data.get("status"),
            provider_reference={
                "provider": "mercado_pago",
                "operation": "create_preference",
                "preference_id": str(data.get("id") or ""),
                "duration_ms": int((monotonic() - started) * 1000),
            },
        )

    def get_payment(self, payment_id: str) -> MercadoPagoPaymentResult:
        response = httpx.get(f"{self.base_url}/v1/payments/{payment_id}", headers=self._headers(), timeout=self.timeout)
        data = self._json_or_error(response)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        return MercadoPagoPaymentResult(
            payment_id=str(data.get("id") or payment_id),
            status=str(data.get("status") or "unknown"),
            status_detail=data.get("status_detail"),
            external_reference=data.get("external_reference"),
            preference_id=str(data.get("preference_id")) if data.get("preference_id") is not None else None,
            metadata_payment_order_id=_safe_int(metadata.get("realmeet_payment_order_id")),
            metadata_appointment_id=_safe_int(metadata.get("realmeet_appointment_id")),
            provider_reference={
                "provider": "mercado_pago",
                "operation": "get_payment",
                "payment_id": str(data.get("id") or payment_id),
                "status": str(data.get("status") or "unknown"),
            },
        )

    def get_preference(self, preference_id: str) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}/checkout/preferences/{preference_id}", headers=self._headers(), timeout=self.timeout)
        return self._json_or_error(response)

    def health_check(self) -> MercadoPagoHealthResult:
        started = monotonic()
        response = httpx.get(f"{self.base_url}/users/me", headers=self._headers(), timeout=self.timeout)
        data = self._json_or_error(response)
        return MercadoPagoHealthResult(
            healthy=True,
            code="mercado_pago_health_ok",
            message="Mercado Pago disponible.",
            metadata={"account_id": str(data.get("id") or ""), "site_id": data.get("site_id")},
            duration_ms=int((monotonic() - started) * 1000),
        )

    def create_refund(self, payment_id: str, *, amount: Decimal, currency: PaymentCurrency, idempotency_key: str) -> MercadoPagoRefundResult:
        payload: dict[str, Any] = {}
        if amount > 0:
            payload["amount"] = int(amount) if currency == PaymentCurrency.CLP else float(amount)
        response = httpx.post(f"{self.base_url}/v1/payments/{payment_id}/refunds", headers=self._headers(idempotency_key), json=payload, timeout=self.timeout)
        data = self._json_or_error(response)
        return _refund_from_payload(data, currency=currency)

    def get_refund(self, payment_id: str, refund_id: str, *, currency: PaymentCurrency = PaymentCurrency.CLP) -> MercadoPagoRefundResult:
        response = httpx.get(f"{self.base_url}/v1/payments/{payment_id}/refunds/{refund_id}", headers=self._headers(), timeout=self.timeout)
        data = self._json_or_error(response)
        return _refund_from_payload(data, currency=currency)

    def cancel_payment(self, _: str) -> None:
        raise IntegrationProviderExecutionError("Cancelacion Mercado Pago no soportada en 17.3", code="mercado_pago_cancel_not_supported")

    def refund_payment(self, _: str) -> None:
        raise IntegrationProviderExecutionError("Reembolso Mercado Pago no soportado en 17.3", code="mercado_pago_refund_not_supported")

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        return headers

    @staticmethod
    def _json_or_error(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise IntegrationProviderExecutionError("Mercado Pago rechazo la operacion.", code=f"mercado_pago_http_{response.status_code}")
        data = response.json()
        if not isinstance(data, dict):
            raise IntegrationProviderExecutionError("Respuesta Mercado Pago invalida.", code="mercado_pago_invalid_response")
        return data


class MercadoPagoIntegrationProvider:
    def validate_configuration(self, integration: Integration) -> IntegrationResult:
        config = parse_mercado_pago_config(integration)
        return IntegrationResult.ok(
            code="mercado_pago_config_valid",
            message="Configuracion Mercado Pago valida.",
            metadata={"provider": "mercado_pago", "environment": config["environment"], "currency": config["currency"]},
        )

    def health_check(self, integration: Integration) -> IntegrationResult:
        config = parse_mercado_pago_config(integration)
        token = resolve_secret_reference(config["access_token_reference"])
        result = mercado_pago_client_factory(token).health_check()
        return IntegrationResult(
            success=result.healthy,
            code=result.code,
            message=result.message,
            metadata=result.metadata,
            duration_ms=result.duration_ms,
        )

    def execute(self, integration: Integration, operation: str, payload: dict | None = None) -> IntegrationResult:
        if operation == "health_check":
            return self.health_check(integration)
        raise IntegrationProviderExecutionError("Operacion Mercado Pago no soportada.", code="mercado_pago_operation_not_supported")


def parse_mercado_pago_config(integration: Integration) -> dict[str, Any]:
    if integration.integration_type != IntegrationType.payment or integration.provider != IntegrationProvider.mercado_pago:
        raise IntegrationConfigurationError("La integracion no es Mercado Pago de pagos.", code="mercado_pago_integration_mismatch")
    config = dict(integration.config or {})
    for key in SENSITIVE_CONFIG_KEYS:
        if key in config:
            raise IntegrationConfigurationError("La configuracion no puede contener secretos directos.", code="mercado_pago_secret_in_config")
    secret_refs = config.get("secret_references") if isinstance(config.get("secret_references"), dict) else {}
    access_ref = config.get("access_token_reference") or secret_refs.get("access_token")
    webhook_ref = config.get("webhook_secret_reference") or secret_refs.get("webhook_secret")
    environment = config.get("environment", "sandbox")
    currency = config.get("currency", "CLP")
    if environment not in {"sandbox", "production"}:
        raise IntegrationConfigurationError("Ambiente Mercado Pago invalido.", code="mercado_pago_environment_invalid")
    if environment == "production" and not config.get("production_enabled"):
        raise IntegrationConfigurationError("Produccion Mercado Pago requiere habilitacion explicita.", code="mercado_pago_production_not_enabled")
    if currency != PaymentCurrency.CLP.value:
        raise IntegrationConfigurationError("Mercado Pago 17.3 solo soporta CLP.", code="mercado_pago_currency_not_supported")
    if not access_ref:
        raise IntegrationConfigurationError("Falta referencia de access token.", code="mercado_pago_access_token_reference_missing")
    if not webhook_ref:
        raise IntegrationConfigurationError("Falta referencia de webhook secret.", code="mercado_pago_webhook_secret_reference_missing")
    _validate_reference(access_ref)
    _validate_reference(webhook_ref)
    for key in ("notification_url", "success_url", "pending_url", "failure_url"):
        _validate_url(str(config.get(key) or ""), key=key)
    if "/api/" not in str(config.get("notification_url")) or "mercado-pago" not in str(config.get("notification_url")):
        raise IntegrationConfigurationError("notification_url debe apuntar al backend Mercado Pago.", code="mercado_pago_notification_url_invalid")
    return {
        **config,
        "environment": environment,
        "country": config.get("country", "CL"),
        "currency": currency,
        "access_token_reference": access_ref,
        "webhook_secret_reference": webhook_ref,
        "auto_return": config.get("auto_return", "approved"),
    }


def build_preference_payload(*, order_id: int, appointment_id: int | None, amount: Decimal, currency: PaymentCurrency, description: str, config: dict[str, Any], payer_email: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "items": [
            {
                "id": f"realmeet-payment-order-{order_id}",
                "title": description[:120] or "Reserva RealMeet",
                "quantity": 1,
                "currency_id": currency.value,
                "unit_price": int(amount),
            }
        ],
        "external_reference": f"payment-order-{order_id}",
        "notification_url": config["notification_url"],
        "back_urls": {
            "success": config["success_url"],
            "pending": config["pending_url"],
            "failure": config["failure_url"],
        },
        "auto_return": config.get("auto_return", "approved"),
        "metadata": {
            "realmeet_payment_order_id": order_id,
            "realmeet_appointment_id": appointment_id,
        },
    }
    if payer_email and "@" in payer_email:
        payload["payer"] = {"email": payer_email}
    return payload


def map_mercado_pago_status(provider_status: str) -> PaymentOrderStatus | None:
    mapping = {
        "approved": PaymentOrderStatus.approved,
        "pending": PaymentOrderStatus.pending,
        "in_process": PaymentOrderStatus.requires_action,
        "authorized": PaymentOrderStatus.requires_action,
        "rejected": PaymentOrderStatus.rejected,
        "cancelled": PaymentOrderStatus.cancelled,
        "refunded": PaymentOrderStatus.refunded,
        "charged_back": PaymentOrderStatus.failed,
    }
    return mapping.get((provider_status or "").strip().lower())


def verify_mercado_pago_signature(*, x_signature: str | None, x_request_id: str | None, data_id: str | None, secret: str) -> bool:
    if not x_signature or not secret:
        return False
    parts = {}
    for part in x_signature.split(","):
        key, _, value = part.partition("=")
        if key.strip() and value.strip():
            parts[key.strip()] = value.strip()
    ts = parts.get("ts")
    expected = parts.get("v1")
    if not ts or not expected:
        return False
    normalized_id = (data_id or "").lower()
    manifest = ""
    if normalized_id:
        manifest += f"id:{normalized_id};"
    if x_request_id:
        manifest += f"request-id:{x_request_id};"
    manifest += f"ts:{ts};"
    digest = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def resolve_secret_reference(reference: str) -> str:
    value = os.environ.get(reference)
    if not value:
        raise IntegrationConfigurationError("Referencia secreta no configurada.", code="mercado_pago_secret_reference_not_configured")
    return value


def mercado_pago_client_factory(access_token: str) -> MercadoPagoClient:
    return MercadoPagoClient(access_token)


def _validate_reference(value: str) -> None:
    if not value.isupper() or not value.replace("_", "").isalnum():
        raise IntegrationConfigurationError("Referencia secreta invalida.", code="mercado_pago_secret_reference_invalid")


def _validate_url(value: str, *, key: str) -> None:
    parsed = urlparse(value)
    if parsed.fragment or not parsed.scheme or not parsed.netloc:
        raise IntegrationConfigurationError(f"{key} invalida.", code=f"mercado_pago_{key}_invalid")
    if parsed.username or parsed.password:
        raise IntegrationConfigurationError(f"{key} no puede contener credenciales.", code=f"mercado_pago_{key}_credentials")
    local_hosts = {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and parsed.hostname not in local_hosts and settings.app_env != "local":
        raise IntegrationConfigurationError(f"{key} debe usar HTTPS.", code=f"mercado_pago_{key}_https_required")
    if key != "notification_url" and settings.cors_origins:
        allowed = {urlparse(origin).netloc for origin in settings.cors_origins}
        if parsed.netloc not in allowed and parsed.hostname not in local_hosts:
            raise IntegrationConfigurationError(f"{key} no pertenece a origen permitido.", code=f"mercado_pago_{key}_origin_not_allowed")



def _refund_from_payload(data: dict[str, Any], *, currency: PaymentCurrency) -> MercadoPagoRefundResult:
    status = str(data.get("status") or "unknown")
    amount = Decimal(str(data.get("amount") or data.get("transaction_amount") or 0))
    processed_at = None
    raw_date = data.get("date_created") or data.get("date_approved")
    if isinstance(raw_date, str):
        try:
            processed_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except ValueError:
            processed_at = None
    return MercadoPagoRefundResult(
        external_refund_id=str(data.get("id") or ""),
        status=status,
        amount=amount,
        currency=currency,
        processed_at=processed_at,
        provider_reference={"provider": "mercado_pago", "operation": "refund", "refund_id": str(data.get("id") or ""), "status": status},
    )

def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
