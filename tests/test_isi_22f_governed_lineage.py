from __future__ import annotations

import pytest
from sqlalchemy import select

from src.platform.data.analytical_service import (
    _snapshot_fingerprint,
    create_analytical_feature, create_analytical_feature_version, get_analytical_lineage,
    create_analytical_snapshot, transition_analytical_feature_version, transition_analytical_snapshot,
)
from src.platform.data.models import (
    AnalyticalDatasetSnapshot,
    AnalyticalSnapshotGovernedOutput,
    AnalyticalSnapshotRecordInput,
    AnalyticalSnapshotSourceVersion,
    DataGovernanceInvalidation,
    DataIngestionEvaluation,
    DataNormalizedRecord,
    DataSourceGovernanceProfile,
)
from src.platform.data.schemas import (
    AnalyticalFeatureCreate,
    AnalyticalFeatureVersionCreate,
    AnalyticalSnapshotCreate,
)
from src.platform.data.service import DataPlatformError
from test_isi_21c_analytical_governance import build_analytical_case


def _new_snapshot_payload(org, ws, snapshot):
    return AnalyticalSnapshotCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        dataset_contract_version_id=snapshot.dataset_contract_version_id,
        governed_output_ids=[snapshot.governed_outputs[0].governed_output_id],
        methodology_reference="methodology:approved", methodology_version="v1",
        build_reference="build:next")


def test_snapshot_persists_exact_governed_output_and_record_membership(tmp_path):
    db, org, ws, _ws2, _ordo, _member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    lineage = get_analytical_lineage(db, snapshot_id=snapshot.id, organization_id=org.id,
                                     workspace_id=ws.id, product_code="SIMPA")
    assert lineage.snapshot.lineage_mode == "GOVERNED_OUTPUT_V1"
    assert lineage.snapshot.record_count == 1 == len(lineage.snapshot.record_membership)
    assert lineage.snapshot.governed_outputs[0].evaluation_decision == "ACCEPTED"
    assert lineage.snapshot.record_membership[0].content_fingerprint == "1" * 64


def test_membership_and_fingerprint_do_not_rewrite_after_supersession(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    fingerprint = snapshot.fingerprint
    membership = snapshot.record_membership[0]
    pinned_membership = membership.model_dump()
    db.get(DataNormalizedRecord, membership.normalized_record_id).disposition = "SUPERSEDED"
    db.flush()
    validated = transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)
    frozen = transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=validated.revision, target_state="FROZEN", actor_id=member.id)
    assert validated.fingerprint == frozen.fingerprint == fingerprint
    assert validated.record_membership[0].model_dump() == pinned_membership
    assert frozen.record_membership[0].model_dump() == pinned_membership


def test_evaluation_warning_derives_quality_and_tampering_fails_closed(tmp_path):
    warning_case = build_analytical_case(tmp_path, decision="ACCEPTED_WITH_WARNING")
    assert warning_case[-1].analytical_quality_state == "ACCEPTED_WITH_WARNING"
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(
        tmp_path / "tamper")
    edge = snapshot.governed_outputs[0]
    evaluation = db.get(DataIngestionEvaluation, edge.evaluation_id)
    evaluation.decision = "ACCEPTED_WITH_WARNING"
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_changed"):
        transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id,
            workspace_id=ws.id, product_code="SIMPA", expected_revision=1,
            target_state="VALIDATED", actor_id=member.id)


@pytest.mark.parametrize("field", ["identity_fingerprint", "content_fingerprint"])
def test_pinned_record_identity_or_content_tampering_fails_closed(tmp_path, field):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    record = db.get(DataNormalizedRecord, snapshot.record_membership[0].normalized_record_id)
    setattr(record, field, "8" * 64)
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_changed"):
        transition_analytical_snapshot(
            db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)


@pytest.mark.parametrize("disposition", ["QUARANTINED", "REJECTED", "PURGED"])
def test_ineligible_record_dispositions_do_not_enter_new_membership(tmp_path, disposition):
    db, org, ws, _ws2, _ordo, member, _source, _version, dataset, snapshot = build_analytical_case(tmp_path)
    record = db.get(DataNormalizedRecord, snapshot.record_membership[0].normalized_record_id)
    record.disposition = disposition
    db.flush()
    created = create_analytical_snapshot(
        db, dataset_id=dataset.id, payload=_new_snapshot_payload(org, ws, snapshot), actor_id=member.id)
    assert created.record_count == 0
    assert created.record_membership == []


def test_new_snapshot_rejects_unavailable_or_invalidated_source_lineage(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, source_version, dataset, snapshot = build_analytical_case(tmp_path)
    source_version.content_state = "PURGED"
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_invalidated"):
        create_analytical_snapshot(
            db, dataset_id=dataset.id, payload=_new_snapshot_payload(org, ws, snapshot), actor_id=member.id)
    source_version.content_state = "AVAILABLE"
    db.add(DataGovernanceInvalidation(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        upstream_version_id=source_version.id, reason="PURGED", actor_membership_id=member.id,
        fingerprint="7" * 64))
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_invalidated"):
        create_analytical_snapshot(
            db, dataset_id=dataset.id, payload=_new_snapshot_payload(org, ws, snapshot), actor_id=member.id)


def test_new_snapshot_rejects_incomplete_source_governance(tmp_path):
    db, org, ws, _ws2, _ordo, member, source, _version, dataset, snapshot = build_analytical_case(tmp_path)
    profile = db.scalar(select(DataSourceGovernanceProfile).where(
        DataSourceGovernanceProfile.source_id == source.id))
    profile.data_owner_ref = ""
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_governance_incomplete"):
        create_analytical_snapshot(
            db, dataset_id=dataset.id, payload=_new_snapshot_payload(org, ws, snapshot), actor_id=member.id)


def test_snapshot_fingerprint_covers_contract_output_and_record_semantics(tmp_path):
    db, _org, _ws, _ws2, _ordo, _member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    row = db.get(AnalyticalDatasetSnapshot, snapshot.id)
    outputs = list(db.scalars(select(AnalyticalSnapshotGovernedOutput).where(
        AnalyticalSnapshotGovernedOutput.snapshot_id == snapshot.id)))
    records = list(db.scalars(select(AnalyticalSnapshotRecordInput).where(
        AnalyticalSnapshotRecordInput.snapshot_id == snapshot.id)))
    baseline = _snapshot_fingerprint(row, outputs, records)

    original_contract = row.dataset_contract_fingerprint
    row.dataset_contract_fingerprint = "4" * 64
    assert _snapshot_fingerprint(row, outputs, records) != baseline
    row.dataset_contract_fingerprint = original_contract

    original_output = outputs[0].governed_output_fingerprint
    outputs[0].governed_output_fingerprint = "5" * 64
    assert _snapshot_fingerprint(row, outputs, records) != baseline
    outputs[0].governed_output_fingerprint = original_output

    original_record = records[0].content_fingerprint
    records[0].content_fingerprint = "6" * 64
    assert _snapshot_fingerprint(row, outputs, records) != baseline
    records[0].content_fingerprint = original_record
    assert _snapshot_fingerprint(row, outputs, records) == baseline == snapshot.fingerprint


def test_feature_lineage_propagates_contract_and_quality(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    validated = transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=1,
        target_state="VALIDATED", actor_id=member.id)
    feature = create_analytical_feature(db, payload=AnalyticalFeatureCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="LINEAGE",
        name="Lineage", methodology_reference="method:feature", methodology_version="v1"), actor_id=member.id)
    version = create_analytical_feature_version(db, feature_id=feature.id,
        payload=AnalyticalFeatureVersionCreate(organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", snapshot_ids=[snapshot.id], methodology_reference="method:feature",
            methodology_version="v1"), actor_id=member.id)
    governed = transition_analytical_feature_version(db, feature_version_id=version.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", expected_revision=1,
        target_state="GOVERNED", actor_id=member.id)
    assert governed.snapshot_inputs[0].dataset_contract_fingerprint == validated.dataset_contract_fingerprint
    assert governed.snapshot_inputs[0].analytical_quality_state == "ACCEPTED_CLEAN"
    with pytest.raises(DataPlatformError, match="analytical_snapshot_lifecycle_ineligible"):
        transition_analytical_feature_version(
            db, feature_version_id=version.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=governed.revision,
            target_state="FROZEN", actor_id=member.id)
    transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=validated.revision,
        target_state="FROZEN", actor_id=member.id)
    frozen = transition_analytical_feature_version(
        db, feature_version_id=version.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=governed.revision,
        target_state="FROZEN", actor_id=member.id)
    assert frozen.state == "FROZEN"


def test_new_feature_governance_rejects_legacy_snapshot_lineage(tmp_path):
    db, org, ws, _ws2, _ordo, member, source, source_version, dataset, _snapshot = build_analytical_case(tmp_path)
    legacy = AnalyticalDatasetSnapshot(
        dataset_id=dataset.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        version_no=2, methodology_reference="historical", methodology_version="v1",
        classification="CONFIDENTIAL", privacy_category="AGGREGATE_NON_PERSONAL",
        ai_use_policy="RAG_RETRIEVAL_ALLOWED", state="VALIDATED", fingerprint="9" * 64)
    db.add(legacy)
    db.flush()
    db.add(AnalyticalSnapshotSourceVersion(
        snapshot_id=legacy.id, source_version_id=source_version.id, source_id=source.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        source_version_no=source_version.version_no, classification="CONFIDENTIAL",
        privacy_category="AGGREGATE_NON_PERSONAL", ai_use_policy="RAG_RETRIEVAL_ALLOWED",
        source_fingerprint=source_version.sha256))
    db.flush()
    feature = create_analytical_feature(db, payload=AnalyticalFeatureCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="LEGACY_LINEAGE",
        name="Legacy lineage", methodology_reference="method:feature", methodology_version="v1"),
        actor_id=member.id)
    version = create_analytical_feature_version(db, feature_id=feature.id,
        payload=AnalyticalFeatureVersionCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            snapshot_ids=[legacy.id], methodology_reference="method:feature", methodology_version="v1"),
        actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_legacy_snapshot_feature_governance_forbidden"):
        transition_analytical_feature_version(
            db, feature_version_id=version.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=1, target_state="GOVERNED", actor_id=member.id)
