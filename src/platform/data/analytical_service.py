from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.platform.ai.namespaces import NamespaceError, assert_namespace_access, private_namespace
from src.platform.data.governance import (
    AIUsePolicy,
    AnalyticalAIAction,
    AnalyticalSnapshotState,
    ContentState,
    DataClassification,
    GovernanceState,
    PrivacyCategory,
    ai_policy_capabilities,
    inherited_ai_policy,
    inherited_classification,
    inherited_privacy,
)
from src.platform.data.models import (
    AnalyticalDataset,
    AnalyticalDatasetContractVersion,
    AnalyticalDatasetSnapshot,
    AnalyticalFeature,
    AnalyticalFeatureSnapshotInput,
    AnalyticalFeatureVersion,
    AnalyticalSnapshotGovernedOutput,
    AnalyticalSnapshotRecordInput,
    AnalyticalSnapshotSourceVersion,
    DataAuditEvent,
    DataGovernedIngestionOutput,
    DataGovernanceInvalidation,
    DataIngestionEvaluation,
    DataIngestionRun,
    DataNormalizedRecord,
    DataSourceGovernanceProfile,
    DataSourceVersion,
)
from src.platform.data.schemas import (
    AnalyticalAIEligibilityResponse,
    AnalyticalDatasetCreate,
    AnalyticalDatasetContractVersionCreate,
    AnalyticalDatasetContractVersionResponse,
    AnalyticalDatasetResponse,
    AnalyticalFeatureCreate,
    AnalyticalFeatureResponse,
    AnalyticalFeatureVersionCreate,
    AnalyticalFeatureVersionResponse,
    GovernedOutputLineageResponse,
    AnalyticalLineageResponse,
    AnalyticalSnapshotCreate,
    AnalyticalSnapshotResponse,
    SnapshotInputResponse,
    SnapshotRecordMembershipResponse,
    SourceLineageResponse,
)
from src.platform.data.service import DataPlatformError, validate_scope


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fingerprint(value: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _scope(model, organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str):
    return (
        model.organization_id == organization_id,
        model.workspace_id == workspace_id,
        model.product_code == product_code,
    )


def _validate_analytical_scope(
    session: Session,
    *,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> None:
    validate_scope(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )


def _audit(session: Session, *, artifact, actor_id: uuid.UUID | None, event_type: str, detail: str) -> None:
    session.add(DataAuditEvent(
        organization_id=artifact.organization_id,
        workspace_id=artifact.workspace_id,
        product_code=artifact.product_code,
        actor_membership_id=actor_id,
        event_type=event_type,
        entity_type=artifact.__tablename__,
        entity_id=artifact.id,
        detail=detail,
    ))


def _dataset_response(row: AnalyticalDataset) -> AnalyticalDatasetResponse:
    return AnalyticalDatasetResponse(
        id=row.id, organization_id=row.organization_id, workspace_id=row.workspace_id, product_code=row.product_code,
        code=row.code, name=row.name, description=row.description, methodology_reference=row.methodology_reference,
        methodology_version=row.methodology_version, revision=row.revision,
        created_by_membership_id=row.created_by_membership_id, updated_by_membership_id=row.updated_by_membership_id,
        created_at=row.created_at, updated_at=row.updated_at,
    )


def _feature_response(row: AnalyticalFeature) -> AnalyticalFeatureResponse:
    return AnalyticalFeatureResponse(
        id=row.id, organization_id=row.organization_id, workspace_id=row.workspace_id, product_code=row.product_code,
        code=row.code, name=row.name, description=row.description, methodology_reference=row.methodology_reference,
        methodology_version=row.methodology_version, revision=row.revision,
        created_by_membership_id=row.created_by_membership_id, updated_by_membership_id=row.updated_by_membership_id,
        created_at=row.created_at, updated_at=row.updated_at,
    )


def _json(value: str) -> object:
    return json.loads(value)


def _contract_response(row: AnalyticalDatasetContractVersion) -> AnalyticalDatasetContractVersionResponse:
    return AnalyticalDatasetContractVersionResponse(
        id=row.id, dataset_id=row.dataset_id, organization_id=row.organization_id,
        workspace_id=row.workspace_id, product_code=row.product_code, version_no=row.version_no,
        contract_format_version=row.contract_format_version,
        field_contract=_json(row.field_contract_json), temporal_mode=row.temporal_mode,
        temporal_key_fields=_json(row.temporal_key_fields_json),
        granularity_key_fields=_json(row.granularity_key_fields_json),
        missing_value_policy=row.missing_value_policy, fingerprint=row.fingerprint,
        lifecycle_state=row.lifecycle_state, created_by_membership_id=row.created_by_membership_id,
        activated_by_membership_id=row.activated_by_membership_id,
        retired_by_membership_id=row.retired_by_membership_id, created_at=row.created_at,
        activated_at=row.activated_at, retired_at=row.retired_at,
    )


def _source_edges(session: Session, snapshot_id: uuid.UUID) -> list[AnalyticalSnapshotSourceVersion]:
    return list(session.scalars(select(AnalyticalSnapshotSourceVersion).where(
        AnalyticalSnapshotSourceVersion.snapshot_id == snapshot_id
    ).order_by(AnalyticalSnapshotSourceVersion.source_version_id)))


def _output_edges(session: Session, snapshot_id: uuid.UUID) -> list[AnalyticalSnapshotGovernedOutput]:
    return list(session.scalars(select(AnalyticalSnapshotGovernedOutput).where(
        AnalyticalSnapshotGovernedOutput.snapshot_id == snapshot_id
    ).order_by(AnalyticalSnapshotGovernedOutput.governed_output_id)))


def _record_edges(session: Session, snapshot_id: uuid.UUID) -> list[AnalyticalSnapshotRecordInput]:
    return list(session.scalars(select(AnalyticalSnapshotRecordInput).where(
        AnalyticalSnapshotRecordInput.snapshot_id == snapshot_id
    ).order_by(AnalyticalSnapshotRecordInput.source_id,
               AnalyticalSnapshotRecordInput.source_record_ordinal,
               AnalyticalSnapshotRecordInput.normalized_record_id)))


def _snapshot_response(session: Session, row: AnalyticalDatasetSnapshot) -> AnalyticalSnapshotResponse:
    edges = _source_edges(session, row.id)
    output_edges = _output_edges(session, row.id)
    record_edges = _record_edges(session, row.id)
    return AnalyticalSnapshotResponse(
        id=row.id, dataset_id=row.dataset_id, organization_id=row.organization_id, workspace_id=row.workspace_id,
        product_code=row.product_code, version_no=row.version_no,
        dataset_contract_version_id=row.dataset_contract_version_id,
        dataset_contract_fingerprint=row.dataset_contract_fingerprint,
        lineage_mode=row.lineage_mode, temporal_mode=row.temporal_mode,
        temporal_key_fields=_json(row.temporal_key_fields_json),
        granularity_key_fields=_json(row.granularity_key_fields_json),
        missing_value_policy=row.missing_value_policy,
        analytical_quality_state=row.analytical_quality_state, record_count=row.record_count,
        methodology_reference=row.methodology_reference,
        methodology_version=row.methodology_version, build_reference=row.build_reference,
        classification=row.classification, privacy_category=row.privacy_category, ai_use_policy=row.ai_use_policy,
        state=row.state, fingerprint=row.fingerprint, revision=row.revision, invalidated=row.invalidated,
        invalidation_reason=row.invalidation_reason, invalidated_at=row.invalidated_at,
        invalidated_by_membership_id=row.invalidated_by_membership_id, frozen_at=row.frozen_at,
        created_by_membership_id=row.created_by_membership_id, updated_by_membership_id=row.updated_by_membership_id,
        created_at=row.created_at, updated_at=row.updated_at,
        source_versions=[SourceLineageResponse(
            source_id=edge.source_id, source_version_id=edge.source_version_id,
            source_version_no=edge.source_version_no, organization_id=edge.organization_id,
            workspace_id=edge.workspace_id, product_code=edge.product_code, classification=edge.classification,
            privacy_category=edge.privacy_category, ai_use_policy=edge.ai_use_policy,
            source_fingerprint=edge.source_fingerprint,
        ) for edge in edges],
        governed_outputs=[GovernedOutputLineageResponse(
            governed_output_id=edge.governed_output_id,
            governed_output_fingerprint=edge.governed_output_fingerprint,
            source_id=edge.source_id, source_version_id=edge.source_version_id,
            ingestion_run_id=edge.ingestion_run_id, evaluation_id=edge.evaluation_id,
            evaluation_fingerprint=edge.evaluation_fingerprint,
            evaluation_decision=edge.evaluation_decision,
            classification=edge.classification, privacy_category=edge.privacy_category,
            ai_use_policy=edge.ai_use_policy,
            organization_id=edge.organization_id, workspace_id=edge.workspace_id,
            product_code=edge.product_code,
        ) for edge in output_edges],
        record_membership=[SnapshotRecordMembershipResponse(
            governed_output_id=edge.governed_output_id,
            normalized_record_id=edge.normalized_record_id, source_id=edge.source_id,
            source_version_id=edge.source_version_id, ingestion_run_id=edge.ingestion_run_id,
            source_record_ordinal=edge.source_record_ordinal, source_locator=edge.source_locator,
            identity_fingerprint=edge.identity_fingerprint, content_fingerprint=edge.content_fingerprint,
            organization_id=edge.organization_id, workspace_id=edge.workspace_id,
            product_code=edge.product_code,
        ) for edge in record_edges],
    )


def _feature_inputs(session: Session, version_id: uuid.UUID) -> list[AnalyticalFeatureSnapshotInput]:
    return list(session.scalars(select(AnalyticalFeatureSnapshotInput).where(
        AnalyticalFeatureSnapshotInput.feature_version_id == version_id
    ).order_by(AnalyticalFeatureSnapshotInput.snapshot_id)))


def _feature_version_response(session: Session, row: AnalyticalFeatureVersion) -> AnalyticalFeatureVersionResponse:
    edges = _feature_inputs(session, row.id)
    return AnalyticalFeatureVersionResponse(
        id=row.id, feature_id=row.feature_id, organization_id=row.organization_id, workspace_id=row.workspace_id,
        product_code=row.product_code, version_no=row.version_no, methodology_reference=row.methodology_reference,
        methodology_version=row.methodology_version, classification=row.classification,
        privacy_category=row.privacy_category, ai_use_policy=row.ai_use_policy, state=row.state,
        fingerprint=row.fingerprint, revision=row.revision, invalidated=row.invalidated,
        invalidation_reason=row.invalidation_reason, invalidated_at=row.invalidated_at,
        invalidated_by_membership_id=row.invalidated_by_membership_id, frozen_at=row.frozen_at,
        created_by_membership_id=row.created_by_membership_id, updated_by_membership_id=row.updated_by_membership_id,
        created_at=row.created_at, updated_at=row.updated_at,
        snapshot_inputs=[SnapshotInputResponse(
            snapshot_id=edge.snapshot_id, snapshot_version_no=edge.snapshot_version_no,
            snapshot_fingerprint=edge.snapshot_fingerprint, organization_id=edge.organization_id,
            workspace_id=edge.workspace_id, product_code=edge.product_code,
            snapshot_lineage_mode=edge.snapshot_lineage_mode,
            dataset_contract_version_id=edge.dataset_contract_version_id,
            dataset_contract_fingerprint=edge.dataset_contract_fingerprint,
            analytical_quality_state=edge.analytical_quality_state,
        ) for edge in edges],
    )


def create_analytical_dataset(session: Session, *, payload: AnalyticalDatasetCreate,
                              actor_id: uuid.UUID | None) -> AnalyticalDatasetResponse:
    _validate_analytical_scope(
        session, organization_id=payload.organization_id,
        workspace_id=payload.workspace_id, product_code=payload.product_code,
    )
    row = AnalyticalDataset(**payload.model_dump(), created_by_membership_id=actor_id, updated_by_membership_id=actor_id)
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        raise DataPlatformError("analytical_dataset_code_exists") from None
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_dataset.created", detail="outcome=CREATED")
    return _dataset_response(row)


def list_analytical_datasets(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
                             product_code: str) -> list[AnalyticalDatasetResponse]:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    rows = session.scalars(select(AnalyticalDataset).where(*_scope(
        AnalyticalDataset, organization_id, workspace_id, product_code
    )).order_by(AnalyticalDataset.code)).all()
    return [_dataset_response(row) for row in rows]


def _get_dataset(session: Session, dataset_id: uuid.UUID, organization_id: uuid.UUID,
                 workspace_id: uuid.UUID, product_code: str) -> AnalyticalDataset:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    row = session.scalar(select(AnalyticalDataset).where(AnalyticalDataset.id == dataset_id, *_scope(
        AnalyticalDataset, organization_id, workspace_id, product_code)))
    if row is None:
        raise DataPlatformError("analytical_dataset_not_accessible")
    return row


def _contract_semantic(payload: AnalyticalDatasetContractVersionCreate,
                       *, dataset_id: uuid.UUID) -> dict[str, object]:
    fields = sorted((field.model_dump() for field in payload.field_contract), key=lambda item: item["field_key"])
    return {
        "dataset_id": dataset_id, "organization_id": payload.organization_id,
        "workspace_id": payload.workspace_id, "product_code": payload.product_code,
        "contract_format_version": 1, "field_contract": fields,
        "temporal_mode": payload.temporal_mode,
        "temporal_key_fields": payload.temporal_key_fields,
        "granularity_key_fields": payload.granularity_key_fields,
        "missing_value_policy": payload.missing_value_policy,
    }


def create_analytical_dataset_contract_version(
    session: Session, *, dataset_id: uuid.UUID, payload: AnalyticalDatasetContractVersionCreate,
    actor_id: uuid.UUID | None,
) -> AnalyticalDatasetContractVersionResponse:
    dataset = _get_dataset(session, dataset_id, payload.organization_id, payload.workspace_id, payload.product_code)
    semantic = _contract_semantic(payload, dataset_id=dataset.id)
    fingerprint = _fingerprint(semantic)
    if session.scalar(select(AnalyticalDatasetContractVersion.id).where(
        AnalyticalDatasetContractVersion.dataset_id == dataset.id,
        AnalyticalDatasetContractVersion.fingerprint == fingerprint,
    )) is not None:
        raise DataPlatformError("analytical_contract_unchanged")
    next_version = (session.scalar(select(func.max(AnalyticalDatasetContractVersion.version_no)).where(
        AnalyticalDatasetContractVersion.dataset_id == dataset.id)) or 0) + 1
    row = AnalyticalDatasetContractVersion(
        dataset_id=dataset.id, organization_id=dataset.organization_id, workspace_id=dataset.workspace_id,
        product_code=dataset.product_code, version_no=next_version, contract_format_version=1,
        field_contract_json=json.dumps(semantic["field_contract"], sort_keys=True, separators=(",", ":")),
        temporal_mode=payload.temporal_mode,
        temporal_key_fields_json=json.dumps(semantic["temporal_key_fields"], separators=(",", ":")),
        granularity_key_fields_json=json.dumps(semantic["granularity_key_fields"], separators=(",", ":")),
        missing_value_policy=payload.missing_value_policy, fingerprint=fingerprint,
        created_by_membership_id=actor_id,
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        raise DataPlatformError("analytical_contract_version_conflict") from None
    _audit(session, artifact=row, actor_id=actor_id,
           event_type="data.analytical_dataset_contract.created",
           detail=f"version={row.version_no}; fingerprint={row.fingerprint}")
    return _contract_response(row)


def list_analytical_dataset_contract_versions(
    session: Session, *, dataset_id: uuid.UUID, organization_id: uuid.UUID,
    workspace_id: uuid.UUID, product_code: str,
) -> list[AnalyticalDatasetContractVersionResponse]:
    _get_dataset(session, dataset_id, organization_id, workspace_id, product_code)
    rows = session.scalars(select(AnalyticalDatasetContractVersion).where(
        AnalyticalDatasetContractVersion.dataset_id == dataset_id,
        *_scope(AnalyticalDatasetContractVersion, organization_id, workspace_id, product_code),
    ).order_by(AnalyticalDatasetContractVersion.version_no.desc())).all()
    return [_contract_response(row) for row in rows]


def activate_analytical_dataset_contract_version(
    session: Session, *, dataset_id: uuid.UUID, contract_version_id: uuid.UUID,
    organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
    actor_id: uuid.UUID | None,
) -> AnalyticalDatasetContractVersionResponse:
    _get_dataset(session, dataset_id, organization_id, workspace_id, product_code)
    row = session.scalar(select(AnalyticalDatasetContractVersion).where(
        AnalyticalDatasetContractVersion.id == contract_version_id,
        AnalyticalDatasetContractVersion.dataset_id == dataset_id,
        *_scope(AnalyticalDatasetContractVersion, organization_id, workspace_id, product_code),
    ))
    if row is None:
        raise DataPlatformError("analytical_contract_version_not_accessible")
    if row.lifecycle_state != "DRAFT":
        raise DataPlatformError("analytical_contract_state_conflict")
    now = utcnow()
    prior = session.scalar(select(AnalyticalDatasetContractVersion).where(
        AnalyticalDatasetContractVersion.dataset_id == dataset_id,
        AnalyticalDatasetContractVersion.lifecycle_state == "ACTIVE",
    ).with_for_update())
    if prior is not None:
        prior.lifecycle_state = "RETIRED"
        prior.retired_at = now
        prior.retired_by_membership_id = actor_id
        _audit(session, artifact=prior, actor_id=actor_id,
               event_type="data.analytical_dataset_contract.retired",
               detail=f"replacement_id={row.id}")
        session.flush()
    row.lifecycle_state = "ACTIVE"
    row.activated_at = now
    row.activated_by_membership_id = actor_id
    try:
        session.flush()
    except IntegrityError:
        raise DataPlatformError("analytical_contract_state_conflict") from None
    _audit(session, artifact=row, actor_id=actor_id,
           event_type="data.analytical_dataset_contract.activated",
           detail=f"version={row.version_no}")
    return _contract_response(row)


def _get_active_contract(
    session: Session, contract_id: uuid.UUID, *, dataset_id: uuid.UUID,
    organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
) -> AnalyticalDatasetContractVersion:
    row = session.scalar(select(AnalyticalDatasetContractVersion).where(
        AnalyticalDatasetContractVersion.id == contract_id,
        AnalyticalDatasetContractVersion.dataset_id == dataset_id,
        AnalyticalDatasetContractVersion.lifecycle_state == "ACTIVE",
        *_scope(AnalyticalDatasetContractVersion, organization_id, workspace_id, product_code),
    ))
    if row is None:
        raise DataPlatformError("analytical_contract_not_active")
    return row


def _validate_value(value: object, logical_type: str) -> bool:
    if value is None:
        return True
    if logical_type == "STRING":
        return isinstance(value, str)
    if logical_type == "INTEGER":
        return isinstance(value, int) and not isinstance(value, bool)
    if logical_type == "NUMBER":
        if not isinstance(value, str):
            return False
        try:
            return Decimal(value).is_finite()
        except InvalidOperation:
            return False
    if logical_type == "BOOLEAN":
        return isinstance(value, bool)
    if logical_type == "DATE":
        if not isinstance(value, str) or "T" in value:
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if logical_type == "DATETIME":
        if not isinstance(value, str) or "T" not in value:
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True
    return logical_type == "JSON"


def _record_conforms(record: DataNormalizedRecord, contract: AnalyticalDatasetContractVersion) -> None:
    value = _json(record.normalized_record_json)
    if not isinstance(value, dict):
        raise DataPlatformError("analytical_record_contract_mismatch")
    fields = _json(contract.field_contract_json)
    if set(value) != {field["field_key"] for field in fields}:
        raise DataPlatformError("analytical_record_contract_mismatch")
    for field in fields:
        field_value = value.get(field["field_key"])
        if field["required"] and (field["field_key"] not in value or field_value is None):
            raise DataPlatformError("analytical_record_contract_mismatch")
        if not _validate_value(field_value, field["logical_type"]):
            raise DataPlatformError("analytical_record_contract_mismatch")


def _load_governed_inputs(
    session: Session, ids: list[uuid.UUID], *, contract: AnalyticalDatasetContractVersion,
    organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
) -> tuple[list[tuple[DataGovernedIngestionOutput, DataIngestionEvaluation, DataSourceGovernanceProfile]],
           list[tuple[DataGovernedIngestionOutput, DataNormalizedRecord]]]:
    unique_ids = sorted(set(ids), key=str)
    if not unique_ids:
        raise DataPlatformError("analytical_snapshot_inputs_required")
    outputs = session.scalars(select(DataGovernedIngestionOutput).where(
        DataGovernedIngestionOutput.id.in_(unique_ids)).order_by(DataGovernedIngestionOutput.id)).all()
    if len(outputs) != len(unique_ids):
        raise DataPlatformError("governed_ingestion_output_not_accessible")
    loaded = []
    candidates = []
    for output in outputs:
        if (output.organization_id, output.workspace_id, output.product_code) != (
            organization_id, workspace_id, product_code
        ):
            raise DataPlatformError("analytical_lineage_scope_mismatch")
        evaluation = session.get(DataIngestionEvaluation, output.evaluation_id)
        run = session.get(DataIngestionRun, output.ingestion_run_id)
        version = session.get(DataSourceVersion, output.source_version_id)
        profile = session.scalar(select(DataSourceGovernanceProfile).where(
            DataSourceGovernanceProfile.source_id == output.source_id,
            *_scope(DataSourceGovernanceProfile, organization_id, workspace_id, product_code),
        ))
        invalidated = session.scalar(select(DataGovernanceInvalidation.id).where(
            DataGovernanceInvalidation.upstream_version_id == output.source_version_id))
        if evaluation is None or run is None or version is None or profile is None:
            raise DataPlatformError("analytical_governed_lineage_incomplete")
        expected_scope = (organization_id, workspace_id, product_code)
        if any((item.organization_id, item.workspace_id, item.product_code) != expected_scope
               for item in (evaluation, run, version)):
            raise DataPlatformError("analytical_lineage_scope_mismatch")
        if (evaluation.ingestion_run_id, evaluation.source_id,
            evaluation.operational_policy_version_id) != (
                output.ingestion_run_id, output.source_id, output.operational_policy_version_id):
            raise DataPlatformError("analytical_governed_lineage_incomplete")
        if evaluation.decision not in {"ACCEPTED", "ACCEPTED_WITH_WARNING"}:
            raise DataPlatformError("analytical_governed_output_ineligible")
        pinned = (
            run.source_id, run.source_version_id, run.connector_contract_version_id,
            run.schema_mapping_version_id, run.record_governance_policy_version_id,
            run.operational_policy_version_id,
        )
        recorded = (
            output.source_id, output.source_version_id, output.connector_contract_version_id,
            output.schema_mapping_version_id, output.record_governance_policy_version_id,
            output.operational_policy_version_id,
        )
        if run.status != "SUCCEEDED" or None in pinned or pinned != recorded:
            raise DataPlatformError("analytical_governed_lineage_incomplete")
        if version.content_state != ContentState.AVAILABLE or invalidated is not None:
            raise DataPlatformError("analytical_upstream_invalidated")
        if profile.governance_state not in {GovernanceState.GOVERNED, GovernanceState.FROZEN}:
            raise DataPlatformError("analytical_upstream_not_governed")
        if profile.classification == DataClassification.UNCLASSIFIED or profile.privacy_category in {
            PrivacyCategory.UNKNOWN, PrivacyCategory.NONE_DECLARED
        } or not profile.processing_purpose.strip() or not profile.data_owner_ref.strip():
            raise DataPlatformError("analytical_upstream_governance_incomplete")
        records = session.scalars(select(DataNormalizedRecord).where(
            DataNormalizedRecord.ingestion_run_id == output.ingestion_run_id,
            DataNormalizedRecord.disposition == "ACCEPTED",
            *_scope(DataNormalizedRecord, organization_id, workspace_id, product_code),
        ).order_by(DataNormalizedRecord.source_record_ordinal, DataNormalizedRecord.id)).all()
        for record in records:
            _record_conforms(record, contract)
            candidates.append((output, record))
        loaded.append((output, evaluation, profile))
    # Entity identity is preferred for overlap; source + identity is the deterministic fallback.
    effective: dict[tuple[object, ...], tuple[DataGovernedIngestionOutput, DataNormalizedRecord]] = {}
    for output, record in sorted(candidates, key=lambda item: (
        str(item[0].id), item[1].source_record_ordinal, str(item[1].id)
    )):
        key = (("entity", record.entity_id) if record.entity_id is not None else
               ("identity", record.source_id, record.identity_fingerprint))
        effective.setdefault(key, (output, record))
    return loaded, sorted(effective.values(), key=lambda item: (
        str(item[0].id), str(item[1].source_id), item[1].source_record_ordinal, str(item[1].id)
    ))


def _snapshot_fingerprint(row: AnalyticalDatasetSnapshot,
                          outputs: list[AnalyticalSnapshotGovernedOutput],
                          records: list[AnalyticalSnapshotRecordInput]) -> str:
    return _fingerprint({
        "dataset_id": row.dataset_id, "version_no": row.version_no, "organization_id": row.organization_id,
        "workspace_id": row.workspace_id, "product_code": row.product_code,
        "dataset_contract_version_id": row.dataset_contract_version_id,
        "dataset_contract_fingerprint": row.dataset_contract_fingerprint,
        "lineage_mode": row.lineage_mode, "temporal_mode": row.temporal_mode,
        "temporal_key_fields": _json(row.temporal_key_fields_json),
        "granularity_key_fields": _json(row.granularity_key_fields_json),
        "missing_value_policy": row.missing_value_policy,
        "methodology_reference": row.methodology_reference, "methodology_version": row.methodology_version,
        "build_reference": row.build_reference, "classification": row.classification,
        "privacy_category": row.privacy_category, "ai_use_policy": row.ai_use_policy,
        "analytical_quality_state": row.analytical_quality_state,
        "outputs": [{"id": edge.governed_output_id, "fingerprint": edge.governed_output_fingerprint}
                    for edge in sorted(outputs, key=lambda item: str(item.governed_output_id))],
        "records": [{"id": edge.normalized_record_id, "identity": edge.identity_fingerprint,
                     "content": edge.content_fingerprint}
                    for edge in sorted(records, key=lambda item: str(item.normalized_record_id))],
    })


def create_analytical_snapshot(session: Session, *, dataset_id: uuid.UUID, payload: AnalyticalSnapshotCreate,
                               actor_id: uuid.UUID | None) -> AnalyticalSnapshotResponse:
    dataset = _get_dataset(session, dataset_id, payload.organization_id, payload.workspace_id, payload.product_code)
    contract = _get_active_contract(
        session, payload.dataset_contract_version_id, dataset_id=dataset.id,
        organization_id=payload.organization_id, workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    outputs, records = _load_governed_inputs(
        session, payload.governed_output_ids, contract=contract,
        organization_id=payload.organization_id, workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    next_version = (session.scalar(select(func.max(AnalyticalDatasetSnapshot.version_no)).where(
        AnalyticalDatasetSnapshot.dataset_id == dataset.id)) or 0) + 1
    row = AnalyticalDatasetSnapshot(
        dataset_id=dataset.id, organization_id=dataset.organization_id, workspace_id=dataset.workspace_id,
        product_code=dataset.product_code, version_no=next_version,
        dataset_contract_version_id=contract.id, dataset_contract_fingerprint=contract.fingerprint,
        lineage_mode="GOVERNED_OUTPUT_V1", temporal_mode=contract.temporal_mode,
        temporal_key_fields_json=contract.temporal_key_fields_json,
        granularity_key_fields_json=contract.granularity_key_fields_json,
        missing_value_policy=contract.missing_value_policy,
        analytical_quality_state=("ACCEPTED_WITH_WARNING" if any(
            evaluation.decision == "ACCEPTED_WITH_WARNING" for _, evaluation, _ in outputs
        ) else "ACCEPTED_CLEAN"), record_count=len(records),
        methodology_reference=payload.methodology_reference, methodology_version=payload.methodology_version,
        build_reference=payload.build_reference,
        classification=inherited_classification([profile.classification for _, _, profile in outputs]).value,
        privacy_category=inherited_privacy([profile.privacy_category for _, _, profile in outputs]).value,
        ai_use_policy=inherited_ai_policy([profile.ai_use_policy for _, _, profile in outputs]).value,
        fingerprint="0" * 64, created_by_membership_id=actor_id, updated_by_membership_id=actor_id,
    )
    session.add(row); session.flush()
    output_edges = [AnalyticalSnapshotGovernedOutput(
        snapshot_id=row.id, governed_output_id=output.id,
        governed_output_fingerprint=output.output_fingerprint, source_id=output.source_id,
        source_version_id=output.source_version_id, ingestion_run_id=output.ingestion_run_id,
        evaluation_id=evaluation.id, evaluation_fingerprint=evaluation.evidence_fingerprint,
        evaluation_decision=evaluation.decision, organization_id=output.organization_id,
        workspace_id=output.workspace_id, product_code=output.product_code,
        classification=profile.classification, privacy_category=profile.privacy_category,
        ai_use_policy=profile.ai_use_policy,
    ) for output, evaluation, profile in outputs]
    record_edges = [AnalyticalSnapshotRecordInput(
        snapshot_id=row.id, governed_output_id=output.id, normalized_record_id=record.id,
        source_id=record.source_id, source_version_id=record.source_version_id,
        ingestion_run_id=record.ingestion_run_id, source_record_ordinal=record.source_record_ordinal,
        source_locator=record.source_locator, identity_fingerprint=record.identity_fingerprint,
        content_fingerprint=record.content_fingerprint, organization_id=record.organization_id,
        workspace_id=record.workspace_id, product_code=record.product_code,
    ) for output, record in records]
    session.add_all(output_edges + record_edges); session.flush()
    row.fingerprint = _snapshot_fingerprint(row, output_edges, record_edges)
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_snapshot.created",
           detail=f"version={row.version_no}; fingerprint={row.fingerprint}")
    session.flush()
    return _snapshot_response(session, row)


def _get_snapshot(session: Session, snapshot_id: uuid.UUID, organization_id: uuid.UUID,
                  workspace_id: uuid.UUID, product_code: str) -> AnalyticalDatasetSnapshot:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    row = session.scalar(select(AnalyticalDatasetSnapshot).where(
        AnalyticalDatasetSnapshot.id == snapshot_id,
        *_scope(AnalyticalDatasetSnapshot, organization_id, workspace_id, product_code)))
    if row is None:
        raise DataPlatformError("analytical_snapshot_not_accessible")
    return row


def list_analytical_snapshots(session: Session, *, dataset_id: uuid.UUID, organization_id: uuid.UUID,
                              workspace_id: uuid.UUID, product_code: str) -> list[AnalyticalSnapshotResponse]:
    _get_dataset(session, dataset_id, organization_id, workspace_id, product_code)
    rows = session.scalars(select(AnalyticalDatasetSnapshot).where(
        AnalyticalDatasetSnapshot.dataset_id == dataset_id,
        *_scope(AnalyticalDatasetSnapshot, organization_id, workspace_id, product_code)
    ).order_by(AnalyticalDatasetSnapshot.version_no.desc())).all()
    return [_snapshot_response(session, row) for row in rows]


def _governed_snapshot_valid(session: Session, snapshot: AnalyticalDatasetSnapshot) -> None:
    if snapshot.lineage_mode != "GOVERNED_OUTPUT_V1" or snapshot.dataset_contract_version_id is None:
        raise DataPlatformError("analytical_legacy_snapshot_promotion_forbidden")
    contract = session.get(AnalyticalDatasetContractVersion, snapshot.dataset_contract_version_id)
    outputs = _output_edges(session, snapshot.id)
    records = _record_edges(session, snapshot.id)
    if contract is None or contract.fingerprint != snapshot.dataset_contract_fingerprint or not outputs:
        raise DataPlatformError("analytical_governed_lineage_incomplete")
    profiles = []
    for edge in outputs:
        output = session.get(DataGovernedIngestionOutput, edge.governed_output_id)
        evaluation = session.get(DataIngestionEvaluation, edge.evaluation_id)
        version = session.get(DataSourceVersion, edge.source_version_id)
        profile = session.scalar(select(DataSourceGovernanceProfile).where(
            DataSourceGovernanceProfile.source_id == edge.source_id,
            *_scope(DataSourceGovernanceProfile, snapshot.organization_id,
                    snapshot.workspace_id, snapshot.product_code),
        ))
        invalidated = session.scalar(select(DataGovernanceInvalidation.id).where(
            DataGovernanceInvalidation.upstream_version_id == edge.source_version_id))
        if output is None or evaluation is None or version is None or profile is None:
            raise DataPlatformError("analytical_governed_lineage_incomplete")
        if output.output_fingerprint != edge.governed_output_fingerprint or (
            evaluation.evidence_fingerprint, evaluation.decision
        ) != (edge.evaluation_fingerprint, edge.evaluation_decision):
            raise DataPlatformError("analytical_upstream_changed")
        if evaluation.decision not in {"ACCEPTED", "ACCEPTED_WITH_WARNING"}:
            raise DataPlatformError("analytical_governed_output_ineligible")
        if version.content_state != ContentState.AVAILABLE or invalidated is not None:
            raise DataPlatformError("analytical_upstream_invalidated")
        if profile.governance_state not in {GovernanceState.GOVERNED, GovernanceState.FROZEN}:
            raise DataPlatformError("analytical_upstream_not_governed")
        if profile.classification == DataClassification.UNCLASSIFIED or profile.privacy_category in {
            PrivacyCategory.UNKNOWN, PrivacyCategory.NONE_DECLARED
        } or not profile.processing_purpose.strip() or not profile.data_owner_ref.strip():
            raise DataPlatformError("analytical_upstream_governance_incomplete")
        if (profile.classification, profile.privacy_category, profile.ai_use_policy) != (
            edge.classification, edge.privacy_category, edge.ai_use_policy
        ):
            raise DataPlatformError("analytical_upstream_changed")
        profiles.append(profile)
    for edge in records:
        record = session.get(DataNormalizedRecord, edge.normalized_record_id)
        if record is None or record.disposition not in {"ACCEPTED", "SUPERSEDED"} or (
            record.identity_fingerprint, record.content_fingerprint, record.source_id,
            record.source_version_id, record.ingestion_run_id, record.source_record_ordinal,
            record.source_locator, record.organization_id, record.workspace_id, record.product_code,
        ) != (
            edge.identity_fingerprint, edge.content_fingerprint, edge.source_id,
            edge.source_version_id, edge.ingestion_run_id, edge.source_record_ordinal,
            edge.source_locator, edge.organization_id, edge.workspace_id, edge.product_code,
        ):
            raise DataPlatformError("analytical_upstream_changed")
    if snapshot.record_count != len(records):
        raise DataPlatformError("analytical_governed_lineage_incomplete")
    inherited = (
        inherited_classification([profile.classification for profile in profiles]).value,
        inherited_privacy([profile.privacy_category for profile in profiles]).value,
        inherited_ai_policy([profile.ai_use_policy for profile in profiles]).value,
    )
    if inherited != (snapshot.classification, snapshot.privacy_category, snapshot.ai_use_policy):
        raise DataPlatformError("analytical_upstream_changed")
    if snapshot.fingerprint != _snapshot_fingerprint(snapshot, outputs, records):
        raise DataPlatformError("analytical_upstream_changed")


_SNAPSHOT_NEXT = {
    AnalyticalSnapshotState.DRAFT: AnalyticalSnapshotState.VALIDATED,
    AnalyticalSnapshotState.VALIDATED: AnalyticalSnapshotState.FROZEN,
    AnalyticalSnapshotState.FROZEN: AnalyticalSnapshotState.RETIRED,
}


def transition_analytical_snapshot(session: Session, *, snapshot_id: uuid.UUID, organization_id: uuid.UUID,
                                   workspace_id: uuid.UUID, product_code: str, expected_revision: int,
                                   target_state: AnalyticalSnapshotState | str,
                                   actor_id: uuid.UUID | None) -> AnalyticalSnapshotResponse:
    row = _get_snapshot(session, snapshot_id, organization_id, workspace_id, product_code)
    target = AnalyticalSnapshotState(target_state)
    current = AnalyticalSnapshotState(row.state)
    if row.revision != expected_revision:
        raise DataPlatformError("analytical_revision_conflict")
    if _SNAPSHOT_NEXT.get(current) != target:
        raise DataPlatformError("analytical_snapshot_transition_invalid")
    if target in {AnalyticalSnapshotState.VALIDATED, AnalyticalSnapshotState.FROZEN}:
        _governed_snapshot_valid(session, row)
    values: dict[str, object] = {"state": target.value, "revision": expected_revision + 1,
                                 "updated_by_membership_id": actor_id, "updated_at": utcnow()}
    if target is AnalyticalSnapshotState.FROZEN:
        values["frozen_at"] = utcnow()
    result = session.execute(update(AnalyticalDatasetSnapshot).where(
        AnalyticalDatasetSnapshot.id == row.id, AnalyticalDatasetSnapshot.revision == expected_revision
    ).values(**values))
    if result.rowcount != 1:
        raise DataPlatformError("analytical_revision_conflict")
    session.flush(); session.expire(row); session.refresh(row)
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_snapshot.transitioned",
           detail=f"state={target.value}; revision={row.revision}; fingerprint={row.fingerprint}")
    return _snapshot_response(session, row)


def get_analytical_lineage(session: Session, *, snapshot_id: uuid.UUID, organization_id: uuid.UUID,
                           workspace_id: uuid.UUID, product_code: str) -> AnalyticalLineageResponse:
    snapshot = _get_snapshot(session, snapshot_id, organization_id, workspace_id, product_code)
    dataset = _get_dataset(session, snapshot.dataset_id, organization_id, workspace_id, product_code)
    feature_ids = session.scalars(select(AnalyticalFeatureSnapshotInput.feature_version_id).where(
        AnalyticalFeatureSnapshotInput.snapshot_id == snapshot.id,
        *_scope(AnalyticalFeatureSnapshotInput, organization_id, workspace_id, product_code))).all()
    features = session.scalars(select(AnalyticalFeatureVersion).where(AnalyticalFeatureVersion.id.in_(feature_ids))).all() if feature_ids else []
    return AnalyticalLineageResponse(dataset=_dataset_response(dataset), snapshot=_snapshot_response(session, snapshot),
                                     dependent_feature_versions=[_feature_version_response(session, row) for row in features])


def create_analytical_feature(session: Session, *, payload: AnalyticalFeatureCreate,
                              actor_id: uuid.UUID | None) -> AnalyticalFeatureResponse:
    _validate_analytical_scope(
        session, organization_id=payload.organization_id,
        workspace_id=payload.workspace_id, product_code=payload.product_code,
    )
    row = AnalyticalFeature(**payload.model_dump(), created_by_membership_id=actor_id, updated_by_membership_id=actor_id)
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        raise DataPlatformError("analytical_feature_code_exists") from None
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_feature.created", detail="outcome=CREATED")
    return _feature_response(row)


def list_analytical_features(session: Session, *, organization_id: uuid.UUID, workspace_id: uuid.UUID,
                             product_code: str) -> list[AnalyticalFeatureResponse]:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    return [_feature_response(row) for row in session.scalars(select(AnalyticalFeature).where(*_scope(
        AnalyticalFeature, organization_id, workspace_id, product_code)).order_by(AnalyticalFeature.code)).all()]


def _get_feature(session: Session, feature_id: uuid.UUID, organization_id: uuid.UUID,
                 workspace_id: uuid.UUID, product_code: str) -> AnalyticalFeature:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    row = session.scalar(select(AnalyticalFeature).where(AnalyticalFeature.id == feature_id, *_scope(
        AnalyticalFeature, organization_id, workspace_id, product_code)))
    if row is None:
        raise DataPlatformError("analytical_feature_not_accessible")
    return row


def _feature_version_fingerprint(row: AnalyticalFeatureVersion, edges: list[AnalyticalFeatureSnapshotInput]) -> str:
    return _fingerprint({
        "feature_id": row.feature_id, "version_no": row.version_no, "organization_id": row.organization_id,
        "workspace_id": row.workspace_id, "product_code": row.product_code,
        "methodology_reference": row.methodology_reference, "methodology_version": row.methodology_version,
        "classification": row.classification, "privacy_category": row.privacy_category,
        "ai_use_policy": row.ai_use_policy,
        "snapshots": [{"id": edge.snapshot_id, "version": edge.snapshot_version_no,
                       "fingerprint": edge.snapshot_fingerprint,
                       "lineage_mode": edge.snapshot_lineage_mode,
                       "dataset_contract_version_id": edge.dataset_contract_version_id,
                       "dataset_contract_fingerprint": edge.dataset_contract_fingerprint,
                       "analytical_quality_state": edge.analytical_quality_state} for edge in edges],
    })


def create_analytical_feature_version(session: Session, *, feature_id: uuid.UUID,
                                      payload: AnalyticalFeatureVersionCreate,
                                      actor_id: uuid.UUID | None) -> AnalyticalFeatureVersionResponse:
    feature = _get_feature(session, feature_id, payload.organization_id, payload.workspace_id, payload.product_code)
    unique_ids = list(dict.fromkeys(payload.snapshot_ids))
    if not unique_ids:
        raise DataPlatformError("analytical_feature_inputs_required")
    snapshots = [_get_snapshot(session, item, payload.organization_id, payload.workspace_id, payload.product_code) for item in unique_ids]
    next_version = (session.scalar(select(func.max(AnalyticalFeatureVersion.version_no)).where(
        AnalyticalFeatureVersion.feature_id == feature.id)) or 0) + 1
    row = AnalyticalFeatureVersion(
        feature_id=feature.id, organization_id=feature.organization_id, workspace_id=feature.workspace_id,
        product_code=feature.product_code, version_no=next_version,
        methodology_reference=payload.methodology_reference, methodology_version=payload.methodology_version,
        classification=inherited_classification([item.classification for item in snapshots]).value,
        privacy_category=inherited_privacy([item.privacy_category for item in snapshots]).value,
        ai_use_policy=inherited_ai_policy([item.ai_use_policy for item in snapshots]).value,
        fingerprint="0" * 64, created_by_membership_id=actor_id, updated_by_membership_id=actor_id,
    )
    session.add(row); session.flush()
    edges = [AnalyticalFeatureSnapshotInput(
        feature_version_id=row.id, snapshot_id=item.id, organization_id=item.organization_id,
        workspace_id=item.workspace_id, product_code=item.product_code, snapshot_version_no=item.version_no,
        snapshot_fingerprint=item.fingerprint,
        snapshot_lineage_mode=item.lineage_mode,
        dataset_contract_version_id=item.dataset_contract_version_id,
        dataset_contract_fingerprint=item.dataset_contract_fingerprint,
        analytical_quality_state=item.analytical_quality_state,
    ) for item in snapshots]
    session.add_all(edges); session.flush()
    row.fingerprint = _feature_version_fingerprint(row, sorted(edges, key=lambda edge: str(edge.snapshot_id)))
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_feature_version.created",
           detail=f"version={row.version_no}; fingerprint={row.fingerprint}")
    session.flush()
    return _feature_version_response(session, row)


def list_analytical_feature_versions(session: Session, *, feature_id: uuid.UUID, organization_id: uuid.UUID,
                                     workspace_id: uuid.UUID, product_code: str) -> list[AnalyticalFeatureVersionResponse]:
    _get_feature(session, feature_id, organization_id, workspace_id, product_code)
    rows = session.scalars(select(AnalyticalFeatureVersion).where(
        AnalyticalFeatureVersion.feature_id == feature_id,
        *_scope(AnalyticalFeatureVersion, organization_id, workspace_id, product_code)
    ).order_by(AnalyticalFeatureVersion.version_no.desc())).all()
    return [_feature_version_response(session, row) for row in rows]


def _get_feature_version(session: Session, version_id: uuid.UUID, organization_id: uuid.UUID,
                         workspace_id: uuid.UUID, product_code: str) -> AnalyticalFeatureVersion:
    _validate_analytical_scope(
        session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
    )
    row = session.scalar(select(AnalyticalFeatureVersion).where(
        AnalyticalFeatureVersion.id == version_id,
        *_scope(AnalyticalFeatureVersion, organization_id, workspace_id, product_code)))
    if row is None:
        raise DataPlatformError("analytical_feature_version_not_accessible")
    return row


def _feature_snapshots_valid(session: Session, row: AnalyticalFeatureVersion, *, frozen: bool,
                             refresh: bool) -> list[AnalyticalFeatureSnapshotInput]:
    edges = _feature_inputs(session, row.id)
    if not edges:
        raise DataPlatformError("analytical_feature_inputs_required")
    snapshots = []
    for edge in edges:
        snapshot = _get_snapshot(session, edge.snapshot_id, row.organization_id, row.workspace_id, row.product_code)
        if snapshot.invalidated:
            raise DataPlatformError("analytical_upstream_invalidated")
        if snapshot.lineage_mode != "GOVERNED_OUTPUT_V1" or snapshot.dataset_contract_version_id is None:
            raise DataPlatformError("analytical_legacy_snapshot_feature_governance_forbidden")
        _governed_snapshot_valid(session, snapshot)
        allowed_states = {AnalyticalSnapshotState.FROZEN} if frozen else {
            AnalyticalSnapshotState.VALIDATED, AnalyticalSnapshotState.FROZEN}
        if AnalyticalSnapshotState(snapshot.state) not in allowed_states:
            raise DataPlatformError("analytical_snapshot_lifecycle_ineligible")
        if refresh:
            edge.snapshot_version_no, edge.snapshot_fingerprint = snapshot.version_no, snapshot.fingerprint
            edge.snapshot_lineage_mode = snapshot.lineage_mode
            edge.dataset_contract_version_id = snapshot.dataset_contract_version_id
            edge.dataset_contract_fingerprint = snapshot.dataset_contract_fingerprint
            edge.analytical_quality_state = snapshot.analytical_quality_state
        elif (edge.snapshot_version_no, edge.snapshot_fingerprint, edge.snapshot_lineage_mode,
              edge.dataset_contract_version_id, edge.dataset_contract_fingerprint,
              edge.analytical_quality_state) != (
                  snapshot.version_no, snapshot.fingerprint, snapshot.lineage_mode,
                  snapshot.dataset_contract_version_id, snapshot.dataset_contract_fingerprint,
                  snapshot.analytical_quality_state):
            raise DataPlatformError("analytical_upstream_changed")
        snapshots.append(snapshot)
    if refresh:
        row.classification = inherited_classification([item.classification for item in snapshots]).value
        row.privacy_category = inherited_privacy([item.privacy_category for item in snapshots]).value
        row.ai_use_policy = inherited_ai_policy([item.ai_use_policy for item in snapshots]).value
        row.fingerprint = _feature_version_fingerprint(row, edges)
    return edges


_FEATURE_NEXT = {
    GovernanceState.DRAFT: GovernanceState.GOVERNED,
    GovernanceState.GOVERNED: GovernanceState.FROZEN,
    GovernanceState.FROZEN: GovernanceState.RETIRED,
}


def transition_analytical_feature_version(session: Session, *, feature_version_id: uuid.UUID,
                                          organization_id: uuid.UUID, workspace_id: uuid.UUID,
                                          product_code: str, expected_revision: int,
                                          target_state: GovernanceState | str,
                                          actor_id: uuid.UUID | None) -> AnalyticalFeatureVersionResponse:
    row = _get_feature_version(session, feature_version_id, organization_id, workspace_id, product_code)
    target, current = GovernanceState(target_state), GovernanceState(row.state)
    if row.revision != expected_revision:
        raise DataPlatformError("analytical_revision_conflict")
    if _FEATURE_NEXT.get(current) != target:
        raise DataPlatformError("analytical_feature_transition_invalid")
    if target in {GovernanceState.GOVERNED, GovernanceState.FROZEN}:
        _feature_snapshots_valid(session, row, frozen=target is GovernanceState.FROZEN,
                                 refresh=target is GovernanceState.GOVERNED)
    values: dict[str, object] = {"state": target.value, "revision": expected_revision + 1,
                                 "updated_by_membership_id": actor_id, "updated_at": utcnow()}
    if target is GovernanceState.FROZEN:
        values["frozen_at"] = utcnow()
    result = session.execute(update(AnalyticalFeatureVersion).where(
        AnalyticalFeatureVersion.id == row.id, AnalyticalFeatureVersion.revision == expected_revision
    ).values(**values))
    if result.rowcount != 1:
        raise DataPlatformError("analytical_revision_conflict")
    session.flush(); session.expire(row); session.refresh(row)
    _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_feature_version.transitioned",
           detail=f"state={target.value}; revision={row.revision}; fingerprint={row.fingerprint}")
    return _feature_version_response(session, row)


def propagate_source_version_invalidation(session: Session, *, source_version_id: uuid.UUID,
                                          organization_id: uuid.UUID, workspace_id: uuid.UUID,
                                          product_code: str, actor_id: uuid.UUID | None,
                                          reason: str = "SOURCE_VERSION_PURGED") -> int:
    legacy_ids = session.scalars(select(AnalyticalSnapshotSourceVersion.snapshot_id).where(
        AnalyticalSnapshotSourceVersion.source_version_id == source_version_id,
        *_scope(AnalyticalSnapshotSourceVersion, organization_id, workspace_id, product_code))).all()
    governed_ids = session.scalars(select(AnalyticalSnapshotGovernedOutput.snapshot_id).where(
        AnalyticalSnapshotGovernedOutput.source_version_id == source_version_id,
        *_scope(AnalyticalSnapshotGovernedOutput, organization_id, workspace_id, product_code))).all()
    snapshot_ids = list(dict.fromkeys([*legacy_ids, *governed_ids]))
    if not snapshot_ids:
        return 0
    at = utcnow()
    snapshots = session.scalars(select(AnalyticalDatasetSnapshot).where(
        AnalyticalDatasetSnapshot.id.in_(snapshot_ids), AnalyticalDatasetSnapshot.invalidated.is_(False),
        *_scope(AnalyticalDatasetSnapshot, organization_id, workspace_id, product_code))).all()
    for row in snapshots:
        row.invalidated, row.invalidation_reason, row.invalidated_at = True, reason, at
        row.invalidated_by_membership_id = actor_id
        _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_snapshot.invalidated",
               detail=f"reason={reason}; source_version_id={source_version_id}")
    feature_ids = session.scalars(select(AnalyticalFeatureSnapshotInput.feature_version_id).where(
        AnalyticalFeatureSnapshotInput.snapshot_id.in_(snapshot_ids))).all()
    features = session.scalars(select(AnalyticalFeatureVersion).where(
        AnalyticalFeatureVersion.id.in_(feature_ids), AnalyticalFeatureVersion.invalidated.is_(False),
        *_scope(AnalyticalFeatureVersion, organization_id, workspace_id, product_code))).all() if feature_ids else []
    for row in features:
        row.invalidated, row.invalidation_reason, row.invalidated_at = True, "UPSTREAM_SNAPSHOT_INVALIDATED", at
        row.invalidated_by_membership_id = actor_id
        _audit(session, artifact=row, actor_id=actor_id, event_type="data.analytical_feature_version.invalidated",
               detail="reason=UPSTREAM_SNAPSHOT_INVALIDATED")
    session.flush()
    return len(snapshots) + len(features)


def _all_raw_policies(session: Session, artifact_type: str, artifact_id: uuid.UUID) -> list[AIUsePolicy]:
    if artifact_type == "snapshot":
        snapshot_ids = [artifact_id]
    else:
        snapshot_ids = list(session.scalars(select(AnalyticalFeatureSnapshotInput.snapshot_id).where(
            AnalyticalFeatureSnapshotInput.feature_version_id == artifact_id)))
    governed_policies = session.scalars(select(AnalyticalSnapshotGovernedOutput.ai_use_policy).where(
        AnalyticalSnapshotGovernedOutput.snapshot_id.in_(snapshot_ids))).all()
    if governed_policies:
        return [AIUsePolicy(value) for value in governed_policies]
    return [AIUsePolicy(value) for value in session.scalars(select(AnalyticalSnapshotSourceVersion.ai_use_policy).where(
        AnalyticalSnapshotSourceVersion.snapshot_id.in_(snapshot_ids))).all()]


def _dependency_reason(session: Session, artifact, artifact_type: str) -> str | None:
    if artifact_type == "snapshot":
        snapshots = [artifact]
    else:
        inputs = _feature_inputs(session, artifact.id)
        if not inputs:
            return "UPSTREAM_LINEAGE_MISSING"
        snapshots = []
        for edge in inputs:
            if (edge.organization_id, edge.workspace_id, edge.product_code) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
            snapshot = session.get(AnalyticalDatasetSnapshot, edge.snapshot_id)
            if snapshot is None or (snapshot.organization_id, snapshot.workspace_id, snapshot.product_code) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
            if snapshot.invalidated:
                return "UPSTREAM_INVALIDATED"
            snapshots.append(snapshot)
    for snapshot in snapshots:
        if snapshot.lineage_mode != "GOVERNED_OUTPUT_V1":
            return "UPSTREAM_LINEAGE_MISSING"
        try:
            _governed_snapshot_valid(session, snapshot)
        except DataPlatformError as exc:
            return ("UPSTREAM_INVALIDATED" if str(exc) == "analytical_upstream_invalidated"
                    else "UPSTREAM_CHANGED")
        edges = _output_edges(session, snapshot.id)
        if not edges:
            return "UPSTREAM_LINEAGE_MISSING"
        for edge in edges:
            if (edge.organization_id, edge.workspace_id, edge.product_code) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
            output = session.get(DataGovernedIngestionOutput, edge.governed_output_id)
            evaluation = session.get(DataIngestionEvaluation, edge.evaluation_id)
            version = session.get(DataSourceVersion, edge.source_version_id)
            invalidation = session.scalar(select(DataGovernanceInvalidation.id).where(
                DataGovernanceInvalidation.upstream_version_id == edge.source_version_id))
            if output is None or evaluation is None or version is None or (
                version.organization_id, version.workspace_id, version.product_code
            ) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
            if output.output_fingerprint != edge.governed_output_fingerprint or evaluation.decision not in {
                "ACCEPTED", "ACCEPTED_WITH_WARNING"
            }:
                return "UPSTREAM_CHANGED"
            if version.content_state != ContentState.AVAILABLE or invalidation is not None:
                return "UPSTREAM_INVALIDATED"
    return None


def evaluate_analytical_ai_eligibility(session: Session, *, artifact_type: str, artifact_id: uuid.UUID,
                                       action: AnalyticalAIAction | str, organization_id: uuid.UUID,
                                       workspace_id: uuid.UUID, product_code: str,
                                       namespace: str) -> AnalyticalAIEligibilityResponse:
    requested = AnalyticalAIAction(action)
    if artifact_type == "snapshot":
        artifact = _get_snapshot(session, artifact_id, organization_id, workspace_id, product_code)
    elif artifact_type == "feature_version":
        artifact = _get_feature_version(session, artifact_id, organization_id, workspace_id, product_code)
    else:
        raise DataPlatformError("analytical_artifact_type_invalid")
    reason = "ELIGIBLE"
    expected_namespace = private_namespace(artifact.organization_id, artifact.product_code)
    try:
        assert_namespace_access(namespace, organization_id=artifact.organization_id, product_code=artifact.product_code)
    except NamespaceError:
        reason = "NAMESPACE_SCOPE_MISMATCH"
    if namespace != expected_namespace:
        reason = "NAMESPACE_SCOPE_MISMATCH"
    policies = _all_raw_policies(session, artifact_type, artifact.id)
    dependency_reason = _dependency_reason(session, artifact, artifact_type)
    if reason != "ELIGIBLE":
        pass
    elif not policies:
        reason = "UPSTREAM_POLICY_MISSING"
    elif artifact.classification == DataClassification.UNCLASSIFIED:
        reason = "CLASSIFICATION_FAIL_CLOSED"
    elif artifact.privacy_category in {PrivacyCategory.UNKNOWN, PrivacyCategory.NONE_DECLARED}:
        reason = "PRIVACY_FAIL_CLOSED"
    elif artifact.invalidated:
        reason = "ARTIFACT_INVALIDATED"
    elif dependency_reason is not None:
        reason = dependency_reason
    else:
        states = ({AnalyticalSnapshotState.VALIDATED.value, AnalyticalSnapshotState.FROZEN.value}
                  if artifact_type == "snapshot" else {GovernanceState.GOVERNED.value, GovernanceState.FROZEN.value})
        if artifact.state not in states:
            reason = "LIFECYCLE_INELIGIBLE"
        elif requested in {AnalyticalAIAction.RAG_RETRIEVAL, AnalyticalAIAction.MODEL_EVALUATION} and artifact.state != "FROZEN":
            reason = "FROZEN_REQUIRED"
        elif requested is AnalyticalAIAction.MODEL_TRAINING:
            reason = "MODEL_TRAINING_SEPARATE_APPROVAL_REQUIRED" if all(
                policy is AIUsePolicy.MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL for policy in policies
            ) else "MODEL_TRAINING_PROHIBITED"
        elif any(requested not in ai_policy_capabilities(policy) for policy in policies):
            reason = "UPSTREAM_POLICY_DENIES_ACTION"
    allowed = reason == "ELIGIBLE"
    return AnalyticalAIEligibilityResponse(
        allowed=allowed, requested_action=requested, reason_code=reason,
        requires_separate_approval=(requested is AnalyticalAIAction.MODEL_TRAINING and
                                    reason == "MODEL_TRAINING_SEPARATE_APPROVAL_REQUIRED"),
        organization_id=artifact.organization_id, workspace_id=artifact.workspace_id,
        product_code=artifact.product_code, artifact_type=artifact_type, artifact_id=artifact.id,
        artifact_version=artifact.version_no, lifecycle_state=artifact.state,
        classification=artifact.classification, privacy_category=artifact.privacy_category,
        ai_use_policy=artifact.ai_use_policy, namespace=namespace, human_review_required=True,
        provenance_fingerprint=artifact.fingerprint,
    )
