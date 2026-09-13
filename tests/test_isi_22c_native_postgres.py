from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from src.core.database import build_engine, build_session_factory
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.models import (
    DataConnectorContractVersion,
    DataIngestionRun,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
    IngestionJob,
)
from src.platform.data.service import create_source_version
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def _version(source, *, version_no, sha):
    return DataSourceVersion(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=version_no,
        original_filename=f"native-{version_no}.csv",
        extension="csv",
        content_type="text/csv",
        size_bytes=1,
        sha256=sha,
        storage_key=f"native/{sha}.csv",
        ingest_status="queued",
        content_state="AVAILABLE",
    )


def _job(version):
    return IngestionJob(
        version_id=version.id,
        organization_id=version.organization_id,
        workspace_id=version.workspace_id,
        product_code=version.product_code,
        job_type="inspect",
        status="queued",
        backend="inline",
    )


def _run(source, connector, mapping, version, job, *, run_no, key, fingerprint, status="QUEUED"):
    return DataIngestionRun(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        run_no=run_no,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
        source_version_id=version.id,
        inspection_job_id=job.id,
        idempotency_key=key,
        request_fingerprint=fingerprint,
        payload_sha256=version.sha256,
        cursor_before="",
        cursor_after=f"cursor-{run_no}",
        status=status,
    )


def _add_version_job(db, source, *, version_no, marker):
    version = _version(source, version_no=version_no, sha=(marker * 64)[:64])
    db.add(version)
    db.flush()
    job = _job(version)
    db.add(job)
    db.flush()
    return version, job


def test_native_postgres_0022_schema_and_ingestion_run_constraints(tmp_path):
    engine = build_engine()
    inspector = inspect(engine)
    table = "core_data_ingestion_runs"
    assert table in set(inspector.get_table_names())
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260913_0022"

    uniques = {tuple(item["column_names"]) for item in inspector.get_unique_constraints(table)}
    assert {
        ("source_id", "run_no"),
        ("source_id", "idempotency_key"),
        ("source_id", "request_fingerprint"),
        ("source_version_id",),
        ("inspection_job_id",),
    } <= uniques
    foreign_keys = {
        (tuple(item["constrained_columns"]), item["referred_table"]): item.get("options", {}).get("ondelete")
        for item in inspector.get_foreign_keys(table)
    }
    assert foreign_keys[(('connector_contract_version_id',), 'core_data_connector_contract_versions')] == "RESTRICT"
    assert foreign_keys[(('schema_mapping_version_id',), 'core_data_source_schema_mapping_versions')] == "RESTRICT"
    assert foreign_keys[(('source_version_id',), 'core_data_source_versions')] == "RESTRICT"
    assert foreign_keys[(('inspection_job_id',), 'core_ingestion_jobs')] == "RESTRICT"
    live_indexes = [item for item in inspector.get_indexes(table) if item["name"] == "uq_ing_run_live_source"]
    assert len(live_indexes) == 1 and live_indexes[0]["unique"] is True
    predicate = str(live_indexes[0].get("dialect_options", {}).get("postgresql_where", ""))
    assert "QUEUED" in predicate and "RUNNING" in predicate

    marker = uuid.uuid4().hex
    organization_id = None
    with build_session_factory(engine)() as db:
        bootstrap_reference_catalog(db)
        organization = Organization(slug=f"isi22c-{marker}", name="ISI-22C synthetic")
        db.add(organization)
        db.flush()
        organization_id = organization.id
        workspace = Workspace(
            organization_id=organization.id,
            product_code="SIMPA",
            slug=f"ws-{marker}",
            name="ISI-22C synthetic",
            status="active",
        )
        db.add(workspace)
        db.flush()
        source = DataSource(
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            name=f"ISI-22C synthetic {marker}",
            source_kind="dataset",
            status="active",
        )
        db.add(source)
        db.flush()
        source_id = source.id
        connector = DataConnectorContractVersion(
            source_id=source.id,
            organization_id=source.organization_id,
            workspace_id=source.workspace_id,
            product_code=source.product_code,
            version_no=1,
            connector_kind="native",
            transport="batch",
            fingerprint="a" * 64,
            lifecycle_state="ACTIVE",
        )
        db.add(connector)
        db.flush()
        mapping = DataSourceSchemaMappingVersion(
            source_id=source.id,
            connector_contract_version_id=connector.id,
            organization_id=source.organization_id,
            workspace_id=source.workspace_id,
            product_code=source.product_code,
            version_no=1,
            contract_format_version=1,
            schema_kind="TABULAR",
            source_schema_json=(
                '[{"logical_type":"STRING","missing_values":[],"nullable":false,'
                '"ordinal":1,"required":true,"source_field":"external_id"}]'
            ),
            field_mapping_json=(
                '[{"disposition":"MAP","field_key":"record.id","source_field":"external_id"}]'
            ),
            missing_value_policy="PRESERVE_MISSING",
            unexpected_field_policy="REJECT",
            fingerprint="b" * 64,
            lifecycle_state="ACTIVE",
        )
        db.add(mapping)
        db.flush()
        version1, job1 = _add_version_job(db, source, version_no=1, marker="c")
        run1 = _run(
            source,
            connector,
            mapping,
            version1,
            job1,
            run_no=1,
            key="native:1",
            fingerprint="d" * 64,
        )
        db.add(run1)
        db.commit()

        def rejected(candidate):
            with pytest.raises(IntegrityError):
                with db.begin_nested():
                    db.add(candidate)
                    db.flush()

        version2, job2 = _add_version_job(db, source, version_no=2, marker="e")
        rejected(
            _run(
                source,
                connector,
                mapping,
                version2,
                job2,
                run_no=1,
                key="native:2",
                fingerprint="f" * 64,
                status="FAILED",
            )
        )
        rejected(
            _run(
                source,
                connector,
                mapping,
                version2,
                job2,
                run_no=2,
                key="native:1",
                fingerprint="f" * 64,
                status="FAILED",
            )
        )
        rejected(
            _run(
                source,
                connector,
                mapping,
                version2,
                job2,
                run_no=2,
                key="native:2",
                fingerprint="d" * 64,
                status="FAILED",
            )
        )
        rejected(
            _run(
                source,
                connector,
                mapping,
                version1,
                job2,
                run_no=2,
                key="native:2",
                fingerprint="f" * 64,
                status="FAILED",
            )
        )
        rejected(
            _run(
                source,
                connector,
                mapping,
                version2,
                job1,
                run_no=2,
                key="native:2",
                fingerprint="f" * 64,
                status="FAILED",
            )
        )
        rejected(
            _run(
                source,
                connector,
                mapping,
                version2,
                job2,
                run_no=2,
                key="native:2",
                fingerprint="f" * 64,
                status="RUNNING",
            )
        )

        run1 = db.get(DataIngestionRun, run1.id)
        run1.status = "SUCCEEDED"
        db.flush()
        run2 = _run(
            source,
            connector,
            mapping,
            version2,
            job2,
            run_no=2,
            key="native:2",
            fingerprint="f" * 64,
        )
        db.add(run2)
        db.flush()
        assert run2.id is not None

        run2.status = "SUCCEEDED"
        db.flush()
        version3, job3 = _add_version_job(db, source, version_no=3, marker="1")
        unknown_connector = DataConnectorContractVersion(id=uuid.uuid4())
        rejected(
            _run(
                source,
                unknown_connector,
                mapping,
                version3,
                job3,
                run_no=3,
                key="native:3",
                fingerprint="1" * 64,
            )
        )

        allocated, _allocated_job, _ = create_source_version(
            db,
            LocalFilesystemStorage(tmp_path / "native-storage"),
            source=source,
            filename="allocated.csv",
            content_type="text/csv",
            payload=b"external_id\n4\n",
            actor_id=None,
            backend="inline",
        )
        assert allocated.version_no == 4
        db.execute(
            DataIngestionRun.__table__.delete().where(DataIngestionRun.source_id == source.id)
        )
        db.commit()
        organization = db.get(Organization, organization_id)
        db.delete(organization)
        db.commit()

    with build_session_factory(engine)() as db:
        assert db.get(Organization, organization_id) is None
        assert db.scalar(select(DataIngestionRun.id).where(DataIngestionRun.source_id == source_id)) is None
