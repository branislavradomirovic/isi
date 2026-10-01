import pytest

from tools.performance.evidence import summarize
from tools.performance.harness import run
from tools.performance.scenarios import prepared, ordo_operation, simpa_operation
from tools.performance.workloads import catalogue


@pytest.mark.parametrize("category", ["simpa", "ordo"])
def test_repeated_concurrent_domain_results(category):
    workload = next(w for w in catalogue() if w.category == category)
    with prepared(workload) as operation:
        result = run(workload, operation, repository_sha="a" * 40)
    assert summarize(result)["accepted"]
    assert len({s.operation.result_sha256 for s in result.measured}) == 1


def test_non_causal_and_not_estimated_semantics():
    assert all(r["non_causal"] for r in simpa_operation())
    result = ordo_operation()
    assert result[-1] == {"status": "NOT_ESTIMATED", "reason": "SEASONAL_PERIOD_REQUIRED"}
    assert result[-2] == {"status": "NOT_ESTIMATED", "reason": "EXECUTABLE_FAMILY_NOT_DEFINED_24C"}
    from types import SimpleNamespace
    from src.domains.ordo.analytics_service import _scenario_assessment_payload
    payload = _scenario_assessment_payload(
        scenario=SimpleNamespace(name="Synthetic", assumptions=["Synthetic"], measures=["Synthetic"]),
        goal=SimpleNamespace(code="G", title="Synthetic", focus_area="custom", target_horizon=None),
        run=SimpleNamespace(snapshot={}, analytical_artifact_fingerprint="", dataset_contract_fingerprint=""),
    )
    assert payload["forecast_performed"] is False
    assert payload["impact"] == "NOT_ESTIMATED"
    assert payload["impact_estimation_reason_code"] == "NO_APPROVED_RESPONSE_MODEL"
