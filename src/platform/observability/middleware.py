from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.platform.observability.context import normalize_request_id, reset_request_id, set_request_id
from src.platform.observability.metrics import metrics_registry, normalize_route

_LOG = logging.getLogger("isi.request")
_CallNext = Callable[[Request], Awaitable[Response]]


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        request_id = normalize_request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started = time.perf_counter()
        response: Response | None = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed_ms = max((time.perf_counter() - started) * 1000.0, 0.0)
            route_definition = request.scope.get("route")
            route_path = getattr(route_definition, "path", None)
            route = normalize_route(route_path) if isinstance(route_path, str) else "/unmatched"
            outcome = "success" if status_code < 500 else "error"
            request_labels = {
                "method": request.method,
                "route": route,
                "status_class": f"{status_code // 100}xx",
                "outcome": outcome,
            }
            metrics_registry.increment("isi_http_requests_total", labels=request_labels)
            metrics_registry.observe(
                "isi_http_request_latency_ms",
                elapsed_ms,
                labels={"method": request.method, "route": route, "outcome": outcome},
            )
            _LOG.info(
                "request.completed",
                extra={
                    "event": "request.completed",
                    "method": request.method,
                    "route": route,
                    "status_class": request_labels["status_class"],
                    "outcome": outcome,
                },
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            reset_request_id(token)
