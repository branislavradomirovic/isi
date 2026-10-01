import json
import threading

import pytest
from pydantic import ValidationError

from tools.performance.contracts import Budget, BudgetClass, BudgetState, Operation, Result, Workload, fingerprint
from tools.performance.evidence import render, summarize, validate_record
from tools.performance.harness import nearest_rank, run
from tools.performance.workloads import catalogue

SHA = "a" * 40


def profile(**changes):
    return Workload.model_validate(catalogue()[0].model_dump() | changes)


def test_exact_vocabulary_and_closed_contract():
    assert set(BudgetClass) == {"CORRECTNESS", "LATENCY_THROUGHPUT", "RESOURCE", "RESILIENCE"}
    assert set(BudgetState) == {"HARD_GATE", "CALIBRATED", "UNCALIBRATED", "NOT_APPLICABLE", "UNAVAILABLE"}
    for change in ({"samples": 0}, {"samples": True}, {"concurrency": 17}, {"warmups": -1},
                   {"environment": "PRODUCTION"}, {"token": "unsafe"}, {"tenant_id": "unsafe"},
                   {"title": "user@example.test"}, {"workload_id": "unregistered"}, {"budgets": ()}):
        with pytest.raises(ValidationError):
            profile(**change)
    with pytest.raises(ValidationError):
        profile().samples = 1


def test_calibration_requires_accepted_evidence_and_margin():
    base = {"metric": "p95_seconds", "budget_class": "LATENCY_THROUGHPUT", "state": "CALIBRATED", "threshold": 2}
    with pytest.raises(ValidationError):
        Budget(**base)
    evidence = {"evidence_sha256": "a" * 64, "accepted_contract_sha256": "b" * 64,
                "repeated_runs": 3, "observed_bound": 1, "safety_margin": 2}
    assert Budget(**base, calibration=evidence).threshold == 2
    for change in ({"state": "invented"}, {"threshold": 1}, {"threshold": float("nan")},
                   {"budget_class": "CORRECTNESS"}):
        with pytest.raises(ValidationError):
            Budget(**(base | change), calibration=evidence)
    with pytest.raises(ValidationError):
        Budget(metric="correctness_failures", budget_class="CORRECTNESS", state="UNCALIBRATED")


def test_percentiles_exact_empty_and_invalid():
    assert nearest_rank([], .99) is None
    assert [nearest_rank(list(range(1, 101)), q) for q in (.5, .95, .99)] == [50, 95, 99]
    assert nearest_rank([7, 1, 4], .5) == 4
    for values, q in (([-1], .5), ([float("nan")], .5), ([float("inf")], .5), ([1], 0), ([1], 1.1)):
        with pytest.raises(ValueError):
            nearest_rank(values, q)


def test_fake_clock_warmups_failures_throughput_and_no_exception_text():
    values = iter([Operation(), Operation(), Operation(success=False, correct=True, reason="timeout")])
    clock = iter([0, 0, 1, 1, 3, 4])
    result = run(profile(samples=2, concurrency=1, expected_failures=("timeout",)), lambda: next(values),
                 repository_sha=SHA, clock=lambda: next(clock))
    summary = summarize(result)
    assert summary["completed"] == 2 and summary["successes"] == 1 and summary["failures"] == 1
    assert summary["correctness_pass"] and summary["metrics"]["throughput"] == .5
    assert summary["metrics"]["p50_seconds"] == 1 and summary["metrics"]["p99_seconds"] == 2
    assert validate_record(json.loads(render(result))) == result

    def broken():
        raise RuntimeError("sensitive raw exception")
    failed = run(profile(samples=2), broken, repository_sha=SHA)
    assert summarize(failed)["correctness_failures"] == 3
    assert "sensitive" not in render(failed)
    assert summarize(failed)["failure_codes"] == {"unexpected_exception": 2}


def test_nonpositive_duration_fails_closed_and_timing_does_not_change_contract():
    with pytest.raises(ValidationError):
        run(profile(samples=1), Operation, repository_sha=SHA, clock=lambda: 0)
    first = run(profile(samples=1), Operation, repository_sha=SHA)
    second = Result.model_validate(first.model_dump() | {"wall_seconds": first.wall_seconds * 2})
    assert first.contract_sha256 == second.contract_sha256 == fingerprint(first.contract)
    assert summarize(first)["correctness_pass"] == summarize(second)["correctness_pass"]
    assert render(first) != render(second)
    data = json.loads(render(first))
    data["summary"]["successes"] = 99
    with pytest.raises(ValueError):
        validate_record(data)


def test_unknown_fields_and_unsafe_failure_codes_are_rejected():
    for change in ({"reason": "secret exception"}, {"password": "unsafe"}, {"success": "true"}):
        with pytest.raises(ValidationError):
            Operation(**change)
    result = run(profile(samples=1), Operation, repository_sha=SHA)
    for change in ({"SERVER_VERIFIED": True}, {"hostname": "unsafe"}, {"measured": ()}):
        with pytest.raises(ValidationError):
            Result.model_validate(result.model_dump() | change)


def test_concurrency_is_real_bounded_and_counts_are_exact():
    barrier = threading.Barrier(3)
    active = 0
    peak = 0
    lock = threading.Lock()
    def operation():
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        barrier.wait(timeout=5)
        with lock:
            active -= 1
        return Operation()
    result = run(profile(samples=6, warmups=0, concurrency=3), operation, repository_sha=SHA)
    assert peak == 3 and summarize(result)["successes"] == 6
    assert result.effective_concurrency == 3


def test_catalogue_is_exact_and_all_budgets_truthful():
    assert {w.workload_id for w in catalogue()} == {
        "api.health.read.v1", "api.authenticated.context.v1", "api.authenticated.navigation.v1",
        "api.readiness.synthetic.v1", "data.ingestion.synthetic.v1", "simpa.analytics.synthetic.v1",
        "ordo.forecast.synthetic.v1", "report.render.synthetic.v1", "ai.stub.synthetic.v1", "ai.circuit.synthetic.v1"}
    assert len(catalogue()) == 10
    assert all(b.state != "CALIBRATED" for w in catalogue() for b in w.budgets)
