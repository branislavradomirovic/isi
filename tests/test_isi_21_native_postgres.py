from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect, select

from src.core.database import build_engine, build_session_factory
from src.platform.data.models import DataRetentionState, DataSourceGovernanceProfile
from src.platform.data.service import create_source_upload
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership
from src.platform.workspaces.models import Workspace


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def test_native_postgres_governance_tables_and_constraints(tmp_path):
    engine = build_engine()
    inspector = inspect(engine)
    required = {
        "core_data_retention_policies",
        "core_data_source_governance_profiles",
        "core_data_retention_states",
    }
    assert required <= set(inspector.get_table_names())
    profile_columns = {column["name"] for column in inspector.get_columns("core_data_source_governance_profiles")}
    assert {"source_id", "classification", "privacy_category", "revision", "retention_policy_id"} <= profile_columns
    profile_unique = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("core_data_source_governance_profiles")}
    retention_unique = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("core_data_retention_states")}
    policy_unique = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("core_data_retention_policies")}
    assert ("source_id",) in profile_unique
    assert ("version_id",) in retention_unique
    assert ("workspace_id", "policy_code", "version_no") in policy_unique
    profile_checks = " ".join(item["sqltext"] for item in inspector.get_check_constraints("core_data_source_governance_profiles"))
    assert "UNCLASSIFIED" in profile_checks
    assert "UNKNOWN" in profile_checks
    assert "PROHIBITED" in profile_checks

    factory = build_session_factory(engine)
    with factory() as session:
        workspace = session.scalar(select(Workspace).where(Workspace.status == "active").limit(1))
        if workspace is None:
            pytest.skip("native database has no active workspace fixture")
        actor_id = session.scalar(
            select(Membership.id).where(
                Membership.organization_id == workspace.organization_id,
                Membership.status == "active",
            ).limit(1)
        )
        source, version, _job, _reused = create_source_upload(
            session,
            LocalFilesystemStorage(tmp_path),
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            product_code=workspace.product_code,
            source_name=f"isi21-native-{uuid.uuid4().hex}",
            filename="native.csv",
            content_type="text/csv",
            payload=b"synthetic,value\nrow,1\n",
            actor_id=actor_id,
            backend="inline",
        )
        session.commit()
        profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == source.id))
        state = session.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
        assert profile is not None
        assert (profile.classification, profile.privacy_category, profile.ai_use_policy, profile.export_policy) == (
            "UNCLASSIFIED", "UNKNOWN", "PROHIBITED", "PROHIBITED"
        )
        assert state is not None and state.retention_due_at is None and state.hold_active is False
        session.delete(source)
        session.commit()
