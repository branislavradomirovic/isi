from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from src.core.database import build_engine, build_session_factory
from src.platform.access.service import bootstrap_reference_catalog
from src.platform.data.models import (
    AnalyticalDataset, AnalyticalDatasetSnapshot, AnalyticalFeature, AnalyticalFeatureSnapshotInput,
    AnalyticalFeatureVersion,
)
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1", reason="native PostgreSQL acceptance only")


def test_native_postgres_0019_schema_constraints_and_persistence():
    engine = build_engine()
    tables = set(inspect(engine).get_table_names())
    assert {"core_analytical_datasets", "core_analytical_dataset_snapshots", "core_analytical_features",
            "core_analytical_feature_versions", "core_analytical_snapshot_source_versions",
            "core_analytical_feature_snapshot_inputs"} <= tables
    with build_session_factory(engine)() as db:
        bootstrap_reference_catalog(db)
        marker = uuid.uuid4().hex
        org = Organization(slug=f"isi21c-{marker}", name="ISI-21C synthetic")
        db.add(org); db.flush()
        ws = Workspace(organization_id=org.id, product_code="SIMPA", slug=f"ws-{marker}", name="Synthetic", status="active")
        db.add(ws); db.flush()
        dataset = AnalyticalDataset(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            code="DATA", name="Data", methodology_reference="method:ref", methodology_version="v1")
        feature = AnalyticalFeature(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            code="FEATURE", name="Feature", methodology_reference="method:ref", methodology_version="v1")
        db.add_all([dataset, feature]); db.flush()
        snapshot = AnalyticalDatasetSnapshot(dataset_id=dataset.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", version_no=1, methodology_reference="method:ref", methodology_version="v1",
            classification="INTERNAL", privacy_category="AGGREGATE_NON_PERSONAL", ai_use_policy="LOCAL_ANALYSIS_ONLY",
            state="FROZEN", fingerprint="1" * 64, invalidated=True, invalidation_reason="SYNTHETIC")
        version = AnalyticalFeatureVersion(feature_id=feature.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", version_no=1, methodology_reference="method:ref", methodology_version="v1",
            classification="INTERNAL", privacy_category="AGGREGATE_NON_PERSONAL", ai_use_policy="LOCAL_ANALYSIS_ONLY",
            state="FROZEN", fingerprint="2" * 64, invalidated=True, invalidation_reason="SYNTHETIC")
        db.add_all([snapshot, version]); db.flush()
        assert db.scalar(select(AnalyticalDatasetSnapshot).where(AnalyticalDatasetSnapshot.id == snapshot.id)).invalidated
        db.add(AnalyticalDataset(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            code="DATA", name="Collision", methodology_reference="method:ref", methodology_version="v1"))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


def test_native_postgres_typed_lineage_fk_rejects_unknown_snapshot():
    engine = build_engine()
    with build_session_factory(engine)() as db:
        bootstrap_reference_catalog(db)
        marker = uuid.uuid4().hex
        org = Organization(slug=f"isi21c-fk-{marker}", name="ISI-21C FK synthetic")
        db.add(org); db.flush()
        ws = Workspace(organization_id=org.id, product_code="SIMPA", slug=f"ws-{marker}", name="Synthetic", status="active")
        db.add(ws); db.flush()
        feature = AnalyticalFeature(organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            code="FEATURE", name="Feature", methodology_reference="method:ref", methodology_version="v1")
        db.add(feature); db.flush()
        version = AnalyticalFeatureVersion(feature_id=feature.id, organization_id=org.id, workspace_id=ws.id,
            product_code="SIMPA", version_no=1, methodology_reference="method:ref", methodology_version="v1",
            classification="INTERNAL", privacy_category="AGGREGATE_NON_PERSONAL", ai_use_policy="PROHIBITED",
            state="DRAFT", fingerprint="3" * 64)
        db.add(version); db.flush()
        db.add(AnalyticalFeatureSnapshotInput(feature_version_id=version.id, snapshot_id=uuid.uuid4(),
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", snapshot_version_no=1,
            snapshot_fingerprint="4" * 64))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
