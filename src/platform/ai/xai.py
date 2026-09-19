from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.ai.models import (
    AIDriftSnapshot,
    AIEvaluationBenchmark,
    AIEvaluationResult,
    AIEvaluationReview,
    AIEvaluationRun,
    AIJob,
    AIJobAttempt,
    AIModelRegistration,
    AIPolicyProfile,
    AIPromptVersion,
)
from src.platform.ai.promotion import resolve_runtime_state


UNAVAILABLE_XAI = {
    "confidence": {"state": "unavailable", "reason": "no explicit calibrated confidence contract"},
    "probability": {"state": "unavailable", "reason": "no explicit probability semantics"},
    "calibration": {"state": "unavailable", "reason": "no supplied calibration evidence"},
    "feature_importance": {"state": "unavailable", "reason": "no validated feature-importance evidence"},
    "shap": {"state": "unavailable", "reason": "no validated SHAP attribution evidence"},
    "uncertainty": {"state": "unavailable", "reason": "no supplied uncertainty contract"},
}


def evaluation_explanation(
    session: Session, *, run_id: uuid.UUID, organization_id: uuid.UUID,
    workspace_id: uuid.UUID, product_code: str,
) -> dict[str, Any]:
    run = session.scalar(select(AIEvaluationRun).where(
        AIEvaluationRun.id == run_id,
        AIEvaluationRun.organization_id == organization_id,
        AIEvaluationRun.workspace_id == workspace_id,
        AIEvaluationRun.product_code == product_code,
    ))
    if run is None:
        raise ValueError("evaluation_run_not_found")
    registration = session.get(AIModelRegistration, run.model_registration_id)
    benchmark = session.get(AIEvaluationBenchmark, run.benchmark_id) if run.benchmark_id else None
    prompt = session.get(AIPromptVersion, run.prompt_version_id) if run.prompt_version_id else None
    policy = session.get(AIPolicyProfile, run.policy_profile_id) if run.policy_profile_id else None
    results = list(session.scalars(select(AIEvaluationResult).where(
        AIEvaluationResult.evaluation_run_id == run.id
    ).order_by(AIEvaluationResult.sequence_no)).all())
    reviews = list(session.scalars(select(AIEvaluationReview).where(
        AIEvaluationReview.evaluation_run_id == run.id
    ).order_by(AIEvaluationReview.reviewed_at)).all())
    state = resolve_runtime_state(
        session, product_code=product_code, capability_key=registration.capability_key
    ) if registration else None
    drift = session.scalar(select(AIDriftSnapshot).where(
        AIDriftSnapshot.organization_id == organization_id,
        AIDriftSnapshot.workspace_id == workspace_id,
        AIDriftSnapshot.product_code == product_code,
        AIDriftSnapshot.capability_key == registration.capability_key,
        AIDriftSnapshot.model_registration_id == run.model_registration_id,
    ).order_by(AIDriftSnapshot.window_end.desc()))
    return {
        "product_code": run.product_code,
        "capability_key": registration.capability_key if registration else None,
        "model_registration": {
            "id": str(registration.id), "model_key": registration.model_key,
            "version": registration.version, "fingerprint": registration.registry_fingerprint,
            "family": registration.model_family, "lifecycle_state": registration.lifecycle_state,
        } if registration else None,
        "prompt_identity": {"id": str(prompt.id), "version": prompt.version_no, "checksum": prompt.checksum} if prompt else None,
        "policy_identity": {"id": str(policy.id), "key": policy.policy_key} if policy else None,
        "benchmark_identity": {"id": str(benchmark.id), "fingerprint": benchmark.manifest_fingerprint} if benchmark else {"state": "foundation_only_or_unavailable"},
        "evaluation": {"run_id": str(run.id), "result_fingerprint": run.result_fingerprint, "status": run.status},
        "metrics": [{
            "key": item.result_key, "type": item.result_type, "fingerprint": item.fingerprint,
            "value": item.payload.get("value"), "direction": item.payload.get("direction"),
            "support": item.payload.get("support"), "state": item.payload.get("state", "available"),
            "evidence": item.payload.get("evidence", {}),
        } for item in results],
        "structured_output_validation": next((item.payload for item in results if item.result_key == "structured_schema_compliance"), {"state": "unavailable"}),
        "provenance": run.provenance,
        "final_human_review": next(({
            "decision": review.decision, "fingerprint": review.fingerprint,
            "evidence_reference": review.evidence_reference,
        } for review in reversed(reviews) if review.is_final), None),
        "circuit_state": state.circuit_state if state else "unconfigured",
        "drift_state": drift.status if drift else "insufficient_evidence",
        "rollback_registration_id": str(state.rollback_registration_id) if state and state.rollback_registration_id else None,
        "authority_distinction": "Deterministic numerical systems remain authoritative; generative output is bounded synthesis requiring human review.",
        "unsupported_xai": UNAVAILABLE_XAI,
    }


def job_fallback_explanation(session: Session, *, job_id: uuid.UUID) -> dict[str, Any]:
    job = session.get(AIJob, job_id)
    if job is None:
        raise ValueError("ai_job_not_found")
    attempts = list(session.scalars(select(AIJobAttempt).where(
        AIJobAttempt.job_id == job.id
    ).order_by(AIJobAttempt.attempt_no)).all())
    return {
        "job_id": str(job.id), "source_registration_id": str(job.model_registration_id) if job.model_registration_id else None,
        "legacy_selected_model_only": job.model_registration_id is None,
        "status": job.status, "human_review_status": job.human_review_status,
        "attempts": [{
            "attempt_no": item.attempt_no,
            "model_registration_id": str(item.model_registration_id) if item.model_registration_id else None,
            "fallback_edge_id": str(item.fallback_edge_id) if item.fallback_edge_id else None,
            "is_fallback": item.is_fallback, "requires_human_review": item.requires_human_review,
            "status": item.status, "error_code": item.error_code,
        } for item in attempts],
        "unsupported_xai": UNAVAILABLE_XAI,
    }
