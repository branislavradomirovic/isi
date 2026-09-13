from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.orm import Session

from src.platform.data.governance import (
    AnonymizationStatus,
    ContentState,
    DataClassification,
    ExportPolicy,
    GovernanceState,
    PrivacyCategory,
    PurgeStatus,
)
from src.platform.data.models import (
    DataAnonymizationRecord,
    DataExportManifest,
    DataGovernanceInvalidation,
    DataRetentionPolicy,
    DataRetentionState,
    DataSourceGovernanceProfile,
    DataSourceVersion,
)
from src.platform.data.schemas import (
    AnonymizationProposalCreate,
    AnonymizationRecordResponse,
    RetentionStateResponse,
)
from src.platform.data.record_governance_service import purge_source_version_records
from src.platform.data.service import DataPlatformError, _audit, retention_state_response, validate_scope
from src.platform.data.storage import StorageBackend, StorageError, digest_bytes


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _scoped_version(
    session: Session,
    *,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> DataSourceVersion:
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    version = session.scalar(
        select(DataSourceVersion).where(
            DataSourceVersion.id == version_id,
            DataSourceVersion.organization_id == organization_id,
            DataSourceVersion.workspace_id == workspace_id,
            DataSourceVersion.product_code == product_code,
        )
    )
    if version is None:
        raise DataPlatformError("version_not_accessible")
    return version


def _state(session: Session, version: DataSourceVersion) -> DataRetentionState:
    state = session.scalar(
        select(DataRetentionState).where(
            DataRetentionState.version_id == version.id,
            DataRetentionState.organization_id == version.organization_id,
            DataRetentionState.workspace_id == version.workspace_id,
            DataRetentionState.product_code == version.product_code,
        )
    )
    if state is None:
        raise DataPlatformError("retention_state_missing")
    return state


def get_retention_state(
    session: Session,
    *,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> RetentionStateResponse:
    return retention_state_response(
        _state(
            session,
            _scoped_version(
                session,
                version_id=version_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code=product_code,
            ),
        )
    )


def _atomic_state_update(
    session: Session,
    state: DataRetentionState,
    *,
    expected_revision: int,
    values: dict[str, object],
) -> DataRetentionState:
    result = session.execute(
        sql_update(DataRetentionState)
        .where(DataRetentionState.id == state.id, DataRetentionState.revision == expected_revision)
        .values(**values, revision=expected_revision + 1, updated_at=func.now())
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        session.expire(state)
        raise DataPlatformError("retention_revision_conflict")
    session.refresh(state)
    return state


def place_hold(
    session: Session,
    *,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    expected_revision: int,
    reason_reference: str,
    actor_id: uuid.UUID | None,
    now: datetime | None = None,
) -> RetentionStateResponse:
    reason = " ".join(reason_reference.split()).strip()
    if not reason or len(reason) > 500:
        raise DataPlatformError("hold_reason_required")
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    state = _state(session, version)
    if state.hold_active:
        if state.revision != expected_revision:
            raise DataPlatformError("retention_revision_conflict")
        return retention_state_response(state)
    state = _atomic_state_update(
        session,
        state,
        expected_revision=expected_revision,
        values={
            "hold_active": True,
            "hold_reason_ref": reason,
            "hold_placed_at": now or utcnow(),
            "hold_placed_by_membership_id": actor_id,
            "hold_released_at": None,
            "hold_released_by_membership_id": None,
        },
    )
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.retention.hold_placed", entity_type="data_source_version", entity_id=version.id,
           detail=f"revision={state.revision}; reason_reference_recorded=true")
    return retention_state_response(state)


def release_hold(
    session: Session,
    *,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    expected_revision: int,
    actor_id: uuid.UUID | None,
    now: datetime | None = None,
) -> RetentionStateResponse:
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    state = _state(session, version)
    if not state.hold_active:
        raise DataPlatformError("hold_not_active")
    state = _atomic_state_update(
        session,
        state,
        expected_revision=expected_revision,
        values={
            "hold_active": False,
            "hold_released_at": now or utcnow(),
            "hold_released_by_membership_id": actor_id,
        },
    )
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.retention.hold_released", entity_type="data_source_version", entity_id=version.id,
           detail=f"revision={state.revision}")
    return retention_state_response(state)


def _eligible_policy(session: Session, version: DataSourceVersion, state: DataRetentionState, *, now: datetime) -> DataRetentionPolicy:
    if state.hold_active:
        raise DataPlatformError("hold_active")
    if version.content_state != ContentState.AVAILABLE:
        raise DataPlatformError("content_purged_unavailable")
    profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == version.source_id))
    if profile is not None and (profile.organization_id, profile.workspace_id, profile.product_code) != (
        version.organization_id, version.workspace_id, version.product_code
    ):
        raise DataPlatformError("governance_scope_mismatch")
    policy = session.scalar(
        select(DataRetentionPolicy).where(
            DataRetentionPolicy.id == (profile.retention_policy_id if profile else None),
            DataRetentionPolicy.organization_id == version.organization_id,
            DataRetentionPolicy.workspace_id == version.workspace_id,
            DataRetentionPolicy.product_code == version.product_code,
            DataRetentionPolicy.status == "active",
        )
    )
    due = state.retention_due_at
    if policy is None or policy.no_auto_delete or policy.retention_days is None or due is None:
        raise DataPlatformError("retention_not_eligible")
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    if due > now:
        raise DataPlatformError("retention_not_eligible")
    return policy


def request_purge(session: Session, *, version_id: uuid.UUID, organization_id: uuid.UUID, workspace_id: uuid.UUID,
                  product_code: str, expected_revision: int, actor_id: uuid.UUID | None,
                  now: datetime | None = None) -> RetentionStateResponse:
    at = now or utcnow()
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    state = _state(session, version)
    _eligible_policy(session, version, state, now=at)
    if state.purge_status not in {PurgeStatus.NONE, PurgeStatus.FAILED}:
        raise DataPlatformError("purge_state_conflict")
    state = _atomic_state_update(session, state, expected_revision=expected_revision, values={
        "purge_status": PurgeStatus.REQUESTED.value, "purge_requested_at": at,
        "purge_requested_by_membership_id": actor_id, "purge_result": "",
    })
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.purge.requested", entity_type="data_source_version", entity_id=version.id,
           detail=f"revision={state.revision}; outcome=REQUESTED")
    return retention_state_response(state)


def approve_purge(session: Session, *, version_id: uuid.UUID, organization_id: uuid.UUID, workspace_id: uuid.UUID,
                  product_code: str, expected_revision: int, actor_id: uuid.UUID | None,
                  now: datetime | None = None) -> RetentionStateResponse:
    at = now or utcnow()
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    state = _state(session, version)
    _eligible_policy(session, version, state, now=at)
    if state.purge_status != PurgeStatus.REQUESTED:
        raise DataPlatformError("purge_state_conflict")
    state = _atomic_state_update(session, state, expected_revision=expected_revision, values={
        "purge_status": PurgeStatus.APPROVED.value, "purge_approved_at": at,
        "purge_approved_by_membership_id": actor_id,
    })
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.purge.approved", entity_type="data_source_version", entity_id=version.id,
           detail=f"revision={state.revision}; outcome=APPROVED")
    return retention_state_response(state)


def execute_purge(session: Session, storage: StorageBackend, *, version_id: uuid.UUID, organization_id: uuid.UUID,
                  workspace_id: uuid.UUID, product_code: str, expected_revision: int,
                  actor_id: uuid.UUID | None, now: datetime | None = None) -> RetentionStateResponse:
    at = now or utcnow()
    scoped_version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    version = session.scalar(
        select(DataSourceVersion)
        .where(
            DataSourceVersion.id == scoped_version.id,
            DataSourceVersion.organization_id == organization_id,
            DataSourceVersion.workspace_id == workspace_id,
            DataSourceVersion.product_code == product_code,
        )
        .with_for_update()
    )
    if version is None:
        raise DataPlatformError("version_not_accessible")
    state = _state(session, version)
    if state.purge_status == PurgeStatus.EXECUTED and version.content_state == ContentState.PURGED:
        if state.revision != expected_revision:
            raise DataPlatformError("retention_revision_conflict")
        return retention_state_response(state)
    _eligible_policy(session, version, state, now=at)
    if state.purge_status not in {PurgeStatus.APPROVED, PurgeStatus.EXECUTING}:
        raise DataPlatformError("purge_state_conflict")
    if state.purge_status == PurgeStatus.APPROVED:
        state = _atomic_state_update(session, state, expected_revision=expected_revision, values={"purge_status": PurgeStatus.EXECUTING.value})
    elif state.revision != expected_revision:
        raise DataPlatformError("retention_revision_conflict")
    references = session.scalars(
        select(DataSourceVersion).where(
            DataSourceVersion.organization_id == organization_id,
            DataSourceVersion.workspace_id == workspace_id,
            DataSourceVersion.product_code == product_code,
            DataSourceVersion.storage_key == version.storage_key,
            DataSourceVersion.content_state == ContentState.AVAILABLE,
        ).order_by(DataSourceVersion.id).with_for_update()
    ).all()
    shared = next((reference for reference in references if reference.id != version.id), None)
    result_code = "LOGICAL_ONLY_SHARED_OBJECT_RETAINED"
    if shared is None:
        try:
            storage.delete_bytes(version.storage_key)
        except StorageError:
            state = _atomic_state_update(session, state, expected_revision=state.revision, values={
                "purge_status": PurgeStatus.FAILED.value, "purge_result": "STORAGE_OPERATION_FAILED",
            })
            _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
                   event_type="data.purge.failed", entity_type="data_source_version", entity_id=version.id,
                   detail=f"revision={state.revision}; outcome=STORAGE_OPERATION_FAILED")
            raise DataPlatformError("storage_operation_failed") from None
        result_code = "PHYSICAL_OBJECT_DELETED"
    purge_source_version_records(
        session,
        source_version_id=version.id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
    )
    version.content_state = ContentState.PURGED.value
    tombstone = hashlib.sha256(
        f"{organization_id}:{product_code}:{workspace_id}:{version.id}:{version.sha256}:PURGED".encode()
    ).hexdigest()
    state = _atomic_state_update(session, state, expected_revision=state.revision, values={
        "purge_status": PurgeStatus.EXECUTED.value, "purge_executed_at": at,
        "purge_executed_by_membership_id": actor_id, "purge_result": result_code,
        "tombstone_checksum": tombstone,
    })
    existing = session.scalar(select(DataGovernanceInvalidation).where(
        DataGovernanceInvalidation.upstream_version_id == version.id,
        DataGovernanceInvalidation.reason == "PURGED",
    ))
    if existing is None:
        session.add(DataGovernanceInvalidation(
            organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
            upstream_entity_type="source_version", upstream_version_id=version.id, reason="PURGED",
            actor_membership_id=actor_id, fingerprint=tombstone,
        ))
    session.flush()
    # Analytical invalidation is downstream metadata only; source purge semantics remain authoritative here.
    from src.platform.data.analytical_service import propagate_source_version_invalidation
    propagate_source_version_invalidation(
        session,
        source_version_id=version.id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        actor_id=actor_id,
    )
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.purge.executed", entity_type="data_source_version", entity_id=version.id,
           detail=f"revision={state.revision}; outcome={result_code}; tombstone={tombstone}")
    return retention_state_response(state)


def record_purge_storage_failure(session: Session, *, version_id: uuid.UUID, organization_id: uuid.UUID,
                                 workspace_id: uuid.UUID, product_code: str, expected_revision: int,
                                 actor_id: uuid.UUID | None) -> None:
    """Record a bounded failure after the caller rolled back the failed storage transaction."""
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id,
                              workspace_id=workspace_id, product_code=product_code)
    state = _state(session, version)
    if state.purge_status not in {PurgeStatus.APPROVED, PurgeStatus.EXECUTING}:
        return
    state = _atomic_state_update(session, state, expected_revision=expected_revision, values={
        "purge_status": PurgeStatus.FAILED.value, "purge_result": "STORAGE_OPERATION_FAILED",
    })
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
           actor_id=actor_id, event_type="data.purge.failed", entity_type="data_source_version",
           entity_id=version.id, detail=f"revision={state.revision}; outcome=STORAGE_OPERATION_FAILED")


def anonymization_response(record: DataAnonymizationRecord) -> AnonymizationRecordResponse:
    return AnonymizationRecordResponse(**{column.name: getattr(record, column.name) for column in record.__table__.columns})


def propose_anonymization(session: Session, *, payload: AnonymizationProposalCreate,
                          actor_id: uuid.UUID | None) -> AnonymizationRecordResponse:
    if (
        not payload.method_code.strip()
        or not payload.method_version.strip()
        or not payload.method_reference.strip()
        or not payload.evidence_reference.strip()
    ):
        raise DataPlatformError("anonymization_evidence_required")
    input_version = _scoped_version(session, version_id=payload.input_version_id, organization_id=payload.organization_id,
                                    workspace_id=payload.workspace_id, product_code=payload.product_code)
    output_version = _scoped_version(session, version_id=payload.output_version_id, organization_id=payload.organization_id,
                                     workspace_id=payload.workspace_id, product_code=payload.product_code)
    if input_version.source_id == output_version.source_id:
        raise DataPlatformError("anonymization_output_source_required")
    if output_version.content_state != ContentState.AVAILABLE:
        raise DataPlatformError("content_purged_unavailable")
    input_profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == input_version.source_id))
    if input_profile is None:
        raise DataPlatformError("governance_profile_missing")
    if (input_profile.organization_id, input_profile.workspace_id, input_profile.product_code) != (
        payload.organization_id, payload.workspace_id, payload.product_code
    ):
        raise DataPlatformError("governance_scope_mismatch")
    record = DataAnonymizationRecord(
        organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code,
        input_version_id=input_version.id, output_version_id=output_version.id,
        method_code=payload.method_code.strip(), method_version=payload.method_version.strip(),
        method_reference=payload.method_reference.strip(), parameter_reference=payload.parameter_reference.strip(),
        evidence_checksum=payload.evidence_checksum.strip(), evidence_reference=payload.evidence_reference.strip(),
        classification_before=input_profile.classification, classification_after=payload.classification_after.value,
        privacy_category_before=input_profile.privacy_category, privacy_category_after=payload.privacy_category_after.value,
        status=AnonymizationStatus.PROPOSED.value, proposed_by_membership_id=actor_id,
    )
    session.add(record)
    session.flush()
    _audit(session, organization_id=payload.organization_id, workspace_id=payload.workspace_id, product_code=payload.product_code,
           actor_id=actor_id, event_type="data.anonymization.proposed", entity_type="data_anonymization_record",
           entity_id=record.id, detail=f"input_version_id={input_version.id}; output_version_id={output_version.id}; status=PROPOSED")
    return anonymization_response(record)


def review_anonymization(session: Session, *, record_id: uuid.UUID, organization_id: uuid.UUID,
                         workspace_id: uuid.UUID, product_code: str, decision: AnonymizationStatus,
                         review_reference: str, actor_id: uuid.UUID | None, review_reason: str = "",
                         now: datetime | None = None) -> AnonymizationRecordResponse:
    if not review_reference.strip():
        raise DataPlatformError("anonymization_review_reference_required")
    validate_scope(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    record = session.scalar(select(DataAnonymizationRecord).where(
        DataAnonymizationRecord.id == record_id, DataAnonymizationRecord.organization_id == organization_id,
        DataAnonymizationRecord.workspace_id == workspace_id, DataAnonymizationRecord.product_code == product_code,
    ))
    if record is None:
        raise DataPlatformError("anonymization_record_not_accessible")
    if record.status != AnonymizationStatus.PROPOSED or decision not in {AnonymizationStatus.VERIFIED, AnonymizationStatus.REJECTED}:
        raise DataPlatformError("anonymization_state_conflict")
    output = session.get(DataSourceVersion, record.output_version_id)
    if output is None or output.content_state != ContentState.AVAILABLE:
        raise DataPlatformError("content_purged_unavailable")
    record.status = decision.value
    record.reviewed_by_membership_id = actor_id
    record.reviewed_at = now or utcnow()
    record.review_reference = review_reference.strip()[:1000]
    record.review_reason = review_reason.strip()[:1000]
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type=f"data.anonymization.{decision.value.lower()}", entity_type="data_anonymization_record",
           entity_id=record.id, detail=f"status={decision.value}; output_version_id={record.output_version_id}")
    return anonymization_response(record)


SENSITIVE_CLASSIFICATIONS = {DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED}
SENSITIVE_PRIVACY = {
    PrivacyCategory.PSEUDONYMOUS_OR_LINKABLE, PrivacyCategory.PERSONAL_DATA,
    PrivacyCategory.SENSITIVE_PERSONAL_DATA,
}


def export_is_sensitive(profile: DataSourceGovernanceProfile) -> bool:
    return DataClassification(profile.classification) in SENSITIVE_CLASSIFICATIONS or PrivacyCategory(profile.privacy_category) in SENSITIVE_PRIVACY


def _export_manifest(session: Session, *, version: DataSourceVersion, profile: DataSourceGovernanceProfile,
                     actor_id: uuid.UUID | None, purpose_reference: str, outcome: str,
                     result_code: str, assurance_method: str = "", assurance_reference: str = "") -> DataExportManifest:
    manifest = DataExportManifest(
        organization_id=version.organization_id, workspace_id=version.workspace_id, product_code=version.product_code,
        source_id=version.source_id, source_version_id=version.id, actor_membership_id=actor_id,
        purpose_reference=purpose_reference[:1000], classification=profile.classification,
        privacy_category=profile.privacy_category, governance_revision=profile.revision,
        content_checksum=version.sha256, outcome=outcome, assurance_method=assurance_method[:24],
        assurance_reference=assurance_reference[:200], result_code=result_code[:120],
        completed_at=utcnow() if outcome in {"COMPLETED", "FAILED", "DENIED"} else None,
    )
    session.add(manifest)
    session.flush()
    return manifest


def record_export_failure(session: Session, *, version_id: uuid.UUID, organization_id: uuid.UUID,
                          workspace_id: uuid.UUID, product_code: str, purpose_reference: str,
                          actor_id: uuid.UUID | None, result_code: str = "storage_operation_failed") -> None:
    version, profile, _state_row, _sensitive = inspect_export(
        session, version_id=version_id, organization_id=organization_id,
        workspace_id=workspace_id, product_code=product_code,
    )
    _export_manifest(session, version=version, profile=profile, actor_id=actor_id,
                     purpose_reference=purpose_reference, outcome="FAILED", result_code=result_code)
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code,
           actor_id=actor_id, event_type="data.export.failed", entity_type="data_source_version",
           entity_id=version.id, detail=f"outcome=FAILED; reason={result_code}")


def record_export_denial(session: Session, *, version: DataSourceVersion,
                         profile: DataSourceGovernanceProfile, purpose_reference: str,
                         actor_id: uuid.UUID | None, result_code: str) -> None:
    _export_manifest(session, version=version, profile=profile, actor_id=actor_id,
                     purpose_reference=purpose_reference, outcome="DENIED", result_code=result_code)
    _audit(session, organization_id=version.organization_id, workspace_id=version.workspace_id,
           product_code=version.product_code, actor_id=actor_id, event_type="data.export.denied",
           entity_type="data_source_version", entity_id=version.id,
           detail=f"outcome=DENIED; reason={result_code}")


def inspect_export(session: Session, *, version_id: uuid.UUID, organization_id: uuid.UUID,
                   workspace_id: uuid.UUID, product_code: str) -> tuple[DataSourceVersion, DataSourceGovernanceProfile, DataRetentionState, bool]:
    version = _scoped_version(session, version_id=version_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code)
    profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == version.source_id))
    state = _state(session, version)
    if profile is None:
        raise DataPlatformError("governance_profile_missing")
    if (profile.organization_id, profile.workspace_id, profile.product_code) != (
        version.organization_id, version.workspace_id, version.product_code
    ):
        raise DataPlatformError("governance_scope_mismatch")
    return version, profile, state, export_is_sensitive(profile)


def validate_export_policy(session: Session, *, version: DataSourceVersion,
                           profile: DataSourceGovernanceProfile, state: DataRetentionState,
                           purpose_reference: str, actor_id: uuid.UUID | None) -> bool:
    purpose = " ".join(purpose_reference.split()).strip()
    if not purpose or len(purpose) > 1000:
        raise DataPlatformError("export_purpose_required")
    sensitive = export_is_sensitive(profile)
    denial = None
    if profile.governance_state not in {GovernanceState.GOVERNED, GovernanceState.FROZEN}:
        denial = "governance_incomplete_export_prohibited"
    elif profile.classification == DataClassification.UNCLASSIFIED or profile.privacy_category == PrivacyCategory.UNKNOWN:
        denial = "governance_incomplete_export_prohibited"
    elif profile.export_policy != ExportPolicy.GOVERNED_EXPORT_ALLOWED:
        denial = "governance_incomplete_export_prohibited"
    elif version.content_state != ContentState.AVAILABLE:
        denial = "content_purged_unavailable"
    elif state.hold_active:
        denial = "hold_active"
    elif not sensitive and not (
        DataClassification(profile.classification) in {DataClassification.PUBLIC, DataClassification.INTERNAL}
        and PrivacyCategory(profile.privacy_category) in {PrivacyCategory.NONE_DECLARED, PrivacyCategory.AGGREGATE_NON_PERSONAL}
    ):
        denial = "governance_incomplete_export_prohibited"
    if denial:
        record_export_denial(session, version=version, profile=profile, actor_id=actor_id,
                             purpose_reference=purpose, result_code=denial)
        raise DataPlatformError(denial)
    return sensitive


def export_source_version(session: Session, storage: StorageBackend, *, version_id: uuid.UUID,
                          organization_id: uuid.UUID, workspace_id: uuid.UUID, product_code: str,
                          purpose_reference: str, actor_id: uuid.UUID | None,
                          assurance_method: str = "", assurance_reference: str = "") -> tuple[bytes, DataExportManifest]:
    purpose = " ".join(purpose_reference.split()).strip()
    if not purpose or len(purpose) > 1000:
        raise DataPlatformError("export_purpose_required")
    version, profile, state, _sensitive = inspect_export(
        session, version_id=version_id, organization_id=organization_id,
        workspace_id=workspace_id, product_code=product_code,
    )
    validate_export_policy(session, version=version, profile=profile, state=state,
                           purpose_reference=purpose, actor_id=actor_id)
    try:
        payload = storage.get_bytes(version.storage_key)
    except StorageError:
        _export_manifest(session, version=version, profile=profile, actor_id=actor_id,
                         purpose_reference=purpose, outcome="FAILED", result_code="storage_operation_failed",
                         assurance_method=assurance_method, assurance_reference=assurance_reference)
        raise DataPlatformError("storage_operation_failed") from None
    if digest_bytes(payload) != version.sha256:
        _export_manifest(session, version=version, profile=profile, actor_id=actor_id,
                         purpose_reference=purpose, outcome="FAILED", result_code="content_checksum_mismatch",
                         assurance_method=assurance_method, assurance_reference=assurance_reference)
        raise DataPlatformError("storage_operation_failed")
    manifest = _export_manifest(session, version=version, profile=profile, actor_id=actor_id,
                                purpose_reference=purpose, outcome="COMPLETED", result_code="EXPORT_COMPLETED",
                                assurance_method=assurance_method, assurance_reference=assurance_reference)
    _audit(session, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, actor_id=actor_id,
           event_type="data.export.completed", entity_type="data_source_version", entity_id=version.id,
           detail=f"manifest_id={manifest.id}; outcome=COMPLETED; checksum={version.sha256}")
    return payload, manifest
