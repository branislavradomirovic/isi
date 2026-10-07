from copy import deepcopy
from datetime import date
from uuid import uuid4
import pytest
from pydantic import ValidationError
from src.platform.spatial.contracts import GeometryCreate, GeometryError, canonical_bytes, validate_geometry

POLYGON = {"type": "Polygon", "coordinates": [[[20, 44], [21, 44], [21, 45], [20, 45], [20, 44]]]}


def request(**changes):
    args = dict(
        organization_id=uuid4(),
        workspace_id=uuid4(),
        domain_kind="local_system",
        domain_id=uuid4(),
        version="synthetic-v1",
        source_uri="https://example.org/synthetic",
        source_version="v1",
        declared_source_sha256="a" * 64,
        license_identifier="CC0-1.0 synthetic fixture only",
        original_crs="OGC:CRS84",
        axis_order="longitude_latitude",
        valid_from=date(2026, 1, 1),
        geometry=deepcopy(POLYGON),
    )
    return GeometryCreate(**(args | changes))


@pytest.mark.parametrize(
    "geometry",
    [
        POLYGON,
        {"type": "MultiPolygon", "coordinates": [POLYGON["coordinates"]]},
        {"type": "Point", "coordinates": [0, 0]},
    ],
)
def test_canonical_geometry_preserves_exact_source(geometry):
    original = deepcopy(geometry)
    assert validate_geometry(geometry) == canonical_bytes(geometry)
    assert geometry == original


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]},
        {"type": "Point", "coordinates": [float("nan"), 0]},
        {"type": "Point", "coordinates": [False, 0]},
        {"type": "Point", "coordinates": [0, 91]},
        {"type": "Point", "coordinates": [181, 0]},
        {"type": "Point", "coordinates": [0, 0, 1]},
        {"type": "GeometryCollection", "coordinates": []},
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1]]]},
        {"type": "Polygon", "coordinates": [[[170, 0], [-170, 0], [-170, 1], [170, 1], [170, 0]]]},
        {"type": "MultiPolygon", "coordinates": []},
        {"type": "Point", "coordinates": [0, 0], "script": "hostile"},
    ],
)
def test_invalid_geometry_fails_closed(geometry):
    with pytest.raises(GeometryError):
        validate_geometry(geometry)


@pytest.mark.parametrize(
    "changes",
    [
        {"original_crs": "UNKNOWN"},
        {"original_crs": "EPSG:3857"},
        {"axis_order": "latitude_longitude"},
        {"license_identifier": " "},
        {"source_uri": "https://user@example.org/source"},
        {"source_uri": "https://example.org/?token=private"},
        {"valid_to": date(2025, 1, 1)},
        {"declared_source_sha256": "bad"},
    ],
)
def test_bad_provenance_crs_validity_rejected(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_huge_geometry_and_coordinate_limits():
    with pytest.raises(GeometryError):
        validate_geometry({"type": "Polygon", "coordinates": [[[0, 0]] * 10001]})
    with pytest.raises(GeometryError):
        validate_geometry({"type": "Point", "coordinates": [0, 0], "padding": "x" * 200000})


def test_extreme_integer_fails_closed():
    with pytest.raises(GeometryError):
        validate_geometry({"type": "Point", "coordinates": [10**400, 0]})


def test_holes_outside_polygon_and_overlapping_multipolygons_rejected():
    hole = [[30, 50], [31, 50], [31, 51], [30, 51], [30, 50]]
    with pytest.raises(GeometryError):
        validate_geometry({"type": "Polygon", "coordinates": POLYGON["coordinates"] + [hole]})
    with pytest.raises(GeometryError):
        validate_geometry({"type": "MultiPolygon", "coordinates": [POLYGON["coordinates"], POLYGON["coordinates"]]})


def test_unhashable_geometry_type_rejected_as_validation_error():
    with pytest.raises(GeometryError):
        validate_geometry({"type": [], "coordinates": []})
    with pytest.raises(ValidationError):
        request(geometry={"type": {}, "coordinates": []})
