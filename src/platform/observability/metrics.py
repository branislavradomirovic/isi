from __future__ import annotations

import json
import re
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping

_LABEL_RE = re.compile(r"[^A-Za-z0-9_.:-]+")
_DYNAMIC_SEGMENT_RE = re.compile(r"^(?:[0-9]+|[0-9a-fA-F]{16,}|[0-9a-fA-F-]{32,})$")


def safe_label(value: object, *, max_length: int = 64) -> str:
    text = str(value or "unknown").strip()
    text = _LABEL_RE.sub("_", text)[:max_length]
    return text or "unknown"


def normalize_route(path: str) -> str:
    clean = path.split("?", 1)[0]
    segments = []
    for segment in clean.split("/"):
        if not segment:
            continue
        segments.append(":id" if _DYNAMIC_SEGMENT_RE.match(segment) else safe_label(segment))
    return "/" + "/".join(segments)


@dataclass(frozen=True)
class MetricKey:
    name: str
    labels: tuple[tuple[str, str], ...]


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[MetricKey, float] = defaultdict(float)
        self._sums: dict[MetricKey, float] = defaultdict(float)

    @staticmethod
    def _key(name: str, labels: Mapping[str, object] | None = None) -> MetricKey:
        items = tuple(sorted((safe_label(k), safe_label(v)) for k, v in (labels or {}).items()))
        return MetricKey(safe_label(name), items)

    def increment(self, name: str, *, labels: Mapping[str, object] | None = None, value: float = 1.0) -> None:
        with self._lock:
            self._counters[self._key(name, labels)] += float(value)

    def observe(self, name: str, value: float, *, labels: Mapping[str, object] | None = None) -> None:
        with self._lock:
            key = self._key(name, labels)
            self._counters[MetricKey(key.name + "_count", key.labels)] += 1.0
            self._sums[MetricKey(key.name + "_sum", key.labels)] += float(value)

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._sums.clear()

    def as_dict(self) -> dict[str, object]:
        with self._lock:
            rows = []
            for key, value in sorted({**self._counters, **self._sums}.items(), key=lambda item: (item[0].name, item[0].labels)):
                rows.append({"name": key.name, "labels": dict(key.labels), "value": value})
        return {"metrics": rows}

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))

    def as_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            values = {**self._counters, **self._sums}
            for key, value in sorted(values.items(), key=lambda item: (item[0].name, item[0].labels)):
                label_text = ""
                if key.labels:
                    encoded = ",".join(f'{k}="{v}"' for k, v in key.labels)
                    label_text = "{" + encoded + "}"
                lines.append(f"{key.name}{label_text} {value:g}")
        return "\n".join(lines) + ("\n" if lines else "")


metrics_registry = MetricsRegistry()
