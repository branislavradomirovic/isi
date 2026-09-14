from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domains.ordo.analytics_models import (
    OrdoAISynthesis,
    OrdoAnalyticsRun,
    OrdoDevelopmentGoal,
    OrdoIndicatorMethodology,
    OrdoIndicatorResult,
    OrdoScenario,
    OrdoScenarioAssessment,
)
from src.domains.ordo.models import (
    OrdoDimension,
    OrdoIndicatorDefinition,
    OrdoMonitoringCycle,
    OrdoPillar,
)
from src.domains.ordo.service import validate_ordo_scope
from src.platform.ai.models import AIJob
from src.platform.ai.namespaces import assert_namespace_access, private_namespace, public_namespace
from src.platform.ai.service import create_ai_job
from src.platform.data.analytical_service import GovernedAnalyticalInput, load_governed_analytical_input
from src.platform.data.service import DataPlatformError


class OrdoAnalyticsError(ValueError):
    pass


def _validate_scope(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
    try:
        validate_ordo_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    except RuntimeError as exc:
        raise OrdoAnalyticsError(str(exc)) from None


def _utcnow():
    return datetime.now(timezone.utc)


def _ratio(num: int, den: int) -> float:
    return round(float(num) / float(den), 6) if den else 0.0


def _load_input(session: Session, *, artifact_type: str, artifact_id: uuid.UUID,
                organization_id: uuid.UUID, workspace_id: uuid.UUID) -> GovernedAnalyticalInput:
    try:
        return load_governed_analytical_input(
            session, artifact_type=artifact_type, artifact_id=artifact_id,
            organization_id=organization_id, workspace_id=workspace_id, product_code="ORDO")
    except DataPlatformError as exc:
        raise OrdoAnalyticsError(str(exc)) from None


def _analytical_source(value: GovernedAnalyticalInput) -> dict:
    return {
        "artifact_type": value.artifact_type,
        "artifact_id": str(value.artifact_id),
        "artifact_fingerprint": value.artifact_fingerprint,
        "dataset_contract_version_id": str(value.dataset_contract_version_id),
        "dataset_contract_fingerprint": value.dataset_contract_fingerprint,
        "analytical_quality_state": value.analytical_quality_state,
        "resolved_snapshot_id": str(value.snapshot_id),
        "resolved_snapshot_fingerprint": value.snapshot_fingerprint,
    }


def _validate_direct_observation_contract(value: GovernedAnalyticalInput, *, cycle: bool) -> None:
    fields = {str(item.get("field_key")): item for item in value.field_contract}
    expected = {
        "indicator_code": ("STRING", True), "quality_status": ("STRING", True),
        "value_numeric": ("NUMBER", False), "value_text": ("STRING", False),
    }
    for key, (logical_type, required) in expected.items():
        field = fields.get(key)
        if field is None or field.get("logical_type") != logical_type or bool(field.get("required")) != required:
            raise OrdoAnalyticsError("direct_observation_contract_invalid")
    field = fields.get("monitoring_cycle_id")
    if field is not None and (field.get("logical_type") != "STRING" or bool(field.get("required"))):
        raise OrdoAnalyticsError("direct_observation_contract_invalid")
    if cycle and field is None:
        raise OrdoAnalyticsError("direct_observation_cycle_contract_required")


def _records(value: GovernedAnalyticalInput, monitoring_cycle_id: uuid.UUID | None):
    _validate_direct_observation_contract(value, cycle=monitoring_cycle_id is not None)
    selected = []
    for record in value.records:
        quality, code = record.payload.get("quality_status"), record.payload.get("indicator_code")
        if quality not in {"validated", "draft", "rejected"} or not isinstance(code, str) or not code.strip():
            raise OrdoAnalyticsError("direct_observation_record_invalid")
        if monitoring_cycle_id is not None and record.payload.get("monitoring_cycle_id") != str(monitoring_cycle_id):
            continue
        selected.append(record)
    return selected


def revalidate_analytics_run(session: Session, *, run: OrdoAnalyticsRun,
                             organization_id: uuid.UUID, workspace_id: uuid.UUID) -> GovernedAnalyticalInput:
    if run.status != "completed" or (run.organization_id, run.workspace_id) != (organization_id, workspace_id):
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    if run.analytical_artifact_type == "ANALYTICAL_SNAPSHOT":
        artifact_type, artifact_id = "snapshot", run.analytical_snapshot_id
    elif run.analytical_artifact_type == "ANALYTICAL_FEATURE_VERSION":
        artifact_type, artifact_id = "feature_version", run.analytical_feature_version_id
    else:
        raise OrdoAnalyticsError("legacy_analytics_run_ineligible")
    if artifact_id is None:
        raise OrdoAnalyticsError("analytics_run_governed_binding_invalid")
    value = _load_input(session, artifact_type=artifact_type, artifact_id=artifact_id,
                        organization_id=organization_id, workspace_id=workspace_id)
    if (run.analytical_artifact_fingerprint != value.artifact_fingerprint
            or run.dataset_contract_version_id != value.dataset_contract_version_id
            or run.dataset_contract_fingerprint != value.dataset_contract_fingerprint
            or run.analytical_quality_state != value.analytical_quality_state
            or (run.snapshot or {}).get("analytical_source") != _analytical_source(value)):
        raise OrdoAnalyticsError("analytics_run_governed_binding_changed")
    return value


def _assert_cycle_scope(
    session: Session,
    *,
    cycle_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> None:
    if cycle_id is None:
        return
    cycle = session.scalar(
        select(OrdoMonitoringCycle).where(
            OrdoMonitoringCycle.id == cycle_id,
            OrdoMonitoringCycle.organization_id == organization_id,
            OrdoMonitoringCycle.workspace_id == workspace_id,
        )
    )
    if cycle is None:
        raise OrdoAnalyticsError("monitoring_cycle_not_accessible")


def build_destination_snapshot(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytical_artifact_type: str,
    analytical_artifact_id: uuid.UUID,
    monitoring_cycle_id: uuid.UUID | None = None,
) -> dict:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    _assert_cycle_scope(
        session,
        cycle_id=monitoring_cycle_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    analytical_input = _load_input(
        session, artifact_type=analytical_artifact_type, artifact_id=analytical_artifact_id,
        organization_id=organization_id, workspace_id=workspace_id)
    observations = _records(analytical_input, monitoring_cycle_id)
    active_indicators = list(
        session.scalars(
            select(OrdoIndicatorDefinition).where(OrdoIndicatorDefinition.active.is_(True))
        ).all()
    )
    dimensions = list(session.scalars(select(OrdoDimension).where(OrdoDimension.active.is_(True))).all())
    pillars = list(session.scalars(select(OrdoPillar).where(OrdoPillar.active.is_(True))).all())

    total = len(observations)
    indicators_by_code = {row.code: row for row in active_indicators}
    for observation in observations:
        if observation.payload["indicator_code"] not in indicators_by_code:
            raise OrdoAnalyticsError("indicator_unknown")
    validated = sum(1 for row in observations if row.payload["quality_status"] == "validated")
    draft = sum(1 for row in observations if row.payload["quality_status"] == "draft")
    rejected = sum(1 for row in observations if row.payload["quality_status"] == "rejected")
    provenance = total
    observed_indicator_ids = {indicators_by_code[str(row.payload["indicator_code"])].id for row in observations}
    indicator_by_id = {row.id: row for row in active_indicators}
    observed_dimensions = {
        indicator_by_id[indicators_by_code[str(row.payload["indicator_code"])].id].dimension_code
        for row in observations
        if indicators_by_code[str(row.payload["indicator_code"])].id in indicator_by_id
    }
    observed_pillars = {
        indicator_by_id[indicators_by_code[str(row.payload["indicator_code"])].id].pillar_code
        for row in observations
        if indicators_by_code[str(row.payload["indicator_code"])].id in indicator_by_id
    }
    conceptual = sum(1 for row in active_indicators if row.methodology_status == "conceptual")
    validated_methodology = sum(1 for row in active_indicators if row.methodology_status == "validated")

    validated_ratio = _ratio(validated, total)
    provenance_coverage = _ratio(provenance, total)
    indicator_coverage = _ratio(len(observed_indicator_ids), len(active_indicators))
    dimension_coverage = _ratio(len(observed_dimensions), len(dimensions))
    pillar_coverage = _ratio(len(observed_pillars), len(pillars))
    evidence_quality_score = round(
        (0.45 * validated_ratio) + (0.35 * provenance_coverage) + (0.20 * indicator_coverage),
        6,
    )
    if total == 0:
        quality_band = "no_evidence"
    elif evidence_quality_score < 0.50:
        quality_band = "weak"
    elif evidence_quality_score < 0.80:
        quality_band = "moderate"
    else:
        quality_band = "strong"

    return {
        "analytical_source": _analytical_source(analytical_input),
        "scope": {
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "monitoring_cycle_id": str(monitoring_cycle_id) if monitoring_cycle_id else None,
        },
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
        "dimension_coverage": dimension_coverage,
        "pillar_coverage": pillar_coverage,
        "observed_dimensions": sorted(observed_dimensions),
        "missing_dimensions": sorted({row.code for row in dimensions} - observed_dimensions),
        "observed_pillars": sorted(observed_pillars),
        "missing_pillars": sorted({row.code for row in pillars} - observed_pillars),
        "evidence_quality_score": evidence_quality_score,
        "evidence_quality_band": quality_band,
        "semantic_notice": (
            "This score measures evidence quality and coverage only. It is not a competitiveness, "
            "sustainability, inclusion, employment, quality-of-life, investment, or destination-performance score."
        ),
    }


def create_analytics_run(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytical_artifact_type: str,
    analytical_artifact_id: uuid.UUID,
    monitoring_cycle_id: uuid.UUID | None,
    actor_id: uuid.UUID | None,
) -> OrdoAnalyticsRun:
    snapshot = build_destination_snapshot(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytical_artifact_type=analytical_artifact_type,
        analytical_artifact_id=analytical_artifact_id,
        monitoring_cycle_id=monitoring_cycle_id,
    )
    source = snapshot["analytical_source"]
    row = OrdoAnalyticsRun(
        organization_id=organization_id,
        workspace_id=workspace_id,
        monitoring_cycle_id=monitoring_cycle_id,
        analytical_artifact_type=("ANALYTICAL_SNAPSHOT" if analytical_artifact_type == "snapshot" else "ANALYTICAL_FEATURE_VERSION"),
        analytical_snapshot_id=analytical_artifact_id if analytical_artifact_type == "snapshot" else None,
        analytical_feature_version_id=analytical_artifact_id if analytical_artifact_type == "feature_version" else None,
        analytical_artifact_fingerprint=source["artifact_fingerprint"],
        dataset_contract_version_id=uuid.UUID(source["dataset_contract_version_id"]),
        dataset_contract_fingerprint=source["dataset_contract_fingerprint"],
        analytical_quality_state=source["analytical_quality_state"],
        status="completed",
        snapshot=snapshot,
        evidence_quality_score=snapshot["evidence_quality_score"],
        validated_observation_ratio=snapshot["validated_observation_ratio"],
        provenance_coverage=snapshot["provenance_coverage"],
        indicator_coverage=snapshot["indicator_coverage"],
        dimension_coverage=snapshot["dimension_coverage"],
        pillar_coverage=snapshot["pillar_coverage"],
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_analytics_runs(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    limit: int = 50,
) -> list[OrdoAnalyticsRun]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(
        session.scalars(
            select(OrdoAnalyticsRun)
            .where(
                OrdoAnalyticsRun.organization_id == organization_id,
                OrdoAnalyticsRun.workspace_id == workspace_id,
            )
            .order_by(OrdoAnalyticsRun.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def list_methodologies(session: Session) -> list[tuple[OrdoIndicatorMethodology, OrdoIndicatorDefinition]]:
    return list(
        session.execute(
            select(OrdoIndicatorMethodology, OrdoIndicatorDefinition)
            .join(OrdoIndicatorDefinition, OrdoIndicatorDefinition.id == OrdoIndicatorMethodology.indicator_id)
            .order_by(OrdoIndicatorDefinition.code, OrdoIndicatorMethodology.version_no.desc())
        ).all()
    )


def create_methodology(
    session: Session,
    *,
    indicator_code: str,
    computation_type: str,
    methodology_note: str,
    source_requirements: dict,
    actor_id: uuid.UUID | None,
) -> OrdoIndicatorMethodology:
    indicator = session.scalar(
        select(OrdoIndicatorDefinition).where(
            OrdoIndicatorDefinition.code == indicator_code,
            OrdoIndicatorDefinition.active.is_(True),
        )
    )
    if indicator is None:
        raise OrdoAnalyticsError("indicator_unknown")
    latest = session.scalar(
        select(func.max(OrdoIndicatorMethodology.version_no)).where(
            OrdoIndicatorMethodology.indicator_id == indicator.id
        )
    )
    row = OrdoIndicatorMethodology(
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


def validate_methodology(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    validation_note: str,
    actor_id: uuid.UUID | None,
) -> OrdoIndicatorMethodology:
    row = session.get(OrdoIndicatorMethodology, methodology_id)
    if row is None:
        raise OrdoAnalyticsError("methodology_not_found")
    indicator = session.get(OrdoIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise OrdoAnalyticsError("indicator_unknown")
    if not row.methodology_note.strip():
        raise OrdoAnalyticsError("methodology_note_required")
    if row.computation_type != "direct_observation":
        raise OrdoAnalyticsError("unsupported_computation_type")
    for other in session.scalars(
        select(OrdoIndicatorMethodology).where(
            OrdoIndicatorMethodology.indicator_id == row.indicator_id,
            OrdoIndicatorMethodology.status == "validated",
            OrdoIndicatorMethodology.id != row.id,
        )
    ).all():
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
    analytics_run_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> OrdoIndicatorResult:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    _assert_cycle_scope(
        session,
        cycle_id=monitoring_cycle_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    indicator = session.scalar(
        select(OrdoIndicatorDefinition).where(
            OrdoIndicatorDefinition.code == indicator_code,
            OrdoIndicatorDefinition.active.is_(True),
        )
    )
    if indicator is None:
        raise OrdoAnalyticsError("indicator_unknown")
    if indicator.methodology_status != "validated":
        raise OrdoAnalyticsError("methodology_not_validated")
    methodology = session.scalar(
        select(OrdoIndicatorMethodology)
        .where(
            OrdoIndicatorMethodology.indicator_id == indicator.id,
            OrdoIndicatorMethodology.status == "validated",
        )
        .order_by(OrdoIndicatorMethodology.version_no.desc())
    )
    if methodology is None:
        raise OrdoAnalyticsError("methodology_not_validated")
    if methodology.computation_type != "direct_observation":
        raise OrdoAnalyticsError("unsupported_computation_type")

    run = session.scalar(select(OrdoAnalyticsRun).where(
        OrdoAnalyticsRun.id == analytics_run_id,
        OrdoAnalyticsRun.organization_id == organization_id,
        OrdoAnalyticsRun.workspace_id == workspace_id))
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    if monitoring_cycle_id != run.monitoring_cycle_id:
        raise OrdoAnalyticsError("monitoring_cycle_run_mismatch")
    analytical_input = revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    matches = [row for row in _records(analytical_input, monitoring_cycle_id)
               if row.payload["indicator_code"] == indicator.code
               and row.payload["quality_status"] == "validated"]
    if not matches:
        raise OrdoAnalyticsError("validated_observation_required")
    if len(matches) > 1:
        raise OrdoAnalyticsError("validated_observation_ambiguous")
    observation = matches[0]
    numeric, text = observation.payload.get("value_numeric"), observation.payload.get("value_text")
    value_text = text.strip() if isinstance(text, str) else ""
    if numeric is None and not value_text:
        raise OrdoAnalyticsError("computed_value_required")
    result = OrdoIndicatorResult(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=analytics_run_id,
        indicator_id=indicator.id,
        methodology_id=methodology.id,
        value_numeric=float(numeric) if numeric is not None else None,
        value_text=value_text,
        unit=indicator.unit_hint,
        quality_score=1.0,
        source_observation_ids=[],
        computation_trace={
            "type": "direct_observation",
            "artifact_type": analytical_input.artifact_type,
            "artifact_id": str(analytical_input.artifact_id),
            "artifact_fingerprint": analytical_input.artifact_fingerprint,
            "dataset_contract_fingerprint": analytical_input.dataset_contract_fingerprint,
            "normalized_record_id": str(observation.normalized_record_id),
            "identity_fingerprint": observation.identity_fingerprint,
            "content_fingerprint": observation.content_fingerprint,
            "methodology_version": methodology.version_no,
            "analytical_quality_state": analytical_input.analytical_quality_state,
            "observation_quality": "validated",
            "provenance_present": True,
            "forecast_performed": False,
        },
        status="computed",
        created_by_membership_id=actor_id,
    )
    session.add(result)
    session.flush()
    return result


def list_goals(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> list[OrdoDevelopmentGoal]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(
        session.scalars(
            select(OrdoDevelopmentGoal)
            .where(
                OrdoDevelopmentGoal.organization_id == organization_id,
                OrdoDevelopmentGoal.workspace_id == workspace_id,
            )
            .order_by(OrdoDevelopmentGoal.created_at.desc())
        ).all()
    )


def create_goal(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    code: str,
    title: str,
    description: str,
    focus_area: str,
    target_horizon,
    status: str,
    actor_id: uuid.UUID | None,
) -> OrdoDevelopmentGoal:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = OrdoDevelopmentGoal(
        organization_id=organization_id,
        workspace_id=workspace_id,
        code=code.strip(),
        title=title.strip(),
        description=description.strip(),
        focus_area=focus_area,
        target_horizon=target_horizon,
        status=status,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_scenarios(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> list[tuple[OrdoScenario, OrdoDevelopmentGoal]]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(
        session.execute(
            select(OrdoScenario, OrdoDevelopmentGoal)
            .join(OrdoDevelopmentGoal, OrdoDevelopmentGoal.id == OrdoScenario.goal_id)
            .where(
                OrdoScenario.organization_id == organization_id,
                OrdoScenario.workspace_id == workspace_id,
            )
            .order_by(OrdoScenario.created_at.desc())
        ).all()
    )


def create_scenario(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    goal_id: uuid.UUID,
    name: str,
    description: str,
    assumptions: list[str],
    measures: list[str],
    actor_id: uuid.UUID | None,
) -> OrdoScenario:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    goal = session.scalar(
        select(OrdoDevelopmentGoal).where(
            OrdoDevelopmentGoal.id == goal_id,
            OrdoDevelopmentGoal.organization_id == organization_id,
            OrdoDevelopmentGoal.workspace_id == workspace_id,
        )
    )
    if goal is None:
        raise OrdoAnalyticsError("development_goal_not_accessible")
    row = OrdoScenario(
        organization_id=organization_id,
        workspace_id=workspace_id,
        goal_id=goal.id,
        name=name.strip(),
        description=description.strip(),
        assumptions=[str(item).strip() for item in assumptions if str(item).strip()],
        measures=[str(item).strip() for item in measures if str(item).strip()],
        status="draft",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def set_scenario_status(
    session: Session,
    *,
    scenario_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    status: str,
) -> OrdoScenario:
    row = session.scalar(
        select(OrdoScenario).where(
            OrdoScenario.id == scenario_id,
            OrdoScenario.organization_id == organization_id,
            OrdoScenario.workspace_id == workspace_id,
        )
    )
    if row is None:
        raise OrdoAnalyticsError("scenario_not_accessible")
    row.status = status
    session.flush()
    return row


def _scenario_assessment_payload(
    *,
    scenario: OrdoScenario,
    goal: OrdoDevelopmentGoal,
    run: OrdoAnalyticsRun,
) -> dict:
    snapshot = run.snapshot or {}
    return {
        "assessment_mode": "evidence_readiness_only",
        "forecast_performed": False,
        "goal": {
            "code": goal.code,
            "title": goal.title,
            "focus_area": goal.focus_area,
            "target_horizon": goal.target_horizon.isoformat() if goal.target_horizon else None,
        },
        "scenario": {
            "name": scenario.name,
            "assumption_count": len(scenario.assumptions or []),
            "measure_count": len(scenario.measures or []),
        },
        "evidence": {
            "quality_score": snapshot.get("evidence_quality_score", 0.0),
            "quality_band": snapshot.get("evidence_quality_band", "no_evidence"),
            "provenance_coverage": snapshot.get("provenance_coverage", 0.0),
            "indicator_coverage": snapshot.get("indicator_coverage", 0.0),
            "dimension_coverage": snapshot.get("dimension_coverage", 0.0),
            "pillar_coverage": snapshot.get("pillar_coverage", 0.0),
            "observed_dimensions": snapshot.get("observed_dimensions", []),
            "missing_dimensions": snapshot.get("missing_dimensions", []),
        },
        "limitations": [
            "No causal, predictive, financial, visitor-volume, employment, sustainability, inclusion, or quality-of-life effect is calculated by this assessment.",
            "Scenario assumptions and measures are user-authored planning inputs, not verified outcomes.",
            "A human expert must interpret the evidence before a scenario can inform a development decision.",
        ],
    }


def create_scenario_assessment(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    scenario_id: uuid.UUID,
    analytics_run_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> OrdoScenarioAssessment:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    scenario = session.scalar(
        select(OrdoScenario).where(
            OrdoScenario.id == scenario_id,
            OrdoScenario.organization_id == organization_id,
            OrdoScenario.workspace_id == workspace_id,
        )
    )
    if scenario is None:
        raise OrdoAnalyticsError("scenario_not_accessible")
    goal = session.scalar(
        select(OrdoDevelopmentGoal).where(
            OrdoDevelopmentGoal.id == scenario.goal_id,
            OrdoDevelopmentGoal.organization_id == organization_id,
            OrdoDevelopmentGoal.workspace_id == workspace_id,
        )
    )
    if goal is None:
        raise OrdoAnalyticsError("development_goal_not_accessible")
    run = session.scalar(
        select(OrdoAnalyticsRun).where(
            OrdoAnalyticsRun.id == analytics_run_id,
            OrdoAnalyticsRun.organization_id == organization_id,
            OrdoAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    assessment = _scenario_assessment_payload(scenario=scenario, goal=goal, run=run)
    row = OrdoScenarioAssessment(
        organization_id=organization_id,
        workspace_id=workspace_id,
        scenario_id=scenario.id,
        analytics_run_id=run.id,
        evidence_snapshot=run.snapshot,
        assessment=assessment,
        forecast_performed=False,
        status="evidence_only",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def list_scenario_assessments(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> list[OrdoScenarioAssessment]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(
        session.scalars(
            select(OrdoScenarioAssessment)
            .where(
                OrdoScenarioAssessment.organization_id == organization_id,
                OrdoScenarioAssessment.workspace_id == workspace_id,
            )
            .order_by(OrdoScenarioAssessment.created_at.desc())
        ).all()
    )


def review_scenario_assessment(
    session: Session,
    *,
    assessment_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    decision: str,
    reviewer_note: str,
    actor_id: uuid.UUID | None,
) -> OrdoScenarioAssessment:
    row = session.scalar(
        select(OrdoScenarioAssessment).where(
            OrdoScenarioAssessment.id == assessment_id,
            OrdoScenarioAssessment.organization_id == organization_id,
            OrdoScenarioAssessment.workspace_id == workspace_id,
        )
    )
    if row is None:
        raise OrdoAnalyticsError("scenario_assessment_not_accessible")
    run = session.scalar(
        select(OrdoAnalyticsRun).where(
            OrdoAnalyticsRun.id == row.analytics_run_id,
            OrdoAnalyticsRun.organization_id == organization_id,
            OrdoAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    row.status = decision
    row.reviewer_note = reviewer_note.strip()
    row.reviewed_by_membership_id = actor_id
    row.reviewed_at = _utcnow()
    session.flush()
    return row


def _allowed_knowledge_namespaces(organization_id: uuid.UUID) -> list[str]:
    namespaces = [
        private_namespace(organization_id, "ORDO"),
        public_namespace("ORDO"),
        public_namespace("ISI"),
    ]
    for namespace in namespaces:
        assert_namespace_access(namespace, organization_id=organization_id, product_code="ORDO")
    return namespaces


def _synthesis_input(
    *,
    run: OrdoAnalyticsRun,
    scenario: OrdoScenario | None,
    goal: OrdoDevelopmentGoal | None,
    synthesis_type: str,
) -> str:
    payload = {
        "synthesis_type": synthesis_type,
        "analytics_run_id": str(run.id),
        "analytical_source": (run.snapshot or {}).get("analytical_source"),
        "snapshot": run.snapshot,
        "scenario": None,
        "development_goal": None,
        "instruction": (
            "Use only supplied evidence and user-authored scenario inputs. Distinguish evidence from assumptions. "
            "Do not forecast effects, invent facts, rank destinations, recommend an investment as certain, or make a development decision."
        ),
    }
    if scenario is not None:
        payload["scenario"] = {
            "id": str(scenario.id),
            "name": scenario.name,
            "description": scenario.description,
            "assumptions": scenario.assumptions,
            "measures": scenario.measures,
            "status": scenario.status,
        }
    if goal is not None:
        payload["development_goal"] = {
            "id": str(goal.id),
            "code": goal.code,
            "title": goal.title,
            "description": goal.description,
            "focus_area": goal.focus_area,
            "target_horizon": goal.target_horizon.isoformat() if goal.target_horizon else None,
        }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def create_synthesis(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID,
    scenario_id: uuid.UUID | None,
    synthesis_type: str,
    model_key: str | None,
    actor_id: uuid.UUID | None,
) -> tuple[OrdoAISynthesis, AIJob]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    run = session.scalar(
        select(OrdoAnalyticsRun).where(
            OrdoAnalyticsRun.id == analytics_run_id,
            OrdoAnalyticsRun.organization_id == organization_id,
            OrdoAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id)

    scenario = None
    goal = None
    if synthesis_type == "scenario_review":
        if scenario_id is None:
            raise OrdoAnalyticsError("scenario_required")
        scenario = session.scalar(
            select(OrdoScenario).where(
                OrdoScenario.id == scenario_id,
                OrdoScenario.organization_id == organization_id,
                OrdoScenario.workspace_id == workspace_id,
            )
        )
        if scenario is None:
            raise OrdoAnalyticsError("scenario_not_accessible")
        goal = session.scalar(
            select(OrdoDevelopmentGoal).where(
                OrdoDevelopmentGoal.id == scenario.goal_id,
                OrdoDevelopmentGoal.organization_id == organization_id,
                OrdoDevelopmentGoal.workspace_id == workspace_id,
            )
        )
        if goal is None:
            raise OrdoAnalyticsError("development_goal_not_accessible")
    elif scenario_id is not None:
        raise OrdoAnalyticsError("scenario_not_allowed_for_monitoring_synthesis")

    namespaces = _allowed_knowledge_namespaces(organization_id)
    input_text = _synthesis_input(
        run=run,
        scenario=scenario,
        goal=goal,
        synthesis_type=synthesis_type,
    )
    input_text = json.dumps(
        {
            "knowledge_namespace_contract": namespaces,
            "retrieval_note": (
                "Namespaces are access boundaries for ORDO knowledge. This ISI-11 synthesis does not claim semantic retrieval "
                "unless retrieved chunks are explicitly supplied by the shared AI layer."
            ),
            "payload": json.loads(input_text),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    job = create_ai_job(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code="ORDO",
        input_text=input_text,
        prompt_key="ordo.decision_support.synthesis",
        model_key=model_key,
        policy_key="ordo-decision-support-local",
        sensitivity="internal",
        actor_id=actor_id,
    )
    row = OrdoAISynthesis(
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=run.id,
        scenario_id=scenario.id if scenario else None,
        ai_job_id=job.id,
        synthesis_type=synthesis_type,
        source_snapshot_sha256=hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        review_status="pending",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row, job


def list_syntheses(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    limit: int = 50,
) -> list[tuple[OrdoAISynthesis, AIJob]]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(
        session.execute(
            select(OrdoAISynthesis, AIJob)
            .join(AIJob, AIJob.id == OrdoAISynthesis.ai_job_id)
            .where(
                OrdoAISynthesis.organization_id == organization_id,
                OrdoAISynthesis.workspace_id == workspace_id,
            )
            .order_by(OrdoAISynthesis.created_at.desc())
            .limit(max(1, min(limit, 100)))
        ).all()
    )


def review_synthesis(
    session: Session,
    *,
    synthesis_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    decision: str,
    reviewer_note: str,
    actor_id: uuid.UUID | None,
) -> tuple[OrdoAISynthesis, AIJob]:
    row = session.scalar(
        select(OrdoAISynthesis).where(
            OrdoAISynthesis.id == synthesis_id,
            OrdoAISynthesis.organization_id == organization_id,
            OrdoAISynthesis.workspace_id == workspace_id,
        )
    )
    if row is None:
        raise OrdoAnalyticsError("synthesis_not_accessible")
    run = session.scalar(
        select(OrdoAnalyticsRun).where(
            OrdoAnalyticsRun.id == row.analytics_run_id,
            OrdoAnalyticsRun.organization_id == organization_id,
            OrdoAnalyticsRun.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    job = session.get(AIJob, row.ai_job_id)
    if (
        job is None
        or job.product_code != "ORDO"
        or job.organization_id != organization_id
        or job.workspace_id != workspace_id
    ):
        raise OrdoAnalyticsError("synthesis_ai_job_not_accessible")
    if job.status not in {"review_required", "succeeded"}:
        raise OrdoAnalyticsError("synthesis_not_reviewable")
    row.review_status = decision
    row.reviewer_note = reviewer_note.strip()
    row.reviewed_by_membership_id = actor_id
    row.reviewed_at = _utcnow()
    job.human_review_status = "accepted" if decision == "accepted" else "rejected"
    session.flush()
    return row, job
