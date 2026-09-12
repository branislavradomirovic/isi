from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from src.core.database import build_engine, build_session_factory
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.models import DataConnectorContractVersion, DataSource
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_0020_schema_constraints_and_round_trip():
    engine = build_engine()
    inspector = inspect(engine)
    table = "core_data_connector_contract_versions"
    assert table in set(inspector.get_table_names())
    uniques = {tuple(item["column_names"]) for item in inspector.get_unique_constraints(table)}
    assert ("source_id", "version_no") in uniques
    foreign_keys = {
        (tuple(item["constrained_columns"]), item["referred_table"])
        for item in inspector.get_foreign_keys(table)
    }
    assert (("source_id",), "core_data_sources") in foreign_keys

    marker = uuid.uuid4().hex
    organization_id = None
    with build_session_factory(engine)() as db:
        bootstrap_reference_catalog(db)
        organization = Organization(slug=f"isi22a-{marker}", name="ISI-22A synthetic")
        db.add(organization)
        db.flush()
        organization_id = organization.id
        workspace = Workspace(
            organization_id=organization.id,
            product_code="SIMPA",
            slug=f"ws-{marker}",
            name="ISI-22A synthetic",
            status="active",
        )
        db.add(workspace)
        db.flush()
        source = DataSource(
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            name=f"ISI-22A synthetic {marker}",
            source_kind="dataset",
            status="active",
        )
        db.add(source)
        db.flush()
        contract = DataConnectorContractVersion(
            source_id=source.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            version_no=1,
            connector_kind="synthetic",
            transport="https",
            configuration_json='{"resource":"synthetic"}',
            credential_reference="",
            capabilities_json='["read"]',
            fingerprint="a" * 64,
            lifecycle_state="ACTIVE",
        )
        db.add(contract)
        db.commit()
        contract_id = contract.id
        source_id = source.id
        workspace_id = workspace.id

        persisted = db.scalar(
            select(DataConnectorContractVersion).where(DataConnectorContractVersion.id == contract_id)
        )
        assert persisted is not None
        assert (persisted.lifecycle_state, persisted.fingerprint) == ("ACTIVE", "a" * 64)
        assert persisted.configuration_json == '{"resource":"synthetic"}'

        db.add(
            DataConnectorContractVersion(
                source_id=source_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code="SIMPA",
                version_no=1,
                connector_kind="collision",
                transport="https",
                fingerprint="b" * 64,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

        db.add(
            DataConnectorContractVersion(
                source_id=uuid.uuid4(),
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code="SIMPA",
                version_no=2,
                connector_kind="unknown_source",
                transport="https",
                fingerprint="c" * 64,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

        persisted = db.get(DataConnectorContractVersion, contract_id)
        assert persisted is not None
        assert (persisted.lifecycle_state, persisted.fingerprint) == ("ACTIVE", "a" * 64)
        organization = db.get(Organization, organization_id)
        db.delete(organization)
        db.commit()
