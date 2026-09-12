from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select, update

from src.core.database import build_engine, build_session_factory
from src.platform.access.models import Permission, Role, RolePermission
from src.platform.data.models import DataRetentionState, DataSource, DataSourceVersion
from src.platform.identity.models import Organization
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_privacy_schema_constraints_and_role_matrix():
    engine = build_engine()
    inspector = inspect(engine)
    assert {"core_data_anonymization_records", "core_data_export_manifests", "core_data_governance_invalidations"} <= set(inspector.get_table_names())
    version_columns = {column["name"]: column for column in inspector.get_columns("core_data_source_versions")}
    assert "content_state" in version_columns and "AVAILABLE" in str(version_columns["content_state"]["default"])
    retention_details = {column["name"]: column for column in inspector.get_columns("core_data_retention_states")}
    retention_columns = set(retention_details)
    assert {"revision", "purge_status", "hold_placed_at", "hold_released_at"} <= retention_columns
    assert "1" in str(retention_details["revision"]["default"])
    assert "NONE" in str(retention_details["purge_status"]["default"])
    checks = " ".join(str(item.get("sqltext", "")) for item in inspector.get_check_constraints("core_data_source_governance_profiles"))
    assert "GOVERNED_EXPORT_ALLOWED" in checks and "PROHIBITED" in checks
    anonymization_checks = " ".join(str(item.get("sqltext", "")) for item in inspector.get_check_constraints("core_data_anonymization_records"))
    assert "PROPOSED" in anonymization_checks and "VERIFIED" in anonymization_checks and "REJECTED" in anonymization_checks
    invalidation_uniques = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("core_data_governance_invalidations")}
    assert ("upstream_version_id", "reason") in invalidation_uniques

    with build_session_factory(engine)() as db:
        permissions = {row.code: row for row in db.scalars(select(Permission).where(Permission.code.in_(("data.governance.manage", "data.export"))))}
        assert set(permissions) == {"data.governance.manage", "data.export"}
        mapped = set(db.execute(
            select(Role.code, Permission.code).join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(Permission.code.in_(permissions))
        ))
        assert ("analyst", "data.export") in mapped
        assert ("analyst", "data.governance.manage") not in mapped
        assert not {"reviewer", "viewer"} & {role for role, _permission in mapped}


def test_native_postgres_retention_revision_is_atomic_and_synthetic_rows_roll_back():
    engine = build_engine()
    with build_session_factory(engine)() as db:
        marker = uuid.uuid4().hex
        org = Organization(slug=f"isi21b-{marker}", name="ISI-21B synthetic")
        db.add(org); db.flush()
        workspace = Workspace(organization_id=org.id, product_code="SIMPA", slug=f"ws-{marker}", name="Synthetic", status="active")
        db.add(workspace); db.flush()
        source = DataSource(organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
                            name=f"source-{marker}", source_kind="dataset", status="active")
        db.add(source); db.flush()
        version = DataSourceVersion(
            source_id=source.id, organization_id=org.id, workspace_id=workspace.id, product_code="SIMPA",
            version_no=1, original_filename="synthetic.csv", extension="csv", content_type="text/csv",
            size_bytes=1, sha256="0" * 64, storage_key=f"synthetic/{marker}", ingest_status="uploaded",
        )
        db.add(version); db.flush()
        state = DataRetentionState(version_id=version.id, source_id=source.id, organization_id=org.id,
                                   workspace_id=workspace.id, product_code="SIMPA", revision=1, purge_status="NONE")
        db.add(state); db.flush()
        first = db.execute(update(DataRetentionState).where(DataRetentionState.id == state.id, DataRetentionState.revision == 1)
                           .values(revision=2, hold_active=True))
        stale = db.execute(update(DataRetentionState).where(DataRetentionState.id == state.id, DataRetentionState.revision == 1)
                           .values(revision=2, hold_active=False))
        assert first.rowcount == 1 and stale.rowcount == 0
        db.rollback()  # synthetic acceptance rows are never persisted
