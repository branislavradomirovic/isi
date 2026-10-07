"""SIMPA aggregate/facility identity authority; no citizen geolocation."""

from sqlalchemy import select
from src.domains.simpa.models import SimpaLocalActor, SimpaLocalSystemProfile
from src.platform.spatial.contracts import GeometryError


def binding(session, *, organization_id, workspace_id, domain_kind, domain_id, geometry_type, valid_from, valid_to):
    models = {"local_system": SimpaLocalSystemProfile, "local_actor": SimpaLocalActor}
    model = models.get(domain_kind)
    if (
        model is None
        or (domain_kind == "local_system" and geometry_type == "Point")
        or (domain_kind == "local_actor" and geometry_type != "Point")
    ):
        raise GeometryError("simpa_geometry_domain_invalid")
    row = session.scalar(
        select(model).where(
            model.id == domain_id, model.organization_id == organization_id, model.workspace_id == workspace_id
        )
    )
    if row is None or (domain_kind == "local_actor" and not row.active):
        raise GeometryError("geometry_domain_not_accessible")
    code = row.jurisdiction_code if domain_kind == "local_system" else row.external_code
    if not code:
        raise GeometryError("geometry_domain_code_required")
    return {"kind": domain_kind, "id": str(row.id), "key": code}
