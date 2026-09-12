from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.governance import AIUsePolicy, DataClassification, GovernanceState, PrivacyCategory
from src.platform.data.models import DataAuditEvent, DataRetentionState, DataSourceGovernanceProfile
from src.platform.data.schemas import RetentionPolicyCreate, SourceGovernanceUpdate
from src.platform.data.service import (
    DataPlatformError,
    create_retention_policy,
    create_source_upload,
    create_source_version,
    get_source_governance,
    list_retention_policies,
    update_source_governance,
)
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _seed(session: Session) -> dict[str, object]:
    session.add_all([Product(code="SIMPA", name="SIMPA", is_active=True), Product(code="ORDO", name="ORDO", is_active=True)])
    org_a = Organization(slug="org-a", name="Organization A", status="active")
    org_b = Organization(slug="org-b", name="Organization B", status="active")
    user_a = User(email="steward-a@example.invalid", display_name="Steward A", is_active=True)
    user_b = User(email="steward-b@example.invalid", display_name="Steward B", is_active=True)
    user_inactive = User(email="inactive@example.invalid", display_name="Inactive Steward", is_active=True)
    session.add_all([org_a, org_b, user_a, user_b, user_inactive])
    session.flush()
    steward_a = Membership(user_id=user_a.id, organization_id=org_a.id, status="active")
    steward_b = Membership(user_id=user_b.id, organization_id=org_b.id, status="active")
    inactive = Membership(user_id=user_inactive.id, organization_id=org_a.id, status="suspended")
    ws_a_simpa = Workspace(organization_id=org_a.id, product_code="SIMPA", slug="a-simpa", name="A SIMPA", status="active")
    ws_a_simpa_2 = Workspace(organization_id=org_a.id, product_code="SIMPA", slug="a-simpa-2", name="A SIMPA 2", status="active")
    ws_a_ordo = Workspace(organization_id=org_a.id, product_code="ORDO", slug="a-ordo", name="A ORDO", status="active")
    ws_b_simpa = Workspace(organization_id=org_b.id, product_code="SIMPA", slug="b-simpa", name="B SIMPA", status="active")
    session.add_all([steward_a, steward_b, inactive, ws_a_simpa, ws_a_simpa_2, ws_a_ordo, ws_b_simpa])
    session.commit()
    return {
        "org_a": org_a,
        "org_b": org_b,
        "steward_a": steward_a,
        "steward_b": steward_b,
        "inactive": inactive,
        "ws_a_simpa": ws_a_simpa,
        "ws_a_simpa_2": ws_a_simpa_2,
        "ws_a_ordo": ws_a_ordo,
        "ws_b_simpa": ws_b_simpa,
    }


@pytest.fixture
def governed_setup(tmp_path: Path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    seeded = _seed(session)
    source, version, _job, _reused = create_source_upload(
        session,
        LocalFilesystemStorage(tmp_path),
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
        source_name="Conservative source",
        filename="source.csv",
        content_type="text/csv",
        payload=b"private-marker-21a\nvalue\n",
        actor_id=seeded["steward_a"].id,
        backend="inline",
    )
    session.commit()
    yield session, seeded, source, version, LocalFilesystemStorage(tmp_path)
    session.close()


def test_governance_catalog_values_are_exact_and_stable():
    assert [item.value for item in DataClassification] == [
        "UNCLASSIFIED", "PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"
    ]
    assert [item.value for item in PrivacyCategory] == [
        "NONE_DECLARED",
        "AGGREGATE_NON_PERSONAL",
        "PSEUDONYMOUS_OR_LINKABLE",
        "PERSONAL_DATA",
        "SENSITIVE_PERSONAL_DATA",
        "UNKNOWN",
    ]
    assert [item.value for item in GovernanceState] == ["DRAFT", "GOVERNED", "FROZEN", "RETIRED"]
    assert [item.value for item in AIUsePolicy] == [
        "PROHIBITED",
        "LOCAL_ANALYSIS_ONLY",
        "RAG_RETRIEVAL_ALLOWED",
        "MODEL_EVALUATION_ALLOWED",
        "MODEL_TRAINING_REQUIRES_SEPARATE_APPROVAL",
    ]


def test_new_source_and_versions_get_exactly_one_fail_closed_record(governed_setup):
    session, seeded, source, first_version, storage = governed_setup
    profile = session.scalar(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == source.id))
    assert profile is not None
    assert session.scalar(
        select(func.count()).select_from(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == source.id)
    ) == 1
    assert (profile.classification, profile.privacy_category, profile.ai_use_policy) == ("UNCLASSIFIED", "UNKNOWN", "PROHIBITED")
    assert (profile.export_policy, profile.governance_state, profile.revision, profile.retention_policy_id) == (
        "PROHIBITED", "DRAFT", 1, None
    )
    first_state = session.scalar(select(DataRetentionState).where(DataRetentionState.version_id == first_version.id))
    assert first_state is not None
    assert first_state.retention_start_at is not None
    assert first_state.retention_due_at is None
    assert first_state.hold_active is False
    second_version, _job, _reused = create_source_version(
        session,
        storage,
        source=source,
        filename="source-2.csv",
        content_type="text/csv",
        payload=b"second-version\n",
        actor_id=seeded["steward_a"].id,
        backend="inline",
    )
    session.commit()
    assert session.scalar(select(func.count()).select_from(DataRetentionState).where(DataRetentionState.version_id == second_version.id)) == 1


def test_governance_lookup_is_exactly_scoped(governed_setup):
    session, seeded, source, _version, _storage = governed_setup
    response = get_source_governance(
        session,
        source_id=source.id,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
    )
    assert response.source_id == source.id
    invalid_scopes = [
        (seeded["org_b"].id, seeded["ws_b_simpa"].id, "SIMPA"),
        (seeded["org_a"].id, seeded["ws_a_simpa_2"].id, "SIMPA"),
        (seeded["org_a"].id, seeded["ws_a_ordo"].id, "ORDO"),
    ]
    for organization_id, workspace_id, product_code in invalid_scopes:
        with pytest.raises(DataPlatformError):
            get_source_governance(
                session,
                source_id=source.id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code=product_code,
            )


def test_governance_update_revision_validation_and_privacy_safe_audit(governed_setup):
    session, seeded, source, _version, _storage = governed_setup
    updated = update_source_governance(
        session,
        source_id=source.id,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
        update=SourceGovernanceUpdate(
            expected_revision=1,
            classification="INTERNAL",
            privacy_category="PERSONAL_DATA",
            processing_purpose="Reviewed institutional analysis",
            data_owner_ref="owner-registry:unit-a",
            governance_state="GOVERNED",
        ),
        actor_id=seeded["steward_a"].id,
    )
    session.commit()
    assert updated.revision == 2
    assert updated.updated_by_membership_id == seeded["steward_a"].id
    with pytest.raises(DataPlatformError, match="governance_revision_conflict"):
        update_source_governance(
            session,
            source_id=source.id,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa"].id,
            product_code="SIMPA",
            update=SourceGovernanceUpdate(expected_revision=1, classification="CONFIDENTIAL"),
            actor_id=seeded["steward_a"].id,
        )
    event = session.scalar(
        select(DataAuditEvent).where(DataAuditEvent.event_type == "data.governance.updated").order_by(DataAuditEvent.created_at.desc())
    )
    assert event is not None
    assert "private-marker-21a" not in event.detail
    assert "Reviewed institutional analysis" not in event.detail


@pytest.mark.parametrize(
    "changes",
    [
        {"classification": "UNCLASSIFIED", "privacy_category": "PERSONAL_DATA", "processing_purpose": "purpose", "data_owner_ref": "owner"},
        {"classification": "INTERNAL", "privacy_category": "UNKNOWN", "processing_purpose": "purpose", "data_owner_ref": "owner"},
        {"classification": "INTERNAL", "privacy_category": "PERSONAL_DATA", "processing_purpose": "", "data_owner_ref": "owner"},
        {"classification": "INTERNAL", "privacy_category": "PERSONAL_DATA", "processing_purpose": "purpose", "data_owner_ref": ""},
    ],
)
@pytest.mark.parametrize("state", ["GOVERNED", "FROZEN"])
def test_governed_and_frozen_require_reviewed_metadata(governed_setup, changes, state):
    session, seeded, source, _version, _storage = governed_setup
    with pytest.raises(DataPlatformError, match="governance_profile_incomplete"):
        update_source_governance(
            session,
            source_id=source.id,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa"].id,
            product_code="SIMPA",
            update=SourceGovernanceUpdate(expected_revision=1, governance_state=state, **changes),
            actor_id=seeded["steward_a"].id,
        )
    session.expire_all()
    assert get_source_governance(
        session,
        source_id=source.id,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
    ).revision == 1


@pytest.mark.parametrize("steward_key", ["steward_b", "inactive"])
def test_steward_must_be_active_and_in_same_organization(governed_setup, steward_key):
    session, seeded, source, _version, _storage = governed_setup
    with pytest.raises(DataPlatformError, match="invalid_data_steward"):
        update_source_governance(
            session,
            source_id=source.id,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa"].id,
            product_code="SIMPA",
            update=SourceGovernanceUpdate(
                expected_revision=1, data_steward_membership_id=seeded[steward_key].id
            ),
            actor_id=seeded["steward_a"].id,
        )


def test_steward_metadata_never_bypasses_source_scope(governed_setup):
    session, seeded, source, _version, _storage = governed_setup
    with pytest.raises(DataPlatformError, match="source_not_accessible"):
        update_source_governance(
            session,
            source_id=source.id,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa_2"].id,
            product_code="SIMPA",
            update=SourceGovernanceUpdate(
                expected_revision=1, data_steward_membership_id=seeded["steward_a"].id
            ),
            actor_id=seeded["steward_a"].id,
        )


def test_retention_policy_create_list_duplicate_and_assignment_are_scoped(governed_setup):
    session, seeded, source, _version, _storage = governed_setup
    payload = RetentionPolicyCreate(policy_code="REVIEWED-365", version_no=1, name="Reviewed retention", retention_days=365)
    policy = create_retention_policy(
        session,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
        payload=payload,
        actor_id=seeded["steward_a"].id,
    )
    session.commit()
    assert policy.no_auto_delete is True
    assert [item.id for item in list_retention_policies(
        session,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
    )] == [policy.id]
    assert list_retention_policies(
        session,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa_2"].id,
        product_code="SIMPA",
    ) == []
    with pytest.raises(DataPlatformError, match="retention_policy_version_exists"):
        create_retention_policy(
            session,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa"].id,
            product_code="SIMPA",
            payload=payload,
            actor_id=seeded["steward_a"].id,
        )
    assigned = update_source_governance(
        session,
        source_id=source.id,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa"].id,
        product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=1, retention_policy_id=policy.id),
        actor_id=seeded["steward_a"].id,
    )
    assert assigned.retention_policy_id == policy.id

    foreign_policy = create_retention_policy(
        session,
        organization_id=seeded["org_a"].id,
        workspace_id=seeded["ws_a_simpa_2"].id,
        product_code="SIMPA",
        payload=RetentionPolicyCreate(policy_code="FOREIGN", version_no=1, name="Foreign scope"),
        actor_id=seeded["steward_a"].id,
    )
    with pytest.raises(DataPlatformError, match="retention_policy_not_accessible"):
        update_source_governance(
            session,
            source_id=source.id,
            organization_id=seeded["org_a"].id,
            workspace_id=seeded["ws_a_simpa"].id,
            product_code="SIMPA",
            update=SourceGovernanceUpdate(expected_revision=2, retention_policy_id=foreign_policy.id),
            actor_id=seeded["steward_a"].id,
        )


def test_retention_policy_schema_rejects_negative_days():
    with pytest.raises(ValueError):
        RetentionPolicyCreate(policy_code="BAD", version_no=1, name="Bad", retention_days=-1)
