from datetime import date
import pytest
from pydantic import ValidationError
from src.domains.ordo.models import OrdoSpatialUnit
from src.domains.ordo.schemas import SpatialUnitCreateRequest


def test_spatial_unit_has_versioned_boundary_identity_contract() -> None:
    cols = OrdoSpatialUnit.__table__.columns
    for name in ["spatial_unit_key", "spatial_unit_type", "boundary_source", "boundary_version", "geometry_id", "crs", "artifact_sha256", "valid_from", "valid_to", "provenance", "lifecycle_status"]:
        assert name in cols


def test_spatial_unit_validity_rejects_reversed_window() -> None:
    with pytest.raises(ValidationError):
        SpatialUnitCreateRequest(organization_id="00000000-0000-0000-0000-000000000001", workspace_id="00000000-0000-0000-0000-000000000002", spatial_unit_key="rs-1", spatial_unit_type="region", name="R", valid_from=date(2026, 2, 2), valid_to=date(2026, 1, 1))
