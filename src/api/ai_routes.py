from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.ai.embeddings import pgvector_capability
from src.platform.ai.queue import AIQueueError, dispatch_ai_job
from src.platform.ai.schemas import (
    AICapabilityResponse,
    AIEmbeddingCreateRequest,
    AIEmbeddingResponse,
    AIJobCreateRequest,
    AIJobResponse,
    AIModelResponse,
    AIPromptResponse,
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


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
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
    if not has_permission(db, context.user.id, organization_id, "ai.run", product_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ai permission denied")


def _service_error(exc: AIServiceError) -> HTTPException:
    code = str(exc)
    if code in {"ai_job_not_accessible", "prompt_not_accessible", "policy_not_accessible", "model_not_accessible"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    if code in {"development_stub_not_allowed", "provider_blocked_by_policy", "embedding_provider_blocked_by_policy"}:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=code)
    if code in {"provider_unavailable", "timeout", "provider_http_error", "external_provider_not_configured"}:
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=code)
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
