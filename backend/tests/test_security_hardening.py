from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import middleware
from app.core.middleware import InMemoryRateLimitMiddleware, SecurityHeadersMiddleware
from app.main import app


def test_security_headers_are_added_to_sensitive_response() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"


def test_sensitive_paths_disable_cache() -> None:
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/api/v1/auth/me")
    def auth_me() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(test_app).get("/api/v1/auth/me")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"


def test_rate_limit_returns_429(monkeypatch) -> None:
    test_app = FastAPI()
    test_app.add_middleware(InMemoryRateLimitMiddleware)

    @test_app.post("/api/v1/auth/login")
    def login() -> dict[str, str]:
        return {"status": "attempted"}

    monkeypatch.setattr(middleware.settings, "rate_limit_enabled", True)
    monkeypatch.setattr(middleware.settings, "rate_limit_window_seconds", 60)
    monkeypatch.setattr(middleware.settings, "rate_limit_max_requests", 1)

    client = TestClient(test_app)
    first = client.post("/api/v1/auth/login")
    second = client.post("/api/v1/auth/login")

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json() == {"detail": "Too many requests"}
    assert "Retry-After" in second.headers
