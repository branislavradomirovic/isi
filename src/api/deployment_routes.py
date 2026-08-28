from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.core.config import get_settings
from src.platform.data.storage import StorageError, build_storage


router = APIRouter(prefix="/api/v1", tags=["deployment"])


@router.get("/readiness")
def deployment_readiness(db: Session = Depends(get_db)) -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error:{type(exc).__name__}"

    try:
        redis = Redis.from_url(settings.redis_url, socket_timeout=2, socket_connect_timeout=2)
        redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error:{type(exc).__name__}"

    try:
        storage = build_storage()
        storage.exists("__isi_readiness__/missing-object")
        checks["storage"] = "ok"
    except StorageError as exc:
        checks["storage"] = f"error:{type(exc).__name__}"
    except Exception as exc:
        checks["storage"] = f"error:{type(exc).__name__}"

    ready = all(value == "ok" for value in checks.values())
    payload: dict[str, object] = {"status": "ready" if ready else "not_ready", "checks": checks}
    if not ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=payload)
    return payload
