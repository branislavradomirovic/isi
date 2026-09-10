from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from redis import Redis
from sqlalchemy import create_engine, text

from src.core.config import Settings, get_settings
from src.platform.data.storage import S3CompatibleStorage

_CODE_RE = re.compile(r"[^a-z0-9_.-]+")


@dataclass(frozen=True)
class ComponentStatus:
    component: str
    state: str
    reason_code: str


def _code(value: object) -> str:
    normalized = _CODE_RE.sub("_", str(value).strip().lower())[:80]
    return normalized or "unknown"


def _status(component: str, state: str, reason_code: str) -> ComponentStatus:
    return ComponentStatus(_code(component), _code(state), _code(reason_code))


def check_postgres(settings: Settings | None = None) -> ComponentStatus:
    current = settings or get_settings()
    engine = None
    try:
        engine = create_engine(current.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return _status("postgres", "ready", "ok")
    except Exception:
        return _status("postgres", "unhealthy", "database_unavailable")
    finally:
        if engine is not None:
            engine.dispose()


def check_redis(settings: Settings | None = None) -> ComponentStatus:
    current = settings or get_settings()
    rq_required = str(current.ai_job_backend).lower() == "rq" or str(current.data_job_backend).lower() == "rq"
    if not rq_required:
        return _status("redis", "not_required", "inline_backends")
    try:
        client = Redis.from_url(current.redis_url, socket_connect_timeout=2, socket_timeout=2)
        if client.ping():
            return _status("redis", "ready", "ok")
        return _status("redis", "unhealthy", "redis_unavailable")
    except Exception:
        return _status("redis", "unhealthy", "redis_unavailable")


def check_storage(settings: Settings | None = None) -> ComponentStatus:
    current = settings or get_settings()
    backend = str(current.data_storage_backend).lower()
    if backend == "local":
        root = Path(current.data_storage_root).expanduser()
        probe = root if root.exists() else root.parent
        if probe.exists() and os.access(probe, os.R_OK | os.W_OK):
            return _status("object_storage", "ready", "local_storage_available")
        return _status("object_storage", "unhealthy", "local_storage_unavailable")
    if backend == "s3":
        try:
            storage = S3CompatibleStorage(
                bucket=current.data_s3_bucket,
                endpoint_url=current.data_s3_endpoint_url,
                access_key_id=current.data_s3_access_key_id,
                secret_access_key=current.data_s3_secret_access_key,
                region=current.data_s3_region,
            )
            storage._client().head_bucket(Bucket=storage.bucket)
            return _status("object_storage", "ready", "s3_storage_available")
        except Exception:
            return _status("object_storage", "unhealthy", "s3_storage_unavailable")
    return _status("object_storage", "unhealthy", "unsupported_storage_backend")


def collect_readiness(checks: Iterable[Callable[[], ComponentStatus]]) -> dict[str, object]:
    results: list[ComponentStatus] = []
    for check in checks:
        try:
            result = check()
        except Exception:
            result = _status("diagnostic", "unhealthy", "check_failed")
        results.append(_status(result.component, result.state, result.reason_code))
    ready = all(item.state in {"ready", "not_required"} for item in results)
    return {
        "status": "ready" if ready else "not_ready",
        "components": [asdict(item) for item in results],
    }


def readiness_snapshot(settings: Settings | None = None) -> dict[str, object]:
    current = settings or get_settings()
    return collect_readiness(
        [
            lambda: check_postgres(current),
            lambda: check_redis(current),
            lambda: check_storage(current),
        ]
    )
