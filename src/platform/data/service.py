from __future__ import annotations

import base64
import binascii
import uuid
from pathlib import Path

from sqlalchemy import delete, func, select, update as sql_update
from sqlalchemy.orm import Session

from src.platform.data.governance import (
    AIUsePolicy,
    DEFAULT_AI_USE_POLICY,
    DEFAULT_CLASSIFICATION,
    DEFAULT_EXPORT_POLICY,
    DEFAULT_GOVERNANCE_STATE,
    DEFAULT_PRIVACY_CATEGORY,
    EXPORT_POLICY_PROHIBITED,
    DataClassification,
    GovernanceState,
    PrivacyCategory,
)
from src.platform.data.models import (
    DataAuditEvent,
    DataQualityResult,
    DataRetentionPolicy,
    DataRetentionState,
    DataSource,
    DataSourceGovernanceProfile,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.schemas import (
    IngestionJobResponse,
    QualityResultResponse,
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionStateResponse,
    SourceDetailResponse,
    SourceGovernanceResponse,
    SourceGovernanceUpdate,
    SourceSummaryResponse,
    UploadResponse,
    VersionResponse,
)
from src.platform.data.storage import StorageBackend, digest_bytes, scoped_storage_key
from src.platform.identity.models import Membership
from src.platform.workspaces.models import Workspace


class DataPlatformError(ValueError):
    pass


DATASET_EXTENSIONS = {"csv", "json", "xlsx"}
DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt"}
ALLOWED_EXTENSIONS = DATASET_EXTENSIONS | DOCUMENT_EXTENSIONS


def actor_membership_id(session: Session, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> uuid.UUID | None:
    membership = session.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
    )
    return membership.id if membership is not None else None


def validate_scope(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> Workspace:
    if product_code not in {"SIMPA", "ORDO"}:
        raise DataPlatformError("unsupported_product")
    workspace = session.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.organization_id == organization_id,
            Workspace.product_code == product_code,
            Workspace.status == "active",
        )
    )
    if workspace is None:
        raise DataPlatformError("workspace_scope_mismatch")
    return workspace


def decode_upload(content_base64: str, *, max_bytes: int) -> bytes:
    try:
        payload = base64.b64decode(content_base64.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise DataPlatformError("invalid_base64") from exc
    if not payload:
        raise DataPlatformError("empty_upload")
    if len(payload) > max_bytes:
        raise DataPlatformError("upload_too_large")
    return payload


def safe_filename(filename: str) -> tuple[str, str]:
    name = Path(filename.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."}:
        raise DataPlatformError("invalid_filename")
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise DataPlatformError("unsupported_format")
    return name[:500], ext


def _audit(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID,
    detail: str,
) -> None:
    session.add(
        DataAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail[:4000],
        )
    )


def _version_response(session: Session, version: DataSourceVersion) -> VersionResponse:
    quality_rows = session.scalars(
        select(DataQualityResult)
        .where(DataQualityResult.version_id == version.id)
        .order_by(DataQualityResult.check_code, DataQualityResult.id)
    ).all()
    return VersionResponse(
        id=version.id,
        version_no=version.version_no,
        original_filename=version.original_filename,
        extension=version.extension,
        content_type=version.content_type,
        size_bytes=version.size_bytes,
        sha256=version.sha256,
        ingest_status=version.ingest_status,
        detected_format=version.detected_format,
        row_count=version.row_count,
        column_count=version.column_count,
        sheet_count=version.sheet_count,
        schema_fingerprint=version.schema_fingerprint,
        created_at=version.created_at,
        quality=[
            QualityResultResponse(
                check_code=row.check_code,
                status=row.status,
                message=row.message,
                metric_name=row.metric_name,
                metric_value=row.metric_value,
            )
            for row in quality_rows
        ],
    )


def _latest_version(session: Session, source_id: uuid.UUID) -> DataSourceVersion | None:
    return session.scalar(
        select(DataSourceVersion)
        .where(DataSourceVersion.source_id == source_id)
        .order_by(DataSourceVersion.version_no.desc())
        .limit(1)
    )


def source_summary(session: Session, source: DataSource) -> SourceSummaryResponse:
    latest = _latest_version(session, source.id)
    return SourceSummaryResponse(
        id=source.id,
        name=source.name,
        source_kind=source.source_kind,
        product_code=source.product_code,
        workspace_id=source.workspace_id,
        status=source.status,
        created_at=source.created_at,
        latest_version=_version_response(session, latest) if latest else None,
    )


def source_detail(session: Session, source: DataSource) -> SourceDetailResponse:
    versions = session.scalars(
        select(DataSourceVersion)
        .where(DataSourceVersion.source_id == source.id)
        .order_by(DataSourceVersion.version_no.desc())
    ).all()
    latest = versions[0] if versions else None
    return SourceDetailResponse(
        id=source.id,
        name=source.name,
        source_kind=source.source_kind,
        product_code=source.product_code,
        workspace_id=source.workspace_id,
        status=source.status,
        created_at=source.created_at,
        latest_version=_version_response(session, latest) if latest else None,
        versions=[_version_response(session, version) for version in versions],
    )


def job_response(job: IngestionJob) -> IngestionJobResponse:
    return IngestionJobResponse(
        id=job.id,
        version_id=job.version_id,
        job_type=job.job_type,
        status=job.status,
        backend=job.backend,
        progress=job.progress,
        attempts=job.attempts,
        error_code=job.error_code,
        error_message=job.error_message,
        queued_at=job.queued_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def list_sources(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[SourceSummaryResponse]:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    rows = session.scalars(
        select(DataSource)
        .where(
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
        .order_by(DataSource.created_at.desc(), DataSource.id)
    ).all()
    return [source_summary(session, row) for row in rows]


def get_scoped_source(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> DataSource:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    source = session.scalar(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
    )
    if source is None:
        raise DataPlatformError("source_not_accessible")
    return source


def governance_response(profile: DataSourceGovernanceProfile) -> SourceGovernanceResponse:
    return SourceGovernanceResponse(
        id=profile.id,
        source_id=profile.source_id,
        organization_id=profile.organization_id,
        workspace_id=profile.workspace_id,
        product_code=profile.product_code,
        classification=profile.classification,
        privacy_category=profile.privacy_category,
        processing_purpose=profile.processing_purpose,
        data_owner_ref=profile.data_owner_ref,
        data_steward_membership_id=profile.data_steward_membership_id,
        retention_policy_id=profile.retention_policy_id,
        ai_use_policy=profile.ai_use_policy,
        export_policy=profile.export_policy,
        governance_state=profile.governance_state,
        classification_rationale=profile.classification_rationale,
        revision=profile.revision,
        created_by_membership_id=profile.created_by_membership_id,
        updated_by_membership_id=profile.updated_by_membership_id,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def get_source_governance(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> SourceGovernanceResponse:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    profile = session.scalar(
        select(DataSourceGovernanceProfile).where(
            DataSourceGovernanceProfile.source_id == source.id,
            DataSourceGovernanceProfile.organization_id == source.organization_id,
            DataSourceGovernanceProfile.workspace_id == source.workspace_id,
            DataSourceGovernanceProfile.product_code == source.product_code,
        )
    )
    if profile is None:
        raise DataPlatformError("governance_profile_missing")
    return governance_response(profile)


def _validated_governance_values(values: dict[str, object]) -> None:
    try:
        DataClassification(str(values["classification"]))
        PrivacyCategory(str(values["privacy_category"]))
        AIUsePolicy(str(values["ai_use_policy"]))
        GovernanceState(str(values["governance_state"]))
    except ValueError as exc:
        raise DataPlatformError("invalid_governance_value") from exc
    if values["export_policy"] != EXPORT_POLICY_PROHIBITED:
        raise DataPlatformError("invalid_export_policy")
    if values["governance_state"] in {GovernanceState.GOVERNED, GovernanceState.FROZEN} and (
        values["classification"] == DataClassification.UNCLASSIFIED
        or values["privacy_category"] == PrivacyCategory.UNKNOWN
        or not str(values["processing_purpose"]).strip()
        or not str(values["data_owner_ref"]).strip()
    ):
        raise DataPlatformError("governance_profile_incomplete")


def update_source_governance(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    update: SourceGovernanceUpdate,
    actor_id: uuid.UUID | None,
) -> SourceGovernanceResponse:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == source.id))
    if profile is None:
        raise DataPlatformError("governance_profile_missing")
    if (profile.organization_id, profile.workspace_id, profile.product_code) != (
        source.organization_id,
        source.workspace_id,
        source.product_code,
    ):
        raise DataPlatformError("governance_scope_mismatch")
    if update.expected_revision != profile.revision:
        raise DataPlatformError("governance_revision_conflict")

    supplied = update.model_fields_set
    if "data_steward_membership_id" in supplied and update.data_steward_membership_id is not None:
        steward = session.scalar(
            select(Membership).where(
                Membership.id == update.data_steward_membership_id,
                Membership.organization_id == source.organization_id,
                Membership.status == "active",
            )
        )
        if steward is None:
            raise DataPlatformError("invalid_data_steward")
    if "retention_policy_id" in supplied and update.retention_policy_id is not None:
        policy = session.scalar(
            select(DataRetentionPolicy).where(
                DataRetentionPolicy.id == update.retention_policy_id,
                DataRetentionPolicy.organization_id == source.organization_id,
                DataRetentionPolicy.workspace_id == source.workspace_id,
                DataRetentionPolicy.product_code == source.product_code,
                DataRetentionPolicy.status == "active",
            )
        )
        if policy is None:
            raise DataPlatformError("retention_policy_not_accessible")

    mutable_fields = (
        "classification",
        "privacy_category",
        "processing_purpose",
        "data_owner_ref",
        "data_steward_membership_id",
        "retention_policy_id",
        "ai_use_policy",
        "export_policy",
        "governance_state",
        "classification_rationale",
    )
    candidate = {field: getattr(profile, field) for field in mutable_fields}
    changed_fields: list[str] = []
    for field in mutable_fields:
        if field not in supplied:
            continue
        value = getattr(update, field)
        if field in {"processing_purpose", "data_owner_ref", "classification_rationale"}:
            value = (value or "").strip()
        if value is not None and isinstance(value, (DataClassification, PrivacyCategory, AIUsePolicy, GovernanceState)):
            value = value.value
        candidate[field] = value
        changed_fields.append(field)

    _validated_governance_values(candidate)
    result = session.execute(
        sql_update(DataSourceGovernanceProfile)
        .where(
            DataSourceGovernanceProfile.id == profile.id,
            DataSourceGovernanceProfile.revision == update.expected_revision,
        )
        .values(
            **candidate,
            revision=update.expected_revision + 1,
            updated_by_membership_id=actor_id,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        session.expire(profile)
        raise DataPlatformError("governance_revision_conflict")
    session.refresh(profile)
    _audit(
        session,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        actor_id=actor_id,
        event_type="data.governance.updated",
        entity_type="data_source_governance_profile",
        entity_id=profile.id,
        detail=f"source_id={source.id}; revision={profile.revision}; fields={','.join(sorted(changed_fields))}",
    )
    return governance_response(profile)


def retention_policy_response(policy: DataRetentionPolicy) -> RetentionPolicyResponse:
    return RetentionPolicyResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        workspace_id=policy.workspace_id,
        product_code=policy.product_code,
        policy_code=policy.policy_code,
        version_no=policy.version_no,
        name=policy.name,
        status=policy.status,
        retention_days=policy.retention_days,
        no_auto_delete=policy.no_auto_delete,
        manual_review_required=policy.manual_review_required,
        archive_before_purge=policy.archive_before_purge,
        tombstone_retention_days=policy.tombstone_retention_days,
        reference_text=policy.reference_text,
        created_by_membership_id=policy.created_by_membership_id,
        created_at=policy.created_at,
    )


def create_retention_policy(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    payload: RetentionPolicyCreate,
    actor_id: uuid.UUID | None,
) -> RetentionPolicyResponse:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    policy_code = payload.policy_code.strip()
    existing = session.scalar(
        select(DataRetentionPolicy.id).where(
            DataRetentionPolicy.workspace_id == workspace_id,
            DataRetentionPolicy.policy_code == policy_code,
            DataRetentionPolicy.version_no == payload.version_no,
        )
    )
    if existing is not None:
        raise DataPlatformError("retention_policy_version_exists")
    policy = DataRetentionPolicy(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        policy_code=policy_code,
        version_no=payload.version_no,
        name=payload.name.strip(),
        status=payload.status,
        retention_days=payload.retention_days,
        no_auto_delete=payload.no_auto_delete,
        manual_review_required=payload.manual_review_required,
        archive_before_purge=payload.archive_before_purge,
        tombstone_retention_days=payload.tombstone_retention_days,
        reference_text=payload.reference_text.strip(),
        created_by_membership_id=actor_id,
    )
    session.add(policy)
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="data.retention_policy.created",
        entity_type="data_retention_policy",
        entity_id=policy.id,
        detail=f"policy_code={policy.policy_code}; version_no={policy.version_no}",
    )
    return retention_policy_response(policy)


def list_retention_policies(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[RetentionPolicyResponse]:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    policies = session.scalars(
        select(DataRetentionPolicy)
        .where(
            DataRetentionPolicy.organization_id == organization_id,
            DataRetentionPolicy.workspace_id == workspace_id,
            DataRetentionPolicy.product_code == product_code,
        )
        .order_by(DataRetentionPolicy.policy_code, DataRetentionPolicy.version_no.desc())
    ).all()
    return [retention_policy_response(policy) for policy in policies]


def retention_state_response(state: DataRetentionState) -> RetentionStateResponse:
    return RetentionStateResponse(
        id=state.id,
        version_id=state.version_id,
        source_id=state.source_id,
        organization_id=state.organization_id,
        workspace_id=state.workspace_id,
        product_code=state.product_code,
        retention_start_at=state.retention_start_at,
        retention_due_at=state.retention_due_at,
        hold_active=state.hold_active,
        hold_reason_ref=state.hold_reason_ref,
        purge_requested_at=state.purge_requested_at,
        purge_requested_by_membership_id=state.purge_requested_by_membership_id,
        purge_approved_at=state.purge_approved_at,
        purge_approved_by_membership_id=state.purge_approved_by_membership_id,
        purge_executed_at=state.purge_executed_at,
        purge_executed_by_membership_id=state.purge_executed_by_membership_id,
        purge_result=state.purge_result,
        tombstone_checksum=state.tombstone_checksum,
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


def _create_version(
    session: Session,
    storage: StorageBackend,
    *,
    source: DataSource,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSourceVersion, IngestionJob, bool]:
    safe_name, extension = safe_filename(filename)
    sha256 = digest_bytes(payload)
    storage_key = scoped_storage_key(
        organization_id=str(source.organization_id),
        product_code=source.product_code,
        workspace_id=str(source.workspace_id),
        sha256=sha256,
        extension=extension,
    )
    stored_new = storage.put_bytes(storage_key, payload)
    next_no = (session.scalar(select(func.max(DataSourceVersion.version_no)).where(DataSourceVersion.source_id == source.id)) or 0) + 1
    version = DataSourceVersion(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=next_no,
        original_filename=safe_name,
        extension=extension,
        content_type=(content_type or "application/octet-stream")[:200],
        size_bytes=len(payload),
        sha256=sha256,
        storage_key=storage_key,
        ingest_status="queued",
        created_by_membership_id=actor_id,
    )
    session.add(version)
    session.flush()
    session.add(
        DataRetentionState(
            version_id=version.id,
            source_id=source.id,
            organization_id=source.organization_id,
            workspace_id=source.workspace_id,
            product_code=source.product_code,
            retention_start_at=version.created_at if version.created_at is not None else func.now(),
            retention_due_at=None,
            hold_active=False,
        )
    )
    session.flush()
    job = IngestionJob(
        version_id=version.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        job_type="inspect",
        status="queued",
        backend=backend,
        progress=0,
        created_by_membership_id=actor_id,
    )
    session.add(job)
    session.flush()
    _audit(
        session,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        actor_id=actor_id,
        event_type="data.version.uploaded",
        entity_type="data_source_version",
        entity_id=version.id,
        detail=f"filename={safe_name}; sha256={sha256}; storage_reused={str(not stored_new).lower()}",
    )
    return version, job, not stored_new


def create_source_upload(
    session: Session,
    storage: StorageBackend,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    source_name: str,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSource, DataSourceVersion, IngestionJob, bool]:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    name = " ".join(source_name.split()).strip()
    if not name:
        raise DataPlatformError("source_name_required")
    existing = session.scalar(select(DataSource).where(DataSource.workspace_id == workspace_id, DataSource.name == name))
    if existing is not None:
        raise DataPlatformError("source_name_exists")
    _safe, ext = safe_filename(filename)
    source = DataSource(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        name=name[:300],
        source_kind="dataset" if ext in DATASET_EXTENSIONS else "document",
        status="active",
        created_by_membership_id=actor_id,
    )
    session.add(source)
    session.flush()
    session.add(
        DataSourceGovernanceProfile(
            source_id=source.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            classification=DEFAULT_CLASSIFICATION.value,
            privacy_category=DEFAULT_PRIVACY_CATEGORY.value,
            ai_use_policy=DEFAULT_AI_USE_POLICY.value,
            export_policy=DEFAULT_EXPORT_POLICY,
            governance_state=DEFAULT_GOVERNANCE_STATE.value,
            created_by_membership_id=actor_id,
            updated_by_membership_id=actor_id,
        )
    )
    session.flush()
    _audit(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
        event_type="data.source.created",
        entity_type="data_source",
        entity_id=source.id,
        detail=f"name={source.name}; kind={source.source_kind}",
    )
    version, job, reused = _create_version(
        session,
        storage,
        source=source,
        filename=filename,
        content_type=content_type,
        payload=payload,
        actor_id=actor_id,
        backend=backend,
    )
    return source, version, job, reused


def create_source_version(
    session: Session,
    storage: StorageBackend,
    *,
    source: DataSource,
    filename: str,
    content_type: str,
    payload: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> tuple[DataSourceVersion, IngestionJob, bool]:
    return _create_version(
        session,
        storage,
        source=source,
        filename=filename,
        content_type=content_type,
        payload=payload,
        actor_id=actor_id,
        backend=backend,
    )


def create_validation_job(
    session: Session,
    *,
    version: DataSourceVersion,
    actor_id: uuid.UUID | None,
    backend: str,
) -> IngestionJob:
    job = IngestionJob(
        version_id=version.id,
        organization_id=version.organization_id,
        workspace_id=version.workspace_id,
        product_code=version.product_code,
        job_type="validate",
        status="queued",
        backend=backend,
        progress=0,
        created_by_membership_id=actor_id,
    )
    session.add(job)
    session.flush()
    version.ingest_status = "queued"
    _audit(
        session,
        organization_id=version.organization_id,
        workspace_id=version.workspace_id,
        product_code=version.product_code,
        actor_id=actor_id,
        event_type="data.validation.requested",
        entity_type="data_source_version",
        entity_id=version.id,
        detail=f"job_id={job.id}",
    )
    return job


def replace_quality_results(session: Session, version_id: uuid.UUID, checks) -> None:
    session.execute(delete(DataQualityResult).where(DataQualityResult.version_id == version_id))
    for check in checks:
        session.add(
            DataQualityResult(
                version_id=version_id,
                check_code=check.code,
                status=check.status,
                message=check.message,
                metric_name=check.metric_name,
                metric_value=check.metric_value,
            )
        )
