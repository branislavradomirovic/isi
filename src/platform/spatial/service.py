from __future__ import annotations
import json
from datetime import date, datetime, timezone
from uuid import UUID
from sqlalchemy import select
from src.platform.access.service import has_permission
from src.platform.app_context.service import resolve_selection, AppContextError
from src.platform.data.models import DataAuditEvent
from src.platform.data.service import actor_membership_id
from src.platform.data.storage import build_storage, scoped_storage_key
from src.platform.spatial.contracts import (
    GeometryCreate,
    GeometryReview,
    GeometryError,
    canonical_bytes,
    digest,
    validate_geometry,
)
from src.platform.spatial.models import SpatialGeometryVersion


class GeometryAccessError(GeometryError):
    pass


class GeometryConflict(GeometryError):
    pass


def authorize(db, *, user_id, organization_id, workspace_id, product_code, permission):
    try:
        resolve_selection(
            db, user_id=user_id, organization_id=organization_id, workspace_id=workspace_id, product_code=product_code
        )
    except AppContextError:
        raise GeometryAccessError("geometry_scope_not_accessible") from None
    if not has_permission(db, user_id, organization_id, permission, product_code):
        raise GeometryAccessError("geometry_permission_denied")
    actor = actor_membership_id(db, user_id=user_id, organization_id=organization_id)
    if actor is None:
        raise GeometryAccessError("geometry_actor_not_accessible")
    return actor


def domain_binding(db, row):
    if row.product_code == "SIMPA":
        from src.domains.simpa.spatial_adapter import binding
    elif row.product_code == "ORDO":
        from src.domains.ordo.spatial_adapter import binding
    else:
        raise GeometryError("geometry_product_invalid")
    return binding(
        db,
        organization_id=row.organization_id,
        workspace_id=row.workspace_id,
        domain_kind=row.domain_kind,
        domain_id=row.domain_id,
        geometry_type=row.geometry_type,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
    )


def immutable_metadata(row):
    names = (
        "organization_id",
        "workspace_id",
        "product_code",
        "domain_kind",
        "domain_id",
        "version",
        "source_uri",
        "source_version",
        "declared_source_sha256",
        "license_identifier",
        "original_crs",
        "axis_order",
        "render_crs",
        "transformation",
        "valid_from",
        "valid_to",
        "geometry_type",
        "geometry_sha256",
        "domain_binding",
    )
    return {
        name: (str(value) if isinstance(value, (UUID, date)) else value)
        for name in names
        if (value := getattr(row, name)) is not None
    }


def fingerprint(row):
    return digest(canonical_bytes(immutable_metadata(row)))


def metadata(row):
    return {
        "id": str(row.id),
        **immutable_metadata(row),
        "fingerprint": row.fingerprint,
        "state": row.state,
        "revision": row.revision,
        "reviewed_by_membership_id": str(row.reviewed_by_membership_id) if row.reviewed_by_membership_id else None,
        "reviewed_at": row.reviewed_at,
        "schema_version": "ISI-SPATIAL-GEOMETRY-v1",
        "source_verification": "HUMAN_ATTESTED"
        if row.reviewed_by_membership_id and row.state == "VALIDATED"
        else "DECLARED_NOT_INDEPENDENTLY_VERIFIED",
    }


def key(row):
    return scoped_storage_key(
        organization_id=str(row.organization_id),
        workspace_id=str(row.workspace_id),
        product_code=row.product_code,
        sha256=row.geometry_sha256,
        extension="geojson",
    )


def verify(db, row, storage):
    if row.fingerprint != fingerprint(row) or row.storage_key != key(row):
        raise GeometryError("geometry_metadata_integrity_failed")
    if domain_binding(db, row) != row.domain_binding:
        raise GeometryError("geometry_domain_binding_changed")
    payload = storage.get_bytes(row.storage_key)
    if digest(payload) != row.geometry_sha256:
        raise GeometryError("geometry_storage_integrity_failed")
    geometry = json.loads(payload)
    if validate_geometry(geometry) != payload or geometry["type"] != row.geometry_type:
        raise GeometryError("geometry_payload_integrity_failed")
    return geometry


def audit(db, row, actor, event):
    db.add(
        DataAuditEvent(
            organization_id=row.organization_id,
            workspace_id=row.workspace_id,
            product_code=row.product_code,
            actor_membership_id=actor,
            event_type=event,
            entity_type="spatial_geometry_version",
            entity_id=row.id,
            detail=json.dumps({"fingerprint": row.fingerprint, "state": row.state, "revision": row.revision}),
        )
    )


def create_geometry(db, *, user_id, product_code, payload: GeometryCreate, storage=None):
    actor = authorize(
        db,
        user_id=user_id,
        organization_id=payload.organization_id,
        workspace_id=payload.workspace_id,
        product_code=product_code,
        permission="data.upload",
    )
    data = validate_geometry(payload.geometry)
    row = SpatialGeometryVersion(
        **payload.model_dump(exclude={"geometry"}),
        product_code=product_code,
        geometry_type=payload.geometry["type"],
        geometry_sha256=digest(data),
        render_crs="OGC:CRS84",
        transformation="IDENTITY_WGS84_LON_LAT",
        state="DRAFT",
        revision=1,
        created_by_membership_id=actor,
    )
    row.domain_binding = domain_binding(db, row)
    if row.domain_kind == "spatial_unit" and (
        row.source_uri != row.domain_binding["boundary_source"]
        or row.source_version != row.domain_binding["boundary_version"]
    ):
        raise GeometryError("geometry_boundary_provenance_mismatch")
    row.storage_key = key(row)
    row.fingerprint = fingerprint(row)
    db.add(row)
    db.flush()  # uniqueness before writing; caller commits or rolls back
    (storage or build_storage()).put_bytes(row.storage_key, data)
    audit(db, row, actor, "spatial.geometry.created")
    return row


def scoped_row(db, *, geometry_id, organization_id, workspace_id, product_code):
    row = db.scalar(
        select(SpatialGeometryVersion).where(
            SpatialGeometryVersion.id == geometry_id,
            SpatialGeometryVersion.organization_id == organization_id,
            SpatialGeometryVersion.workspace_id == workspace_id,
            SpatialGeometryVersion.product_code == product_code,
        )
    )
    if row is None:
        raise GeometryAccessError("geometry_not_accessible")
    return row


def list_geometry(db, *, user_id, organization_id, workspace_id, product_code, limit=100):
    authorize(
        db,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission="data.read",
    )
    return db.scalars(
        select(SpatialGeometryVersion)
        .where(
            SpatialGeometryVersion.organization_id == organization_id,
            SpatialGeometryVersion.workspace_id == workspace_id,
            SpatialGeometryVersion.product_code == product_code,
        )
        .order_by(SpatialGeometryVersion.created_at.desc(), SpatialGeometryVersion.id)
        .limit(max(1, min(limit, 100)))
    ).all()


def review_geometry(
    db, *, user_id, organization_id, workspace_id, product_code, geometry_id, payload: GeometryReview, storage=None
):
    permission = "data.validate" if payload.state == "VALIDATED" else "data.governance.manage"
    actor = authorize(
        db,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission=permission,
    )
    row = scoped_row(
        db,
        geometry_id=geometry_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    if row.revision != payload.revision:
        raise GeometryConflict("geometry_revision_conflict")
    transitions = {
        "DRAFT": {"PROPOSED", "RETIRED"},
        "PROPOSED": {"VALIDATED", "RETIRED"},
        "VALIDATED": {"RETIRED"},
        "RETIRED": set(),
    }
    if payload.state not in transitions[row.state]:
        raise GeometryError("geometry_transition_invalid")
    if payload.state == "VALIDATED" and not payload.source_license_location_attested:
        raise GeometryError("geometry_review_attestation_required")
    # Retirement remains available if underlying source/domain/storage became invalid.
    if payload.state != "RETIRED":
        verify(db, row, storage or build_storage())
    row.state = payload.state
    row.reviewed_by_membership_id = actor
    row.reviewed_at = datetime.now(timezone.utc)
    db.flush()  # SQLAlchemy version column rejects concurrent stale writes
    audit(db, row, actor, "spatial.geometry." + payload.state.lower())
    return row


def get_geometry(db, *, user_id, organization_id, workspace_id, product_code, geometry_id, at_date, storage=None):
    authorize(
        db,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission="data.read",
    )
    row = scoped_row(
        db,
        geometry_id=geometry_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    if row.state != "VALIDATED" or row.reviewed_by_membership_id is None:
        raise GeometryError("geometry_not_validated")
    if at_date < row.valid_from or (row.valid_to and at_date > row.valid_to):
        raise GeometryError("geometry_not_valid_at_date")
    geometry = verify(db, row, storage or build_storage())
    return {"metadata": metadata(row), "geometry": geometry}


def export_geometry(db, *, user_id, organization_id, workspace_id, product_code, geometry_id, at_date):
    actor = authorize(
        db,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        permission="data.export",
    )
    result = get_geometry(
        db,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
        geometry_id=geometry_id,
        at_date=at_date,
    )
    row = result["metadata"]
    persisted = scoped_row(
        db,
        geometry_id=geometry_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_code=product_code,
    )
    audit(db, persisted, actor, "spatial.geometry.exported")
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": result["geometry"],
                "properties": {
                    name: row.get(name)
                    for name in (
                        "product_code",
                        "domain_kind",
                        "domain_id",
                        "version",
                        "source_uri",
                        "source_version",
                        "license_identifier",
                        "valid_from",
                        "valid_to",
                        "geometry_sha256",
                        "fingerprint",
                        "render_crs",
                        "source_verification",
                    )
                },
            }
        ],
        "geometry_at_date": at_date.isoformat(),
        "observation_period": "NOT_ASSIGNED",
    }
