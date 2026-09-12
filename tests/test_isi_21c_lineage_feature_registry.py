from __future__ import annotations

from src.platform.data.analytical_service import (
    create_analytical_feature, create_analytical_feature_version, get_analytical_lineage,
    transition_analytical_feature_version, transition_analytical_snapshot,
)
from src.platform.data.schemas import AnalyticalFeatureCreate, AnalyticalFeatureVersionCreate
from test_isi_21c_analytical_governance import build_analytical_case


def test_typed_lineage_and_feature_inheritance(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    validated = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    feature = create_analytical_feature(db, payload=AnalyticalFeatureCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="GOVERNED-FEATURE",
        name="Governed feature", methodology_reference="methodology:approved", methodology_version="v1"), actor_id=member.id)
    version = create_analytical_feature_version(db, feature_id=feature.id, payload=AnalyticalFeatureVersionCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", snapshot_ids=[snapshot.id],
        methodology_reference="methodology:approved", methodology_version="v1"), actor_id=member.id)
    governed = transition_analytical_feature_version(db, feature_version_id=version.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=1, target_state="GOVERNED", actor_id=member.id)
    assert governed.classification == validated.classification and governed.snapshot_inputs[0].snapshot_id == snapshot.id
    transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=validated.revision, target_state="FROZEN", actor_id=member.id)
    frozen = transition_analytical_feature_version(db, feature_version_id=version.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=governed.revision, target_state="FROZEN", actor_id=member.id)
    lineage = get_analytical_lineage(db, snapshot_id=snapshot.id, organization_id=org.id,
                                     workspace_id=ws.id, product_code="SIMPA")
    assert frozen.frozen_at is not None and lineage.dependent_feature_versions[0].id == version.id
    assert lineage.snapshot.source_versions[0].source_version_id
