from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.ai.evaluation import (
    AIEvaluationError,
    threshold_profile_fingerprint_matches,
    validate_threshold_profile_contract,
)
from src.platform.ai.governance import (
    drift_snapshot_fingerprint_from_row,
    fallback_fingerprint_matches,
    registration_fingerprint_matches,
)
from src.platform.ai.models import (
    AIAuditEvent,
    AICapabilityRuntimeState,
    AICapabilityThreshold,
    AIDriftSnapshot,
    AIEvaluationRun,
    AIModelFallback,
    AIModelRegistration,
    AIPromotionDecision,
)
from src.platform.ai.promotion import resolve_runtime_state


class AIMonitoringError(ValueError):
    pass


def classify_drift(
    *, observed_metrics: dict[str, Any], reference_metrics: dict[str, Any],
    threshold_profile: AICapabilityThreshold,
) -> tuple[str, dict[str, Any]]:
    if not observed_metrics or not reference_metrics:
        return "insufficient_evidence", {"reason": "observed_and_reference_windows_required"}
    try:
        validate_threshold_profile_contract(
            metric_definitions=threshold_profile.metric_definitions,
            minimum_thresholds=getattr(threshold_profile, "minimum_thresholds", {}),
            minimum_deltas=getattr(threshold_profile, "minimum_deltas", {}),
            hard_gates=getattr(threshold_profile, "hard_gates", {}),
            resource_limits=getattr(threshold_profile, "resource_limits", {}),
            failure_threshold=getattr(threshold_profile, "failure_threshold", 1),
            cooldown_seconds=getattr(threshold_profile, "cooldown_seconds", 0),
        )
    except AIEvaluationError as exc:
        return "insufficient_evidence", {"reason": f"threshold_profile_invalid:{exc}"}
    comparisons: dict[str, Any] = {}
    status = "ok"
    for key, definition in threshold_profile.metric_definitions.items():
        observed = observed_metrics.get(key)
        reference = reference_metrics.get(key)
        if (
            isinstance(observed, bool)
            or isinstance(reference, bool)
            or not isinstance(observed, (int, float))
            or not isinstance(reference, (int, float))
            or not math.isfinite(float(observed))
            or not math.isfinite(float(reference))
        ):
            return "insufficient_evidence", {"reason": f"required_metric_invalid:{key}"}
        direction = definition["direction"]
        deterioration = (
            float(reference) - float(observed)
            if direction == "higher"
            else float(observed) - float(reference)
            if direction == "lower"
            else abs(float(observed)) - abs(float(reference))
            if direction == "toward_zero"
            else abs(float(observed) - float(reference))
        )
        warning_delta = float(definition.get("drift_warning_delta", float("inf")))
        blocker_delta = float(definition.get("drift_blocker_delta", float("inf")))
        metric_status = "blocker" if deterioration >= blocker_delta else "warning" if deterioration >= warning_delta else "ok"
        if metric_status == "blocker":
            status = "blocker"
        elif metric_status == "warning" and status == "ok":
            status = "warning"
        comparisons[key] = {
            "observed": observed, "reference": reference,
            "deterioration": deterioration, "status": metric_status,
        }
    return status, comparisons


def create_drift_snapshot(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    product_code: str, capability_key: str, model_registration_id: uuid.UUID,
    threshold_profile_id: uuid.UUID, window_start: datetime, window_end: datetime,
    observed_metrics: dict[str, Any], reference_metrics: dict[str, Any],
    provenance: dict[str, Any], actor_id: uuid.UUID | None,
) -> AIDriftSnapshot:
    registration = session.get(AIModelRegistration, model_registration_id)
    profile = session.get(AICapabilityThreshold, threshold_profile_id)
    if registration is None or profile is None or not profile.enabled:
        raise AIMonitoringError("drift_governance_reference_not_found")
    if not registration_fingerprint_matches(registration):
        raise AIMonitoringError("drift_registration_identity_changed")
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
        raise AIMonitoringError(f"drift_threshold_profile_invalid:{exc}") from exc
    if not threshold_profile_fingerprint_matches(profile):
        raise AIMonitoringError("drift_threshold_profile_identity_changed")
    if window_end <= window_start:
        raise AIMonitoringError("drift_window_invalid")
    if (
        registration.capability_key != capability_key
        or profile.capability_key != capability_key
        or registration.model_family != profile.model_family
        or registration.product_scope not in {"SHARED", product_code}
        or profile.product_scope not in {"SHARED", product_code}
    ):
        raise AIMonitoringError("drift_scope_incompatible")
    status, comparisons = classify_drift(
        observed_metrics=observed_metrics, reference_metrics=reference_metrics,
        threshold_profile=profile,
    )
    metrics = {
        "observed": observed_metrics, "reference": reference_metrics,
        "comparisons": comparisons,
    }
    row = AIDriftSnapshot(
        organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
        capability_key=capability_key, model_registration_id=model_registration_id,
        threshold_profile_id=threshold_profile_id, window_start=window_start,
        window_end=window_end, metrics=metrics, provenance=provenance,
        fingerprint="", status=status, created_by_membership_id=actor_id,
    )
    digest = drift_snapshot_fingerprint_from_row(row, threshold_fingerprint=profile.fingerprint)
    existing = session.scalar(select(AIDriftSnapshot).where(AIDriftSnapshot.fingerprint == digest))
    if existing is not None:
        return existing
    row.fingerprint = digest
    session.add(row)
    session.flush()
    return row


def list_drift_snapshots(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    product_code: str, capability_key: str | None = None,
) -> list[AIDriftSnapshot]:
    statement = select(AIDriftSnapshot).where(
        AIDriftSnapshot.organization_id == organization_id,
        AIDriftSnapshot.workspace_id == workspace_id,
        AIDriftSnapshot.product_code == product_code,
    )
    if capability_key is not None:
        statement = statement.where(AIDriftSnapshot.capability_key == capability_key)
    return list(session.scalars(statement.order_by(AIDriftSnapshot.window_end.desc())).all())


def capability_status(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    product_code: str, capability_key: str
) -> dict[str, Any]:
    registrations = list(session.scalars(select(AIModelRegistration).where(
        AIModelRegistration.product_scope.in_(["SHARED", product_code]),
        AIModelRegistration.capability_key == capability_key,
    ).order_by(AIModelRegistration.created_at)).all())
    state = resolve_runtime_state(session, product_code=product_code, capability_key=capability_key)
    latest_drift = session.scalar(select(AIDriftSnapshot).where(
        AIDriftSnapshot.organization_id == organization_id,
        AIDriftSnapshot.workspace_id == workspace_id,
        AIDriftSnapshot.product_code == product_code,
        AIDriftSnapshot.capability_key == capability_key,
    ).order_by(AIDriftSnapshot.window_end.desc(), AIDriftSnapshot.created_at.desc()))
    latest_decision = session.scalar(select(AIPromotionDecision).join(
        AIEvaluationRun, AIEvaluationRun.id == AIPromotionDecision.candidate_run_id
    ).where(
        AIPromotionDecision.product_code == product_code,
        AIPromotionDecision.capability_key == capability_key,
        AIEvaluationRun.organization_id == organization_id,
        AIEvaluationRun.workspace_id == workspace_id,
        AIEvaluationRun.product_code == product_code,
    ).order_by(AIPromotionDecision.created_at.desc()))
    latest_run = session.scalar(select(AIEvaluationRun).join(
        AIModelRegistration, AIModelRegistration.id == AIEvaluationRun.model_registration_id
    ).where(
        AIEvaluationRun.product_code == product_code,
        AIEvaluationRun.organization_id == organization_id,
        AIEvaluationRun.workspace_id == workspace_id,
        AIModelRegistration.capability_key == capability_key,
    ).order_by(AIEvaluationRun.created_at.desc()))
    fallbacks = []
    for edge in session.scalars(select(AIModelFallback).order_by(AIModelFallback.priority)).all():
        source = session.get(AIModelRegistration, edge.source_registration_id)
        target = session.get(AIModelRegistration, edge.target_registration_id)
        if (
            source
            and target
            and fallback_fingerprint_matches(edge, source, target)
            and source.capability_key == capability_key
            and target.capability_key == capability_key
            and source.product_scope in {"SHARED", product_code}
            and target.product_scope in {"SHARED", product_code}
        ):
            fallbacks.append({
                "edge_id": str(edge.id), "source_registration_id": str(source.id),
                "target_registration_id": str(target.id), "priority": edge.priority,
                "semantically_equivalent": edge.semantically_equivalent,
                "requires_human_review": edge.requires_human_review,
            })
    return {
        "product_code": product_code, "capability_key": capability_key,
        "champion_registration_id": str(state.champion_registration_id) if state and state.champion_registration_id else None,
        "challenger_registration_ids": [str(item.id) for item in registrations if item.lifecycle_state == "challenger"],
        "rollback_registration_id": str(state.rollback_registration_id) if state and state.rollback_registration_id else None,
        "circuit_state": state.circuit_state if state else "unconfigured",
        "consecutive_failures": state.consecutive_failures if state else 0,
        "latest_drift_status": latest_drift.status if latest_drift else "insufficient_evidence",
        "latest_drift_fingerprint": latest_drift.fingerprint if latest_drift else None,
        "latest_evaluation_run_id": str(latest_run.id) if latest_run else None,
        "latest_evaluation_fingerprint": latest_run.result_fingerprint if latest_run else None,
        "latest_promotion_status": latest_decision.decision_status if latest_decision else None,
        "latest_promotion_fingerprint": latest_decision.evidence_fingerprint if latest_decision else None,
        "fallbacks": fallbacks,
        "automatic_training": False, "silent_replacement": False, "scheduler": None,
    }


def reset_circuit(
    session: Session, *, product_code: str, capability_key: str, reason: str,
    actor_id: uuid.UUID | None, organization_id: uuid.UUID, workspace_id: uuid.UUID,
) -> AICapabilityRuntimeState:
    state = resolve_runtime_state(session, product_code=product_code, capability_key=capability_key)
    if state is None:
        raise AIMonitoringError("capability_runtime_state_not_found")
    state.circuit_state = "closed"
    state.consecutive_failures = 0
    state.opened_at = None
    state.version += 1
    state.updated_by_membership_id = actor_id
    session.add(AIAuditEvent(
        organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
        actor_membership_id=actor_id, event_type="ai.runtime.circuit_reset",
        entity_type="ai_capability_runtime_state", entity_id=state.id, detail=f"reason={reason}",
    ))
    session.flush()
    return state
