from __future__ import annotations

import hashlib
import json
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from src.domains.ordo import analytics_service as ordo_analytics_service
from src.domains.ordo import reporting_adapter as ordo_reporting_adapter
from src.domains.simpa import analytics_service as simpa_analytics_service
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import compute_indicator, create_analytics_run
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.data.analytical_service import (
    _snapshot_fingerprint,
    create_analytical_feature,
    create_analytical_feature_version,
    load_governed_analytical_input,
    transition_analytical_feature_version,
    transition_analytical_snapshot,
)
from src.platform.data.models import (
    AnalyticalDatasetContractVersion,
    AnalyticalDatasetSnapshot,
    AnalyticalSnapshotGovernedOutput,
    AnalyticalSnapshotRecordInput,
    DataNormalizedRecord,
)
from src.platform.data.service import DataPlatformError
from src.platform.data.schemas import AnalyticalFeatureCreate, AnalyticalFeatureVersionCreate
from test_isi_21c_analytical_governance import build_analytical_case


FIELDS = [
    {"field_key": "indicator_code", "logical_type": "STRING", "required": True, "semantic_role": "KEY"},
    {"field_key": "quality_status", "logical_type": "STRING", "required": True, "semantic_role": "ATTRIBUTE"},
    {"field_key": "value_numeric", "logical_type": "NUMBER", "required": False, "semantic_role": "MEASURE"},
    {"field_key": "value_text", "logical_type": "STRING", "required": False, "semantic_role": "MEASURE"},
]


def _domain_case(tmp_path):
    db, org, ws, ws2, ordo, member, source, version, dataset, response = build_analytical_case(tmp_path)
    snapshot = db.get(AnalyticalDatasetSnapshot, response.id)
    contract = db.get(AnalyticalDatasetContractVersion, snapshot.dataset_contract_version_id)
    contract.field_contract_json = json.dumps(FIELDS, sort_keys=True, separators=(",", ":"))
    contract.fingerprint = "4" * 64
    snapshot.dataset_contract_fingerprint = contract.fingerprint
    edge = db.scalar(select(AnalyticalSnapshotRecordInput).where(AnalyticalSnapshotRecordInput.snapshot_id == snapshot.id))
    record = db.get(DataNormalizedRecord, edge.normalized_record_id)
    record.normalized_record_json = json.dumps(
        {"indicator_code": "TEST", "quality_status": "validated", "value_numeric": "12.5", "value_text": None},
        sort_keys=True, separators=(",", ":"),
    )
    content_identity = {
        "contract_format_version": 1,
        "schema_mapping_version_id": str(record.schema_mapping_version_id),
        "normalized_record": json.loads(record.normalized_record_json),
    }
    record.content_fingerprint = hashlib.sha256(json.dumps(
        content_identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    edge.content_fingerprint = record.content_fingerprint
    outputs = list(db.scalars(select(AnalyticalSnapshotGovernedOutput).where(
        AnalyticalSnapshotGovernedOutput.snapshot_id == snapshot.id)))
    records = list(db.scalars(select(AnalyticalSnapshotRecordInput).where(
        AnalyticalSnapshotRecordInput.snapshot_id == snapshot.id)))
    snapshot.fingerprint = _snapshot_fingerprint(snapshot, outputs, records)
    db.flush()
    transition_analytical_snapshot(
        db, snapshot_id=snapshot.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="VALIDATED", actor_id=member.id,
    )
    return db, org, ws, ws2, ordo, member, snapshot, record


def test_loader_returns_exact_pinned_normalized_membership(tmp_path):
    db, org, ws, _ws2, _ordo, _member, snapshot, record = _domain_case(tmp_path)
    value = load_governed_analytical_input(
        db, artifact_type="snapshot", artifact_id=snapshot.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
    )
    assert value.snapshot_id == snapshot.id
    assert value.artifact_fingerprint == snapshot.fingerprint
    assert len(value.records) == 1
    assert value.records[0].normalized_record_id == record.id
    assert value.records[0].payload["value_numeric"] == "12.5"


def test_loader_fails_closed_for_scope_lifecycle_and_payload_tampering(tmp_path):
    db, org, ws, ws2, _ordo, _member, snapshot, record = _domain_case(tmp_path)
    with pytest.raises(DataPlatformError):
        load_governed_analytical_input(
            db, artifact_type="snapshot", artifact_id=snapshot.id,
            organization_id=org.id, workspace_id=ws2.id, product_code="SIMPA",
        )
    record.normalized_record_json = record.normalized_record_json.replace("12.5", "99.0")
    db.flush()
    with pytest.raises(DataPlatformError, match="analytical_upstream_changed"):
        load_governed_analytical_input(
            db, artifact_type="snapshot", artifact_id=snapshot.id,
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        )


def test_simpa_run_and_indicator_use_only_governed_normalized_record(tmp_path):
    db, org, ws, _ws2, _ordo, member, snapshot, record = _domain_case(tmp_path)
    dimension = SimpaDimension(code="TEST_DIM", name_sr="Test")
    db.add(dimension)
    db.flush()
    indicator = SimpaIndicatorDefinition(
        code="TEST", name_sr="Test indicator", dimension_code=dimension.code,
        unit_hint="unit", methodology_status="validated", methodology_note="approved",
    )
    db.add(indicator)
    db.flush()
    methodology = SimpaIndicatorMethodology(
        indicator_id=indicator.id, version_no=1, status="validated",
        computation_type="direct_observation", methodology_note="approved",
        validation_note="human approved",
    )
    db.add(methodology)
    db.flush()
    run = create_analytics_run(
        db, organization_id=org.id, workspace_id=ws.id,
        analytical_artifact_type="snapshot", analytical_artifact_id=snapshot.id,
        monitoring_cycle_id=None, actor_id=member.id,
    )
    result = compute_indicator(
        db, organization_id=org.id, workspace_id=ws.id, indicator_code="TEST",
        monitoring_cycle_id=None, analytics_run_id=run.id, actor_id=member.id,
    )
    assert run.snapshot["analytical_source"]["artifact_fingerprint"] == snapshot.fingerprint
    assert result.value_numeric == 12.5
    assert result.source_observation_ids == []
    assert result.computation_trace["normalized_record_id"] == str(record.id)


def test_single_snapshot_governed_feature_resolves_same_exact_membership(tmp_path):
    db, org, ws, _ws2, _ordo, member, snapshot, record = _domain_case(tmp_path)
    feature = create_analytical_feature(
        db,
        payload=AnalyticalFeatureCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            code="DIRECT_OBSERVATION", name="Direct observation",
            methodology_reference="method:direct", methodology_version="v1",
        ),
        actor_id=member.id,
    )
    version = create_analytical_feature_version(
        db, feature_id=feature.id,
        payload=AnalyticalFeatureVersionCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            snapshot_ids=[snapshot.id], methodology_reference="method:direct",
            methodology_version="v1",
        ), actor_id=member.id,
    )
    transition_analytical_feature_version(
        db, feature_version_id=version.id, organization_id=org.id, workspace_id=ws.id,
        product_code="SIMPA", expected_revision=1, target_state="GOVERNED", actor_id=member.id,
    )
    value = load_governed_analytical_input(
        db, artifact_type="feature_version", artifact_id=version.id,
        organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
    )
    assert value.snapshot_id == snapshot.id
    assert [item.normalized_record_id for item in value.records] == [record.id]

class _FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _ReviewSession:
    def __init__(self, *scalar_rows):
        self._scalar_rows = iter(scalar_rows)
        self.flushed = False

    def scalar(self, _statement):
        return next(self._scalar_rows)

    def get(self, *_args, **_kwargs):
        raise AssertionError("AI job lookup must not occur after governed-run revalidation rejects")

    def flush(self):
        self.flushed = True


class _ReportingSession:
    def __init__(self, runs, assessments):
        self._runs = runs
        self._assessments = assessments

    def scalars(self, _statement):
        return _FakeRows(self._runs)

    def execute(self, _statement):
        return _FakeRows(self._assessments)


def _reject_revalidation(error_type):
    def reject(*_args, **_kwargs):
        raise error_type("legacy_analytics_run")
    return reject


def test_simpa_review_synthesis_revalidates_before_mutation(monkeypatch):
    organization_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    run = SimpleNamespace(id=uuid.uuid4(), analytical_artifact_type="LEGACY_OBSERVATION")
    row = SimpleNamespace(
        id=uuid.uuid4(), organization_id=organization_id, workspace_id=workspace_id,
        analytics_run_id=run.id, ai_job_id=uuid.uuid4(), review_status="pending",
        reviewer_note="", reviewed_by_membership_id=None, reviewed_at=None,
    )
    session = _ReviewSession(row, run)
    monkeypatch.setattr(
        simpa_analytics_service, "revalidate_analytics_run",
        _reject_revalidation(simpa_analytics_service.SimpaAnalyticsError),
    )
    with pytest.raises(simpa_analytics_service.SimpaAnalyticsError, match="legacy_analytics_run"):
        simpa_analytics_service.review_synthesis(
            session, synthesis_id=row.id, organization_id=organization_id,
            workspace_id=workspace_id, decision="accepted",
            reviewer_note="must not be applied", actor_id=actor_id,
        )
    assert row.review_status == "pending"
    assert row.reviewer_note == ""
    assert row.reviewed_by_membership_id is None
    assert row.reviewed_at is None
    assert session.flushed is False


def test_ordo_review_synthesis_revalidates_before_mutation(monkeypatch):
    organization_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    run = SimpleNamespace(id=uuid.uuid4(), analytical_artifact_type="LEGACY_OBSERVATION")
    row = SimpleNamespace(
        id=uuid.uuid4(), organization_id=organization_id, workspace_id=workspace_id,
        analytics_run_id=run.id, ai_job_id=uuid.uuid4(), review_status="pending",
        reviewer_note="", reviewed_by_membership_id=None, reviewed_at=None,
    )
    session = _ReviewSession(row, run)
    monkeypatch.setattr(
        ordo_analytics_service, "revalidate_analytics_run",
        _reject_revalidation(ordo_analytics_service.OrdoAnalyticsError),
    )
    with pytest.raises(ordo_analytics_service.OrdoAnalyticsError, match="legacy_analytics_run"):
        ordo_analytics_service.review_synthesis(
            session, synthesis_id=row.id, organization_id=organization_id,
            workspace_id=workspace_id, decision="accepted",
            reviewer_note="must not be applied", actor_id=actor_id,
        )
    assert row.review_status == "pending"
    assert row.reviewer_note == ""
    assert row.reviewed_by_membership_id is None
    assert row.reviewed_at is None
    assert session.flushed is False


def test_ordo_review_scenario_assessment_revalidates_before_mutation(monkeypatch):
    organization_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    run = SimpleNamespace(id=uuid.uuid4(), analytical_artifact_type="LEGACY_OBSERVATION")
    row = SimpleNamespace(
        id=uuid.uuid4(), organization_id=organization_id, workspace_id=workspace_id,
        analytics_run_id=run.id, status="evidence_only", reviewer_note="",
        reviewed_by_membership_id=None, reviewed_at=None,
    )
    session = _ReviewSession(row, run)
    monkeypatch.setattr(
        ordo_analytics_service, "revalidate_analytics_run",
        _reject_revalidation(ordo_analytics_service.OrdoAnalyticsError),
    )
    with pytest.raises(ordo_analytics_service.OrdoAnalyticsError, match="legacy_analytics_run"):
        ordo_analytics_service.review_scenario_assessment(
            session, assessment_id=row.id, organization_id=organization_id,
            workspace_id=workspace_id, decision="reviewed",
            reviewer_note="must not be applied", actor_id=actor_id,
        )
    assert row.status == "evidence_only"
    assert row.reviewer_note == ""
    assert row.reviewed_by_membership_id is None
    assert row.reviewed_at is None
    assert session.flushed is False


def test_ordo_available_sources_keeps_assessment_with_eligible_run_outside_latest_50(monkeypatch):
    organization_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    recent_runs = [SimpleNamespace(id=uuid.uuid4(), created_at=index, status="completed") for index in range(50)]
    assessment_run = SimpleNamespace(id=uuid.uuid4(), created_at=-1, status="completed")
    assert assessment_run.id not in {row.id for row in recent_runs}
    assessment = SimpleNamespace(id=uuid.uuid4(), analytics_run_id=assessment_run.id, created_at=100, status="reviewed")
    scenario = SimpleNamespace(name="Independent assessment source")
    session = _ReportingSession(recent_runs, [(assessment, scenario, assessment_run)])
    revalidated_ids = []

    def accept_revalidation(_session, *, run, organization_id, workspace_id):
        revalidated_ids.append(run.id)
        return SimpleNamespace()

    monkeypatch.setattr(ordo_reporting_adapter, "revalidate_analytics_run", accept_revalidation)
    items = ordo_reporting_adapter.available_sources(session, organization_id=organization_id, workspace_id=workspace_id)
    assessment_items = [item for item in items if item["kind"] == "scenario_assessment"]
    assert len(assessment_items) == 1
    assert assessment_items[0]["id"] == str(assessment.id)
    assert assessment_run.id in revalidated_ids
