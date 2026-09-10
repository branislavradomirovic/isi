from __future__ import annotations

from src.platform.observability.metrics import metrics_registry


def record_queue_dispatch(*, job_kind: str, backend: str, outcome: str) -> None:
    metrics_registry.increment(
        "isi_queue_dispatch_total",
        labels={"job_kind": job_kind, "backend": backend, "outcome": outcome},
    )


def record_worker_execution(*, job_kind: str, outcome: str, duration_ms: float) -> None:
    labels = {"job_kind": job_kind, "outcome": outcome}
    metrics_registry.increment("isi_worker_executions_total", labels=labels)
    metrics_registry.observe("isi_worker_execution_latency_ms", duration_ms, labels=labels)


def record_ai_execution(
    *,
    provider: str,
    model_key: str,
    prompt_key: str,
    product_code: str,
    outcome: str,
    duration_ms: float,
) -> None:
    labels = {
        "provider": provider,
        "model_key": model_key,
        "prompt_key": prompt_key,
        "product": product_code,
        "outcome": outcome,
    }
    metrics_registry.increment("isi_ai_executions_total", labels=labels)
    metrics_registry.observe("isi_ai_execution_latency_ms", duration_ms, labels=labels)


def record_ingestion(
    *,
    detected_format: str,
    outcome: str,
    row_count: int,
    column_count: int,
    duration_ms: float,
) -> None:
    labels = {"format": detected_format, "outcome": outcome}
    metrics_registry.increment("isi_ingestion_executions_total", labels=labels)
    metrics_registry.observe("isi_ingestion_execution_latency_ms", duration_ms, labels=labels)
    metrics_registry.observe("isi_ingestion_rows", max(row_count, 0), labels=labels)
    metrics_registry.observe("isi_ingestion_columns", max(column_count, 0), labels=labels)
