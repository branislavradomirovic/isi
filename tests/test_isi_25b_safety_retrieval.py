from __future__ import annotations

from pathlib import Path

from src.platform.ai.evaluation import evaluate_retrieval, evaluate_safety_cases


ROOT = Path(__file__).resolve().parents[1]


def test_private_cross_product_cross_tenant_and_public_isolation_fail_closed():
    rows = {row["metric_key"]: row for row in evaluate_retrieval([
        {"relevant_ids": ["simpa-a"], "retrieved_ids": ["ordo-b"],
         "allowed_namespace": "SIMPA:org-a:private", "retrieved_namespaces": ["ORDO:org-b:private"]},
    ], k=1)}
    assert rows["namespace_isolation"]["value"] is False
    assert rows["recall_at_k"]["value"] == 0


def test_namespace_evidence_missing_empty_partial_mismatch_and_correct():
    base = {"relevant_ids": ["a", "b"], "retrieved_ids": ["a", "b"],
            "allowed_namespace": "ORG-a/SIMPA"}
    invalid = [
        {"relevant_ids": ["a", "b"], "retrieved_ids": ["a", "b"],
         "retrieved_namespaces": ["ORG-a/SIMPA", "ORG-a/SIMPA"]},
        base,
        {**base, "retrieved_namespaces": []},
        {**base, "retrieved_namespaces": ["ORG-a/SIMPA"]},
        {**base, "retrieved_namespaces": ["ORG-a/SIMPA", "ORG-b/SIMPA"]},
    ]
    for case in invalid:
        isolation = {row["metric_key"]: row for row in evaluate_retrieval([case], k=2)}["namespace_isolation"]
        assert isolation["value"] is False
        assert isolation["evidence"]["reason"] in {
            "retrieval_allowed_namespace_required",
            "retrieval_namespace_evidence_required",
            "retrieval_namespace_mismatch",
        }
    correct = {**base, "retrieved_namespaces": ["ORG-a/SIMPA", "ORG-a/SIMPA"]}
    isolation = {row["metric_key"]: row for row in evaluate_retrieval([correct], k=2)}["namespace_isolation"]
    assert isolation["value"] is True and isolation["evidence"] == {}


def test_adversarial_failures_are_non_compensable_blockers():
    kinds = [
        "prompt_injection", "pii_boundary", "cross_product", "cross_tenant",
        "unsupported_causal", "unsupported_forecast", "unsupported_scenario_impact",
        "fabricated_score_threshold", "human_review_bypass", "missing_evidence",
        "contradictory_evidence", "stale_evidence",
    ]
    rows = evaluate_safety_cases([{"case_id": key, "kind": key, "passed": False} for key in kinds])
    assert len(rows) == len(kinds)
    assert all(row["value"] is False and row["evidence"]["blocker"] is True for row in rows)


def test_ordo_forecast_family_runtime_remains_outside_mlops_fallback():
    service = (ROOT / "src/platform/ai/service.py").read_text(encoding="utf-8")
    forecasting = (ROOT / "src/domains/ordo/forecasting.py").read_text(encoding="utf-8")
    analytics_service = (ROOT / "src/domains/ordo/analytics_service.py").read_text(encoding="utf-8")
    assert "execute_forecast" not in service
    assert "authorized_runtime_fallbacks" not in forecasting
    assert "NOT_ESTIMATED" in analytics_service


def test_safety_passed_string_is_not_truthy_evidence():
    import pytest
    from src.platform.ai.evaluation import AIEvaluationError

    with pytest.raises(AIEvaluationError, match="safety_passed_boolean_required"):
        evaluate_safety_cases([{"case_id": "x", "kind": "cross_tenant", "passed": "false"}])


def test_retrieval_duplicate_ids_cannot_inflate_ndcg_above_one():
    rows = {row["metric_key"]: row for row in evaluate_retrieval([
        {
            "relevant_ids": ["a"],
            "retrieved_ids": ["a", "a"],
            "allowed_namespace": "SIMPA:org-a:private",
            "retrieved_namespaces": ["SIMPA:org-a:private", "SIMPA:org-a:private"],
        }
    ], k=2)}
    assert 0.0 <= rows["recall_at_k"]["value"] <= 1.0
    assert 0.0 <= rows["mrr"]["value"] <= 1.0
    assert 0.0 <= rows["ndcg_at_k"]["value"] <= 1.0
    assert rows["ndcg_at_k"]["value"] == 1.0
