import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tools.performance.evidence import render, summarize
from tools.performance.harness import run
from tools.performance.scenarios import prepared
from tools.performance.workloads import catalogue


@pytest.mark.parametrize("workload", [w for w in catalogue() if w.category == "api"])
def test_concurrent_api_contract_and_scope(workload):
    with prepared(workload) as operation:
        result = run(workload, operation, repository_sha="a" * 40)
    assert summarize(result)["accepted"]
    assert len({s.operation.result_sha256 for s in result.measured}) == 1
    evidence = render(result)
    for forbidden in ("Bearer", "Authorization", "example.test", "workspace_id", "organization_id", "password"):
        assert forbidden not in evidence


def test_dependency_failure_is_safe_http_503_and_recovers():
    from src.api.diagnostics_routes import router
    from src.platform.observability.readiness import ComponentStatus, collect_readiness
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        for component in ("postgres", "redis", "object_storage"):
            for state in ("unhealthy", "ready"):
                snapshot = collect_readiness([lambda: ComponentStatus(component, state, "synthetic")])
                with patch("src.api.diagnostics_routes.readiness_snapshot", return_value=snapshot):
                    response = client.get("/api/v1/diagnostics/readiness")
                assert response.status_code == (503 if state == "unhealthy" else 200)
                assert response.json() == snapshot
                assert "exception" not in json.dumps(response.json())
