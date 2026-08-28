from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.domains.simpa.analytics_schemas import AnalyticsRunCreateRequest, IndicatorComputeRequest, MethodologyCreateRequest, MethodologyValidateRequest, SynthesisCreateRequest, SynthesisReviewRequest
from src.domains.simpa.analytics_service import SimpaAnalyticsError, build_monitoring_snapshot, compute_indicator, create_analytics_run, create_methodology, create_synthesis, list_analytics_runs, list_methodologies, list_syntheses, review_synthesis, validate_methodology
from src.platform.access.service import has_permission
from src.platform.ai.queue import AIQueueError, dispatch_ai_job
from src.platform.ai.service import AIServiceError, actor_membership_id, job_response
from src.platform.app_context.service import AppContextError, resolve_selection


router = APIRouter(prefix="/api/v1/simpa/analytics", tags=["simpa-analytics"])


def _require_scope(db: Session, context: AuthContext, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, permission_code: str) -> None:
    try:
        resolve_selection(db, user_id=context.user.id, organization_id=organization_id, product_code="SIMPA", workspace_id=workspace_id)
    except AppContextError:
        raise HTTPException(status_code=403, detail="simpa_analytics_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, "SIMPA"):
        raise HTTPException(status_code=403, detail="simpa_analytics_permission_denied")


def _error(exc: Exception) -> HTTPException:
    code = str(exc)
    if code.endswith("not_accessible") or code in {"methodology_not_found"}:
        return HTTPException(status_code=404, detail=code)
    if code in {"methodology_not_validated", "validated_observation_required", "synthesis_not_reviewable"}:
        return HTTPException(status_code=409, detail=code)
    if code in {"provider_unavailable", "timeout", "provider_http_error", "external_provider_not_configured"}:
        return HTTPException(status_code=503, detail=code)
    return HTTPException(status_code=400, detail=code)


def _run_dict(row):
    return {"id": str(row.id), "monitoring_cycle_id": str(row.monitoring_cycle_id) if row.monitoring_cycle_id else None, "status": row.status, "snapshot": row.snapshot, "evidence_quality_score": row.evidence_quality_score, "validated_observation_ratio": row.validated_observation_ratio, "provenance_coverage": row.provenance_coverage, "indicator_coverage": row.indicator_coverage, "created_at": row.created_at}


@router.get("/summary")
def get_summary(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), monitoring_cycle_id: uuid.UUID | None = Query(default=None), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    try:
        return build_monitoring_snapshot(db, organization_id=organization_id, workspace_id=workspace_id, monitoring_cycle_id=monitoring_cycle_id)
    except SimpaAnalyticsError as exc:
        raise _error(exc) from None


@router.get("/runs")
def get_runs(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [_run_dict(row) for row in list_analytics_runs(db, organization_id=organization_id, workspace_id=workspace_id)]


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def post_run(payload: AnalyticsRunCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_analytics_run(db, organization_id=payload.organization_id, workspace_id=payload.workspace_id, monitoring_cycle_id=payload.monitoring_cycle_id, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return _run_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/methodologies")
def get_methodologies(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    return [{"id": str(method.id), "indicator_code": indicator.code, "indicator_name_sr": indicator.name_sr, "version_no": method.version_no, "status": method.status, "computation_type": method.computation_type, "methodology_note": method.methodology_note, "validation_note": method.validation_note} for method, indicator in list_methodologies(db)]


@router.post("/methodologies", status_code=status.HTTP_201_CREATED)
def post_methodology(payload: MethodologyCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_methodology(db, indicator_code=payload.indicator_code, computation_type=payload.computation_type, methodology_note=payload.methodology_note, source_requirements=payload.source_requirements, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "version_no": row.version_no, "status": row.status, "computation_type": row.computation_type}
    except SimpaAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/validate")
def post_validate_methodology(methodology_id: uuid.UUID, payload: MethodologyValidateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="indicator.manage")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = validate_methodology(db, methodology_id=methodology_id, validation_note=payload.validation_note, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "status": row.status, "approved_at": row.approved_at}
    except SimpaAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/compute", status_code=status.HTTP_201_CREATED)
def post_compute(payload: IndicatorComputeRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = compute_indicator(db, organization_id=payload.organization_id, workspace_id=payload.workspace_id, indicator_code=payload.indicator_code, monitoring_cycle_id=payload.monitoring_cycle_id, analytics_run_id=payload.analytics_run_id, actor_id=actor_id)
        db.commit(); db.refresh(row)
        return {"id": str(row.id), "value_numeric": row.value_numeric, "value_text": row.value_text, "unit": row.unit, "quality_score": row.quality_score, "status": row.status, "source_observation_ids": row.source_observation_ids, "computation_trace": row.computation_trace}
    except SimpaAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None


@router.get("/syntheses")
def get_syntheses(organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read")
    result = []
    for row, job in list_syntheses(db, organization_id=organization_id, workspace_id=workspace_id):
        job_data = job_response(db, job).model_dump(mode="json")
        result.append({"id": str(row.id), "analytics_run_id": str(row.analytics_run_id), "review_status": row.review_status, "reviewer_note": row.reviewer_note, "source_snapshot_sha256": row.source_snapshot_sha256, "created_at": row.created_at, "job": job_data})
    return result


@router.post("/syntheses", status_code=status.HTTP_202_ACCEPTED)
def post_synthesis(payload: SynthesisCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row, job = create_synthesis(db, organization_id=payload.organization_id, workspace_id=payload.workspace_id, analytics_run_id=payload.analytics_run_id, sensitivity=payload.sensitivity, model_key=payload.model_key, actor_id=actor_id)
        db.commit(); synthesis_id = row.id; job_id = job.id
        try:
            dispatch_ai_job(job_id)
        except AIQueueError as exc:
            raise HTTPException(status_code=503, detail="ai job queue unavailable") from exc
        db.expire_all()
        row = db.get(type(row), synthesis_id); job = db.get(type(job), job_id)
        return {"id": str(row.id), "review_status": row.review_status, "job": job_response(db, job).model_dump(mode="json")}
    except (SimpaAnalyticsError, AIServiceError) as exc:
        db.rollback(); raise _error(exc) from None


@router.post("/syntheses/{synthesis_id}/review")
def post_review(synthesis_id: uuid.UUID, payload: SynthesisReviewRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id, permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row, job = review_synthesis(db, synthesis_id=synthesis_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id, decision=payload.decision, reviewer_note=payload.reviewer_note, actor_id=actor_id)
        db.commit(); db.refresh(row); db.refresh(job)
        return {"id": str(row.id), "review_status": row.review_status, "human_review_status": job.human_review_status, "reviewed_at": row.reviewed_at}
    except SimpaAnalyticsError as exc:
        db.rollback(); raise _error(exc) from None
