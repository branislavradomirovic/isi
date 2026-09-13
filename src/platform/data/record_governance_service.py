from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.ingestion import StructuredRecord
from src.platform.data.models import (
    DataAuditEvent,
    DataConnectorContractVersion,
    DataIngestionRun,
    DataNormalizedRecord,
    DataRecordEntity,
    DataRecordGovernancePolicyVersion,
    DataRecordResolution,
    DataSource,
    DataSourceSchemaMappingVersion,
    DataSourceVersion,
)
from src.platform.data.schemas import (
    RecordGovernancePolicyVersionCreate,
    RecordGovernancePolicyVersionResponse,
    RecordQuarantineDetailResponse,
    RecordQuarantineListItem,
    RecordResolutionCreate,
    RecordResolutionResponse,
)
from src.platform.data.service import DataPlatformError, get_scoped_source


_INTEGER_PATTERN = re.compile(r"^[+-]?[0-9]+$")
_MAX_CANONICAL_NUMBER_CHARS = 4096
_ACCEPTABLE_RECONCILIATION_REASONS = {
    "IDENTITY_CONTENT_CONFLICT",
    "ENTITY_UNRESOLVED",
}


@dataclass(frozen=True)
class RecordMaterializationResult:
    materialized: int
    accepted: int
    duplicates: int
    quarantined: int


class _TypeNormalizationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_timestamp(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _canonical_json(value: object, *, error_code: str = "record_materialization_integrity_failed") -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DataPlatformError(error_code) from exc


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


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
    locked = session.scalar(
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
    if locked is None:
        raise DataPlatformError("source_not_accessible")
    return locked


def _load_policy_binding(
    session: Session,
    *,
    source: DataSource,
    connector_contract_version_id: uuid.UUID,
    schema_mapping_version_id: uuid.UUID,
) -> tuple[DataConnectorContractVersion, DataSourceSchemaMappingVersion]:
    connector = session.scalar(
        select(DataConnectorContractVersion).where(
            DataConnectorContractVersion.id == connector_contract_version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
    )
    if connector is None:
        raise DataPlatformError("connector_contract_version_not_accessible")
    mapping = session.scalar(
        select(DataSourceSchemaMappingVersion).where(
            DataSourceSchemaMappingVersion.id == schema_mapping_version_id,
            DataSourceSchemaMappingVersion.source_id == source.id,
            DataSourceSchemaMappingVersion.organization_id == source.organization_id,
            DataSourceSchemaMappingVersion.workspace_id == source.workspace_id,
            DataSourceSchemaMappingVersion.product_code == source.product_code,
        )
    )
    if mapping is None:
        raise DataPlatformError("schema_mapping_version_not_accessible")
    if mapping.connector_contract_version_id != connector.id:
        raise DataPlatformError("record_policy_binding_mismatch")
    return connector, mapping


def _mapped_field_keys(mapping: DataSourceSchemaMappingVersion) -> set[str]:
    try:
        items = json.loads(mapping.field_mapping_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DataPlatformError("record_policy_mapping_integrity_failed") from exc
    if not isinstance(items, list):
        raise DataPlatformError("record_policy_mapping_integrity_failed")
    result: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise DataPlatformError("record_policy_mapping_integrity_failed")
        if item.get("disposition") == "MAP":
            key = item.get("field_key")
            if not isinstance(key, str) or not key or key in result:
                raise DataPlatformError("record_policy_mapping_integrity_failed")
            result.add(key)
    return result


def _policy_fingerprint(
    *,
    source_id: uuid.UUID,
    connector_contract_version_id: uuid.UUID,
    schema_mapping_version_id: uuid.UUID,
    identity_field_keys: list[str],
) -> str:
    return _sha256_json(
        {
            "source_id": str(source_id),
            "connector_contract_version_id": str(connector_contract_version_id),
            "schema_mapping_version_id": str(schema_mapping_version_id),
            "contract_format_version": 1,
            "identity_field_keys": identity_field_keys,
            "missing_identity_policy": "QUARANTINE",
            "exact_duplicate_policy": "LINK_EXISTING",
            "conflict_policy": "QUARANTINE",
        }
    )


def _policy_response(row: DataRecordGovernancePolicyVersion) -> RecordGovernancePolicyVersionResponse:
    try:
        identity_field_keys = json.loads(row.identity_field_keys_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DataPlatformError("record_policy_integrity_failed") from exc
    if not isinstance(identity_field_keys, list) or not all(
        isinstance(item, str) for item in identity_field_keys
    ):
        raise DataPlatformError("record_policy_integrity_failed")
    return RecordGovernancePolicyVersionResponse(
        id=row.id,
        source_id=row.source_id,
        connector_contract_version_id=row.connector_contract_version_id,
        schema_mapping_version_id=row.schema_mapping_version_id,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        product_code=row.product_code,
        version_no=row.version_no,
        contract_format_version=row.contract_format_version,
        identity_field_keys=identity_field_keys,
        missing_identity_policy=row.missing_identity_policy,
        exact_duplicate_policy=row.exact_duplicate_policy,
        conflict_policy=row.conflict_policy,
        fingerprint=row.fingerprint,
        lifecycle_state=row.lifecycle_state,
        created_by_membership_id=row.created_by_membership_id,
        activated_by_membership_id=row.activated_by_membership_id,
        retired_by_membership_id=row.retired_by_membership_id,
        created_at=_aware_timestamp(row.created_at),
        activated_at=_aware_timestamp(row.activated_at),
        retired_at=_aware_timestamp(row.retired_at),
    )


def _audit_policy(
    session: Session,
    *,
    row: DataRecordGovernancePolicyVersion,
    actor_id: uuid.UUID | None,
    event_type: str,
    transition: str,
    replacement_id: uuid.UUID | None = None,
) -> None:
    detail = (
        f"version_no={row.version_no}; connector_contract_version_id={row.connector_contract_version_id}; "
        f"schema_mapping_version_id={row.schema_mapping_version_id}; fingerprint={row.fingerprint}; "
        f"transition={transition}"
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
            entity_type="record_governance_policy_version",
            entity_id=row.id,
            detail=detail,
        )
    )


def create_record_governance_policy_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    payload: RecordGovernancePolicyVersionCreate,
    actor_id: uuid.UUID | None,
) -> RecordGovernancePolicyVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    if source.source_kind != "dataset":
        raise DataPlatformError("record_policy_source_kind_unsupported")
    connector, mapping = _load_policy_binding(
        session,
        source=source,
        connector_contract_version_id=payload.connector_contract_version_id,
        schema_mapping_version_id=payload.schema_mapping_version_id,
    )
    if connector.lifecycle_state == "RETIRED":
        raise DataPlatformError("record_policy_connector_retired")
    if mapping.lifecycle_state == "RETIRED":
        raise DataPlatformError("record_policy_mapping_retired")
    identity_field_keys = sorted(
        {
            key.strip().casefold()
            for key in payload.identity_field_keys
            if isinstance(key, str) and key.strip()
        }
    )
    if not identity_field_keys:
        raise DataPlatformError("record_policy_identity_fields_required")
    if any(len(key) > 120 for key in identity_field_keys):
        raise DataPlatformError("record_policy_identity_field_invalid")
    if not set(identity_field_keys).issubset(_mapped_field_keys(mapping)):
        raise DataPlatformError("record_policy_identity_field_not_mapped")
    fingerprint = _policy_fingerprint(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
        identity_field_keys=identity_field_keys,
    )
    latest = session.scalar(
        select(DataRecordGovernancePolicyVersion)
        .where(DataRecordGovernancePolicyVersion.source_id == source.id)
        .order_by(DataRecordGovernancePolicyVersion.version_no.desc())
        .limit(1)
    )
    if latest is not None and latest.fingerprint == fingerprint:
        raise DataPlatformError("record_policy_unchanged")
    next_version = (
        session.scalar(
            select(func.max(DataRecordGovernancePolicyVersion.version_no)).where(
                DataRecordGovernancePolicyVersion.source_id == source.id
            )
        )
        or 0
    ) + 1
    row = DataRecordGovernancePolicyVersion(
        source_id=source.id,
        connector_contract_version_id=connector.id,
        schema_mapping_version_id=mapping.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=next_version,
        contract_format_version=1,
        identity_field_keys_json=_canonical_json(identity_field_keys),
        missing_identity_policy="QUARANTINE",
        exact_duplicate_policy="LINK_EXISTING",
        conflict_policy="QUARANTINE",
        fingerprint=fingerprint,
        lifecycle_state="DRAFT",
        created_by_membership_id=actor_id,
    )
    session.add(row)
    session.flush()
    _audit_policy(
        session,
        row=row,
        actor_id=actor_id,
        event_type="data.record_governance_policy_version.created",
        transition="CREATED_DRAFT",
    )
    return _policy_response(row)


def list_record_governance_policy_versions(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[RecordGovernancePolicyVersionResponse]:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    rows = session.scalars(
        select(DataRecordGovernancePolicyVersion)
        .where(
            DataRecordGovernancePolicyVersion.source_id == source.id,
            DataRecordGovernancePolicyVersion.organization_id == source.organization_id,
            DataRecordGovernancePolicyVersion.workspace_id == source.workspace_id,
            DataRecordGovernancePolicyVersion.product_code == source.product_code,
        )
        .order_by(DataRecordGovernancePolicyVersion.version_no.desc())
    ).all()
    return [_policy_response(row) for row in rows]


def activate_record_governance_policy_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    policy_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
) -> RecordGovernancePolicyVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    row = session.scalar(
        select(DataRecordGovernancePolicyVersion)
        .where(
            DataRecordGovernancePolicyVersion.id == policy_id,
            DataRecordGovernancePolicyVersion.source_id == source.id,
            DataRecordGovernancePolicyVersion.organization_id == source.organization_id,
            DataRecordGovernancePolicyVersion.workspace_id == source.workspace_id,
            DataRecordGovernancePolicyVersion.product_code == source.product_code,
        )
        .with_for_update()
    )
    if row is None:
        raise DataPlatformError("record_policy_version_not_accessible")
    if row.lifecycle_state == "ACTIVE":
        return _policy_response(row)
    if row.lifecycle_state != "DRAFT":
        raise DataPlatformError("record_policy_state_conflict")
    connector, mapping = _load_policy_binding(
        session,
        source=source,
        connector_contract_version_id=row.connector_contract_version_id,
        schema_mapping_version_id=row.schema_mapping_version_id,
    )
    if connector.lifecycle_state != "ACTIVE":
        raise DataPlatformError("record_policy_connector_not_active")
    if mapping.lifecycle_state != "ACTIVE":
        raise DataPlatformError("record_policy_mapping_not_active")
    now = _utcnow()
    active_rows = session.scalars(
        select(DataRecordGovernancePolicyVersion)
        .where(
            DataRecordGovernancePolicyVersion.source_id == source.id,
            DataRecordGovernancePolicyVersion.lifecycle_state == "ACTIVE",
        )
        .order_by(DataRecordGovernancePolicyVersion.version_no)
        .with_for_update()
    ).all()
    for active in active_rows:
        active.lifecycle_state = "RETIRED"
        active.retired_by_membership_id = actor_id
        active.retired_at = now
        _audit_policy(
            session,
            row=active,
            actor_id=actor_id,
            event_type="data.record_governance_policy_version.retired",
            transition="ACTIVE_TO_RETIRED",
            replacement_id=row.id,
        )
    session.flush()
    row.lifecycle_state = "ACTIVE"
    row.activated_by_membership_id = actor_id
    row.activated_at = now
    _audit_policy(
        session,
        row=row,
        actor_id=actor_id,
        event_type="data.record_governance_policy_version.activated",
        transition="DRAFT_TO_ACTIVE",
    )
    session.flush()
    return _policy_response(row)


def get_active_record_governance_policy_for_binding(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    connector_contract_version_id: uuid.UUID,
    schema_mapping_version_id: uuid.UUID,
) -> DataRecordGovernancePolicyVersion | None:
    row = session.scalar(
        select(DataRecordGovernancePolicyVersion).where(
            DataRecordGovernancePolicyVersion.source_id == source_id,
            DataRecordGovernancePolicyVersion.lifecycle_state == "ACTIVE",
        )
    )
    if row is None:
        return None
    if (
        row.organization_id != organization_id
        or row.workspace_id != workspace_id
        or row.product_code != product_code
        or row.connector_contract_version_id != connector_contract_version_id
        or row.schema_mapping_version_id != schema_mapping_version_id
    ):
        raise DataPlatformError("record_policy_binding_mismatch")
    return row


def validate_pinned_record_governance_policy(
    session: Session,
    *,
    run: DataIngestionRun,
) -> DataRecordGovernancePolicyVersion | None:
    if run.record_governance_policy_version_id is None:
        return None
    policy = session.get(
        DataRecordGovernancePolicyVersion,
        run.record_governance_policy_version_id,
    )
    if policy is None:
        raise DataPlatformError("record_policy_integrity_failed")
    if (
        policy.source_id != run.source_id
        or policy.organization_id != run.organization_id
        or policy.workspace_id != run.workspace_id
        or policy.product_code != run.product_code
        or policy.connector_contract_version_id != run.connector_contract_version_id
        or policy.schema_mapping_version_id != run.schema_mapping_version_id
    ):
        raise DataPlatformError("record_policy_integrity_failed")
    mapping = session.get(DataSourceSchemaMappingVersion, run.schema_mapping_version_id)
    if mapping is None or mapping.connector_contract_version_id != run.connector_contract_version_id:
        raise DataPlatformError("record_policy_integrity_failed")
    return policy


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise _TypeNormalizationError
    decimal_tuple = value.as_tuple()
    digits = decimal_tuple.digits
    if not any(digits):
        return "0"
    exponent = decimal_tuple.exponent
    significant_digit_count = len(digits)
    while digits[significant_digit_count - 1] == 0:
        significant_digit_count -= 1
    exponent += len(digits) - significant_digit_count
    digits = digits[:significant_digit_count]
    digit_count = len(digits)
    sign_count = int(decimal_tuple.sign)
    if exponent >= 0:
        rendered_length = sign_count + digit_count + exponent
        decimal_position = digit_count
    else:
        decimal_position = digit_count + exponent
        rendered_length = (
            sign_count + digit_count + 1
            if decimal_position > 0
            else sign_count + 2 - decimal_position + digit_count
        )
    if rendered_length > _MAX_CANONICAL_NUMBER_CHARS:
        raise _TypeNormalizationError
    coefficient = "".join(str(digit) for digit in digits)
    sign = "-" if decimal_tuple.sign else ""
    if exponent >= 0:
        return f"{sign}{coefficient}{'0' * exponent}"
    if decimal_position > 0:
        return f"{sign}{coefficient[:decimal_position]}.{coefficient[decimal_position:]}"
    return f"{sign}0.{'0' * -decimal_position}{coefficient}"


def _normalize_json_value(value: object) -> object:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return json.loads(rendered)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _TypeNormalizationError from exc


def _normalize_value(value: object, logical_type: str) -> object:
    try:
        if logical_type == "STRING":
            if not isinstance(value, str):
                raise _TypeNormalizationError
            return value
        if logical_type == "INTEGER":
            if isinstance(value, bool):
                raise _TypeNormalizationError
            if isinstance(value, int):
                return value
            if isinstance(value, str) and _INTEGER_PATTERN.fullmatch(value):
                return int(value, 10)
            raise _TypeNormalizationError
        if logical_type == "NUMBER":
            if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
                raise _TypeNormalizationError
            if isinstance(value, float) and not math.isfinite(value):
                raise _TypeNormalizationError
            return _canonical_decimal(Decimal(str(value)))
        if logical_type == "BOOLEAN":
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.casefold() in {"true", "false"}:
                return value.casefold() == "true"
            raise _TypeNormalizationError
        if logical_type == "DATE":
            if not isinstance(value, str):
                raise _TypeNormalizationError
            return date.fromisoformat(value).isoformat()
        if logical_type == "DATETIME":
            if not isinstance(value, str):
                raise _TypeNormalizationError
            return datetime.fromisoformat(value).isoformat()
        if logical_type == "JSON":
            return _normalize_json_value(value)
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise _TypeNormalizationError from exc
    raise DataPlatformError("record_materialization_mapping_integrity_failed")


def _mapping_contract(
    mapping: DataSourceSchemaMappingVersion,
    policy: DataRecordGovernancePolicyVersion,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    try:
        source_schema = json.loads(mapping.source_schema_json)
        field_mapping = json.loads(mapping.field_mapping_json)
        identity_field_keys = json.loads(policy.identity_field_keys_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DataPlatformError("record_materialization_mapping_integrity_failed") from exc
    if (
        not isinstance(source_schema, list)
        or not source_schema
        or not isinstance(field_mapping, list)
        or not isinstance(identity_field_keys, list)
        or not identity_field_keys
        or mapping.missing_value_policy != "PRESERVE_MISSING"
        or mapping.unexpected_field_policy not in {"REJECT", "IGNORE"}
        or policy.contract_format_version != 1
        or policy.missing_identity_policy != "QUARANTINE"
        or policy.exact_duplicate_policy != "LINK_EXISTING"
        or policy.conflict_policy != "QUARANTINE"
    ):
        raise DataPlatformError("record_materialization_mapping_integrity_failed")
    fields_by_source: dict[str, dict[str, Any]] = {}
    expected_ordinals = list(range(1, len(source_schema) + 1))
    if [item.get("ordinal") for item in source_schema if isinstance(item, dict)] != expected_ordinals:
        raise DataPlatformError("record_materialization_mapping_integrity_failed")
    for field in source_schema:
        if not isinstance(field, dict):
            raise DataPlatformError("record_materialization_mapping_integrity_failed")
        source_field = field.get("source_field")
        logical_type = field.get("logical_type")
        if (
            not isinstance(source_field, str)
            or not source_field
            or source_field in fields_by_source
            or logical_type not in {"STRING", "INTEGER", "NUMBER", "BOOLEAN", "DATE", "DATETIME", "JSON"}
            or not isinstance(field.get("required"), bool)
            or not isinstance(field.get("nullable"), bool)
            or not isinstance(field.get("missing_values"), list)
            or not all(isinstance(item, str) for item in field["missing_values"])
        ):
            raise DataPlatformError("record_materialization_mapping_integrity_failed")
        fields_by_source[source_field] = field
    mappings_by_source: dict[str, dict[str, Any]] = {}
    mapped_keys: set[str] = set()
    for item in field_mapping:
        if not isinstance(item, dict):
            raise DataPlatformError("record_materialization_mapping_integrity_failed")
        source_field = item.get("source_field")
        disposition = item.get("disposition")
        field_key = item.get("field_key")
        if source_field not in fields_by_source or source_field in mappings_by_source:
            raise DataPlatformError("record_materialization_mapping_integrity_failed")
        if disposition == "MAP":
            if not isinstance(field_key, str) or not field_key or field_key in mapped_keys:
                raise DataPlatformError("record_materialization_mapping_integrity_failed")
            mapped_keys.add(field_key)
        elif disposition == "IGNORE":
            if field_key is not None:
                raise DataPlatformError("record_materialization_mapping_integrity_failed")
        else:
            raise DataPlatformError("record_materialization_mapping_integrity_failed")
        mappings_by_source[source_field] = item
    if set(mappings_by_source) != set(fields_by_source):
        raise DataPlatformError("record_materialization_mapping_integrity_failed")
    if (
        not all(isinstance(item, str) for item in identity_field_keys)
        or identity_field_keys != sorted(set(identity_field_keys))
        or not set(identity_field_keys).issubset(mapped_keys)
    ):
        raise DataPlatformError("record_materialization_policy_integrity_failed")
    ordered_fields = sorted(source_schema, key=lambda item: item["ordinal"])
    return ordered_fields, mappings_by_source, identity_field_keys


def _normalize_record(
    record: StructuredRecord,
    *,
    mapping: DataSourceSchemaMappingVersion,
    policy: DataRecordGovernancePolicyVersion,
    fields: list[dict[str, Any]],
    mappings_by_source: dict[str, dict[str, Any]],
    identity_field_keys: list[str],
) -> tuple[dict[str, object], str, str, str | None]:
    declared = {field["source_field"] for field in fields}
    unexpected = set(record.values) - declared
    normalized: dict[str, object] = {}
    missing_required = False
    missing_identity = False
    type_failed = False
    for field in fields:
        source_field = field["source_field"]
        field_binding = mappings_by_source[source_field]
        raw_value = record.values.get(source_field)
        missing = raw_value is None or (
            isinstance(raw_value, str) and raw_value in field["missing_values"]
        )
        mapped_key = field_binding.get("field_key")
        if missing:
            if field["required"] or not field["nullable"]:
                missing_required = True
            if field_binding["disposition"] == "MAP":
                normalized[mapped_key] = None
                if mapped_key in identity_field_keys:
                    missing_identity = True
            continue
        if field_binding["disposition"] == "IGNORE":
            continue
        try:
            normalized[mapped_key] = _normalize_value(raw_value, field["logical_type"])
        except _TypeNormalizationError:
            normalized[mapped_key] = None
            type_failed = True
    reason = None
    if unexpected and mapping.unexpected_field_policy == "REJECT":
        reason = "UNEXPECTED_FIELD"
    elif type_failed:
        reason = "TYPE_NORMALIZATION_FAILED"
    elif missing_identity:
        reason = "MISSING_IDENTITY"
    elif missing_required:
        reason = "REQUIRED_FIELD_MISSING"
    normalized_json = _canonical_json(normalized)
    identity_fingerprint = _sha256_json(
        {
            "contract_format_version": 1,
            "record_governance_policy_version_id": str(policy.id),
            "identity": [[key, normalized.get(key)] for key in identity_field_keys],
        }
    )
    content_fingerprint = _sha256_json(
        {
            "contract_format_version": 1,
            "schema_mapping_version_id": str(mapping.id),
            "normalized_record": normalized,
        }
    )
    return json.loads(normalized_json), identity_fingerprint, content_fingerprint, reason


def _materialization_counts(rows: list[DataNormalizedRecord]) -> RecordMaterializationResult:
    return RecordMaterializationResult(
        materialized=len(rows),
        accepted=sum(row.disposition == "ACCEPTED" for row in rows),
        duplicates=sum(row.disposition == "DUPLICATE" for row in rows),
        quarantined=sum(row.disposition == "QUARANTINED" for row in rows),
    )


def materialize_ingestion_run_records(
    session: Session,
    *,
    run: DataIngestionRun,
    records: tuple[StructuredRecord, ...],
) -> RecordMaterializationResult:
    locked_run = session.scalar(
        select(DataIngestionRun).where(DataIngestionRun.id == run.id).with_for_update()
    )
    if locked_run is None or locked_run.record_governance_policy_version_id is None:
        raise DataPlatformError("record_materialization_policy_required")
    if [record.ordinal for record in records] != list(range(1, len(records) + 1)) or any(
        not record.locator for record in records
    ):
        raise DataPlatformError("record_materialization_structured_records_invalid")
    existing = session.scalars(
        select(DataNormalizedRecord)
        .where(DataNormalizedRecord.ingestion_run_id == locked_run.id)
        .order_by(DataNormalizedRecord.source_record_ordinal)
    ).all()
    source = session.scalar(
        select(DataSource)
        .where(
            DataSource.id == locked_run.source_id,
            DataSource.organization_id == locked_run.organization_id,
            DataSource.workspace_id == locked_run.workspace_id,
            DataSource.product_code == locked_run.product_code,
        )
        .with_for_update()
    )
    version = session.get(DataSourceVersion, locked_run.source_version_id)
    connector = session.get(DataConnectorContractVersion, locked_run.connector_contract_version_id)
    mapping = session.get(DataSourceSchemaMappingVersion, locked_run.schema_mapping_version_id)
    policy = validate_pinned_record_governance_policy(session, run=locked_run)
    if (
        source is None
        or version is None
        or connector is None
        or mapping is None
        or policy is None
        or source.source_kind != "dataset"
        or version.source_id != source.id
        or version.organization_id != source.organization_id
        or version.workspace_id != source.workspace_id
        or version.product_code != source.product_code
        or connector.source_id != source.id
        or connector.organization_id != source.organization_id
        or connector.workspace_id != source.workspace_id
        or connector.product_code != source.product_code
        or mapping.source_id != source.id
        or mapping.organization_id != source.organization_id
        or mapping.workspace_id != source.workspace_id
        or mapping.product_code != source.product_code
    ):
        raise DataPlatformError("record_materialization_provenance_integrity_failed")
    fields, mappings_by_source, identity_field_keys = _mapping_contract(mapping, policy)
    if existing:
        expected_ordinals = list(range(1, len(records) + 1))
        inconsistent = (
            len(existing) != len(records)
            or [row.source_record_ordinal for row in existing] != expected_ordinals
            or any(
                row.source_id != locked_run.source_id
                or row.source_version_id != locked_run.source_version_id
                or row.connector_contract_version_id != locked_run.connector_contract_version_id
                or row.schema_mapping_version_id != locked_run.schema_mapping_version_id
                or row.record_governance_policy_version_id
                != locked_run.record_governance_policy_version_id
                or row.organization_id != locked_run.organization_id
                or row.workspace_id != locked_run.workspace_id
                or row.product_code != locked_run.product_code
                or row.source_locator != structured.locator[:1000]
                for row, structured in zip(existing, records)
            )
        )
        if not inconsistent:
            for row, structured in zip(existing, records):
                normalized, identity_fingerprint, content_fingerprint, _reason = _normalize_record(
                    structured,
                    mapping=mapping,
                    policy=policy,
                    fields=fields,
                    mappings_by_source=mappings_by_source,
                    identity_field_keys=identity_field_keys,
                )
                if (
                    row.normalized_record_json != _canonical_json(normalized)
                    or row.identity_fingerprint != identity_fingerprint
                    or row.content_fingerprint != content_fingerprint
                ):
                    inconsistent = True
                    break
        if inconsistent:
            raise DataPlatformError("record_materialization_partial_integrity_failed")
        return _materialization_counts(existing)
    created_rows: list[DataNormalizedRecord] = []
    with session.begin_nested():
        for structured_record in records:
            normalized, identity_fingerprint, content_fingerprint, invalid_reason = _normalize_record(
                structured_record,
                mapping=mapping,
                policy=policy,
                fields=fields,
                mappings_by_source=mappings_by_source,
                identity_field_keys=identity_field_keys,
            )
            entity = session.scalar(
                select(DataRecordEntity)
                .where(
                    DataRecordEntity.source_id == source.id,
                    DataRecordEntity.record_governance_policy_version_id == policy.id,
                    DataRecordEntity.identity_fingerprint == identity_fingerprint,
                )
                .with_for_update()
            )
            if entity is None:
                entity = DataRecordEntity(
                    source_id=source.id,
                    record_governance_policy_version_id=policy.id,
                    organization_id=source.organization_id,
                    workspace_id=source.workspace_id,
                    product_code=source.product_code,
                    identity_fingerprint=identity_fingerprint,
                    state="QUARANTINED" if invalid_reason else "ACTIVE",
                )
                session.add(entity)
                session.flush()
            accepted = session.scalar(
                select(DataNormalizedRecord)
                .where(
                    DataNormalizedRecord.entity_id == entity.id,
                    DataNormalizedRecord.disposition == "ACCEPTED",
                )
                .with_for_update()
            )
            disposition = "ACCEPTED"
            quarantine_reason = None
            duplicate_of_record_id = None
            conflict_with_record_id = None
            if invalid_reason is not None:
                disposition = "QUARANTINED"
                quarantine_reason = invalid_reason
                entity.state = "QUARANTINED"
            elif accepted is not None and accepted.content_fingerprint == content_fingerprint:
                disposition = "DUPLICATE"
                duplicate_of_record_id = accepted.id
            elif accepted is not None:
                disposition = "QUARANTINED"
                quarantine_reason = "IDENTITY_CONTENT_CONFLICT"
                conflict_with_record_id = accepted.id
                entity.state = "QUARANTINED"
            else:
                unresolved = session.scalar(
                    select(DataNormalizedRecord.id)
                    .where(
                        DataNormalizedRecord.entity_id == entity.id,
                        DataNormalizedRecord.disposition == "QUARANTINED",
                    )
                    .order_by(DataNormalizedRecord.created_at, DataNormalizedRecord.id)
                    .limit(1)
                )
                if unresolved is not None:
                    disposition = "QUARANTINED"
                    quarantine_reason = "ENTITY_UNRESOLVED"
                    entity.state = "QUARANTINED"
                else:
                    entity.state = "ACTIVE"
            row = DataNormalizedRecord(
                source_id=source.id,
                source_version_id=version.id,
                ingestion_run_id=locked_run.id,
                connector_contract_version_id=connector.id,
                schema_mapping_version_id=mapping.id,
                record_governance_policy_version_id=policy.id,
                organization_id=source.organization_id,
                workspace_id=source.workspace_id,
                product_code=source.product_code,
                source_record_ordinal=structured_record.ordinal,
                source_locator=structured_record.locator[:1000],
                entity_id=entity.id,
                normalized_record_json=_canonical_json(normalized),
                identity_fingerprint=identity_fingerprint,
                content_fingerprint=content_fingerprint,
                disposition=disposition,
                duplicate_of_record_id=duplicate_of_record_id,
                conflict_with_record_id=conflict_with_record_id,
                quarantine_reason=quarantine_reason,
            )
            session.add(row)
            session.flush()
            created_rows.append(row)
    return _materialization_counts(created_rows)


def _quarantine_item(row: DataNormalizedRecord) -> RecordQuarantineListItem:
    return RecordQuarantineListItem(
        id=row.id,
        source_id=row.source_id,
        source_version_id=row.source_version_id,
        ingestion_run_id=row.ingestion_run_id,
        connector_contract_version_id=row.connector_contract_version_id,
        schema_mapping_version_id=row.schema_mapping_version_id,
        record_governance_policy_version_id=row.record_governance_policy_version_id,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        product_code=row.product_code,
        source_record_ordinal=row.source_record_ordinal,
        source_locator=row.source_locator,
        entity_id=row.entity_id,
        identity_fingerprint=row.identity_fingerprint,
        content_fingerprint=row.content_fingerprint,
        disposition=row.disposition,
        duplicate_of_record_id=row.duplicate_of_record_id,
        conflict_with_record_id=row.conflict_with_record_id,
        quarantine_reason=row.quarantine_reason,
        created_at=_aware_timestamp(row.created_at),
        updated_at=_aware_timestamp(row.updated_at),
    )


def list_record_quarantine(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[RecordQuarantineListItem]:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    rows = session.scalars(
        select(DataNormalizedRecord)
        .where(
            DataNormalizedRecord.source_id == source.id,
            DataNormalizedRecord.organization_id == source.organization_id,
            DataNormalizedRecord.workspace_id == source.workspace_id,
            DataNormalizedRecord.product_code == source.product_code,
            DataNormalizedRecord.disposition == "QUARANTINED",
        )
        .order_by(DataNormalizedRecord.created_at, DataNormalizedRecord.id)
    ).all()
    return [_quarantine_item(row) for row in rows]


def get_record_quarantine_detail(
    session: Session,
    *,
    source_id: uuid.UUID,
    record_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> RecordQuarantineDetailResponse:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    row = session.scalar(
        select(DataNormalizedRecord).where(
            DataNormalizedRecord.id == record_id,
            DataNormalizedRecord.source_id == source.id,
            DataNormalizedRecord.organization_id == source.organization_id,
            DataNormalizedRecord.workspace_id == source.workspace_id,
            DataNormalizedRecord.product_code == source.product_code,
            DataNormalizedRecord.disposition == "QUARANTINED",
        )
    )
    if row is None:
        raise DataPlatformError("record_quarantine_not_accessible")
    accepted = None
    if row.entity_id is not None:
        accepted = session.scalar(
            select(DataNormalizedRecord).where(
                DataNormalizedRecord.entity_id == row.entity_id,
                DataNormalizedRecord.disposition == "ACCEPTED",
            )
        )
    item = _quarantine_item(row)
    return RecordQuarantineDetailResponse(
        **item.model_dump(),
        normalized_record=json.loads(row.normalized_record_json),
        current_accepted_record_id=accepted.id if accepted is not None else None,
        current_accepted_record=(
            json.loads(accepted.normalized_record_json) if accepted is not None else None
        ),
    )


def _recompute_entity_state(session: Session, entity: DataRecordEntity) -> None:
    unresolved = session.scalar(
        select(DataNormalizedRecord.id)
        .where(
            DataNormalizedRecord.entity_id == entity.id,
            DataNormalizedRecord.disposition == "QUARANTINED",
        )
        .limit(1)
    )
    accepted = session.scalar(
        select(DataNormalizedRecord.id)
        .where(
            DataNormalizedRecord.entity_id == entity.id,
            DataNormalizedRecord.disposition == "ACCEPTED",
        )
        .limit(1)
    )
    entity.state = "QUARANTINED" if unresolved is not None else "ACTIVE" if accepted is not None else "EMPTY"


def _resolution_response(row: DataRecordResolution) -> RecordResolutionResponse:
    return RecordResolutionResponse(
        id=row.id,
        source_id=row.source_id,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        product_code=row.product_code,
        entity_id=row.entity_id,
        quarantined_record_id=row.quarantined_record_id,
        existing_accepted_record_id=row.existing_accepted_record_id,
        decision=row.decision,
        resolution_reference=row.resolution_reference,
        reason=row.reason,
        resolved_by_membership_id=row.resolved_by_membership_id,
        resolved_at=_aware_timestamp(row.resolved_at),
    )


def resolve_quarantined_record(
    session: Session,
    *,
    source_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: RecordResolutionCreate,
    actor_id: uuid.UUID | None,
) -> RecordResolutionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    incoming = session.scalar(
        select(DataNormalizedRecord)
        .where(
            DataNormalizedRecord.id == record_id,
            DataNormalizedRecord.source_id == source.id,
            DataNormalizedRecord.organization_id == source.organization_id,
            DataNormalizedRecord.workspace_id == source.workspace_id,
            DataNormalizedRecord.product_code == source.product_code,
        )
        .with_for_update()
    )
    if incoming is None:
        raise DataPlatformError("record_quarantine_not_accessible")
    if incoming.disposition != "QUARANTINED":
        raise DataPlatformError("record_resolution_state_conflict")
    if incoming.entity_id is None:
        raise DataPlatformError("record_resolution_integrity_failed")
    existing_resolution = session.scalar(
        select(DataRecordResolution.id).where(
            DataRecordResolution.quarantined_record_id == incoming.id
        )
    )
    if existing_resolution is not None:
        raise DataPlatformError("record_resolution_state_conflict")
    entity = session.scalar(
        select(DataRecordEntity)
        .where(
            DataRecordEntity.id == incoming.entity_id,
            DataRecordEntity.source_id == source.id,
            DataRecordEntity.organization_id == source.organization_id,
            DataRecordEntity.workspace_id == source.workspace_id,
            DataRecordEntity.product_code == source.product_code,
        )
        .with_for_update()
    )
    if entity is None:
        raise DataPlatformError("record_resolution_integrity_failed")
    accepted = session.scalar(
        select(DataNormalizedRecord)
        .where(
            DataNormalizedRecord.entity_id == entity.id,
            DataNormalizedRecord.disposition == "ACCEPTED",
        )
        .with_for_update()
    )
    original_quarantine_reason = incoming.quarantine_reason
    if payload.decision == "ACCEPT_INCOMING":
        if incoming.quarantine_reason not in _ACCEPTABLE_RECONCILIATION_REASONS:
            raise DataPlatformError("record_resolution_accept_forbidden")
        if accepted is not None:
            accepted.disposition = "SUPERSEDED"
            session.flush()
        incoming.disposition = "ACCEPTED"
        incoming.quarantine_reason = None
        incoming.conflict_with_record_id = None
        incoming.duplicate_of_record_id = None
        session.flush()
        _recompute_entity_state(session, entity)
    else:
        incoming.disposition = "REJECTED"
        session.flush()
        _recompute_entity_state(session, entity)
    resolution = DataRecordResolution(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        entity_id=entity.id,
        quarantined_record_id=incoming.id,
        existing_accepted_record_id=accepted.id if accepted is not None else None,
        decision=payload.decision,
        resolution_reference=payload.resolution_reference.strip(),
        reason=payload.reason.strip() if payload.reason is not None else None,
        resolved_by_membership_id=actor_id,
        resolved_at=_utcnow(),
    )
    session.add(resolution)
    session.flush()
    session.add(
        DataAuditEvent(
            organization_id=source.organization_id,
            workspace_id=source.workspace_id,
            product_code=source.product_code,
            actor_membership_id=actor_id,
            event_type="data.record_quarantine.resolved",
            entity_type="data_record_resolution",
            entity_id=resolution.id,
            detail=(
                f"quarantined_record_id={incoming.id}; entity_id={entity.id}; "
                f"existing_accepted_record_id={resolution.existing_accepted_record_id}; "
                f"decision={resolution.decision}; reason_code={original_quarantine_reason or 'UNSPECIFIED'}"
            ),
        )
    )
    return _resolution_response(resolution)


def _record_tombstone(record_id: uuid.UUID, kind: str) -> str:
    return hashlib.sha256(f"record:{record_id}:{kind}:PURGED:v1".encode("utf-8")).hexdigest()


def _entity_tombstone(entity_id: uuid.UUID) -> str:
    return hashlib.sha256(f"entity:{entity_id}:identity:PURGED:v1".encode("utf-8")).hexdigest()


def purge_source_version_records(
    session: Session,
    *,
    source_version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
) -> int:
    rows = session.scalars(
        select(DataNormalizedRecord)
        .where(
            DataNormalizedRecord.source_version_id == source_version_id,
            DataNormalizedRecord.organization_id == organization_id,
            DataNormalizedRecord.workspace_id == workspace_id,
            DataNormalizedRecord.product_code == product_code,
        )
        .order_by(DataNormalizedRecord.created_at, DataNormalizedRecord.id)
        .with_for_update()
    ).all()
    if not rows:
        session.add(
            DataAuditEvent(
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_code=product_code,
                actor_membership_id=actor_id,
                event_type="data.record_content.purged",
                entity_type="data_source_version",
                entity_id=source_version_id,
                detail="normalized_record_count=0; affected_entity_count=0",
            )
        )
        return 0
    entity_ids = {row.entity_id for row in rows if row.entity_id is not None}
    entities = {
        entity.id: entity
        for entity in session.scalars(
            select(DataRecordEntity)
            .where(DataRecordEntity.id.in_(entity_ids))
            .with_for_update()
        ).all()
    }
    purged_ids = {row.id for row in rows}
    affected_accepted: dict[uuid.UUID, DataNormalizedRecord] = {
        row.entity_id: row
        for row in rows
        if row.entity_id is not None and row.disposition == "ACCEPTED"
    }
    promotions: dict[uuid.UUID, DataNormalizedRecord] = {}
    for entity_id, accepted in affected_accepted.items():
        replacement = session.scalar(
            select(DataNormalizedRecord)
            .where(
                DataNormalizedRecord.entity_id == entity_id,
                DataNormalizedRecord.id.notin_(purged_ids),
                DataNormalizedRecord.disposition == "DUPLICATE",
                DataNormalizedRecord.content_fingerprint == accepted.content_fingerprint,
            )
            .order_by(DataNormalizedRecord.created_at, DataNormalizedRecord.id)
            .limit(1)
            .with_for_update()
        )
        if replacement is not None:
            promotions[entity_id] = replacement
    for row in rows:
        row.normalized_record_json = "{}"
        row.identity_fingerprint = _record_tombstone(row.id, "identity")
        row.content_fingerprint = _record_tombstone(row.id, "content")
        row.disposition = "PURGED"
        row.quarantine_reason = None
        row.duplicate_of_record_id = None
        row.conflict_with_record_id = None
    session.flush()
    for replacement in promotions.values():
        replacement.disposition = "ACCEPTED"
        replacement.duplicate_of_record_id = None
    session.flush()
    for entity_id in entity_ids:
        replacement = promotions.get(entity_id)
        non_purged = session.scalars(
            select(DataNormalizedRecord)
            .where(
                DataNormalizedRecord.entity_id == entity_id,
                DataNormalizedRecord.disposition != "PURGED",
            )
            .order_by(DataNormalizedRecord.created_at, DataNormalizedRecord.id)
            .with_for_update()
        ).all()
        if replacement is not None:
            for candidate in non_purged:
                if candidate.disposition == "DUPLICATE":
                    candidate.duplicate_of_record_id = replacement.id
                if candidate.conflict_with_record_id in purged_ids:
                    candidate.conflict_with_record_id = replacement.id
        else:
            for candidate in non_purged:
                if candidate.duplicate_of_record_id in purged_ids:
                    candidate.duplicate_of_record_id = None
                if candidate.conflict_with_record_id in purged_ids:
                    candidate.conflict_with_record_id = None
        entity = entities.get(entity_id)
        if entity is None:
            raise DataPlatformError("record_purge_integrity_failed")
        _recompute_entity_state(session, entity)
        if not non_purged:
            entity.identity_fingerprint = _entity_tombstone(entity.id)
            entity.state = "EMPTY"
    session.flush()
    session.add(
        DataAuditEvent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            product_code=product_code,
            actor_membership_id=actor_id,
            event_type="data.record_content.purged",
            entity_type="data_source_version",
            entity_id=source_version_id,
            detail=f"normalized_record_count={len(rows)}; affected_entity_count={len(entity_ids)}",
        )
    )
    return len(rows)
