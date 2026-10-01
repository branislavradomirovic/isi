"""Evidence contains only typed counts, digests and bounded codes, never payloads."""
from __future__ import annotations

from collections import Counter

from tools.performance.contracts import BudgetState, Result, canonical_json, fingerprint
from tools.performance.harness import nearest_rank


def summarize(result: Result) -> dict:
    operations = [s.operation for s in result.measured]
    latencies = [s.seconds for s in result.measured]
    unexpected = sum(not op.correct or (not op.success and op.reason not in result.contract.expected_failures)
                     for op in operations)
    metrics = {
        "correctness_failures": unexpected + result.warmup_failures,
        "resilience_failures": unexpected + result.warmup_failures,
        "p50_seconds": nearest_rank(latencies, .50),
        "p95_seconds": nearest_rank(latencies, .95),
        "p99_seconds": nearest_rank(latencies, .99),
        "throughput": len(operations) / result.wall_seconds,
        "resource": None,
    }
    budget_pass = True
    for budget in result.contract.budgets:
        if budget.state == BudgetState.CALIBRATED:
            value = metrics[budget.metric]
            assert value is not None and budget.threshold is not None
            budget_pass &= value >= budget.threshold if budget.metric == "throughput" else value <= budget.threshold
    return {
        "completed": len(operations), "successes": sum(op.success for op in operations),
        "failures": sum(not op.success for op in operations),
        "correctness_passes": sum(op.correct for op in operations),
        "correctness_failures": metrics["correctness_failures"],
        "failure_codes": dict(sorted(Counter(op.reason for op in operations if not op.success).items())),
        "min_seconds": min(latencies), "max_seconds": max(latencies), "metrics": metrics,
        "correctness_pass": metrics["correctness_failures"] == 0,
        "budget_pass": bool(budget_pass),
        "accepted": metrics["correctness_failures"] == 0 and bool(budget_pass),
    }


def render(result: Result) -> str:
    record = result.model_dump(mode="json")
    record["summary"] = summarize(result)
    record["evidence_sha256"] = fingerprint(record)
    return canonical_json(record)


def validate_record(record: dict) -> Result:
    data = dict(record)
    digest = data.pop("evidence_sha256")
    if digest != fingerprint(data):
        raise ValueError("evidence_fingerprint_mismatch")
    summary = data.pop("summary")
    result = Result.model_validate(data)
    if summary != summarize(result):
        raise ValueError("evidence_summary_mismatch")
    return result
