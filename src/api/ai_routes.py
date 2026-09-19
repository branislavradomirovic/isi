from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.ai.embeddings import pgvector_capability
from src.platform.ai.evaluation import (
    AIEvaluationError,
    append_evaluation_result,
    append_evaluation_review,
    aggregate_evaluation_metrics,
    benchmark_execution_provenance,
    canonical_safety_kind,
    create_evaluation_run,
    finalize_evaluation_run,
    get_evaluation_run,
    governed_execution_cases,
    list_evaluation_datasets,
    list_evaluation_results,
    list_evaluation_reviews,
    list_evaluation_runs,
    register_evaluation_dataset,
    evaluate_classification,
    evaluate_llm_case,
    evaluate_regression,
    evaluate_retrieval,
    evaluate_safety_cases,
    evaluate_vlm_case,
    list_promotion_benchmarks,
    list_threshold_profiles,
    register_promotion_benchmark,
    register_threshold_profile,
)
from src.platform.ai.governance import (
    AIGovernanceError,
    list_fallbacks,
    list_prompt_rollbacks,
    list_registrations,
    register_fallback,
    register_model,
    register_prompt_rollback,
    retire_registration,
)
from src.platform.ai.queue import AIQueueError, dispatch_ai_job
from src.platform.ai.monitoring import (
    AIMonitoringError,
    capability_status,
    create_drift_snapshot,
    list_drift_snapshots,
    reset_circuit,
)
from src.platform.ai.promotion import (
    AIPromotionError,
    execute_promotion,
    execute_rollback,
    preview_promotion,
)
from src.platform.ai.xai import evaluation_explanation, job_fallback_explanation
from src.platform.ai.schemas import (
    AICapabilityResponse,
    AIScope,
    AIEmbeddingCreateRequest,
    AIEmbeddingResponse,
    AIJobCreateRequest,
    AIJobResponse,
    AIModelResponse,
    AIModelRegistrationCreateRequest,
    AIModelRegistrationResponse,
    AIPromptResponse,
    AIGovernanceScopeRequest,
    AIFallbackCreateRequest,
    AIFallbackResponse,
    AIPromptRollbackCreateRequest,
    AIPromptRollbackResponse,
    AIEvaluationDatasetCreateRequest,
    AIEvaluationDatasetResponse,
    AIEvaluationResultCreateRequest,
    AIEvaluationResultResponse,
    AIEvaluationReviewCreateRequest,
    AIEvaluationReviewResponse,
    AIEvaluationRunCreateRequest,
    AIEvaluationRunResponse,
    AIEvaluationTerminalRequest,
    AICapabilityThresholdCreateRequest,
    AICapabilityThresholdResponse,
    AICircuitResetRequest,
    AIDriftSnapshotCreateRequest,
    AIEvaluationBenchmarkCreateRequest,
    AIEvaluationBenchmarkResponse,
    AIEvaluationExecuteRequest,
    AIPromotionExecuteRequest,
    AIPromotionPreviewRequest,
    AIRollbackExecuteRequest,
)
from src.platform.ai.service import (
    AIServiceError,
    actor_membership_id,
    create_ai_job,
    create_embedding,
    get_scoped_job,
    job_response,
    list_jobs,
    list_models,
    list_prompts,
    model_response,
)
from src.platform.app_context.service import AppContextError, resolve_selection


router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


def _require_permission(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    permission_code: str,
) -> None:
    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
    except AppContextError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ai scope not accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, product_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ai permission denied")


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> None:
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="ai.run",
    )


def _require_platform_admin_mutation(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> None:
    """Resolve the normal scope, then require global platform authority."""

    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="organization.manage",
    )
    if not context.user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="platform admin required for shared AI governance mutation",
        )


def _require_promotion_authority(
    db: Session, context: AuthContext, *, organization_id: uuid.UUID,
    workspace_id: uuid.UUID, product_code: str,
) -> None:
    _require_platform_admin_mutation(
        db, context, organization_id=organization_id,
        workspace_id=workspace_id, product_code=product_code,
    )
    if not has_permission(db, context.user.id, organization_id, "report.publish", product_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="report.publish required")


def _authorized_serbian_rubric_reviewer(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
    cases: list[dict[str, object]],
) -> uuid.UUID | None:
    rubric_cases = [case for case in cases if case.get("serbian_human_rubric") is not None]
    if not rubric_cases:
        return None
    if (
        actor_id is None
        or not has_permission(
            db, context.user.id, organization_id, "report.publish", product_code
        )
    ):
        raise AIEvaluationError("serbian_human_rubric_requires_authorized_review")
    for case in rubric_cases:
        rubric = case.get("serbian_human_rubric")
        evidence_reference = rubric.get("evidence_reference") if isinstance(rubric, dict) else None
        if (
            not isinstance(evidence_reference, str)
            or not evidence_reference.strip()
            or len(evidence_reference.strip()) > 500
        ):
            raise AIEvaluationError("serbian_human_rubric_requires_authorized_review")
    return actor_id


def _service_error(exc: AIServiceError) -> HTTPException:
    code = str(exc)
    if code in {"ai_job_not_accessible", "prompt_not_accessible", "policy_not_accessible", "model_not_accessible"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    if code in {"development_stub_not_allowed", "provider_blocked_by_policy", "embedding_provider_blocked_by_policy"}:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=code)
    if code in {"provider_unavailable", "timeout", "provider_http_error", "external_provider_not_configured"}:
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


def _governance_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    if code.endswith("not_accessible") or code.endswith("not_found"):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    conflict_markers = (
        "immutable",
        "already",
        "cycle",
        "champion",
        "transition",
        "terminal",
        "new_version_required",
    )
    if any(marker in code for marker in conflict_markers):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


def _dispatch_or_503(job_id: uuid.UUID) -> None:
    try:
        dispatch_ai_job(job_id)
    except AIQueueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ai job queue unavailable") from exc


@router.get("/capabilities", response_model=AICapabilityResponse)
def get_capabilities(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    capability = pgvector_capability(db)
    settings = get_settings()
    return AICapabilityResponse(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        provider_default=str(getattr(settings, "ai_provider_default", "ollama")),
        ollama_base_url=str(getattr(settings, "ai_ollama_base_url", "http://127.0.0.1:11434")),
        development_stub_enabled=bool(getattr(settings, "ai_allow_dev_stub", False))
        and str(getattr(settings, "isi_env", "development")).lower() != "production",
        pgvector_available=capability.available,
        pgvector_enabled=capability.enabled,
        native_vector_table=capability.native_table,
        human_accountability="AI output is decision-support; human professional/institutional responsibility remains required.",
    )


@router.get("/models", response_model=list[AIModelResponse])
def get_models(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    purpose: str | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    return [model_response(model) for model in list_models(db, product_code=product_code, purpose=purpose)]


@router.get("/prompts", response_model=list[AIPromptResponse])
def get_prompts(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    return list_prompts(db, product_code=product_code)


@router.get("/jobs", response_model=list[AIJobResponse])
def get_jobs(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    return [
        job_response(db, job)
        for job in list_jobs(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    ]


@router.post("/jobs", response_model=AIJobResponse, status_code=status.HTTP_202_ACCEPTED)
def post_job(
    payload: AIJobCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        job = create_ai_job(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            input_text=payload.input_text,
            prompt_key=payload.prompt_key,
            model_key=payload.model_key,
            model_registration_id=payload.model_registration_id,
            policy_key=payload.policy_key,
            sensitivity=payload.sensitivity,
            actor_id=actor_id,
        )
        db.commit()
        job_id = job.id
        _dispatch_or_503(job_id)
        db.expire_all()
        return job_response(db, db.get(type(job), job_id))
    except AIServiceError as exc:
        db.rollback()
        raise _service_error(exc) from None


@router.get("/jobs/{job_id}", response_model=AIJobResponse)
def get_job(
    job_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    try:
        job = get_scoped_job(
            db,
            job_id=job_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        return job_response(db, job)
    except AIServiceError as exc:
        raise _service_error(exc) from None


@router.post("/embeddings", response_model=AIEmbeddingResponse, status_code=status.HTTP_201_CREATED)
def post_embedding(
    payload: AIEmbeddingCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        result = create_embedding(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            namespace=payload.namespace,
            source_type=payload.source_type,
            source_id=payload.source_id,
            chunk_index=payload.chunk_index,
            text=payload.text,
            model_key=payload.model_key,
            sensitivity=payload.sensitivity,
            actor_id=actor_id,
        )
        db.commit()
        return result
    except (AIServiceError, ValueError) as exc:
        db.rollback()
        if isinstance(exc, AIServiceError):
            raise _service_error(exc) from None
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None


@router.get("/governance/registrations", response_model=list[AIModelRegistrationResponse])
def get_model_registrations(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    capability_key: str | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    return list_registrations(db, product_code=product_code, capability_key=capability_key)


@router.post(
    "/governance/registrations",
    response_model=AIModelRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_model_registration(
    payload: AIModelRegistrationCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_model(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            capability_key=payload.capability_key,
            product_scope=payload.product_scope,
            model_family=payload.model_family,
            model_key=payload.model_key,
            runtime_model_id=payload.runtime_model_id,
            provider_name=payload.provider_name,
            runtime_name=payload.runtime_name,
            version=payload.version,
            revision=payload.revision,
            artifact_uri=payload.artifact_uri,
            artifact_checksum=payload.artifact_checksum,
            provenance=payload.provenance,
            lifecycle_state=payload.lifecycle_state,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIGovernanceError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/governance/registrations/{registration_id}/retire", response_model=AIModelRegistrationResponse)
def post_retire_model_registration(
    registration_id: uuid.UUID,
    payload: AIGovernanceScopeRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = retire_registration(
            db,
            registration_id=registration_id,
            product_code=payload.product_code,
            actor_id=actor_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIGovernanceError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/governance/fallbacks", response_model=list[AIFallbackResponse])
def get_registered_fallbacks(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    source_registration_id: uuid.UUID | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    return list_fallbacks(
        db,
        product_code=product_code,
        source_registration_id=source_registration_id,
    )


@router.post("/governance/fallbacks", response_model=AIFallbackResponse, status_code=status.HTTP_201_CREATED)
def post_registered_fallback(
    payload: AIFallbackCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_fallback(
            db,
            source_registration_id=payload.source_registration_id,
            target_registration_id=payload.target_registration_id,
            priority=payload.priority,
            trigger_codes=payload.trigger_codes,
            semantically_equivalent=payload.semantically_equivalent,
            requires_human_review=payload.requires_human_review,
            provenance=payload.provenance,
            actor_id=actor_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIGovernanceError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/governance/prompt-rollbacks", response_model=list[AIPromptRollbackResponse])
def get_prompt_rollbacks(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    return list_prompt_rollbacks(db, product_code=product_code)


@router.post(
    "/governance/prompt-rollbacks",
    response_model=AIPromptRollbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_prompt_rollback(
    payload: AIPromptRollbackCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_prompt_rollback(
            db,
            source_prompt_version_id=payload.source_prompt_version_id,
            target_prompt_version_id=payload.target_prompt_version_id,
            provenance=payload.provenance,
            actor_id=actor_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIGovernanceError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/evaluation/datasets", response_model=list[AIEvaluationDatasetResponse])
def get_evaluation_datasets(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    return list_evaluation_datasets(db, product_code=product_code)


@router.post(
    "/evaluation/datasets",
    response_model=AIEvaluationDatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_evaluation_dataset(
    payload: AIEvaluationDatasetCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_evaluation_dataset(
            db,
            manifest=payload.manifest,
            product_code=payload.product_code,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/evaluation/runs", response_model=list[AIEvaluationRunResponse])
def get_evaluation_runs(
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    return list_evaluation_runs(
        db,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )


@router.post("/evaluation/runs", response_model=AIEvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def post_evaluation_run(
    payload: AIEvaluationRunCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="analysis.run",
    )
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_evaluation_run(
            db,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            dataset_id=payload.dataset_id,
            benchmark_id=payload.benchmark_id,
            model_registration_id=payload.model_registration_id,
            baseline_registration_id=payload.baseline_registration_id,
            prompt_version_id=payload.prompt_version_id,
            policy_profile_id=payload.policy_profile_id,
            input_fingerprint=payload.input_fingerprint,
            environment_fingerprint=payload.environment_fingerprint,
            provenance=payload.provenance,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/evaluation/runs/{run_id}", response_model=AIEvaluationRunResponse)
def get_evaluation_run_route(
    run_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    try:
        return get_evaluation_run(
            db,
            run_id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except AIEvaluationError as exc:
        raise _governance_error(exc) from None


def _scoped_run_for_payload(
    db: Session,
    *,
    run_id: uuid.UUID,
    payload: AIScope,
):
    return get_evaluation_run(
        db,
        run_id=run_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )


@router.get("/evaluation/runs/{run_id}/results", response_model=list[AIEvaluationResultResponse])
def get_evaluation_results(
    run_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    try:
        get_evaluation_run(
            db,
            run_id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        return list_evaluation_results(db, run_id=run_id)
    except AIEvaluationError as exc:
        raise _governance_error(exc) from None


@router.post(
    "/evaluation/runs/{run_id}/results",
    response_model=AIEvaluationResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_evaluation_result(
    run_id: uuid.UUID,
    payload: AIEvaluationResultCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="analysis.run",
    )
    try:
        run = _scoped_run_for_payload(db, run_id=run_id, payload=payload)
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = append_evaluation_result(
            db,
            run=run,
            result_type=payload.result_type,
            result_key=payload.result_key,
            payload=payload.payload,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


def _finalize_run_route(
    *,
    run_id: uuid.UUID,
    payload: AIEvaluationTerminalRequest,
    terminal_status: str,
    context: AuthContext,
    db: Session,
):
    _require_permission(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="analysis.run",
    )
    try:
        run = _scoped_run_for_payload(db, run_id=run_id, payload=payload)
        row = finalize_evaluation_run(
            db,
            run=run,
            status=terminal_status,
            failure_reason=payload.failure_reason,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/evaluation/runs/{run_id}/complete", response_model=AIEvaluationRunResponse)
def post_complete_evaluation_run(
    run_id: uuid.UUID,
    payload: AIEvaluationTerminalRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    return _finalize_run_route(
        run_id=run_id,
        payload=payload,
        terminal_status="completed",
        context=context,
        db=db,
    )


@router.post("/evaluation/runs/{run_id}/fail", response_model=AIEvaluationRunResponse)
def post_fail_evaluation_run(
    run_id: uuid.UUID,
    payload: AIEvaluationTerminalRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    return _finalize_run_route(
        run_id=run_id,
        payload=payload,
        terminal_status="failed",
        context=context,
        db=db,
    )


@router.get("/evaluation/runs/{run_id}/reviews", response_model=list[AIEvaluationReviewResponse])
def get_evaluation_reviews(
    run_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission_code="analysis.read",
    )
    try:
        get_evaluation_run(
            db,
            run_id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        return list_evaluation_reviews(db, run_id=run_id)
    except AIEvaluationError as exc:
        raise _governance_error(exc) from None


@router.post(
    "/evaluation/runs/{run_id}/reviews",
    response_model=AIEvaluationReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_evaluation_review(
    run_id: uuid.UUID,
    payload: AIEvaluationReviewCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="report.publish",
    )
    try:
        run = _scoped_run_for_payload(db, run_id=run_id, payload=payload)
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        if actor_id is None:
            raise AIEvaluationError("evaluation_reviewer_membership_required")
        row = append_evaluation_review(
            db,
            run=run,
            reviewer_membership_id=actor_id,
            decision=payload.decision,
            notes=payload.notes,
            evidence_reference=payload.evidence_reference,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/evaluation/benchmarks", response_model=list[AIEvaluationBenchmarkResponse])
def get_promotion_benchmarks(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    return list_promotion_benchmarks(db, product_code=product_code)


@router.post("/evaluation/benchmarks", response_model=AIEvaluationBenchmarkResponse, status_code=status.HTTP_201_CREATED)
def post_promotion_benchmark(
    payload: AIEvaluationBenchmarkCreateRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(db, context, organization_id=payload.organization_id,
                                     workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_promotion_benchmark(db, manifest=payload.manifest,
                                           product_code=payload.product_code, actor_id=actor_id)
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/governance/thresholds", response_model=list[AICapabilityThresholdResponse])
def get_capability_thresholds(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    return list_threshold_profiles(db, product_code=product_code)


@router.post("/governance/thresholds", response_model=AICapabilityThresholdResponse, status_code=status.HTTP_201_CREATED)
def post_capability_threshold(
    payload: AICapabilityThresholdCreateRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(db, context, organization_id=payload.organization_id,
                                     workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = register_threshold_profile(
            db, product_scope=payload.product_scope, capability_key=payload.capability_key,
            model_family=payload.model_family, version=payload.version,
            metric_definitions=payload.metric_definitions, minimum_thresholds=payload.minimum_thresholds,
            minimum_deltas=payload.minimum_deltas, hard_gates=payload.hard_gates,
            resource_limits=payload.resource_limits, failure_threshold=payload.failure_threshold,
            cooldown_seconds=payload.cooldown_seconds, provenance=payload.provenance, actor_id=actor_id,
            product_code=payload.product_code,
        )
        db.commit()
        db.refresh(row)
        return row
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/evaluation/runs/{run_id}/execute", response_model=list[AIEvaluationResultResponse])
def post_execute_evaluation(
    run_id: uuid.UUID, payload: AIEvaluationExecuteRequest,
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=payload.organization_id,
                        workspace_id=payload.workspace_id, product_code=payload.product_code,
                        permission_code="analysis.run")
    try:
        run = _scoped_run_for_payload(db, run_id=run_id, payload=payload)
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        cases = governed_execution_cases(
            db,
            run=run,
            submitted_cases=payload.cases,
            evaluator_family=payload.evaluator,
        )
        authorized_rubric_reviewer_id = (
            _authorized_serbian_rubric_reviewer(
                db,
                context,
                organization_id=payload.organization_id,
                product_code=payload.product_code,
                actor_id=actor_id,
                cases=cases,
            )
            if payload.evaluator == "llm"
            else None
        )
        if run.benchmark_id is not None:
            primary_cases = [case for case in cases if canonical_safety_kind(case) is None]
            safety_cases = [case for case in cases if canonical_safety_kind(case) is not None]
            if not primary_cases:
                raise AIEvaluationError("promotion_benchmark_primary_cases_required")
        else:
            primary_cases = cases
            safety_cases = []
        metrics: list[dict[str, object]] = []
        if payload.evaluator == "statistical_ml":
            for case_index, case in enumerate(primary_cases):
                if case.get("task") == "classification":
                    case_metrics = evaluate_classification(
                        case.get("expected", []), case.get("predicted", []), case.get("probabilities")
                    )
                else:
                    case_metrics = evaluate_regression(case.get("expected", []), case.get("actual", []))
                for item in case_metrics:
                    item["case_refs"] = [str(case.get("case_id", f"case-{case_index + 1}"))]
                metrics.extend(case_metrics)
        elif payload.evaluator == "embedding":
            if not primary_cases:
                raise AIEvaluationError("promotion_benchmark_primary_cases_required")
            k_value = primary_cases[0].get("k", 10)
            if isinstance(k_value, bool) or not isinstance(k_value, int):
                raise AIEvaluationError("retrieval_positive_integer_k_required")
            metrics = evaluate_retrieval(primary_cases, k=k_value)
            case_refs = [str(case.get("case_id", f"case-{index + 1}")) for index, case in enumerate(primary_cases)]
            for item in metrics:
                item["case_refs"] = case_refs
        elif payload.evaluator == "llm":
            for case_index, case in enumerate(primary_cases):
                case_metrics = evaluate_llm_case(
                    case,
                    authorized_reviewer_membership_id=authorized_rubric_reviewer_id,
                )
                for item in case_metrics:
                    item["case_refs"] = [str(case.get("case_id", f"case-{case_index + 1}"))]
                metrics.extend(case_metrics)
        elif payload.evaluator == "vlm":
            for case_index, case in enumerate(primary_cases):
                case_metrics = evaluate_vlm_case(case)
                for item in case_metrics:
                    item["case_refs"] = [str(case.get("case_id", f"case-{case_index + 1}"))]
                metrics.extend(case_metrics)
        else:
            metrics = evaluate_safety_cases(primary_cases)
        if safety_cases:
            metrics.extend(evaluate_safety_cases(safety_cases))
        if run.benchmark_id is not None:
            metrics.append(benchmark_execution_provenance(db, run=run, cases=cases))
        metrics = aggregate_evaluation_metrics(metrics)
        def result_type_for(metric_key: object) -> str:
            key = str(metric_key)
            if key.startswith("safety."):
                return "safety"
            if "provenance" in key or key == "namespace_isolation":
                return "provenance"
            if key in {"latency_ms", "failure_rate", "input_tokens", "output_tokens", "memory_mb"}:
                return "reliability"
            return "metric"

        rows = [append_evaluation_result(
            db, run=run, result_type=result_type_for(item["metric_key"]),
            result_key=str(item["metric_key"]), payload=item, actor_id=actor_id,
            governed_execution=True,
        ) for item in metrics]
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows
    except AIEvaluationError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/promotion/preview")
def post_promotion_preview(
    payload: AIPromotionPreviewRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_platform_admin_mutation(db, context, organization_id=payload.organization_id,
                                     workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = preview_promotion(
            db, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, candidate_run_id=payload.candidate_run_id,
            baseline_run_id=payload.baseline_run_id, threshold_profile_id=payload.threshold_profile_id,
            rollback_registration_id=payload.rollback_registration_id, actor_id=actor_id,
        )
        db.commit()
        return {"id": str(row.id), "status": row.decision_status,
                "blocker_reasons": row.blocker_reasons,
                "comparison_evidence": row.comparison_evidence,
                "evidence_fingerprint": row.evidence_fingerprint}
    except AIPromotionError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/promotion/execute")
def post_promotion_execute(
    payload: AIPromotionExecuteRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_promotion_authority(db, context, organization_id=payload.organization_id,
                                 workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = execute_promotion(
            db, decision_id=payload.promotion_decision_id,
            owner_approval_reference=payload.owner_approval_reference, actor_id=actor_id,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        db.commit()
        return {"id": str(row.id), "status": row.decision_status,
                "evidence_fingerprint": row.evidence_fingerprint,
                "server_activation": False, "model_installation": False}
    except AIPromotionError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.post("/promotion/rollback")
def post_promotion_rollback(
    payload: AIRollbackExecuteRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_promotion_authority(db, context, organization_id=payload.organization_id,
                                 workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = execute_rollback(
            db, product_code=payload.product_code, capability_key=payload.capability_key,
            reason=payload.reason, evidence_reference=payload.evidence_reference, actor_id=actor_id,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
        )
        db.commit()
        return {"runtime_state_id": str(row.id), "champion_registration_id": str(row.champion_registration_id),
                "server_activation": False, "model_installation": False}
    except AIPromotionError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/runtime/capabilities/{capability_key}")
def get_capability_runtime_status(
    capability_key: str, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    return capability_status(
        db, organization_id=organization_id, workspace_id=workspace_id,
        product_code=product_code, capability_key=capability_key,
    )


@router.post("/runtime/circuit/reset")
def post_circuit_reset(
    payload: AICircuitResetRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_promotion_authority(db, context, organization_id=payload.organization_id,
                                 workspace_id=payload.workspace_id, product_code=payload.product_code)
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = reset_circuit(
            db, product_code=payload.product_code, capability_key=payload.capability_key,
            reason=payload.reason, actor_id=actor_id, organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
        )
        db.commit()
        return {"id": str(row.id), "circuit_state": row.circuit_state, "version": row.version}
    except AIMonitoringError as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/monitoring/drift")
def get_drift_snapshots(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), capability_key: str | None = Query(default=None),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    return list_drift_snapshots(db, organization_id=organization_id, workspace_id=workspace_id,
                                product_code=product_code, capability_key=capability_key)


@router.post("/monitoring/drift", status_code=status.HTTP_201_CREATED)
def post_drift_snapshot(
    payload: AIDriftSnapshotCreateRequest, context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=payload.organization_id,
                        workspace_id=payload.workspace_id, product_code=payload.product_code,
                        permission_code="analysis.run")
    try:
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        row = create_drift_snapshot(
            db, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, capability_key=payload.capability_key,
            model_registration_id=payload.model_registration_id,
            threshold_profile_id=payload.threshold_profile_id,
            window_start=payload.window_start, window_end=payload.window_end,
            observed_metrics=payload.observed_metrics, reference_metrics=payload.reference_metrics,
            provenance=payload.provenance, actor_id=actor_id,
        )
        db.commit()
        return {"id": str(row.id), "status": row.status, "fingerprint": row.fingerprint}
    except (AIMonitoringError, ValueError) as exc:
        db.rollback()
        raise _governance_error(exc) from None


@router.get("/xai/evaluations/{run_id}")
def get_evaluation_xai(
    run_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    get_evaluation_run(db, run_id=run_id, organization_id=organization_id,
                       workspace_id=workspace_id, product_code=product_code)
    return evaluation_explanation(
        db, run_id=run_id, organization_id=organization_id,
        workspace_id=workspace_id, product_code=product_code,
    )


@router.get("/xai/jobs/{job_id}")
def get_job_xai(
    job_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_permission(db, context, organization_id=organization_id, workspace_id=workspace_id,
                        product_code=product_code, permission_code="analysis.read")
    get_scoped_job(db, job_id=job_id, organization_id=organization_id,
                   workspace_id=workspace_id, product_code=product_code)
    return job_fallback_explanation(db, job_id=job_id)
