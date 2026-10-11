from uuid import uuid4
import pytest
from sqlalchemy import select
from test_isi_29b_spatial_api import api as scoped_api, params
from src.platform.access.models import Role, RoleAssignment
from src.domains.simpa import attribution_service
from src.streamlit_app import simpa_analytics_api
from src.streamlit_app.attribution_view import checked, matrix_rows, heatmap, waterfall
from src.domains.simpa.statistical_attribution import explain
from test_isi_29d_attribution_engine import case, FIELDS

api = scoped_api


def artifact():
    c, r, d = case()
    return explain(c, d, r, FIELDS, unit="synthetic units")


def test_render_matrix_waterfall_global_and_safe_labels():
    a = artifact()
    a["features"][0] = "<script>alert(1)</script>"
    rows = matrix_rows(a)
    assert len(rows) == 8 and rows[0]["SHAP · " + a["features"][0]] == a["matrix"][0][0]
    heat = heatmap(a)
    water = waterfall(a, 0)
    assert "<script>" not in heat.svg + water.svg and "&lt;script&gt;" in heat.svg + water.svg
    assert [x["SHAP"] for x in water.rows] == a["matrix"][0]
    assert water.rows[-1]["do"] == pytest.approx(a["samples"][0]["prediction"])
    assert "baseline=" in heat.svg and "input=" in water.svg


@pytest.mark.parametrize("kind", ["matrix", "global", "schema", "sample", "background", "error", "feature_type"])
def test_invalid_read_model_never_plots(kind):
    a = artifact()
    if kind == "matrix":
        a["matrix"][0][0] += 1
    elif kind == "global":
        a["global_mean_absolute"][0] += 1
    elif kind == "schema":
        a["schema"] = "unsupported"
    elif kind == "sample":
        a["samples"][0]["sample"] = 99
    elif kind == "background":
        a["background_means"][0] += 1
    elif kind == "error":
        a["samples"][0]["additivity_error"] = -1
    elif kind == "feature_type":
        a["features"][0] = 7
    with pytest.raises(ValueError):
        checked(a)


def test_api_scope_and_permission_before_service(api, monkeypatch):
    client, c, factory = api
    calls = []
    monkeypatch.setattr(attribution_service, "read", lambda *a, **kw: calls.append(kw) or {"status": "NOT_CREATED"})
    monkeypatch.setattr(attribution_service, "create", lambda *a, **kw: calls.append(kw) or {"status": "AVAILABLE"})
    url = "/api/v1/simpa/analytics/statistical-model-results/" + str(uuid4()) + "/attribution"
    assert client.get(url, params=params(c)).status_code == 200
    assert calls[-1]["organization_id"] == c["org"].id
    assert client.get(url, params=params(c, "ORDO")).status_code == 403
    calls.clear()
    with factory() as db:
        assignment = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == c["member"].id))
        viewer = db.scalar(select(Role).where(Role.code == "viewer"))
        assignment.role_id = viewer.id
        db.commit()
    assert client.post(url, params=params(c)).status_code == 403 and not calls
    assert client.get(url, params=params(c)).status_code == 200


def test_transport_forwards_scope_and_safe_unavailable(monkeypatch):
    captured = []

    class Response:
        status_code = 409

        def json(self):
            return {"detail": "sensitive source payload should not echo"}

    monkeypatch.setattr(simpa_analytics_api, "request", lambda *a, **kw: captured.append((a, kw)) or Response())
    r = simpa_analytics_api.attribution("synthetic-test-token", "org", "workspace", "result", create=True)
    assert r["status"] == "UNAVAILABLE" and "sensitive" not in str(r)
    assert captured[0][0][0] == "POST" and captured[0][1]["params"] == {
        "organization_id": "org",
        "workspace_id": "workspace",
    }


def test_help_ten_items_and_truthful_ordo_limit():
    from pathlib import Path

    guide = Path("docs/help/ISI-SHAP-GUIDE.md").read_text()
    for i in range(1, 11):
        assert f"## {i}. " in guide
    for text in ["OLS", "ORDO", "background", "analysis.read", "analysis.run", "1e-8", "non-causal", "LLM"]:
        assert text in guide


def test_streamlit_viewer_explicit_load_and_selected_waterfall_without_creation():
    from streamlit.testing.v1 import AppTest

    code = """
import streamlit as st
from types import SimpleNamespace
from src.streamlit_app.attribution_view import render_attribution
from src.domains.simpa.statistical_attribution import explain
from test_isi_29d_attribution_engine import case,FIELDS
c,r,d=case()
a=explain(c,d,r,FIELDS,unit="synthetic units")
a["provenance"]={"product":"SIMPA","result_id":"synthetic-result"}
def read(*args,**kwargs):
    assert not kwargs["create"]
    return {"status":"AVAILABLE","artifact":a,"fingerprint":"a"*64}
render_attribution(st,token="synthetic",organization_id="synthetic-org",workspace_id="synthetic-workspace",
    result={"id":"synthetic-result","result_fingerprint":"b"*64,"production_eligible":True,"result_detail":d},
    permissions={"analysis.read"},api=SimpleNamespace(attribution=read))
"""
    at = AppTest.from_string(code).run(timeout=30)
    assert not at.exception and not at.button and not at.dataframe
    at.checkbox[0].check().run(timeout=30)
    assert not at.exception and len(at.dataframe) == 4
    assert not any("SHAP atribucija nije dostupna" in x.value for x in at.caption)
    assert any("SHAP objašnjava doprinos modelu" in x.value for x in at.caption)
    assert at.selectbox[0].value == 0
    at.selectbox[0].select(3).run(timeout=30)
    assert not at.exception and at.selectbox[0].value == 3
    at.checkbox[0].uncheck().run(timeout=30)
    assert not at.exception and not at.dataframe


def test_exact_zero_has_neutral_heatmap_and_waterfall_marker():
    from src.domains.simpa.statistical_models import run_statistical_model

    c, r, _ = case()
    for item, x in zip(r, [0, 1, 2, 3, 3.5, 4, 5, 9.5]):
        item["x"] = x
    d = run_statistical_model(c, r, FIELDS)
    a = explain(c, d, r, FIELDS, unit="synthetic units")
    assert a["matrix"][4][0] == 0
    assert 'fill="#d1d5db"' in heatmap(a).svg
    assert 'fill="#d1d5db"' in waterfall(a, 4).svg


def test_streamlit_create_preserves_loaded_sample_view_after_rerun():
    from streamlit.testing.v1 import AppTest

    code = """
import streamlit as st
from types import SimpleNamespace
from src.streamlit_app.attribution_view import render_attribution
from src.domains.simpa.statistical_attribution import explain
from test_isi_29d_attribution_engine import case,FIELDS
c,r,d=case()
a=explain(c,d,r,FIELDS,unit="synthetic units")
a["provenance"]={"product":"SIMPA","result_id":"synthetic-result"}
def read(*args,**kwargs):
    st.session_state["create_flag"]=kwargs["create"]
    return {"status":"AVAILABLE","artifact":a,"fingerprint":"a"*64}
render_attribution(st,token="synthetic",organization_id="synthetic-org",workspace_id="synthetic-workspace",
    result={"id":"synthetic-result","result_fingerprint":"b"*64,"production_eligible":True,"result_detail":d},
    permissions={"analysis.read","analysis.run"},api=SimpleNamespace(attribution=read))
"""
    at = AppTest.from_string(code).run(timeout=30)
    assert not at.exception and len(at.button) == 1
    at.button[0].click().run(timeout=30)
    assert not at.exception and at.checkbox[0].value and at.session_state["create_flag"]
    at.selectbox[0].select(3).run(timeout=30)
    assert not at.exception and at.selectbox[0].value == 3 and not at.session_state["create_flag"]
