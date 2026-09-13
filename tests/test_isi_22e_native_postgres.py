from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.ingestion_operations_service import (
    activate_ingestion_operational_policy_version,
    create_ingestion_operational_policy_version,
)
from src.platform.data.ingestion_run_service import create_ingestion_run
from src.platform.data.models import (
    DataConnectorContractVersion,
    DataGovernedIngestionOutput,
    DataIngestionEvaluation,
    DataIngestionOperationalPolicyVersion,
    DataIngestionRun,
    DataRecordGovernancePolicyVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
)
from src.platform.data.schemas import IngestionOperationalPolicyVersionCreate, IngestionRunCreate
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace
from src.workers import data_jobs


pytestmark = pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
                                reason="native PostgreSQL acceptance only")


def test_native_postgres_0024_constraints_uniqueness_and_cursor_commitment(tmp_path, monkeypatch):
    engine = build_engine(); inspector = inspect(engine)
    assert {"core_data_ingestion_operational_policy_versions", "core_data_ingestion_evaluations",
            "core_data_ingestion_dead_letters", "core_data_governed_ingestion_outputs"} <= set(inspector.get_table_names())
    run_columns = {item["name"] for item in inspector.get_columns("core_data_ingestion_runs")}
    assert {"operational_policy_version_id", "execution_mode", "window_start_cursor", "window_end_cursor",
            "replay_of_run_id", "source_observed_at", "forward_cursor_committed"} <= run_columns
    run_unique = {item["name"] for item in inspector.get_unique_constraints("core_data_ingestion_runs")}
    assert {"uq_ing_run_source_fp", "uq_ing_run_source_version"} <= run_unique
    active_index = next(item for item in inspector.get_indexes("core_data_ingestion_operational_policy_versions")
                        if item["name"] == "uq_ing_op_policy_active_source")
    assert active_index["unique"] is True and "ACTIVE" in str(active_index.get("dialect_options", {}).get("postgresql_where", ""))
    connection = engine.connect(); outer = connection.begin(); db = Session(bind=connection)
    try:
        bootstrap_reference_catalog(db)
        marker = uuid.uuid4().hex
        organization = Organization(slug=f"isi22e-{marker}", name="ISI-22E synthetic")
        db.add(organization); db.flush()
        workspace = Workspace(organization_id=organization.id, product_code="SIMPA",
            slug=f"isi22e-{marker}", name="ISI-22E synthetic", status="active")
        db.add(workspace); db.flush()
        source = DataSource(organization_id=organization.id, workspace_id=workspace.id,
            product_code="SIMPA", name=f"Synthetic {marker}", source_kind="dataset", status="active")
        db.add(source); db.flush()
        connector = DataConnectorContractVersion(source_id=source.id, organization_id=organization.id,
            workspace_id=workspace.id, product_code="SIMPA", version_no=1,
            connector_kind="synthetic", transport="batch", fingerprint="a" * 64, lifecycle_state="ACTIVE")
        db.add(connector); db.flush()
        mapping = DataSourceSchemaMappingVersion(source_id=source.id, connector_contract_version_id=connector.id,
            organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA", version_no=1,
            contract_format_version=1, schema_kind="TABULAR",
            source_schema_json='[{"logical_type":"STRING","missing_values":[],"nullable":false,"ordinal":1,"required":true,"source_field":"id"}]',
            field_mapping_json='[{"disposition":"MAP","field_key":"record.id","source_field":"id"}]',
            missing_value_policy="PRESERVE_MISSING", unexpected_field_policy="REJECT",
            fingerprint="b" * 64, lifecycle_state="ACTIVE")
        db.add(mapping); db.flush()
        record_policy = DataRecordGovernancePolicyVersion(source_id=source.id,
            connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
            organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA",
            version_no=1, contract_format_version=1, identity_field_keys_json='["record.id"]',
            missing_identity_policy="QUARANTINE", exact_duplicate_policy="LINK_EXISTING",
            conflict_policy="QUARANTINE", fingerprint="c" * 64, lifecycle_state="ACTIVE")
        db.add(record_policy); db.flush()
        payload = IngestionOperationalPolicyVersionCreate(organization_id=organization.id,
            workspace_id=workspace.id, product_code="SIMPA", connector_contract_version_id=connector.id,
            schema_mapping_version_id=mapping.id, record_governance_policy_version_id=record_policy.id,
            freshness_contract={"warning_after_seconds": 60, "reject_after_seconds": 300, "missing_evidence_action": "WARN"},
            quality_contract={"required_check_codes": [], "warning_quarantine_ratio": .1,
                              "reject_quarantine_ratio": .5, "missing_required_check_action": "REJECT"},
            backfill_contract={"backfill_allowed": True, "replay_allowed": True,
                               "require_explicit_window": True, "cursor_mutation_allowed": False},
            dead_letter_contract={"max_retry_attempts": 2, "terminal_error_codes": ["synthetic.terminal"],
                                  "rejected_evaluation_to_dead_letter": False})
        created = create_ingestion_operational_policy_version(db, source_id=source.id, payload=payload, actor_id=None)
        activate_ingestion_operational_policy_version(db, source_id=source.id, policy_version_id=created.id,
            organization_id=organization.id, workspace_id=workspace.id, product_code="SIMPA", actor_id=None)
        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(DataIngestionOperationalPolicyVersion(source_id=source.id,
                    connector_contract_version_id=connector.id, schema_mapping_version_id=mapping.id,
                    record_governance_policy_version_id=record_policy.id, organization_id=organization.id,
                    workspace_id=workspace.id, product_code="SIMPA", version_no=2, contract_format_version=1,
                    freshness_contract_json="{}", quality_contract_json="{}", backfill_contract_json="{}",
                    dead_letter_contract_json="{}", fingerprint="d" * 64, lifecycle_state="ACTIVE")); db.flush()
        storage = LocalFilesystemStorage(tmp_path / "native-storage")
        def make_run(key, cursor, raw):
            result = create_ingestion_run(db, storage, source_id=source.id,
                request=IngestionRunCreate(organization_id=organization.id, workspace_id=workspace.id,
                    product_code="SIMPA", connector_contract_version_id=connector.id,
                    schema_mapping_version_id=mapping.id, idempotency_key=key, filename=f"{key}.csv",
                    content_type="text/csv", content_base64=base64.b64encode(raw).decode(),
                    cursor_after=cursor, source_observed_at=datetime.now(timezone.utc)),
                payload_bytes=raw, actor_id=None, backend="inline")
            return db.get(DataIngestionRun, result.run.id)
        monkeypatch.setattr(data_jobs, "build_storage", lambda: storage)
        monkeypatch.setattr(data_jobs, "get_settings", lambda: SimpleNamespace(data_max_xlsx_uncompressed_bytes=1024 * 1024))
        first = make_run("native:one", "native:cursor", b"id\n1\n")
        data_jobs.process_ingestion_job(db, job_id=first.inspection_job_id)
        assert first.forward_cursor_committed is True
        evaluation = db.scalar(select(DataIngestionEvaluation).where(DataIngestionEvaluation.ingestion_run_id == first.id))
        output = db.scalar(select(DataGovernedIngestionOutput).where(DataGovernedIngestionOutput.ingestion_run_id == first.id))
        assert evaluation is not None and output is not None
        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(DataIngestionEvaluation(source_id=source.id, ingestion_run_id=first.id,
                    operational_policy_version_id=created.id, organization_id=organization.id,
                    workspace_id=workspace.id, product_code="SIMPA", freshness_status="FRESH",
                    quality_status="PASS", decision="ACCEPTED", freshness_details_json="{}",
                    quality_details_json="{}", record_metrics_json="{}", evidence_fingerprint="e" * 64)); db.flush()
        second = make_run("native:two", "native:next", b"id\n2\n")
        assert second.cursor_before == "native:cursor"
    finally:
        db.close(); outer.rollback(); connection.close()


def test_0024_migration_declares_historical_success_backfill():
    text_value = Path("migrations/versions/20260913_0024_ingestion_operations_quality_backfill.py").read_text()
    assert "CASE WHEN status = 'SUCCEEDED' THEN true ELSE false END" in text_value
