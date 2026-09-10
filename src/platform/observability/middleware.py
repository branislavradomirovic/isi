from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.platform.observability.context import normalize_request_id, reset_request_id, set_request_id
from src.platform.observability.metrics import metrics_registry, normalize_route

_LOG = logging.getLogger("isi.request")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = normalize_request_id(request.headers.get("X-Request-ID"))
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
            route = normalize_route(request.url.path)
            labels = {
                "method": request.method,
                "route": route,
                "status_class": f"{status_code // 100}xx",
            }
            metrics_registry.increment("isi_http_requests_total", labels=labels)
            metrics_registry.observe("isi_http_request_latency_ms", elapsed_ms, labels={"method": request.method, "route": route})
            _LOG.info("request.completed", extra={"event": "request.completed", "method": request.method, "route": route, "status_class": labels["status_class"]})
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            reset_request_id(token)
