from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.ai.evaluation import (
    AIEvaluationError,
    append_evaluation_result,
    append_evaluation_review,
    benchmark_execution_provenance,
    benchmark_input_fingerprint,
    cases_sha256,
    create_evaluation_run,
    evaluation_result_fingerprint,
    evaluation_review_fingerprint,
    evaluation_terminal_fingerprint,
    finalize_evaluation_run,
    load_evaluation_manifest,
    register_evaluation_dataset,
    register_promotion_benchmark,
    register_threshold_profile,
    threshold_profile_identity,
    validate_promotion_benchmark_manifest,
)
from src.platform.ai.governance import fingerprint, register_model, registration_fingerprint
from src.platform.ai.models import (
    AICapabilityRuntimeState,
    AIDriftSnapshot,
    AIEvaluationResult,
    AIEvaluationReview,
)
from src.platform.ai.monitoring import create_drift_snapshot
from src.platform.ai.promotion import (
    AIPromotionError,
    execute_promotion,
    execute_rollback,
    preview_promotion,
    resolve_runtime_state,
)
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _manifest(version="1"):
    cases = [{
        "case_id": "synthetic-1", "product_code": "SIMPA", "domain": "SIMPA",
        "capability": "simpa.synthetic.summary", "language": "sr", "input_version": "1",
        "expected_contract": {"status": "ok"}, "source_refs": ["fixture:1"],
        "sensitivity_class": "synthetic", "methodology_version": None,
        "human_gold_state": "not_applicable", "notes": "synthetic contract only",
    }]
    return {
        "dataset_key": "SIMPA-PROMOTION-SYNTHETIC", "version": version, "product_code": "SIMPA",
        "capability_key": "simpa.synthetic.summary", "model_family": "llm", "schema_version": "1",
        "case_count": 1, "cases_sha256": cases_sha256(cases), "source_provenance": "repository synthetic",
        "sensitivity_class": "synthetic", "methodology_version": None, "frozen": True,
        "approval_state": "approved", "owner": "test owner", "cases": cases,
    }


def test_promotion_benchmark_is_separate_frozen_and_hash_addressed():
    manifest = validate_promotion_benchmark_manifest(_manifest())
    assert manifest["frozen"] is True and manifest["approval_state"] == "approved"
    foundation = _manifest()
    foundation["dataset_key"] = "SIMPA-EVAL-v1"
    with pytest.raises(AIEvaluationError, match="foundation_fixture_cannot_be_promotion_benchmark"):
        validate_promotion_benchmark_manifest(foundation)
    changed = _manifest()
    changed["cases"][0]["notes"] = "changed"
    with pytest.raises(AIEvaluationError, match="cases_hash_mismatch"):
        validate_promotion_benchmark_manifest(changed)


def test_comparison_has_no_generic_winner_score_and_fails_closed():
    source = inspect.getsource(__import__("src.platform.ai.promotion", fromlist=["x"]))
    for marker in (
        "same_frozen_approved_promotion_benchmark_required", "required_metric_missing",
        "absolute_threshold_failed", "minimum_delta_failed", "non_compensable_gate_failed",
        "latest_final_evaluation_review_not_approved", "compatible_enabled_rollback_registration_required",
        '"no_generic_winner_score": True',
    ):
        assert marker in source
    assert "weighted" not in source and "aggregate_score" not in source


def test_promotion_and_rollback_are_governance_only_and_audited():
    promote = inspect.getsource(execute_promotion)
    rollback = inspect.getsource(execute_rollback)
    assert 'current.lifecycle_state = "challenger"' in promote
    assert 'candidate.lifecycle_state = "champion"' in promote
    assert "owner_approval_reference_required" in promote
    assert 'event_type="ai.governance.champion_promoted"' in promote
    assert 'event_type="ai.governance.champion_rolled_back"' in rollback
    for forbidden in ("ollama", "ssh", "deploy", "subprocess", "download"):
        assert forbidden not in (promote + rollback).lower()


@pytest.fixture
def promotion_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        db.add_all([Product(code="SIMPA", name="SIMPA"), Product(code="ORDO", name="ORDO")])
        organization = Organization(slug=f"org-{marker}", name="Organization")
        users = [User(email=f"{index}-{marker}@example.test", display_name=f"Reviewer {index}") for index in range(2)]
        db.add_all([organization, *users])
        db.flush()
        actors = [Membership(user_id=user.id, organization_id=organization.id) for user in users]
        db.add_all(actors)
        db.flush()
        workspaces = [
            Workspace(
                organization_id=organization.id, product_code="SIMPA", slug=f"simpa-{index}",
                name=f"SIMPA {index}", created_by_membership_id=actors[0].id,
            )
            for index in range(2)
        ]
        db.add_all(workspaces)
        db.flush()
        registrations = []
        for role in ("candidate", "baseline", "rollback"):
            registrations.append(register_model(
                db, organization_id=organization.id, workspace_id=workspaces[0].id,
                product_code="SIMPA", capability_key="simpa.bias", product_scope="SIMPA",
                model_family="statistical_ml", model_key=f"{role}-{marker}", version="1",
                lifecycle_state="challenger", actor_id=actors[0].id,
                provenance={"source": "synthetic"},
            ))
        dataset = register_evaluation_dataset(
            db, manifest=load_evaluation_manifest("tests/evals/SIMPA-EVAL-v1.json"),
            product_code="SIMPA", actor_id=actors[0].id,
        )
        manifest = _manifest()
        manifest["capability_key"] = "simpa.bias"
        manifest["model_family"] = "statistical_ml"
        manifest["cases"][0]["capability"] = "simpa.bias"
        manifest["cases"][0]["expected_contract"] = {"expected": [0.0]}
        manifest["cases"].append({
            "case_id": "safety-1", "product_code": "SIMPA", "domain": "SIMPA",
            "capability": "simpa.bias", "language": "sr", "input_version": "1",
            "expected_contract": {"kind": "prompt_injection"}, "source_refs": ["fixture:safety-1"],
            "sensitivity_class": "synthetic", "methodology_version": None,
            "human_gold_state": "approved", "notes": "synthetic safety contract",
        })
        manifest["case_count"] = len(manifest["cases"])
        manifest["cases_sha256"] = cases_sha256(manifest["cases"])
        benchmark = register_promotion_benchmark(
            db, manifest=manifest, product_code="SIMPA", actor_id=actors[0].id,
        )
        profile = register_threshold_profile(
            db, product_scope="SIMPA", product_code="SIMPA", capability_key="simpa.bias",
            model_family="statistical_ml", version="1",
            metric_definitions={"bias": {"direction": "toward_zero", "drift_warning_delta": 0.2,
                                                   "drift_blocker_delta": 0.5}},
            minimum_thresholds={"bias": 1.0}, minimum_deltas={"bias": 0.1},
            hard_gates={}, resource_limits={}, failure_threshold=2, cooldown_seconds=30,
            provenance="synthetic", actor_id=actors[0].id,
        )

        def make_run(registration, bias, *, safety=True, provenance=True):
            run = create_evaluation_run(
                db, organization_id=organization.id, workspace_id=workspaces[0].id,
                product_code="SIMPA", dataset_id=dataset.id, benchmark_id=benchmark.id,
                model_registration_id=registration.id, baseline_registration_id=registrations[1].id,
                prompt_version_id=None, policy_profile_id=None,
                input_fingerprint=benchmark_input_fingerprint(benchmark), environment_fingerprint="e" * 64,
                provenance={"methodology_version": None}, actor_id=actors[0].id,
            )
            append_evaluation_result(
                db, run=run, result_type="metric", result_key="bias",
                payload={"value": bias, "state": "available", "direction": "toward_zero",
                         "support": 1, "case_refs": ["synthetic-1"], "evidence": {}},
                actor_id=actors[0].id, governed_execution=True,
            )
            if safety:
                append_evaluation_result(
                    db, run=run, result_type="safety", result_key="safety.prompt_injection",
                    payload={"value": True, "state": "available", "direction": "exact",
                             "support": 1, "case_refs": ["safety-1"], "evidence": {"blocker": False}},
                    actor_id=actors[0].id, governed_execution=True,
                )
            if provenance:
                provenance_payload = benchmark_execution_provenance(
                    db, run=run, cases=benchmark.manifest_json["cases"]
                )
                append_evaluation_result(
                    db, run=run, result_type="provenance", result_key="benchmark_execution_provenance",
                    payload=provenance_payload, actor_id=actors[0].id, governed_execution=True,
                )
            finalize_evaluation_run(db, run=run, status="completed")
            return run

        candidate_run = make_run(registrations[0], -0.2)
        baseline_run = make_run(registrations[1], 0.8)
        append_evaluation_review(
            db, run=candidate_run, reviewer_membership_id=actors[0].id, decision="approved",
            notes="approved", evidence_reference="synthetic://review/approved",
        )
        yield SimpleNamespace(
            db=db, organization=organization, workspaces=workspaces, actors=actors,
            registrations=registrations, benchmark=benchmark, profile=profile,
            candidate_run=candidate_run, baseline_run=baseline_run,
        )


def _preview(case, *, workspace_index=0):
    return preview_promotion(
        case.db, organization_id=case.organization.id, workspace_id=case.workspaces[workspace_index].id,
        product_code="SIMPA", candidate_run_id=case.candidate_run.id,
        baseline_run_id=case.baseline_run.id, threshold_profile_id=case.profile.id,
        rollback_registration_id=case.registrations[2].id, actor_id=case.actors[0].id,
    )


def test_preview_is_exact_scope_and_toward_zero_is_magnitude_based(promotion_case):
    eligible = _preview(promotion_case)
    assert eligible.decision_status == "eligible"
    assert eligible.comparison_evidence["comparisons"]["bias"]["signed_improvement"] == pytest.approx(0.6)
    assert eligible.comparison_evidence["scope"]["workspace_id"] == str(promotion_case.workspaces[0].id)


def test_preview_rejects_wrong_workspace_and_missing_mandatory_evidence(promotion_case):
    wrong_scope = _preview(promotion_case, workspace_index=1)
    assert wrong_scope.decision_status == "blocked"
    assert "evaluation_run_scope_mismatch" in wrong_scope.blocker_reasons
    safety = promotion_case.db.scalar(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationResult.result_type == "safety",
    ))
    promotion_case.db.delete(safety)
    provenance = promotion_case.db.scalar(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationResult.result_type == "provenance",
    ))
    promotion_case.db.delete(provenance)
    promotion_case.db.flush()
    blocked = _preview(promotion_case)
    assert "required_safety_evidence_missing" in blocked.blocker_reasons
    assert "required_provenance_evidence_missing" in blocked.blocker_reasons


def test_latest_final_review_and_post_preview_drift_invalidate_execution(promotion_case):
    decision = _preview(promotion_case)
    assert decision.decision_status == "eligible"
    now = datetime.now(timezone.utc)
    drift = AIDriftSnapshot(
        organization_id=promotion_case.organization.id, workspace_id=promotion_case.workspaces[0].id,
        product_code="SIMPA", capability_key="simpa.bias",
        model_registration_id=promotion_case.registrations[0].id,
        threshold_profile_id=promotion_case.profile.id, window_start=now - timedelta(days=1),
        window_end=now, metrics={}, provenance={}, fingerprint="d" * 64, status="blocker",
        created_by_membership_id=promotion_case.actors[0].id,
    )
    promotion_case.db.add(drift)
    promotion_case.db.flush()
    with pytest.raises(AIPromotionError, match="promotion_evidence_changed_since_preview"):
        execute_promotion(
            promotion_case.db, decision_id=decision.id, owner_approval_reference="owner-approved",
            actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
            workspace_id=promotion_case.workspaces[0].id, product_code="SIMPA",
        )
    assert promotion_case.registrations[0].lifecycle_state != "champion"


def test_other_workspace_drift_does_not_block_preview(promotion_case):
    now = datetime.now(timezone.utc)
    promotion_case.db.add(AIDriftSnapshot(
        organization_id=promotion_case.organization.id, workspace_id=promotion_case.workspaces[1].id,
        product_code="SIMPA", capability_key="simpa.bias",
        model_registration_id=promotion_case.registrations[0].id,
        threshold_profile_id=promotion_case.profile.id, window_start=now - timedelta(days=1),
        window_end=now, metrics={}, provenance={}, fingerprint="c" * 64, status="blocker",
        created_by_membership_id=promotion_case.actors[0].id,
    ))
    promotion_case.db.flush()
    assert _preview(promotion_case).decision_status == "eligible"


def test_newer_rejected_review_invalidates_older_approval(promotion_case):
    eligible = _preview(promotion_case)
    append_evaluation_review(
        promotion_case.db, run=promotion_case.candidate_run,
        reviewer_membership_id=promotion_case.actors[1].id, decision="rejected",
        notes="new evidence", evidence_reference="synthetic://review/rejected",
    )
    with pytest.raises(AIPromotionError, match="latest_final_evaluation_review_not_approved"):
        execute_promotion(
            promotion_case.db, decision_id=eligible.id, owner_approval_reference="owner-approved",
            actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
            workspace_id=promotion_case.workspaces[0].id, product_code="SIMPA",
        )
    assert promotion_case.registrations[0].lifecycle_state != "champion"
    decision = _preview(promotion_case)
    assert "latest_final_evaluation_review_not_approved" in decision.blocker_reasons




def test_fhr3_r2_empty_final_review_reference_blocks_promotion(promotion_case):
    review = promotion_case.db.scalar(select(AIEvaluationReview).where(
        AIEvaluationReview.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationReview.is_final.is_(True),
    ))
    assert review is not None
    review.evidence_reference = ""
    review.fingerprint = evaluation_review_fingerprint(review)
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert decision.decision_status == "blocked"
    assert "final_evaluation_review_evidence_reference_required" in decision.blocker_reasons


@pytest.mark.parametrize(("field", "value"), [("schema_version", "tampered"), ("product_code", "ORDO")])
def test_fhr3_r2_current_benchmark_identity_must_match_both_runs(promotion_case, field, value):
    setattr(promotion_case.benchmark, field, value)
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert decision.decision_status == "blocked"
    assert "promotion_benchmark_input_identity_changed" in decision.blocker_reasons


def test_fhr3_r2_boolean_is_never_numeric_promotion_evidence():
    import src.platform.ai.promotion as promotion_module
    assert promotion_module._metric_value({"value": True}) is None
    assert promotion_module._metric_value({"value": 1}) == 1.0

def test_successful_execute_mutates_governance_only_after_revalidation(promotion_case):
    decision = _preview(promotion_case)
    executed = execute_promotion(
        promotion_case.db, decision_id=decision.id, owner_approval_reference="owner-approved",
        actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
        workspace_id=promotion_case.workspaces[0].id, product_code="SIMPA",
    )
    assert executed.decision_status == "promoted"
    assert promotion_case.registrations[0].lifecycle_state == "champion"
    assert promotion_case.registrations[1].lifecycle_state == "challenger"


def test_rollback_prefers_exact_product_state_over_shared(promotion_case):
    decision = _preview(promotion_case)
    execute_promotion(
        promotion_case.db, decision_id=decision.id, owner_approval_reference="owner-approved",
        actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
        workspace_id=promotion_case.workspaces[0].id, product_code="SIMPA",
    )
    shared = AICapabilityRuntimeState(
        product_scope="SHARED", capability_key="simpa.bias", model_family="statistical_ml",
        champion_registration_id=None, rollback_registration_id=None,
        threshold_profile_id=promotion_case.profile.id, circuit_state="closed",
        consecutive_failures=0, failure_threshold=2, cooldown_seconds=30,
    )
    promotion_case.db.add(shared)
    promotion_case.db.flush()
    selected = resolve_runtime_state(
        promotion_case.db, product_code="SIMPA", capability_key="simpa.bias"
    )
    assert selected.product_scope == "SIMPA"
    rolled_back = execute_rollback(
        promotion_case.db, product_code="SIMPA", capability_key="simpa.bias",
        reason="synthetic", evidence_reference="synthetic://rollback",
        actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
        workspace_id=promotion_case.workspaces[0].id,
    )
    assert rolled_back.product_scope == "SIMPA"
    assert rolled_back.champion_registration_id == promotion_case.registrations[2].id


def test_result_fingerprint_is_recomputed_before_promotion(promotion_case):
    result = promotion_case.db.scalar(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationResult.result_key == "bias",
    ))
    assert result is not None
    result.payload = {**result.payload, "value": -0.1}
    promotion_case.db.flush()
    result_tamper = _preview(promotion_case)
    assert any(
        reason.startswith("evaluation_result_fingerprint_mismatch:candidate:bias")
        for reason in result_tamper.blocker_reasons
    )


def test_review_fingerprint_is_recomputed_before_promotion(promotion_case):
    review = promotion_case.db.scalar(select(AIEvaluationReview).where(
        AIEvaluationReview.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationReview.is_final.is_(True),
    ))
    assert review is not None
    review.notes = "tampered after approval"
    promotion_case.db.flush()
    review_tamper = _preview(promotion_case)
    assert "evaluation_review_fingerprint_mismatch" in review_tamper.blocker_reasons


def test_candidate_run_is_bound_to_the_compared_baseline_registration(promotion_case):
    promotion_case.candidate_run.baseline_registration_id = promotion_case.registrations[2].id
    promotion_case.candidate_run.result_fingerprint = evaluation_terminal_fingerprint(
        promotion_case.db,
        run=promotion_case.candidate_run,
        status=promotion_case.candidate_run.status,
        failure_reason=promotion_case.candidate_run.failure_reason,
    )
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert "candidate_baseline_registration_binding_mismatch" in decision.blocker_reasons


def test_product_local_promotion_cannot_mutate_shared_scope(promotion_case):
    for registration in promotion_case.registrations:
        registration.product_scope = "SHARED"
    promotion_case.profile.product_scope = "SHARED"
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert "shared_scope_promotion_not_authorized_in_isi25b" in decision.blocker_reasons

    state = AICapabilityRuntimeState(
        product_scope="SHARED", capability_key="simpa.bias", model_family="statistical_ml",
        champion_registration_id=promotion_case.registrations[0].id,
        rollback_registration_id=promotion_case.registrations[2].id,
        threshold_profile_id=promotion_case.profile.id, circuit_state="closed",
        consecutive_failures=0, failure_threshold=2, cooldown_seconds=30,
    )
    promotion_case.db.add(state)
    promotion_case.db.flush()
    with pytest.raises(AIPromotionError, match="shared_scope_promotion_not_authorized_in_isi25b"):
        execute_rollback(
            promotion_case.db, product_code="SIMPA", capability_key="simpa.bias",
            reason="synthetic", evidence_reference="synthetic://rollback/shared",
            actor_id=promotion_case.actors[0].id, organization_id=promotion_case.organization.id,
            workspace_id=promotion_case.workspaces[0].id,
        )


def test_semantically_failed_provenance_blocks_even_with_valid_fingerprints(promotion_case):
    provenance = promotion_case.db.scalar(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == promotion_case.candidate_run.id,
        AIEvaluationResult.result_key == "benchmark_execution_provenance",
    ))
    assert provenance is not None
    provenance.payload = {**provenance.payload, "value": False}
    provenance.fingerprint = evaluation_result_fingerprint(provenance)
    promotion_case.candidate_run.result_fingerprint = evaluation_terminal_fingerprint(
        promotion_case.db,
        run=promotion_case.candidate_run,
        status=promotion_case.candidate_run.status,
        failure_reason=promotion_case.candidate_run.failure_reason,
    )
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert "non_compensable_provenance_blocker:benchmark_execution_provenance" in decision.blocker_reasons
    assert "required_benchmark_execution_provenance_missing:candidate" in decision.blocker_reasons


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"minimum_deltas": {"bias": "nan"}}, "minimum_delta_invalid:bias"),
        ({"minimum_deltas": {"bias": -0.1}}, "minimum_delta_invalid:bias"),
        ({"resource_limits": {"latency_ms": "nan"}}, "resource_limit_invalid:latency_ms"),
        ({"hard_gates": {"required_gate": "true"}}, "hard_gate_boolean_required:required_gate"),
        ({
            "metric_definitions": {
                "bias": {
                    "direction": "toward_zero",
                    "drift_warning_delta": "nan",
                    "drift_blocker_delta": 0.5,
                }
            }
        }, "threshold_drift_warning_invalid:bias"),
        ({
            "metric_definitions": {
                "bias": {
                    "direction": "toward_zero",
                    "drift_warning_delta": 0.5,
                    "drift_blocker_delta": 0.2,
                }
            }
        }, "threshold_drift_order_invalid:bias"),
    ],
)
def test_fhr3_r3_threshold_profile_registration_rejects_fail_open_numbers(
    promotion_case, changes, error
):
    values = {
        "metric_definitions": {
            "bias": {
                "direction": "toward_zero",
                "drift_warning_delta": 0.2,
                "drift_blocker_delta": 0.5,
            }
        },
        "minimum_thresholds": {"bias": 1.0},
        "minimum_deltas": {"bias": 0.1},
        "hard_gates": {},
        "resource_limits": {},
    }
    values.update(changes)
    with pytest.raises(AIEvaluationError, match=error):
        register_threshold_profile(
            promotion_case.db,
            product_scope="SIMPA",
            product_code="SIMPA",
            capability_key="simpa.bias",
            model_family="statistical_ml",
            version=f"bad-{uuid.uuid4().hex}",
            failure_threshold=2,
            cooldown_seconds=30,
            provenance="synthetic",
            actor_id=promotion_case.actors[0].id,
            **values,
        )


def test_fhr3_r3_persisted_invalid_threshold_profile_fails_closed_even_with_matching_fingerprint(
    promotion_case,
):
    promotion_case.profile.minimum_deltas = {"bias": -0.2}
    promotion_case.profile.fingerprint = fingerprint(threshold_profile_identity(promotion_case.profile))
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert decision.decision_status == "blocked"
    assert any(
        reason.startswith("threshold_profile_contract_invalid:minimum_delta_invalid:bias")
        for reason in decision.blocker_reasons
    )


def test_fhr3_r3_registration_identity_tamper_blocks_promotion(promotion_case):
    registration = promotion_case.registrations[0]
    registration.product_scope = "SHARED"
    registration.registry_fingerprint = registration_fingerprint(registration)
    promotion_case.db.flush()
    registration.product_scope = "SIMPA"
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert decision.decision_status == "blocked"
    assert "candidate_registration_identity_changed" in decision.blocker_reasons


def test_fhr3_r3_drift_status_tamper_without_fingerprint_change_blocks_promotion(promotion_case):
    now = datetime.now(timezone.utc)
    drift = create_drift_snapshot(
        promotion_case.db,
        organization_id=promotion_case.organization.id,
        workspace_id=promotion_case.workspaces[0].id,
        product_code="SIMPA",
        capability_key="simpa.bias",
        model_registration_id=promotion_case.registrations[0].id,
        threshold_profile_id=promotion_case.profile.id,
        window_start=now - timedelta(days=1),
        window_end=now,
        observed_metrics={"bias": 1.0},
        reference_metrics={"bias": 0.0},
        provenance={"source": "synthetic"},
        actor_id=promotion_case.actors[0].id,
    )
    assert drift.status == "blocker"
    drift.status = "ok"
    promotion_case.db.flush()
    decision = _preview(promotion_case)
    assert decision.decision_status == "blocked"
    assert "drift_snapshot_fingerprint_mismatch" in decision.blocker_reasons


@pytest.mark.parametrize(
    ("reason", "evidence_reference", "error"),
    [
        ("   ", "synthetic://rollback", "rollback_reason_required"),
        ("synthetic", "   ", "rollback_evidence_reference_required"),
    ],
)
def test_fhr3_r3_rollback_requires_non_whitespace_reason_and_evidence(
    promotion_case, reason, evidence_reference, error
):
    decision = _preview(promotion_case)
    execute_promotion(
        promotion_case.db,
        decision_id=decision.id,
        owner_approval_reference="owner-approved",
        actor_id=promotion_case.actors[0].id,
        organization_id=promotion_case.organization.id,
        workspace_id=promotion_case.workspaces[0].id,
        product_code="SIMPA",
    )
    with pytest.raises(AIPromotionError, match=error):
        execute_rollback(
            promotion_case.db,
            product_code="SIMPA",
            capability_key="simpa.bias",
            reason=reason,
            evidence_reference=evidence_reference,
            actor_id=promotion_case.actors[0].id,
            organization_id=promotion_case.organization.id,
            workspace_id=promotion_case.workspaces[0].id,
        )
