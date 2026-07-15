from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class WebhookClientResult:
    success: bool
    status_code: int | None
    duration_ms: int
    error_code: str | None = None
    error_message: str | None = None


class OutboundWebhookClient(Protocol):
    def send(self, *, target_url: str, headers: dict[str, str], json_payload: dict) -> WebhookClientResult:
        ...


class HttpOutboundWebhookClient:
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    def send(self, *, target_url: str, headers: dict[str, str], json_payload: dict) -> WebhookClientResult:
        import time

        started = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = client.post(target_url, headers=headers, json=json_payload)
            duration = int((time.perf_counter() - started) * 1000)
            if 200 <= response.status_code < 300:
                return WebhookClientResult(success=True, status_code=response.status_code, duration_ms=duration)
            return WebhookClientResult(
                success=False,
                status_code=response.status_code,
                duration_ms=duration,
                error_code="webhook_http_error",
                error_message="El endpoint respondio con un estado no exitoso.",
            )
        except httpx.TimeoutException:
            duration = int((time.perf_counter() - started) * 1000)
            return WebhookClientResult(False, None, duration, "webhook_timeout", "El endpoint no respondio dentro del tiempo esperado.")
        except httpx.HTTPError:
            duration = int((time.perf_counter() - started) * 1000)
            return WebhookClientResult(False, None, duration, "webhook_http_failure", "No pudimos entregar el webhook.")


class FakeOutboundWebhookClient:
    def __init__(self, *, should_fail: bool = False, status_code: int = 202) -> None:
        self.should_fail = should_fail
        self.status_code = status_code
        self.calls: list[dict] = []

    def send(self, *, target_url: str, headers: dict[str, str], json_payload: dict) -> WebhookClientResult:
        self.calls.append({"target_url": target_url, "headers": headers, "json_payload": json_payload})
        if self.should_fail:
            return WebhookClientResult(False, self.status_code, 1, "fake_webhook_failed", "Fallo fake controlado.")
        return WebhookClientResult(True, self.status_code, 1)
