from __future__ import annotations

import hashlib
import inspect
import json
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.api import data_routes
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.connector_service import (
    activate_connector_contract_version,
    create_connector_contract_version,
    list_connector_contract_versions,
)
from src.platform.data.models import DataAuditEvent, DataConnectorContractVersion
from src.platform.data.schemas import ConnectorContractActivationRequest, ConnectorContractVersionCreate
from src.platform.data.service import DataPlatformError, create_source_upload
from src.platform.data.storage import LocalFilesystemStorage
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _build_case(tmp_path: Path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all(
        [
            Product(code="SIMPA", name="SIMPA", is_active=True),
            Product(code="ORDO", name="ORDO", is_active=True),
        ]
    )
    organization = Organization(slug="connector-org", name="Connector organization")
    other_organization = Organization(slug="connector-other", name="Other organization")
    user = User(email="connector@example.invalid", display_name="Connector steward", is_active=True)
    db.add_all([organization, other_organization, user])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id, status="active")
    workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug="connector-simpa",
        name="Connector SIMPA",
        status="active",
    )
    other_workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug="connector-simpa-other",
        name="Connector SIMPA other",
        status="active",
    )
    ordo_workspace = Workspace(
        organization_id=organization.id,
        product_code="ORDO",
        slug="connector-ordo",
        name="Connector ORDO",
        status="active",
    )
    foreign_workspace = Workspace(
        organization_id=other_organization.id,
        product_code="SIMPA",
        slug="connector-foreign",
        name="Connector foreign",
        status="active",
    )
    db.add_all([membership, workspace, other_workspace, ordo_workspace, foreign_workspace])
    db.flush()
    source, _version, _job, _reused = create_source_upload(
        db,
        LocalFilesystemStorage(tmp_path),
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        source_name="Synthetic connector source",
        filename="synthetic.csv",
        content_type="text/csv",
        payload=b"item,value\nsynthetic,1\n",
        actor_id=membership.id,
        backend="inline",
    )
    db.commit()
    return (
        db,
        organization,
        other_organization,
        workspace,
        other_workspace,
        ordo_workspace,
        foreign_workspace,
        membership,
        source,
    )


def _payload(organization, workspace, **changes) -> ConnectorContractVersionCreate:
    values = {
        "organization_id": organization.id,
        "workspace_id": workspace.id,
        "product_code": "SIMPA",
        "connector_kind": "REST_API",
        "transport": "HTTPS",
        "configuration": {"page_size": 100, "resource": {"name": "items", "revision": 1}},
        "credential_reference": "secretref://vault/connectors/synthetic",
        "capabilities": ["READ", "pagination", "read"],
    }
    values.update(changes)
    return ConnectorContractVersionCreate(**values)


def test_first_version_is_draft_normalized_and_deterministically_fingerprinted(tmp_path):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    response = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(
            organization,
            workspace,
            configuration={"resource": {"revision": 1, "name": "items"}, "page_size": 100},
        ),
        actor_id=membership.id,
    )
    expected_payload = {
        "source_id": str(source.id),
        "connector_kind": "rest_api",
        "transport": "https",
        "configuration": {"page_size": 100, "resource": {"name": "items", "revision": 1}},
        "credential_reference": "secretref://vault/connectors/synthetic",
        "capabilities": ["pagination", "read"],
    }
    expected_fingerprint = hashlib.sha256(
        json.dumps(
            expected_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert response.version_no == 1
    assert response.lifecycle_state == "DRAFT"
    assert response.connector_kind == "rest_api"
    assert response.transport == "https"
    assert response.capabilities == ["pagination", "read"]
    assert response.configuration == expected_payload["configuration"]
    assert response.fingerprint == expected_fingerprint
    stored = db.scalar(select(DataConnectorContractVersion).where(DataConnectorContractVersion.id == response.id))
    assert stored.configuration_json == '{"page_size":100,"resource":{"name":"items","revision":1}}'
    assert stored.capabilities_json == '["pagination","read"]'


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "PASSWD",
        "Secret",
        "client-secret",
        "api_key",
        "ApiKey",
        "access.key",
        "private key",
        "token",
        "auth_token",
        "bearer",
        "credential",
        "credentials",
        "Authorization",
        "Proxy-Authorization",
        "X-API-Key",
        "X-Auth-Token",
        "access_token",
        "refresh_token",
        "id_token",
        "oauth_token",
        "bearer_token",
        "session_token",
        "Cookie",
        "session_cookie",
        "secret_value",
        "db_password",
        "aws_secret_access_key",
        "private_key_passphrase",
    ],
)
def test_nested_secret_bearing_configuration_keys_are_rejected(tmp_path, key):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    payload = _payload(
        organization,
        workspace,
        configuration={"outer": [{"nested": {key: "synthetic-forbidden-value"}}]},
        credential_reference="",
    )
    with pytest.raises(DataPlatformError, match="connector_secret_material_forbidden"):
        create_connector_contract_version(db, source_id=source.id, payload=payload, actor_id=membership.id)
    assert db.scalar(select(DataConnectorContractVersion.id)) is None


def test_non_secret_key_names_remain_allowed(tmp_path):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    payload = _payload(
        organization,
        workspace,
        configuration={
            "monkey": "value",
            "public_key_id": "kid-1",
            "tokenization_mode": "none",
            "resource": {"name": "items"},
        },
        credential_reference="",
    )
    result = create_connector_contract_version(
        db, source_id=source.id, payload=payload, actor_id=membership.id
    )
    assert result.lifecycle_state == "DRAFT"
    assert result.configuration["public_key_id"] == "kid-1"
    assert result.configuration["tokenization_mode"] == "none"


@pytest.mark.parametrize(
    "reference",
    [
        "vault://connectors/synthetic",
        "secretref://",
        "secretref://vault/synthetic?revision=1",
        "secretref://vault/synthetic#current",
        "secretref://vault/synthetic reference",
    ],
)
def test_invalid_credential_references_are_rejected(tmp_path, reference):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    with pytest.raises(DataPlatformError, match="invalid_connector_credential_reference"):
        create_connector_contract_version(
            db,
            source_id=source.id,
            payload=_payload(organization, workspace, credential_reference=reference),
            actor_id=membership.id,
        )


def test_unchanged_version_is_rejected_and_changed_content_allocates_next_version(tmp_path):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    first = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace),
        actor_id=membership.id,
    )
    with pytest.raises(DataPlatformError, match="connector_contract_unchanged"):
        create_connector_contract_version(
            db,
            source_id=source.id,
            payload=_payload(
                organization,
                workspace,
                connector_kind="rest_api",
                transport="https",
                configuration={"resource": {"revision": 1, "name": "items"}, "page_size": 100},
                capabilities=["pagination", "read", "READ"],
            ),
            actor_id=membership.id,
        )
    second = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(
            organization,
            workspace,
            configuration={"page_size": 200, "resource": {"name": "items", "revision": 1}},
        ),
        actor_id=membership.id,
    )
    assert (first.version_no, second.version_no) == (1, 2)
    assert first.fingerprint != second.fingerprint


def test_activation_retires_previous_active_is_idempotent_and_preserves_content(tmp_path):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    first = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace),
        actor_id=membership.id,
    )
    first_active = activate_connector_contract_version(
        db,
        source_id=source.id,
        version_id=first.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        actor_id=membership.id,
    )
    audit_count = len(
        db.scalars(
            select(DataAuditEvent).where(DataAuditEvent.event_type.like("data.connector_contract_version.%"))
        ).all()
    )
    idempotent = activate_connector_contract_version(
        db,
        source_id=source.id,
        version_id=first.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        actor_id=membership.id,
    )
    assert idempotent.lifecycle_state == "ACTIVE"
    assert idempotent.activated_at == first_active.activated_at
    assert len(
        db.scalars(
            select(DataAuditEvent).where(DataAuditEvent.event_type.like("data.connector_contract_version.%"))
        ).all()
    ) == audit_count

    second = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace, transport="HTTPS_STREAM"),
        actor_id=membership.id,
    )
    second_active = activate_connector_contract_version(
        db,
        source_id=source.id,
        version_id=second.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        actor_id=membership.id,
    )
    first_row = db.get(DataConnectorContractVersion, first.id)
    assert second_active.lifecycle_state == "ACTIVE"
    assert first_row.lifecycle_state == "RETIRED"
    assert first_row.retired_at is not None
    assert first_row.fingerprint == first.fingerprint
    assert json.loads(first_row.configuration_json) == first.configuration
    with pytest.raises(DataPlatformError, match="connector_contract_state_conflict"):
        activate_connector_contract_version(
            db,
            source_id=source.id,
            version_id=first.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            actor_id=membership.id,
        )


def test_list_and_activation_reject_cross_scope_and_wrong_source_access(tmp_path):
    (
        db,
        organization,
        other_organization,
        workspace,
        other_workspace,
        ordo_workspace,
        foreign_workspace,
        membership,
        source,
    ) = _build_case(tmp_path)
    first = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace),
        actor_id=membership.id,
    )
    second = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace, capabilities=["read", "write"]),
        actor_id=membership.id,
    )
    assert [item.version_no for item in list_connector_contract_versions(
        db,
        source_id=source.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
    )] == [2, 1]

    for scope in (
        (organization.id, other_workspace.id, "SIMPA"),
        (organization.id, ordo_workspace.id, "ORDO"),
        (other_organization.id, foreign_workspace.id, "SIMPA"),
    ):
        with pytest.raises(DataPlatformError, match="source_not_accessible"):
            list_connector_contract_versions(
                db,
                source_id=source.id,
                organization_id=scope[0],
                workspace_id=scope[1],
                product_code=scope[2],
            )
        with pytest.raises(DataPlatformError, match="source_not_accessible"):
            activate_connector_contract_version(
                db,
                source_id=source.id,
                version_id=first.id,
                organization_id=scope[0],
                workspace_id=scope[1],
                product_code=scope[2],
                actor_id=membership.id,
            )

    other_source, _version, _job, _reused = create_source_upload(
        db,
        LocalFilesystemStorage(tmp_path),
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        source_name="Second synthetic source",
        filename="second.csv",
        content_type="text/csv",
        payload=b"item,value\nsynthetic,2\n",
        actor_id=membership.id,
        backend="inline",
    )
    with pytest.raises(DataPlatformError, match="connector_contract_version_not_accessible"):
        activate_connector_contract_version(
            db,
            source_id=other_source.id,
            version_id=second.id,
            organization_id=organization.id,
            workspace_id=workspace.id,
            product_code="SIMPA",
            actor_id=membership.id,
        )


def test_lifecycle_audits_are_evidential_and_exclude_configuration_and_credential_contents(tmp_path):
    db, organization, _other, workspace, *_tail, membership, source = _build_case(tmp_path)
    first = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace),
        actor_id=membership.id,
    )
    activate_connector_contract_version(
        db,
        source_id=source.id,
        version_id=first.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        actor_id=membership.id,
    )
    second = create_connector_contract_version(
        db,
        source_id=source.id,
        payload=_payload(organization, workspace, configuration={"page_size": 250}),
        actor_id=membership.id,
    )
    activate_connector_contract_version(
        db,
        source_id=source.id,
        version_id=second.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        actor_id=membership.id,
    )
    events = db.scalars(
        select(DataAuditEvent)
        .where(DataAuditEvent.event_type.like("data.connector_contract_version.%"))
        .order_by(DataAuditEvent.created_at, DataAuditEvent.id)
    ).all()
    assert {event.event_type for event in events} == {
        "data.connector_contract_version.created",
        "data.connector_contract_version.activated",
        "data.connector_contract_version.retired",
    }
    assert all("fingerprint=" in event.detail for event in events)
    combined_detail = " ".join(event.detail for event in events)
    assert "page_size" not in combined_detail
    assert "vault/connectors/synthetic" not in combined_detail
    assert "configuration_json" not in combined_detail
    assert "credential_reference" not in combined_detail


def test_mutation_schemas_forbid_extras_and_connector_service_has_no_execution_clients():
    scope = {"organization_id": uuid.uuid4(), "workspace_id": uuid.uuid4(), "product_code": "SIMPA"}
    minimal = ConnectorContractVersionCreate(**scope, connector_kind="api", transport="https")
    assert minimal.configuration == {}
    assert minimal.credential_reference == ""
    assert minimal.capabilities == []
    with pytest.raises(ValidationError):
        ConnectorContractVersionCreate(
            **scope,
            connector_kind="api",
            transport="https",
            execute_immediately=True,
        )
    with pytest.raises(ValidationError):
        ConnectorContractActivationRequest(**scope, force=True)
    service_source = Path("src/platform/data/connector_service.py").read_text()
    locking_helper = service_source.split("def _locked_scoped_source", 1)[1].split(
        "def _connector_response", 1
    )[0]
    create_service = service_source.split("def create_connector_contract_version", 1)[1].split(
        "def list_connector_contract_versions", 1
    )[0]
    activate_service = service_source.split("def activate_connector_contract_version", 1)[1]
    assert ".with_for_update()" in locking_helper
    assert create_service.index("_locked_scoped_source(") < create_service.index("func.max(")
    assert activate_service.index("_locked_scoped_source(") < activate_service.index("lifecycle_state")
    for execution_client in ("requests", "httpx", "boto3", "paramiko", "socket", "create_engine"):
        assert execution_client not in service_source


def test_connector_routes_use_existing_scope_permissions_actor_and_error_mapping():
    route_methods = {
        (route.path, method)
        for route in data_routes.router.routes
        for method in getattr(route, "methods", set())
    }
    assert (
        "/api/v1/data/sources/{source_id}/connector-contracts/versions",
        "POST",
    ) in route_methods
    assert ("/api/v1/data/sources/{source_id}/connector-contracts", "GET") in route_methods
    assert (
        "/api/v1/data/sources/{source_id}/connector-contracts/{version_id}/activate",
        "POST",
    ) in route_methods
    assert not any(
        "/connector-contracts" in path and method in {"PUT", "PATCH", "DELETE"}
        for path, method in route_methods
    )
    expectations = (
        (data_routes.post_connector_contract_version, "data.governance.manage"),
        (data_routes.get_connector_contract_versions, "data.read"),
        (data_routes.post_connector_contract_activation, "data.governance.manage"),
    )
    for function, permission in expectations:
        function_source = inspect.getsource(function)
        assert function_source.index("_require_scope(") < function_source.index(
            "create_connector_contract_version(" if function is data_routes.post_connector_contract_version
            else "list_connector_contract_versions(" if function is data_routes.get_connector_contract_versions
            else "activate_connector_contract_version("
        )
        assert f'permission_code="{permission}"' in function_source
    assert "actor_membership_id(" in inspect.getsource(data_routes.post_connector_contract_version)
    assert "actor_membership_id(" in inspect.getsource(data_routes.post_connector_contract_activation)
    for error_code, expected_status in (
        ("connector_contract_version_not_accessible", 404),
        ("connector_contract_state_conflict", 409),
        ("connector_contract_unchanged", 409),
        ("connector_secret_material_forbidden", 400),
        ("invalid_connector_credential_reference", 400),
    ):
        assert data_routes._platform_error(DataPlatformError(error_code)).status_code == expected_status
