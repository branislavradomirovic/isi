from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.models import (
    DataConnectorContractVersion,
    DataGovernanceInvalidation,
    DataIngestionRun,
    DataNormalizedRecord,
    DataRecordEntity,
    DataRecordGovernancePolicyVersion,
    DataRetentionState,
    DataSourceVersion,
    DataSourceSchemaMappingVersion,
    IngestionJob,
)
from src.platform.data.privacy_service import approve_purge, execute_purge, place_hold, release_hold, request_purge, utcnow
from src.platform.data.schemas import RetentionPolicyCreate, SourceGovernanceUpdate
from src.platform.data.service import DataPlatformError, create_retention_policy, create_source_upload, create_source_version, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage, StorageError
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


@pytest.fixture()
def governed(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all([Product(code="SIMPA", name="SIMPA", is_active=True), Product(code="ORDO", name="ORDO", is_active=True)])
    org = Organization(slug="privacy", name="Privacy")
    foreign_org = Organization(slug="foreign", name="Foreign")
    user = User(email="privacy@example.invalid", display_name="Privacy", is_active=True)
    db.add_all([org, foreign_org, user]); db.flush()
    member = Membership(user_id=user.id, organization_id=org.id, status="active")
    ws = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa", name="SIMPA", status="active")
    foreign_ws = Workspace(organization_id=foreign_org.id, product_code="SIMPA", slug="foreign", name="Foreign", status="active")
    db.add_all([member, ws, foreign_ws]); db.flush()
    storage = LocalFilesystemStorage(tmp_path)
    source, version, _job, _ = create_source_upload(
        db, storage, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        source_name="Source one", filename="one.csv", content_type="text/csv", payload=b"shared-content\n",
        actor_id=member.id, backend="inline",
    )
    policy = create_retention_policy(
        db, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        payload=RetentionPolicyCreate(policy_code="PURGE-0", version_no=1, name="Immediate", retention_days=0,
                                      no_auto_delete=False), actor_id=member.id,
    )
    update_source_governance(
        db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=1, retention_policy_id=policy.id), actor_id=member.id,
    )
    db.commit()
    yield db, org, ws, foreign_org, foreign_ws, member, source, version, policy, storage
    db.close()


def test_due_calculation_assignment_new_version_removal_and_fail_closed_policies(governed):
    db, org, ws, _fo, _fw, member, source, first, _policy, storage = governed
    first_state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == first.id))
    assert first_state.retention_due_at == first_state.retention_start_at
    second, _job, _ = create_source_version(db, storage, source=source, filename="two.csv", content_type="text/csv",
                                             payload=b"second\n", actor_id=member.id, backend="inline")
    second_state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == second.id))
    assert second_state.retention_due_at == second_state.retention_start_at
    update_source_governance(db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                             update=SourceGovernanceUpdate(expected_revision=2, retention_policy_id=None), actor_id=member.id)
    assert all(state.retention_due_at is None for state in db.scalars(select(DataRetentionState).where(DataRetentionState.source_id == source.id)))
    no_delete = create_retention_policy(
        db, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        payload=RetentionPolicyCreate(policy_code="NO-DELETE", version_no=1, name="No delete", retention_days=1,
                                      no_auto_delete=True), actor_id=member.id)
    update_source_governance(db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                             update=SourceGovernanceUpdate(expected_revision=3, retention_policy_id=no_delete.id), actor_id=member.id)
    assert all(state.retention_due_at is None for state in db.scalars(select(DataRetentionState).where(DataRetentionState.source_id == source.id)))
    indefinite = create_retention_policy(
        db, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        payload=RetentionPolicyCreate(policy_code="INDEFINITE", version_no=1, name="Indefinite", retention_days=None,
                                      no_auto_delete=False), actor_id=member.id)
    update_source_governance(db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                             update=SourceGovernanceUpdate(expected_revision=4, retention_policy_id=indefinite.id), actor_id=member.id)
    assert all(state.retention_due_at is None for state in db.scalars(select(DataRetentionState).where(DataRetentionState.source_id == source.id)))


def test_hold_atomic_revision_and_blocks_every_purge_stage(governed):
    db, org, ws, _fo, _fw, member, _source, version, _policy, _storage = governed
    state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
    old_revision = state.revision
    held = place_hold(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                      expected_revision=state.revision, reason_reference="legal-case:synthetic", actor_id=member.id)
    assert held.hold_active and held.revision == old_revision + 1
    with pytest.raises(DataPlatformError, match="retention_revision_conflict"):
        release_hold(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                     expected_revision=old_revision, actor_id=member.id)
    with pytest.raises(DataPlatformError, match="hold_active"):
        request_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                      expected_revision=held.revision, actor_id=member.id)
    released = release_hold(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                            expected_revision=held.revision, actor_id=member.id)
    requested = request_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                              expected_revision=released.revision, actor_id=member.id)
    with pytest.raises(DataPlatformError, match="retention_revision_conflict"):
        approve_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                      expected_revision=released.revision, actor_id=member.id)
    placed_after_request = place_hold(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                                      product_code="SIMPA", expected_revision=requested.revision,
                                      reason_reference="administrative:pause", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="hold_active"):
        approve_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                      expected_revision=placed_after_request.revision, actor_id=member.id)


def _approve(db, org, ws, member, version):
    state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
    requested = request_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                              product_code="SIMPA", expected_revision=state.revision, actor_id=member.id)
    return approve_purge(db, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                         product_code="SIMPA", expected_revision=requested.revision, actor_id=member.id)


def test_reference_safe_purge_tombstone_invalidation_and_scope_isolation(governed):
    db, org, ws, foreign_org, foreign_ws, member, source, first, policy, storage = governed
    second_source, second, _job, reused = create_source_upload(
        db, storage, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", source_name="Source two",
        filename="same.csv", content_type="text/csv", payload=b"shared-content\n", actor_id=member.id, backend="inline")
    assert reused and first.storage_key == second.storage_key
    update_source_governance(db, source_id=second_source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                             update=SourceGovernanceUpdate(expected_revision=1, retention_policy_id=policy.id), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="version_not_accessible"):
        request_purge(db, version_id=first.id, organization_id=foreign_org.id, workspace_id=foreign_ws.id,
                      product_code="SIMPA", expected_revision=1, actor_id=member.id)
    approved_first = _approve(db, org, ws, member, first)
    held = place_hold(db, version_id=first.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                      expected_revision=approved_first.revision, reason_reference="case:after-approval", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="hold_active"):
        execute_purge(db, storage, version_id=first.id, organization_id=org.id, workspace_id=ws.id,
                      product_code="SIMPA", expected_revision=held.revision, actor_id=member.id)
    released = release_hold(db, version_id=first.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
                            expected_revision=held.revision, actor_id=member.id)
    purged_first = execute_purge(db, storage, version_id=first.id, organization_id=org.id, workspace_id=ws.id,
                                 product_code="SIMPA", expected_revision=released.revision, actor_id=member.id)
    assert purged_first.purge_result == "LOGICAL_ONLY_SHARED_OBJECT_RETAINED"
    assert storage.exists(first.storage_key)
    approved_second = _approve(db, org, ws, member, second)
    purged_second = execute_purge(db, storage, version_id=second.id, organization_id=org.id, workspace_id=ws.id,
                                  product_code="SIMPA", expected_revision=approved_second.revision, actor_id=member.id)
    assert purged_second.purge_result == "PHYSICAL_OBJECT_DELETED"
    assert not storage.exists(second.storage_key)
    assert db.get(DataSourceVersion, first.id).content_state == "PURGED"
    assert purged_first.tombstone_checksum
    assert db.scalar(select(func.count()).select_from(DataGovernanceInvalidation)) == 2


def test_storage_failure_never_reports_success_and_keeps_content_available(governed):
    db, org, ws, _fo, _fw, member, _source, version, _policy, storage = governed
    approved = _approve(db, org, ws, member, version)

    class FailingStorage:
        def delete_bytes(self, key):
            raise StorageError("provider secret must not escape")

    with pytest.raises(DataPlatformError, match="storage_operation_failed"):
        execute_purge(db, FailingStorage(), version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                      product_code="SIMPA", expected_revision=approved.revision, actor_id=member.id)
    assert db.get(DataSourceVersion, version.id).content_state == "AVAILABLE"
    state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
    assert state.purge_status == "FAILED" and state.purge_result == "STORAGE_OPERATION_FAILED"
    assert "secret" not in state.purge_result
    assert storage.exists(version.storage_key)


def test_local_delete_is_exact_idempotent_and_cannot_escape_root(tmp_path):
    storage = LocalFilesystemStorage(tmp_path / "objects")
    assert storage.put_bytes("org/SIMPA/ws/object.bin", b"object") is True
    assert storage.delete_bytes("org/SIMPA/ws/object.bin") is True
    assert storage.delete_bytes("org/SIMPA/ws/object.bin") is False
    with pytest.raises(StorageError, match="unsafe storage key"):
        storage.delete_bytes("../outside.bin")
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "objects"
    root.mkdir(exist_ok=True)
    (root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(StorageError, match="unsafe storage key"):
        storage.delete_bytes("link/outside.bin")


def _seed_22d_purge_graph(db, source, first, second):
    connector = DataConnectorContractVersion(
        source_id=source.id, organization_id=source.organization_id,
        workspace_id=source.workspace_id, product_code=source.product_code,
        version_no=1, connector_kind="purge", transport="batch",
        fingerprint="a" * 64, lifecycle_state="ACTIVE",
    )
    db.add(connector); db.flush()
    mapping = DataSourceSchemaMappingVersion(
        source_id=source.id, connector_contract_version_id=connector.id,
        organization_id=source.organization_id, workspace_id=source.workspace_id,
        product_code=source.product_code, version_no=1, contract_format_version=1,
        schema_kind="TABULAR",
        source_schema_json='[{"logical_type":"STRING","missing_values":[],"nullable":false,"ordinal":1,"required":true,"source_field":"id"}]',
        field_mapping_json='[{"disposition":"MAP","field_key":"record.id","source_field":"id"}]',
        missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
        fingerprint="b" * 64, lifecycle_state="ACTIVE",
    )
    db.add(mapping); db.flush()
    policy = DataRecordGovernancePolicyVersion(
        source_id=source.id, connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id, organization_id=source.organization_id,
        workspace_id=source.workspace_id, product_code=source.product_code,
        version_no=1, contract_format_version=1,
        identity_field_keys_json='["record.id"]', missing_identity_policy="QUARANTINE",
        exact_duplicate_policy="LINK_EXISTING", conflict_policy="QUARANTINE",
        fingerprint="c" * 64, lifecycle_state="ACTIVE",
    )
    db.add(policy); db.flush()

    def run_for(version, number):
        job = db.scalar(select(IngestionJob).where(IngestionJob.version_id == version.id).order_by(IngestionJob.id))
        run = DataIngestionRun(
            source_id=source.id, organization_id=source.organization_id,
            workspace_id=source.workspace_id, product_code=source.product_code,
            run_no=number, connector_contract_version_id=connector.id,
            schema_mapping_version_id=mapping.id,
            record_governance_policy_version_id=policy.id,
            source_version_id=version.id, inspection_job_id=job.id,
            idempotency_key=f"purge:{number}", request_fingerprint=str(number) * 64,
            payload_sha256=version.sha256, cursor_before="", cursor_after=str(number),
            status="SUCCEEDED",
        )
        db.add(run); db.flush()
        return run

    first_run = run_for(first, 1)
    second_run = run_for(second, 2)

    def entity(identity, state="ACTIVE"):
        row = DataRecordEntity(
            source_id=source.id, record_governance_policy_version_id=policy.id,
            organization_id=source.organization_id, workspace_id=source.workspace_id,
            product_code=source.product_code, identity_fingerprint=identity * 64,
            state=state,
        )
        db.add(row); db.flush()
        return row

    def record(version, run, entity_row, ordinal, marker, disposition, *, duplicate=None, conflict=None, reason=None, at=None):
        row = DataNormalizedRecord(
            source_id=source.id, source_version_id=version.id, ingestion_run_id=run.id,
            connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
            record_governance_policy_version_id=policy.id,
            organization_id=source.organization_id, workspace_id=source.workspace_id,
            product_code=source.product_code, source_record_ordinal=ordinal,
            source_locator=f"purge:{run.run_no}:{ordinal}", entity_id=entity_row.id,
            normalized_record_json=f'{{"record.id":"private-{marker}"}}',
            identity_fingerprint=entity_row.identity_fingerprint,
            content_fingerprint=marker * 64, disposition=disposition,
            duplicate_of_record_id=duplicate.id if duplicate else None,
            conflict_with_record_id=conflict.id if conflict else None,
            quarantine_reason=reason, created_at=at,
        )
        db.add(row); db.flush()
        return row

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    promoted_entity = entity("1", "QUARANTINED")
    accepted = record(first, first_run, promoted_entity, 1, "d", "ACCEPTED", at=base)
    oldest = record(second, second_run, promoted_entity, 1, "d", "DUPLICATE", duplicate=accepted, at=base + timedelta(seconds=1))
    newer = record(second, second_run, promoted_entity, 2, "d", "DUPLICATE", duplicate=accepted, at=base + timedelta(seconds=2))
    conflict = record(
        second, second_run, promoted_entity, 3, "e", "QUARANTINED",
        conflict=accepted, reason="IDENTITY_CONTENT_CONFLICT", at=base + timedelta(seconds=3),
    )

    quarantined_entity = entity("2", "QUARANTINED")
    accepted_without_duplicate = record(first, first_run, quarantined_entity, 2, "f", "ACCEPTED", at=base)
    remaining_quarantine = record(
        second, second_run, quarantined_entity, 4, "g", "QUARANTINED",
        conflict=accepted_without_duplicate, reason="IDENTITY_CONTENT_CONFLICT",
        at=base + timedelta(seconds=1),
    )

    empty_entity = entity("3")
    empty_original_identity = empty_entity.identity_fingerprint
    empty_accepted = record(first, first_run, empty_entity, 3, "h", "ACCEPTED", at=base)

    unrelated_entity = entity("4")
    unrelated = record(second, second_run, unrelated_entity, 5, "i", "ACCEPTED", at=base)
    db.flush()
    return {
        "target": [accepted, accepted_without_duplicate, empty_accepted],
        "oldest": oldest,
        "newer": newer,
        "conflict": conflict,
        "promoted_entity": promoted_entity,
        "remaining_quarantine": remaining_quarantine,
        "quarantined_entity": quarantined_entity,
        "empty_entity": empty_entity,
        "empty_original_identity": empty_original_identity,
        "unrelated": unrelated,
    }


def test_purge_scrubs_22d_records_promotes_duplicate_repairs_references_and_is_idempotent(governed):
    db, org, ws, _foreign_org, _foreign_ws, member, source, first, _policy, storage = governed
    second, _job, _reused = create_source_version(
        db, storage, source=source, filename="second.csv", content_type="text/csv",
        payload=b"second-private-content\n", actor_id=member.id, backend="inline",
    )
    graph = _seed_22d_purge_graph(db, source, first, second)
    unrelated_before = (
        graph["unrelated"].normalized_record_json,
        graph["unrelated"].identity_fingerprint,
        graph["unrelated"].content_fingerprint,
        graph["unrelated"].disposition,
    )
    approved = _approve(db, org, ws, member, first)
    result = execute_purge(
        db, storage, version_id=first.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=approved.revision,
        actor_id=member.id,
    )
    assert result.purge_status == "EXECUTED"
    for row in graph["target"]:
        assert row.normalized_record_json == "{}"
        assert row.disposition == "PURGED"
        assert row.quarantine_reason is None
        assert row.duplicate_of_record_id is None and row.conflict_with_record_id is None
        assert "private" not in row.normalized_record_json
    assert graph["oldest"].disposition == "ACCEPTED"
    assert graph["newer"].duplicate_of_record_id == graph["oldest"].id
    assert graph["conflict"].conflict_with_record_id == graph["oldest"].id
    assert graph["promoted_entity"].state == "QUARANTINED"
    assert graph["remaining_quarantine"].conflict_with_record_id is None
    assert graph["quarantined_entity"].state == "QUARANTINED"
    assert graph["empty_entity"].state == "EMPTY"
    assert graph["empty_entity"].identity_fingerprint != graph["empty_original_identity"]
    assert unrelated_before == (
        graph["unrelated"].normalized_record_json,
        graph["unrelated"].identity_fingerprint,
        graph["unrelated"].content_fingerprint,
        graph["unrelated"].disposition,
    )
    logical_state = [
        (row.id, row.normalized_record_json, row.identity_fingerprint, row.content_fingerprint, row.disposition)
        for row in db.scalars(select(DataNormalizedRecord).order_by(DataNormalizedRecord.id))
    ]
    repeated = execute_purge(
        db, storage, version_id=first.id, organization_id=org.id,
        workspace_id=ws.id, product_code="SIMPA", expected_revision=result.revision,
        actor_id=member.id,
    )
    assert repeated.revision == result.revision
    assert logical_state == [
        (row.id, row.normalized_record_json, row.identity_fingerprint, row.content_fingerprint, row.disposition)
        for row in db.scalars(select(DataNormalizedRecord).order_by(DataNormalizedRecord.id))
    ]
    assert not db.scalars(
        select(DataNormalizedRecord).where(
            DataNormalizedRecord.source_version_id == first.id,
            DataNormalizedRecord.normalized_record_json != "{}",
        )
    ).all()
