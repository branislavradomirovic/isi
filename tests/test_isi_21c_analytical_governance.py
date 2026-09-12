from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.analytical_service import (
    create_analytical_dataset, create_analytical_feature, create_analytical_snapshot,
    list_analytical_datasets, list_analytical_feature_versions, list_analytical_features,
    list_analytical_snapshots, transition_analytical_snapshot,
)
from src.platform.data.schemas import (
    AnalyticalDatasetCreate, AnalyticalFeatureCreate, AnalyticalSnapshotCreate, SourceGovernanceUpdate,
)
from src.platform.data.governance import inherited_ai_policy, inherited_classification, inherited_privacy
from src.platform.data.service import DataPlatformError, create_source_upload, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def build_analytical_case(tmp_path: Path, *, policy: str = "RAG_RETRIEVAL_ALLOWED"):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all([Product(code="SIMPA", name="SIMPA", is_active=True), Product(code="ORDO", name="ORDO", is_active=True)])
    org = Organization(slug="analytical", name="Analytical")
    other = Organization(slug="other", name="Other")
    user = User(email="analytical@example.invalid", display_name="Steward", is_active=True)
    db.add_all([org, other, user]); db.flush()
    member = Membership(user_id=user.id, organization_id=org.id, status="active")
    ws = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa", name="SIMPA", status="active")
    ws2 = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa-2", name="SIMPA 2", status="active")
    ordo = Workspace(organization_id=org.id, product_code="ORDO", slug="ordo", name="ORDO", status="active")
    db.add_all([member, ws, ws2, ordo]); db.flush()
    source, version, _job, _ = create_source_upload(
        db, LocalFilesystemStorage(tmp_path), organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        source_name="Governed source", filename="evidence.csv", content_type="text/csv", payload=b"evidence\n",
        actor_id=member.id, backend="inline")
    update_source_governance(
        db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=1, classification="CONFIDENTIAL",
            privacy_category="AGGREGATE_NON_PERSONAL", processing_purpose="Approved analytical evidence",
            data_owner_ref="owner:unit", ai_use_policy=policy, governance_state="GOVERNED"), actor_id=member.id)
    dataset = create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="EVIDENCE",
        name="Evidence", methodology_reference="methodology:approved", methodology_version="v1"), actor_id=member.id)
    snapshot = create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", source_version_ids=[version.id],
        methodology_reference="methodology:approved", methodology_version="v1", build_reference="build:deterministic"),
        actor_id=member.id)
    db.commit()
    return db, org, ws, ws2, ordo, member, source, version, dataset, snapshot


def test_snapshot_inheritance_lifecycle_revision_and_fingerprint(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    assert (snapshot.classification, snapshot.privacy_category, snapshot.ai_use_policy) == (
        "CONFIDENTIAL", "AGGREGATE_NON_PERSONAL", "RAG_RETRIEVAL_ALLOWED")
    assert len(snapshot.fingerprint) == 64 and len(snapshot.source_versions) == 1
    validated = transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    frozen = transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        expected_revision=validated.revision, target_state="FROZEN", actor_id=member.id)
    assert frozen.state == "FROZEN" and frozen.frozen_at is not None
    with pytest.raises(DataPlatformError, match="analytical_revision_conflict"):
        transition_analytical_snapshot(
            db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            expected_revision=1, target_state="RETIRED", actor_id=member.id)


def test_snapshot_cannot_skip_lifecycle_or_cross_scope(tmp_path):
    db, org, ws, ws2, _ordo, member, _source, version, dataset, snapshot = build_analytical_case(tmp_path)
    with pytest.raises(DataPlatformError, match="transition_invalid"):
        transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=1, target_state="FROZEN", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_dataset_not_accessible"):
        create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA", source_version_ids=[version.id],
            methodology_reference="methodology:approved", methodology_version="v1"), actor_id=member.id)


def test_registry_services_validate_scope_and_ordo_cannot_consume_simpa_lineage(tmp_path):
    db, org, ws, ws2, ordo, member, _source, version, dataset, _snapshot = build_analytical_case(tmp_path)

    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        list_analytical_datasets(
            db, organization_id=__import__("uuid").uuid4(), workspace_id=ws.id, product_code="SIMPA",
        )
    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="ORDO", code="WRONG_PRODUCT",
            name="Wrong product", methodology_reference="methodology:approved", methodology_version="v1",
        ), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_dataset_not_accessible"):
        create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA", source_version_ids=[version.id],
            methodology_reference="methodology:approved", methodology_version="v1",
        ), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_dataset_not_accessible"):
        list_analytical_snapshots(
            db, dataset_id=dataset.id, organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA",
        )

    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        list_analytical_features(
            db, organization_id=org.id, workspace_id=ordo.id, product_code="SIMPA",
        )
    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        create_analytical_feature(db, payload=AnalyticalFeatureCreate(
            organization_id=org.id, workspace_id=ordo.id, product_code="SIMPA", code="WRONG_SCOPE",
            name="Wrong scope", methodology_reference="methodology:approved", methodology_version="v1",
        ), actor_id=member.id)
    feature = create_analytical_feature(db, payload=AnalyticalFeatureCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="SCOPED_FEATURE",
        name="Scoped feature", methodology_reference="methodology:approved", methodology_version="v1",
    ), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_feature_not_accessible"):
        list_analytical_feature_versions(
            db, feature_id=feature.id, organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA",
        )

    ordo_dataset = create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
        organization_id=org.id, workspace_id=ordo.id, product_code="ORDO", code="ORDO_EVIDENCE",
        name="ORDO evidence", methodology_reference="methodology:approved", methodology_version="v1",
    ), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_lineage_scope_mismatch"):
        create_analytical_snapshot(db, dataset_id=ordo_dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=org.id, workspace_id=ordo.id, product_code="ORDO", source_version_ids=[version.id],
            methodology_reference="methodology:approved", methodology_version="v1",
        ), actor_id=member.id)


def test_fail_closed_inheritance_capability_intersection_and_no_override():
    assert inherited_classification(["PUBLIC", "UNCLASSIFIED", "RESTRICTED"]) == "UNCLASSIFIED"
    assert inherited_classification(["PUBLIC", "CONFIDENTIAL"]) == "CONFIDENTIAL"
    assert inherited_privacy(["SENSITIVE_PERSONAL_DATA", "NONE_DECLARED"]) == "NONE_DECLARED"
    assert inherited_privacy(["NONE_DECLARED", "UNKNOWN"]) == "UNKNOWN"
    assert inherited_ai_policy(["RAG_RETRIEVAL_ALLOWED", "MODEL_EVALUATION_ALLOWED"]) == "LOCAL_ANALYSIS_ONLY"
    with pytest.raises(ValidationError):
        AnalyticalSnapshotCreate(organization_id=__import__("uuid").uuid4(), workspace_id=__import__("uuid").uuid4(),
            product_code="SIMPA", source_version_ids=[__import__("uuid").uuid4()],
            methodology_reference="method:ref", methodology_version="v1", classification="PUBLIC")
