"""ORDO boundary/asset identity authority; preserves legacy identity-only rows."""

from sqlalchemy import select
from src.domains.ordo.models import OrdoAsset, OrdoSpatialUnit
from src.platform.spatial.contracts import GeometryError


def binding(session, *, organization_id, workspace_id, domain_kind, domain_id, geometry_type, valid_from, valid_to):
    models = {"spatial_unit": OrdoSpatialUnit, "asset": OrdoAsset}
    model = models.get(domain_kind)
    if (
        model is None
        or (domain_kind == "spatial_unit" and geometry_type == "Point")
        or (domain_kind == "asset" and geometry_type != "Point")
    ):
        raise GeometryError("ordo_geometry_domain_invalid")
    row = session.scalar(
        select(model).where(
            model.id == domain_id, model.organization_id == organization_id, model.workspace_id == workspace_id
        )
    )
    if row is None:
        raise GeometryError("geometry_domain_not_accessible")
    if domain_kind == "spatial_unit":
        if row.lifecycle_status != "validated" or not row.boundary_source or not row.boundary_version:
            raise GeometryError("geometry_domain_not_validated")
        if (row.valid_from is not None and valid_from < row.valid_from) or (
            row.valid_to is not None and (valid_to is None or valid_to > row.valid_to)
        ):
            raise GeometryError("geometry_domain_validity_mismatch")
        return {
            "kind": domain_kind,
            "id": str(row.id),
            "key": row.spatial_unit_key,
            "boundary_version": row.boundary_version,
            "boundary_source": row.boundary_source,
        }
    if not row.external_code:
        raise GeometryError("geometry_domain_code_required")
    return {"kind": domain_kind, "id": str(row.id), "key": row.external_code}
