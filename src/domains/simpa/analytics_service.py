from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domains.simpa.analytics_models import SimpaAISynthesis, SimpaAnalyticsRun, SimpaIndicatorMethodology, SimpaIndicatorResult
from src.domains.simpa.models import SimpaIndicatorDefinition, SimpaIndicatorObservation, SimpaMonitoringCycle
from src.platform.ai.models import AIJob
from src.platform.ai.service import create_ai_job


class SimpaAnalyticsError(ValueError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _ratio(num: int, den: int) -> float:
    return round(float(num) / float(den), 6) if den else 0.0


def _assert_cycle_scope(session: Session, *, cycle_id: uuid.UUID | None, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
    if cycle_id is None:
        return
    cycle = session.scalar(
        select(SimpaMonitoringCycle).where(
            SimpaMonitoringCycle.id == cycle_id,
            SimpaMonitoringCycle.organization_id == organization_id,
            SimpaMonitoringCycle.workspace_id == workspace_id,
        )
    )
    if cycle is None:
        raise SimpaAnalyticsError("monitoring_cycle_not_accessible")


def build_monitoring_snapshot(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    monitoring_cycle_id: uuid.UUID | None = None,
) -> dict:
    _assert_cycle_scope(session, cycle_id=monitoring_cycle_id, organization_id=organization_id, workspace_id=workspace_id)
    base = [
        SimpaIndicatorObservation.organization_id == organization_id,
        SimpaIndicatorObservation.workspace_id == workspace_id,
    ]
    if monitoring_cycle_id is not None:
        base.append(SimpaIndicatorObservation.monitoring_cycle_id == monitoring_cycle_id)
    observations = list(session.scalars(select(SimpaIndicatorObservation).where(*base)).all())
    active_indicators = list(session.scalars(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.active.is_(True))).all())

    total = len(observations)
    validated = sum(1 for row in observations if row.quality_status == "validated")
    draft = sum(1 for row in observations if row.quality_status == "draft")
    rejected = sum(1 for row in observations if row.quality_status == "rejected")
    provenance = sum(1 for row in observations if row.source_version_id is not None or bool((row.provenance_note or "").strip()))
    observed_indicator_ids = {row.indicator_id for row in observations}
    conceptual = sum(1 for row in active_indicators if row.methodology_status == "conceptual")
    validated_methodology = sum(1 for row in active_indicators if row.methodology_status == "validated")

    validated_ratio = _ratio(validated, total)
    provenance_coverage = _ratio(provenance, total)
    indicator_coverage = _ratio(len(observed_indicator_ids), len(active_indicators))
    evidence_quality_score = round((0.45 * validated_ratio) + (0.35 * provenance_coverage) + (0.20 * indicator_coverage), 6)
    if total == 0:
        quality_band = "no_evidence"
    elif evidence_quality_score < 0.50:
        quality_band = "weak"
    elif evidence_quality_score < 0.80:
        quality_band = "moderate"
    else:
        quality_band = "strong"

    return {
        "scope": {"organization_id": str(organization_id), "workspace_id": str(workspace_id), "monitoring_cycle_id": str(monitoring_cycle_id) if monitoring_cycle_id else None},
        "observation_count": total,
        "validated_observation_count": validated,
        "draft_observation_count": draft,
        "rejected_observation_count": rejected,
        "active_indicator_count": len(active_indicators),
        "observed_indicator_count": len(observed_indicator_ids),
        "conceptual_indicator_count": conceptual,
        "validated_methodology_indicator_count": validated_methodology,
        "validated_observation_ratio": validated_ratio,
        "provenance_coverage": provenance_coverage,
        "indicator_coverage": indicator_coverage,
        "evidence_quality_score": evidence_quality_score,
        "evidence_quality_band": quality_band,
        "semantic_notice": "This score measures evidence quality and coverage only; it is not a social-risk or policy-outcome score.",
    }


def create_analytics_run(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, monitoring_cycle_id: uuid.UUID | None, actor_id: uuid.UUID | None) -> SimpaAnalyticsRun:
    snapshot = build_monitoring_snapshot(session, organization_id=organization_id, workspace_id=workspace_id, monitoring_cycle_id=monitoring_cycle_id)
    row = SimpaAnalyticsRun(
        organization_id=organization_id,
        workspace_id=workspace_id,
        monitoring_cycle_id=monitoring_cycle_id,
        status="completed",
        snapshot=snapshot,
        evidence_quality_score=snapshot["evidence_quality_score"],
        validated_observation_ratio=snapshot["validated_observation_ratio"],
        provenance_coverage=snapshot["provenance_coverage"],
        indicator_coverage=snapshot["indicator_coverage"],
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_analytics_runs(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 50) -> list[SimpaAnalyticsRun]:
    return list(session.scalars(select(SimpaAnalyticsRun).where(SimpaAnalyticsRun.organization_id == organization_id, SimpaAnalyticsRun.workspace_id == workspace_id).order_by(SimpaAnalyticsRun.created_at.desc()).limit(max(1, min(limit, 100)))).all())


def list_methodologies(session: Session) -> list[tuple[SimpaIndicatorMethodology, SimpaIndicatorDefinition]]:
    return list(session.execute(select(SimpaIndicatorMethodology, SimpaIndicatorDefinition).join(SimpaIndicatorDefinition, SimpaIndicatorDefinition.id == SimpaIndicatorMethodology.indicator_id).order_by(SimpaIndicatorDefinition.code, SimpaIndicatorMethodology.version_no.desc())).all())


def create_methodology(session: Session, *, indicator_code: str, computation_type: str, methodology_note: str, source_requirements: dict, actor_id: uuid.UUID | None) -> SimpaIndicatorMethodology:
    indicator = session.scalar(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.code == indicator_code, SimpaIndicatorDefinition.active.is_(True)))
    if indicator is None:
        raise SimpaAnalyticsError("indicator_unknown")
    latest = session.scalar(select(func.max(SimpaIndicatorMethodology.version_no)).where(SimpaIndicatorMethodology.indicator_id == indicator.id))
    row = SimpaIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=int(latest or 0) + 1,
        status="draft",
        computation_type=computation_type,
        computation_spec={},
        source_requirements=source_requirements,
        methodology_note=methodology_note.strip(),
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def validate_methodology(session: Session, *, methodology_id: uuid.UUID, validation_note: str, actor_id: uuid.UUID | None) -> SimpaIndicatorMethodology:
    row = session.get(SimpaIndicatorMethodology, methodology_id)
    if row is None:
        raise SimpaAnalyticsError("methodology_not_found")
    indicator = session.get(SimpaIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise SimpaAnalyticsError("indicator_unknown")
    if not row.methodology_note.strip():
        raise SimpaAnalyticsError("methodology_note_required")
    if row.computation_type != "direct_observation":
        raise SimpaAnalyticsError("unsupported_computation_type")
    for other in session.scalars(select(SimpaIndicatorMethodology).where(SimpaIndicatorMethodology.indicator_id == row.indicator_id, SimpaIndicatorMethodology.status == "validated", SimpaIndicatorMethodology.id != row.id)).all():
        other.status = "retired"
    row.status = "validated"
    row.validation_note = validation_note.strip()
    row.approved_by_membership_id = actor_id
    row.approved_at = _utcnow()
    indicator.methodology_status = "validated"
    indicator.methodology_note = row.methodology_note
    session.flush()
    return row


def compute_indicator(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    indicator_code: str,
    monitoring_cycle_id: uuid.UUID | None,
    analytics_run_id: uuid.UUID | None,
    actor_id: uuid.UUID | None,
) -> SimpaIndicatorResult:
    _assert_cycle_scope(session, cycle_id=monitoring_cycle_id, organization_id=organization_id, workspace_id=workspace_id)
    indicator = session.scalar(select(SimpaIndicatorDefinition).where(SimpaIndicatorDefinition.code == indicator_code, SimpaIndicatorDefinition.active.is_(True)))
    if indicator is None:
        raise SimpaAnalyticsError("indicator_unknown")
    if indicator.methodology_status != "validated":
        raise SimpaAnalyticsError("methodology_not_validated")
    methodology = session.scalar(select(SimpaIndicatorMethodology).where(SimpaIndicatorMethodology.indicator_id == indicator.id, SimpaIndicatorMethodology.status == "validated").order_by(SimpaIndicatorMethodology.version_no.desc()))
    if methodology is None:
        raise SimpaAnalyticsError("methodology_not_validated")
    if methodology.computation_type != "direct_observation":
        raise SimpaAnalyticsError("unsupported_computation_type")
    predicates = [
        SimpaIndicatorObservation.organization_id == organization_id,
        SimpaIndicatorObservation.workspace_id == workspace_id,
        SimpaIndicatorObservation.indicator_id == indicator.id,
        SimpaIndicatorObservation.quality_status == "validated",
    ]
    if monitoring_cycle_id is not None:
        predicates.append(SimpaIndicatorObservation.monitoring_cycle_id == monitoring_cycle_id)
    observation = session.scalar(select(SimpaIndicatorObservation).where(*predicates).order_by(SimpaIndicatorObservation.created_at.desc()))
    if observation is None:
        raise SimpaAnalyticsError("validated_observation_required")
    if analytics_run_id is not None:
        run = session.scalar(select(SimpaAnalyticsRun).where(SimpaAnalyticsRun.id == analytics_run_id, SimpaAnalyticsRun.organization_id == organization_id, SimpaAnalyticsRun.workspace_id == workspace_id))
        if run is None:
            raise SimpaAnalyticsError("analytics_run_not_accessible")
    provenance_ok = observation.source_version_id is not None or bool((observation.provenance_note or "").strip())
    result = SimpaIndicatorResult(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=analytics_run_id,
        indicator_id=indicator.id,
        methodology_id=methodology.id,
        value_numeric=observation.value_numeric,
        value_text=observation.value_text,
        unit=indicator.unit_hint,
        quality_score=1.0 if provenance_ok else 0.75,
        source_observation_ids=[str(observation.id)],
        computation_trace={"type": "direct_observation", "methodology_version": methodology.version_no, "observation_quality": observation.quality_status, "provenance_present": provenance_ok},
        status="computed",
        created_by_membership_id=actor_id,
    )
    session.add(result)
    session.flush()
    return result


def _synthesis_input(run: SimpaAnalyticsRun) -> str:
    payload = {
        "analytics_run_id": str(run.id),
        "snapshot": run.snapshot,
        "instruction": "Synthesize only the evidence-quality state. Do not infer citizen-level facts, eligibility, diagnosis, or institutional decisions.",
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def create_synthesis(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, analytics_run_id: uuid.UUID, sensitivity: str, model_key: str | None, actor_id: uuid.UUID | None) -> tuple[SimpaAISynthesis, AIJob]:
    run = session.scalar(select(SimpaAnalyticsRun).where(SimpaAnalyticsRun.id == analytics_run_id, SimpaAnalyticsRun.organization_id == organization_id, SimpaAnalyticsRun.workspace_id == workspace_id))
    if run is None:
        raise SimpaAnalyticsError("analytics_run_not_accessible")
    input_text = _synthesis_input(run)
    job = create_ai_job(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code="SIMPA",
        input_text=input_text,
        prompt_key="simpa.monitoring.synthesis",
        model_key=model_key,
        policy_key="simpa-sensitive-local" if sensitivity == "sensitive" else "shared-local-only",
        sensitivity=sensitivity,
        actor_id=actor_id,
    )
    row = SimpaAISynthesis(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=run.id,
        ai_job_id=job.id,
        source_snapshot_sha256=hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        review_status="pending",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row, job


def list_syntheses(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 50) -> list[tuple[SimpaAISynthesis, AIJob]]:
    return list(session.execute(select(SimpaAISynthesis, AIJob).join(AIJob, AIJob.id == SimpaAISynthesis.ai_job_id).where(SimpaAISynthesis.organization_id == organization_id, SimpaAISynthesis.workspace_id == workspace_id).order_by(SimpaAISynthesis.created_at.desc()).limit(max(1, min(limit, 100)))).all())


def review_synthesis(session: Session, *, synthesis_id: uuid.UUID, organization_id: uuid.UUID, workspace_id: uuid.UUID, decision: str, reviewer_note: str, actor_id: uuid.UUID | None) -> tuple[SimpaAISynthesis, AIJob]:
    row = session.scalar(select(SimpaAISynthesis).where(SimpaAISynthesis.id == synthesis_id, SimpaAISynthesis.organization_id == organization_id, SimpaAISynthesis.workspace_id == workspace_id))
    if row is None:
        raise SimpaAnalyticsError("synthesis_not_accessible")
    job = session.get(AIJob, row.ai_job_id)
    if job is None or job.product_code != "SIMPA" or job.organization_id != organization_id or job.workspace_id != workspace_id:
        raise SimpaAnalyticsError("synthesis_ai_job_not_accessible")
    if job.status not in {"review_required", "succeeded"}:
        raise SimpaAnalyticsError("synthesis_not_reviewable")
    row.review_status = decision
    row.reviewer_note = reviewer_note.strip()
    row.reviewed_by_membership_id = actor_id
    row.reviewed_at = _utcnow()
    job.human_review_status = "accepted" if decision == "accepted" else "rejected"
    session.flush()
    return row, job
