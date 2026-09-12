"""Integrated ISI-21 acceptance across source, analytical, AI, and retention boundaries."""

from __future__ import annotations

from sqlalchemy import select

from src.platform.ai.namespaces import private_namespace
from src.platform.data.analytical_service import (
    create_analytical_feature, create_analytical_feature_version, evaluate_analytical_ai_eligibility,
    transition_analytical_feature_version, transition_analytical_snapshot,
)
from src.platform.data.models import AnalyticalDatasetSnapshot, AnalyticalFeatureVersion, DataRetentionState
from src.platform.data.privacy_service import approve_purge, execute_purge, request_purge
from src.platform.data.schemas import (
    AnalyticalFeatureCreate, AnalyticalFeatureVersionCreate, RetentionPolicyCreate, SourceGovernanceUpdate,
)
from src.platform.data.service import create_retention_policy, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage
from test_isi_21c_analytical_governance import build_analytical_case


def test_source_snapshot_feature_purge_and_ai_fail_closed_integration(tmp_path):
    db, org, ws, _ws2, _ordo, member, source, source_version, _dataset, snapshot = build_analytical_case(tmp_path)
    validated = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    frozen_snapshot = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=validated.revision, target_state="FROZEN", actor_id=member.id)
    feature = create_analytical_feature(db, payload=AnalyticalFeatureCreate(organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", code="INTEGRATED", name="Integrated", methodology_reference="method:ref",
        methodology_version="v1"), actor_id=member.id)
    feature_version = create_analytical_feature_version(db, feature_id=feature.id, payload=AnalyticalFeatureVersionCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", snapshot_ids=[snapshot.id],
        methodology_reference="method:ref", methodology_version="v1"), actor_id=member.id)
    governed = transition_analytical_feature_version(db, feature_version_id=feature_version.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=1, target_state="GOVERNED", actor_id=member.id)
    frozen_feature = transition_analytical_feature_version(db, feature_version_id=feature_version.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=governed.revision, target_state="FROZEN", actor_id=member.id)
    namespace = private_namespace(org.id, "SIMPA")
    assert evaluate_analytical_ai_eligibility(db, artifact_type="feature_version", artifact_id=frozen_feature.id,
        action="RAG_RETRIEVAL", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace).allowed

    ordo_boundary = evaluate_analytical_ai_eligibility(
        db, artifact_type="feature_version", artifact_id=frozen_feature.id, action="RAG_RETRIEVAL",
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        namespace=private_namespace(org.id, "ORDO"),
    )
    assert not ordo_boundary.allowed
    assert ordo_boundary.reason_code == "NAMESPACE_SCOPE_MISMATCH"
    assert ordo_boundary.product_code == "SIMPA"

    policy = create_retention_policy(db, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        payload=RetentionPolicyCreate(policy_code="PURGE", version_no=1, name="Purge", retention_days=0,
                                      no_auto_delete=False), actor_id=member.id)
    update_source_governance(db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=2, retention_policy_id=policy.id), actor_id=member.id)
    state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == source_version.id))
    requested = request_purge(db, version_id=source_version.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=state.revision, actor_id=member.id)
    approved = approve_purge(db, version_id=source_version.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=requested.revision, actor_id=member.id)
    execute_purge(db, LocalFilesystemStorage(tmp_path), version_id=source_version.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=approved.revision, actor_id=member.id)
    assert db.get(AnalyticalDatasetSnapshot, frozen_snapshot.id).invalidated
    assert db.get(AnalyticalFeatureVersion, frozen_feature.id).invalidated
    denied = evaluate_analytical_ai_eligibility(db, artifact_type="feature_version", artifact_id=frozen_feature.id,
        action="RAG_RETRIEVAL", organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", namespace=namespace)
    assert not denied.allowed and denied.reason_code == "ARTIFACT_INVALIDATED"
    assert denied.provenance_fingerprint == frozen_feature.fingerprint
    assert denied.human_review_required
    assert "formula" not in frozen_feature.methodology_reference.casefold()
