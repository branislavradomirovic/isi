from __future__ import annotations

from fastapi import Request
from starlette.responses import PlainTextResponse

from src.platform.observability.context import normalize_request_id


async def unhandled_exception_response(request: Request, exc: Exception) -> PlainTextResponse:
    """Return a content-free 500 while preserving the request correlation ID."""
    request_id = normalize_request_id(getattr(request.state, "request_id", None))
    return PlainTextResponse(
        "Internal Server Error",
        status_code=500,
        headers={"X-Request-ID": request_id},
    )
