from __future__ import annotations

import re
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, environment: str = "development") -> None:
        super().__init__(app)
        self.environment = environment.strip().casefold()

    async def dispatch(self, request: Request, call_next):
        supplied = request.headers.get("x-request-id", "").strip()
        request_id = supplied if _REQUEST_ID.fullmatch(supplied) else secrets.token_hex(16)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        response.headers["X-Request-ID"] = request_id
        if request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store"
        if self.environment == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
