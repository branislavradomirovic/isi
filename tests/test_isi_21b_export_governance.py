from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.platform.access.catalog import PermissionCode, ROLE_PERMISSION_MAP, RoleCode
from src.platform.access.models import Product
from src.platform.data.governance import AnonymizationStatus, ExportPolicy
from src.platform.data.models import DataExportManifest, DataRetentionState, DataSourceGovernanceProfile
from src.platform.data.privacy_service import export_source_version, propose_anonymization, review_anonymization
from src.platform.data.schemas import AnonymizationProposalCreate, SourceGovernanceUpdate
from src.platform.data.service import DataPlatformError, create_source_upload, update_source_governance
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.security.assurance import PrivilegedOperation, evaluate_privileged_operation
from src.platform.auth.models import AuthSession
from src.platform.auth.service import utcnow
from src.platform.workspaces.models import Workspace


def test_exact_permission_catalog_and_role_matrix():
    assert PermissionCode.DATA_GOVERNANCE_MANAGE.value == "data.governance.manage"
    assert PermissionCode.DATA_EXPORT.value == "data.export"
    for role in (RoleCode.ORGANIZATION_ADMIN, RoleCode.DOMAIN_MANAGER, RoleCode.DATA_MANAGER):
        assert {PermissionCode.DATA_GOVERNANCE_MANAGE, PermissionCode.DATA_EXPORT} <= ROLE_PERMISSION_MAP[role]
    assert PermissionCode.DATA_EXPORT in ROLE_PERMISSION_MAP[RoleCode.ANALYST]
    assert PermissionCode.DATA_GOVERNANCE_MANAGE not in ROLE_PERMISSION_MAP[RoleCode.ANALYST]
    for role in (RoleCode.REVIEWER, RoleCode.VIEWER):
        assert PermissionCode.DATA_EXPORT not in ROLE_PERMISSION_MAP[role]
        assert PermissionCode.DATA_GOVERNANCE_MANAGE not in ROLE_PERMISSION_MAP[role]


@pytest.fixture()
def export_setup(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all([Product(code="SIMPA", name="SIMPA", is_active=True), Product(code="ORDO", name="ORDO", is_active=True)])
    org = Organization(slug="export", name="Export")
    user = User(email="export@example.invalid", display_name="Export", is_active=True)
    db.add_all([org, user]); db.flush()
    member = Membership(user_id=user.id, organization_id=org.id, status="active")
    ws = Workspace(organization_id=org.id, product_code="SIMPA", slug="simpa", name="SIMPA", status="active")
    ordo = Workspace(organization_id=org.id, product_code="ORDO", slug="ordo", name="ORDO", status="active")
    db.add_all([member, ws, ordo]); db.flush()
    storage = LocalFilesystemStorage(tmp_path)
    source, version, _job, _ = create_source_upload(
        db, storage, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", source_name="Exportable",
        filename="export.csv", content_type="text/csv", payload=b"governed-export\n", actor_id=member.id,
        backend="inline")
    db.commit()
    yield db, org, ws, ordo, member, source, version, storage
    db.close()


def _govern(db, org, ws, member, source, *, classification="INTERNAL", privacy="AGGREGATE_NON_PERSONAL"):
    return update_source_governance(
        db, source_id=source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(
            expected_revision=1, classification=classification, privacy_category=privacy,
            processing_purpose="Approved synthetic purpose", data_owner_ref="registry:owner",
            export_policy=ExportPolicy.GOVERNED_EXPORT_ALLOWED, governance_state="GOVERNED",
        ), actor_id=member.id)


@pytest.mark.parametrize("field,value,code", [
    ("governance_state", "DRAFT", "governance_incomplete_export_prohibited"),
    ("classification", "UNCLASSIFIED", "governance_incomplete_export_prohibited"),
    ("privacy_category", "UNKNOWN", "governance_incomplete_export_prohibited"),
    ("export_policy", "PROHIBITED", "governance_incomplete_export_prohibited"),
])
def test_export_fails_closed_for_incomplete_governance(export_setup, field, value, code):
    db, org, ws, _ordo, member, source, version, storage = export_setup
    profile = db.execute(select(DataSourceGovernanceProfile).where(DataSourceGovernanceProfile.source_id == source.id)).scalar_one()
    profile.classification = "INTERNAL"
    profile.privacy_category = "AGGREGATE_NON_PERSONAL"
    profile.processing_purpose = "purpose"
    profile.data_owner_ref = "owner"
    profile.export_policy = "GOVERNED_EXPORT_ALLOWED"
    profile.governance_state = "GOVERNED"
    setattr(profile, field, value)
    with pytest.raises(DataPlatformError, match=code):
        export_source_version(db, storage, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                              product_code="SIMPA", purpose_reference="case:1", actor_id=member.id)
    manifest = db.scalar(select(DataExportManifest).order_by(DataExportManifest.created_at.desc()))
    assert manifest.outcome == "DENIED" and not hasattr(manifest, "storage_key")


def test_non_sensitive_export_checksum_manifest_hold_purge_and_scope_controls(export_setup):
    db, org, ws, ordo, member, source, version, storage = export_setup
    _govern(db, org, ws, member, source)
    raw, manifest = export_source_version(
        db, storage, version_id=version.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        purpose_reference="audit-case:non-sensitive", actor_id=member.id)
    assert raw == b"governed-export\n"
    assert manifest.content_checksum == version.sha256 and manifest.outcome == "COMPLETED"
    serialized = " ".join(str(value) for value in vars(manifest).values())
    assert version.storage_key not in serialized and "governed-export" not in serialized
    state = db.scalar(select(DataRetentionState).where(DataRetentionState.version_id == version.id))
    state.hold_active = True
    with pytest.raises(DataPlatformError, match="hold_active"):
        export_source_version(db, storage, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                              product_code="SIMPA", purpose_reference="audit-case:hold", actor_id=member.id)
    state.hold_active = False
    version.content_state = "PURGED"
    with pytest.raises(DataPlatformError, match="content_purged_unavailable"):
        export_source_version(db, storage, version_id=version.id, organization_id=org.id, workspace_id=ws.id,
                              product_code="SIMPA", purpose_reference="audit-case:purged", actor_id=member.id)
    with pytest.raises(DataPlatformError, match="version_not_accessible"):
        export_source_version(db, storage, version_id=version.id, organization_id=org.id, workspace_id=ordo.id,
                              product_code="ORDO", purpose_reference="audit-case:foreign", actor_id=member.id)


def test_sensitive_export_assurance_is_mfa_only():
    now = utcnow()
    model = AuthSession(
        user_id=__import__("uuid").uuid4(), token_hash="x" * 64, expires_at=now + timedelta(hours=1),
        last_seen_at=now, password_verified_at=now,
    )
    password_only = evaluate_privileged_operation(model, PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION, now=now)
    assert not password_only.allowed
    model.mfa_verified_at = now - timedelta(hours=1)
    assert not evaluate_privileged_operation(model, PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION, now=now).allowed
    model.mfa_verified_at = now
    assert evaluate_privileged_operation(model, PrivilegedOperation.SENSITIVE_EXPORT_ADMINISTRATION, now=now).allowed


def test_verified_anonymization_is_required_and_must_match_output_source(export_setup):
    db, org, ws, _ordo, member, sensitive_source, input_version, storage = export_setup
    _govern(db, org, ws, member, sensitive_source, classification="RESTRICTED", privacy="PERSONAL_DATA")
    output_source, output_version, _job, _ = create_source_upload(
        db, storage, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", source_name="Deidentified output",
        filename="output.csv", content_type="text/csv", payload=b"aggregate\n", actor_id=member.id, backend="inline")
    update_source_governance(
        db, source_id=output_source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=1, classification="RESTRICTED",
                                      privacy_category="PERSONAL_DATA"), actor_id=member.id)
    proposal = propose_anonymization(
        db, payload=AnonymizationProposalCreate(
            organization_id=org.id, workspace_id=ws.id, product_code="SIMPA", input_version_id=input_version.id,
            output_version_id=output_version.id, method_code="SYNTHETIC-METHOD", method_version="1",
            method_reference="method:v1",
            evidence_reference="evidence:checksum", classification_after="INTERNAL",
            privacy_category_after="AGGREGATE_NON_PERSONAL"), actor_id=member.id)
    with pytest.raises(DataPlatformError, match="anonymization_proof_invalid_not_verified"):
        update_source_governance(
            db, source_id=output_source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
            update=SourceGovernanceUpdate(expected_revision=2, classification="INTERNAL",
                                          privacy_category="AGGREGATE_NON_PERSONAL",
                                          verified_anonymization_record_id=proposal.id), actor_id=member.id)
    verified = review_anonymization(
        db, record_id=proposal.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        decision=AnonymizationStatus.VERIFIED, review_reference="review:approved", actor_id=member.id)
    assert verified.status == AnonymizationStatus.VERIFIED
    updated = update_source_governance(
        db, source_id=output_source.id, organization_id=org.id, workspace_id=ws.id, product_code="SIMPA",
        update=SourceGovernanceUpdate(expected_revision=2, classification="INTERNAL",
                                      privacy_category="AGGREGATE_NON_PERSONAL",
                                      verified_anonymization_record_id=proposal.id), actor_id=member.id)
    assert updated.classification.value == "INTERNAL"
