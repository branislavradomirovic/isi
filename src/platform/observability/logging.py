from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from src.platform.observability.context import current_request_id

_SENSITIVE = re.compile(r"(?i)(authorization|cookie|password|token|secret|api[_-]?key)\s*[:=]\s*([^\s,;]+)")
_ALLOWED_EXTRA = {"component", "event", "outcome", "reason_code", "route", "method", "status_class", "provider", "model", "prompt", "product"}


def redact(value: object) -> str:
    return _SENSITIVE.sub(lambda match: f"{match.group(1)}=[REDACTED]", str(value))


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
