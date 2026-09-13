from __future__ import annotations

import base64
import os
import uuid

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.ingestion import StructuredRecord
from src.platform.data.ingestion_run_service import create_ingestion_run
from src.platform.data import record_governance_service
from src.platform.data.models import (
    DataConnectorContractVersion,
    DataIngestionRun,
    DataNormalizedRecord,
    DataRecordEntity,
    DataRecordGovernancePolicyVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.record_governance_service import (
    activate_record_governance_policy_version,
    create_record_governance_policy_version,
    materialize_ingestion_run_records,
    purge_source_version_records,
)
from src.platform.data.schemas import IngestionRunCreate, RecordGovernancePolicyVersionCreate
from src.platform.data.service import DataPlatformError
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_0023_schema_constraints_lifecycle_savepoint_and_purge(tmp_path, monkeypatch):
    engine = build_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected_tables = {
        "core_data_record_governance_policy_versions",
        "core_data_record_entities",
        "core_data_normalized_records",
        "core_data_record_resolutions",
    }
    assert expected_tables <= tables
    with engine.connect() as check_connection:
        assert check_connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260913_0023"
    run_columns = {item["name"] for item in inspector.get_columns("core_data_ingestion_runs")}
    assert "record_governance_policy_version_id" in run_columns
    run_policy_fks = [
        item for item in inspector.get_foreign_keys("core_data_ingestion_runs")
        if item["constrained_columns"] == ["record_governance_policy_version_id"]
    ]
    assert len(run_policy_fks) == 1
    assert run_policy_fks[0]["referred_table"] == "core_data_record_governance_policy_versions"
    assert run_policy_fks[0].get("options", {}).get("ondelete") == "RESTRICT"
    policy_active = next(
        item for item in inspector.get_indexes("core_data_record_governance_policy_versions")
        if item["name"] == "uq_rec_policy_active_source"
    )
    accepted_active = next(
        item for item in inspector.get_indexes("core_data_normalized_records")
        if item["name"] == "uq_norm_rec_accepted_entity"
    )
    assert policy_active["unique"] is True and "ACTIVE" in str(
        policy_active.get("dialect_options", {}).get("postgresql_where", "")
    )
    assert accepted_active["unique"] is True and "ACCEPTED" in str(
        accepted_active.get("dialect_options", {}).get("postgresql_where", "")
    )

    connection = engine.connect()
    outer = connection.begin()
    db = Session(bind=connection)
    try:
        bootstrap_reference_catalog(db)
        marker = uuid.uuid4().hex
        organization = Organization(slug=f"isi22d-{marker}", name="ISI-22D synthetic")
        db.add(organization); db.flush()
        workspace = Workspace(
            organization_id=organization.id, product_code="SIMPA", slug=f"ws-{marker}",
            name="ISI-22D synthetic", status="active",
        )
        db.add(workspace); db.flush()
        source = DataSource(
            organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            name=f"ISI-22D synthetic {marker}", source_kind="dataset", status="active",
        )
        db.add(source); db.flush()
        connector = DataConnectorContractVersion(
            source_id=source.id, organization_id=organization.id, workspace_id=workspace.id,
            product_code="SIMPA", version_no=1, connector_kind="native",
            transport="batch", fingerprint="a" * 64, lifecycle_state="ACTIVE",
        )
        db.add(connector); db.flush()
        mapping = DataSourceSchemaMappingVersion(
            source_id=source.id, connector_contract_version_id=connector.id,
            organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            version_no=1, contract_format_version=1, schema_kind="TABULAR",
            source_schema_json=(
                '[{"logical_type":"STRING","missing_values":[],"nullable":false,'
                '"ordinal":1,"required":true,"source_field":"id"},'
                '{"logical_type":"STRING","missing_values":[],"nullable":true,'
                '"ordinal":2,"required":false,"source_field":"name"}]'
            ),
            field_mapping_json=(
                '[{"disposition":"MAP","field_key":"record.id","source_field":"id"},'
                '{"disposition":"MAP","field_key":"record.name","source_field":"name"}]'
            ),
            missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
            fingerprint="b" * 64, lifecycle_state="ACTIVE",
        )
        db.add(mapping); db.flush()
        created_policy = create_record_governance_policy_version(
            db, source_id=source.id,
            payload=RecordGovernancePolicyVersionCreate(
                organization_id=organization.id, workspace_id=workspace.id,
                product_code="SIMPA", connector_contract_version_id=connector.id,
                schema_mapping_version_id=mapping.id, identity_field_keys=["record.id"],
            ), actor_id=None,
        )
        activated = activate_record_governance_policy_version(
            db, source_id=source.id, policy_id=created_policy.id,
            organization_id=organization.id, workspace_id=workspace.id,
            product_code="SIMPA", actor_id=None,
        )
        assert activated.lifecycle_state == "ACTIVE"
        policy = db.get(DataRecordGovernancePolicyVersion, activated.id)

        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(DataRecordGovernancePolicyVersion(
                    source_id=source.id, connector_contract_version_id=connector.id,
                    schema_mapping_version_id=mapping.id, organization_id=organization.id,
                    workspace_id=workspace.id, product_code="SIMPA", version_no=2,
                    contract_format_version=1, identity_field_keys_json='["record.id"]',
                    missing_identity_policy="QUARANTINE", exact_duplicate_policy="LINK_EXISTING",
                    conflict_policy="QUARANTINE", fingerprint="c" * 64, lifecycle_state="ACTIVE",
                ))
                db.flush()

        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(DataRecordEntity(
                    source_id=source.id, record_governance_policy_version_id=uuid.uuid4(),
                    organization_id=organization.id, workspace_id=workspace.id,
                    product_code="SIMPA", identity_fingerprint="d" * 64, state="ACTIVE",
                ))
                db.flush()

        storage = LocalFilesystemStorage(tmp_path / "native-storage")

        def make_run(raw, key):
            response = create_ingestion_run(
                db, storage, source_id=source.id,
                request=IngestionRunCreate(
                    organization_id=organization.id, workspace_id=workspace.id,
                    product_code="SIMPA", connector_contract_version_id=connector.id,
                    schema_mapping_version_id=mapping.id, idempotency_key=f"native:{key}",
                    filename=f"{key}.csv", content_type="text/csv",
                    content_base64=base64.b64encode(raw).decode(), cursor_after=key,
                ), payload_bytes=raw, actor_id=None, backend="inline",
            )
            return db.get(DataIngestionRun, response.run.id)

        first_run = make_run(b"id,name\n1,Alice\n", "one")
        first_result = materialize_ingestion_run_records(
            db, run=first_run,
            records=(StructuredRecord(1, "native:1", {"id": "1", "name": "Alice"}),),
        )
        assert (first_result.accepted, first_result.duplicates, first_result.quarantined) == (1, 0, 0)
        first_run.status = "SUCCEEDED"
        db.get(IngestionJob, first_run.inspection_job_id).status = "succeeded"
        db.get(DataSourceVersion, first_run.source_version_id).ingest_status = "succeeded"
        db.flush()

        second_run = make_run(b"id,name\n1,Alice\n\n", "two")
        second_result = materialize_ingestion_run_records(
            db, run=second_run,
            records=(StructuredRecord(1, "native:1", {"id": "1", "name": "Alice"}),),
        )
        assert second_result.duplicates == 1
        first_row = db.scalar(select(DataNormalizedRecord).where(
            DataNormalizedRecord.ingestion_run_id == first_run.id
        ))
        second_row = db.scalar(select(DataNormalizedRecord).where(
            DataNormalizedRecord.ingestion_run_id == second_run.id
        ))
        assert second_row.duplicate_of_record_id == first_row.id

        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(DataNormalizedRecord(
                    source_id=source.id, source_version_id=second_run.source_version_id,
                    ingestion_run_id=second_run.id, connector_contract_version_id=connector.id,
                    schema_mapping_version_id=mapping.id,
                    record_governance_policy_version_id=policy.id,
                    organization_id=organization.id, workspace_id=workspace.id,
                    product_code="SIMPA", source_record_ordinal=2, source_locator="invalid:accepted",
                    entity_id=first_row.entity_id, normalized_record_json='{"record.id":"1"}',
                    identity_fingerprint=first_row.identity_fingerprint,
                    content_fingerprint=first_row.content_fingerprint, disposition="ACCEPTED",
                ))
                db.flush()

        scrubbed = purge_source_version_records(
            db, source_version_id=first_run.source_version_id,
            organization_id=organization.id, workspace_id=workspace.id,
            product_code="SIMPA", actor_id=None,
        )
        assert scrubbed == 1
        assert first_row.disposition == "PURGED" and first_row.normalized_record_json == "{}"
        assert second_row.disposition == "ACCEPTED" and second_row.duplicate_of_record_id is None

        second_run.status = "SUCCEEDED"
        db.get(IngestionJob, second_run.inspection_job_id).status = "succeeded"
        db.get(DataSourceVersion, second_run.source_version_id).ingest_status = "succeeded"
        db.flush()
        third_run = make_run(b"id,name\n2,Bob\n3,Carol\n", "three")
        original_normalize = record_governance_service._normalize_record

        def fail_second(structured_record, **kwargs):
            if structured_record.ordinal == 2:
                raise DataPlatformError("synthetic_savepoint_failure")
            return original_normalize(structured_record, **kwargs)

        monkeypatch.setattr(record_governance_service, "_normalize_record", fail_second)
        with pytest.raises(DataPlatformError, match="synthetic_savepoint_failure"):
            materialize_ingestion_run_records(
                db, run=third_run,
                records=(
                    StructuredRecord(1, "native:1", {"id": "2", "name": "Bob"}),
                    StructuredRecord(2, "native:2", {"id": "3", "name": "Carol"}),
                ),
            )
        assert db.scalar(select(func.count()).select_from(DataNormalizedRecord).where(
            DataNormalizedRecord.ingestion_run_id == third_run.id
        )) == 0
    finally:
        db.close()
        if outer.is_active:
            outer.rollback()
        connection.close()
