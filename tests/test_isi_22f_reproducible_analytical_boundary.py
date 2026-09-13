from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from src.platform.data.analytical_service import (
    activate_analytical_dataset_contract_version,
    create_analytical_dataset,
    create_analytical_dataset_contract_version,
    create_analytical_snapshot,
    list_analytical_dataset_contract_versions,
    transition_analytical_snapshot,
)
from src.platform.data.models import (
    AnalyticalDatasetSnapshot,
    AnalyticalSnapshotSourceVersion,
    DataGovernedIngestionOutput,
    DataIngestionEvaluation,
    DataSourceGovernanceProfile,
)
from src.platform.data.schemas import (
    AnalyticalDatasetContractVersionCreate,
    AnalyticalDatasetCreate,
    AnalyticalSnapshotCreate,
)
from src.platform.data.service import DataPlatformError
from src.workers import data_jobs
from test_isi_21c_analytical_governance import build_analytical_case
from test_isi_22e_ingestion_operations import build_case as build_22e_case
from test_isi_22e_ingestion_operations import create_run as create_22e_run


def _contract_payload(org, ws, *, logical_type="STRING", temporal_mode="STATIC", temporal_keys=None):
    return AnalyticalDatasetContractVersionCreate(
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        field_contract=[{"field_key": "record.id", "logical_type": logical_type,
                         "required": True, "semantic_role": "KEY"}],
        temporal_mode=temporal_mode, temporal_key_fields=temporal_keys or [],
        granularity_key_fields=["record.id"], missing_value_policy="PRESERVE_MISSING")


def _run_real_22e_case(tmp_path, monkeypatch, *, warning=False, rejected=False, dead_letter=False):
    freshness = {"missing_evidence_action": "REJECT" if rejected else "WARN"}
    dead_letter_contract = {"rejected_evaluation_to_dead_letter": dead_letter}
    case = build_22e_case(
        tmp_path, freshness_contract=freshness, dead_letter_contract=dead_letter_contract)
    case["db"].add(DataSourceGovernanceProfile(
        source_id=case["source"].id, organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code="SIMPA",
        classification="CONFIDENTIAL", privacy_category="AGGREGATE_NON_PERSONAL",
        processing_purpose="Approved analytical evidence", data_owner_ref="owner:unit",
        ai_use_policy="RAG_RETRIEVAL_ALLOWED", export_policy="PROHIBITED",
        governance_state="GOVERNED", created_by_membership_id=case["membership"].id,
        updated_by_membership_id=case["membership"].id))
    case["db"].flush()
    observed = None if warning or rejected else datetime.now(timezone.utc)
    run = create_22e_run(case, observed=observed)
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(
        data_jobs, "get_settings",
        lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    output = case["db"].scalar(select(DataGovernedIngestionOutput).where(
        DataGovernedIngestionOutput.ingestion_run_id == run.id))
    evaluation = case["db"].scalar(select(DataIngestionEvaluation).where(
        DataIngestionEvaluation.ingestion_run_id == run.id))
    return case, run, evaluation, output


def _create_dataset_contract(case, *, code="WORKER_EVIDENCE"):
    dataset = create_analytical_dataset(case["db"], payload=AnalyticalDatasetCreate(
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", code=code, name="Worker evidence",
        methodology_reference="methodology:approved", methodology_version="v1"),
        actor_id=case["membership"].id)
    contract = create_analytical_dataset_contract_version(
        case["db"], dataset_id=dataset.id,
        payload=_contract_payload(case["organization"], case["workspace"]),
        actor_id=case["membership"].id)
    activate_analytical_dataset_contract_version(
        case["db"], dataset_id=dataset.id, contract_version_id=contract.id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", actor_id=case["membership"].id)
    return dataset, contract


def _snapshot_payload(case, contract, output_id):
    return AnalyticalSnapshotCreate(
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code="SIMPA", dataset_contract_version_id=contract.id,
        governed_output_ids=[output_id], methodology_reference="methodology:approved",
        methodology_version="v1", build_reference="worker:22e")


def test_contract_fingerprint_versioning_activation_and_duplicate_rejection(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, dataset, snapshot = build_analytical_case(tmp_path)
    first = list_analytical_dataset_contract_versions(
        db, dataset_id=dataset.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA")[0]
    with pytest.raises(DataPlatformError, match="analytical_contract_unchanged"):
        create_analytical_dataset_contract_version(
            db, dataset_id=dataset.id, payload=_contract_payload(org, ws), actor_id=member.id)
    second = create_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, payload=_contract_payload(org, ws, logical_type="JSON"), actor_id=member.id)
    active = activate_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, contract_version_id=second.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", actor_id=member.id)
    rows = list_analytical_dataset_contract_versions(
        db, dataset_id=dataset.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA")
    assert second.version_no == first.version_no + 1
    assert active.lifecycle_state == "ACTIVE"
    assert [row.lifecycle_state for row in rows].count("ACTIVE") == 1
    assert snapshot.dataset_contract_fingerprint == first.fingerprint


def test_contract_temporal_granularity_and_missing_semantics_fail_closed():
    with pytest.raises(ValidationError):
        AnalyticalDatasetContractVersionCreate(
            organization_id=uuid.uuid4(), workspace_id=uuid.uuid4(), product_code="SIMPA",
            field_contract=[{"field_key": "entity", "logical_type": "STRING",
                             "required": True, "semantic_role": "KEY"}],
            temporal_mode="POINT_IN_TIME", temporal_key_fields=[],
            granularity_key_fields=["missing"])
    with pytest.raises(ValidationError):
        AnalyticalDatasetContractVersionCreate(
            organization_id=uuid.uuid4(), workspace_id=uuid.uuid4(), product_code="SIMPA",
            field_contract=[{"field_key": "entity", "logical_type": "STRING",
                             "required": True, "semantic_role": "KEY"}],
            temporal_mode="STATIC", temporal_key_fields=[], granularity_key_fields=["entity"],
            missing_value_policy="ZERO")


def test_public_snapshot_contract_rejects_raw_source_ids():
    with pytest.raises(ValidationError) as exc_info:
        AnalyticalSnapshotCreate(
            organization_id=uuid.uuid4(), workspace_id=uuid.uuid4(), product_code="SIMPA",
            dataset_contract_version_id=uuid.uuid4(), governed_output_ids=[uuid.uuid4()],
            source_version_ids=[uuid.uuid4()], methodology_reference="method:ref",
            methodology_version="v1", build_reference="build:1")
    assert any(error["loc"] == ("source_version_ids",) and error["type"] == "extra_forbidden"
               for error in exc_info.value.errors())


@pytest.mark.parametrize(
    "warning,expected_decision,expected_quality",
    [(False, "ACCEPTED", "ACCEPTED_CLEAN"),
     (True, "ACCEPTED_WITH_WARNING", "ACCEPTED_WITH_WARNING")],
)
def test_actual_22e_worker_output_builds_quality_aware_snapshot(
    tmp_path, monkeypatch, warning, expected_decision, expected_quality,
):
    case, _run, evaluation, output = _run_real_22e_case(
        tmp_path, monkeypatch, warning=warning)
    assert evaluation.decision == expected_decision and output is not None
    dataset, contract = _create_dataset_contract(case)
    snapshot = create_analytical_snapshot(
        case["db"], dataset_id=dataset.id,
        payload=_snapshot_payload(case, contract, output.id),
        actor_id=case["membership"].id)
    assert snapshot.analytical_quality_state == expected_quality
    assert snapshot.record_count == 1
    assert snapshot.governed_outputs[0].governed_output_id == output.id


@pytest.mark.parametrize(
    "dead_letter,expected_decision", [(False, "REJECTED"), (True, "DEAD_LETTERED")])
def test_rejected_or_dead_letter_22e_evidence_cannot_build_snapshot(
    tmp_path, monkeypatch, dead_letter, expected_decision,
):
    case, _run, evaluation, output = _run_real_22e_case(
        tmp_path, monkeypatch, rejected=True, dead_letter=dead_letter)
    assert evaluation.decision == expected_decision and output is None
    dataset, contract = _create_dataset_contract(case)
    with pytest.raises(DataPlatformError, match="governed_ingestion_output_not_accessible"):
        create_analytical_snapshot(
            case["db"], dataset_id=dataset.id,
            payload=_snapshot_payload(case, contract, evaluation.id),
            actor_id=case["membership"].id)


def test_legacy_snapshot_is_readable_but_cannot_be_promoted(tmp_path):
    db, org, ws, _ws2, _ordo, member, source, version, dataset, _snapshot = build_analytical_case(tmp_path)
    legacy = AnalyticalDatasetSnapshot(
        dataset_id=dataset.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        version_no=2, methodology_reference="historical", methodology_version="v1",
        classification="CONFIDENTIAL", privacy_category="AGGREGATE_NON_PERSONAL",
        ai_use_policy="RAG_RETRIEVAL_ALLOWED", state="DRAFT", fingerprint="9" * 64)
    db.add(legacy); db.flush()
    db.add(AnalyticalSnapshotSourceVersion(
        snapshot_id=legacy.id, source_version_id=version.id, source_id=source.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", source_version_no=version.version_no,
        classification="CONFIDENTIAL", privacy_category="AGGREGATE_NON_PERSONAL",
        ai_use_policy="RAG_RETRIEVAL_ALLOWED", source_fingerprint=version.sha256))
    db.flush()
    with pytest.raises(DataPlatformError, match="legacy_snapshot_promotion_forbidden"):
        transition_analytical_snapshot(
            db, snapshot_id=legacy.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id)


def test_retired_contract_cannot_create_new_snapshot(tmp_path):
    db, org, ws, _ws2, _ordo, member, _source, _version, dataset, snapshot = build_analytical_case(tmp_path)
    second = create_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, payload=_contract_payload(org, ws, logical_type="JSON"), actor_id=member.id)
    activate_analytical_dataset_contract_version(
        db, dataset_id=dataset.id, contract_version_id=second.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="analytical_contract_not_active"):
        create_analytical_snapshot(db, dataset_id=dataset.id, payload=AnalyticalSnapshotCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            dataset_contract_version_id=snapshot.dataset_contract_version_id,
            governed_output_ids=[snapshot.governed_outputs[0].governed_output_id],
            methodology_reference="method:ref", methodology_version="v1",
            build_reference="build:2"), actor_id=member.id)
