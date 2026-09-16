from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.domains.ordo.analytics_schemas import (
    AnalyticsRunCreateRequest,
    DevelopmentGoalCreateRequest,
    ForecastExecutionRequest,
    IndicatorComputeRequest,
    MethodologyCreateRequest,
    MethodologyProposeRequest,
    MethodologyRetireRequest,
    MethodologyValidateRequest,
    ScenarioAssessmentCreateRequest,
    ScenarioAssessmentReviewRequest,
    ScenarioCreateRequest,
    ScenarioStatusRequest,
    SynthesisCreateRequest,
    SynthesisReviewRequest,
)
from src.domains.ordo.analytics_service import (
    OrdoAnalyticsError,
    build_destination_snapshot,
    compute_indicator,
    create_analytics_run,
    create_goal,
    create_methodology,
    create_scenario,
    create_scenario_assessment,
    create_synthesis,
    execute_forecast,
    get_forecast_run,
    list_analytics_runs,
    list_goals,
    list_forecast_runs,
    list_methodologies,
    list_scenario_assessments,
    list_scenarios,
    list_syntheses,
    propose_methodology,
    retire_methodology,
    review_scenario_assessment,
    review_synthesis,
    set_scenario_status,
    validate_methodology,
)
from src.platform.access.service import has_permission
from src.platform.ai.queue import AIQueueError, dispatch_ai_job
from src.platform.ai.service import AIServiceError, actor_membership_id, job_response
from src.platform.app_context.service import AppContextError, resolve_selection


router = APIRouter(prefix="/api/v1/ordo/analytics", tags=["ordo-analytics"])


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    permission_code: str,
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code="ORDO",
            workspace_id=workspace_id,
        )
    except AppContextError:
        raise HTTPException(status_code=403, detail="ordo_analytics_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, "ORDO"):
        raise HTTPException(status_code=403, detail="ordo_analytics_permission_denied")


def _error(exc: Exception) -> HTTPException:
    code = str(exc)
    if code.endswith("not_accessible") or code in {"methodology_not_found", "time_series_spec_not_found", "forecast_run_not_found"}:
        return HTTPException(status_code=404, detail=code)
    if code in {
        "methodology_not_validated",
        "methodology_not_draft",
        "methodology_not_proposed",
        "validated_observation_required",
        "synthesis_not_reviewable",
        "scenario_required",
        "scenario_not_allowed_for_monitoring_synthesis",
    }:
        return HTTPException(status_code=409, detail=code)
    if code in {"provider_unavailable", "timeout", "provider_http_error", "external_provider_not_configured"}:
        return HTTPException(status_code=503, detail=code)
    return HTTPException(status_code=400, detail=code)


def _run_dict(row):
    return {
        "id": str(row.id),
        "monitoring_cycle_id": str(row.monitoring_cycle_id) if row.monitoring_cycle_id else None,
        "status": row.status,
        "snapshot": row.snapshot,
        "analytical_artifact_type": row.analytical_artifact_type,
        "analytical_snapshot_id": str(row.analytical_snapshot_id) if row.analytical_snapshot_id else None,
        "analytical_feature_version_id": str(row.analytical_feature_version_id) if row.analytical_feature_version_id else None,
        "analytical_artifact_fingerprint": row.analytical_artifact_fingerprint,
        "dataset_contract_version_id": str(row.dataset_contract_version_id) if row.dataset_contract_version_id else None,
        "dataset_contract_fingerprint": row.dataset_contract_fingerprint,
        "analytical_quality_state": row.analytical_quality_state,
        "evidence_quality_score": row.evidence_quality_score,
        "validated_observation_ratio": row.validated_observation_ratio,
        "provenance_coverage": row.provenance_coverage,
        "indicator_coverage": row.indicator_coverage,
        "dimension_coverage": row.dimension_coverage,
        "pillar_coverage": row.pillar_coverage,
        "created_at": row.created_at,
    }


def _forecast_dict(row):
    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id),
        "workspace_id": str(row.workspace_id),
        "analytics_run_id": str(row.analytics_run_id),
        "time_series_spec_id": str(row.time_series_spec_id),
        "time_series_spec_version": row.time_series_spec_version,
        "time_series_spec_fingerprint": row.time_series_spec_fingerprint,
        "target_indicator_id": str(row.target_indicator_id),
        "target_methodology_id": str(row.target_methodology_id),
        "target_methodology_version": row.target_methodology_version,
        "methodology_fingerprint": row.methodology_fingerprint,
        "input_snapshot_sha256": row.input_snapshot_sha256,
        "schema_version": row.schema_version,
        "series_identity": row.series_identity,
        "request_fingerprint": row.request_fingerprint,
        "requested_family": row.requested_family,
        "executed_family": row.executed_family,
        "engine_key": row.engine_key,
        "engine_version": row.engine_version,
        "interval_method": row.interval_method,
        "interval_level": row.interval_level,
        "result_status": row.result_status,
        "reason_code": row.reason_code,
        "observation_window": row.observation_window,
        "training_window": row.training_window,
        "horizon": row.horizon,
        "rolling_origin_plan": row.rolling_origin_plan,
        "backtest_records": row.backtest_records,
        "aggregate_backtest_metrics": row.aggregate_backtest_metrics,
        "metric_availability": row.metric_availability,
        "diagnostics": row.diagnostics,
        "warnings": row.warnings,
        "forecast_points": row.forecast_points,
        "result_fingerprint": row.result_fingerprint,
        "non_causal": row.non_causal,
        "automatic_model_selection": row.automatic_model_selection,
        "automatic_policy_recommendation": row.automatic_policy_recommendation,
        "created_by_membership_id": str(row.created_by_membership_id) if row.created_by_membership_id else None,
        "created_at": row.created_at,
    }


@router.get("/summary")
def get_summary(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    analytical_artifact_type: Literal["snapshot", "feature_version"] = Query(...),
    analytical_artifact_id: uuid.UUID = Query(...),
    monitoring_cycle_id: uuid.UUID | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    try:
        return build_destination_snapshot(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            analytical_artifact_type=analytical_artifact_type,
            analytical_artifact_id=analytical_artifact_id,
            monitoring_cycle_id=monitoring_cycle_id,
        )
    except (OrdoAnalyticsError, ValueError) as exc:
        raise _error(exc) from None


@router.get("/runs")
def get_runs(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [_run_dict(row) for row in list_analytics_runs(db, organization_id=organization_id, workspace_id=workspace_id)]


@router.post("/forecasts", status_code=status.HTTP_201_CREATED)
def post_forecast(
    payload: ForecastExecutionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=payload.organization_id,
        workspace_id=payload.workspace_id, permission_code="analysis.run",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = execute_forecast(db, actor_id=actor_id, **payload.model_dump())
        db.commit()
        db.refresh(row)
        return _forecast_dict(row)
    except OrdoAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/forecasts")
def get_forecasts(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=organization_id,
        workspace_id=workspace_id, permission_code="analysis.read",
    )
    return [_forecast_dict(row) for row in list_forecast_runs(
        db, organization_id=organization_id, workspace_id=workspace_id
    )]


@router.get("/forecasts/{forecast_run_id}")
def get_forecast(
    forecast_run_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=organization_id,
        workspace_id=workspace_id, permission_code="analysis.read",
    )
    try:
        return _forecast_dict(get_forecast_run(
            db, forecast_run_id=forecast_run_id,
            organization_id=organization_id, workspace_id=workspace_id,
        ))
    except OrdoAnalyticsError as exc:
        raise _error(exc) from None


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def post_run(
    payload: AnalyticsRunCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_analytics_run(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            analytical_artifact_type=payload.analytical_artifact_type,
            analytical_artifact_id=payload.analytical_artifact_id,
            monitoring_cycle_id=payload.monitoring_cycle_id,
            actor_id=actor_id,
        )
        db.commit(); db.refresh(row)
        return _run_dict(row)
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/methodologies")
def get_methodologies(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [
        {
            "id": str(method.id),
            "indicator_code": indicator.code,
            "indicator_name_sr": indicator.name_sr,
            "version_no": method.version_no,
            "status": method.status,
            "computation_type": method.computation_type,
            "methodology_note": method.methodology_note,
            "proposed_at": method.proposed_at,
            "validation_note": method.validation_note,
            "approved_at": method.approved_at,
            "retired_at": method.retired_at,
            "retirement_note": method.retirement_note,
        }
        for method, indicator in list_methodologies(db)
    ]


@router.post("/methodologies", status_code=status.HTTP_201_CREATED)
def post_methodology(
    payload: MethodologyCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_methodology(
            db,
            indicator_code=payload.indicator_code,
            computation_type=payload.computation_type,
            methodology_note=payload.methodology_note,
            source_requirements=payload.source_requirements,
            actor_id=actor_id,
        )
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "version_no": row.version_no, "status": row.status, "computation_type": row.computation_type}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/validate")
def post_validate_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyValidateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = validate_methodology(db, methodology_id=methodology_id, validation_note=payload.validation_note, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status, "approved_at": row.approved_at}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/propose")
def post_propose_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyProposeRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = propose_methodology(db, methodology_id=methodology_id, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status, "proposed_at": row.proposed_at}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/retire")
def post_retire_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyRetireRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = retire_methodology(
            db, methodology_id=methodology_id, retirement_note=payload.retirement_note, actor_id=actor_id
        )
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status, "retired_at": row.retired_at}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/compute", status_code=status.HTTP_201_CREATED)
def post_compute(
    payload: IndicatorComputeRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = compute_indicator(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            indicator_code=payload.indicator_code,
            monitoring_cycle_id=payload.monitoring_cycle_id,
            analytics_run_id=payload.analytics_run_id,
            actor_id=actor_id,
        )
        db.commit(); db.refresh(row)
        return {
            "id": str(row.id),
            "value_numeric": row.value_numeric,
            "value_text": row.value_text,
            "unit": row.unit,
            "quality_score": row.quality_score,
            "status": row.status,
            "source_observation_ids": row.source_observation_ids,
            "computation_trace": row.computation_trace,
        }
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/goals")
def get_goals(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [
        {
            "id": str(row.id), "code": row.code, "title": row.title, "description": row.description,
            "focus_area": row.focus_area, "target_horizon": row.target_horizon, "status": row.status,
        }
        for row in list_goals(db, organization_id=organization_id, workspace_id=workspace_id)
    ]


@router.post("/goals", status_code=status.HTTP_201_CREATED)
def post_goal(
    payload: DevelopmentGoalCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_goal(db, actor_id=actor_id, **payload.model_dump())
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "code": row.code, "title": row.title, "focus_area": row.focus_area, "status": row.status}
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/scenarios")
def get_scenarios(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [
        {
            "id": str(row.id), "goal_id": str(goal.id), "goal_title": goal.title, "name": row.name,
            "description": row.description, "assumptions": row.assumptions, "measures": row.measures, "status": row.status,
        }
        for row, goal in list_scenarios(db, organization_id=organization_id, workspace_id=workspace_id)
    ]


@router.post("/scenarios", status_code=status.HTTP_201_CREATED)
def post_scenario(
    payload: ScenarioCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_scenario(db, actor_id=actor_id, **payload.model_dump())
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "goal_id": str(row.goal_id), "name": row.name, "status": row.status}
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/scenarios/{scenario_id}/status")
def post_scenario_status(
    scenario_id: uuid.UUID,
    payload: ScenarioStatusRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        row = set_scenario_status(
            db,
            scenario_id=scenario_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            status=payload.status,
        )
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/scenario-assessments")
def get_scenario_assessments(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [
        {
            "id": str(row.id), "scenario_id": str(row.scenario_id), "analytics_run_id": str(row.analytics_run_id),
            "assessment": row.assessment, "forecast_performed": row.forecast_performed, "status": row.status,
            "impact": row.impact_estimation_status,
            "impact_estimation_reason_code": row.impact_estimation_reason_code,
            "impact_estimate_numeric": row.impact_estimate_numeric,
            "impact_estimate_unit": row.impact_estimate_unit,
            "impact_model_reference": row.impact_model_reference,
            "reviewer_note": row.reviewer_note, "created_at": row.created_at,
        }
        for row in list_scenario_assessments(db, organization_id=organization_id, workspace_id=workspace_id)
    ]


@router.post("/scenario-assessments", status_code=status.HTTP_201_CREATED)
def post_scenario_assessment(
    payload: ScenarioAssessmentCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_scenario_assessment(db, actor_id=actor_id, **payload.model_dump())
        db.commit(); db.refresh(row)
        return {
            "id": str(row.id), "scenario_id": str(row.scenario_id), "analytics_run_id": str(row.analytics_run_id),
            "assessment": row.assessment, "forecast_performed": row.forecast_performed, "status": row.status,
            "impact": row.impact_estimation_status,
            "impact_estimation_reason_code": row.impact_estimation_reason_code,
            "impact_estimate_numeric": row.impact_estimate_numeric,
            "impact_estimate_unit": row.impact_estimate_unit,
            "impact_model_reference": row.impact_model_reference,
        }
    except (OrdoAnalyticsError, ValueError) as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/scenario-assessments/{assessment_id}/review")
def post_scenario_assessment_review(
    assessment_id: uuid.UUID,
    payload: ScenarioAssessmentReviewRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = review_scenario_assessment(
            db,
            assessment_id=assessment_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            decision=payload.decision,
            reviewer_note=payload.reviewer_note,
            actor_id=actor_id,
        )
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status, "reviewed_at": row.reviewed_at}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/syntheses")
def get_syntheses(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    result = []
    for row, job in list_syntheses(db, organization_id=organization_id, workspace_id=workspace_id):
        result.append({
            "id": str(row.id),
            "analytics_run_id": str(row.analytics_run_id),
            "scenario_id": str(row.scenario_id) if row.scenario_id else None,
            "synthesis_type": row.synthesis_type,
            "review_status": row.review_status,
            "reviewer_note": row.reviewer_note,
            "source_snapshot_sha256": row.source_snapshot_sha256,
            "created_at": row.created_at,
            "job": job_response(db, job).model_dump(mode="json"),
        })
    return result


@router.post("/syntheses", status_code=status.HTTP_202_ACCEPTED)
def post_synthesis(
    payload: SynthesisCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row, job = create_synthesis(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            analytics_run_id=payload.analytics_run_id,
            scenario_id=payload.scenario_id,
            synthesis_type=payload.synthesis_type,
            model_key=payload.model_key,
            actor_id=actor_id,
        )
        db.commit(); synthesis_id = row.id; job_id = job.id
        try:
            dispatch_ai_job(job_id)
        except AIQueueError as exc:
            raise HTTPException(status_code=503, detail="ai job queue unavailable") from exc
        db.expire_all()
        row = db.get(type(row), synthesis_id); job = db.get(type(job), job_id)
        return {"id": str(row.id), "review_status": row.review_status, "job": job_response(db, job).model_dump(mode="json")}
    except (OrdoAnalyticsError, AIServiceError, ValueError) as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/syntheses/{synthesis_id}/review")
def post_review(
    synthesis_id: uuid.UUID,
    payload: SynthesisReviewRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row, job = review_synthesis(
            db,
            synthesis_id=synthesis_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            decision=payload.decision,
            reviewer_note=payload.reviewer_note,
            actor_id=actor_id,
        )
        db.commit(); db.refresh(row); db.refresh(job)
        return {"id": str(row.id), "review_status": row.review_status, "human_review_status": job.human_review_status, "reviewed_at": row.reviewed_at}
    except OrdoAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None
