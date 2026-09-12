from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.data.models import DataSourceVersion, IngestionJob
from src.platform.data.queue import DataQueueError, dispatch_job
from src.platform.data.schemas import (
    AnonymizationProposalCreate,
    AnonymizationRecordResponse,
    AnonymizationReviewRequest,
    ExportRequest,
    HoldPlaceRequest,
    IngestionJobResponse,
    ScopeQuery,
    RetentionMutationRequest,
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionStateResponse,
    SourceGovernanceResponse,
    SourceGovernanceUpdate,
    SourceDetailResponse,
    SourceSummaryResponse,
    UploadCreateRequest,
    UploadResponse,
    VersionCreateRequest,
)
from src.platform.data.service import (
    DataPlatformError,
    actor_membership_id,
    create_source_upload,
    create_source_version,
    create_retention_policy,
    create_validation_job,
    decode_upload,
    get_scoped_source,
    get_source_governance,
    job_response,
    list_sources,
    list_retention_policies,
    source_detail,
    source_summary,
    update_source_governance,
)
from src.platform.data.storage import build_storage
from src.platform.data.privacy_service import (
    approve_purge,
    execute_purge,
    export_source_version,
    get_retention_state,
    inspect_export,
    place_hold,
    propose_anonymization,
    record_export_failure,
    record_export_denial,
    record_purge_storage_failure,
    release_hold,
    request_purge,
    review_anonymization,
    validate_export_policy,
)
from src.platform.security.assurance import PrivilegedOperation, evaluate_privileged_operation
from src.platform.security.service import record_security_event, utcnow


router = APIRouter(prefix="/api/v1/data", tags=["data"])


def _require_scope(
    db: Session,
    context: AuthContext,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    permission_code: str,
) -> None:
    def deny(reason: str) -> None:
        record_security_event(
            db,
            event_type="data.authorization",
            outcome="deny",
            user_id=context.user.id,
            metadata={
                "organization_id": str(organization_id),
                "workspace_id": str(workspace_id),
                "product_code": product_code,
                "permission_code": permission_code,
                "reason": reason,
            },
        )
        db.commit()

    try:
        resolve_selection(
            db,
            user_id=context.user.id,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
    except AppContextError:
        deny("scope_not_accessible")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="data_scope_not_accessible") from None
    if not has_permission(db, context.user.id, organization_id, permission_code, product_code):
        deny("permission_denied")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="data_permission_denied")


def _platform_error(exc: DataPlatformError) -> HTTPException:
    code = str(exc)
    if code in {"source_not_accessible", "version_not_accessible", "anonymization_record_not_accessible", "workspace_scope_mismatch"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    if code in {"upload_too_large"}:
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=code)
    if code in {"source_name_exists", "governance_revision_conflict", "retention_revision_conflict", "purge_state_conflict", "anonymization_state_conflict"}:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code)
    if code == "storage_operation_failed":
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


def _step_up(
    db: Session,
    context: AuthContext,
    *,
    operation: PrivilegedOperation,
    organization_id: uuid.UUID,
    product_code: str,
):
    decision = evaluate_privileged_operation(context.auth_session, operation, now=utcnow())
    record_security_event(
        db,
        event_type="data.privileged_operation",
        outcome="allow" if decision.allowed else "deny",
        user_id=context.user.id,
        metadata={
            "operation_code": decision.operation_code,
            "organization_id": str(organization_id),
            "product_code": product_code,
            "reason": decision.reason.value,
            "required_assurance": decision.required_assurance.value,
            "satisfied_by": decision.satisfied_by.value if decision.satisfied_by else None,
        },
    )
    if not decision.allowed:
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="step_up_authentication_required")
    return decision


def _dispatch_or_503(job_id: uuid.UUID) -> None:
    try:
        dispatch_job(job_id)
    except DataQueueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="data job queue unavailable") from exc


@router.get("/sources", response_model=list[SourceSummaryResponse])
def get_sources(
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
        permission_code="data.read",
    )
    try:
        return list_sources(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/sources", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def post_source(
    payload: UploadCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.upload",
    )
    settings = get_settings()
    try:
        raw = decode_upload(payload.content_base64, max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)))
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        source, version, job, reused = create_source_upload(
            db,
            build_storage(),
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            source_name=payload.source_name,
            filename=payload.filename,
            content_type=payload.content_type,
            payload=raw,
            actor_id=actor_id,
            backend=getattr(settings, "data_job_backend", "inline"),
        )
        db.commit()
        job_id = job.id
        _dispatch_or_503(job_id)
        db.expire_all()
        source = get_scoped_source(
            db,
            source_id=source.id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        version = db.get(DataSourceVersion, version.id)
        job = db.get(IngestionJob, job_id)
        return UploadResponse(
            source=source_summary(db, source),
            version=source_detail(db, source).versions[0] if version is not None else source_summary(db, source).latest_version,
            job=job_response(job),
            storage_reused=reused,
        )
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/sources/{source_id}", response_model=SourceDetailResponse)
def get_source(
    source_id: uuid.UUID,
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
        permission_code="data.read",
    )
    try:
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
        return source_detail(db, source)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/sources/{source_id}/versions", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def post_source_version(
    source_id: uuid.UUID,
    payload: VersionCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.upload",
    )
    settings = get_settings()
    try:
        raw = decode_upload(payload.content_base64, max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)))
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
        version, job, reused = create_source_version(
            db,
            build_storage(),
            source=source,
            filename=payload.filename,
            content_type=payload.content_type,
            payload=raw,
            actor_id=actor_id,
            backend=getattr(settings, "data_job_backend", "inline"),
        )
        db.commit()
        _dispatch_or_503(job.id)
        db.expire_all()
        source = get_scoped_source(
            db,
            source_id=source_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        latest = source_detail(db, source).versions[0]
        refreshed_job = db.get(IngestionJob, job.id)
        return UploadResponse(source=source_summary(db, source), version=latest, job=job_response(refreshed_job), storage_reused=reused)
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/versions/{version_id}/validate", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
def validate_version(
    version_id: uuid.UUID,
    payload: ScopeQuery,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.validate",
    )
    version = db.scalar(
        select(DataSourceVersion).where(
            DataSourceVersion.id == version_id,
            DataSourceVersion.organization_id == payload.organization_id,
            DataSourceVersion.workspace_id == payload.workspace_id,
            DataSourceVersion.product_code == payload.product_code,
        )
    )
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version_not_accessible")
    settings = get_settings()
    actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
    job = create_validation_job(db, version=version, actor_id=actor_id, backend=getattr(settings, "data_job_backend", "inline"))
    db.commit()
    _dispatch_or_503(job.id)
    db.expire_all()
    return job_response(db.get(IngestionJob, job.id))


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_job(
    job_id: uuid.UUID,
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
        permission_code="data.read",
    )
    job = db.scalar(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.organization_id == organization_id,
            IngestionJob.workspace_id == workspace_id,
            IngestionJob.product_code == product_code,
        )
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_accessible")
    return job_response(job)


@router.get("/sources/{source_id}/governance", response_model=SourceGovernanceResponse)
def read_source_governance(
    source_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return get_source_governance(db, source_id=source_id, organization_id=organization_id,
                                     workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.put("/sources/{source_id}/governance", response_model=SourceGovernanceResponse)
def put_source_governance(
    source_id: uuid.UUID, payload: SourceGovernanceUpdate,
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.governance.manage")
    try:
        result = update_source_governance(
            db, source_id=source_id, organization_id=organization_id, workspace_id=workspace_id,
            product_code=product_code, update=payload,
            actor_id=actor_membership_id(db, user_id=context.user.id, organization_id=organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/retention-policies", response_model=list[RetentionPolicyResponse])
def get_retention_policies(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_retention_policies(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/retention-policies", response_model=RetentionPolicyResponse, status_code=status.HTTP_201_CREATED)
def post_retention_policy(
    payload: RetentionPolicyCreate,
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.governance.manage")
    try:
        result = create_retention_policy(
            db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
            payload=payload, actor_id=actor_membership_id(db, user_id=context.user.id, organization_id=organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/versions/{version_id}/retention", response_model=RetentionStateResponse)
def read_version_retention(
    version_id: uuid.UUID,
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return get_retention_state(db, version_id=version_id, organization_id=organization_id,
                                   workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


def _retention_mutation(db: Session, context: AuthContext, version_id: uuid.UUID,
                        payload: RetentionMutationRequest, operation: str) -> RetentionStateResponse:
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
    if operation in {"approve", "execute"}:
        _step_up(db, context, operation=PrivilegedOperation.DESTRUCTIVE_ADMINISTRATION,
                 organization_id=payload.organization_id, product_code=payload.product_code)
    kwargs = dict(version_id=version_id, organization_id=payload.organization_id,
                  workspace_id=payload.workspace_id, product_code=payload.product_code,
                  expected_revision=payload.expected_revision, actor_id=actor_id)
    try:
        if operation == "release":
            result = release_hold(db, **kwargs)
        elif operation == "request":
            result = request_purge(db, **kwargs)
        elif operation == "approve":
            result = approve_purge(db, **kwargs)
        else:
            result = execute_purge(db, build_storage(), **kwargs)
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        if operation == "execute" and str(exc) == "storage_operation_failed":
            record_purge_storage_failure(db, **kwargs)
            db.commit()
        raise _platform_error(exc) from None


@router.post("/versions/{version_id}/hold", response_model=RetentionStateResponse)
def post_hold(version_id: uuid.UUID, payload: HoldPlaceRequest,
              context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = place_hold(
            db, version_id=version_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, expected_revision=payload.expected_revision,
            reason_reference=payload.reason_reference,
            actor_id=actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/versions/{version_id}/hold/release", response_model=RetentionStateResponse)
def post_hold_release(version_id: uuid.UUID, payload: RetentionMutationRequest,
                      context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    return _retention_mutation(db, context, version_id, payload, "release")


@router.post("/versions/{version_id}/purge/request", response_model=RetentionStateResponse)
def post_purge_request(version_id: uuid.UUID, payload: RetentionMutationRequest,
                       context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    return _retention_mutation(db, context, version_id, payload, "request")


@router.post("/versions/{version_id}/purge/approve", response_model=RetentionStateResponse)
def post_purge_approve(version_id: uuid.UUID, payload: RetentionMutationRequest,
                       context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    return _retention_mutation(db, context, version_id, payload, "approve")


@router.post("/versions/{version_id}/purge/execute", response_model=RetentionStateResponse)
def post_purge_execute(version_id: uuid.UUID, payload: RetentionMutationRequest,
                       context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    return _retention_mutation(db, context, version_id, payload, "execute")


@router.post("/anonymization-records", response_model=AnonymizationRecordResponse, status_code=status.HTTP_201_CREATED)
def post_anonymization(payload: AnonymizationProposalCreate,
                       context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = propose_anonymization(
            db, payload=payload,
            actor_id=actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/anonymization-records/{record_id}/review", response_model=AnonymizationRecordResponse)
def post_anonymization_review(record_id: uuid.UUID, payload: AnonymizationReviewRequest,
                              context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = review_anonymization(
            db, record_id=record_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, decision=payload.decision,
            review_reference=payload.review_reference, review_reason=payload.review_reason,
            actor_id=actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/versions/{version_id}/export")
def post_version_export(version_id: uuid.UUID, payload: ExportRequest,
                        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.export")
    actor_id = actor_membership_id(db, user_id=context.user.id, organization_id=payload.organization_id)
    try:
        version, profile, retention, _ = inspect_export(
            db, version_id=version_id, organization_id=payload.organization_id,
            workspace_id=payload.workspace_id, product_code=payload.product_code,
        )
        sensitive = validate_export_policy(
            db, version=version, profile=profile, state=retention,
            purpose_reference=payload.purpose_reference, actor_id=actor_id,
        )
        decision = None
        if sensitive:
            if not has_permission(db, context.user.id, payload.organization_id,
                                  "data.governance.manage", payload.product_code):
                record_export_denial(
                    db, version=version, profile=profile, purpose_reference=payload.purpose_reference,
                    actor_id=actor_id, result_code="sensitive_export_governance_permission_required",
                )
                db.commit()
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="sensitive_export_governance_permission_required")
            try:
                decision = _step_up(
                    db, context, operation=PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION,
                    organization_id=payload.organization_id, product_code=payload.product_code,
                )
            except HTTPException:
                record_export_denial(
                    db, version=version, profile=profile, purpose_reference=payload.purpose_reference,
                    actor_id=actor_id, result_code="step_up_authentication_required",
                )
                db.commit()
                raise
        raw, manifest = export_source_version(
            db, build_storage(), version_id=version_id, organization_id=payload.organization_id,
            workspace_id=payload.workspace_id, product_code=payload.product_code,
            purpose_reference=payload.purpose_reference, actor_id=actor_id,
            assurance_method=decision.satisfied_by.value if decision and decision.satisfied_by else "",
            assurance_reference=decision.operation_code if decision else "",
        )
        db.commit()
        return Response(
            content=raw, media_type=version.content_type,
            headers={"X-Data-Export-Manifest-ID": str(manifest.id)},
        )
    except HTTPException:
        raise
    except DataPlatformError as exc:
        if str(exc) == "storage_operation_failed":
            db.rollback()
            record_export_failure(
                db, version_id=version_id, organization_id=payload.organization_id,
                workspace_id=payload.workspace_id, product_code=payload.product_code,
                purpose_reference=payload.purpose_reference, actor_id=actor_id,
            )
            db.commit()
        else:
            # Policy-level denials are bounded, scoped, auditable attempts.
            db.commit()
        raise _platform_error(exc) from None
