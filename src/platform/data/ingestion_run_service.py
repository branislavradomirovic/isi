from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.governance import ContentState
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataIngestionRun,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.ingestion_operations_service import (
    get_active_ingestion_operational_policy_for_binding,
    validate_pinned_ingestion_operational_policy,
)
from src.platform.data.record_governance_service import (
    get_active_record_governance_policy_for_binding,
    validate_pinned_record_governance_policy,
)
from src.platform.data.schemas import (
    IngestionBackfillCreate,
    IngestionReplayCreate,
    IngestionRunCreate,
    IngestionRunCreateResponse,
    IngestionRunResponse,
)
from src.platform.data.service import (
    DataPlatformError,
    create_source_version,
    get_scoped_source,
    safe_filename,
)
from src.platform.data.storage import StorageBackend, digest_bytes


_LIVE_STATUSES = ("QUEUED", "RUNNING")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_timestamp(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _normalized_content_type(value: str) -> str:
    normalized = value.strip().lower()
    return (normalized or "application/octet-stream")[:200]


def _normalized_timestamp(value: datetime | None) -> str | None:
    aware = _aware_timestamp(value)
    return aware.astimezone(timezone.utc).isoformat() if aware is not None else None


def _request_fingerprint(
    *,
    source_id: uuid.UUID,
    connector_contract_version_id: uuid.UUID,
    schema_mapping_version_id: uuid.UUID,
    payload_sha256: str,
    extension: str,
    content_type: str,
    cursor_before: str,
    cursor_after: str,
) -> str:
    semantic_batch = {
        "contract_format_version": 1,
        "source_id": str(source_id),
        "connector_contract_version_id": str(connector_contract_version_id),
        "schema_mapping_version_id": str(schema_mapping_version_id),
        "payload_sha256": payload_sha256,
        "extension": extension,
        "content_type": content_type,
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
    }
    return hashlib.sha256(_canonical_json(semantic_batch).encode("utf-8")).hexdigest()


def _backfill_request_fingerprint(*, source_id: uuid.UUID,
        connector_contract_version_id: uuid.UUID, schema_mapping_version_id: uuid.UUID,
        payload_sha256: str, extension: str, content_type: str,
        source_observed_at: datetime | None, window_start_cursor: str,
        window_end_cursor: str) -> str:
    semantic = {"contract_format_version": 1, "execution_mode": "BACKFILL",
        "source_id": str(source_id), "connector_contract_version_id": str(connector_contract_version_id),
        "schema_mapping_version_id": str(schema_mapping_version_id), "payload_sha256": payload_sha256,
        "extension": extension, "content_type": content_type,
        "source_observed_at": _normalized_timestamp(source_observed_at),
        "window_start_cursor": window_start_cursor, "window_end_cursor": window_end_cursor}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _replay_request_fingerprint(*, replay_of_run_id: uuid.UUID, source_id: uuid.UUID,
        connector_contract_version_id: uuid.UUID, schema_mapping_version_id: uuid.UUID,
        record_governance_policy_version_id: uuid.UUID,
        operational_policy_version_id: uuid.UUID, payload_sha256: str) -> str:
    semantic = {"contract_format_version": 1, "execution_mode": "REPLAY",
        "replay_of_run_id": str(replay_of_run_id), "source_id": str(source_id),
        "connector_contract_version_id": str(connector_contract_version_id),
        "schema_mapping_version_id": str(schema_mapping_version_id),
        "record_governance_policy_version_id": str(record_governance_policy_version_id),
        "operational_policy_version_id": str(operational_policy_version_id),
        "payload_sha256": payload_sha256}
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _locked_scoped_source(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> DataSource:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    locked_source = session.scalar(
        select(DataSource)
        .where(
            DataSource.id == source.id,
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
        .with_for_update()
    )
    if locked_source is None:
        raise DataPlatformError("source_not_accessible")
    return locked_source


def _load_pinned_contracts(
    session: Session,
    *,
    source: DataSource,
    connector_contract_version_id: uuid.UUID,
    schema_mapping_version_id: uuid.UUID,
    require_active: bool,
) -> tuple[DataConnectorContractVersion, DataSourceSchemaMappingVersion]:
    connector = session.scalar(
        select(DataConnectorContractVersion).where(
            DataConnectorContractVersion.id == connector_contract_version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
    )
    if connector is None:
        raise DataPlatformError("connector_contract_version_not_accessible")
    mapping = session.scalar(
        select(DataSourceSchemaMappingVersion).where(
            DataSourceSchemaMappingVersion.id == schema_mapping_version_id,
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.organization_id == source.organization_id,
            DataSourceSchemaMappingVersion.workspace_id == source.workspace_id,
            DataSourceSchemaMappingVersion.product_code == source.product_code,
        )
    )
    if mapping is None:
        raise DataPlatformError("schema_mapping_version_not_accessible")
    if require_active and connector.lifecycle_state != "ACTIVE":
        raise DataPlatformError("ingestion_run_connector_not_active")
    if require_active and mapping.lifecycle_state != "ACTIVE":
        raise DataPlatformError("ingestion_run_mapping_not_active")
    if mapping.connector_contract_version_id != connector.id:
        raise DataPlatformError("ingestion_run_contract_mismatch")
    return connector, mapping


def _audit(
    session: Session,
    *,
    run: DataIngestionRun,
    actor_id: uuid.UUID | None,
    event_type: str,
) -> None:
    detail = (
        f"run_no={run.run_no}; connector_contract_version_id={run.connector_contract_version_id}; "
        f"schema_mapping_version_id={run.schema_mapping_version_id}; "
        f"record_governance_policy_version_id={run.record_governance_policy_version_id}; "
        f"source_version_id={run.source_version_id}; inspection_job_id={run.inspection_job_id}; "
        f"status={run.status}; request_fingerprint={run.request_fingerprint}"
    )
    session.add(
        DataAuditEvent(
            organization_id=run.organization_id,
            workspace_id=run.workspace_id,
            product_code=run.product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type="data_ingestion_run",
            entity_id=run.id,
            detail=detail,
        )
    )


def ingestion_run_response(run: DataIngestionRun) -> IngestionRunResponse:
    return IngestionRunResponse(
        id=run.id,
        source_id=run.source_id,
        run_no=run.run_no,
        connector_contract_version_id=run.connector_contract_version_id,
        schema_mapping_version_id=run.schema_mapping_version_id,
        record_governance_policy_version_id=run.record_governance_policy_version_id,
        operational_policy_version_id=run.operational_policy_version_id,
        execution_mode=run.execution_mode,
        window_start_cursor=run.window_start_cursor,
        window_end_cursor=run.window_end_cursor,
        replay_of_run_id=run.replay_of_run_id,
        source_observed_at=_aware_timestamp(run.source_observed_at),
        forward_cursor_committed=run.forward_cursor_committed,
        source_version_id=run.source_version_id,
        inspection_job_id=run.inspection_job_id,
        request_fingerprint=run.request_fingerprint,
        payload_sha256=run.payload_sha256,
        cursor_before=run.cursor_before,
        cursor_after=run.cursor_after,
        status=run.status,
        attempts=run.attempts,
        error_code=run.error_code,
        error_message=run.error_message,
        queued_at=_aware_timestamp(run.queued_at),
        started_at=_aware_timestamp(run.started_at),
        finished_at=_aware_timestamp(run.finished_at),
        created_at=_aware_timestamp(run.created_at),
        updated_at=_aware_timestamp(run.updated_at),
    )


def create_ingestion_run(
    session: Session,
    storage: StorageBackend,
    *,
    source_id: uuid.UUID,
    request: IngestionRunCreate,
    payload_bytes: bytes,
    actor_id: uuid.UUID | None,
    backend: str,
) -> IngestionRunCreateResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=request.organization_id,
        workspace_id=request.workspace_id,
        product_code=request.product_code,
    )
    existing = session.scalar(
        select(DataIngestionRun).where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.idempotency_key == request.idempotency_key,
        )
    )
    connector, mapping = _load_pinned_contracts(
        session,
        source=source,
        connector_contract_version_id=request.connector_contract_version_id,
        schema_mapping_version_id=request.schema_mapping_version_id,
        require_active=existing is None,
    )
    _safe_name, extension = safe_filename(request.filename)
    content_type = _normalized_content_type(request.content_type)
    payload_sha256 = digest_bytes(payload_bytes)

    if existing is not None:
        fingerprint = _request_fingerprint(
            source_id=source.id,
            connector_contract_version_id=connector.id,
            schema_mapping_version_id=mapping.id,
            payload_sha256=payload_sha256,
            extension=extension,
            content_type=content_type,
            cursor_before=existing.cursor_before,
            cursor_after=request.cursor_after,
        )
        if fingerprint != existing.request_fingerprint:
            raise DataPlatformError("ingestion_run_idempotency_conflict")
        if _normalized_timestamp(request.source_observed_at) != _normalized_timestamp(existing.source_observed_at):
            raise DataPlatformError("ingestion_run_idempotency_conflict")
        return IngestionRunCreateResponse(run=ingestion_run_response(existing), reused=True)

    record_policy = get_active_record_governance_policy_for_binding(
        session,
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
    )
    operational_policy = get_active_ingestion_operational_policy_for_binding(
        session, source_id=source.id, organization_id=source.organization_id,
        workspace_id=source.workspace_id, product_code=source.product_code,
        connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        record_governance_policy_version_id=(record_policy.id if record_policy is not None else None),
    )

    live_run = session.scalar(
        select(DataIngestionRun)
        .where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.status.in_(_LIVE_STATUSES),
        )
        .order_by(DataIngestionRun.run_no.desc())
        .limit(1)
    )
    if live_run is not None:
        raise DataPlatformError("ingestion_run_active_conflict")

    latest_binding_run = session.scalar(
        select(DataIngestionRun)
        .where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.connector_contract_version_id == connector.id,
            DataIngestionRun.schema_mapping_version_id == mapping.id,
            DataIngestionRun.execution_mode == "INCREMENTAL",
        )
        .order_by(DataIngestionRun.run_no.desc())
        .limit(1)
    )
    cursor_before = ""
    if latest_binding_run is not None:
        if latest_binding_run.status in _LIVE_STATUSES:
            raise DataPlatformError("ingestion_run_active_conflict")
        if latest_binding_run.status == "FAILED":
            raise DataPlatformError("ingestion_run_retry_required")
        if latest_binding_run.status != "SUCCEEDED":
            raise DataPlatformError("ingestion_run_execution_integrity_failed")
    committed_run = session.scalar(select(DataIngestionRun).where(
        DataIngestionRun.source_id == source.id,
        DataIngestionRun.connector_contract_version_id == connector.id,
        DataIngestionRun.schema_mapping_version_id == mapping.id,
        DataIngestionRun.execution_mode == "INCREMENTAL",
        DataIngestionRun.status == "SUCCEEDED",
        ((DataIngestionRun.forward_cursor_committed.is_(True)) |
         (DataIngestionRun.operational_policy_version_id.is_(None))),
    ).order_by(DataIngestionRun.run_no.desc()).limit(1))
    if committed_run is not None:
        cursor_before = committed_run.cursor_after

    fingerprint = _request_fingerprint(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
        payload_sha256=payload_sha256,
        extension=extension,
        content_type=content_type,
        cursor_before=cursor_before,
        cursor_after=request.cursor_after,
    )
    duplicate = session.scalar(
        select(DataIngestionRun.id).where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.request_fingerprint == fingerprint,
        )
    )
    if duplicate is not None:
        raise DataPlatformError("ingestion_run_duplicate_batch")

    next_run_no = (
        session.scalar(
            select(func.max(DataIngestionRun.run_no)).where(
                DataIngestionRun.source_id == source.id
            )
        )
        or 0
    ) + 1
    version, job, _storage_reused = create_source_version(
        session,
        storage,
        source=source,
        filename=request.filename,
        content_type=content_type,
        payload=payload_bytes,
        actor_id=actor_id,
        backend=backend,
    )
    run = DataIngestionRun(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        run_no=next_run_no,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
        record_governance_policy_version_id=(record_policy.id if record_policy is not None else None),
        operational_policy_version_id=(operational_policy.id if operational_policy is not None else None),
        execution_mode="INCREMENTAL",
        source_observed_at=_aware_timestamp(request.source_observed_at),
        forward_cursor_committed=False,
        source_version_id=version.id,
        inspection_job_id=job.id,
        idempotency_key=request.idempotency_key,
        request_fingerprint=fingerprint,
        payload_sha256=payload_sha256,
        cursor_before=cursor_before,
        cursor_after=request.cursor_after,
        status="QUEUED",
        attempts=0,
        created_by_membership_id=actor_id,
    )
    session.add(run)
    session.flush()
    _audit(
        session,
        run=run,
        actor_id=actor_id,
        event_type="data.ingestion_run.created",
    )
    session.flush()
    return IngestionRunCreateResponse(run=ingestion_run_response(run), reused=False)


def _ensure_no_live_run(session: Session, source_id: uuid.UUID) -> None:
    if session.scalar(select(DataIngestionRun.id).where(
        DataIngestionRun.source_id == source_id, DataIngestionRun.status.in_(_LIVE_STATUSES)
    ).limit(1)) is not None:
        raise DataPlatformError("ingestion_run_active_conflict")


def _latest_committed_cursor(session: Session, *, source_id: uuid.UUID,
        connector_id: uuid.UUID, mapping_id: uuid.UUID) -> str:
    row = session.scalar(select(DataIngestionRun).where(
        DataIngestionRun.source_id == source_id,
        DataIngestionRun.connector_contract_version_id == connector_id,
        DataIngestionRun.schema_mapping_version_id == mapping_id,
        DataIngestionRun.execution_mode == "INCREMENTAL", DataIngestionRun.status == "SUCCEEDED",
        ((DataIngestionRun.forward_cursor_committed.is_(True)) |
         (DataIngestionRun.operational_policy_version_id.is_(None))),
    ).order_by(DataIngestionRun.run_no.desc()).limit(1))
    return row.cursor_after if row is not None else ""


def create_backfill_ingestion_run(session: Session, storage: StorageBackend, *, source_id: uuid.UUID,
        request: IngestionBackfillCreate, payload_bytes: bytes, actor_id: uuid.UUID | None,
        backend: str) -> IngestionRunCreateResponse:
    source = _locked_scoped_source(session, source_id=source_id, organization_id=request.organization_id,
        workspace_id=request.workspace_id, product_code=request.product_code)
    existing = session.scalar(select(DataIngestionRun).where(
        DataIngestionRun.source_id == source.id, DataIngestionRun.idempotency_key == request.idempotency_key))
    connector, mapping = _load_pinned_contracts(session, source=source,
        connector_contract_version_id=request.connector_contract_version_id,
        schema_mapping_version_id=request.schema_mapping_version_id, require_active=existing is None)
    _name, extension = safe_filename(request.filename)
    content_type = _normalized_content_type(request.content_type)
    checksum = digest_bytes(payload_bytes)
    fingerprint = _backfill_request_fingerprint(source_id=source.id,
        connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        payload_sha256=checksum, extension=extension, content_type=content_type,
        source_observed_at=request.source_observed_at, window_start_cursor=request.window_start_cursor,
        window_end_cursor=request.window_end_cursor)
    if existing is not None:
        if existing.execution_mode != "BACKFILL" or existing.request_fingerprint != fingerprint:
            raise DataPlatformError("ingestion_run_idempotency_conflict")
        validate_pinned_record_governance_policy(session, run=existing)
        validate_pinned_ingestion_operational_policy(session, run=existing)
        return IngestionRunCreateResponse(run=ingestion_run_response(existing), reused=True)
    record_policy = get_active_record_governance_policy_for_binding(session, source_id=source.id,
        organization_id=source.organization_id, workspace_id=source.workspace_id,
        product_code=source.product_code, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id)
    if record_policy is None: raise DataPlatformError("operational_policy_required")
    policy = get_active_ingestion_operational_policy_for_binding(session, source_id=source.id,
        organization_id=source.organization_id, workspace_id=source.workspace_id,
        product_code=source.product_code, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, record_governance_policy_version_id=record_policy.id)
    if policy is None: raise DataPlatformError("operational_policy_required")
    if not json.loads(policy.backfill_contract_json)["backfill_allowed"]:
        raise DataPlatformError("ingestion_backfill_not_allowed")
    _ensure_no_live_run(session, source.id)
    if session.scalar(select(DataIngestionRun.id).where(DataIngestionRun.source_id == source.id,
        DataIngestionRun.request_fingerprint == fingerprint)) is not None:
        raise DataPlatformError("ingestion_run_duplicate_batch")
    cursor = _latest_committed_cursor(session, source_id=source.id, connector_id=connector.id, mapping_id=mapping.id)
    run_no = (session.scalar(select(func.max(DataIngestionRun.run_no)).where(DataIngestionRun.source_id == source.id)) or 0) + 1
    version, job, _ = create_source_version(session, storage, source=source, filename=request.filename,
        content_type=content_type, payload=payload_bytes, actor_id=actor_id, backend=backend)
    run = DataIngestionRun(source_id=source.id, organization_id=source.organization_id,
        workspace_id=source.workspace_id, product_code=source.product_code, run_no=run_no,
        connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        record_governance_policy_version_id=record_policy.id, operational_policy_version_id=policy.id,
        execution_mode="BACKFILL", window_start_cursor=request.window_start_cursor,
        window_end_cursor=request.window_end_cursor, source_observed_at=_aware_timestamp(request.source_observed_at),
        forward_cursor_committed=False, source_version_id=version.id, inspection_job_id=job.id,
        idempotency_key=request.idempotency_key, request_fingerprint=fingerprint, payload_sha256=checksum,
        cursor_before=cursor, cursor_after=cursor, status="QUEUED", attempts=0,
        created_by_membership_id=actor_id)
    session.add(run); session.flush(); _audit(session, run=run, actor_id=actor_id,
        event_type="data.ingestion_run.backfill_created"); session.flush()
    return IngestionRunCreateResponse(run=ingestion_run_response(run), reused=False)


def create_replay_ingestion_run(session: Session, storage: StorageBackend, *, source_id: uuid.UUID,
        run_id: uuid.UUID, request: IngestionReplayCreate, actor_id: uuid.UUID | None,
        backend: str) -> IngestionRunCreateResponse:
    source = _locked_scoped_source(session, source_id=source_id, organization_id=request.organization_id,
        workspace_id=request.workspace_id, product_code=request.product_code)
    parent = session.scalar(select(DataIngestionRun).where(DataIngestionRun.id == run_id,
        DataIngestionRun.source_id == source.id, DataIngestionRun.organization_id == source.organization_id,
        DataIngestionRun.workspace_id == source.workspace_id, DataIngestionRun.product_code == source.product_code))
    if parent is None: raise DataPlatformError("ingestion_run_not_accessible")
    policy = validate_pinned_ingestion_operational_policy(session, run=parent)
    if policy is None: raise DataPlatformError("ingestion_replay_legacy_run_forbidden")
    if not json.loads(policy.backfill_contract_json)["replay_allowed"]:
        raise DataPlatformError("ingestion_replay_not_allowed")
    existing = session.scalar(select(DataIngestionRun).where(DataIngestionRun.source_id == source.id,
        DataIngestionRun.idempotency_key == request.idempotency_key))
    fingerprint = _replay_request_fingerprint(replay_of_run_id=parent.id, source_id=source.id,
        connector_contract_version_id=parent.connector_contract_version_id,
        schema_mapping_version_id=parent.schema_mapping_version_id,
        record_governance_policy_version_id=parent.record_governance_policy_version_id,
        operational_policy_version_id=parent.operational_policy_version_id,
        payload_sha256=parent.payload_sha256)
    if existing is not None:
        if existing.execution_mode != "REPLAY" or existing.request_fingerprint != fingerprint:
            raise DataPlatformError("ingestion_run_idempotency_conflict")
        return IngestionRunCreateResponse(run=ingestion_run_response(existing), reused=True)
    _ensure_no_live_run(session, source.id)
    if session.scalar(select(DataIngestionRun.id).where(DataIngestionRun.source_id == source.id,
        DataIngestionRun.request_fingerprint == fingerprint)) is not None:
        raise DataPlatformError("ingestion_run_duplicate_batch")
    original = session.get(DataSourceVersion, parent.source_version_id)
    if original is None or original.content_state != ContentState.AVAILABLE.value:
        raise DataPlatformError("ingestion_run_content_unavailable")
    payload_bytes = storage.get_bytes(original.storage_key)
    if digest_bytes(payload_bytes) != original.sha256 or len(payload_bytes) != original.size_bytes or original.sha256 != parent.payload_sha256:
        raise DataPlatformError("ingestion_replay_content_integrity_failed")
    run_no = (session.scalar(select(func.max(DataIngestionRun.run_no)).where(DataIngestionRun.source_id == source.id)) or 0) + 1
    version, job, _ = create_source_version(session, storage, source=source,
        filename=original.original_filename, content_type=original.content_type, payload=payload_bytes,
        actor_id=actor_id, backend=backend)
    run = DataIngestionRun(source_id=source.id, organization_id=source.organization_id,
        workspace_id=source.workspace_id, product_code=source.product_code, run_no=run_no,
        connector_contract_version_id=parent.connector_contract_version_id,
        schema_mapping_version_id=parent.schema_mapping_version_id,
        record_governance_policy_version_id=parent.record_governance_policy_version_id,
        operational_policy_version_id=parent.operational_policy_version_id, execution_mode="REPLAY",
        window_start_cursor=parent.window_start_cursor, window_end_cursor=parent.window_end_cursor,
        replay_of_run_id=parent.id, source_observed_at=parent.source_observed_at,
        forward_cursor_committed=False, source_version_id=version.id, inspection_job_id=job.id,
        idempotency_key=request.idempotency_key, request_fingerprint=fingerprint,
        payload_sha256=parent.payload_sha256, cursor_before=parent.cursor_before,
        cursor_after=parent.cursor_after, status="QUEUED", attempts=0,
        created_by_membership_id=actor_id)
    session.add(run); session.flush(); _audit(session, run=run, actor_id=actor_id,
        event_type="data.ingestion_run.replay_created"); session.flush()
    return IngestionRunCreateResponse(run=ingestion_run_response(run), reused=False)


def list_ingestion_runs(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[IngestionRunResponse]:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    rows = session.scalars(
        select(DataIngestionRun)
        .where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.organization_id == source.organization_id,
            DataIngestionRun.workspace_id == source.workspace_id,
            DataIngestionRun.product_code == source.product_code,
        )
        .order_by(DataIngestionRun.run_no.desc())
    ).all()
    return [ingestion_run_response(row) for row in rows]


def get_ingestion_run(
    session: Session,
    *,
    source_id: uuid.UUID,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> IngestionRunResponse:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    run = session.scalar(
        select(DataIngestionRun).where(
            DataIngestionRun.id == run_id,
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.organization_id == source.organization_id,
            DataIngestionRun.workspace_id == source.workspace_id,
            DataIngestionRun.product_code == source.product_code,
        )
    )
    if run is None:
        raise DataPlatformError("ingestion_run_not_accessible")
    return ingestion_run_response(run)


def retry_ingestion_run(
    session: Session,
    *,
    source_id: uuid.UUID,
    run_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
) -> IngestionRunResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    run_scope = (
        DataIngestionRun.id == run_id,
        DataIngestionRun.source_id == source.id,
        DataIngestionRun.organization_id == source.organization_id,
        DataIngestionRun.workspace_id == source.workspace_id,
        DataIngestionRun.product_code == source.product_code,
    )
    candidate = session.scalar(select(DataIngestionRun).where(*run_scope))
    if candidate is None:
        raise DataPlatformError("ingestion_run_not_accessible")
    job = session.scalar(
        select(IngestionJob)
        .where(IngestionJob.id == candidate.inspection_job_id)
        .with_for_update()
    )
    run = session.scalar(select(DataIngestionRun).where(*run_scope).with_for_update())
    if run is None:
        raise DataPlatformError("ingestion_run_not_accessible")
    if run.status != "FAILED":
        raise DataPlatformError("ingestion_run_retry_state_conflict")
    if job is None or job.id != run.inspection_job_id:
        raise DataPlatformError("ingestion_run_execution_integrity_failed")

    live_run = session.scalar(
        select(DataIngestionRun.id).where(
            DataIngestionRun.source_id == source.id,
            DataIngestionRun.id != run.id,
            DataIngestionRun.status.in_(_LIVE_STATUSES),
        )
    )
    if live_run is not None:
        raise DataPlatformError("ingestion_run_active_conflict")

    version = session.scalar(
        select(DataSourceVersion)
        .where(DataSourceVersion.id == run.source_version_id)
        .with_for_update()
    )
    if version is None:
        raise DataPlatformError("ingestion_run_execution_integrity_failed")
    if (
        job.job_type != "inspect"
        or job.status != "failed"
        or job.version_id != version.id
        or version.source_id != source.id
        or (run.organization_id, run.workspace_id, run.product_code)
        != (source.organization_id, source.workspace_id, source.product_code)
        or (version.organization_id, version.workspace_id, version.product_code)
        != (source.organization_id, source.workspace_id, source.product_code)
        or (job.organization_id, job.workspace_id, job.product_code)
        != (source.organization_id, source.workspace_id, source.product_code)
    ):
        raise DataPlatformError("ingestion_run_execution_integrity_failed")
    if version.content_state != ContentState.AVAILABLE.value:
        raise DataPlatformError("ingestion_run_content_unavailable")
    try:
        _load_pinned_contracts(
            session,
            source=source,
            connector_contract_version_id=run.connector_contract_version_id,
            schema_mapping_version_id=run.schema_mapping_version_id,
            require_active=False,
        )
        validate_pinned_record_governance_policy(session, run=run)
        validate_pinned_ingestion_operational_policy(session, run=run)
    except DataPlatformError as exc:
        if str(exc) in {
            "connector_contract_version_not_accessible",
            "schema_mapping_version_not_accessible",
            "ingestion_run_contract_mismatch",
            "record_policy_integrity_failed",
            "operational_policy_integrity_failed",
        }:
            raise DataPlatformError("ingestion_run_execution_integrity_failed") from None
        raise

    queued_at = _utcnow()
    run.status = "QUEUED"
    run.error_code = ""
    run.error_message = ""
    run.queued_at = queued_at
    run.started_at = None
    run.finished_at = None
    job.status = "queued"
    job.progress = 0
    job.rq_job_id = ""
    job.error_code = ""
    job.error_message = ""
    job.queued_at = queued_at
    job.started_at = None
    job.finished_at = None
    version.ingest_status = "queued"
    _audit(
        session,
        run=run,
        actor_id=actor_id,
        event_type="data.ingestion_run.retried",
    )
    session.flush()
    return ingestion_run_response(run)
