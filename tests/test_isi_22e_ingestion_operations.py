from __future__ import annotations

import base64
import inspect
import json
import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.api import data_routes
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.ingestion_operations_service import (
    activate_ingestion_operational_policy_version,
    create_ingestion_operational_policy_version,
    create_or_get_governed_ingestion_output,
    create_or_get_ingestion_evaluation,
    list_ingestion_dead_letters,
    record_ingestion_failure_dead_letter,
    requeue_ingestion_dead_letter,
    resolve_ingestion_dead_letter,
)
from src.platform.data.ingestion_run_service import (
    _backfill_request_fingerprint,
    _replay_request_fingerprint,
    _request_fingerprint,
    create_backfill_ingestion_run,
    create_ingestion_run,
    create_replay_ingestion_run,
)
from src.platform.data.models import (
    DataGovernedIngestionOutput,
    DataIngestionDeadLetter,
    DataIngestionEvaluation,
    DataIngestionOperationalPolicyVersion,
    DataIngestionRun,
    DataNormalizedRecord,
    DataQualityResult,
    DataRecordGovernancePolicyVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataConnectorContractVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.schemas import (
    IngestionBackfillCreate,
    IngestionDeadLetterResolveRequest,
    IngestionDeadLetterRequeueRequest,
    IngestionOperationalPolicyVersionCreate,
    IngestionReplayCreate,
    IngestionRunCreate,
)
from src.platform.data.service import DataPlatformError
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace
from src.workers import data_jobs


def build_case(tmp_path, *, product="SIMPA", policy=True, **policy_changes):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all([Product(code="SIMPA", name="SIMPA", is_active=True), Product(code="ORDO", name="ORDO", is_active=True)])
    marker = uuid.uuid4().hex
    organization = Organization(slug=f"ops-{marker}", name="Synthetic operations")
    user = User(email=f"ops-{marker}@example.invalid", display_name="Operator")
    db.add_all([organization, user]); db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id, status="active")
    workspace = Workspace(organization_id=organization.id, product_code=product,
                          slug=f"ops-{marker}", name="Synthetic workspace", status="active")
    db.add_all([membership, workspace]); db.flush()
    source = DataSource(organization_id=organization.id, workspace_id=workspace.id,
        product_code=product, name="Synthetic source", source_kind="dataset", status="active")
    db.add(source); db.flush()
    connector = DataConnectorContractVersion(source_id=source.id, organization_id=organization.id,
        workspace_id=workspace.id, product_code=product, version_no=1, connector_kind="synthetic",
        transport="batch", fingerprint="a" * 64, lifecycle_state="ACTIVE")
    db.add(connector); db.flush()
    mapping = DataSourceSchemaMappingVersion(source_id=source.id,
        connector_contract_version_id=connector.id, organization_id=organization.id,
        workspace_id=workspace.id, product_code=product, version_no=1, contract_format_version=1,
        schema_kind="TABULAR", source_schema_json='[{"logical_type":"STRING","missing_values":[],"nullable":false,"ordinal":1,"required":true,"source_field":"id"}]',
        field_mapping_json='[{"disposition":"MAP","field_key":"record.id","source_field":"id"}]',
        missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
        fingerprint="b" * 64, lifecycle_state="ACTIVE")
    db.add(mapping); db.flush()
    record_policy = DataRecordGovernancePolicyVersion(source_id=source.id,
        connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
        organization_id=organization.id, workspace_id=workspace.id, product_code=product,
        version_no=1, contract_format_version=1, identity_field_keys_json='["record.id"]',
        missing_identity_policy="QUARANTINE", exact_duplicate_policy="LINK_EXISTING",
        conflict_policy="QUARANTINE", fingerprint="c" * 64, lifecycle_state="ACTIVE")
    db.add(record_policy); db.flush()
    case = dict(db=db, engine=engine, organization=organization, workspace=workspace,
                membership=membership, source=source, connector=connector, mapping=mapping,
                record_policy=record_policy, storage=LocalFilesystemStorage(tmp_path / marker))
    if policy:
        create_policy(case, **policy_changes)
    db.commit()
    return case


def policy_payload(case, **changes):
    values = dict(organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=case["source"].product_code, connector_contract_version_id=case["connector"].id,
        schema_mapping_version_id=case["mapping"].id,
        record_governance_policy_version_id=case["record_policy"].id,
        freshness_contract={"warning_after_seconds": 60, "reject_after_seconds": 300, "missing_evidence_action": "WARN"},
        quality_contract={"required_check_codes": [], "warning_quarantine_ratio": .1,
                          "reject_quarantine_ratio": .5, "missing_required_check_action": "REJECT"},
        backfill_contract={"backfill_allowed": True, "replay_allowed": True,
                           "require_explicit_window": True, "cursor_mutation_allowed": False},
        dead_letter_contract={"max_retry_attempts": 2, "terminal_error_codes": ["synthetic.terminal"],
                              "rejected_evaluation_to_dead_letter": False})
    for key, value in changes.items():
        if key in values and isinstance(values[key], dict) and isinstance(value, dict): values[key].update(value)
        else: values[key] = value
    return IngestionOperationalPolicyVersionCreate(**values)


def create_policy(case, **changes):
    result = create_ingestion_operational_policy_version(case["db"], source_id=case["source"].id,
        payload=policy_payload(case, **changes), actor_id=case["membership"].id)
    activate_ingestion_operational_policy_version(case["db"], source_id=case["source"].id,
        policy_version_id=result.id, organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        actor_id=case["membership"].id)
    case["operational_policy"] = case["db"].get(DataIngestionOperationalPolicyVersion, result.id)
    return result


def run_request(case, key="run:1", cursor="cursor:1", observed=None):
    return IngestionRunCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        connector_contract_version_id=case["connector"].id,
        schema_mapping_version_id=case["mapping"].id, idempotency_key=key,
        filename="batch.csv", content_type="text/csv",
        content_base64=base64.b64encode(b"id\n1\n").decode(), cursor_after=cursor,
        source_observed_at=observed)


def create_run(case, key="run:1", cursor="cursor:1", observed=None, raw=b"id\n1\n"):
    response = create_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        request=run_request(case, key, cursor, observed), payload_bytes=raw,
        actor_id=case["membership"].id, backend="inline")
    return case["db"].get(DataIngestionRun, response.run.id)


def finish(case, run, status="SUCCEEDED"):
    run.status = status
    job = case["db"].get(IngestionJob, run.inspection_job_id); job.status = status.lower()
    version = case["db"].get(DataSourceVersion, run.source_version_id); version.ingest_status = status.lower()
    case["db"].flush()


def add_quality(case, run, code="required.synthetic", status="pass"):
    case["db"].add(DataQualityResult(version_id=run.source_version_id, check_code=code, status=status))
    case["db"].flush()


def test_policy_creation_fingerprinting_unchanged_rejection_and_activation_binding(tmp_path):
    case = build_case(tmp_path, policy=False)
    first = create_policy(case)
    with pytest.raises(DataPlatformError, match="operational_policy_unchanged"):
        create_ingestion_operational_policy_version(case["db"], source_id=case["source"].id,
            payload=policy_payload(case), actor_id=case["membership"].id)
    assert len(first.fingerprint) == 64 and first.lifecycle_state == "DRAFT"
    assert case["operational_policy"].lifecycle_state == "ACTIVE"


def test_historical_policy_version_is_pinned_when_new_policy_activates(tmp_path):
    case = build_case(tmp_path)
    run = create_run(case)
    pinned = run.operational_policy_version_id
    case["operational_policy"].lifecycle_state = "RETIRED"
    second = create_policy(case, freshness_contract={"warning_after_seconds": 61})
    assert run.operational_policy_version_id == pinned and second.id != pinned


@pytest.mark.parametrize("missing_action,expected", [("WARN", ("UNKNOWN", "ACCEPTED_WITH_WARNING")), ("REJECT", ("UNKNOWN", "REJECTED"))])
def test_missing_freshness_evidence_is_policy_governed(tmp_path, missing_action, expected):
    case = build_case(tmp_path, freshness_contract={"missing_evidence_action": missing_action})
    run = create_run(case); add_quality(case, run)
    result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert (result.freshness_status, result.decision) == expected


@pytest.mark.parametrize("age,expected", [(10, "FRESH"), (100, "STALE_WARNING"), (500, "STALE_REJECTED")])
def test_freshness_uses_persisted_queued_time(tmp_path, age, expected):
    case = build_case(tmp_path)
    run = create_run(case); run.source_observed_at = run.queued_at - timedelta(seconds=age); add_quality(case, run)
    result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.freshness_status == expected
    assert result.freshness_details["reference_queued_at"]


def test_future_freshness_evidence_is_clamped_and_recorded(tmp_path):
    case = build_case(tmp_path); run = create_run(case)
    run.source_observed_at = run.queued_at + timedelta(seconds=30)
    result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.freshness_status == "FRESH"
    assert result.freshness_details["age_seconds"] == 0
    assert result.freshness_details["future_evidence_clamped_to_zero"] is True


@pytest.mark.parametrize("state,expected", [("pass", "PASS"), ("warn", "WARNING"), ("fail", "REJECTED"), (None, "REJECTED")])
def test_required_quality_check_states(tmp_path, state, expected):
    case = build_case(tmp_path, quality_contract={"required_check_codes": ["required.synthetic"]})
    run = create_run(case); run.source_observed_at = run.queued_at
    if state: add_quality(case, run, status=state)
    result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.quality_status == expected


def test_missing_required_quality_check_can_warn(tmp_path):
    case = build_case(tmp_path, quality_contract={"required_check_codes": ["required.synthetic"],
                                                  "missing_required_check_action": "WARN"})
    run = create_run(case); run.source_observed_at = run.queued_at
    result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.quality_status == "WARNING" and result.decision == "ACCEPTED_WITH_WARNING"


@pytest.mark.parametrize("quarantined,total,expected", [(0, 0, (0.0, "PASS")), (1, 5, (.2, "WARNING")), (3, 5, (.6, "REJECTED"))])
def test_quarantine_ratio_and_zero_record_semantics(tmp_path, quarantined, total, expected):
    case = build_case(tmp_path); run = create_run(case); run.source_observed_at = run.queued_at
    for ordinal in range(1, total + 1):
        case["db"].add(DataNormalizedRecord(source_id=run.source_id, source_version_id=run.source_version_id,
            ingestion_run_id=run.id, connector_contract_version_id=run.connector_contract_version_id,
            schema_mapping_version_id=run.schema_mapping_version_id,
            record_governance_policy_version_id=run.record_governance_policy_version_id,
            organization_id=run.organization_id, workspace_id=run.workspace_id, product_code=run.product_code,
            source_record_ordinal=ordinal, source_locator=f"synthetic:{ordinal}", entity_id=None,
            normalized_record_json="{}", identity_fingerprint=f"{ordinal:064x}", content_fingerprint=f"{ordinal+1:064x}",
            disposition="QUARANTINED" if ordinal <= quarantined else "REJECTED",
            quarantine_reason="synthetic" if ordinal <= quarantined else None))
    case["db"].flush(); result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.record_metrics["quarantine_ratio"] == expected[0]
    assert result.quality_status == expected[1]


def test_evaluation_fingerprint_and_output_are_immutable_and_idempotent(tmp_path):
    case = build_case(tmp_path); run = create_run(case); run.source_observed_at = run.queued_at
    first = create_or_get_ingestion_evaluation(case["db"], run=run)
    second = create_or_get_ingestion_evaluation(case["db"], run=run)
    output1 = create_or_get_governed_ingestion_output(case["db"], run=run)
    output2 = create_or_get_governed_ingestion_output(case["db"], run=run)
    assert first.id == second.id and first.evidence_fingerprint == second.evidence_fingerprint
    assert output1.id == output2.id and case["db"].scalar(select(func.count(DataGovernedIngestionOutput.id))) == 1


def test_rejected_evaluation_has_no_governed_output_and_optional_dead_letter(tmp_path):
    case = build_case(tmp_path, freshness_contract={"missing_evidence_action": "REJECT"},
                      dead_letter_contract={"rejected_evaluation_to_dead_letter": True})
    run = create_run(case); result = create_or_get_ingestion_evaluation(case["db"], run=run)
    assert result.decision == "DEAD_LETTERED"
    with pytest.raises(DataPlatformError, match="governed_output_decision_conflict"):
        create_or_get_governed_ingestion_output(case["db"], run=run)
    assert case["db"].scalar(select(func.count(DataIngestionDeadLetter.id))) == 1


def test_dead_letter_terminal_retry_budget_quarantine_distinction_and_resolution(tmp_path):
    case = build_case(tmp_path); run = create_run(case); run.attempts = 1
    case["db"].add(DataNormalizedRecord(source_id=run.source_id, source_version_id=run.source_version_id,
        ingestion_run_id=run.id, connector_contract_version_id=run.connector_contract_version_id,
        schema_mapping_version_id=run.schema_mapping_version_id,
        record_governance_policy_version_id=run.record_governance_policy_version_id,
        organization_id=run.organization_id, workspace_id=run.workspace_id, product_code=run.product_code,
        source_record_ordinal=1, source_locator="synthetic:quarantine", entity_id=None,
        normalized_record_json="{}", identity_fingerprint="1" * 64, content_fingerprint="2" * 64,
        disposition="QUARANTINED", quarantine_reason="synthetic")); case["db"].flush()
    assert case["db"].scalar(select(func.count(DataIngestionDeadLetter.id))) == 0
    assert record_ingestion_failure_dead_letter(case["db"], run=run, reason_code="transient", error_category="IO") is None
    terminal = record_ingestion_failure_dead_letter(case["db"], run=run, reason_code="synthetic.terminal", error_category="IO")
    assert terminal.status == "OPEN"
    assert record_ingestion_failure_dead_letter(case["db"], run=run, reason_code="synthetic.terminal", error_category="IO").id == terminal.id
    request = IngestionDeadLetterResolveRequest(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        status="DISCARDED", resolution_note="Synthetic failure reviewed.")
    resolved = resolve_ingestion_dead_letter(case["db"], source_id=case["source"].id,
        dead_letter_id=terminal.id, request=request, actor_id=case["membership"].id)
    assert resolved.status == "DISCARDED" and resolved.resolver_membership_id == case["membership"].id
    assert len(list_ingestion_dead_letters(case["db"], source_id=case["source"].id,
        organization_id=case["organization"].id, workspace_id=case["workspace"].id,
        product_code=case["source"].product_code)) == 1


def test_dead_letter_requeue_creates_controlled_replay(tmp_path):
    case = build_case(tmp_path); run = create_run(case); finish(case, run, "FAILED"); run.attempts = 2
    dead = record_ingestion_failure_dead_letter(case["db"], run=run, reason_code="retry.exhausted",
                                                error_category="IO")
    request = IngestionDeadLetterRequeueRequest(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        idempotency_key="dead:requeue")
    result = requeue_ingestion_dead_letter(case["db"], case["storage"],
        source_id=case["source"].id, dead_letter_id=dead.id, request=request,
        actor_id=case["membership"].id, backend="inline")
    replacement = case["db"].get(DataIngestionRun, result.replacement_run_id)
    assert result.status == "REQUEUED" and replacement.execution_mode == "REPLAY"
    assert replacement.replay_of_run_id == run.id and replacement.forward_cursor_committed is False


def test_dead_letter_requeue_is_idempotent_after_committed_replacement(tmp_path):
    case = build_case(tmp_path); run = create_run(case); finish(case, run, "FAILED"); run.attempts = 2
    dead = record_ingestion_failure_dead_letter(case["db"], run=run, reason_code="retry.exhausted",
                                                error_category="IO")
    request = IngestionDeadLetterRequeueRequest(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        idempotency_key="dead:requeue")
    first = requeue_ingestion_dead_letter(case["db"], case["storage"],
        source_id=case["source"].id, dead_letter_id=dead.id, request=request,
        actor_id=case["membership"].id, backend="inline")
    case["db"].commit()
    persisted = case["db"].get(DataIngestionDeadLetter, dead.id)
    historical = (persisted.resolved_at, persisted.resolver_membership_id, persisted.resolution_note)

    second = requeue_ingestion_dead_letter(case["db"], case["storage"],
        source_id=case["source"].id, dead_letter_id=dead.id, request=request,
        actor_id=case["membership"].id, backend="inline")
    assert second.id == first.id and second.replacement_run_id == first.replacement_run_id
    assert case["db"].scalar(select(func.count(DataIngestionRun.id)).where(
        DataIngestionRun.replay_of_run_id == run.id, DataIngestionRun.execution_mode == "REPLAY")) == 1
    persisted = case["db"].get(DataIngestionDeadLetter, dead.id)
    assert (persisted.resolved_at, persisted.resolver_membership_id, persisted.resolution_note) == historical

    conflict = request.model_copy(update={"idempotency_key": "dead:other"})
    with pytest.raises(DataPlatformError, match="ingestion_dead_letter_state_conflict"):
        requeue_ingestion_dead_letter(case["db"], case["storage"],
            source_id=case["source"].id, dead_letter_id=dead.id, request=conflict,
            actor_id=case["membership"].id, backend="inline")
    assert case["db"].scalar(select(func.count(DataIngestionRun.id)).where(
        DataIngestionRun.replay_of_run_id == run.id, DataIngestionRun.execution_mode == "REPLAY")) == 1


def test_backfill_idempotent_retry_survives_policy_rotation(tmp_path):
    case = build_case(tmp_path)
    request = IngestionBackfillCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        connector_contract_version_id=case["connector"].id,
        schema_mapping_version_id=case["mapping"].id, idempotency_key="backfill:rotation",
        filename="backfill.csv", content_type="text/csv",
        content_base64=base64.b64encode(b"id\n2\n").decode(),
        window_start_cursor="opaque:a", window_end_cursor="opaque:b")
    first = create_backfill_ingestion_run(case["db"], case["storage"],
        source_id=case["source"].id, request=request, payload_bytes=b"id\n2\n",
        actor_id=case["membership"].id, backend="inline")
    pinned_policy_id = first.run.operational_policy_version_id
    create_policy(case, backfill_contract={"backfill_allowed": False})
    before = tuple(case["db"].scalar(select(func.count(model.id))) for model in (
        DataSourceVersion, IngestionJob, DataIngestionRun))

    retry = create_backfill_ingestion_run(case["db"], case["storage"],
        source_id=case["source"].id, request=request, payload_bytes=b"id\n2\n",
        actor_id=case["membership"].id, backend="inline")
    assert retry.reused is True and retry.run.id == first.run.id
    assert retry.run.operational_policy_version_id == pinned_policy_id
    assert case["db"].get(DataIngestionOperationalPolicyVersion, pinned_policy_id).lifecycle_state == "RETIRED"
    assert tuple(case["db"].scalar(select(func.count(model.id))) for model in (
        DataSourceVersion, IngestionJob, DataIngestionRun)) == before

    conflict = request.model_copy(update={"window_end_cursor": "opaque:other"})
    with pytest.raises(DataPlatformError, match="ingestion_run_idempotency_conflict"):
        create_backfill_ingestion_run(case["db"], case["storage"],
            source_id=case["source"].id, request=conflict, payload_bytes=b"id\n2\n",
            actor_id=case["membership"].id, backend="inline")


def test_backfill_and_replay_use_mode_specific_request_fingerprints():
    source, connector, mapping, record, policy, parent = [uuid.uuid4() for _ in range(6)]
    historical = _request_fingerprint(source_id=source, connector_contract_version_id=connector,
        schema_mapping_version_id=mapping, payload_sha256="a" * 64, extension="csv",
        content_type="text/csv", cursor_before="opaque:a", cursor_after="opaque:b")
    backfill = _backfill_request_fingerprint(source_id=source, connector_contract_version_id=connector,
        schema_mapping_version_id=mapping, payload_sha256="a" * 64, extension="csv",
        content_type="text/csv", source_observed_at=None, window_start_cursor="opaque:a", window_end_cursor="opaque:b")
    replay = _replay_request_fingerprint(replay_of_run_id=parent, source_id=source,
        connector_contract_version_id=connector, schema_mapping_version_id=mapping,
        record_governance_policy_version_id=record, operational_policy_version_id=policy,
        payload_sha256="a" * 64)
    assert len({historical, backfill, replay}) == 3
    source_text = inspect.getsource(_request_fingerprint)
    assert "execution_mode" not in source_text and "source_observed_at" not in source_text


def test_replay_reuses_original_bytes_via_new_source_version(tmp_path):
    case = build_case(tmp_path); parent = create_run(case); finish(case, parent)
    original_version_id = parent.source_version_id
    request = IngestionReplayCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        idempotency_key="replay:1")
    result = create_replay_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        run_id=parent.id, request=request, actor_id=case["membership"].id, backend="inline")
    replay = case["db"].get(DataIngestionRun, result.run.id)
    assert replay.source_version_id != original_version_id and replay.inspection_job_id != parent.inspection_job_id
    assert replay.payload_sha256 == parent.payload_sha256 and replay.replay_of_run_id == parent.id
    assert (replay.connector_contract_version_id, replay.schema_mapping_version_id,
            replay.record_governance_policy_version_id, replay.operational_policy_version_id) == (
            parent.connector_contract_version_id, parent.schema_mapping_version_id,
            parent.record_governance_policy_version_id, parent.operational_policy_version_id)
    with pytest.raises(ValidationError):
        IngestionReplayCreate(**request.model_dump(), content_base64="replacement")


def test_incremental_idempotency_rejects_source_observed_at_drift(tmp_path):
    case = build_case(tmp_path); run = create_run(case); observed = run.queued_at
    with pytest.raises(DataPlatformError, match="ingestion_run_idempotency_conflict"):
        create_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
            request=run_request(case, observed=observed), payload_bytes=b"id\n1\n",
            actor_id=case["membership"].id, backend="inline")


def test_backfill_and_replay_share_source_live_run_exclusion(tmp_path):
    case = build_case(tmp_path); live = create_run(case)
    backfill = IngestionBackfillCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code,
        connector_contract_version_id=case["connector"].id, schema_mapping_version_id=case["mapping"].id,
        idempotency_key="backfill:1", filename="backfill.csv", content_type="text/csv",
        content_base64=base64.b64encode(b"id\n2\n").decode(), window_start_cursor="a", window_end_cursor="b")
    with pytest.raises(DataPlatformError, match="ingestion_run_active_conflict"):
        create_backfill_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
            request=backfill, payload_bytes=b"id\n2\n", actor_id=None, backend="inline")
    finish(case, live)
    replay_request = IngestionReplayCreate(organization_id=case["organization"].id,
        workspace_id=case["workspace"].id, product_code=case["source"].product_code, idempotency_key="replay:1")
    replay = create_replay_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
        run_id=live.id, request=replay_request, actor_id=None, backend="inline")
    with pytest.raises(DataPlatformError, match="ingestion_run_active_conflict"):
        create_ingestion_run(case["db"], case["storage"], source_id=case["source"].id,
            request=run_request(case, key="next:1"), payload_bytes=b"id\n1\n", actor_id=None, backend="inline")
    assert replay.run.execution_mode == "REPLAY"


def test_backfill_request_rejects_forward_cursor_after(tmp_path):
    case = build_case(tmp_path)
    with pytest.raises(ValidationError):
        IngestionBackfillCreate(organization_id=case["organization"].id,
            workspace_id=case["workspace"].id, product_code="SIMPA",
            connector_contract_version_id=case["connector"].id, schema_mapping_version_id=case["mapping"].id,
            idempotency_key="backfill:1", filename="batch.csv", content_base64="eA==",
            window_start_cursor="a", window_end_cursor="b", cursor_after="forbidden")


def test_rejected_governed_run_stays_technically_succeeded_without_cursor_commit(tmp_path, monkeypatch):
    case = build_case(tmp_path, freshness_contract={"missing_evidence_action": "REJECT"})
    run = create_run(case)
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    evaluation = case["db"].scalar(select(DataIngestionEvaluation).where(DataIngestionEvaluation.ingestion_run_id == run.id))
    assert run.status == "SUCCEEDED" and case["db"].get(IngestionJob, run.inspection_job_id).status == "succeeded"
    assert evaluation.decision == "REJECTED" and run.forward_cursor_committed is False
    assert case["db"].scalar(select(func.count(DataGovernedIngestionOutput.id))) == 0


def test_legacy_no_operational_policy_compatibility(tmp_path, monkeypatch):
    case = build_case(tmp_path, policy=False); run = create_run(case)
    assert run.operational_policy_version_id is None
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    assert run.status == "SUCCEEDED" and run.forward_cursor_committed is True
    assert case["db"].scalar(select(func.count(DataIngestionEvaluation.id))) == 0


def test_scope_product_access_fails_closed(tmp_path):
    case = build_case(tmp_path)
    with pytest.raises(DataPlatformError):
        list_ingestion_dead_letters(case["db"], source_id=case["source"].id,
            organization_id=case["organization"].id, workspace_id=case["workspace"].id,
            product_code="ORDO")
    assert data_routes._platform_error(DataPlatformError("ingestion_evaluation_not_accessible")).status_code == 404
