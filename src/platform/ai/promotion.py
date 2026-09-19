from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.ai.evaluation import (
    AIEvaluationError,
    benchmark_input_fingerprint,
    cases_sha256,
    evaluation_result_fingerprint,
    evaluation_review_fingerprint,
    evaluation_terminal_fingerprint,
    threshold_profile_fingerprint_matches,
    validate_threshold_profile_contract,
)
from src.platform.ai.governance import (
    drift_snapshot_fingerprint_from_row,
    fingerprint,
    registration_fingerprint_matches,
)
from src.platform.ai.models import (
    AIAuditEvent,
    AICapabilityRuntimeState,
    AICapabilityThreshold,
    AIDriftSnapshot,
    AIEvaluationBenchmark,
    AIEvaluationResult,
    AIEvaluationReview,
    AIEvaluationRun,
    AIModelRegistration,
    AIPromotionDecision,
)


class AIPromotionError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _visible(scope: str, product_code: str) -> bool:
    return scope in {"SHARED", product_code}


def resolve_runtime_state(
    session: Session, *, product_code: str, capability_key: str
) -> AICapabilityRuntimeState | None:
    exact = session.scalar(select(AICapabilityRuntimeState).where(
        AICapabilityRuntimeState.product_scope == product_code,
        AICapabilityRuntimeState.capability_key == capability_key,
    ))
    if exact is not None:
        return exact
    return session.scalar(select(AICapabilityRuntimeState).where(
        AICapabilityRuntimeState.product_scope == "SHARED",
        AICapabilityRuntimeState.capability_key == capability_key,
    ))


def _result_map(session: Session, run_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    rows = list(session.scalars(
        select(AIEvaluationResult)
        .where(AIEvaluationResult.evaluation_run_id == run_id)
        .order_by(AIEvaluationResult.sequence_no)
    ).all())
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.result_key in result:
            raise AIPromotionError(f"ambiguous_duplicate_result_key:{row.result_key}")
        result[row.result_key] = row.payload
    return result


def _metric_value(payload: dict[str, Any]) -> float | None:
    value = payload.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def _compatible_registration(
    registration: AIModelRegistration | None,
    *,
    product_code: str,
    capability_key: str,
    model_family: str,
) -> bool:
    return bool(
        registration is not None
        and registration_fingerprint_matches(registration)
        and registration.enabled
        and registration.lifecycle_state != "retired"
        and _visible(registration.product_scope, product_code)
        and registration.capability_key == capability_key
        and registration.model_family == model_family
        and (model_family == "statistical_ml" or registration.runtime_model_id is not None)
    )


def _latest_final_review(session: Session, run_id: uuid.UUID) -> AIEvaluationReview | None:
    return session.scalar(select(AIEvaluationReview).where(
        AIEvaluationReview.evaluation_run_id == run_id,
        AIEvaluationReview.is_final.is_(True),
    ).order_by(AIEvaluationReview.reviewed_at.desc(), AIEvaluationReview.id.desc()))


def _assessment(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    candidate_run_id: uuid.UUID,
    baseline_run_id: uuid.UUID,
    threshold_profile_id: uuid.UUID,
    rollback_registration_id: uuid.UUID,
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    candidate_run = session.get(AIEvaluationRun, candidate_run_id)
    baseline_run = session.get(AIEvaluationRun, baseline_run_id)
    profile = session.get(AICapabilityThreshold, threshold_profile_id)
    if candidate_run is None or baseline_run is None:
        raise AIPromotionError("promotion_evaluation_run_not_found")
    candidate = session.get(AIModelRegistration, candidate_run.model_registration_id)
    baseline = session.get(AIModelRegistration, baseline_run.model_registration_id)
    if candidate is None or baseline is None or profile is None:
        raise AIPromotionError("promotion_governance_reference_not_found")
    blockers: list[str] = []
    expected_scope = (organization_id, workspace_id, product_code)
    if any(
        (run.organization_id, run.workspace_id, run.product_code) != expected_scope
        for run in (candidate_run, baseline_run)
    ):
        blockers.append("evaluation_run_scope_mismatch")
    if candidate.id == baseline.id:
        blockers.append("candidate_and_baseline_must_be_distinct")
    if not registration_fingerprint_matches(candidate):
        blockers.append("candidate_registration_identity_changed")
    if not registration_fingerprint_matches(baseline):
        blockers.append("baseline_registration_identity_changed")
    if (
        candidate_run.baseline_registration_id is None
        or candidate_run.baseline_registration_id != baseline_run.model_registration_id
    ):
        blockers.append("candidate_baseline_registration_binding_mismatch")

    candidate_rows = list(session.scalars(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == candidate_run.id
    ).order_by(AIEvaluationResult.sequence_no)).all())
    baseline_rows = list(session.scalars(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == baseline_run.id
    ).order_by(AIEvaluationResult.sequence_no)).all())
    for label, rows in (("candidate", candidate_rows), ("baseline", baseline_rows)):
        for row in rows:
            if evaluation_result_fingerprint(row) != row.fingerprint:
                blockers.append(f"evaluation_result_fingerprint_mismatch:{label}:{row.result_key}")

    if candidate_run.status != "completed" or baseline_run.status != "completed":
        blockers.append("evaluation_runs_must_be_completed")
    else:
        for label, run in (("candidate", candidate_run), ("baseline", baseline_run)):
            recomputed = evaluation_terminal_fingerprint(
                session, run=run, status=run.status, failure_reason=run.failure_reason
            )
            if recomputed != run.result_fingerprint:
                blockers.append(f"{label}_terminal_fingerprint_mismatch")
    benchmark = session.get(AIEvaluationBenchmark, candidate_run.benchmark_id) if candidate_run.benchmark_id else None
    if benchmark is None:
        raise AIPromotionError("frozen_approved_promotion_benchmark_required")
    if (
        baseline_run.benchmark_id != candidate_run.benchmark_id
        or not benchmark.frozen
        or benchmark.approval_state != "approved"
    ):
        blockers.append("same_frozen_approved_promotion_benchmark_required")
    manifest_cases = benchmark.manifest_json.get("cases") if isinstance(benchmark.manifest_json, dict) else None
    if (
        not isinstance(manifest_cases, list)
        or cases_sha256(manifest_cases) != benchmark.cases_sha256
        or fingerprint(benchmark.manifest_json) != benchmark.manifest_fingerprint
    ):
        blockers.append("promotion_benchmark_identity_changed")
    current_benchmark_input_fingerprint = benchmark_input_fingerprint(benchmark)
    if candidate_run.input_fingerprint != baseline_run.input_fingerprint:
        blockers.append("candidate_baseline_canonical_input_identity_mismatch")
    if (
        candidate_run.input_fingerprint != current_benchmark_input_fingerprint
        or baseline_run.input_fingerprint != current_benchmark_input_fingerprint
    ):
        blockers.append("promotion_benchmark_input_identity_changed")
    capability_key = candidate.capability_key
    family = candidate.model_family
    if not _compatible_registration(
        candidate, product_code=product_code, capability_key=capability_key, model_family=family
    ):
        blockers.append("candidate_registration_incompatible")
    if not _compatible_registration(
        baseline, product_code=product_code, capability_key=capability_key, model_family=family
    ):
        blockers.append("baseline_registration_incompatible")
    if candidate.product_scope != baseline.product_scope:
        blockers.append("candidate_baseline_product_scope_mismatch")
    if candidate.product_scope != product_code or baseline.product_scope != product_code:
        blockers.append("shared_scope_promotion_not_authorized_in_isi25b")
    if benchmark.capability_key != capability_key or benchmark.model_family != family:
        blockers.append("benchmark_capability_or_family_mismatch")
    if (
        profile.capability_key != capability_key
        or profile.model_family != family
        or not _visible(profile.product_scope, product_code)
        or not profile.enabled
    ):
        blockers.append("threshold_profile_incompatible")
    profile_contract_valid = True
    try:
        validate_threshold_profile_contract(
            metric_definitions=profile.metric_definitions,
            minimum_thresholds=profile.minimum_thresholds,
            minimum_deltas=profile.minimum_deltas,
            hard_gates=profile.hard_gates,
            resource_limits=profile.resource_limits,
            failure_threshold=profile.failure_threshold,
            cooldown_seconds=profile.cooldown_seconds,
        )
    except AIEvaluationError as exc:
        profile_contract_valid = False
        blockers.append(f"threshold_profile_contract_invalid:{exc}")
    if not threshold_profile_fingerprint_matches(profile):
        blockers.append("threshold_profile_identity_changed")

    metric_definitions = profile.metric_definitions if profile_contract_valid else {}
    minimum_thresholds = profile.minimum_thresholds if profile_contract_valid else {}
    minimum_deltas = profile.minimum_deltas if profile_contract_valid else {}
    hard_gates = profile.hard_gates if profile_contract_valid else {}
    resource_limits = profile.resource_limits if profile_contract_valid else {}

    if hard_gates.get("require_same_prompt", True) and candidate_run.prompt_version_id != baseline_run.prompt_version_id:
        blockers.append("prompt_identity_mismatch")
    if hard_gates.get("require_same_policy", True) and candidate_run.policy_profile_id != baseline_run.policy_profile_id:
        blockers.append("policy_identity_mismatch")
    if hard_gates.get("require_same_methodology", True) and (
        candidate_run.provenance.get("methodology_version")
        != baseline_run.provenance.get("methodology_version")
    ):
        blockers.append("methodology_identity_mismatch")

    candidate_results = _result_map(session, candidate_run.id)
    baseline_results = _result_map(session, baseline_run.id)
    safety_rows = [row for row in candidate_rows if row.result_type == "safety"]
    provenance_rows = [row for row in candidate_rows if row.result_type == "provenance"]
    if not safety_rows:
        blockers.append("required_safety_evidence_missing")
    if not provenance_rows:
        blockers.append("required_provenance_evidence_missing")
    for label, results in (("candidate", candidate_results), ("baseline", baseline_results)):
        execution_provenance = results.get("benchmark_execution_provenance")
        if (
            execution_provenance is None
            or execution_provenance.get("state", "available") != "available"
            or execution_provenance.get("value") is not True
        ):
            blockers.append(f"required_benchmark_execution_provenance_missing:{label}")
    applicable_safety_case_ids = {
        str(case.get("case_id"))
        for case in benchmark.manifest_json.get("cases", [])
        if isinstance(case, dict) and (
            case.get("capability") == "safety"
            or case.get("kind") is not None
            or (isinstance(case.get("expected_contract"), dict) and case["expected_contract"].get("kind") is not None)
        )
    }
    represented_safety_case_ids = {
        str(ref) for row in safety_rows for ref in row.payload.get("case_refs", [])
    }
    if not applicable_safety_case_ids:
        blockers.append("required_safety_evidence_missing")
    elif not applicable_safety_case_ids.issubset(represented_safety_case_ids):
        blockers.append("required_safety_evidence_missing")
    for result in candidate_rows:
        if result.result_type == "safety" and (
            result.payload.get("state", "available") != "available"
            or result.payload.get("evidence", {}).get("blocker") is True
            or result.payload.get("value") is not True
        ):
            blockers.append(f"non_compensable_safety_blocker:{result.result_key}")
        if result.result_type == "provenance" and (
            result.payload.get("state", "available") != "available"
            or result.payload.get("value") is not True
        ):
            blockers.append(f"non_compensable_provenance_blocker:{result.result_key}")
        if (
            result.result_key.startswith("structured_")
            and result.payload.get("state", "available") == "available"
            and result.payload.get("value") is not True
        ):
            blockers.append(f"non_compensable_structured_output_blocker:{result.result_key}")

    comparisons: dict[str, Any] = {}
    for metric_key, definition in metric_definitions.items():
        candidate_payload = candidate_results.get(metric_key)
        baseline_payload = baseline_results.get(metric_key)
        if not candidate_payload or candidate_payload.get("state", "available") != "available":
            blockers.append(f"required_metric_missing:{metric_key}:candidate")
            continue
        if not baseline_payload or baseline_payload.get("state", "available") != "available":
            blockers.append(f"required_metric_missing:{metric_key}:baseline")
            continue
        candidate_value = _metric_value(candidate_payload)
        baseline_value = _metric_value(baseline_payload)
        if candidate_value is None or baseline_value is None:
            blockers.append(f"required_metric_non_numeric:{metric_key}")
            continue
        direction = definition["direction"]
        threshold = minimum_thresholds.get(metric_key)
        delta_required = minimum_deltas.get(metric_key)
        if threshold is not None:
            absolute_pass = (
                float(candidate_value) >= float(threshold) if direction == "higher"
                else float(candidate_value) <= float(threshold) if direction == "lower"
                else abs(float(candidate_value)) <= abs(float(threshold)) if direction == "toward_zero"
                else candidate_value == threshold
            )
            if not absolute_pass:
                blockers.append(f"absolute_threshold_failed:{metric_key}")
        signed_delta = (
            float(candidate_value) - float(baseline_value) if direction == "higher"
            else float(baseline_value) - float(candidate_value) if direction == "lower"
            else abs(float(baseline_value)) - abs(float(candidate_value)) if direction == "toward_zero"
            else 0.0 if candidate_value == baseline_value else -1.0
        )
        if delta_required is not None and signed_delta < float(delta_required):
            blockers.append(f"minimum_delta_failed:{metric_key}")
        comparisons[metric_key] = {
            "candidate": candidate_value,
            "baseline": baseline_value,
            "direction": direction,
            "signed_improvement": signed_delta,
        }

    for gate_key, required in hard_gates.items():
        if gate_key.startswith("require_same_") or not required:
            continue
        payload = candidate_results.get(gate_key)
        if payload is None or payload.get("state", "available") != "available" or payload.get("value") is not True:
            blockers.append(f"non_compensable_gate_failed:{gate_key}")
    for resource_key, maximum in resource_limits.items():
        payload = candidate_results.get(resource_key)
        value = _metric_value(payload) if payload else None
        if value is None or float(value) > float(maximum):
            blockers.append(f"resource_limit_failed:{resource_key}")

    final_review = _latest_final_review(session, candidate_run.id)
    if final_review is None or final_review.decision != "approved":
        blockers.append("latest_final_evaluation_review_not_approved")
    elif not isinstance(final_review.evidence_reference, str) or not final_review.evidence_reference.strip():
        blockers.append("final_evaluation_review_evidence_reference_required")
    elif evaluation_review_fingerprint(final_review) != final_review.fingerprint:
        blockers.append("evaluation_review_fingerprint_mismatch")
    rollback = session.get(AIModelRegistration, rollback_registration_id)
    if rollback is not None and not registration_fingerprint_matches(rollback):
        blockers.append("rollback_registration_identity_changed")
    if not _compatible_registration(
        rollback, product_code=product_code, capability_key=capability_key, model_family=family
    ):
        blockers.append("compatible_enabled_rollback_registration_required")
    elif rollback.id == candidate.id:
        blockers.append("rollback_registration_must_differ_from_candidate")
    elif rollback.product_scope != product_code:
        blockers.append("shared_scope_promotion_not_authorized_in_isi25b")
    latest_drift = session.scalar(select(AIDriftSnapshot).where(
        AIDriftSnapshot.organization_id == organization_id,
        AIDriftSnapshot.workspace_id == workspace_id,
        AIDriftSnapshot.product_code == product_code,
        AIDriftSnapshot.capability_key == capability_key,
        AIDriftSnapshot.model_registration_id == candidate.id,
    ).order_by(AIDriftSnapshot.window_end.desc(), AIDriftSnapshot.created_at.desc()))
    if latest_drift is not None:
        drift_profile = session.get(AICapabilityThreshold, latest_drift.threshold_profile_id)
        if drift_profile is None:
            blockers.append("drift_snapshot_threshold_profile_missing")
        else:
            try:
                validate_threshold_profile_contract(
                    metric_definitions=drift_profile.metric_definitions,
                    minimum_thresholds=drift_profile.minimum_thresholds,
                    minimum_deltas=drift_profile.minimum_deltas,
                    hard_gates=drift_profile.hard_gates,
                    resource_limits=drift_profile.resource_limits,
                    failure_threshold=drift_profile.failure_threshold,
                    cooldown_seconds=drift_profile.cooldown_seconds,
                )
            except AIEvaluationError as exc:
                blockers.append(f"drift_threshold_profile_contract_invalid:{exc}")
            if not threshold_profile_fingerprint_matches(drift_profile):
                blockers.append("drift_threshold_profile_identity_changed")
            if (
                drift_snapshot_fingerprint_from_row(
                    latest_drift, threshold_fingerprint=drift_profile.fingerprint
                )
                != latest_drift.fingerprint
            ):
                blockers.append("drift_snapshot_fingerprint_mismatch")
        if latest_drift.status == "blocker":
            blockers.append("candidate_drift_blocker")

    evidence = {
        "scope": {
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "product_code": product_code,
        },
        "candidate_result_fingerprint": candidate_run.result_fingerprint,
        "baseline_result_fingerprint": baseline_run.result_fingerprint,
        "candidate_result_row_fingerprints": sorted(row.fingerprint for row in candidate_rows),
        "baseline_result_row_fingerprints": sorted(row.fingerprint for row in baseline_rows),
        "canonical_input_fingerprint": candidate_run.input_fingerprint,
        "candidate_prompt_version_id": str(candidate_run.prompt_version_id) if candidate_run.prompt_version_id else None,
        "baseline_prompt_version_id": str(baseline_run.prompt_version_id) if baseline_run.prompt_version_id else None,
        "candidate_policy_profile_id": str(candidate_run.policy_profile_id) if candidate_run.policy_profile_id else None,
        "baseline_policy_profile_id": str(baseline_run.policy_profile_id) if baseline_run.policy_profile_id else None,
        "benchmark_fingerprint": benchmark.manifest_fingerprint,
        "benchmark_cases_sha256": benchmark.cases_sha256,
        "threshold_fingerprint": profile.fingerprint,
        "final_review_id": str(final_review.id) if final_review else None,
        "final_review_fingerprint": final_review.fingerprint if final_review else None,
        "latest_drift_fingerprint": latest_drift.fingerprint if latest_drift else None,
        "comparisons": comparisons,
        "blockers": sorted(set(blockers)),
        "no_generic_winner_score": True,
    }
    context = {
        "candidate_run": candidate_run,
        "baseline_run": baseline_run,
        "candidate": candidate,
        "baseline": baseline,
        "benchmark": benchmark,
        "profile": profile,
        "rollback": rollback,
        "final_review": final_review,
        "capability_key": capability_key,
        "family": family,
    }
    return evidence, sorted(set(blockers)), context


def _evidence_fingerprint(
    *, candidate_run_id: uuid.UUID, baseline_run_id: uuid.UUID,
    rollback_registration_id: uuid.UUID, evidence: dict[str, Any]
) -> str:
    return str(fingerprint({
        "candidate_run_id": str(candidate_run_id),
        "baseline_run_id": str(baseline_run_id),
        "rollback_registration_id": str(rollback_registration_id),
        "evidence": evidence,
    }))


def preview_promotion(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    candidate_run_id: uuid.UUID,
    baseline_run_id: uuid.UUID,
    threshold_profile_id: uuid.UUID,
    rollback_registration_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> AIPromotionDecision:
    evidence, blockers, context = _assessment(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        candidate_run_id=candidate_run_id,
        baseline_run_id=baseline_run_id,
        threshold_profile_id=threshold_profile_id,
        rollback_registration_id=rollback_registration_id,
    )
    benchmark = context["benchmark"]
    final_review = context["final_review"]
    row = AIPromotionDecision(
        product_code=product_code,
        capability_key=context["capability_key"],
        model_family=context["family"],
        candidate_registration_id=context["candidate"].id,
        baseline_registration_id=context["baseline"].id,
        candidate_run_id=candidate_run_id,
        baseline_run_id=baseline_run_id,
        benchmark_id=benchmark.id,
        threshold_profile_id=threshold_profile_id,
        rollback_registration_id=rollback_registration_id,
        comparison_evidence=evidence,
        evidence_fingerprint=_evidence_fingerprint(
            candidate_run_id=candidate_run_id,
            baseline_run_id=baseline_run_id,
            rollback_registration_id=rollback_registration_id,
            evidence=evidence,
        ),
        decision_status="blocked" if blockers else "eligible",
        blocker_reasons=blockers,
        final_review_id=final_review.id if final_review else None,
        owner_approval_reference="",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def execute_promotion(
    session: Session, *, decision_id: uuid.UUID, owner_approval_reference: str,
    actor_id: uuid.UUID | None, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    product_code: str,
) -> AIPromotionDecision:
    decision = session.get(AIPromotionDecision, decision_id)
    if decision is None:
        raise AIPromotionError("promotion_decision_not_found")
    if decision.product_code != product_code:
        raise AIPromotionError("promotion_decision_scope_mismatch")
    if decision.decision_status != "eligible" or decision.blocker_reasons:
        raise AIPromotionError("promotion_decision_not_eligible")
    if not owner_approval_reference.strip():
        raise AIPromotionError("promotion_owner_approval_reference_required")
    evidence, blockers, context = _assessment(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        candidate_run_id=decision.candidate_run_id,
        baseline_run_id=decision.baseline_run_id,
        threshold_profile_id=decision.threshold_profile_id,
        rollback_registration_id=decision.rollback_registration_id,
    )
    current_fingerprint = _evidence_fingerprint(
        candidate_run_id=decision.candidate_run_id,
        baseline_run_id=decision.baseline_run_id,
        rollback_registration_id=decision.rollback_registration_id,
        evidence=evidence,
    )
    if "latest_final_evaluation_review_not_approved" in blockers:
        raise AIPromotionError("latest_final_evaluation_review_not_approved")
    if blockers or current_fingerprint != decision.evidence_fingerprint:
        raise AIPromotionError("promotion_evidence_changed_since_preview")
    candidate = context["candidate"]
    rollback = context["rollback"]
    profile = context["profile"]
    if candidate.id != decision.candidate_registration_id or context["baseline"].id != decision.baseline_registration_id:
        raise AIPromotionError("promotion_evidence_changed_since_preview")
    if (
        candidate.product_scope != product_code
        or context["baseline"].product_scope != product_code
        or rollback is None
        or rollback.product_scope != product_code
    ):
        raise AIPromotionError("shared_scope_promotion_not_authorized_in_isi25b")
    current_champions = session.scalars(select(AIModelRegistration).where(
        AIModelRegistration.product_scope == candidate.product_scope,
        AIModelRegistration.capability_key == candidate.capability_key,
        AIModelRegistration.lifecycle_state == "champion",
        AIModelRegistration.enabled.is_(True),
    )).all()
    for current in current_champions:
        if not registration_fingerprint_matches(current):
            raise AIPromotionError("promotion_runtime_registration_identity_changed")
        if current.id != candidate.id:
            current.lifecycle_state = "challenger"
    candidate.lifecycle_state = "champion"
    state = session.scalar(select(AICapabilityRuntimeState).where(
        AICapabilityRuntimeState.product_scope == candidate.product_scope,
        AICapabilityRuntimeState.capability_key == candidate.capability_key,
    ))
    if state is None:
        state = AICapabilityRuntimeState(
            product_scope=candidate.product_scope, capability_key=candidate.capability_key,
            model_family=candidate.model_family, champion_registration_id=candidate.id,
            rollback_registration_id=rollback.id, threshold_profile_id=profile.id,
            failure_threshold=profile.failure_threshold, cooldown_seconds=profile.cooldown_seconds,
            circuit_state="closed", consecutive_failures=0, updated_by_membership_id=actor_id,
        )
        session.add(state)
    else:
        state.model_family = candidate.model_family
        state.champion_registration_id = candidate.id
        state.rollback_registration_id = rollback.id
        state.threshold_profile_id = profile.id
        state.failure_threshold = profile.failure_threshold
        state.cooldown_seconds = profile.cooldown_seconds
        state.circuit_state = "closed"
        state.consecutive_failures = 0
        state.opened_at = None
        state.version += 1
        state.updated_by_membership_id = actor_id
    decision.decision_status = "promoted"
    decision.owner_approval_reference = owner_approval_reference.strip()
    decision.executed_by_membership_id = actor_id
    decision.executed_at = _utcnow()
    session.add(AIAuditEvent(
        organization_id=organization_id, workspace_id=workspace_id, product_code=decision.product_code,
        actor_membership_id=actor_id, event_type="ai.governance.champion_promoted",
        entity_type="ai_promotion_decision", entity_id=decision.id,
        detail=f"evidence_fingerprint={decision.evidence_fingerprint};owner_approval={owner_approval_reference.strip()}",
    ))
    session.flush()
    return decision


def execute_rollback(
    session: Session, *, product_code: str, capability_key: str, reason: str,
    evidence_reference: str, actor_id: uuid.UUID | None,
    organization_id: uuid.UUID, workspace_id: uuid.UUID,
) -> AICapabilityRuntimeState:
    reason_value = reason.strip()
    evidence_value = evidence_reference.strip()
    if not reason_value:
        raise AIPromotionError("rollback_reason_required")
    if not evidence_value:
        raise AIPromotionError("rollback_evidence_reference_required")
    state = resolve_runtime_state(session, product_code=product_code, capability_key=capability_key)
    if state is None or state.rollback_registration_id is None:
        raise AIPromotionError("governed_rollback_target_not_available")
    if state.product_scope != product_code:
        raise AIPromotionError("shared_scope_promotion_not_authorized_in_isi25b")
    current = session.get(AIModelRegistration, state.champion_registration_id) if state.champion_registration_id else None
    target = session.get(AIModelRegistration, state.rollback_registration_id)
    if (
        not _compatible_registration(
            target, product_code=product_code, capability_key=capability_key, model_family=state.model_family
        )
        or target.product_scope != state.product_scope
    ):
        raise AIPromotionError("governed_rollback_target_not_compatible")
    if current is not None and not registration_fingerprint_matches(current):
        raise AIPromotionError("governed_current_registration_identity_changed")
    if current is not None and current.product_scope != state.product_scope:
        raise AIPromotionError("governed_runtime_state_scope_incompatible")
    if current is not None and current.id != target.id:
        current.lifecycle_state = "challenger"
    prior_id = current.id if current is not None else None
    prior_decision = session.scalar(select(AIPromotionDecision).where(
        AIPromotionDecision.product_code == product_code,
        AIPromotionDecision.capability_key == capability_key,
        AIPromotionDecision.candidate_registration_id == prior_id,
        AIPromotionDecision.decision_status == "promoted",
    ).order_by(AIPromotionDecision.executed_at.desc())) if prior_id is not None else None
    if prior_decision is not None:
        prior_decision.decision_status = "rolled_back"
    target.lifecycle_state = "champion"
    state.champion_registration_id = target.id
    state.rollback_registration_id = prior_id
    state.circuit_state = "closed"
    state.consecutive_failures = 0
    state.opened_at = None
    state.version += 1
    state.updated_by_membership_id = actor_id
    session.add(AIAuditEvent(
        organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
        actor_membership_id=actor_id, event_type="ai.governance.champion_rolled_back",
        entity_type="ai_capability_runtime_state", entity_id=state.id,
        detail=f"reason={reason_value};evidence_reference={evidence_value};target={target.registry_fingerprint}",
    ))
    session.flush()
    return state
