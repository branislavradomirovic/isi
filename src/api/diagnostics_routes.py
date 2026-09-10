from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse

from src.core.config import get_settings
from src.platform.observability.metrics import metrics_registry
from src.platform.observability.readiness import readiness_snapshot

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])


@router.get("/readiness")
def readiness() -> JSONResponse:
    snapshot = readiness_snapshot()
    status_code = status.HTTP_200_OK if snapshot["status"] == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(snapshot, status_code=status_code)


def _require_metrics_enabled() -> None:
    if not bool(get_settings().observability_http_metrics_enabled):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="diagnostics endpoint disabled")


@router.get("/metrics")
def prometheus_metrics() -> PlainTextResponse:
    _require_metrics_enabled()
    return PlainTextResponse(metrics_registry.as_prometheus(), media_type="text/plain; version=0.0.4")


@router.get("/metrics.json")
def json_metrics() -> JSONResponse:
    _require_metrics_enabled()
    return JSONResponse(metrics_registry.as_dict())
