from __future__ import annotations
import hashlib
import json
import math
from datetime import date
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import shape
from shapely.errors import GEOSException

MAX_BYTES = 200000
MAX_COORDINATES = 10000


class GeometryError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError) as exc:
        raise GeometryError("geometry_payload_invalid") from exc


def validate_geometry(value: dict) -> bytes:
    payload = canonical_bytes(value)
    if len(payload) > MAX_BYTES:
        raise GeometryError("geometry_payload_too_large")
    if (
        not isinstance(value, dict)
        or set(value) != {"type", "coordinates"}
        or not isinstance(value["type"], str)
        or value["type"] not in {"Point", "Polygon", "MultiPolygon"}
    ):
        raise GeometryError("geometry_type_invalid")
    count = 0

    def point(v: Any) -> None:
        nonlocal count
        count += 1
        if count > MAX_COORDINATES:
            raise GeometryError("geometry_coordinate_limit")
        if not isinstance(v, list) or len(v) != 2:
            raise GeometryError("geometry_2d_required")
        try:
            invalid = any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v)
        except OverflowError:
            invalid = True
        if invalid:
            raise GeometryError("geometry_coordinate_invalid")
        if not (-180 <= v[0] <= 180 and -90 <= v[1] <= 90):
            raise GeometryError("geometry_coordinate_range")

    def polygon(v: Any) -> None:
        if not isinstance(v, list) or not v:
            raise GeometryError("geometry_polygon_invalid")
        for ring in v:
            if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
                raise GeometryError("geometry_ring_invalid")
            for coordinate in ring:
                point(coordinate)
            if any(abs(a[0] - b[0]) > 180 for a, b in zip(ring, ring[1:])):
                raise GeometryError("geometry_antimeridian_split_required")

    coordinates = value["coordinates"]
    if value["type"] == "Point":
        point(coordinates)
    elif value["type"] == "Polygon":
        polygon(coordinates)
    else:
        if not isinstance(coordinates, list) or not coordinates:
            raise GeometryError("geometry_multipolygon_invalid")
        for part in coordinates:
            polygon(part)
    try:
        geom = shape(value)
        if geom.is_empty or not geom.is_valid:
            raise GeometryError("geometry_topology_invalid")
    except (ValueError, TypeError, IndexError, GEOSException) as exc:
        raise GeometryError("geometry_topology_invalid") from exc
    return payload


class GeometryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    organization_id: UUID
    workspace_id: UUID
    domain_kind: Literal["local_system", "local_actor", "spatial_unit", "asset"]
    domain_id: UUID
    version: str = Field(min_length=1, max_length=120)
    source_uri: str = Field(min_length=1, max_length=500)
    source_version: str = Field(min_length=1, max_length=120)
    declared_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    license_identifier: str = Field(min_length=1, max_length=120)
    original_crs: Literal["OGC:CRS84", "EPSG:4326"]
    axis_order: Literal["longitude_latitude"]
    valid_from: date
    valid_to: date | None = None
    geometry: dict

    @model_validator(mode="after")
    def validate_contract(self):
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("geometry_validity_reversed")
        source = urlsplit(self.source_uri)
        if (
            source.scheme != "https"
            or not source.hostname
            or source.username
            or source.password
            or source.query
            or source.fragment
        ):
            raise ValueError("geometry_source_uri_invalid")
        validate_geometry(self.geometry)
        return self


class GeometryReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    state: Literal["PROPOSED", "VALIDATED", "RETIRED"]
    source_license_location_attested: bool = False


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
