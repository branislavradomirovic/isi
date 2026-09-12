from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataSource,
    DataSourceSchemaMappingVersion,
)
from src.platform.data.schemas import (
    SourceSchemaMappingVersionCreate,
    SourceSchemaMappingVersionResponse,
)
from src.platform.data.service import DataPlatformError, get_scoped_source


_FIELD_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_timestamp(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DataPlatformError("invalid_schema_mapping_contract") from exc


def _locked_scoped_source(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> DataSource:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    locked_source = session.scalar(
        select(DataSource)
        .where(
            DataSource.id == source.id,
            DataSource.organization_id == organization_id,
            DataSource.workspace_id == workspace_id,
            DataSource.product_code == product_code,
            DataSource.status == "active",
        )
        .with_for_update()
    )
    if locked_source is None:
        raise DataPlatformError("source_not_accessible")
    return locked_source


def _normalize_contract(
    payload: SourceSchemaMappingVersionCreate,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fields = sorted(payload.source_schema, key=lambda item: item.ordinal)
    if [field.ordinal for field in fields] != list(range(1, len(fields) + 1)):
        raise DataPlatformError("schema_mapping_ordinals_invalid")

    normalized_fields: list[dict[str, Any]] = []
    declared_fields: dict[str, int] = {}
    for field in fields:
        source_field = field.source_field.strip()
        if not source_field:
            raise DataPlatformError("schema_mapping_source_field_invalid")
        if source_field in declared_fields:
            raise DataPlatformError("schema_mapping_source_field_duplicate")
        declared_fields[source_field] = field.ordinal
        normalized_fields.append(
            {
                "ordinal": field.ordinal,
                "source_field": source_field,
                "logical_type": field.logical_type,
                "required": field.required,
                "nullable": field.nullable,
                "missing_values": sorted(set(field.missing_values)),
            }
        )

    mappings_by_source: dict[str, dict[str, Any]] = {}
    mapped_keys: set[str] = set()
    for mapping in payload.field_mapping:
        source_field = mapping.source_field.strip()
        if not source_field:
            raise DataPlatformError("schema_mapping_source_field_invalid")
        if source_field not in declared_fields:
            raise DataPlatformError("schema_mapping_field_set_mismatch")
        if source_field in mappings_by_source:
            raise DataPlatformError("schema_mapping_field_set_mismatch")

        field_key = mapping.field_key if mapping.field_key is not None else ""
        if mapping.disposition == "MAP":
            if not field_key:
                raise DataPlatformError("schema_mapping_field_key_required")
            if len(field_key) > 120 or _FIELD_KEY_PATTERN.fullmatch(field_key) is None:
                raise DataPlatformError("schema_mapping_field_key_invalid")
            normalized_key = field_key.casefold()
            if normalized_key in mapped_keys:
                raise DataPlatformError("schema_mapping_field_key_duplicate")
            mapped_keys.add(normalized_key)
            normalized_mapping = {
                "source_field": source_field,
                "disposition": "MAP",
                "field_key": normalized_key,
            }
        else:
            if field_key:
                raise DataPlatformError("schema_mapping_field_key_forbidden")
            normalized_mapping = {
                "source_field": source_field,
                "disposition": "IGNORE",
                "field_key": None,
            }
        mappings_by_source[source_field] = normalized_mapping

    if set(mappings_by_source) != set(declared_fields):
        raise DataPlatformError("schema_mapping_field_set_mismatch")

    normalized_mappings = [
        mappings_by_source[field["source_field"]]
        for field in normalized_fields
    ]
    return normalized_fields, normalized_mappings


def _contract_fingerprint(
    *,
    source_id: uuid.UUID,
    connector_contract_version_id: uuid.UUID,
    schema_kind: str,
    source_schema: list[dict[str, Any]],
    field_mapping: list[dict[str, Any]],
    missing_value_policy: str,
    unexpected_field_policy: str,
) -> str:
    semantic_content = {
        "source_id": str(source_id),
        "connector_contract_version_id": str(connector_contract_version_id),
        "contract_format_version": 1,
        "schema_kind": schema_kind,
        "source_schema": source_schema,
        "field_mapping": field_mapping,
        "missing_value_policy": missing_value_policy,
        "unexpected_field_policy": unexpected_field_policy,
    }
    return hashlib.sha256(_canonical_json(semantic_content).encode("utf-8")).hexdigest()


def _response(row: DataSourceSchemaMappingVersion) -> SourceSchemaMappingVersionResponse:
    return SourceSchemaMappingVersionResponse(
        id=row.id,
        source_id=row.source_id,
        connector_contract_version_id=row.connector_contract_version_id,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        product_code=row.product_code,
        version_no=row.version_no,
        contract_format_version=row.contract_format_version,
        schema_kind=row.schema_kind,
        source_schema=json.loads(row.source_schema_json),
        field_mapping=json.loads(row.field_mapping_json),
        missing_value_policy=row.missing_value_policy,
        unexpected_field_policy=row.unexpected_field_policy,
        fingerprint=row.fingerprint,
        lifecycle_state=row.lifecycle_state,
        created_by_membership_id=row.created_by_membership_id,
        activated_by_membership_id=row.activated_by_membership_id,
        retired_by_membership_id=row.retired_by_membership_id,
        created_at=_aware_timestamp(row.created_at),
        activated_at=_aware_timestamp(row.activated_at),
        retired_at=_aware_timestamp(row.retired_at),
    )


def _audit(
    session: Session,
    *,
    row: DataSourceSchemaMappingVersion,
    actor_id: uuid.UUID | None,
    event_type: str,
    transition: str,
    replacement_id: uuid.UUID | None = None,
) -> None:
    detail = (
        f"version_no={row.version_no}; "
        f"connector_contract_version_id={row.connector_contract_version_id}; "
        f"fingerprint={row.fingerprint}; transition={transition}"
    )
    if replacement_id is not None:
        detail = f"{detail}; replacement_id={replacement_id}"
    session.add(
        DataAuditEvent(
            organization_id=row.organization_id,
            workspace_id=row.workspace_id,
            product_code=row.product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type="source_schema_mapping_version",
            entity_id=row.id,
            detail=detail,
        )
    )


def create_source_schema_mapping_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    payload: SourceSchemaMappingVersionCreate,
    actor_id: uuid.UUID | None,
) -> SourceSchemaMappingVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    if source.source_kind != "dataset":
        raise DataPlatformError("schema_mapping_source_kind_unsupported")

    connector = session.scalar(
        select(DataConnectorContractVersion).where(
            DataConnectorContractVersion.id == payload.connector_contract_version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
    )
    if connector is None:
        raise DataPlatformError("connector_contract_version_not_accessible")
    if connector.lifecycle_state == "RETIRED":
        raise DataPlatformError("schema_mapping_connector_retired")

    source_schema, field_mapping = _normalize_contract(payload)
    source_schema_json = _canonical_json(source_schema)
    field_mapping_json = _canonical_json(field_mapping)
    fingerprint = _contract_fingerprint(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        schema_kind=payload.schema_kind,
        source_schema=source_schema,
        field_mapping=field_mapping,
        missing_value_policy=payload.missing_value_policy,
        unexpected_field_policy=payload.unexpected_field_policy,
    )
    latest = session.scalar(
        select(DataSourceSchemaMappingVersion)
        .where(DataSourceSchemaMappingVersion.source_id == source.id)
        .order_by(DataSourceSchemaMappingVersion.version_no.desc())
        .limit(1)
    )
    if latest is not None and latest.fingerprint == fingerprint:
        raise DataPlatformError("schema_mapping_unchanged")

    next_version = (
        session.scalar(
            select(func.max(DataSourceSchemaMappingVersion.version_no)).where(
                DataSourceSchemaMappingVersion.source_id == source.id
            )
        )
        or 0
    ) + 1
    row = DataSourceSchemaMappingVersion(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=next_version,
        contract_format_version=1,
        schema_kind=payload.schema_kind,
        source_schema_json=source_schema_json,
        field_mapping_json=field_mapping_json,
        missing_value_policy=payload.missing_value_policy,
        unexpected_field_policy=payload.unexpected_field_policy,
        fingerprint=fingerprint,
        lifecycle_state="DRAFT",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _audit(
        session,
        row=row,
        actor_id=actor_id,
        event_type="data.source_schema_mapping_version.created",
        transition="CREATED_DRAFT",
    )
    return _response(row)


def list_source_schema_mapping_versions(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[SourceSchemaMappingVersionResponse]:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    rows = session.scalars(
        select(DataSourceSchemaMappingVersion)
        .where(
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.organization_id == source.organization_id,
            DataSourceSchemaMappingVersion.workspace_id == source.workspace_id,
            DataSourceSchemaMappingVersion.product_code == source.product_code,
        )
        .order_by(
            DataSourceSchemaMappingVersion.version_no.desc(),
            DataSourceSchemaMappingVersion.id,
        )
    ).all()
    return [_response(row) for row in rows]


def activate_source_schema_mapping_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
) -> SourceSchemaMappingVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    row = session.scalar(
        select(DataSourceSchemaMappingVersion)
        .where(
            DataSourceSchemaMappingVersion.id == version_id,
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.organization_id == source.organization_id,
            DataSourceSchemaMappingVersion.workspace_id == source.workspace_id,
            DataSourceSchemaMappingVersion.product_code == source.product_code,
        )
        .with_for_update()
    )
    if row is None:
        raise DataPlatformError("schema_mapping_version_not_accessible")
    if row.lifecycle_state == "ACTIVE":
        return _response(row)
    if row.lifecycle_state != "DRAFT":
        raise DataPlatformError("schema_mapping_state_conflict")

    connector_is_active = session.scalar(
        select(DataConnectorContractVersion.id).where(
            DataConnectorContractVersion.id == row.connector_contract_version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
            DataConnectorContractVersion.lifecycle_state == "ACTIVE",
        )
    )
    if connector_is_active is None:
        raise DataPlatformError("schema_mapping_connector_not_active")

    now = _utcnow()
    active_rows = session.scalars(
        select(DataSourceSchemaMappingVersion)
        .where(
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.lifecycle_state == "ACTIVE",
        )
        .order_by(DataSourceSchemaMappingVersion.version_no)
        .with_for_update()
    ).all()
    for active in active_rows:
        active.lifecycle_state = "RETIRED"
        active.retired_by_membership_id = actor_id
        active.retired_at = now
        _audit(
            session,
            row=active,
            actor_id=actor_id,
            event_type="data.source_schema_mapping_version.retired",
            transition="ACTIVE_TO_RETIRED",
            replacement_id=row.id,
        )
    session.flush()

    row.lifecycle_state = "ACTIVE"
    row.activated_by_membership_id = actor_id
    row.activated_at = now
    _audit(
        session,
        row=row,
        actor_id=actor_id,
        event_type="data.source_schema_mapping_version.activated",
        transition="DRAFT_TO_ACTIVE",
    )
    session.flush()
    return _response(row)
