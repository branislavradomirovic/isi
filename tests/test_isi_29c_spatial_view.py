import json
from copy import deepcopy
import pytest
from src.streamlit_app.spatial_view import collection, build_map, map_key, selection_id, MAX_FEATURES
from src.platform.spatial.contracts import GeometryError


def detail(gid="synthetic-geometry", geometry=None):
    return {
        "metadata": {
            "id": gid,
            "state": "VALIDATED",
            "version": "v1",
            "revision": 3,
            "fingerprint": "a" * 64,
            "domain_binding": {"key": "Synthetic boundary"},
            "valid_from": "2026-01-01",
        },
        "geometry": geometry
        or {"type": "Polygon", "coordinates": [[[20, 44], [21, 44], [21, 45], [20, 45], [20, 44]]]},
    }


def test_vector_map_no_network_or_sensitive_metadata_or_credentials(monkeypatch):
    from src.streamlit_app.spatial_view import MAP_HTML, MAP_JS

    monkeypatch.setenv("MAPBOX_API_KEY", "synthetic-must-not-be-serialized")
    data = collection([detail()])
    rendered = build_map(data, "synthetic-geometry")
    assert rendered["projection"] == "WGS84_RENDER_MERCATOR" and rendered["source_geometry_unchanged"]
    assert rendered["features"][0]["selected"]
    assert "source_uri" not in json.dumps(rendered) and "synthetic-must" not in json.dumps(rendered)
    assert "http" not in MAP_HTML and "fetch(" not in MAP_JS and "innerHTML" not in MAP_JS
    assert "textContent=item.label" in MAP_JS and "setTriggerValue('picked',item.id)" in MAP_JS
    assert "fill-rule','evenodd" in MAP_JS


def test_features_exact_geometry_and_safe_properties():
    d = detail()
    d["metadata"]["domain_binding"]["key"] = "<img src=x onerror=alert(1)>"
    data = collection([d])
    assert data["features"][0]["geometry"] == d["geometry"]
    assert set(data["features"][0]["properties"]) == {"id", "label", "color"}
    rendered = build_map(data)
    assert rendered["features"][0]["label"].startswith("<img")  # text-only data, never component code
    assert rendered["features"][0]["paths"][0].startswith("M")


@pytest.mark.parametrize("mutation", ["duplicate", "draft", "invalid", "oversized"])
def test_fail_closed_view_contract(mutation):
    details = [detail()]
    if mutation == "duplicate":
        details.append(deepcopy(details[0]))
    if mutation == "draft":
        details[0]["metadata"]["state"] = "DRAFT"
    if mutation == "invalid":
        details[0]["geometry"] = {"type": "Point", "coordinates": [float("nan"), 44]}
    if mutation == "oversized":
        details = [detail(str(x)) for x in range(MAX_FEATURES + 1)]
    with pytest.raises(GeometryError):
        collection(details)


@pytest.mark.parametrize(
    "index,expected", [([0], "a"), ([1], "b"), ([-1], None), ([2], None), ([True], None), ([0, 1], None), (None, None)]
)
def test_selection_untrusted_indices(index, expected):
    assert selection_id(index, ["a", "b"]) == expected


def test_widget_identity_changes_scope_date_revision_fingerprint():
    details = [detail()]
    base = map_key(("org", "SIMPA", "workspace"), "2026-01-01", details)
    assert base != map_key(("org", "ORDO", "workspace"), "2026-01-01", details)
    assert base != map_key(("org", "SIMPA", "workspace"), "2026-01-02", details)
    details[0]["metadata"]["revision"] += 1
    assert base != map_key(("org", "SIMPA", "workspace"), "2026-01-01", details)


def test_polar_camera_table_fallback():
    with pytest.raises(GeometryError, match="projection"):
        build_map(collection([detail(geometry={"type": "Point", "coordinates": [20, 90]})]))


def test_multipolygon_holes_preserved_in_render_only_paths():
    geometry = {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [[20, 44], [22, 44], [22, 46], [20, 46], [20, 44]],
                [[20.5, 44.5], [20.5, 45], [21, 45], [21, 44.5], [20.5, 44.5]],
            ],
            [[[23, 44], [24, 44], [24, 45], [23, 45], [23, 44]]],
        ],
    }
    original = deepcopy(geometry)
    data = collection([detail(geometry=geometry)])
    paths = build_map(data)["features"][0]["paths"]
    assert len(paths) == 2 and paths[0].count("M") == 2 and paths[0].count("Z") == 2
    assert geometry == original
