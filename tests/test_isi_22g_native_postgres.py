from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.domains.ordo.analytics_models import OrdoAnalyticsRun
from src.domains.ordo.models import OrdoMonitoringCycle  # noqa: F401 - register FK target in Base.metadata
from src.domains.simpa.analytics_models import SimpaAnalyticsRun
from src.domains.simpa.models import SimpaMonitoringCycle  # noqa: F401 - register FK target in Base.metadata
from src.platform.access.models import Product
from src.platform.data.models import (
    AnalyticalDataset,
    AnalyticalDatasetContractVersion,
    AnalyticalDatasetSnapshot,
)
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


@pytest.mark.parametrize("table,prefix", [
    ("simpa_analytics_runs", "simpa"),
    ("ordo_analytics_runs", "ordo"),
])
def test_native_postgres_0026_binding_schema(table: str, prefix: str):
    engine = build_engine()
    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns(table)}
    assert {
        "analytical_artifact_type", "analytical_snapshot_id",
        "analytical_feature_version_id", "analytical_artifact_fingerprint",
        "dataset_contract_version_id", "dataset_contract_fingerprint",
        "analytical_quality_state",
    } <= set(columns)
    assert "LEGACY_OBSERVATION" in str(columns["analytical_artifact_type"]["default"])
    foreign_tables = {fk["referred_table"] for fk in inspector.get_foreign_keys(table)}
    assert {
        "core_analytical_dataset_snapshots",
        "core_analytical_feature_versions",
        "core_analytical_dataset_contract_versions",
    } <= foreign_tables
    checks = {item["name"] for item in inspector.get_check_constraints(table)}
    assert {f"ck_{prefix}_run_artifact_type", f"ck_{prefix}_run_artifact_binding",
            f"ck_{prefix}_run_governed_identity"} <= checks
    indexes = {item["name"] for item in inspector.get_indexes(table)}
    assert {
        f"ix_{prefix}_run_analytical_snapshot",
        f"ix_{prefix}_run_analytical_feature",
        f"ix_{prefix}_run_dataset_contract",
    } <= indexes
    with engine.connect() as connection:
        default = connection.execute(text(
            "SELECT column_default FROM information_schema.columns "
            "WHERE table_name=:table AND column_name='analytical_artifact_type'"
        ), {"table": table}).scalar_one()
    assert "LEGACY_OBSERVATION" in default


@pytest.mark.parametrize(
    "product,run_model",
    [("SIMPA", SimpaAnalyticsRun), ("ORDO", OrdoAnalyticsRun)],
)
def test_native_postgres_0026_persists_governed_binding(product, run_model):
    engine = build_engine()
    connection = engine.connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        if db.get(Product, product) is None:
            db.add(Product(code=product, name=product, is_active=True))
            db.flush()
        marker = uuid.uuid4().hex
        organization = Organization(slug=f"isi22g-{marker}", name="ISI-22G native")
        db.add(organization); db.flush()
        workspace = Workspace(
            organization_id=organization.id, product_code=product,
            slug=f"isi22g-{marker}", name="ISI-22G native")
        db.add(workspace); db.flush()
        dataset = AnalyticalDataset(
            organization_id=organization.id, workspace_id=workspace.id,
            product_code=product, code=f"NATIVE_{marker}", name="Native",
            methodology_reference="test:native", methodology_version="v1")
        db.add(dataset); db.flush()
        contract = AnalyticalDatasetContractVersion(
            dataset_id=dataset.id, organization_id=organization.id,
            workspace_id=workspace.id, product_code=product, version_no=1,
            contract_format_version=1, field_contract_json='[{"field_key":"indicator_code","logical_type":"STRING","required":true,"semantic_role":"KEY"}]',
            temporal_mode="STATIC", temporal_key_fields_json="[]",
            granularity_key_fields_json='["indicator_code"]',
            missing_value_policy="PRESERVE_MISSING", fingerprint="a" * 64,
            lifecycle_state="ACTIVE")
        db.add(contract); db.flush()
        snapshot = AnalyticalDatasetSnapshot(
            dataset_id=dataset.id, organization_id=organization.id,
            workspace_id=workspace.id, product_code=product, version_no=1,
            dataset_contract_version_id=contract.id,
            dataset_contract_fingerprint=contract.fingerprint,
            lineage_mode="GOVERNED_OUTPUT_V1", temporal_mode="STATIC",
            temporal_key_fields_json="[]", granularity_key_fields_json='["indicator_code"]',
            missing_value_policy="PRESERVE_MISSING", analytical_quality_state="ACCEPTED_CLEAN",
            record_count=0, methodology_reference="test:native", methodology_version="v1",
            build_reference="test:native", classification="INTERNAL",
            privacy_category="AGGREGATE_NON_PERSONAL", ai_use_policy="RAG_RETRIEVAL_ALLOWED",
            state="VALIDATED", fingerprint="b" * 64)
        db.add(snapshot); db.flush()
        run = run_model(
            organization_id=organization.id, workspace_id=workspace.id,
            analytical_artifact_type="ANALYTICAL_SNAPSHOT",
            analytical_snapshot_id=snapshot.id, analytical_feature_version_id=None,
            analytical_artifact_fingerprint=snapshot.fingerprint,
            dataset_contract_version_id=contract.id,
            dataset_contract_fingerprint=contract.fingerprint,
            analytical_quality_state="ACCEPTED_CLEAN", status="completed", snapshot={},
            evidence_quality_score=0, validated_observation_ratio=0,
            provenance_coverage=0, indicator_coverage=0,
            **({"dimension_coverage": 0, "pillar_coverage": 0} if product == "ORDO" else {}),
        )
        db.add(run); db.flush()
        persisted = db.scalar(select(run_model).where(run_model.id == run.id))
        assert persisted.analytical_snapshot_id == snapshot.id
        assert persisted.dataset_contract_version_id == contract.id
        assert persisted.analytical_artifact_fingerprint == "b" * 64
    finally:
        transaction.rollback()
        connection.close()
