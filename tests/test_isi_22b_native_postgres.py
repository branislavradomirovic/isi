from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from src.core.database import build_engine, build_session_factory
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.models import (
    DataConnectorContractVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
)
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def _mapping_values(*, source, connector, version_no, fingerprint, lifecycle_state):
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
            '[{"logical_type":"STRING","missing_values":["","NA"],'
            '"nullable":false,"ordinal":1,"required":true,"source_field":"external_id"}]'
        ),
        "field_mapping_json": (
            '[{"disposition":"MAP","field_key":"record.id","source_field":"external_id"}]'
        ),
        "missing_value_policy": "PRESERVE_MISSING",
        "unexpected_field_policy": "REJECT",
        "fingerprint": fingerprint,
        "lifecycle_state": lifecycle_state,
    }


def test_native_postgres_0021_schema_constraints_partial_active_and_round_trip():
    engine = build_engine()
    inspector = inspect(engine)
    table = "core_data_source_schema_mapping_versions"
    assert table in set(inspector.get_table_names())
    uniques = {tuple(item["column_names"]) for item in inspector.get_unique_constraints(table)}
    assert ("source_id", "version_no") in uniques
    foreign_keys = {
        (tuple(item["constrained_columns"]), item["referred_table"])
        for item in inspector.get_foreign_keys(table)
    }
    assert (("source_id",), "core_data_sources") in foreign_keys
    assert (
        ("connector_contract_version_id",),
        "core_data_connector_contract_versions",
    ) in foreign_keys
    active_indexes = [
        item
        for item in inspector.get_indexes(table)
        if item["name"] == "uq_schema_mapping_active_source"
    ]
    assert len(active_indexes) == 1
    assert active_indexes[0]["unique"] is True
    predicate = str(active_indexes[0].get("dialect_options", {}).get("postgresql_where", ""))
    assert "ACTIVE" in predicate

    marker = uuid.uuid4().hex
    organization_id = None
    mapping_id = None
    with build_session_factory(engine)() as db:
        bootstrap_reference_catalog(db)
        organization = Organization(slug=f"isi22b-{marker}", name="ISI-22B synthetic")
        db.add(organization)
        db.flush()
        organization_id = organization.id
        workspace = Workspace(
            organization_id=organization.id,
            product_code="SIMPA",
            slug=f"ws-{marker}",
            name="ISI-22B synthetic",
            status="active",
        )
        db.add(workspace)
        db.flush()
        source = DataSource(
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            name=f"ISI-22B synthetic {marker}",
            source_kind="dataset",
            status="active",
        )
        db.add(source)
        db.flush()
        connector = DataConnectorContractVersion(
            source_id=source.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            version_no=1,
            connector_kind="synthetic",
            transport="https",
            fingerprint="a" * 64,
            lifecycle_state="ACTIVE",
        )
        db.add(connector)
        db.flush()
        mapping = DataSourceSchemaMappingVersion(
            **_mapping_values(
                source=source,
                connector=connector,
                version_no=1,
                fingerprint="b" * 64,
                lifecycle_state="ACTIVE",
            )
        )
        db.add(mapping)
        db.commit()
        mapping_id = mapping.id
        source_id = source.id
        connector_id = connector.id

        persisted = db.get(DataSourceSchemaMappingVersion, mapping_id)
        assert persisted is not None
        assert persisted.source_schema_json == _mapping_values(
            source=source,
            connector=connector,
            version_no=1,
            fingerprint="b" * 64,
            lifecycle_state="ACTIVE",
        )["source_schema_json"]
        assert persisted.field_mapping_json.startswith('[{"disposition":"MAP"')

        db.add(
            DataSourceSchemaMappingVersion(
                **_mapping_values(
                    source=source,
                    connector=connector,
                    version_no=2,
                    fingerprint="c" * 64,
                    lifecycle_state="ACTIVE",
                )
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

        source = db.get(DataSource, source_id)
        connector = db.get(DataConnectorContractVersion, connector_id)
        db.add(
            DataSourceSchemaMappingVersion(
                **_mapping_values(
                    source=source,
                    connector=connector,
                    version_no=1,
                    fingerprint="d" * 64,
                    lifecycle_state="DRAFT",
                )
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

        source = db.get(DataSource, source_id)
        missing_connector = DataConnectorContractVersion(id=uuid.uuid4())
        values = _mapping_values(
            source=source,
            connector=missing_connector,
            version_no=2,
            fingerprint="e" * 64,
            lifecycle_state="DRAFT",
        )
        db.add(DataSourceSchemaMappingVersion(**values))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

        assert db.scalar(
            select(DataSourceSchemaMappingVersion.id).where(
                DataSourceSchemaMappingVersion.id == mapping_id
            )
        ) == mapping_id
        organization = db.get(Organization, organization_id)
        db.delete(organization)
        db.commit()

    with build_session_factory(engine)() as db:
        assert db.get(DataSourceSchemaMappingVersion, mapping_id) is None
        assert db.get(Organization, organization_id) is None
