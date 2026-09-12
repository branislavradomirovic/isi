from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.platform.data.models import DataAuditEvent, DataConnectorContractVersion, DataSource
from src.platform.data.schemas import ConnectorContractVersionCreate, ConnectorContractVersionResponse
from src.platform.data.service import DataPlatformError, get_scoped_source


_FORBIDDEN_SECRET_KEYS = {
    "password",
    "passwd",
    "secret",
    "clientsecret",
    "apikey",
    "accesskey",
    "privatekey",
    "token",
    "authtoken",
    "bearer",
    "credential",
    "credentials",
    "authorization",
    "proxyauthorization",
    "authtoken",
    "xauthtoken",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "oauthtoken",
    "bearertoken",
    "sessiontoken",
    "cookie",
    "sessioncookie",
}


_FORBIDDEN_SECRET_KEY_MARKERS = (
    "password",
    "passwd",
    "secret",
    "apikey",
    "accesskey",
    "privatekey",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_timestamp(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _normalized_secret_key(value: object) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


def _reject_secret_material(value: object) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = _normalized_secret_key(key)
            if normalized_key in _FORBIDDEN_SECRET_KEYS or any(
                marker in normalized_key for marker in _FORBIDDEN_SECRET_KEY_MARKERS
            ):
                raise DataPlatformError("connector_secret_material_forbidden")
            _reject_secret_material(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _reject_secret_material(nested_value)


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
        raise DataPlatformError("invalid_connector_configuration") from exc


def _normalize_identifier(value: str) -> str:
    return value.casefold()


def _normalize_credential_reference(value: str) -> str:
    reference = value.strip()
    if not reference:
        return ""
    prefix = "secretref://"
    if len(reference) > 500 or not reference.startswith(prefix):
        raise DataPlatformError("invalid_connector_credential_reference")
    opaque_reference = reference[len(prefix):]
    if (
        not opaque_reference
        or "?" in opaque_reference
        or "#" in opaque_reference
        or any(character.isspace() or not character.isprintable() for character in opaque_reference)
    ):
        raise DataPlatformError("invalid_connector_credential_reference")
    return reference


def _contract_fingerprint(
    *,
    source_id: uuid.UUID,
    connector_kind: str,
    transport: str,
    configuration: dict[str, Any],
    credential_reference: str,
    capabilities: list[str],
) -> str:
    payload = {
        "source_id": str(source_id),
        "connector_kind": connector_kind,
        "transport": transport,
        "configuration": configuration,
        "credential_reference": credential_reference,
        "capabilities": capabilities,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


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


def _connector_response(row: DataConnectorContractVersion) -> ConnectorContractVersionResponse:
    return ConnectorContractVersionResponse(
        id=row.id,
        source_id=row.source_id,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        product_code=row.product_code,
        version_no=row.version_no,
        connector_kind=row.connector_kind,
        transport=row.transport,
        configuration=json.loads(row.configuration_json),
        credential_reference=row.credential_reference,
        capabilities=json.loads(row.capabilities_json),
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
    row: DataConnectorContractVersion,
    actor_id: uuid.UUID | None,
    event_type: str,
    detail: str,
) -> None:
    session.add(
        DataAuditEvent(
            organization_id=row.organization_id,
            workspace_id=row.workspace_id,
            product_code=row.product_code,
            actor_membership_id=actor_id,
            event_type=event_type,
            entity_type="connector_contract_version",
            entity_id=row.id,
            detail=detail,
        )
    )


def create_connector_contract_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    payload: ConnectorContractVersionCreate,
    actor_id: uuid.UUID | None,
) -> ConnectorContractVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=payload.product_code,
    )
    _reject_secret_material(payload.configuration)
    connector_kind = _normalize_identifier(payload.connector_kind)
    transport = _normalize_identifier(payload.transport)
    credential_reference = _normalize_credential_reference(payload.credential_reference)
    capabilities = sorted({_normalize_identifier(item) for item in payload.capabilities})
    configuration_json = _canonical_json(payload.configuration)
    normalized_configuration = json.loads(configuration_json)
    capabilities_json = _canonical_json(capabilities)
    fingerprint = _contract_fingerprint(
        source_id=source.id,
        connector_kind=connector_kind,
        transport=transport,
        configuration=normalized_configuration,
        credential_reference=credential_reference,
        capabilities=capabilities,
    )
    latest = session.scalar(
        select(DataConnectorContractVersion)
        .where(DataConnectorContractVersion.source_id == source.id)
        .order_by(DataConnectorContractVersion.version_no.desc())
        .limit(1)
    )
    if latest is not None and latest.fingerprint == fingerprint:
        raise DataPlatformError("connector_contract_unchanged")
    next_version = (
        session.scalar(
            select(func.max(DataConnectorContractVersion.version_no)).where(
                DataConnectorContractVersion.source_id == source.id
            )
        )
        or 0
    ) + 1
    row = DataConnectorContractVersion(
        source_id=source.id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        product_code=source.product_code,
        version_no=next_version,
        connector_kind=connector_kind,
        transport=transport,
        configuration_json=configuration_json,
        credential_reference=credential_reference,
        capabilities_json=capabilities_json,
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
        event_type="data.connector_contract_version.created",
        detail=(
            f"version_no={row.version_no}; connector_kind={row.connector_kind}; "
            f"transport={row.transport}; fingerprint={row.fingerprint}; transition=CREATED_DRAFT"
        ),
    )
    return _connector_response(row)


def list_connector_contract_versions(
    session: Session,
    *,
    source_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
) -> list[ConnectorContractVersionResponse]:
    source = get_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    rows = session.scalars(
        select(DataConnectorContractVersion)
        .where(
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
        .order_by(DataConnectorContractVersion.version_no.desc(), DataConnectorContractVersion.id)
    ).all()
    return [_connector_response(row) for row in rows]


def activate_connector_contract_version(
    session: Session,
    *,
    source_id: uuid.UUID,
    version_id: uuid.UUID,
    organization_id: uuid.UUID,
    workspace_id: uuid.UUID,
    product_code: str,
    actor_id: uuid.UUID | None,
) -> ConnectorContractVersionResponse:
    source = _locked_scoped_source(
        session,
        source_id=source_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    row = session.scalar(
        select(DataConnectorContractVersion)
        .where(
            DataConnectorContractVersion.id == version_id,
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.organization_id == source.organization_id,
            DataConnectorContractVersion.workspace_id == source.workspace_id,
            DataConnectorContractVersion.product_code == source.product_code,
        )
        .with_for_update()
    )
    if row is None:
        raise DataPlatformError("connector_contract_version_not_accessible")
    if row.lifecycle_state == "ACTIVE":
        return _connector_response(row)
    if row.lifecycle_state != "DRAFT":
        raise DataPlatformError("connector_contract_state_conflict")

    now = _utcnow()
    active_rows = session.scalars(
        select(DataConnectorContractVersion)
        .where(
            DataConnectorContractVersion.source_id == source.id,
            DataConnectorContractVersion.lifecycle_state == "ACTIVE",
        )
        .order_by(DataConnectorContractVersion.version_no)
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
            event_type="data.connector_contract_version.retired",
            detail=(
                f"version_no={active.version_no}; fingerprint={active.fingerprint}; "
                f"transition=ACTIVE_TO_RETIRED; replacement_id={row.id}"
            ),
        )

    row.lifecycle_state = "ACTIVE"
    row.activated_by_membership_id = actor_id
    row.activated_at = now
    _audit(
        session,
        row=row,
        actor_id=actor_id,
        event_type="data.connector_contract_version.activated",
        detail=(
            f"version_no={row.version_no}; connector_kind={row.connector_kind}; "
            f"transport={row.transport}; fingerprint={row.fingerprint}; transition=DRAFT_TO_ACTIVE"
        ),
    )
    session.flush()
    return _connector_response(row)
