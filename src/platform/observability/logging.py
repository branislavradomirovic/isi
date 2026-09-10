from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from src.platform.observability.context import current_request_id

_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(authorization|cookie|set-cookie|password|passwd|token|secret|api[_-]?key)\b\s*[:=]\s*([^,;]+)"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_ALLOWED_EXTRA = {
    "component",
    "event",
    "outcome",
    "reason_code",
    "route",
    "method",
    "status_class",
    "provider",
    "model_key",
    "prompt_key",
    "product",
    "job_kind",
}


def redact(value: object) -> str:
    text = str(value)
    text = _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    return _BEARER.sub("Bearer [REDACTED]", text)[:2048]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
            "request_id": current_request_id(),
        }
        for field in _ALLOWED_EXTRA:
            if hasattr(record, field):
                payload[field] = redact(getattr(record, field))
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
