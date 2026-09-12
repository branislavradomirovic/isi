from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api import data_routes
from src.core.database import Base
from src.platform.access.models import Product
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
)
from src.platform.data.schema_mapping_service import (
    activate_source_schema_mapping_version,
    create_source_schema_mapping_version,
    list_source_schema_mapping_versions,
)
from src.platform.data.schemas import (
    SourceSchemaMappingActivationRequest,
    SourceSchemaMappingVersionCreate,
)
from src.platform.data.service import DataPlatformError
from src.platform.identity.models import Membership, Organization, User
from src.platform.workspaces.models import Workspace


def _build_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add_all(
        [
            Product(code="SIMPA", name="SIMPA", is_active=True),
            Product(code="ORDO", name="ORDO", is_active=True),
        ]
    )
    organization = Organization(slug="mapping-org", name="Mapping organization")
    other_organization = Organization(slug="mapping-other", name="Other organization")
    user = User(email="mapping@example.invalid", display_name="Mapping steward", is_active=True)
    db.add_all([organization, other_organization, user])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id, status="active")
    workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug="mapping-simpa",
        name="Mapping SIMPA",
        status="active",
    )
    other_workspace = Workspace(
        organization_id=organization.id,
        product_code="SIMPA",
        slug="mapping-simpa-other",
        name="Mapping SIMPA other",
        status="active",
    )
    ordo_workspace = Workspace(
        organization_id=organization.id,
        product_code="ORDO",
        slug="mapping-ordo",
        name="Mapping ORDO",
        status="active",
    )
    foreign_workspace = Workspace(
        organization_id=other_organization.id,
        product_code="SIMPA",
        slug="mapping-foreign",
        name="Mapping foreign",
        status="active",
    )
    db.add_all([membership, workspace, other_workspace, ordo_workspace, foreign_workspace])
    db.flush()
    source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Synthetic mapping source",
        source_kind="dataset",
        status="active",
        created_by_membership_id=membership.id,
    )
    document_source = DataSource(
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        name="Synthetic document source",
        source_kind="document",
        status="active",
        created_by_membership_id=membership.id,
    )
    other_source = DataSource(
        organization_id=organization.id,
        workspace_id=other_workspace.id,
        product_code="SIMPA",
        name="Other mapping source",
        source_kind="dataset",
        status="active",
        created_by_membership_id=membership.id,
    )
    db.add_all([source, document_source, other_source])
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
        lifecycle_state="DRAFT",
        created_by_membership_id=membership.id,
    )
    document_connector = DataConnectorContractVersion(
        source_id=document_source.id,
        organization_id=organization.id,
        workspace_id=workspace.id,
        product_code="SIMPA",
        version_no=1,
        connector_kind="synthetic",
        transport="https",
        fingerprint="b" * 64,
        lifecycle_state="ACTIVE",
        created_by_membership_id=membership.id,
    )
    other_connector = DataConnectorContractVersion(
        source_id=other_source.id,
        organization_id=organization.id,
        workspace_id=other_workspace.id,
        product_code="SIMPA",
        version_no=1,
        connector_kind="synthetic",
        transport="https",
        fingerprint="c" * 64,
        lifecycle_state="ACTIVE",
        created_by_membership_id=membership.id,
    )
    db.add_all([connector, document_connector, other_connector])
    db.commit()
    return {
        "db": db,
        "organization": organization,
        "other_organization": other_organization,
        "workspace": workspace,
        "other_workspace": other_workspace,
        "ordo_workspace": ordo_workspace,
        "foreign_workspace": foreign_workspace,
        "membership": membership,
        "source": source,
        "document_source": document_source,
        "other_source": other_source,
        "connector": connector,
        "document_connector": document_connector,
        "other_connector": other_connector,
    }


def _payload(case, **changes) -> SourceSchemaMappingVersionCreate:
    values = {
        "organization_id": case["organization"].id,
        "workspace_id": case["workspace"].id,
        "product_code": "SIMPA",
        "connector_contract_version_id": case["connector"].id,
        "schema_kind": "TABULAR",
        "source_schema": [
            {
                "ordinal": 2,
                "source_field": "amount",
                "logical_type": "NUMBER",
                "required": False,
                "nullable": True,
                "missing_values": ["NA", "", "0", "NA"],
            },
            {
                "ordinal": 1,
                "source_field": " External ID ",
                "logical_type": "STRING",
                "required": True,
                "nullable": False,
                "missing_values": [],
            },
        ],
        "field_mapping": [
            {"source_field": "amount", "disposition": "IGNORE", "field_key": None},
            {"source_field": "External ID", "disposition": "MAP", "field_key": "Record.ID"},
        ],
    }
    values.update(changes)
    return SourceSchemaMappingVersionCreate(**values)


def _create(case, payload=None):
    return create_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        payload=payload or _payload(case),
        actor_id=case["membership"].id,
    )


def test_first_version_normalizes_and_fingerprints_then_rejects_latest_noop():
    case = _build_case()
    first = _create(case)
    assert (first.version_no, first.lifecycle_state, first.contract_format_version) == (1, "DRAFT", 1)
    assert [field.ordinal for field in first.source_schema] == [1, 2]
    assert first.source_schema[0].source_field == "External ID"
    assert first.source_schema[1].missing_values == ["", "0", "NA"]
    assert [entry.source_field for entry in first.field_mapping] == ["External ID", "amount"]
    assert first.field_mapping[0].field_key == "record.id"
    assert first.missing_value_policy == "PRESERVE_MISSING"

    semantic_content = {
        "source_id": str(case["source"].id),
        "connector_contract_version_id": str(case["connector"].id),
        "contract_format_version": 1,
        "schema_kind": "TABULAR",
        "source_schema": [field.model_dump() for field in first.source_schema],
        "field_mapping": [entry.model_dump() for entry in first.field_mapping],
        "missing_value_policy": "PRESERVE_MISSING",
        "unexpected_field_policy": "REJECT",
    }
    expected = hashlib.sha256(
        json.dumps(
            semantic_content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert first.fingerprint == expected
    stored = case["db"].get(DataSourceSchemaMappingVersion, first.id)
    assert json.loads(stored.source_schema_json) == [
        field.model_dump() for field in first.source_schema
    ]

    equivalent = _payload(
        case,
        source_schema=[
            {
                "required": True,
                "missing_values": [],
                "logical_type": "STRING",
                "source_field": "External ID",
                "nullable": False,
                "ordinal": 1,
            },
            {
                "missing_values": ["0", "NA", "", "0"],
                "nullable": True,
                "required": False,
                "source_field": "amount",
                "ordinal": 2,
                "logical_type": "NUMBER",
            },
        ],
        field_mapping=[
            {"field_key": None, "disposition": "IGNORE", "source_field": "amount"},
            {"field_key": "record.ID", "source_field": "External ID", "disposition": "MAP"},
        ],
    )
    with pytest.raises(DataPlatformError, match="schema_mapping_unchanged"):
        _create(case, equivalent)

    second = _create(case, _payload(case, unexpected_field_policy="IGNORE"))
    assert (second.version_no, second.unexpected_field_policy) == (2, "IGNORE")
    listed = list_source_schema_mapping_versions(
        case["db"],
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
    )
    assert [item.version_no for item in listed] == [2, 1]


def test_create_requires_dataset_and_exact_nonretired_connector_binding():
    case = _build_case()
    draft_bound = _create(case)
    assert draft_bound.connector_contract_version_id == case["connector"].id

    inaccessible = _payload(
        case,
        connector_contract_version_id=case["other_connector"].id,
        unexpected_field_policy="IGNORE",
    )
    with pytest.raises(DataPlatformError, match="connector_contract_version_not_accessible"):
        _create(case, inaccessible)

    wrong_scope_connector = DataConnectorContractVersion(
        source_id=case["source"].id,
        organization_id=case["organization"].id,
        workspace_id=case["other_workspace"].id,
        product_code="SIMPA",
        version_no=2,
        connector_kind="synthetic",
        transport="https",
        fingerprint="f" * 64,
        lifecycle_state="ACTIVE",
    )
    case["db"].add(wrong_scope_connector)
    case["db"].flush()
    with pytest.raises(DataPlatformError, match="connector_contract_version_not_accessible"):
        _create(
            case,
            _payload(
                case,
                connector_contract_version_id=wrong_scope_connector.id,
                unexpected_field_policy="IGNORE",
            ),
        )

    document_payload = _payload(
        case,
        connector_contract_version_id=case["document_connector"].id,
    )
    with pytest.raises(DataPlatformError, match="schema_mapping_source_kind_unsupported"):
        create_source_schema_mapping_version(
            case["db"],
            source_id=case["document_source"].id,
            payload=document_payload,
            actor_id=case["membership"].id,
        )

    case["connector"].lifecycle_state = "ACTIVE"
    active_bound = _create(case, _payload(case, schema_kind="RECORD"))
    assert active_bound.connector_contract_version_id == case["connector"].id
    case["connector"].lifecycle_state = "RETIRED"
    with pytest.raises(DataPlatformError, match="schema_mapping_connector_retired"):
        _create(case, _payload(case, unexpected_field_policy="IGNORE", schema_kind="RECORD"))


def test_activation_requires_active_connector_retires_prior_and_is_idempotent():
    case = _build_case()
    first = _create(case)
    with pytest.raises(DataPlatformError, match="schema_mapping_connector_not_active"):
        activate_source_schema_mapping_version(
            case["db"],
            source_id=case["source"].id,
            version_id=first.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )
    case["connector"].lifecycle_state = "ACTIVE"
    first_active = activate_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        version_id=first.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    immutable = (
        case["db"].get(DataSourceSchemaMappingVersion, first.id).source_schema_json,
        case["db"].get(DataSourceSchemaMappingVersion, first.id).field_mapping_json,
        first.fingerprint,
    )
    audit_count = len(case["db"].scalars(select(DataAuditEvent)).all())
    idempotent = activate_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        version_id=first.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    assert idempotent.activated_at == first_active.activated_at
    assert len(case["db"].scalars(select(DataAuditEvent)).all()) == audit_count

    second = _create(case, _payload(case, unexpected_field_policy="IGNORE"))
    second_active = activate_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        version_id=second.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    first_row = case["db"].get(DataSourceSchemaMappingVersion, first.id)
    assert (first_row.lifecycle_state, second_active.lifecycle_state) == ("RETIRED", "ACTIVE")
    assert (first_row.source_schema_json, first_row.field_mapping_json, first_row.fingerprint) == immutable
    with pytest.raises(DataPlatformError, match="schema_mapping_state_conflict"):
        activate_source_schema_mapping_version(
            case["db"],
            source_id=case["source"].id,
            version_id=first.id,
            organization_id=case["organization"].id,
            workspace_id=case["workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        (
            {"source_schema": [
                {"ordinal": 1, "source_field": "a", "logical_type": "STRING", "required": True, "nullable": False},
                {"ordinal": 1, "source_field": "b", "logical_type": "STRING", "required": True, "nullable": False},
            ], "field_mapping": [
                {"source_field": "a", "disposition": "MAP", "field_key": "a"},
                {"source_field": "b", "disposition": "MAP", "field_key": "b"},
            ]},
            "schema_mapping_ordinals_invalid",
        ),
        (
            {"source_schema": [
                {"ordinal": 1, "source_field": "a", "logical_type": "STRING", "required": True, "nullable": False},
                {"ordinal": 3, "source_field": "b", "logical_type": "STRING", "required": True, "nullable": False},
            ], "field_mapping": [
                {"source_field": "a", "disposition": "MAP", "field_key": "a"},
                {"source_field": "b", "disposition": "MAP", "field_key": "b"},
            ]},
            "schema_mapping_ordinals_invalid",
        ),
        (
            {"source_schema": [
                {"ordinal": 1, "source_field": "same", "logical_type": "STRING", "required": True, "nullable": False},
                {"ordinal": 2, "source_field": " same ", "logical_type": "STRING", "required": True, "nullable": False},
            ], "field_mapping": [
                {"source_field": "same", "disposition": "MAP", "field_key": "a"},
                {"source_field": " same ", "disposition": "MAP", "field_key": "b"},
            ]},
            "schema_mapping_source_field_duplicate",
        ),
        ({"field_mapping": [{"source_field": "External ID", "disposition": "MAP", "field_key": "id"}]}, "schema_mapping_field_set_mismatch"),
        ({"field_mapping": [
            {"source_field": "External ID", "disposition": "MAP", "field_key": "id"},
            {"source_field": "undeclared", "disposition": "IGNORE"},
        ]}, "schema_mapping_field_set_mismatch"),
        ({"field_mapping": [
            {"source_field": "External ID", "disposition": "MAP"},
            {"source_field": "amount", "disposition": "IGNORE"},
        ]}, "schema_mapping_field_key_required"),
        ({"field_mapping": [
            {"source_field": "External ID", "disposition": "MAP", "field_key": "invalid key"},
            {"source_field": "amount", "disposition": "IGNORE"},
        ]}, "schema_mapping_field_key_invalid"),
        ({"field_mapping": [
            {"source_field": "External ID", "disposition": "IGNORE", "field_key": "not-empty"},
            {"source_field": "amount", "disposition": "IGNORE"},
        ]}, "schema_mapping_field_key_forbidden"),
        ({"field_mapping": [
            {"source_field": "External ID", "disposition": "MAP", "field_key": "Shared.Key"},
            {"source_field": "amount", "disposition": "MAP", "field_key": "shared.key"},
        ]}, "schema_mapping_field_key_duplicate"),
    ],
)
def test_semantic_schema_and_mapping_validation(changes, error):
    case = _build_case()
    with pytest.raises(DataPlatformError, match=error):
        _create(case, _payload(case, **changes))


def test_mutation_schemas_forbid_executable_default_transform_and_unknown_fields():
    case = _build_case()
    scope = {
        "organization_id": case["organization"].id,
        "workspace_id": case["workspace"].id,
        "product_code": "SIMPA",
    }
    with pytest.raises(ValidationError):
        SourceSchemaMappingVersionCreate(
            **_payload(case).model_dump(),
            execute_immediately=True,
        )
    for forbidden_field in ("sample_value", "default", "sql", "python", "jinja", "shell"):
        raw = _payload(case).model_dump()
        raw["source_schema"][0][forbidden_field] = "forbidden"
        with pytest.raises(ValidationError):
            SourceSchemaMappingVersionCreate(**raw)
    raw = _payload(case).model_dump()
    raw["field_mapping"][0]["transform"] = "forbidden"
    with pytest.raises(ValidationError):
        SourceSchemaMappingVersionCreate(**raw)
    with pytest.raises(ValidationError):
        SourceSchemaMappingActivationRequest(**scope, force=True)
    with pytest.raises(ValidationError):
        SourceSchemaMappingVersionCreate(
            **{**_payload(case).model_dump(), "missing_value_policy": "ZERO_FILL"}
        )
    assert "0" in _create(case).source_schema[1].missing_values


def test_scope_isolation_and_wrong_source_version_access():
    case = _build_case()
    first = _create(case)
    for scope in (
        (case["organization"].id, case["other_workspace"].id, "SIMPA"),
        (case["organization"].id, case["ordo_workspace"].id, "ORDO"),
        (case["other_organization"].id, case["foreign_workspace"].id, "SIMPA"),
    ):
        with pytest.raises(DataPlatformError, match="source_not_accessible"):
            list_source_schema_mapping_versions(
                case["db"],
                source_id=case["source"].id,
                organization_id=scope[0],
                workspace_id=scope[1],
                product_code=scope[2],
            )
        with pytest.raises(DataPlatformError, match="source_not_accessible"):
            activate_source_schema_mapping_version(
                case["db"],
                source_id=case["source"].id,
                version_id=first.id,
                organization_id=scope[0],
                workspace_id=scope[1],
                product_code=scope[2],
                actor_id=case["membership"].id,
            )
    with pytest.raises(DataPlatformError, match="schema_mapping_version_not_accessible"):
        activate_source_schema_mapping_version(
            case["db"],
            source_id=case["other_source"].id,
            version_id=first.id,
            organization_id=case["organization"].id,
            workspace_id=case["other_workspace"].id,
            product_code="SIMPA",
            actor_id=case["membership"].id,
        )


def test_audits_are_bounded_and_exclude_contract_contents():
    case = _build_case()
    case["connector"].lifecycle_state = "ACTIVE"
    first = _create(case)
    activate_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        version_id=first.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    second = _create(case, _payload(case, unexpected_field_policy="IGNORE"))
    activate_source_schema_mapping_version(
        case["db"],
        source_id=case["source"].id,
        version_id=second.id,
        organization_id=case["organization"].id,
        workspace_id=case["workspace"].id,
        product_code="SIMPA",
        actor_id=case["membership"].id,
    )
    events = case["db"].scalars(
        select(DataAuditEvent).where(
            DataAuditEvent.event_type.like("data.source_schema_mapping_version.%")
        )
    ).all()
    assert {event.event_type for event in events} == {
        "data.source_schema_mapping_version.created",
        "data.source_schema_mapping_version.activated",
        "data.source_schema_mapping_version.retired",
    }
    detail = " ".join(event.detail for event in events)
    for forbidden in ("External ID", "amount", "NA", "source_schema_json", "field_mapping_json"):
        assert forbidden not in detail
    assert all("fingerprint=" in event.detail for event in events)


def test_sqlite_metadata_enforces_one_active_mapping_per_source():
    case = _build_case()
    base = {
        "source_id": case["source"].id,
        "connector_contract_version_id": case["connector"].id,
        "organization_id": case["organization"].id,
        "workspace_id": case["workspace"].id,
        "product_code": "SIMPA",
        "contract_format_version": 1,
        "schema_kind": "TABULAR",
        "source_schema_json": '[{"ordinal":1}]',
        "field_mapping_json": "[]",
        "missing_value_policy": "PRESERVE_MISSING",
        "unexpected_field_policy": "REJECT",
        "lifecycle_state": "ACTIVE",
    }
    case["db"].add(
        DataSourceSchemaMappingVersion(**base, version_no=1, fingerprint="d" * 64)
    )
    case["db"].flush()
    case["db"].add(
        DataSourceSchemaMappingVersion(**base, version_no=2, fingerprint="e" * 64)
    )
    with pytest.raises(IntegrityError):
        case["db"].flush()
    case["db"].rollback()


def test_routes_permissions_errors_and_no_execution_paths():
    route_methods = {
        (route.path, method)
        for route in data_routes.router.routes
        for method in getattr(route, "methods", set())
    }
    paths = {
        "/api/v1/data/sources/{source_id}/schema-mappings/versions": "POST",
        "/api/v1/data/sources/{source_id}/schema-mappings": "GET",
        "/api/v1/data/sources/{source_id}/schema-mappings/{version_id}/activate": "POST",
    }
    assert all((path, method) in route_methods for path, method in paths.items())
    assert not any(
        "/schema-mappings" in path and method in {"PUT", "PATCH", "DELETE"}
        for path, method in route_methods
    )
    expectations = (
        (data_routes.post_source_schema_mapping_version, "data.governance.manage", "create_source_schema_mapping_version("),
        (data_routes.get_source_schema_mapping_versions, "data.read", "list_source_schema_mapping_versions("),
        (data_routes.post_source_schema_mapping_activation, "data.governance.manage", "activate_source_schema_mapping_version("),
    )
    for function, permission, service_call in expectations:
        source = inspect.getsource(function)
        assert source.index("_require_scope(") < source.index(service_call)
        assert f'permission_code="{permission}"' in source
    assert "actor_membership_id(" in inspect.getsource(data_routes.post_source_schema_mapping_version)
    assert "actor_membership_id(" in inspect.getsource(data_routes.post_source_schema_mapping_activation)
    for error_code, expected_status in (
        ("schema_mapping_version_not_accessible", 404),
        ("connector_contract_version_not_accessible", 404),
        ("schema_mapping_state_conflict", 409),
        ("schema_mapping_unchanged", 409),
        ("schema_mapping_connector_retired", 409),
        ("schema_mapping_connector_not_active", 409),
        ("schema_mapping_source_kind_unsupported", 400),
        ("schema_mapping_field_set_mismatch", 400),
    ):
        assert data_routes._platform_error(DataPlatformError(error_code)).status_code == expected_status

    service_source = Path("src/platform/data/schema_mapping_service.py").read_text()
    locking = service_source.split("def _locked_scoped_source", 1)[1].split(
        "def _normalize_contract", 1
    )[0]
    create = service_source.split("def create_source_schema_mapping_version", 1)[1].split(
        "def list_source_schema_mapping_versions", 1
    )[0]
    activation = service_source.split("def activate_source_schema_mapping_version", 1)[1]
    assert ".with_for_update()" in locking
    assert create.index("_locked_scoped_source(") < create.index("func.max(")
    assert activation.index("_locked_scoped_source(") < activation.index("lifecycle_state")
    for forbidden in (
        "requests",
        "httpx",
        "boto3",
        "paramiko",
        "socket",
        "subprocess",
        "create_engine",
        "eval(",
        "exec(",
    ):
        assert forbidden not in service_source
