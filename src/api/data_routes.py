from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import AuthContext, get_auth_context, get_db
from src.core.config import get_settings
from src.platform.access.service import has_permission
from src.platform.app_context.service import AppContextError, resolve_selection
from src.platform.data.models import DataIngestionRun, DataSourceVersion, IngestionJob
from src.platform.data.queue import DataQueueError, dispatch_job
from src.platform.data.schemas import (
    AnalyticalAIEligibilityRequest,
    AnalyticalAIEligibilityResponse,
    AnalyticalDatasetCreate,
    AnalyticalDatasetContractActivationRequest,
    AnalyticalDatasetContractVersionCreate,
    AnalyticalDatasetContractVersionResponse,
    AnalyticalDatasetResponse,
    AnalyticalFeatureCreate,
    AnalyticalFeatureResponse,
    AnalyticalFeatureVersionCreate,
    AnalyticalFeatureVersionResponse,
    AnalyticalLineageResponse,
    AnalyticalSnapshotCreate,
    AnalyticalSnapshotResponse,
    AnalyticalTransitionRequest,
    AnonymizationProposalCreate,
    AnonymizationRecordResponse,
    AnonymizationReviewRequest,
    ConnectorContractActivationRequest,
    ConnectorContractVersionCreate,
    ConnectorContractVersionResponse,
    ExportRequest,
    FeatureTransitionRequest,
    HoldPlaceRequest,
    GovernedIngestionOutputResponse,
    IngestionBackfillCreate,
    IngestionDeadLetterRequeueRequest,
    IngestionDeadLetterResolveRequest,
    IngestionDeadLetterResponse,
    IngestionEvaluationResponse,
    IngestionJobResponse,
    IngestionOperationalPolicyActivationRequest,
    IngestionOperationalPolicyVersionCreate,
    IngestionOperationalPolicyVersionResponse,
    IngestionReplayCreate,
    IngestionRunCreate,
    IngestionRunCreateResponse,
    IngestionRunResponse,
    IngestionRunRetryRequest,
    RecordGovernancePolicyActivationRequest,
    RecordGovernancePolicyVersionCreate,
    RecordGovernancePolicyVersionResponse,
    RecordQuarantineDetailResponse,
    RecordQuarantineListItem,
    RecordResolutionCreate,
    RecordResolutionResponse,
    ScopeQuery,
    RetentionMutationRequest,
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionStateResponse,
    SourceGovernanceResponse,
    SourceGovernanceUpdate,
    SourceDetailResponse,
    SourceSchemaMappingActivationRequest,
    SourceSchemaMappingVersionCreate,
    SourceSchemaMappingVersionResponse,
    SourceSummaryResponse,
    UploadCreateRequest,
    UploadResponse,
    VersionCreateRequest,
)
from src.platform.data.connector_service import (
    activate_connector_contract_version,
    create_connector_contract_version,
    list_connector_contract_versions,
)
from src.platform.data.schema_mapping_service import (
    activate_source_schema_mapping_version,
    create_source_schema_mapping_version,
    list_source_schema_mapping_versions,
)
from src.platform.data.ingestion_run_service import (
    create_backfill_ingestion_run,
    create_ingestion_run,
    create_replay_ingestion_run,
    get_ingestion_run as get_ingestion_run_service,
    list_ingestion_runs,
    retry_ingestion_run,
)
from src.platform.data.ingestion_operations_service import (
    activate_ingestion_operational_policy_version,
    create_ingestion_operational_policy_version,
    get_governed_ingestion_output,
    get_ingestion_evaluation,
    list_ingestion_dead_letters,
    list_ingestion_operational_policy_versions,
    requeue_ingestion_dead_letter,
    resolve_ingestion_dead_letter,
)
from src.platform.data.record_governance_service import (
    activate_record_governance_policy_version,
    create_record_governance_policy_version,
    get_record_quarantine_detail as get_record_quarantine_detail_service,
    list_record_governance_policy_versions,
    list_record_quarantine,
    resolve_quarantined_record,
)
from src.platform.data.analytical_service import (
    activate_analytical_dataset_contract_version,
    create_analytical_dataset,
    create_analytical_dataset_contract_version,
    create_analytical_feature,
    create_analytical_feature_version,
    create_analytical_snapshot,
    evaluate_analytical_ai_eligibility,
    get_analytical_lineage,
    list_analytical_datasets,
    list_analytical_dataset_contract_versions,
    list_analytical_feature_versions,
    list_analytical_features,
    list_analytical_snapshots,
    transition_analytical_feature_version,
    transition_analytical_snapshot,
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
    if code in {"source_not_accessible", "version_not_accessible", "anonymization_record_not_accessible", "workspace_scope_mismatch",
                "analytical_dataset_not_accessible", "analytical_snapshot_not_accessible",
                "analytical_feature_not_accessible", "analytical_feature_version_not_accessible",
                "analytical_contract_version_not_accessible",
                "connector_contract_version_not_accessible", "schema_mapping_version_not_accessible",
                "ingestion_run_not_accessible", "record_policy_version_not_accessible",
                "record_quarantine_not_accessible", "operational_policy_version_not_accessible",
                "ingestion_evaluation_not_accessible", "governed_ingestion_output_not_accessible",
                "ingestion_dead_letter_not_accessible"}:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code)
    if code in {"upload_too_large"}:
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=code)
    if code in {"source_name_exists", "governance_revision_conflict", "retention_revision_conflict", "purge_state_conflict", "anonymization_state_conflict",
                "analytical_dataset_code_exists", "analytical_feature_code_exists", "analytical_revision_conflict",
                "analytical_contract_unchanged", "analytical_contract_version_conflict",
                "analytical_contract_state_conflict",
                "connector_contract_state_conflict", "connector_contract_unchanged",
                "schema_mapping_state_conflict", "schema_mapping_unchanged",
                "schema_mapping_connector_retired", "schema_mapping_connector_not_active",
                "ingestion_run_connector_not_active", "ingestion_run_mapping_not_active",
                "ingestion_run_contract_mismatch", "ingestion_run_idempotency_conflict",
                "ingestion_run_duplicate_batch", "ingestion_run_active_conflict",
                "ingestion_run_retry_required", "ingestion_run_retry_state_conflict",
                "ingestion_run_content_unavailable", "ingestion_run_execution_integrity_failed",
                "record_policy_state_conflict", "record_policy_unchanged",
                "record_policy_connector_retired", "record_policy_mapping_retired",
                "record_policy_connector_not_active", "record_policy_mapping_not_active",
                "record_policy_binding_mismatch", "record_policy_integrity_failed",
                "record_policy_mapping_integrity_failed", "record_resolution_state_conflict",
                "record_resolution_accept_forbidden", "record_resolution_integrity_failed",
                "operational_policy_state_conflict", "operational_policy_unchanged",
                "operational_policy_binding_mismatch", "operational_policy_connector_not_active",
                "operational_policy_mapping_not_active", "operational_policy_record_policy_not_active",
                "operational_policy_integrity_failed", "operational_policy_required",
                "ingestion_backfill_not_allowed", "ingestion_replay_not_allowed",
                "ingestion_replay_legacy_run_forbidden", "ingestion_replay_content_integrity_failed",
                "governed_output_decision_conflict", "governed_output_requires_governed_run",
                "ingestion_dead_letter_state_conflict"}:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code)
    if code in {"connector_secret_material_forbidden", "invalid_connector_credential_reference"}:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)
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


@router.post(
    "/sources/{source_id}/ingestion-runs",
    response_model=IngestionRunCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_ingestion_run(
    source_id: uuid.UUID,
    payload: IngestionRunCreate,
    response: Response,
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
        raw = decode_upload(
            payload.content_base64,
            max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)),
        )
        result = create_ingestion_run(
            db,
            build_storage(),
            source_id=source_id,
            request=payload,
            payload_bytes=raw,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
            backend=getattr(settings, "data_job_backend", "inline"),
        )
        db.commit()
        response.status_code = status.HTTP_200_OK if result.reused else status.HTTP_201_CREATED
        if not result.reused or result.run.status == "QUEUED":
            _dispatch_or_503(result.run.inspection_job_id)
        db.expire_all()
        refreshed = get_ingestion_run_service(
            db,
            source_id=source_id,
            run_id=result.run.id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
        return IngestionRunCreateResponse(run=refreshed, reused=result.reused)
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/ingestion-runs",
    response_model=list[IngestionRunResponse],
)
def get_ingestion_runs(
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
        return list_ingestion_runs(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/ingestion-runs/{run_id}",
    response_model=IngestionRunResponse,
)
def get_ingestion_run(
    source_id: uuid.UUID,
    run_id: uuid.UUID,
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
        return get_ingestion_run_service(
            db,
            source_id=source_id,
            run_id=run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/ingestion-runs/{run_id}/retry",
    response_model=IngestionRunResponse,
)
def post_ingestion_run_retry(
    source_id: uuid.UUID,
    run_id: uuid.UUID,
    payload: IngestionRunRetryRequest,
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
    try:
        result = retry_ingestion_run(
            db,
            source_id=source_id,
            run_id=run_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        _dispatch_or_503(result.inspection_job_id)
        db.expire_all()
        return get_ingestion_run_service(
            db,
            source_id=source_id,
            run_id=run_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
        )
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-operational-policy-versions",
             response_model=IngestionOperationalPolicyVersionResponse,
             status_code=status.HTTP_201_CREATED)
def post_ingestion_operational_policy_version(source_id: uuid.UUID,
        payload: IngestionOperationalPolicyVersionCreate,
        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    try:
        result = create_ingestion_operational_policy_version(db, source_id=source_id,
            payload=payload, actor_id=actor_membership_id(db, user_id=context.user.id,
                                                         organization_id=payload.organization_id))
        db.commit(); return result
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.get("/sources/{source_id}/ingestion-operational-policy-versions",
            response_model=list[IngestionOperationalPolicyVersionResponse])
def get_ingestion_operational_policy_versions(source_id: uuid.UUID,
        organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
        product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_ingestion_operational_policy_versions(db, source_id=source_id,
            organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-operational-policy-versions/{policy_version_id}/activate",
             response_model=IngestionOperationalPolicyVersionResponse)
def post_ingestion_operational_policy_activation(source_id: uuid.UUID,
        policy_version_id: uuid.UUID, payload: IngestionOperationalPolicyActivationRequest,
        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    try:
        result = activate_ingestion_operational_policy_version(db, source_id=source_id,
            policy_version_id=policy_version_id, organization_id=payload.organization_id,
            workspace_id=payload.workspace_id, product_code=payload.product_code,
            actor_id=actor_membership_id(db, user_id=context.user.id,
                                         organization_id=payload.organization_id))
        db.commit(); return result
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-runs/backfill",
             response_model=IngestionRunCreateResponse, status_code=status.HTTP_201_CREATED)
def post_backfill_ingestion_run(source_id: uuid.UUID, payload: IngestionBackfillCreate,
        response: Response, context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.upload")
    settings = get_settings()
    try:
        raw = decode_upload(payload.content_base64,
            max_bytes=int(getattr(settings, "data_max_upload_bytes", 16777216)))
        result = create_backfill_ingestion_run(db, build_storage(), source_id=source_id,
            request=payload, payload_bytes=raw,
            actor_id=actor_membership_id(db, user_id=context.user.id,
                                         organization_id=payload.organization_id),
            backend=getattr(settings, "data_job_backend", "inline"))
        db.commit(); response.status_code = status.HTTP_200_OK if result.reused else status.HTTP_201_CREATED
        if not result.reused or result.run.status == "QUEUED": _dispatch_or_503(result.run.inspection_job_id)
        db.expire_all()
        refreshed = get_ingestion_run_service(db, source_id=source_id, run_id=result.run.id,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code)
        return IngestionRunCreateResponse(run=refreshed, reused=result.reused)
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-runs/{run_id}/replay",
             response_model=IngestionRunCreateResponse, status_code=status.HTTP_201_CREATED)
def post_replay_ingestion_run(source_id: uuid.UUID, run_id: uuid.UUID,
        payload: IngestionReplayCreate, response: Response,
        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.upload")
    settings = get_settings()
    try:
        result = create_replay_ingestion_run(db, build_storage(), source_id=source_id,
            run_id=run_id, request=payload,
            actor_id=actor_membership_id(db, user_id=context.user.id,
                                         organization_id=payload.organization_id),
            backend=getattr(settings, "data_job_backend", "inline"))
        db.commit(); response.status_code = status.HTTP_200_OK if result.reused else status.HTTP_201_CREATED
        if not result.reused or result.run.status == "QUEUED": _dispatch_or_503(result.run.inspection_job_id)
        db.expire_all()
        refreshed = get_ingestion_run_service(db, source_id=source_id, run_id=result.run.id,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code)
        return IngestionRunCreateResponse(run=refreshed, reused=result.reused)
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.get("/sources/{source_id}/ingestion-runs/{run_id}/evaluation",
            response_model=IngestionEvaluationResponse)
def get_run_evaluation(source_id: uuid.UUID, run_id: uuid.UUID,
        organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
        product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return get_ingestion_evaluation(db, source_id=source_id, run_id=run_id,
            organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc: raise _platform_error(exc) from None


@router.get("/sources/{source_id}/ingestion-runs/{run_id}/governed-output",
            response_model=GovernedIngestionOutputResponse)
def get_run_governed_output(source_id: uuid.UUID, run_id: uuid.UUID,
        organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
        product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return get_governed_ingestion_output(db, source_id=source_id, run_id=run_id,
            organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc: raise _platform_error(exc) from None


@router.get("/sources/{source_id}/ingestion-dead-letters",
            response_model=list[IngestionDeadLetterResponse])
def get_source_ingestion_dead_letters(source_id: uuid.UUID,
        organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
        product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_ingestion_dead_letters(db, source_id=source_id,
            organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc: raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-dead-letters/{dead_letter_id}/requeue",
             response_model=IngestionDeadLetterResponse)
def post_ingestion_dead_letter_requeue(source_id: uuid.UUID, dead_letter_id: uuid.UUID,
        payload: IngestionDeadLetterRequeueRequest,
        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    settings = get_settings()
    try:
        result = requeue_ingestion_dead_letter(db, build_storage(), source_id=source_id,
            dead_letter_id=dead_letter_id, request=payload,
            actor_id=actor_membership_id(db, user_id=context.user.id,
                                         organization_id=payload.organization_id),
            backend=getattr(settings, "data_job_backend", "inline"))
        replacement = db.get(DataIngestionRun, result.replacement_run_id)
        db.commit()
        if replacement is not None: _dispatch_or_503(replacement.inspection_job_id)
        return result
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.post("/sources/{source_id}/ingestion-dead-letters/{dead_letter_id}/resolve",
             response_model=IngestionDeadLetterResponse)
def post_ingestion_dead_letter_resolve(source_id: uuid.UUID, dead_letter_id: uuid.UUID,
        payload: IngestionDeadLetterResolveRequest,
        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    try:
        result = resolve_ingestion_dead_letter(db, source_id=source_id,
            dead_letter_id=dead_letter_id, request=payload,
            actor_id=actor_membership_id(db, user_id=context.user.id,
                                         organization_id=payload.organization_id))
        db.commit(); return result
    except DataPlatformError as exc:
        db.rollback(); raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/connector-contracts/versions",
    response_model=ConnectorContractVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_connector_contract_version(
    source_id: uuid.UUID,
    payload: ConnectorContractVersionCreate,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = create_connector_contract_version(
            db,
            source_id=source_id,
            payload=payload,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/connector-contracts",
    response_model=list[ConnectorContractVersionResponse],
)
def get_connector_contract_versions(
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
        return list_connector_contract_versions(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/connector-contracts/{version_id}/activate",
    response_model=ConnectorContractVersionResponse,
)
def post_connector_contract_activation(
    source_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: ConnectorContractActivationRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = activate_connector_contract_version(
            db,
            source_id=source_id,
            version_id=version_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/schema-mappings/versions",
    response_model=SourceSchemaMappingVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_source_schema_mapping_version(
    source_id: uuid.UUID,
    payload: SourceSchemaMappingVersionCreate,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = create_source_schema_mapping_version(
            db,
            source_id=source_id,
            payload=payload,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/schema-mappings",
    response_model=list[SourceSchemaMappingVersionResponse],
)
def get_source_schema_mapping_versions(
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
        return list_source_schema_mapping_versions(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/schema-mappings/{version_id}/activate",
    response_model=SourceSchemaMappingVersionResponse,
)
def post_source_schema_mapping_activation(
    source_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: SourceSchemaMappingActivationRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = activate_source_schema_mapping_version(
            db,
            source_id=source_id,
            version_id=version_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/record-policies/versions",
    response_model=RecordGovernancePolicyVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_record_governance_policy_version(
    source_id: uuid.UUID,
    payload: RecordGovernancePolicyVersionCreate,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = create_record_governance_policy_version(
            db,
            source_id=source_id,
            payload=payload,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/record-policies",
    response_model=list[RecordGovernancePolicyVersionResponse],
)
def get_record_governance_policy_versions(
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
        return list_record_governance_policy_versions(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/record-policies/{policy_id}/activate",
    response_model=RecordGovernancePolicyVersionResponse,
)
def post_record_governance_policy_activation(
    source_id: uuid.UUID,
    policy_id: uuid.UUID,
    payload: RecordGovernancePolicyActivationRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = activate_record_governance_policy_version(
            db,
            source_id=source_id,
            policy_id=policy_id,
            organization_id=payload.organization_id,
            workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/record-quarantine",
    response_model=list[RecordQuarantineListItem],
)
def get_record_quarantine(
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
        permission_code="data.governance.manage",
    )
    try:
        return list_record_quarantine(
            db,
            source_id=source_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.get(
    "/sources/{source_id}/record-quarantine/{record_id}",
    response_model=RecordQuarantineDetailResponse,
)
def get_record_quarantine_detail(
    source_id: uuid.UUID,
    record_id: uuid.UUID,
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
        permission_code="data.governance.manage",
    )
    try:
        return get_record_quarantine_detail_service(
            db,
            source_id=source_id,
            record_id=record_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post(
    "/sources/{source_id}/record-quarantine/{record_id}/resolve",
    response_model=RecordResolutionResponse,
)
def post_record_quarantine_resolution(
    source_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: RecordResolutionCreate,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(
        db,
        context,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
        permission_code="data.governance.manage",
    )
    try:
        result = resolve_quarantined_record(
            db,
            source_id=source_id,
            record_id=record_id,
            payload=payload,
            actor_id=actor_membership_id(
                db,
                user_id=context.user.id,
                organization_id=payload.organization_id,
            ),
        )
        db.commit()
        return result
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


def _analytical_actor(db: Session, context: AuthContext, organization_id: uuid.UUID) -> uuid.UUID | None:
    return actor_membership_id(db, user_id=context.user.id, organization_id=organization_id)


@router.get("/analytical-datasets", response_model=list[AnalyticalDatasetResponse])
def get_analytical_datasets(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    return list_analytical_datasets(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)


@router.post("/analytical-datasets", response_model=AnalyticalDatasetResponse, status_code=status.HTTP_201_CREATED)
def post_analytical_dataset(payload: AnalyticalDatasetCreate,
                            context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = create_analytical_dataset(db, payload=payload,
                                           actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/analytical-datasets/{dataset_id}/contract-versions",
            response_model=list[AnalyticalDatasetContractVersionResponse])
def get_analytical_dataset_contract_versions(
    dataset_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_analytical_dataset_contract_versions(
            db, dataset_id=dataset_id, organization_id=organization_id,
            workspace_id=workspace_id, product_code=product_code,
        )
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/analytical-datasets/{dataset_id}/contract-versions",
             response_model=AnalyticalDatasetContractVersionResponse,
             status_code=status.HTTP_201_CREATED)
def post_analytical_dataset_contract_version(
    dataset_id: uuid.UUID, payload: AnalyticalDatasetContractVersionCreate,
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    try:
        result = create_analytical_dataset_contract_version(
            db, dataset_id=dataset_id, payload=payload,
            actor_id=_analytical_actor(db, context, payload.organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/analytical-datasets/{dataset_id}/contract-versions/{contract_version_id}/activate",
             response_model=AnalyticalDatasetContractVersionResponse)
def post_analytical_dataset_contract_activation(
    dataset_id: uuid.UUID, contract_version_id: uuid.UUID,
    payload: AnalyticalDatasetContractActivationRequest,
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=payload.organization_id,
                   workspace_id=payload.workspace_id, product_code=payload.product_code,
                   permission_code="data.governance.manage")
    try:
        result = activate_analytical_dataset_contract_version(
            db, dataset_id=dataset_id, contract_version_id=contract_version_id,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code,
            actor_id=_analytical_actor(db, context, payload.organization_id),
        )
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/analytical-datasets/{dataset_id}/snapshots", response_model=list[AnalyticalSnapshotResponse])
def get_analytical_snapshots(
    dataset_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_analytical_snapshots(db, dataset_id=dataset_id, organization_id=organization_id,
                                         workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/analytical-datasets/{dataset_id}/snapshots", response_model=AnalyticalSnapshotResponse,
             status_code=status.HTTP_201_CREATED)
def post_analytical_snapshot(dataset_id: uuid.UUID, payload: AnalyticalSnapshotCreate,
                             context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = create_analytical_snapshot(db, dataset_id=dataset_id, payload=payload,
                                            actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/analytical-snapshots/{snapshot_id}/transition", response_model=AnalyticalSnapshotResponse)
def post_analytical_snapshot_transition(snapshot_id: uuid.UUID, payload: AnalyticalTransitionRequest,
                                        context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = transition_analytical_snapshot(
            db, snapshot_id=snapshot_id, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, expected_revision=payload.expected_revision,
            target_state=payload.target_state, actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/analytical-snapshots/{snapshot_id}/lineage", response_model=AnalyticalLineageResponse)
def get_analytical_snapshot_lineage(
    snapshot_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return get_analytical_lineage(db, snapshot_id=snapshot_id, organization_id=organization_id,
                                      workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.get("/analytical-features", response_model=list[AnalyticalFeatureResponse])
def get_analytical_features(
    organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...), product_code: str = Query(...),
    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    return list_analytical_features(db, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)


@router.post("/analytical-features", response_model=AnalyticalFeatureResponse, status_code=status.HTTP_201_CREATED)
def post_analytical_feature(payload: AnalyticalFeatureCreate,
                            context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = create_analytical_feature(db, payload=payload,
                                           actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.get("/analytical-features/{feature_id}/versions", response_model=list[AnalyticalFeatureVersionResponse])
def get_analytical_feature_versions(
    feature_id: uuid.UUID, organization_id: uuid.UUID = Query(...), workspace_id: uuid.UUID = Query(...),
    product_code: str = Query(...), context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db),
):
    _require_scope(db, context, organization_id=organization_id, workspace_id=workspace_id,
                   product_code=product_code, permission_code="data.read")
    try:
        return list_analytical_feature_versions(db, feature_id=feature_id, organization_id=organization_id,
                                                workspace_id=workspace_id, product_code=product_code)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None


@router.post("/analytical-features/{feature_id}/versions", response_model=AnalyticalFeatureVersionResponse,
             status_code=status.HTTP_201_CREATED)
def post_analytical_feature_version(feature_id: uuid.UUID, payload: AnalyticalFeatureVersionCreate,
                                    context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = create_analytical_feature_version(db, feature_id=feature_id, payload=payload,
                                                   actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/analytical-feature-versions/{feature_version_id}/transition",
             response_model=AnalyticalFeatureVersionResponse)
def post_analytical_feature_transition(feature_version_id: uuid.UUID, payload: FeatureTransitionRequest,
                                       context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.governance.manage")
    try:
        result = transition_analytical_feature_version(
            db, feature_version_id=feature_version_id, organization_id=payload.organization_id,
            workspace_id=payload.workspace_id, product_code=payload.product_code,
            expected_revision=payload.expected_revision, target_state=payload.target_state,
            actor_id=_analytical_actor(db, context, payload.organization_id))
        db.commit()
        return result
    except DataPlatformError as exc:
        db.rollback()
        raise _platform_error(exc) from None


@router.post("/analytical-ai/eligibility", response_model=AnalyticalAIEligibilityResponse)
def post_analytical_ai_eligibility(payload: AnalyticalAIEligibilityRequest,
                                   context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    _require_scope(db, context, organization_id=payload.organization_id, workspace_id=payload.workspace_id,
                   product_code=payload.product_code, permission_code="data.read")
    try:
        return evaluate_analytical_ai_eligibility(
            db, artifact_type=payload.artifact_type, artifact_id=payload.artifact_id, action=payload.action,
            organization_id=payload.organization_id, workspace_id=payload.workspace_id,
            product_code=payload.product_code, namespace=payload.namespace)
    except DataPlatformError as exc:
        raise _platform_error(exc) from None
