from __future__ import annotations

import base64
import hashlib
import inspect
import json
import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.api import data_routes
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.ingestion_run_service import (
    create_ingestion_run,
    get_ingestion_run,
    list_ingestion_runs,
    retry_ingestion_run,
)
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataIngestionRun,
    DataRecordGovernancePolicyVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.schemas import IngestionRunCreate, IngestionRunRetryRequest
from src.platform.data.service import (
    DataPlatformError,
    create_source_version,
    create_validation_job,
)
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace
from src.workers import data_jobs


def _mapping_values(*, source, connector, version_no=1, lifecycle_state="ACTIVE"):
    return {
        "source_id": source.id,
        "connector_contract_version_id": connector.id,
        "organization_id": source.organization_id,
        "workspace_id": source.workspace_id,
        "product_code": source.product_code,
        "version_no": version_no,
        "contract_format_version": 1,
        "schema_kind": "TABULAR",
        "source_schema_json": (
            '[{"logical_type":"STRING","missing_values":[],"nullable":false,'
            '"ordinal":1,"required":true,"source_field":"external_id"}]'
        ),
        "field_mapping_json": (
            '[{"disposition":"MAP","field_key":"record.id","source_field":"external_id"}]'
        ),
        "missing_value_policy": "PRESERVE_MISSING",
        "unexpected_field_policy": "REJECT",
        "fingerprint": uuid.uuid4().hex * 2,
        "lifecycle_state": lifecycle_state,
    }


def _build_case(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all(
        [
            Product(code="SIMPA", name="SIMPA", is_active=True),
            Product(code="ORDO", name="ORDO", is_active=True),
        ]
    )
    organization = Organization(slug=f"ing-{uuid.uuid4().hex}", name="Ingestion organization")
    other_organization = Organization(slug=f"other-{uuid.uuid4().hex}", name="Other organization")
    user = User(email=f"ing-{uuid.uuid4().hex}@example.invalid", display_name="Ingestion operator")
    db.add_all([organization, other_organization, user])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id, status="active")
    workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug=f"simpa-{uuid.uuid4().hex}",
        name="SIMPA ingestion",
        status="active",
    )
    other_workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug=f"simpa-other-{uuid.uuid4().hex}",
        name="Other SIMPA workspace",
        status="active",
    )
    db.add_all([membership, workspace, other_workspace])
    db.flush()
    source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Inbound dataset",
        source_kind="dataset",
        status="active",
        created_by_membership_id=membership.id,
    )
    other_source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Other inbound dataset",
        source_kind="dataset",
        status="active",
        created_by_membership_id=membership.id,
    )
    db.add_all([source, other_source])
    db.flush()
    connector = DataConnectorContractVersion(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=1,
        connector_kind="inbound",
        transport="batch",
        fingerprint="a" * 64,
        lifecycle_state="ACTIVE",
        created_by_membership_id=membership.id,
    )
    db.add(connector)
    db.flush()
    mapping = DataSourceSchemaMappingVersion(**_mapping_values(source=source, connector=connector))
    db.add(mapping)
    db.commit()
    return {
        "db": db,
        "storage": LocalFilesystemStorage(tmp_path / "storage"),
        "organization": organization,
        "workspace": workspace,
        "other_workspace": other_workspace,
        "membership": membership,
        "source": source,
        "other_source": other_source,
        "connector": connector,
        "mapping": mapping,
    }


def _request(case, **changes):
    values = {
        "organization_id": case["organization"].id,
        "workspace_id": case["workspace"].id,
        "product_code": "SIMPA",
        "connector_contract_version_id": case["connector"].id,
        "schema_mapping_version_id": case["mapping"].id,
        "idempotency_key": "adapter.batch:001",
        "filename": "batch.csv",
        "content_type": " Text/CSV ",
        "content_base64": base64.b64encode(b"external_id\n1\n").decode("ascii"),
        "cursor_after": "checkpoint-1",
    }
    values.update(changes)
    return IngestionRunCreate(**values)


def _create(case, *, request=None, raw=b"external_id\n1\n"):
    return create_ingestion_run(
        case["db"],
        case["storage"],
        source_id=case["source"].id,
        request=request or _request(case),
        payload_bytes=raw,
        actor_id=case["membership"].id,
        backend="inline",
    )


def _active_record_policy(case):
    policy = DataRecordGovernancePolicyVersion(
        source_id=case["source"].id,
        connector_contract_version_id=case["connector"].id,
        schema_mapping_version_id=case["mapping"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        version_no=1,
        contract_format_version=1,
        identity_field_keys_json='["record.id"]',
        missing_identity_policy="QUARANTINE",
        exact_duplicate_policy="LINK_EXISTING",
        conflict_policy="QUARANTINE",
        fingerprint="9" * 64,
        lifecycle_state="ACTIVE",
        created_by_membership_id=case["membership"].id,
    )
    case["db"].add(policy)
    case["db"].flush()
    return policy


def _terminal(case, run_id, status, *, attempts=1):
    run = case["db"].get(DataIngestionRun, run_id)
    job = case["db"].get(IngestionJob, run.inspection_job_id)
    version = case["db"].get(DataSourceVersion, run.source_version_id)
    run.status = status.upper()
    run.attempts = attempts
    job.status = status.lower()
    job.attempts = attempts
    version.ingest_status = status.lower()
    case["db"].flush()
    return run, job, version


def _worker(case, monkeypatch, run_id):
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    monkeypatch.setattr(
        data_jobs,
        "get_settings",
        lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024),
    )
    run = case["db"].get(DataIngestionRun, run_id)
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    return run, case["db"].get(IngestionJob, run.inspection_job_id)


def test_new_run_pins_exact_provenance_and_normalizes_materialized_content_type(tmp_path):
    case = _build_case(tmp_path)
    result = _create(case)
    assert result.reused is False
    run = case["db"].get(DataIngestionRun, result.run.id)
    version = case["db"].get(DataSourceVersion, run.source_version_id)
    job = case["db"].get(IngestionJob, run.inspection_job_id)
    assert (run.source_id, run.connector_contract_version_id, run.schema_mapping_version_id) == (
        case["source"].id,
        case["connector"].id,
        case["mapping"].id,
    )
    assert run.record_governance_policy_version_id is None
    assert result.run.record_governance_policy_version_id is None
    assert (run.source_version_id, run.inspection_job_id) == (version.id, job.id)
    assert (run.run_no, run.status, run.cursor_before, run.cursor_after) == (
        1,
        "QUEUED",
        "",
        "checkpoint-1",
    )
    assert (version.content_type, version.extension, job.job_type, job.status) == (
        "text/csv",
        "csv",
        "inspect",
        "queued",
    )
    semantic_batch = {
        "contract_format_version": 1,
        "source_id": str(case["source"].id),
        "connector_contract_version_id": str(case["connector"].id),
        "schema_mapping_version_id": str(case["mapping"].id),
        "payload_sha256": hashlib.sha256(b"external_id\n1\n").hexdigest(),
        "extension": "csv",
        "content_type": "text/csv",
        "cursor_before": "",
        "cursor_after": "checkpoint-1",
    }
    expected_fingerprint = hashlib.sha256(
        json.dumps(
            semantic_batch,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert run.request_fingerprint == expected_fingerprint
    assert result.run.model_dump().keys().isdisjoint({"idempotency_key", "content_base64"})


def test_new_run_pins_nullable_record_policy_without_changing_raw_batch_fingerprint(tmp_path):
    case = _build_case(tmp_path)
    policy = _active_record_policy(case)
    result = _create(case)
    run = case["db"].get(DataIngestionRun, result.run.id)
    assert run.record_governance_policy_version_id == policy.id
    assert result.run.record_governance_policy_version_id == policy.id
    assert "record_governance_policy_version_id" not in inspect.getsource(
        __import__(
            "src.platform.data.ingestion_run_service",
            fromlist=["_request_fingerprint"],
        )._request_fingerprint
    )


def test_retry_rejects_missing_pinned_record_policy_as_provenance_corruption(tmp_path):
    case = _build_case(tmp_path)
    _active_record_policy(case)
    created = _create(case)
    run, _job, _version = _terminal(case, created.run.id, "FAILED")
    run.record_governance_policy_version_id = uuid.uuid4()
    case["db"].flush()
    with pytest.raises(DataPlatformError, match="ingestion_run_execution_integrity_failed"):
        retry_ingestion_run(
            case["db"],
            source_id=case["source"].id,
            run_id=run.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("connector", "ingestion_run_connector_not_active"),
        ("mapping", "ingestion_run_mapping_not_active"),
    ],
)
def test_new_run_requires_active_connector_and_mapping_before_materialization(tmp_path, target, expected):
    case = _build_case(tmp_path)
    case[target].lifecycle_state = "DRAFT"
    with pytest.raises(DataPlatformError, match=expected):
        _create(case)
    assert case["db"].scalar(select(DataSourceVersion.id)) is None
    assert case["db"].scalar(select(IngestionJob.id)) is None
    assert case["db"].scalar(select(DataIngestionRun.id)) is None


def test_connector_mapping_mismatch_is_rejected_before_materialization(tmp_path):
    case = _build_case(tmp_path)
    other_connector = DataConnectorContractVersion(
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        version_no=2,
        connector_kind="replacement",
        transport="batch",
        fingerprint="b" * 64,
        lifecycle_state="ACTIVE",
    )
    case["db"].add(other_connector)
    case["db"].flush()
    with pytest.raises(DataPlatformError, match="ingestion_run_contract_mismatch"):
        _create(case, request=_request(case, connector_contract_version_id=other_connector.id))
    assert case["db"].scalar(select(DataSourceVersion.id)) is None


def test_same_key_same_semantic_request_reuses_exact_materialization(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    replay = _create(
        case,
        request=_request(case, filename="incoming/path/renamed.csv", content_type="text/csv"),
    )
    assert replay.reused is True
    assert (replay.run.id, replay.run.source_version_id, replay.run.inspection_job_id) == (
        first.run.id,
        first.run.source_version_id,
        first.run.inspection_job_id,
    )
    assert len(case["db"].scalars(select(DataIngestionRun)).all()) == 1
    assert len(case["db"].scalars(select(DataSourceVersion)).all()) == 1
    assert len(case["db"].scalars(select(IngestionJob)).all()) == 1


@pytest.mark.parametrize(
    ("request_changes", "raw"),
    [
        ({}, b"external_id\n2\n"),
        ({"cursor_after": "checkpoint-changed"}, b"external_id\n1\n"),
    ],
)
def test_same_key_changed_payload_or_cursor_conflicts(tmp_path, request_changes, raw):
    case = _build_case(tmp_path)
    _create(case)
    with pytest.raises(DataPlatformError, match="ingestion_run_idempotency_conflict"):
        _create(case, request=_request(case, **request_changes), raw=raw)


def test_same_key_changed_binding_conflicts_even_after_rollover(tmp_path):
    case = _build_case(tmp_path)
    _create(case)
    case["connector"].lifecycle_state = "RETIRED"
    case["mapping"].lifecycle_state = "RETIRED"
    connector = DataConnectorContractVersion(
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        version_no=2,
        connector_kind="rollover",
        transport="batch",
        fingerprint="c" * 64,
        lifecycle_state="ACTIVE",
    )
    case["db"].add(connector)
    case["db"].flush()
    mapping = DataSourceSchemaMappingVersion(
        **_mapping_values(source=case["source"], connector=connector, version_no=2)
    )
    case["db"].add(mapping)
    case["db"].flush()
    with pytest.raises(DataPlatformError, match="ingestion_run_idempotency_conflict"):
        _create(
            case,
            request=_request(
                case,
                connector_contract_version_id=connector.id,
                schema_mapping_version_id=mapping.id,
            ),
        )


def test_different_key_same_fingerprint_is_explicit_duplicate_batch(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case, request=_request(case, cursor_after=""))
    _terminal(case, first.run.id, "SUCCEEDED")
    with pytest.raises(DataPlatformError, match="ingestion_run_duplicate_batch"):
        _create(case, request=_request(case, idempotency_key="adapter.batch:002", cursor_after=""))


def test_only_one_live_run_per_source(tmp_path):
    case = _build_case(tmp_path)
    _create(case)
    with pytest.raises(DataPlatformError, match="ingestion_run_active_conflict"):
        _create(
            case,
            request=_request(case, idempotency_key="adapter.batch:002", cursor_after="checkpoint-2"),
            raw=b"external_id\n2\n",
        )


def test_successful_run_advances_exact_binding_cursor_and_list_is_newest_first(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    _terminal(case, first.run.id, "SUCCEEDED")
    second = _create(
        case,
        request=_request(case, idempotency_key="adapter.batch:002", cursor_after="checkpoint-2"),
        raw=b"external_id\n2\n",
    )
    assert second.run.cursor_before == "checkpoint-1"
    listed = list_ingestion_runs(
        case["db"],
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
    )
    assert [item.run_no for item in listed] == [2, 1]


def test_failed_latest_binding_requires_retry_instead_of_cursor_fork(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    _terminal(case, first.run.id, "FAILED")
    with pytest.raises(DataPlatformError, match="ingestion_run_retry_required"):
        _create(
            case,
            request=_request(case, idempotency_key="adapter.batch:002", cursor_after="checkpoint-2"),
            raw=b"external_id\n2\n",
        )


def test_retry_reuses_exact_provenance_and_attempt_history(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    run, job, _version = _terminal(case, first.run.id, "FAILED", attempts=3)
    immutable = (
        run.id,
        run.source_version_id,
        run.inspection_job_id,
        run.idempotency_key,
        run.request_fingerprint,
        run.payload_sha256,
        run.cursor_before,
        run.cursor_after,
    )
    response = retry_ingestion_run(
        case["db"],
        source_id=case["source"].id,
        run_id=run.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    assert response.status == "QUEUED"
    assert response.attempts == 3
    assert job.status == "queued" and job.attempts == 3 and job.progress == 0
    assert job.started_at is None and job.finished_at is None
    assert immutable == (
        run.id,
        run.source_version_id,
        run.inspection_job_id,
        run.idempotency_key,
        run.request_fingerprint,
        run.payload_sha256,
        run.cursor_before,
        run.cursor_after,
    )
    assert len(case["db"].scalars(select(DataSourceVersion)).all()) == 1
    assert len(case["db"].scalars(select(IngestionJob)).all()) == 1


def test_retry_rejects_nonfailed_and_unavailable_content(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    with pytest.raises(DataPlatformError, match="ingestion_run_retry_state_conflict"):
        retry_ingestion_run(
            case["db"],
            source_id=case["source"].id,
            run_id=first.run.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )
    run, _job, version = _terminal(case, first.run.id, "FAILED")
    version.content_state = "PURGED"
    with pytest.raises(DataPlatformError, match="ingestion_run_content_unavailable"):
        retry_ingestion_run(
            case["db"],
            source_id=case["source"].id,
            run_id=run.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )


def test_retry_revalidates_the_exact_pinned_binding(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    run, _job, _version = _terminal(case, first.run.id, "FAILED")
    other_connector = DataConnectorContractVersion(
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        version_no=2,
        connector_kind="corrupt-retry",
        transport="batch",
        fingerprint="e" * 64,
        lifecycle_state="ACTIVE",
    )
    case["db"].add(other_connector)
    case["db"].flush()
    run.connector_contract_version_id = other_connector.id
    case["db"].flush()
    with pytest.raises(DataPlatformError, match="ingestion_run_execution_integrity_failed"):
        retry_ingestion_run(
            case["db"],
            source_id=case["source"].id,
            run_id=run.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )


def test_retired_pinned_contracts_are_used_for_retry_and_worker_execution(tmp_path, monkeypatch):
    case = _build_case(tmp_path)
    first = _create(case)
    run = case["db"].get(DataIngestionRun, first.run.id)
    version = case["db"].get(DataSourceVersion, run.source_version_id)
    case["storage"].delete_bytes(version.storage_key)
    case["connector"].lifecycle_state = "RETIRED"
    case["mapping"].lifecycle_state = "RETIRED"
    _worker(case, monkeypatch, run.id)
    assert run.status == "FAILED"
    retry_ingestion_run(
        case["db"],
        source_id=case["source"].id,
        run_id=run.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    case["storage"].put_bytes(version.storage_key, b"external_id\n1\n")
    _worker(case, monkeypatch, run.id)
    assert run.status == "SUCCEEDED"
    assert (run.connector_contract_version_id, run.schema_mapping_version_id) == (
        case["connector"].id,
        case["mapping"].id,
    )


def test_worker_synchronizes_linked_start_success_failure_and_duplicate_is_noop(tmp_path, monkeypatch):
    case = _build_case(tmp_path)
    first = _create(case)
    run, job = _worker(case, monkeypatch, first.run.id)
    assert (run.status, job.status, run.attempts, job.attempts) == (
        "SUCCEEDED",
        "succeeded",
        1,
        1,
    )
    assert run.started_at is not None and run.finished_at is not None
    _worker(case, monkeypatch, first.run.id)
    assert (run.attempts, job.attempts) == (1, 1)
    events = [row.event_type for row in case["db"].scalars(select(DataAuditEvent)).all()]
    assert "data.ingestion_run.worker_started" in events
    assert "data.ingestion_run.worker_succeeded" in events

    second_case = _build_case(tmp_path / "failure")
    second = _create(second_case)
    second_run = second_case["db"].get(DataIngestionRun, second.run.id)
    second_version = second_case["db"].get(DataSourceVersion, second_run.source_version_id)
    second_case["storage"].delete_bytes(second_version.storage_key)
    failed_run, failed_job = _worker(second_case, monkeypatch, second.run.id)
    assert (failed_run.status, failed_job.status) == ("FAILED", "failed")
    assert (failed_run.error_code, failed_run.error_message) == (
        failed_job.error_code,
        failed_job.error_message,
    )


def test_worker_rejects_corrupt_binding_before_storage_construction(tmp_path, monkeypatch):
    case = _build_case(tmp_path)
    first = _create(case)
    run = case["db"].get(DataIngestionRun, first.run.id)
    other_connector = DataConnectorContractVersion(
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        version_no=2,
        connector_kind="corrupt",
        transport="batch",
        fingerprint="d" * 64,
        lifecycle_state="ACTIVE",
    )
    case["db"].add(other_connector)
    case["db"].flush()
    run.connector_contract_version_id = other_connector.id
    case["db"].flush()
    storage_built = False

    def _unexpected_storage():
        nonlocal storage_built
        storage_built = True
        return case["storage"]

    monkeypatch.setattr(data_jobs, "build_storage", _unexpected_storage)
    data_jobs.process_ingestion_job(case["db"], job_id=run.inspection_job_id)
    assert storage_built is False
    assert run.status == "FAILED"
    assert run.error_code == "ingestion_run_execution_integrity_failed"


def test_legacy_unlinked_inspect_and_validate_jobs_remain_compatible(tmp_path, monkeypatch):
    case = _build_case(tmp_path)
    version, inspect_job, _reused = create_source_version(
        case["db"],
        case["storage"],
        source=case["source"],
        filename="legacy.csv",
        content_type="text/csv",
        payload=b"external_id\n1\n",
        actor_id=case["membership"].id,
        backend="inline",
    )
    monkeypatch.setattr(data_jobs, "build_storage", lambda: case["storage"])
    data_jobs.process_ingestion_job(case["db"], job_id=inspect_job.id)
    assert (version.ingest_status, inspect_job.status) == ("succeeded", "succeeded")
    validation = create_validation_job(
        case["db"],
        version=version,
        actor_id=case["membership"].id,
        backend="inline",
    )
    data_jobs.process_ingestion_job(case["db"], job_id=validation.id)
    assert (version.ingest_status, validation.status) == ("succeeded", "succeeded")


def test_run_access_never_crosses_source_or_scope(tmp_path):
    case = _build_case(tmp_path)
    first = _create(case)
    with pytest.raises(DataPlatformError, match="ingestion_run_not_accessible"):
        get_ingestion_run(
            case["db"],
            source_id=case["other_source"].id,
            run_id=first.run.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
        )
    with pytest.raises(DataPlatformError, match="source_not_accessible"):
        list_ingestion_runs(
            case["db"],
            source_id=case["source"].id,
            organization_id=case["organization"].id,
            workspace_id=case["other_workspace"].id,
            product_code="SIMPA",
        )


def test_schemas_routes_permissions_errors_and_transport_neutral_boundary():
    scope = {
        "organization_id": uuid.uuid4(),
        "workspace_id": uuid.uuid4(),
        "product_code": "SIMPA",
    }
    valid = {
        **scope,
        "connector_contract_version_id": uuid.uuid4(),
        "schema_mapping_version_id": uuid.uuid4(),
        "idempotency_key": "batch:1",
        "filename": "batch.csv",
        "content_base64": "YQ==",
    }
    for changes in (
        {"cursor_before": "forbidden"},
        {"idempotency_key": "-invalid"},
        {"filename": "   "},
        {"cursor_after": " leading"},
        {"cursor_after": "control\x00"},
    ):
        with pytest.raises(ValidationError):
            IngestionRunCreate(**(valid | changes))
    with pytest.raises(ValidationError):
        IngestionRunRetryRequest(**scope, unexpected=True)

    route_methods = {
        (route.path, method)
        for route in data_routes.router.routes
        for method in getattr(route, "methods", set())
    }
    for route in (
        ("/api/v1/data/sources/{source_id}/ingestion-runs", "POST"),
        ("/api/v1/data/sources/{source_id}/ingestion-runs", "GET"),
        ("/api/v1/data/sources/{source_id}/ingestion-runs/{run_id}", "GET"),
        ("/api/v1/data/sources/{source_id}/ingestion-runs/{run_id}/retry", "POST"),
    ):
        assert route in route_methods
    expectations = (
        (data_routes.post_ingestion_run, "data.upload", "create_ingestion_run("),
        (data_routes.get_ingestion_runs, "data.read", "list_ingestion_runs("),
        (data_routes.get_ingestion_run, "data.read", "get_ingestion_run_service("),
        (data_routes.post_ingestion_run_retry, "data.upload", "retry_ingestion_run("),
    )
    for function, permission, service_call in expectations:
        source = inspect.getsource(function)
        assert source.index("_require_scope(") < source.index(service_call)
        assert f'permission_code="{permission}"' in source
    for error_code in (
        "ingestion_run_connector_not_active",
        "ingestion_run_mapping_not_active",
        "ingestion_run_contract_mismatch",
        "ingestion_run_idempotency_conflict",
        "ingestion_run_duplicate_batch",
        "ingestion_run_active_conflict",
        "ingestion_run_retry_required",
        "ingestion_run_retry_state_conflict",
        "ingestion_run_content_unavailable",
        "ingestion_run_execution_integrity_failed",
    ):
        assert data_routes._platform_error(DataPlatformError(error_code)).status_code == 409
    assert data_routes._platform_error(DataPlatformError("ingestion_run_not_accessible")).status_code == 404

    service_source = inspect.getsource(create_ingestion_run)
    for forbidden in ("requests", "httpx", "boto3", "paramiko", "socket", "subprocess", "eval(", "exec("):
        assert forbidden not in service_source
    version_creation = inspect.getsource(create_source_version)
    allocator = inspect.getsource(__import__("src.platform.data.service", fromlist=["_create_version"])._create_version)
    assert ".with_for_update()" in allocator
    assert allocator.index(".with_for_update()") < allocator.index("func.max(")
    assert "return _create_version(" in version_creation


def test_ingestion_audits_exclude_idempotency_cursor_and_payload_material(tmp_path, monkeypatch):
    case = _build_case(tmp_path)
    secret_key = "do-not-audit-idempotency"
    secret_cursor = "do-not-audit-cursor"
    raw = b"private-record-value"
    created = _create(
        case,
        request=_request(case, idempotency_key=secret_key, cursor_after=secret_cursor),
        raw=raw,
    )
    _worker(case, monkeypatch, created.run.id)
    details = "\n".join(row.detail for row in case["db"].scalars(select(DataAuditEvent)).all())
    assert secret_key not in details
    assert secret_cursor not in details
    assert raw.decode("ascii") not in details
    assert base64.b64encode(raw).decode("ascii") not in details
