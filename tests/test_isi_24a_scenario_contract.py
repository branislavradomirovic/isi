from types import SimpleNamespace
from src.domains.ordo.analytics_models import OrdoScenarioAssessment
from src.domains.ordo.analytics_service import _canonical_sha256, _scenario_assessment_payload


def test_scenario_assessment_persistence_contract() -> None:
    cols = OrdoScenarioAssessment.__table__.columns
    for name in ["scenario_contract_version", "methodology_key", "methodology_version", "input_reference_identities", "input_snapshot_sha256", "limitations", "uncertainty_semantics", "human_review_state"]:
        assert name in cols


def test_scenario_payload_is_versioned_non_forecast_non_causal_and_reproducible() -> None:
    scenario = SimpleNamespace(name="S", assumptions=["a"], measures=["m"])
    goal = SimpleNamespace(code="G", title="Goal", focus_area="custom", target_horizon=None)
    snapshot = {
        "evidence_quality_score": 0.8,
        "analytical_source": {
            "artifact_type": "snapshot",
            "artifact_id": "artifact-1",
            "dataset_contract_version_id": "contract-1",
            "resolved_snapshot_id": "snapshot-1",
        },
    }
    run = SimpleNamespace(snapshot=snapshot, analytical_artifact_fingerprint="a" * 64, dataset_contract_fingerprint="b" * 64)
    payload = _scenario_assessment_payload(scenario=scenario, goal=goal, run=run)
    contract = payload["scenario_contract"]
    assert payload["forecast_performed"] is False
    assert contract["scenario_contract_version"] == "ORDO-SCENARIO-CONTRACT-v1"
    assert contract["input_snapshot_sha256"] == _canonical_sha256(snapshot)
    assert len(contract["input_snapshot_sha256"]) == 64
    identities = {(item["kind"], item["id"]) for item in contract["input_reference_identities"]}
    assert ("snapshot", "artifact-1") in identities
    assert ("dataset_contract_version", "contract-1") in identities
    assert ("resolved_snapshot", "snapshot-1") in identities
    assert ("analytical_artifact_fingerprint", "a" * 64) in identities
    assert ("dataset_contract_fingerprint", "b" * 64) in identities
    assert contract["scenario_is_forecast"] is False
    assert contract["causal_claim"] is False
    assert contract["automatic_policy_recommendation"] is False
    assert contract["uncertainty_semantics"] == "not_applicable_scenario_not_forecast"
