from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_schemas import (
    AnalyticsRunCreateRequest,
    IndicatorComputeRequest,
    MethodologyCreateRequest,
    MethodologyProposeRequest,
    MethodologyReferenceCheckRequest,
    MethodologyReferenceSuiteCreateRequest,
    MethodologyReferenceSuiteRunRequest,
    MethodologyRetireRequest,
    MethodologyValidateRequest,
    SynthesisCreateRequest,
    SynthesisReviewRequest,
)
from src.domains.simpa.analytics_service import (
    SimpaAnalyticsError,
    build_monitoring_snapshot,
    compute_indicator,
    create_analytics_run,
    create_methodology,
    create_methodology_reference_suite,
    create_synthesis,
    list_analytics_runs,
    list_methodologies,
    list_methodology_reference_suites,
    list_syntheses,
    propose_methodology,
    retire_methodology,
    review_synthesis,
    run_methodology_reference_check,
    run_methodology_reference_suite,
    validate_methodology,
)
from src.platform.access.service import has_permission
from src.platform.ai.queue import AIQueueError, dispatch_ai_job
from src.platform.ai.service import AIServiceError, actor_membership_id, job_response
from src.platform.app_context.service import AppContextError, resolve_selection


router = APIRouter(prefix="/api/v1/simpa/analytics", tags=["simpa-analytics"])


def _require_scope(
    db: Session, context: AuthContext, *, organization_id: uuid.UUID, workspace_id: uuid.UUID, permission_code: str
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code="SIMPA",
            workspace_id=workspace_id,
        )
    except AppContextError:
        raise HTTPException(status_code=403, detail="simpa_analytics_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, "SIMPA"):
        raise HTTPException(status_code=403, detail="simpa_analytics_permission_denied")


def _error(exc: Exception) -> HTTPException:
    code = str(exc)
    if code.endswith("not_accessible") or code in {
        "methodology_not_found",
        "methodology_reference_suite_not_found",
    }:
        return HTTPException(status_code=404, detail=code)
    if code in {
        "methodology_not_validated",
        "validated_observation_required",
        "synthesis_not_reviewable",
        "methodology_transition_forbidden",
        "methodology_reference_check_required",
        "methodology_reference_check_failed",
        "methodology_contract_immutable",
        "methodology_reference_suite_required",
        "methodology_reference_suite_already_passed",
        "methodology_reference_suite_terminal",
        "methodology_reference_suite_evidence_invalid",
        "methodology_reference_evidence_mode_ineligible",
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
        "analytical_feature_version_id": str(row.analytical_feature_version_id)
        if row.analytical_feature_version_id
        else None,
        "analytical_artifact_fingerprint": row.analytical_artifact_fingerprint,
        "dataset_contract_version_id": str(row.dataset_contract_version_id)
        if row.dataset_contract_version_id
        else None,
        "dataset_contract_fingerprint": row.dataset_contract_fingerprint,
        "analytical_quality_state": row.analytical_quality_state,
        "evidence_quality_score": row.evidence_quality_score,
        "validated_observation_ratio": row.validated_observation_ratio,
        "provenance_coverage": row.provenance_coverage,
        "indicator_coverage": row.indicator_coverage,
        "created_at": row.created_at,
    }


def _methodology_dict(method, indicator=None):
    return {
        "id": str(method.id),
        "indicator_code": indicator.code if indicator is not None else None,
        "indicator_name_sr": indicator.name_sr if indicator is not None else None,
        "version_no": method.version_no,
        "status": method.status,
        "computation_type": method.computation_type,
        "computation_spec": method.computation_spec,
        "contract_fingerprint": method.contract_fingerprint,
        "methodology_note": method.methodology_note,
        "reference_check_status": method.reference_check_status,
        "reference_check_fingerprint": method.reference_check_fingerprint,
        "reference_evidence_mode": method.reference_evidence_mode,
        "proposed_by_membership_id": str(method.proposed_by_membership_id)
        if method.proposed_by_membership_id
        else None,
        "proposed_at": method.proposed_at,
        "approved_by_membership_id": str(method.approved_by_membership_id)
        if method.approved_by_membership_id
        else None,
        "approved_at": method.approved_at,
        "validation_note": method.validation_note,
        "retired_by_membership_id": str(method.retired_by_membership_id) if method.retired_by_membership_id else None,
        "retired_at": method.retired_at,
        "retirement_note": method.retirement_note,
    }


def _reference_suite_dict(suite, cases):
    return {
        "id": str(suite.id),
        "methodology_id": str(suite.methodology_id),
        "version_no": suite.version_no,
        "schema_version": suite.schema_version,
        "methodology_contract_fingerprint": suite.methodology_contract_fingerprint,
        "reference_dataset": suite.reference_dataset,
        "reference_dataset_version": suite.reference_dataset_version,
        "suite_fingerprint": suite.suite_fingerprint,
        "case_count": suite.case_count,
        "status": suite.status,
        "result_fingerprint": suite.result_fingerprint,
        "result_detail": suite.result_detail,
        "created_by_membership_id": str(suite.created_by_membership_id) if suite.created_by_membership_id else None,
        "executed_by_membership_id": str(suite.executed_by_membership_id) if suite.executed_by_membership_id else None,
        "created_at": suite.created_at,
        "executed_at": suite.executed_at,
        "cases": [
            {
                "id": str(case.id),
                "case_key": case.case_key,
                "case_index": case.case_index,
                "reference_record": case.reference_record,
                "expected_result": case.expected_result,
                "case_fingerprint": case.case_fingerprint,
                "status": case.status,
                "result_fingerprint": case.result_fingerprint,
                "result_detail": case.result_detail,
                "created_at": case.created_at,
            }
            for case in cases
        ],
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
    _require_scope(
        db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read"
    )
    try:
        return build_monitoring_snapshot(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            analytical_artifact_type=analytical_artifact_type,
            analytical_artifact_id=analytical_artifact_id,
            monitoring_cycle_id=monitoring_cycle_id,
        )
    except SimpaAnalyticsError as exc:
        raise _error(exc) from None


@router.get("/runs")
def get_runs(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read"
    )
    return [
        _run_dict(row) for row in list_analytics_runs(db, organization_id=organization_id, workspace_id=workspace_id)
    ]


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def post_run(
    payload: AnalyticsRunCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="analysis.run",
    )
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
        db.commit()
        db.refresh(row)
        return _run_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/methodologies")
def get_methodologies(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read"
    )
    return [_methodology_dict(method, indicator) for method, indicator in list_methodologies(db)]


@router.post("/methodologies", status_code=status.HTTP_201_CREATED)
def post_methodology(
    payload: MethodologyCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_methodology(
            db,
            indicator_code=payload.indicator_code,
            computation_type=payload.computation_type,
            methodology_note=payload.methodology_note,
            source_requirements=payload.source_requirements,
            computation_spec=payload.computation_spec,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(row)
        return _methodology_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/propose")
def post_propose_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyProposeRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = propose_methodology(db, methodology_id=methodology_id, actor_id=actor_id)
        db.commit()
        db.refresh(row)
        return _methodology_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/reference-check")
def post_methodology_reference_check(
    methodology_id: uuid.UUID,
    payload: MethodologyReferenceCheckRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        row = run_methodology_reference_check(
            db,
            methodology_id=methodology_id,
            reference_record=payload.reference_record.model_dump(mode="json"),
            expected_result=payload.expected_result.model_dump(mode="json"),
        )
        db.commit()
        db.refresh(row)
        return _methodology_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/methodologies/{methodology_id}/reference-suites")
def get_methodology_reference_suites(
    methodology_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission_code="analysis.read",
    )
    if db.get(SimpaIndicatorMethodology, methodology_id) is None:
        raise HTTPException(status_code=404, detail="methodology_not_found")
    return [
        _reference_suite_dict(suite, cases)
        for suite, cases in list_methodology_reference_suites(db, methodology_id=methodology_id)
    ]


@router.post("/methodologies/{methodology_id}/reference-suites", status_code=status.HTTP_201_CREATED)
def post_methodology_reference_suite(
    methodology_id: uuid.UUID,
    payload: MethodologyReferenceSuiteCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        suite = create_methodology_reference_suite(
            db,
            methodology_id=methodology_id,
            reference_dataset_version=payload.reference_dataset_version,
            cases=[case.model_dump(mode="json") for case in payload.cases],
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(suite)
        cases = next(
            cases
            for candidate, cases in list_methodology_reference_suites(db, methodology_id=methodology_id)
            if candidate.id == suite.id
        )
        return _reference_suite_dict(suite, cases)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/reference-suites/{suite_id}/run")
def post_run_methodology_reference_suite(
    methodology_id: uuid.UUID,
    suite_id: uuid.UUID,
    payload: MethodologyReferenceSuiteRunRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        suite = run_methodology_reference_suite(
            db,
            methodology_id=methodology_id,
            suite_id=suite_id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(suite)
        cases = next(
            cases
            for candidate, cases in list_methodology_reference_suites(db, methodology_id=methodology_id)
            if candidate.id == suite.id
        )
        return _reference_suite_dict(suite, cases)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/validate")
def post_validate_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyValidateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = validate_methodology(
            db, methodology_id=methodology_id, validation_note=payload.validation_note, actor_id=actor_id
        )
        db.commit()
        db.refresh(row)
        return _methodology_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/methodologies/{methodology_id}/retire")
def post_retire_methodology(
    methodology_id: uuid.UUID,
    payload: MethodologyRetireRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="indicator.manage",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = retire_methodology(
            db, methodology_id=methodology_id, retirement_note=payload.retirement_note, actor_id=actor_id
        )
        db.commit()
        db.refresh(row)
        return _methodology_dict(row)
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/compute", status_code=status.HTTP_201_CREATED)
def post_compute(
    payload: IndicatorComputeRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="analysis.run",
    )
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
        db.commit()
        db.refresh(row)
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
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None


@router.get("/syntheses")
def get_syntheses(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db, context, organization_id=organization_id, workspace_id=workspace_id, permission_code="analysis.read"
    )
    result = []
    for row, job in list_syntheses(db, organization_id=organization_id, workspace_id=workspace_id):
        job_data = job_response(db, job).model_dump(mode="json")
        result.append(
            {
                "id": str(row.id),
                "analytics_run_id": str(row.analytics_run_id),
                "review_status": row.review_status,
                "reviewer_note": row.reviewer_note,
                "source_snapshot_sha256": row.source_snapshot_sha256,
                "created_at": row.created_at,
                "job": job_data,
            }
        )
    return result


@router.post("/syntheses", status_code=status.HTTP_202_ACCEPTED)
def post_synthesis(
    payload: SynthesisCreateRequest, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="analysis.run",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row, job = create_synthesis(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            analytics_run_id=payload.analytics_run_id,
            sensitivity=payload.sensitivity,
            model_key=payload.model_key,
            actor_id=actor_id,
        )
        db.commit()
        synthesis_id = row.id
        job_id = job.id
        try:
            dispatch_ai_job(job_id)
        except AIQueueError as exc:
            raise HTTPException(status_code=503, detail="ai job queue unavailable") from exc
        db.expire_all()
        row = db.get(type(row), synthesis_id)
        job = db.get(type(job), job_id)
        return {
            "id": str(row.id),
            "review_status": row.review_status,
            "job": job_response(db, job).model_dump(mode="json"),
        }
    except (SimpaAnalyticsError, AIServiceError) as exc:
        db.rollback()
        raise _error(exc) from None


@router.post("/syntheses/{synthesis_id}/review")
def post_review(
    synthesis_id: uuid.UUID,
    payload: SynthesisReviewRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        permission_code="analysis.run",
    )
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
        db.commit()
        db.refresh(row)
        db.refresh(job)
        return {
            "id": str(row.id),
            "review_status": row.review_status,
            "human_review_status": job.human_review_status,
            "reviewed_at": row.reviewed_at,
        }
    except SimpaAnalyticsError as exc:
        db.rollback()
        raise _error(exc) from None
