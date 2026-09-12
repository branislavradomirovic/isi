from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

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
    AnalyticalDatasetSnapshot,
    AnalyticalFeature,
    AnalyticalFeatureSnapshotInput,
    AnalyticalFeatureVersion,
    AnalyticalSnapshotSourceVersion,
    DataAuditEvent,
    DataGovernanceInvalidation,
    DataSourceGovernanceProfile,
    DataSourceVersion,
)
from src.platform.data.schemas import (
    AnalyticalAIEligibilityResponse,
    AnalyticalDatasetCreate,
    AnalyticalDatasetResponse,
    AnalyticalFeatureCreate,
    AnalyticalFeatureResponse,
    AnalyticalFeatureVersionCreate,
    AnalyticalFeatureVersionResponse,
    AnalyticalLineageResponse,
    AnalyticalSnapshotCreate,
    AnalyticalSnapshotResponse,
    SnapshotInputResponse,
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


def _source_edges(session: Session, snapshot_id: uuid.UUID) -> list[AnalyticalSnapshotSourceVersion]:
    return list(session.scalars(select(AnalyticalSnapshotSourceVersion).where(
        AnalyticalSnapshotSourceVersion.snapshot_id == snapshot_id
    ).order_by(AnalyticalSnapshotSourceVersion.source_version_id)))


def _snapshot_response(session: Session, row: AnalyticalDatasetSnapshot) -> AnalyticalSnapshotResponse:
    edges = _source_edges(session, row.id)
    return AnalyticalSnapshotResponse(
        id=row.id, dataset_id=row.dataset_id, organization_id=row.organization_id, workspace_id=row.workspace_id,
        product_code=row.product_code, version_no=row.version_no, methodology_reference=row.methodology_reference,
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


def _load_sources(session: Session, ids: list[uuid.UUID], *, organization_id: uuid.UUID,
                  workspace_id: uuid.UUID, product_code: str) -> list[tuple[DataSourceVersion, DataSourceGovernanceProfile]]:
    unique_ids = list(dict.fromkeys(ids))
    if not unique_ids:
        raise DataPlatformError("analytical_snapshot_inputs_required")
    versions = session.scalars(select(DataSourceVersion).where(DataSourceVersion.id.in_(unique_ids)).order_by(DataSourceVersion.id)).all()
    by_id = {row.id: row for row in versions}
    if len(by_id) != len(unique_ids):
        raise DataPlatformError("source_version_not_accessible")
    result = []
    for source_id in unique_ids:
        version = by_id[source_id]
        if (version.organization_id, version.workspace_id, version.product_code) != (organization_id, workspace_id, product_code):
            raise DataPlatformError("analytical_lineage_scope_mismatch")
        profile = session.scalar(select(DataSourceGovernanceProfile).where(
            DataSourceGovernanceProfile.source_id == version.source_id,
            *_scope(DataSourceGovernanceProfile, organization_id, workspace_id, product_code),
        ))
        if profile is None:
            raise DataPlatformError("source_governance_missing")
        result.append((version, profile))
    return result


def _snapshot_fingerprint(row: AnalyticalDatasetSnapshot, edges: list[AnalyticalSnapshotSourceVersion]) -> str:
    return _fingerprint({
        "dataset_id": row.dataset_id, "version_no": row.version_no, "organization_id": row.organization_id,
        "workspace_id": row.workspace_id, "product_code": row.product_code,
        "methodology_reference": row.methodology_reference, "methodology_version": row.methodology_version,
        "build_reference": row.build_reference, "classification": row.classification,
        "privacy_category": row.privacy_category, "ai_use_policy": row.ai_use_policy,
        "sources": [{"id": edge.source_version_id, "version": edge.source_version_no,
                     "fingerprint": edge.source_fingerprint, "classification": edge.classification,
                     "privacy": edge.privacy_category, "policy": edge.ai_use_policy} for edge in edges],
    })


def create_analytical_snapshot(session: Session, *, dataset_id: uuid.UUID, payload: AnalyticalSnapshotCreate,
                               actor_id: uuid.UUID | None) -> AnalyticalSnapshotResponse:
    dataset = _get_dataset(session, dataset_id, payload.organization_id, payload.workspace_id, payload.product_code)
    sources = _load_sources(session, payload.source_version_ids, organization_id=payload.organization_id,
                            workspace_id=payload.workspace_id, product_code=payload.product_code)
    next_version = (session.scalar(select(func.max(AnalyticalDatasetSnapshot.version_no)).where(
        AnalyticalDatasetSnapshot.dataset_id == dataset.id)) or 0) + 1
    row = AnalyticalDatasetSnapshot(
        dataset_id=dataset.id, organization_id=dataset.organization_id, workspace_id=dataset.workspace_id,
        product_code=dataset.product_code, version_no=next_version,
        methodology_reference=payload.methodology_reference, methodology_version=payload.methodology_version,
        build_reference=payload.build_reference,
        classification=inherited_classification([profile.classification for _, profile in sources]).value,
        privacy_category=inherited_privacy([profile.privacy_category for _, profile in sources]).value,
        ai_use_policy=inherited_ai_policy([profile.ai_use_policy for _, profile in sources]).value,
        fingerprint="0" * 64, created_by_membership_id=actor_id, updated_by_membership_id=actor_id,
    )
    session.add(row); session.flush()
    edges = [AnalyticalSnapshotSourceVersion(
        snapshot_id=row.id, source_version_id=version.id, source_id=version.source_id,
        organization_id=version.organization_id, workspace_id=version.workspace_id, product_code=version.product_code,
        source_version_no=version.version_no, classification=profile.classification,
        privacy_category=profile.privacy_category, ai_use_policy=profile.ai_use_policy,
        source_fingerprint=version.sha256,
    ) for version, profile in sources]
    session.add_all(edges); session.flush()
    row.fingerprint = _snapshot_fingerprint(row, sorted(edges, key=lambda edge: str(edge.source_version_id)))
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


def _sources_valid(session: Session, snapshot: AnalyticalDatasetSnapshot, *, refresh: bool) -> list[AnalyticalSnapshotSourceVersion]:
    edges = _source_edges(session, snapshot.id)
    if not edges:
        raise DataPlatformError("analytical_snapshot_inputs_required")
    for edge in edges:
        version = session.scalar(select(DataSourceVersion).where(DataSourceVersion.id == edge.source_version_id))
        profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == edge.source_id))
        invalidated = session.scalar(select(DataGovernanceInvalidation.id).where(
            DataGovernanceInvalidation.upstream_version_id == edge.source_version_id))
        if version is None or profile is None or (
            version.organization_id, version.workspace_id, version.product_code
        ) != (snapshot.organization_id, snapshot.workspace_id, snapshot.product_code):
            raise DataPlatformError("analytical_lineage_scope_mismatch")
        if version.content_state != ContentState.AVAILABLE or invalidated is not None:
            raise DataPlatformError("analytical_upstream_invalidated")
        if profile.governance_state not in {GovernanceState.GOVERNED, GovernanceState.FROZEN}:
            raise DataPlatformError("analytical_upstream_not_governed")
        if profile.classification == DataClassification.UNCLASSIFIED or profile.privacy_category in {
            PrivacyCategory.UNKNOWN, PrivacyCategory.NONE_DECLARED
        }:
            raise DataPlatformError("analytical_upstream_governance_incomplete")
        current = (profile.classification, profile.privacy_category, profile.ai_use_policy, version.sha256)
        recorded = (edge.classification, edge.privacy_category, edge.ai_use_policy, edge.source_fingerprint)
        if refresh:
            edge.classification, edge.privacy_category, edge.ai_use_policy, edge.source_fingerprint = current
        elif current != recorded:
            raise DataPlatformError("analytical_upstream_changed")
    if refresh:
        snapshot.classification = inherited_classification([edge.classification for edge in edges]).value
        snapshot.privacy_category = inherited_privacy([edge.privacy_category for edge in edges]).value
        snapshot.ai_use_policy = inherited_ai_policy([edge.ai_use_policy for edge in edges]).value
        snapshot.fingerprint = _snapshot_fingerprint(snapshot, edges)
    return edges


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
        _sources_valid(session, row, refresh=target is AnalyticalSnapshotState.VALIDATED)
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
                       "fingerprint": edge.snapshot_fingerprint} for edge in edges],
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
        allowed_states = {AnalyticalSnapshotState.FROZEN} if frozen else {
            AnalyticalSnapshotState.VALIDATED, AnalyticalSnapshotState.FROZEN}
        if AnalyticalSnapshotState(snapshot.state) not in allowed_states:
            raise DataPlatformError("analytical_snapshot_lifecycle_ineligible")
        if refresh:
            edge.snapshot_version_no, edge.snapshot_fingerprint = snapshot.version_no, snapshot.fingerprint
        elif (edge.snapshot_version_no, edge.snapshot_fingerprint) != (snapshot.version_no, snapshot.fingerprint):
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
    snapshot_ids = session.scalars(select(AnalyticalSnapshotSourceVersion.snapshot_id).where(
        AnalyticalSnapshotSourceVersion.source_version_id == source_version_id,
        *_scope(AnalyticalSnapshotSourceVersion, organization_id, workspace_id, product_code))).all()
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
        edges = _source_edges(session, snapshot.id)
        if not edges:
            return "UPSTREAM_LINEAGE_MISSING"
        for edge in edges:
            if (edge.organization_id, edge.workspace_id, edge.product_code) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
            version = session.get(DataSourceVersion, edge.source_version_id)
            invalidation = session.scalar(select(DataGovernanceInvalidation.id).where(
                DataGovernanceInvalidation.upstream_version_id == edge.source_version_id))
            if version is None or (version.organization_id, version.workspace_id, version.product_code) != (
                artifact.organization_id, artifact.workspace_id, artifact.product_code
            ):
                return "UPSTREAM_SCOPE_INCONSISTENT"
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
