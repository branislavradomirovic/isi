from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import Settings
from src.core.logging import configure_logging
from src.platform.observability.errors import unhandled_exception_response
from src.platform.observability.logging import JsonFormatter
from src.platform.observability.metrics import metrics_registry
from src.platform.observability.middleware import ObservabilityMiddleware
from src.platform.observability.telemetry import (
    record_ai_execution,
    record_ingestion,
    record_queue_dispatch,
    record_worker_execution,
)


def _app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(Exception, unhandled_exception_response)
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/items/{item_id}")
    def item(item_id: str) -> dict[str, str]:
        return {"item_id": item_id}

    @app.get("/explode")
    def explode() -> None:
        raise RuntimeError("secret exception detail must not be returned")

    return app


def test_request_id_propagation_and_route_privacy() -> None:
    metrics_registry.reset()
    client = TestClient(_app())
    response = client.get("/items/customer-alice@example.com?token=do-not-record", headers={"X-Request-ID": "req-12345678"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-12345678"

    replacement = client.get("/items/67890", headers={"X-Request-ID": "bad id with spaces"})
    assert replacement.status_code == 200
    assert replacement.headers["X-Request-ID"] != "bad id with spaces"
    assert len(replacement.headers["X-Request-ID"]) == 32

    encoded = json.dumps(metrics_registry.as_dict())
    assert "do-not-record" not in encoded
    assert "customer-alice" not in encoded
    assert "67890" not in encoded
    assert "/items/:id" in encoded


def test_unmatched_routes_do_not_become_metric_labels() -> None:
    metrics_registry.reset()
    client = TestClient(_app())
    response = client.get("/private-customer-name/not-a-real-route")
    assert response.status_code == 404
    encoded = json.dumps(metrics_registry.as_dict())
    assert "private-customer-name" not in encoded
    assert "/unmatched" in encoded


def test_unhandled_500_preserves_request_id_without_exception_text() -> None:
    metrics_registry.reset()
    client = TestClient(_app(), raise_server_exceptions=False)
    response = client.get("/explode", headers={"X-Request-ID": "req-error-123"})
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "req-error-123"
    assert response.text == "Internal Server Error"
    assert "secret exception" not in response.text


def test_structured_log_redacts_credentials() -> None:
    record = logging.LogRecord(
        name="isi.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="authorization=Bearer super-secret; token=token-value",
        args=(),
        exc_info=None,
    )
    payload = json.loads(JsonFormatter().format(record))
    rendered = json.dumps(payload)
    assert "super-secret" not in rendered
    assert "token-value" not in rendered
    assert "[REDACTED]" in rendered
    assert set(payload) >= {"timestamp", "level", "logger", "message", "request_id"}


def test_isi_logger_is_json_even_when_root_is_preconfigured() -> None:
    root = logging.getLogger()
    sentinel = logging.StreamHandler()
    root.addHandler(sentinel)
    isi_logger = logging.getLogger("isi")
    original_handlers = list(isi_logger.handlers)
    original_level = isi_logger.level
    original_propagate = isi_logger.propagate
    try:
        configure_logging()
        assert len(isi_logger.handlers) == 1
        assert isinstance(isi_logger.handlers[0].formatter, JsonFormatter)
        assert isi_logger.propagate is False
    finally:
        isi_logger.handlers[:] = original_handlers
        isi_logger.setLevel(original_level)
        isi_logger.propagate = original_propagate
        root.removeHandler(sentinel)


def test_metrics_and_telemetry_are_bounded_and_exportable() -> None:
    metrics_registry.reset()
    record_queue_dispatch(job_kind="ai", backend="rq", outcome="accepted")
    record_worker_execution(job_kind="ai", outcome="succeeded", duration_ms=12.5)
    record_ai_execution(
        provider="ollama",
        model_key="isi-ollama-chat-default",
        prompt_key="foundation.diagnostic",
        product_code="SIMPA",
        outcome="succeeded",
        duration_ms=10.0,
    )
    record_ingestion(detected_format="csv", outcome="succeeded", row_count=12, column_count=4, duration_ms=8.0)

    payload = metrics_registry.as_dict()
    assert payload["metrics"]
    prometheus = metrics_registry.as_prometheus()
    assert "isi_queue_dispatch_total" in prometheus
    assert "isi_ai_executions_total" in prometheus
    assert "isi_ingestion_rows_count" in prometheus
    assert "SIMPA" in prometheus
    assert Settings().observability_http_metrics_enabled is False
