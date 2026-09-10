from __future__ import annotations

import json

from src.platform.observability.readiness import ComponentStatus, collect_readiness


def test_readiness_aggregates_safe_component_codes() -> None:
    snapshot = collect_readiness(
        [
            lambda: ComponentStatus("postgres", "ready", "ok"),
            lambda: ComponentStatus("redis", "not_required", "inline_backends"),
            lambda: ComponentStatus("object_storage", "ready", "local_storage_available"),
        ]
    )
    assert snapshot["status"] == "ready"
    rendered = json.dumps(snapshot)
    assert "postgresql://" not in rendered
    assert "redis://" not in rendered
    assert "/tmp/" not in rendered


def test_readiness_fails_closed_without_exception_text() -> None:
    def broken() -> ComponentStatus:
        raise RuntimeError("postgresql://user:password@secret-host/private")

    snapshot = collect_readiness([broken])
    assert snapshot == {
        "status": "not_ready",
        "components": [{"component": "diagnostic", "state": "unhealthy", "reason_code": "check_failed"}],
    }
    assert "secret-host" not in json.dumps(snapshot)
