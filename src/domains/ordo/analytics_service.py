from __future__ import annotations

import hashlib
import json
import calendar
import math
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import ValidationError

from src.domains.ordo.analytics_models import (
    OrdoAISynthesis,
    OrdoAnalyticsRun,
    OrdoDevelopmentGoal,
    OrdoIndicatorMethodology,
    OrdoIndicatorResult,
    OrdoForecastRun,
    OrdoSpatialAggregationRun,
    OrdoStatisticalModelContract,
    OrdoTimeSeriesSpec,
    OrdoScenario,
    OrdoScenarioAssessment,
)
from src.domains.ordo.forecast_metrics import aggregate_point_metrics, mae, mase
from src.domains.ordo.forecasting import (
    ENGINE_KEY,
    ENGINE_VERSION,
    INTERVAL_METHOD,
    ForecastNotEstimated,
    clip_interval,
    empirical_residual_interval,
    forecast_family,
    run_rolling_origin,
)
from src.domains.ordo.models import (
    OrdoDimension,
    OrdoIndicatorDefinition,
    OrdoMonitoringCycle,
    OrdoPillar,
    OrdoSpatialUnit,
)
from src.domains.ordo.spatial_processing import (
    OrdoSpatialAggregationContractV1,
    aggregate_numeric_values,
    canonical_sha256,
)
from src.domains.ordo.statistical_contracts import (
    OrdoStatisticalModelContractV1,
    contract_fingerprint as statistical_contract_fingerprint,
    normalize_statistical_model_contract,
)
from src.domains.ordo.time_series_contracts import (
    OrdoTimeSeriesSpecV1,
    contract_fingerprint as time_series_contract_fingerprint,
    normalize_time_series_spec,
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


def _require_methodology_actor(actor_id: uuid.UUID | None) -> uuid.UUID:
    if actor_id is None:
        raise OrdoAnalyticsError("methodology_actor_required")
    return actor_id


def _methodology_fingerprint(row: OrdoIndicatorMethodology) -> str:
    return canonical_sha256({
        "indicator_id": str(row.indicator_id),
        "version_no": row.version_no,
        "computation_type": row.computation_type,
        "computation_spec": row.computation_spec,
        "source_requirements": row.source_requirements,
        "methodology_note": row.methodology_note,
    })


def _input_snapshot_sha256(value: GovernedAnalyticalInput) -> str:
    return canonical_sha256({
        "artifact_type": value.artifact_type,
        "artifact_id": str(value.artifact_id),
        "artifact_fingerprint": value.artifact_fingerprint,
        "records": sorted(
            ({"identity": row.identity_fingerprint, "content": row.content_fingerprint} for row in value.records),
            key=lambda item: (item["identity"], item["content"]),
        ),
    })


def _sync_indicator_methodology_summary(
    session: Session, indicator: OrdoIndicatorDefinition
) -> None:
    active = session.scalar(
        select(OrdoIndicatorMethodology)
        .where(
            OrdoIndicatorMethodology.indicator_id == indicator.id,
            OrdoIndicatorMethodology.status == "validated",
        )
        .order_by(OrdoIndicatorMethodology.version_no.desc())
    )
    if active is None:
        any_retired = session.scalar(
            select(OrdoIndicatorMethodology.id).where(
                OrdoIndicatorMethodology.indicator_id == indicator.id,
                OrdoIndicatorMethodology.status == "retired",
            )
        )
        indicator.methodology_status = "retired" if any_retired is not None else "conceptual"
        if any_retired is None:
            indicator.methodology_note = ""
    else:
        indicator.methodology_status = "validated"
        indicator.methodology_note = active.methodology_note


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


def propose_methodology(
    session: Session, *, methodology_id: uuid.UUID, actor_id: uuid.UUID | None
) -> OrdoIndicatorMethodology:
    actor = _require_methodology_actor(actor_id)
    row = session.get(OrdoIndicatorMethodology, methodology_id)
    if row is None:
        raise OrdoAnalyticsError("methodology_not_found")
    if row.status != "draft":
        raise OrdoAnalyticsError("methodology_not_draft")
    indicator = session.get(OrdoIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise OrdoAnalyticsError("indicator_unknown")
    if not row.methodology_note.strip():
        raise OrdoAnalyticsError("methodology_note_required")
    row.status = "proposed"
    row.proposed_by_membership_id = actor
    row.proposed_at = _utcnow()
    session.flush()
    return row


def validate_methodology(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    validation_note: str,
    actor_id: uuid.UUID | None,
) -> OrdoIndicatorMethodology:
    actor = _require_methodology_actor(actor_id)
    row = session.get(OrdoIndicatorMethodology, methodology_id)
    if row is None:
        raise OrdoAnalyticsError("methodology_not_found")
    indicator = session.get(OrdoIndicatorDefinition, row.indicator_id)
    if indicator is None or not indicator.active:
        raise OrdoAnalyticsError("indicator_unknown")
    if row.status != "proposed":
        raise OrdoAnalyticsError("methodology_not_proposed")
    note = validation_note.strip()
    if not note:
        raise OrdoAnalyticsError("validation_note_required")
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
        other.retired_by_membership_id = actor
        other.retired_at = _utcnow()
        other.retirement_note = f"Superseded by validated methodology version {row.version_no}."
    row.status = "validated"
    row.validation_note = note
    row.approved_by_membership_id = actor
    row.approved_at = _utcnow()
    session.flush()
    _sync_indicator_methodology_summary(session, indicator)
    session.flush()
    return row


def retire_methodology(
    session: Session,
    *,
    methodology_id: uuid.UUID,
    retirement_note: str,
    actor_id: uuid.UUID | None,
) -> OrdoIndicatorMethodology:
    actor = _require_methodology_actor(actor_id)
    row = session.get(OrdoIndicatorMethodology, methodology_id)
    if row is None:
        raise OrdoAnalyticsError("methodology_not_found")
    if row.status != "validated":
        raise OrdoAnalyticsError("methodology_not_validated")
    note = retirement_note.strip()
    if not note:
        raise OrdoAnalyticsError("retirement_note_required")
    indicator = session.get(OrdoIndicatorDefinition, row.indicator_id)
    if indicator is None:
        raise OrdoAnalyticsError("indicator_unknown")
    row.status = "retired"
    row.retired_by_membership_id = actor
    row.retired_at = _utcnow()
    row.retirement_note = note
    session.flush()
    _sync_indicator_methodology_summary(session, indicator)
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


def create_spatial_aggregation_run(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID,
    indicator_code: str,
    target_spatial_unit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> OrdoSpatialAggregationRun:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    indicator = session.scalar(select(OrdoIndicatorDefinition).where(
        OrdoIndicatorDefinition.code == indicator_code,
        OrdoIndicatorDefinition.active.is_(True),
    ))
    if indicator is None:
        raise OrdoAnalyticsError("indicator_unknown")
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
    block = (methodology.source_requirements or {}).get("spatial_aggregation")
    try:
        contract = OrdoSpatialAggregationContractV1.model_validate(block)
    except (ValidationError, TypeError) as exc:
        raise OrdoAnalyticsError("spatial_aggregation_not_authorized") from exc
    target = session.scalar(select(OrdoSpatialUnit).where(
        OrdoSpatialUnit.id == target_spatial_unit_id,
        OrdoSpatialUnit.organization_id == organization_id,
        OrdoSpatialUnit.workspace_id == workspace_id,
    ))
    if target is None:
        raise OrdoAnalyticsError("spatial_unit_not_accessible")
    if target.lifecycle_status != "validated":
        raise OrdoAnalyticsError("spatial_unit_not_validated")
    run = session.scalar(select(OrdoAnalyticsRun).where(
        OrdoAnalyticsRun.id == analytics_run_id,
        OrdoAnalyticsRun.organization_id == organization_id,
        OrdoAnalyticsRun.workspace_id == workspace_id,
    ))
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    analytical_input = revalidate_analytics_run(
        session, run=run, organization_id=organization_id, workspace_id=workspace_id
    )
    fields = {str(item.get("field_key")): item for item in analytical_input.field_contract}
    expected_types = {
        "indicator_code": "STRING", "quality_status": "STRING", "spatial_unit_key": "STRING",
        "spatial_unit_type": "STRING", "boundary_version": "STRING", "crs": "STRING",
        "value_numeric": "NUMBER",
    }
    for field_name in contract.required_source_fields:
        field = fields.get(field_name)
        required = contract.aggregation_rule != "count" or field_name != "value_numeric"
        if field is None or field.get("logical_type") != expected_types[field_name] or (required and not bool(field.get("required"))):
            raise OrdoAnalyticsError("spatial_source_contract_invalid")
    candidates = [row for row in analytical_input.records if row.payload.get("indicator_code") == indicator.code]
    if not candidates:
        raise OrdoAnalyticsError("spatial_evidence_required")
    normalized_records = []
    values: list[int | float | None] = []
    for record in candidates:
        payload = record.payload
        if payload.get("quality_status") != "validated":
            raise OrdoAnalyticsError("spatial_record_quality_not_validated")
        identity = {
            "spatial_unit_key": payload.get("spatial_unit_key"),
            "spatial_unit_type": payload.get("spatial_unit_type"),
            "boundary_version": payload.get("boundary_version"),
            "crs": payload.get("crs"),
        }
        expected_identity = {
            "spatial_unit_key": target.spatial_unit_key,
            "spatial_unit_type": target.spatial_unit_type,
            "boundary_version": target.boundary_version,
            "crs": target.crs,
        }
        if identity != expected_identity:
            raise OrdoAnalyticsError("spatial_identity_mismatch")
        value = payload.get("value_numeric")
        values.append(value if isinstance(value, (int, float)) and not isinstance(value, bool) else value)  # type: ignore[arg-type]
        normalized_records.append({
            "identity_fingerprint": record.identity_fingerprint,
            "content_fingerprint": record.content_fingerprint,
            **identity,
            "value_numeric": value,
        })
    calculation = aggregate_numeric_values(values, contract.aggregation_rule)
    normalized_records.sort(key=lambda item: (item["identity_fingerprint"], item["content_fingerprint"]))
    input_sha = canonical_sha256(normalized_records)
    methodology_sha = _methodology_fingerprint(methodology)
    trace = {
        "schema_version": contract.schema_version,
        "aggregation_rule": contract.aggregation_rule,
        "methodology_id": str(methodology.id),
        "methodology_version": methodology.version_no,
        "methodology_fingerprint": methodology_sha,
        "target_spatial_unit_id": str(target.id),
        "target_identity": expected_identity,
        "input_snapshot_sha256": input_sha,
        "input_record_count": calculation.input_record_count,
        "matched_record_count": calculation.matched_record_count,
        "dropped_missing_numeric_count": calculation.dropped_missing_numeric_count,
        "aggregate_numeric_value": calculation.aggregate_numeric_value,
        "weighted": False,
        "spatial_join_performed": False,
        "forecast_performed": False,
        "causal_claim": False,
        "automatic_policy_recommendation": False,
    }
    row = OrdoSpatialAggregationRun(
        organization_id=organization_id, workspace_id=workspace_id, analytics_run_id=run.id,
        indicator_id=indicator.id, methodology_id=methodology.id,
        methodology_version=methodology.version_no, methodology_fingerprint=methodology_sha,
        target_spatial_unit_id=target.id, schema_version=contract.schema_version,
        aggregation_rule=contract.aggregation_rule, boundary_version=target.boundary_version,
        crs=target.crs, spatial_unit_type=target.spatial_unit_type,
        input_snapshot_sha256=input_sha, input_record_count=calculation.input_record_count,
        matched_record_count=calculation.matched_record_count,
        dropped_missing_numeric_count=calculation.dropped_missing_numeric_count,
        aggregate_numeric_value=calculation.aggregate_numeric_value, unit=indicator.unit_hint,
        computation_trace=trace, run_fingerprint=canonical_sha256(trace),
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    return row


def _validated_methodology_and_run(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID, indicator_code: str,
) -> tuple[OrdoIndicatorDefinition, OrdoIndicatorMethodology, OrdoAnalyticsRun, GovernedAnalyticalInput]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    indicator = session.scalar(select(OrdoIndicatorDefinition).where(
        OrdoIndicatorDefinition.code == indicator_code, OrdoIndicatorDefinition.active.is_(True)))
    if indicator is None:
        raise OrdoAnalyticsError("indicator_unknown")
    methodology = session.scalar(select(OrdoIndicatorMethodology).where(
        OrdoIndicatorMethodology.indicator_id == indicator.id,
        OrdoIndicatorMethodology.status == "validated").order_by(OrdoIndicatorMethodology.version_no.desc()))
    if methodology is None:
        raise OrdoAnalyticsError("methodology_not_validated")
    run = session.scalar(select(OrdoAnalyticsRun).where(
        OrdoAnalyticsRun.id == analytics_run_id, OrdoAnalyticsRun.organization_id == organization_id,
        OrdoAnalyticsRun.workspace_id == workspace_id))
    if run is None:
        raise OrdoAnalyticsError("analytics_run_not_accessible")
    value = revalidate_analytics_run(session, run=run, organization_id=organization_id, workspace_id=workspace_id)
    return indicator, methodology, run, value


def create_statistical_model_contract(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID, contract_value: OrdoStatisticalModelContractV1 | dict,
    actor_id: uuid.UUID | None,
) -> OrdoStatisticalModelContract:
    try:
        contract = normalize_statistical_model_contract(contract_value)
    except ValidationError as exc:
        raise OrdoAnalyticsError("statistical_contract_invalid") from exc
    indicator, methodology, run, value = _validated_methodology_and_run(
        session, organization_id=organization_id, workspace_id=workspace_id,
        analytics_run_id=analytics_run_id, indicator_code=contract.target_indicator_code)
    method_sha = _methodology_fingerprint(methodology)
    if (contract.target_methodology_id != methodology.id or
            contract.target_methodology_version != methodology.version_no or
            contract.target_methodology_fingerprint != method_sha):
        raise OrdoAnalyticsError("statistical_contract_methodology_mismatch")
    latest = session.scalar(select(func.max(OrdoStatisticalModelContract.version_no)).where(
        OrdoStatisticalModelContract.workspace_id == workspace_id,
        OrdoStatisticalModelContract.analysis_key == contract.analysis_key))
    row = OrdoStatisticalModelContract(
        organization_id=organization_id, workspace_id=workspace_id, analytics_run_id=run.id,
        target_indicator_id=indicator.id, target_methodology_id=methodology.id,
        target_methodology_version=methodology.version_no, methodology_fingerprint=method_sha,
        input_snapshot_sha256=_input_snapshot_sha256(value), analysis_key=contract.analysis_key,
        version_no=int(latest or 0) + 1, schema_version=contract.schema_version,
        target_semantic=contract.target_semantic, analysis_structure=contract.analysis_structure,
        model_family=contract.model_family, response_family=contract.response_family,
        contract_json=contract.model_dump(mode="json"), contract_fingerprint=statistical_contract_fingerprint(contract),
        created_by_membership_id=actor_id,
    )
    session.add(row); session.flush(); return row


def create_time_series_spec(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID, spec_value: OrdoTimeSeriesSpecV1 | dict,
    actor_id: uuid.UUID | None,
) -> OrdoTimeSeriesSpec:
    try:
        spec = normalize_time_series_spec(spec_value)
    except ValidationError as exc:
        raise OrdoAnalyticsError("time_series_spec_invalid") from exc
    indicator, methodology, run, value = _validated_methodology_and_run(
        session, organization_id=organization_id, workspace_id=workspace_id,
        analytics_run_id=analytics_run_id, indicator_code=spec.target_indicator_code)
    method_sha = _methodology_fingerprint(methodology)
    if (spec.target_methodology_id != methodology.id or spec.target_methodology_version != methodology.version_no
            or spec.target_methodology_fingerprint != method_sha):
        raise OrdoAnalyticsError("time_series_spec_methodology_mismatch")
    latest = session.scalar(select(func.max(OrdoTimeSeriesSpec.version_no)).where(
        OrdoTimeSeriesSpec.workspace_id == workspace_id, OrdoTimeSeriesSpec.series_key == spec.series_key))
    row = OrdoTimeSeriesSpec(
        organization_id=organization_id, workspace_id=workspace_id, analytics_run_id=run.id,
        target_indicator_id=indicator.id, target_methodology_id=methodology.id,
        target_methodology_version=methodology.version_no, methodology_fingerprint=method_sha,
        input_snapshot_sha256=_input_snapshot_sha256(value), series_key=spec.series_key,
        version_no=int(latest or 0) + 1, schema_version=spec.schema_version,
        target_semantic=spec.target_semantic, frequency=spec.frequency, transformation=spec.transformation,
        contract_json=spec.model_dump(mode="json"), contract_fingerprint=time_series_contract_fingerprint(spec),
        forecast_execution=False, automatic_model_selection=False, non_causal=True,
        created_by_membership_id=actor_id,
    )
    session.add(row); session.flush(); return row


def author_time_series_spec(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    analytics_run_id: uuid.UUID, customer_value: dict, actor_id: uuid.UUID | None,
) -> OrdoTimeSeriesSpec:
    """Resolve methodology authority server-side and persist the accepted strict spec."""
    if actor_id is None:
        raise OrdoAnalyticsError("contract_actor_required")
    indicator_code = str(customer_value.get("target_indicator_code") or "")
    _indicator, methodology, _run, _value = _validated_methodology_and_run(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=analytics_run_id,
        indicator_code=indicator_code,
    )
    spec_value = {
        **customer_value,
        "target_methodology_id": methodology.id,
        "target_methodology_version": methodology.version_no,
        "target_methodology_fingerprint": _methodology_fingerprint(methodology),
        "uncertainty_output_required": True,
        "temporal_validation": {
            "backtest_strategy": "rolling_origin_plan_only",
            "initial_train_periods": customer_value["initial_train_periods"],
            "step_size": customer_value["step_size"],
            "horizon": customer_value["horizon"],
            "minimum_origins": customer_value["minimum_origins"],
            "required_metrics": customer_value["required_metrics"],
        },
        "forecast_execution": False,
        "automatic_model_selection": False,
        "non_causal": True,
    }
    for field in (
        "initial_train_periods", "step_size", "minimum_origins", "required_metrics"
    ):
        spec_value.pop(field, None)
    return create_time_series_spec(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        analytics_run_id=analytics_run_id,
        spec_value=spec_value,
        actor_id=actor_id,
    )


def list_time_series_specs(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    limit: int = 100,
) -> list[OrdoTimeSeriesSpec]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(
        select(OrdoTimeSeriesSpec).where(
            OrdoTimeSeriesSpec.organization_id == organization_id,
            OrdoTimeSeriesSpec.workspace_id == workspace_id,
        ).order_by(
            OrdoTimeSeriesSpec.series_key,
            OrdoTimeSeriesSpec.version_no.desc(),
        ).limit(max(1, min(limit, 100)))
    ).all())


def get_time_series_spec(
    session: Session, *, time_series_spec_id: uuid.UUID,
    organization_id: uuid.UUID, workspace_id: uuid.UUID,
) -> OrdoTimeSeriesSpec:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = session.scalar(select(OrdoTimeSeriesSpec).where(
        OrdoTimeSeriesSpec.id == time_series_spec_id,
        OrdoTimeSeriesSpec.organization_id == organization_id,
        OrdoTimeSeriesSpec.workspace_id == workspace_id,
    ))
    if row is None:
        raise OrdoAnalyticsError("time_series_spec_not_found")
    return row


def _transition_specification(
    session: Session, *, row, action: str, actor_id: uuid.UUID | None,
    validation_note: str = "", validation_evidence_reference: str = "", retirement_note: str = "",
):
    if actor_id is None:
        raise OrdoAnalyticsError("contract_actor_required")
    if action == "propose":
        if row.status != "draft":
            raise OrdoAnalyticsError("contract_not_draft")
        row.status = "proposed"; row.proposed_by_membership_id = actor_id; row.proposed_at = _utcnow()
    elif action == "validate":
        if row.status != "proposed":
            raise OrdoAnalyticsError("contract_not_proposed")
        if not validation_note.strip() or not validation_evidence_reference.strip():
            raise OrdoAnalyticsError("contract_validation_evidence_required")
        row.status = "validated"; row.validation_note = validation_note.strip()
        row.validation_evidence_reference = validation_evidence_reference.strip()
        row.approved_by_membership_id = actor_id; row.approved_at = _utcnow()
    elif action == "retire":
        if row.status != "validated":
            raise OrdoAnalyticsError("contract_not_validated")
        if not retirement_note.strip():
            raise OrdoAnalyticsError("retirement_note_required")
        row.status = "retired"; row.retirement_note = retirement_note.strip()
        row.retired_by_membership_id = actor_id; row.retired_at = _utcnow()
    session.flush()
    return row


def _revalidate_specification_binding(session: Session, row) -> None:
    indicator = session.get(OrdoIndicatorDefinition, row.target_indicator_id)
    methodology = session.get(OrdoIndicatorMethodology, row.target_methodology_id)
    run = session.get(OrdoAnalyticsRun, row.analytics_run_id)
    if indicator is None or methodology is None or run is None:
        raise OrdoAnalyticsError("contract_binding_invalid")
    if (
        methodology.indicator_id != indicator.id
        or methodology.status != "validated"
        or methodology.version_no != row.target_methodology_version
        or _methodology_fingerprint(methodology) != row.methodology_fingerprint
    ):
        raise OrdoAnalyticsError("contract_methodology_changed")
    current = session.scalar(
        select(OrdoIndicatorMethodology)
        .where(
            OrdoIndicatorMethodology.indicator_id == indicator.id,
            OrdoIndicatorMethodology.status == "validated",
        )
        .order_by(OrdoIndicatorMethodology.version_no.desc())
    )
    if current is None or current.id != methodology.id:
        raise OrdoAnalyticsError("contract_methodology_changed")
    value = revalidate_analytics_run(
        session, run=run, organization_id=row.organization_id, workspace_id=row.workspace_id
    )
    if _input_snapshot_sha256(value) != row.input_snapshot_sha256:
        raise OrdoAnalyticsError("contract_input_snapshot_changed")
    try:
        if isinstance(row, OrdoStatisticalModelContract):
            contract = normalize_statistical_model_contract(row.contract_json)
            fingerprint = statistical_contract_fingerprint(contract)
        else:
            contract = normalize_time_series_spec(row.contract_json)
            fingerprint = time_series_contract_fingerprint(contract)
    except ValidationError as exc:
        raise OrdoAnalyticsError("contract_content_invalid") from exc
    if row.contract_fingerprint != fingerprint:
        raise OrdoAnalyticsError("contract_fingerprint_mismatch")


def _specification_row(session: Session, model, row_id: uuid.UUID):
    row = session.get(model, row_id)
    if row is None:
        raise OrdoAnalyticsError("contract_not_found")
    return row


def propose_statistical_model_contract(session: Session, *, contract_id: uuid.UUID, actor_id: uuid.UUID | None):
    row = _specification_row(session, OrdoStatisticalModelContract, contract_id)
    _revalidate_specification_binding(session, row)
    return _transition_specification(session, row=row, action="propose", actor_id=actor_id)


def validate_statistical_model_contract(
    session: Session, *, contract_id: uuid.UUID, validation_note: str,
    validation_evidence_reference: str, actor_id: uuid.UUID | None,
):
    row = _specification_row(session, OrdoStatisticalModelContract, contract_id)
    _revalidate_specification_binding(session, row)
    result = _transition_specification(
        session, row=row, action="validate", actor_id=actor_id,
        validation_note=validation_note, validation_evidence_reference=validation_evidence_reference,
    )
    for other in session.scalars(select(OrdoStatisticalModelContract).where(
        OrdoStatisticalModelContract.workspace_id == row.workspace_id,
        OrdoStatisticalModelContract.analysis_key == row.analysis_key,
        OrdoStatisticalModelContract.status == "validated",
        OrdoStatisticalModelContract.id != row.id,
    )).all():
        _transition_specification(
            session, row=other, action="retire", actor_id=actor_id,
            retirement_note=f"Superseded by validated statistical contract version {row.version_no}.",
        )
    return result


def retire_statistical_model_contract(
    session: Session, *, contract_id: uuid.UUID, retirement_note: str, actor_id: uuid.UUID | None,
):
    row = _specification_row(session, OrdoStatisticalModelContract, contract_id)
    return _transition_specification(
        session, row=row, action="retire", actor_id=actor_id, retirement_note=retirement_note
    )


def propose_time_series_spec(session: Session, *, spec_id: uuid.UUID, actor_id: uuid.UUID | None):
    row = _specification_row(session, OrdoTimeSeriesSpec, spec_id)
    _revalidate_specification_binding(session, row)
    return _transition_specification(session, row=row, action="propose", actor_id=actor_id)


def validate_time_series_spec(
    session: Session, *, spec_id: uuid.UUID, validation_note: str,
    validation_evidence_reference: str, actor_id: uuid.UUID | None,
):
    row = _specification_row(session, OrdoTimeSeriesSpec, spec_id)
    _revalidate_specification_binding(session, row)
    result = _transition_specification(
        session, row=row, action="validate", actor_id=actor_id,
        validation_note=validation_note, validation_evidence_reference=validation_evidence_reference,
    )
    for other in session.scalars(select(OrdoTimeSeriesSpec).where(
        OrdoTimeSeriesSpec.workspace_id == row.workspace_id,
        OrdoTimeSeriesSpec.series_key == row.series_key,
        OrdoTimeSeriesSpec.status == "validated",
        OrdoTimeSeriesSpec.id != row.id,
    )).all():
        _transition_specification(
            session, row=other, action="retire", actor_id=actor_id,
            retirement_note=f"Superseded by validated time-series specification version {row.version_no}.",
        )
    return result


def retire_time_series_spec(
    session: Session, *, spec_id: uuid.UUID, retirement_note: str, actor_id: uuid.UUID | None,
):
    row = _specification_row(session, OrdoTimeSeriesSpec, spec_id)
    return _transition_specification(
        session, row=row, action="retire", actor_id=actor_id, retirement_note=retirement_note
    )


def _parse_series_date(value: object) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ForecastNotEstimated("INVALID_SERIES_VALUE")
    text = value.strip()
    try:
        if "T" in text or " " in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ForecastNotEstimated("INVALID_SERIES_VALUE") from exc


def _advance_period(value: date, frequency: str) -> date:
    if frequency == "daily":
        return value + timedelta(days=1)
    if frequency == "weekly":
        return value + timedelta(days=7)
    months = {"monthly": 1, "quarterly": 3, "annual": 12}.get(frequency)
    if months is None:
        raise ValueError("unsupported_time_series_frequency")
    month_index = (value.month - 1) + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    current_last_day = calendar.monthrange(value.year, value.month)[1]
    day = calendar.monthrange(year, month)[1] if value.day == current_last_day else min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _validate_target_value(value: object, target_semantic: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ForecastNotEstimated("INVALID_SERIES_VALUE")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ForecastNotEstimated("INVALID_SERIES_VALUE")
    if target_semantic == "count" and (numeric < 0 or not numeric.is_integer()):
        raise ForecastNotEstimated("INVALID_SERIES_VALUE")
    if target_semantic == "proportion_rate" and not 0 <= numeric <= 1:
        raise ForecastNotEstimated("INVALID_SERIES_VALUE")
    return numeric


def _forecast_binding(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    time_series_spec_id: uuid.UUID,
) -> tuple[OrdoTimeSeriesSpec, OrdoTimeSeriesSpecV1, OrdoAnalyticsRun, GovernedAnalyticalInput]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = session.scalar(select(OrdoTimeSeriesSpec).where(
        OrdoTimeSeriesSpec.id == time_series_spec_id,
        OrdoTimeSeriesSpec.organization_id == organization_id,
        OrdoTimeSeriesSpec.workspace_id == workspace_id,
    ))
    if row is None:
        raise OrdoAnalyticsError("time_series_spec_not_found")
    if row.status != "validated":
        raise OrdoAnalyticsError("time_series_spec_not_validated")
    try:
        spec = normalize_time_series_spec(row.contract_json)
    except ValidationError as exc:
        raise OrdoAnalyticsError("time_series_spec_binding_invalid") from exc
    if time_series_contract_fingerprint(spec) != row.contract_fingerprint:
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    if (
        row.schema_version != spec.schema_version
        or row.series_key != spec.series_key
        or row.target_semantic != spec.target_semantic
        or row.frequency != spec.frequency
        or row.transformation != spec.transformation
        or row.forecast_execution
        or row.automatic_model_selection
        or not row.non_causal
    ):
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    indicator = session.get(OrdoIndicatorDefinition, row.target_indicator_id)
    methodology = session.get(OrdoIndicatorMethodology, row.target_methodology_id)
    run = session.get(OrdoAnalyticsRun, row.analytics_run_id)
    if indicator is None or methodology is None or run is None:
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    current = session.scalar(select(OrdoIndicatorMethodology).where(
        OrdoIndicatorMethodology.indicator_id == row.target_indicator_id,
        OrdoIndicatorMethodology.status == "validated",
    ).order_by(OrdoIndicatorMethodology.version_no.desc()))
    if (
        methodology.indicator_id != indicator.id
        or methodology.status != "validated"
        or methodology.version_no != row.target_methodology_version
        or _methodology_fingerprint(methodology) != row.methodology_fingerprint
        or current is None
        or current.id != methodology.id
        or spec.target_methodology_id != methodology.id
        or spec.target_methodology_version != methodology.version_no
        or spec.target_methodology_fingerprint != row.methodology_fingerprint
        or spec.target_indicator_code != indicator.code
    ):
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    try:
        governed = revalidate_analytics_run(
            session, run=run, organization_id=organization_id, workspace_id=workspace_id
        )
    except OrdoAnalyticsError as exc:
        raise OrdoAnalyticsError("time_series_spec_binding_invalid") from exc
    if _input_snapshot_sha256(governed) != row.input_snapshot_sha256:
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    return row, spec, run, governed


def list_time_series_identities(
    session: Session, *, time_series_spec_id: uuid.UUID,
    organization_id: uuid.UUID, workspace_id: uuid.UUID,
) -> list[dict[str, object]]:
    """Return deterministic unique series keys from the exact executable binding."""
    _row, spec, _run, governed = _forecast_binding(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        time_series_spec_id=time_series_spec_id,
    )
    fields = {str(item.get("field_key")) for item in governed.field_contract}
    required = {
        "indicator_code", "quality_status", "value_numeric",
        spec.time_index_field, *spec.series_key_fields,
    }
    if not required.issubset(fields):
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    identities: dict[str, dict[str, object]] = {}
    for record in governed.records:
        payload = record.payload
        if payload.get("indicator_code") != spec.target_indicator_code:
            continue
        if payload.get("quality_status") != "validated":
            continue
        try:
            observed_at = _parse_series_date(payload.get(spec.time_index_field))
        except ForecastNotEstimated:
            continue
        if not (spec.observation_window_start <= observed_at <= spec.observation_window_end):
            continue
        if observed_at > spec.observation_as_of:
            continue
        try:
            _validate_target_value(payload.get("value_numeric"), spec.target_semantic)
        except ForecastNotEstimated:
            continue
        identity: dict[str, object] = {}
        eligible = True
        for key in spec.series_key_fields:
            value = payload.get(key)
            if (
                key not in payload
                or not isinstance(value, (str, int, float, bool, type(None)))
                or (isinstance(value, float) and not math.isfinite(value))
            ):
                eligible = False
                break
            identity[key] = value
        if not eligible:
            continue
        canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        identities[canonical] = identity
    return [identities[key] for key in sorted(identities)]


def _extract_forecast_series(
    governed: GovernedAnalyticalInput, spec: OrdoTimeSeriesSpecV1,
    series_identity: dict[str, object],
) -> tuple[list[date], list[float]]:
    if set(series_identity) != set(spec.series_key_fields):
        raise OrdoAnalyticsError("forecast_series_identity_invalid")
    fields = {str(item.get("field_key")) for item in governed.field_contract}
    required = {"indicator_code", "quality_status", "value_numeric", spec.time_index_field, *spec.series_key_fields}
    if not required.issubset(fields):
        raise OrdoAnalyticsError("time_series_spec_binding_invalid")
    selected: list[tuple[date, float]] = []
    for record in governed.records:
        payload = record.payload
        if payload.get("indicator_code") != spec.target_indicator_code or payload.get("quality_status") != "validated":
            continue
        if any(
            key not in payload
            or (isinstance(payload[key], bool) != isinstance(expected, bool))
            or payload[key] != expected
            for key, expected in series_identity.items()
        ):
            continue
        observed_at = _parse_series_date(payload.get(spec.time_index_field))
        if not (spec.observation_window_start <= observed_at <= spec.observation_window_end):
            continue
        if observed_at > spec.observation_as_of:
            continue
        selected.append((observed_at, _validate_target_value(payload.get("value_numeric"), spec.target_semantic)))
    if not selected:
        raise ForecastNotEstimated("SERIES_EVIDENCE_NOT_FOUND")
    selected.sort(key=lambda item: item[0])
    dates = [item[0] for item in selected]
    if len(dates) != len(set(dates)):
        raise ForecastNotEstimated("DUPLICATE_TIME_INDEX")
    values = [item[1] for item in selected]
    if dates[0] != spec.observation_window_start or dates[-1] != spec.observation_window_end:
        raise ForecastNotEstimated("IRREGULAR_OR_MISSING_PERIODS")
    for previous, current in zip(dates, dates[1:]):
        if _advance_period(previous, spec.frequency) != current:
            raise ForecastNotEstimated("IRREGULAR_OR_MISSING_PERIODS")
    return dates, values


def _metric_payload(
    backtests: list[dict[str, object]], *, seasonality_period: int | None,
    required_metrics: set[str], interval_level: float, target_semantic: str,
) -> tuple[dict[str, float], dict[str, dict[str, object]], dict[str, object]]:
    all_actual: list[float] = []
    all_forecast: list[float] = []
    origin_mase: list[float] = []
    residual_history: dict[int, list[float]] = {}
    eligible_intervals = 0
    covered_intervals = 0
    interval_widths: list[float] = []
    for origin in backtests:
        training = [float(value) for value in origin.pop("training")]
        actual = [float(value) for value in origin["actual"]]
        forecasts = [float(value) for value in origin["forecast"]]
        all_actual.extend(actual)
        all_forecast.extend(forecasts)
        scale_lag = seasonality_period or 1
        origin_mase_value = mase(actual, forecasts, training, scale_lag)
        origin_metrics: dict[str, float | None] = aggregate_point_metrics(actual, forecasts)
        origin_metrics["MASE"] = origin_mase_value
        origin["metrics"] = origin_metrics
        if origin_mase_value is not None:
            origin_mase.append(origin_mase_value)
        interval_points = []
        for index, (observed, predicted, residual) in enumerate(
            zip(actual, forecasts, origin["residuals"], strict=True), start=1
        ):
            prior = residual_history.setdefault(index, [])
            interval_point: dict[str, object] = {"horizon_step": index, "available": False, "prior_residual_count": len(prior)}
            if len(prior) >= 3:
                lower, upper = empirical_residual_interval(predicted, prior, interval_level)
                lower, upper = clip_interval(lower, upper, target_semantic)
                interval_point.update({"available": True, "lower": lower, "upper": upper, "covered": lower <= observed <= upper})
                eligible_intervals += 1
                covered_intervals += int(lower <= observed <= upper)
                interval_widths.append(upper - lower)
            interval_points.append(interval_point)
            prior.append(float(residual))
        origin["interval_points"] = interval_points
    metrics = aggregate_point_metrics(all_actual, all_forecast)
    availability: dict[str, dict[str, object]] = {
        name: {"available": True, "denominator_count": len(all_actual)} for name in ("MAE", "RMSE", "bias", "sMAPE")
    }
    if len(origin_mase) == len(backtests):
        metrics["MASE"] = sum(origin_mase) / len(origin_mase)
        availability["MASE"] = {"available": True, "denominator_count": len(origin_mase)}
    else:
        availability["MASE"] = {"available": False, "denominator_count": len(origin_mase)}
    baseline_predictions: list[float] = []
    baseline_available = seasonality_period is not None
    # Each origin's seasonal baseline is retained during execution when it is eligible.
    for origin in backtests:
        baseline = origin.get("seasonal_baseline_forecast")
        if baseline is None:
            baseline_available = False
            break
        baseline_predictions.extend(float(value) for value in baseline)
    if baseline_available and baseline_predictions:
        baseline_mae = mae(all_actual, baseline_predictions)
        if baseline_mae > 0 and math.isfinite(baseline_mae):
            metrics["seasonal_baseline_comparison"] = metrics["MAE"] / baseline_mae
            availability["seasonal_baseline_comparison"] = {"available": True, "denominator_count": len(all_actual)}
        else:
            availability["seasonal_baseline_comparison"] = {"available": False, "denominator_count": len(all_actual)}
    else:
        availability["seasonal_baseline_comparison"] = {"available": False, "denominator_count": 0}
    if eligible_intervals:
        metrics["interval_coverage"] = covered_intervals / eligible_intervals
        metrics["interval_width_sharpness"] = sum(interval_widths) / eligible_intervals
    availability["interval_coverage"] = {"available": bool(eligible_intervals), "denominator_count": eligible_intervals}
    availability["interval_width_sharpness"] = {"available": bool(eligible_intervals), "denominator_count": eligible_intervals}
    if any(not availability.get(metric, {"available": False})["available"] for metric in required_metrics):
        raise ForecastNotEstimated("REQUIRED_BACKTEST_METRIC_UNAVAILABLE")
    return metrics, availability, {
        "backtest_point_count": len(all_actual),
        "rolling_origin_count": len(backtests),
        "eligible_interval_point_count": eligible_intervals,
        "covered_interval_point_count": covered_intervals,
    }


def _forecast_result_data(
    dates: list[date], values: list[float], spec: OrdoTimeSeriesSpecV1,
    requested_family: str, interval_level: float,
) -> dict[str, object]:
    backtests = run_rolling_origin(
        values, family=requested_family,
        initial_train_periods=spec.temporal_validation.initial_train_periods,
        step_size=spec.temporal_validation.step_size, horizon=spec.horizon,
        minimum_origins=spec.temporal_validation.minimum_origins,
        seasonality_period=spec.seasonality_period,
    )
    for origin in backtests:
        training = [float(value) for value in origin["training"]]
        if spec.seasonality_period is not None and len(training) >= spec.seasonality_period:
            origin["seasonal_baseline_forecast"] = forecast_family(
                training, spec.horizon, "seasonal_naive", spec.seasonality_period
            )
    metrics, availability, diagnostics = _metric_payload(
        backtests, seasonality_period=spec.seasonality_period,
        required_metrics=set(spec.temporal_validation.required_metrics),
        interval_level=interval_level, target_semantic=spec.target_semantic,
    )
    residuals_by_horizon: dict[int, list[float]] = {step: [] for step in range(1, spec.horizon + 1)}
    for origin in backtests:
        for step, residual in enumerate(origin["residuals"], start=1):
            residuals_by_horizon[step].append(float(residual))
    if any(len(residuals) < 3 for residuals in residuals_by_horizon.values()):
        raise ForecastNotEstimated("INSUFFICIENT_INTERVAL_CALIBRATION")
    point_forecast = forecast_family(values, spec.horizon, requested_family, spec.seasonality_period)
    forecast_points = []
    forecast_date = dates[-1]
    for step, point in enumerate(point_forecast, start=1):
        forecast_date = _advance_period(forecast_date, spec.frequency)
        lower, upper = empirical_residual_interval(point, residuals_by_horizon[step], interval_level)
        lower, upper = clip_interval(lower, upper, spec.target_semantic)
        forecast_points.append({
            "horizon_step": step, "time": forecast_date.isoformat(), "point": point,
            "lower": lower, "upper": upper, "calibration_residual_count": len(residuals_by_horizon[step]),
        })
    diagnostics["calibration_residual_count_by_horizon"] = {
        str(step): len(residuals) for step, residuals in residuals_by_horizon.items()
    }
    return {
        "executed_family": requested_family,
        "backtest_records": backtests,
        "aggregate_backtest_metrics": metrics,
        "metric_availability": availability,
        "diagnostics": diagnostics,
        "warnings": [],
        "forecast_points": forecast_points,
    }


def _persist_forecast_outcome(
    session: Session, *, row: OrdoTimeSeriesSpec, spec: OrdoTimeSeriesSpecV1,
    series_identity: dict[str, object], requested_family: str, interval_level: float,
    actor_id: uuid.UUID | None, result_status: str, reason_code: str,
    dates: list[date] | None = None, result_data: dict[str, object] | None = None,
) -> OrdoForecastRun:
    dates = dates or []
    result_data = result_data or {
        "executed_family": None, "backtest_records": [], "aggregate_backtest_metrics": {},
        "metric_availability": {}, "diagnostics": {}, "warnings": [], "forecast_points": [],
    }
    request_payload = {
        "organization_id": str(row.organization_id), "workspace_id": str(row.workspace_id),
        "time_series_spec_id": str(row.id), "time_series_spec_fingerprint": row.contract_fingerprint,
        "requested_family": requested_family, "series_identity": series_identity,
        "interval_level": interval_level,
    }
    request_fingerprint = _canonical_sha256(request_payload)
    result_payload = {
        **request_payload, "schema_version": "ORDO-FORECAST-RUN-v1", "result_status": result_status,
        "reason_code": reason_code, "engine_key": ENGINE_KEY, "engine_version": ENGINE_VERSION,
        "interval_method": INTERVAL_METHOD, "analytics_run_id": str(row.analytics_run_id),
        "time_series_spec_version": row.version_no, "target_indicator_id": str(row.target_indicator_id),
        "target_methodology_id": str(row.target_methodology_id),
        "target_methodology_version": row.target_methodology_version,
        "methodology_fingerprint": row.methodology_fingerprint,
        "input_snapshot_sha256": row.input_snapshot_sha256, **result_data,
    }
    forecast = OrdoForecastRun(
        organization_id=row.organization_id, workspace_id=row.workspace_id,
        analytics_run_id=row.analytics_run_id, time_series_spec_id=row.id,
        time_series_spec_version=row.version_no, time_series_spec_fingerprint=row.contract_fingerprint,
        target_indicator_id=row.target_indicator_id, target_methodology_id=row.target_methodology_id,
        target_methodology_version=row.target_methodology_version,
        methodology_fingerprint=row.methodology_fingerprint, input_snapshot_sha256=row.input_snapshot_sha256,
        schema_version="ORDO-FORECAST-RUN-v1", series_identity=series_identity,
        request_fingerprint=request_fingerprint, requested_family=requested_family,
        executed_family=result_data["executed_family"], engine_key=ENGINE_KEY, engine_version=ENGINE_VERSION,
        interval_method=INTERVAL_METHOD, interval_level=interval_level,
        result_status=result_status, reason_code=reason_code,
        observation_window={"start": spec.observation_window_start.isoformat(), "end": spec.observation_window_end.isoformat(), "as_of": spec.observation_as_of.isoformat()},
        training_window={"start": dates[0].isoformat() if dates else None, "end": dates[-1].isoformat() if dates else None, "period_count": len(dates)},
        horizon=spec.horizon, rolling_origin_plan=spec.temporal_validation.model_dump(mode="json"),
        backtest_records=result_data["backtest_records"],
        aggregate_backtest_metrics=result_data["aggregate_backtest_metrics"],
        metric_availability=result_data["metric_availability"], diagnostics=result_data["diagnostics"],
        warnings=result_data["warnings"], forecast_points=result_data["forecast_points"],
        result_fingerprint=_canonical_sha256(result_payload), non_causal=True,
        automatic_model_selection=False, automatic_policy_recommendation=False,
        created_by_membership_id=actor_id,
    )
    session.add(forecast)
    session.flush()
    return forecast


def execute_forecast(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
    time_series_spec_id: uuid.UUID, requested_family: str,
    series_identity: dict[str, object], interval_level: float, actor_id: uuid.UUID | None,
) -> OrdoForecastRun:
    if actor_id is None:
        raise OrdoAnalyticsError("forecast_actor_required")
    if interval_level not in {0.80, 0.90, 0.95}:
        raise OrdoAnalyticsError("forecast_interval_level_invalid")
    if any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(value, (str, int, float, bool, type(None)))
        or (isinstance(value, float) and not math.isfinite(value))
        for key, value in series_identity.items()
    ):
        raise OrdoAnalyticsError("forecast_series_identity_invalid")
    row, spec, _run, governed = _forecast_binding(
        session, organization_id=organization_id, workspace_id=workspace_id,
        time_series_spec_id=time_series_spec_id,
    )
    if requested_family not in spec.candidate_families:
        raise OrdoAnalyticsError("forecast_family_not_in_validated_spec")
    if set(series_identity) != set(spec.series_key_fields):
        raise OrdoAnalyticsError("forecast_series_identity_invalid")
    if requested_family not in {"naive", "seasonal_naive"}:
        return _persist_forecast_outcome(
            session, row=row, spec=spec, series_identity=series_identity,
            requested_family=requested_family, interval_level=interval_level, actor_id=actor_id,
            result_status="NOT_ESTIMATED", reason_code="EXECUTABLE_FAMILY_NOT_DEFINED_24C",
        )
    if spec.transformation != "none":
        return _persist_forecast_outcome(
            session, row=row, spec=spec, series_identity=series_identity,
            requested_family=requested_family, interval_level=interval_level, actor_id=actor_id,
            result_status="NOT_ESTIMATED", reason_code="TRANSFORMATION_EXECUTION_NOT_DEFINED_24C",
        )
    dates: list[date] = []
    try:
        dates, values = _extract_forecast_series(governed, spec, series_identity)
        if len(values) < spec.minimum_history_periods:
            raise ForecastNotEstimated("INSUFFICIENT_HISTORY")
        result_data = _forecast_result_data(dates, values, spec, requested_family, interval_level)
    except ForecastNotEstimated as exc:
        return _persist_forecast_outcome(
            session, row=row, spec=spec, series_identity=series_identity,
            requested_family=requested_family, interval_level=interval_level, actor_id=actor_id,
            result_status="NOT_ESTIMATED", reason_code=exc.reason_code, dates=dates,
        )
    return _persist_forecast_outcome(
        session, row=row, spec=spec, series_identity=series_identity,
        requested_family=requested_family, interval_level=interval_level, actor_id=actor_id,
        result_status="ESTIMATED", reason_code="", dates=dates, result_data=result_data,
    )


def list_forecast_runs(
    session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, limit: int = 50,
) -> list[OrdoForecastRun]:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    return list(session.scalars(select(OrdoForecastRun).where(
        OrdoForecastRun.organization_id == organization_id,
        OrdoForecastRun.workspace_id == workspace_id,
    ).order_by(OrdoForecastRun.created_at.desc()).limit(max(1, min(limit, 100)))).all())


def get_forecast_run(
    session: Session, *, forecast_run_id: uuid.UUID,
    organization_id: uuid.UUID, workspace_id: uuid.UUID,
) -> OrdoForecastRun:
    _validate_scope(session, organization_id=organization_id, workspace_id=workspace_id)
    row = session.scalar(select(OrdoForecastRun).where(
        OrdoForecastRun.id == forecast_run_id,
        OrdoForecastRun.organization_id == organization_id,
        OrdoForecastRun.workspace_id == workspace_id,
    ))
    if row is None:
        raise OrdoAnalyticsError("forecast_run_not_found")
    return row


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


def _canonical_sha256(value) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _scenario_input_reference_identities(run: OrdoAnalyticsRun) -> list[dict[str, str]]:
    snapshot = run.snapshot or {}
    analytical_source = snapshot.get("analytical_source") or {}
    identities: list[dict[str, str]] = []
    artifact_id = analytical_source.get("artifact_id")
    if artifact_id:
        identities.append({
            "kind": str(analytical_source.get("artifact_type") or "analytical_artifact"),
            "id": str(artifact_id),
        })
    dataset_contract_version_id = analytical_source.get("dataset_contract_version_id")
    if dataset_contract_version_id:
        identities.append({"kind": "dataset_contract_version", "id": str(dataset_contract_version_id)})
    resolved_snapshot_id = analytical_source.get("resolved_snapshot_id")
    if resolved_snapshot_id:
        identities.append({"kind": "resolved_snapshot", "id": str(resolved_snapshot_id)})
    if getattr(run, "analytical_artifact_fingerprint", ""):
        identities.append({"kind": "analytical_artifact_fingerprint", "id": run.analytical_artifact_fingerprint})
    if getattr(run, "dataset_contract_fingerprint", ""):
        identities.append({"kind": "dataset_contract_fingerprint", "id": run.dataset_contract_fingerprint})
    return identities


def _scenario_assessment_payload(
    *,
    scenario: OrdoScenario,
    goal: OrdoDevelopmentGoal,
    run: OrdoAnalyticsRun,
) -> dict:
    snapshot = run.snapshot or {}
    input_snapshot_sha256 = _canonical_sha256(snapshot)
    limitations = [
        "No causal, predictive, financial, visitor-volume, employment, sustainability, inclusion, or quality-of-life effect is calculated by this assessment.",
        "Scenario assumptions and measures are user-authored planning inputs, not verified outcomes.",
        "A human expert must interpret the evidence before a scenario can inform a development decision.",
    ]
    return {
        "assessment_mode": "evidence_readiness_only",
        "forecast_performed": False,
        "impact": "NOT_ESTIMATED",
        "impact_estimation_reason_code": "NO_APPROVED_RESPONSE_MODEL",
        "scenario_contract": {
            "scenario_contract_version": "ORDO-SCENARIO-CONTRACT-v1",
            "methodology_key": "ordo_evidence_readiness_v1",
            "methodology_version": "1",
            "input_reference_identities": _scenario_input_reference_identities(run),
            "input_snapshot_sha256": input_snapshot_sha256,
            "limitations": limitations,
            "uncertainty_semantics": "not_applicable_scenario_not_forecast",
            "human_review_state": "pending",
            "scenario_is_forecast": False,
            "causal_claim": False,
            "automatic_policy_recommendation": False,
        },
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
        "limitations": limitations,
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
        scenario_contract_version=assessment["scenario_contract"]["scenario_contract_version"],
        methodology_key=assessment["scenario_contract"]["methodology_key"],
        methodology_version=assessment["scenario_contract"]["methodology_version"],
        input_reference_identities=assessment["scenario_contract"]["input_reference_identities"],
        input_snapshot_sha256=assessment["scenario_contract"]["input_snapshot_sha256"],
        limitations=assessment["limitations"],
        uncertainty_semantics=assessment["scenario_contract"]["uncertainty_semantics"],
        human_review_state="pending",
        forecast_performed=False,
        impact_estimation_status="NOT_ESTIMATED",
        impact_estimation_reason_code="NO_APPROVED_RESPONSE_MODEL",
        impact_estimate_numeric=None,
        impact_estimate_unit="",
        impact_model_reference="",
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
    row.human_review_state = "reviewed" if decision == "reviewed" else "rejected"
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
