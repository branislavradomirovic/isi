from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.analytical_service import (
    activate_analytical_dataset_contract_version, create_analytical_dataset,
    create_analytical_dataset_contract_version, create_analytical_feature, create_analytical_snapshot,
    list_analytical_datasets, list_analytical_feature_versions, list_analytical_features,
    transition_analytical_snapshot,
)
from src.platform.data.schemas import (
    AnalyticalDatasetContractVersionCreate, AnalyticalDatasetCreate, AnalyticalFeatureCreate,
    AnalyticalSnapshotCreate, SourceGovernanceUpdate,
)
from src.platform.data.models import (
    DataConnectorContractVersion, DataGovernedIngestionOutput, DataIngestionEvaluation,
    DataIngestionOperationalPolicyVersion, DataIngestionRun, DataNormalizedRecord,
    DataRecordGovernancePolicyVersion, DataSourceSchemaMappingVersion,
)
from src.platform.data.governance import inherited_ai_policy, inherited_classification, inherited_privacy
from src.platform.data.service import DataPlatformError, create_source_upload, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def build_analytical_case(tmp_path: Path, *, policy: str = "RAG_RETRIEVAL_ALLOWED",
                          decision: str = "ACCEPTED"):
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
    source, version, job, _ = create_source_upload(
        db, LocalFilesystemStorage(tmp_path), organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        source_name="Governed source", filename="evidence.csv", content_type="text/csv", payload=b"evidence\n",
        actor_id=member.id, backend="inline")
    update_source_governance(
        db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=1, classification="CONFIDENTIAL",
            privacy_category="AGGREGATE_NON_PERSONAL", processing_purpose="Approved analytical evidence",
            data_owner_ref="owner:unit", ai_use_policy=policy, governance_state="GOVERNED"), actor_id=member.id)
    connector = DataConnectorContractVersion(
        source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        version_no=1, connector_kind="synthetic", transport="batch", fingerprint="a" * 64,
        lifecycle_state="ACTIVE")
    db.add(connector); db.flush()
    mapping = DataSourceSchemaMappingVersion(
        source_id=source.id, connector_contract_version_id=connector.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", version_no=1, contract_format_version=1,
        schema_kind="TABULAR", source_schema_json="[]", field_mapping_json="[]",
        missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
        fingerprint="b" * 64, lifecycle_state="ACTIVE")
    db.add(mapping); db.flush()
    record_policy = DataRecordGovernancePolicyVersion(
        source_id=source.id, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", version_no=1, contract_format_version=1,
        identity_field_keys_json='["record.id"]', missing_identity_policy="QUARANTINE",
        exact_duplicate_policy="LINK_EXISTING", conflict_policy="QUARANTINE",
        fingerprint="c" * 64, lifecycle_state="ACTIVE")
    db.add(record_policy); db.flush()
    operational_policy = DataIngestionOperationalPolicyVersion(
        source_id=source.id, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, record_governance_policy_version_id=record_policy.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", version_no=1,
        contract_format_version=1, freshness_contract_json="{}", quality_contract_json="{}",
        backfill_contract_json="{}", dead_letter_contract_json="{}", fingerprint="d" * 64,
        lifecycle_state="ACTIVE")
    db.add(operational_policy); db.flush()
    run = DataIngestionRun(
        source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        run_no=1, connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        record_governance_policy_version_id=record_policy.id,
        operational_policy_version_id=operational_policy.id, source_version_id=version.id,
        inspection_job_id=job.id, idempotency_key="analytical:1", request_fingerprint="e" * 64,
        payload_sha256=version.sha256, status="SUCCEEDED")
    db.add(run); db.flush()
    record = DataNormalizedRecord(
        source_id=source.id, source_version_id=version.id, ingestion_run_id=run.id,
        connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        record_governance_policy_version_id=record_policy.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", source_record_ordinal=1,
        source_locator="row:1", normalized_record_json='{"record.id":"1"}',
        identity_fingerprint="f" * 64, content_fingerprint="1" * 64,
        disposition="ACCEPTED")
    db.add(record); db.flush()
    evaluation = DataIngestionEvaluation(
        source_id=source.id, ingestion_run_id=run.id, operational_policy_version_id=operational_policy.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        freshness_status="FRESH", quality_status=("WARNING" if decision == "ACCEPTED_WITH_WARNING" else "PASS"),
        decision=decision,
        freshness_details_json="{}", quality_details_json="{}", record_metrics_json="{}",
        evidence_fingerprint="2" * 64)
    db.add(evaluation); db.flush()
    output = DataGovernedIngestionOutput(
        source_id=source.id, source_version_id=version.id, ingestion_run_id=run.id,
        evaluation_id=evaluation.id, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, record_governance_policy_version_id=record_policy.id,
        operational_policy_version_id=operational_policy.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", contract_version=1, record_count=1,
        current_record_count=1, duplicate_record_count=0, quarantined_record_count=0,
        superseded_record_count=0, output_fingerprint="3" * 64)
    db.add(output); db.flush()
    dataset = create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", code="EVIDENCE",
        name="Evidence", methodology_reference="methodology:approved", methodology_version="v1"), actor_id=member.id)
    contract = create_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, payload=AnalyticalDatasetContractVersionCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            field_contract=[{"field_key": "record.id", "logical_type": "STRING",
                             "required": True, "semantic_role": "KEY"}],
            temporal_mode="STATIC", temporal_key_fields=[],
            granularity_key_fields=["record.id"]), actor_id=member.id)
    activate_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, contract_version_id=contract.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", actor_id=member.id)
    snapshot = create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        dataset_contract_version_id=contract.id, governed_output_ids=[output.id],
        methodology_reference="methodology:approved", methodology_version="v1", build_reference="build:deterministic"),
        actor_id=member.id)
    db.commit()
    return db, org, ws, ws2, ordo, member, source, version, dataset, snapshot


def _create_scoped_dataset_contract(db, *, organization, workspace, product_code, code, actor_id):
    dataset = create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
        organization_id=organization.id, workspace_id=workspace.id, product_code=product_code,
        code=code, name=code, methodology_reference="methodology:approved", methodology_version="v1"),
        actor_id=actor_id)
    contract = create_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, payload=AnalyticalDatasetContractVersionCreate(
            organization_id=organization.id, workspace_id=workspace.id, product_code=product_code,
            field_contract=[{"field_key": "record.id", "logical_type": "STRING",
                             "required": True, "semantic_role": "KEY"}],
            temporal_mode="STATIC", temporal_key_fields=[], granularity_key_fields=["record.id"]),
        actor_id=actor_id)
    activate_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, contract_version_id=contract.id,
        organization_id=organization.id, workspace_id=workspace.id, product_code=product_code,
        actor_id=actor_id)
    return dataset, contract


def test_snapshot_inheritance_lifecycle_revision_and_fingerprint(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, _dataset, snapshot = build_analytical_case(tmp_path)
    assert (snapshot.classification, snapshot.privacy_category, snapshot.ai_use_policy) == (
        "CONFIDENTIAL", "AGGREGATE_NON_PERSONAL", "RAG_RETRIEVAL_ALLOWED")
    assert len(snapshot.fingerprint) == 64 and len(snapshot.governed_outputs) == 1
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
    db, org, ws, ws2, _ordo, member, _source, _version, dataset, snapshot = build_analytical_case(tmp_path)
    with pytest.raises(DataPlatformError, match="transition_invalid"):
        transition_analytical_snapshot(db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=1, target_state="FROZEN", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_dataset_not_accessible"):
        create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA",
            dataset_contract_version_id=snapshot.dataset_contract_version_id,
            governed_output_ids=[snapshot.governed_outputs[0].governed_output_id],
            methodology_reference="methodology:approved", methodology_version="v1",
            build_reference="build:cross-workspace"), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=__import__("uuid").uuid4(), workspace_id=ws.id, product_code="SIMPA",
            dataset_contract_version_id=snapshot.dataset_contract_version_id,
            governed_output_ids=[snapshot.governed_outputs[0].governed_output_id],
            methodology_reference="methodology:approved", methodology_version="v1",
            build_reference="build:cross-organization"), actor_id=member.id)


def test_registry_services_validate_scope_and_ordo_cannot_consume_simpa_lineage(tmp_path):
    db, org, ws, ws2, ordo, member, _source, _version, dataset, snapshot = build_analytical_case(tmp_path)

    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        list_analytical_datasets(
            db, organization_id=__import__("uuid").uuid4(), workspace_id=ws.id, product_code="SIMPA",
        )
    with pytest.raises(DataPlatformError, match="workspace_scope_mismatch"):
        create_analytical_dataset(db, payload=AnalyticalDatasetCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="ORDO", code="WRONG_PRODUCT",
            name="Wrong product", methodology_reference="methodology:approved", methodology_version="v1",
        ), actor_id=member.id)
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

    other = db.query(Organization).filter_by(slug="other").one()
    other_ws = Workspace(organization_id=other.id, product_code="SIMPA", slug="other-simpa",
                         name="Other SIMPA", status="active")
    db.add(other_ws)
    db.flush()
    targets = [
        (org, ws2, "SIMPA", "CROSS_WORKSPACE", member.id),
        (org, ordo, "ORDO", "CROSS_PRODUCT", member.id),
        (other, other_ws, "SIMPA", "CROSS_ORGANIZATION", None),
    ]
    for target_org, target_ws, product_code, code, actor_id in targets:
        target_dataset, target_contract = _create_scoped_dataset_contract(
            db, organization=target_org, workspace=target_ws, product_code=product_code,
            code=code, actor_id=actor_id)
        with pytest.raises(DataPlatformError, match="analytical_lineage_scope_mismatch"):
            create_analytical_snapshot(db, dataset_id=target_dataset.id, payload=AnalyticalSnapshotCreate(
                organization_id=target_org.id, workspace_id=target_ws.id, product_code=product_code,
                dataset_contract_version_id=target_contract.id,
                governed_output_ids=[snapshot.governed_outputs[0].governed_output_id],
                methodology_reference="methodology:approved", methodology_version="v1",
                build_reference=f"build:{code.casefold()}"), actor_id=actor_id)


def test_fail_closed_inheritance_capability_intersection_and_no_override():
    assert inherited_classification(["PUBLIC", "UNCLASSIFIED", "RESTRICTED"]) == "UNCLASSIFIED"
    assert inherited_classification(["PUBLIC", "CONFIDENTIAL"]) == "CONFIDENTIAL"
    assert inherited_privacy(["SENSITIVE_PERSONAL_DATA", "NONE_DECLARED"]) == "NONE_DECLARED"
    assert inherited_privacy(["NONE_DECLARED", "UNKNOWN"]) == "UNKNOWN"
    assert inherited_ai_policy(["RAG_RETRIEVAL_ALLOWED", "MODEL_EVALUATION_ALLOWED"]) == "LOCAL_ANALYSIS_ONLY"
    with pytest.raises(ValidationError):
        AnalyticalSnapshotCreate(organization_id=__import__("uuid").uuid4(), workspace_id=__import__("uuid").uuid4(),
            product_code="SIMPA", dataset_contract_version_id=__import__("uuid").uuid4(),
            governed_output_ids=[__import__("uuid").uuid4()],
            methodology_reference="method:ref", methodology_version="v1", classification="PUBLIC")
