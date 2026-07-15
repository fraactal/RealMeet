from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings


SENSITIVE_CACHE_PATHS = (
    "/api/v1/auth",
    "/api/v1/users",
    "/api/v1/appointments",
    "/api/v1/admin",
    "/api/v1/client/metrics",
    "/api/v1/professional/metrics",
)

RATE_LIMITED_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/appointments"),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.path.startswith(SENSITIVE_CACHE_PATHS):
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("Pragma", "no-cache")
        return response


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: defaultdict[tuple[str, str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        route_key = (request.method.upper(), request.url.path)
        if not settings.rate_limit_enabled or route_key not in RATE_LIMITED_ROUTES:
            return await call_next(request)

        now = monotonic()
        window = settings.rate_limit_window_seconds
        key = (request.client.host if request.client else "unknown", route_key[0], route_key[1])
        hits = self._hits[key]
        while hits and now - hits[0] >= window:
            hits.popleft()

        if len(hits) >= settings.rate_limit_max_requests:
            retry_after = max(1, int(window - (now - hits[0]))) if hits else window
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        return await call_next(request)

    def reset(self) -> None:
        self._hits.clear()
