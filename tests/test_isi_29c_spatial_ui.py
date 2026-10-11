from pathlib import Path
from datetime import date
import httpx
import pytest
from streamlit.testing.v1 import AppTest
from src.streamlit_app import spatial_api
from src.streamlit_app.api_client import AccessDenied, AuthenticationRequired, ApiUnavailable
from test_isi_29c_spatial_view import detail


def test_transport_scope_and_no_raw_error_echo(monkeypatch):
    seen = []

    def req(*a, **k):
        seen.append((a, k))
        return httpx.Response(200, json=[])

    monkeypatch.setattr(spatial_api, "request", req)
    assert spatial_api.call("", "SIMPA", "list", organization_id="org", workspace_id="workspace") == []
    assert seen[0][1]["params"] == {"organization_id": "org", "workspace_id": "workspace"}
    for code, error in [
        (401, AuthenticationRequired),
        (403, AccessDenied),
        (400, AccessDenied),
        (422, AccessDenied),
        (500, ApiUnavailable),
    ]:
        monkeypatch.setattr(
            spatial_api, "request", lambda *a, **k: httpx.Response(code, json={"detail": "MUST_NOT_ECHO_SOURCE"})
        )
        with pytest.raises(error) as exc:
            spatial_api.call("", "SIMPA", "list", organization_id="org", workspace_id="workspace")
        assert "MUST_NOT" not in str(exc.value)


def app_code(permissions):
    shell = {
        "organization": {"id": "synthetic-org"},
        "workspace": {"id": "synthetic-workspace"},
        "product": {"code": "SIMPA", "permission_codes": permissions},
    }
    return (
        'from src.streamlit_app.spatial_workspace import render_spatial_workspace\nrender_spatial_workspace(token="",shell='
        + repr(shell)
        + ")"
    )


def mock_api(monkeypatch, empty=False):
    first = detail("synthetic-a")
    second = detail("synthetic-b", {"type": "Point", "coordinates": [20.5, 44.5]})
    for x, kind, key in [(first, "local_system", "Boundary"), (second, "local_actor", "Facility")]:
        x["metadata"]["domain_kind"] = kind
        x["metadata"]["domain_binding"]["key"] = key
    calls = []

    def call(token, product, action, **kwargs):
        calls.append((action, kwargs))
        if action == "list":
            return [] if empty else [first["metadata"], second["metadata"]]
        if action == "detail":
            return first if kwargs["geometry_id"] == "synthetic-a" else second
        if action == "targets":
            return [{"id": "synthetic-target", "kind": "local_system", "key": "SYNTHETIC", "name": "Synthetic"}]
        if action == "results":
            return {"results": [], "reason": "simpa_result_geography_binding_not_approved"}
        if action == "export":
            return {"type": "FeatureCollection", "features": []}
        raise AssertionError(action)

    monkeypatch.setattr(spatial_api, "call", call)
    return calls


def test_viewer_map_table_dropdown_selection_without_mutation_or_export(monkeypatch):
    calls = mock_api(monkeypatch)
    at = AppTest.from_string(app_code(["data.read", "analysis.read"])).run()
    assert not at.exception
    selector = next(x for x in at.selectbox if x.label.startswith("Izabrana teritorija"))
    selector.select("synthetic-b").run()
    assert not at.exception and len(at.dataframe) == 2
    provenance = at.dataframe[1].value.set_index("Polje")["Vrednost"]
    assert provenance["id"] == "synthetic-b" and provenance["domain_binding.key"] == "Facility"
    assert at.dataframe[0].value["id"].tolist() == ["synthetic-a", "synthetic-b"]
    assert all(a not in {"targets", "create", "review", "export"} for a, k in calls)
    assert calls[-1][1]["geometry_id"] == "synthetic-b"
    at.checkbox[0].uncheck().run()
    assert not at.exception and len(at.dataframe) == 2


def test_empty_source_has_no_fake_map(monkeypatch):
    mock_api(monkeypatch, empty=True)
    at = AppTest.from_string(app_code(["data.read"])).run()
    assert not at.exception and any("Nema potvrđene" in x.value for x in at.info)
    assert not at.get("deck_gl_json_chart")


def test_permissions_before_spatial_api(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("API must not be called")

    monkeypatch.setattr(spatial_api, "call", forbidden)
    assert not AppTest.from_string(app_code([])).run().exception


def test_data_route_and_ordo_permission_drift_fixed():
    data = Path("src/streamlit_app/data_workspace.py").read_text()
    ordo = Path("src/streamlit_app/ordo_workspace.py").read_text()
    assert "render_spatial_workspace(token=token, shell=shell)" in data
    assert 'set(shell.get("product", {}).get("permission_codes", []))' in ordo
    assert 'shell.get("permissions")' not in ordo
    assert "external_code=external_code" in ordo
    assert date.today().year >= 2026


def test_map_and_table_callbacks_use_distinct_widget_state(monkeypatch):
    from types import SimpleNamespace
    from src.streamlit_app import spatial_workspace as ui
    from src.streamlit_app.spatial_view import map_key

    details = [detail("a"), detail("b")]
    state, captured = {}, {}

    def selectbox(label, ids, **kwargs):
        state.setdefault(kwargs["key"], ids[0])

    def mount(**kwargs):
        captured["map"] = kwargs

    def dataframe(rows, **kwargs):
        captured["table"] = kwargs

    monkeypatch.setattr(
        ui,
        "st",
        SimpleNamespace(
            session_state=state,
            selectbox=selectbox,
            caption=lambda *a: None,
            table=lambda *a: None,
            checkbox=lambda *a, **k: True,
            dataframe=dataframe,
        ),
    )
    monkeypatch.setattr(ui, "map_component", lambda: mount)
    ui.render_map_table(details, scope=("org", "SIMPA", "workspace"), at_date="2026-01-01")
    prefix = map_key(("org", "SIMPA", "workspace"), "2026-01-01", details)
    state[captured["map"]["key"]] = {"picked": "b"}
    state[captured["table"]["key"]] = {"selection": {"rows": [0]}}
    captured["map"]["on_picked_change"]()
    assert state[prefix + "-selected"] == "b"
    captured["table"]["on_select"]()
    assert state[prefix + "-selected"] == "a"
    state[captured["map"]["key"]] = {"picked": "foreign-geometry"}
    captured["map"]["on_picked_change"]()
    assert state[prefix + "-selected"] == "a"
