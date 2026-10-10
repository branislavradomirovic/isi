from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app.workflow_shell import clear_workspace_state, context_markup, navigation_items
from src.streamlit_app import ordo_analytics_api


def shell(product="ORDO", permissions=None):
    return {"organization": {"id": "org", "name": "Synthetic institute"},
            "workspace": {"id": "ws", "name": "Synthetic workspace"},
            "product": {"code": product, "permission_codes": permissions or []},
            "navigation": [{"code": "overview", "label_sr": "Pregled", "enabled": True},
                           {"code": "scenarios", "label_sr": "Scenariji", "enabled": True},
                           {"code": "reports", "label_sr": "Izveštaji", "enabled": False}]}


@pytest.mark.parametrize("product,permissions,visible", [
    ("SIMPA", ["analysis.read"], False), ("ORDO", [], False),
    ("ORDO", ["scenario.read"], False), ("ORDO", ["analysis.read"], True),
])
def test_navigation_preserves_backend_guards_and_product_boundary(product, permissions, visible):
    value = shell(product, permissions)
    codes = [row["code"] for row in navigation_items(value)]
    assert ("scenarios" in codes) is visible
    assert "reports" not in codes
    assert f"{product.lower()}_help" in codes
    assert len(value["navigation"]) == 3


def test_context_markup_escapes_untrusted_labels():
    value = shell()
    value["organization"]["name"] = '<img src=x onerror="bad()">'
    value["workspace"]["name"] = "A&B"
    text = context_markup(value, "overview")
    assert "<img" not in text and "&lt;img" in text and "A&amp;B" in text
    assert 'aria-label="Aktivni radni kontekst"' in text


def test_scope_transition_removes_every_payload_widget_and_navigation():
    state = {"isi_access_token": object(), "isi_app_context": {},
             "isi_org_selector": "new_org", "isi_workspace_selector": "new_ws",
             "isi_selected_product": "ORDO", "isi_shell_navigation": "reports",
             "ordo_goal_desc": "synthetic draft", "map_event": {"picked": "old"},
             "report_export": b"synthetic"}
    clear_workspace_state(state)
    assert set(state) == {"isi_access_token", "isi_app_context", "isi_org_selector",
                          "isi_workspace_selector", "isi_selected_product"}
    clear_workspace_state(state)


PREVIEW = '''
import streamlit as st
from src.streamlit_app.ordo_analytics_workspace import render_ordo_scenarios
from src.streamlit_app.style import apply_shell_css
apply_shell_css()
render_ordo_scenarios(token="synthetic-placeholder", shell=SHELL)
'''


def scenario_app(monkeypatch, permissions):
    from src.streamlit_app import ordo_analytics_workspace as ui
    monkeypatch.setattr(ui, "_eligible_artifacts", lambda *a: [])
    for name in ("runs", "goals", "scenarios", "assessments"):
        monkeypatch.setattr(ordo_analytics_api, name, lambda *a: [])
    return AppTest.from_string(PREVIEW.replace("SHELL", repr(shell(permissions=permissions)))).run()


def test_readonly_scenarios_has_prerequisites_and_no_write_controls(monkeypatch):
    app = scenario_app(monkeypatch, ["analysis.read"])
    assert not app.exception
    assert "NOT_ESTIMATED" in " ".join(x.value for x in app.info)
    assert "Za novu procenu" in " ".join(x.value for x in app.info)
    assert not app.button


def test_scenarios_denied_without_api_calls(monkeypatch):
    def forbidden(*a):
        raise AssertionError("No API read without scope/permission")
    monkeypatch.setattr(ordo_analytics_api, "runs", forbidden)
    app = AppTest.from_string(PREVIEW.replace("SHELL", repr(shell(permissions=[])))).run()
    assert not app.exception
    assert "analysis.read" in app.info[0].value


def test_writer_can_reach_existing_goal_form(monkeypatch):
    app = scenario_app(monkeypatch, ["analysis.read", "analysis.run"])
    assert not app.exception
    assert any(b.label == "Sačuvaj razvojni cilj" for b in app.button)
    assert not any(b.label == "Pokreni forecast" for b in app.button)


def test_scenario_status_requires_confirmation(monkeypatch):
    app = scenario_app(monkeypatch, ["analysis.read", "analysis.run"])
    monkeypatch.setattr(ordo_analytics_api, "scenarios", lambda *a: [
        {"id": "scenario", "goal_id": "goal", "name": "Synthetic scenario", "status": "draft"}])
    def forbidden(*a, **kw):
        raise AssertionError("No write without explicit confirmation")
    monkeypatch.setattr(ordo_analytics_api, "scenario_status", forbidden)
    app.run()
    next(b for b in app.button if b.label == "Sačuvaj status scenarija").click().run()
    assert not app.exception
    assert any("Potvrdite" in x.value for x in app.error)


def test_existing_status_and_review_wrappers_pin_scope(monkeypatch):
    seen = []
    monkeypatch.setattr(ordo_analytics_api, "request", lambda *a, **kw: seen.append((a, kw)) or {})
    monkeypatch.setattr(ordo_analytics_api, "_checked", lambda r, **kw: r)
    ordo_analytics_api.scenario_status("synthetic", scenario_id="s", organization_id="o", workspace_id="w", status="review_ready")
    ordo_analytics_api.review_assessment("synthetic", assessment_id="a", organization_id="o", workspace_id="w", decision="reviewed", reviewer_note="Synthetic note")
    assert [x[0][1] for x in seen] == ["/api/v1/ordo/analytics/scenarios/s/status", "/api/v1/ordo/analytics/scenario-assessments/a/review"]
    assert all(x[1]["json"]["organization_id"] == "o" and x[1]["json"]["workspace_id"] == "w" for x in seen)


def test_auth_state_and_mobile_controls_are_preserved():
    source = Path("src/streamlit_app/app.py").read_text()
    assert "st.session_state.clear()" in source
    assert "on_change=_scope_changed" in source
    assert "on_click=_refresh_access" in source
    assert "render_ordo_scenarios(token=token, shell=shell)" in source
    css = Path("src/streamlit_app/assets/app-shell.css").read_text()
    assert '[data-testid="stHeader"], #MainMenu' not in css
    assert '[data-testid="stToolbar"] { visibility: hidden' not in css
    assert "prefers-reduced-motion" in css
    assert "focus-visible" in css


@pytest.mark.parametrize("expired_logout", [False, True])
def test_actual_shell_clears_forms_across_workspace_product_and_logout(monkeypatch, expired_logout):
    import streamlit as st
    from src.streamlit_app import api_client, simpa_workspace, ordo_workspace
    organizations = []
    for org in ("org-a", "org-b"):
        organizations.append({"id": org, "name": org, "products": [
            {"code": product, "workspaces": [{"id": f"{org}-{product}-{i}", "name": f"Workspace {i}"} for i in (1, 2)]}
            for product in ("SIMPA", "ORDO")]})
    monkeypatch.setattr(api_client, "app_context", lambda token: {
        "display_name": "Synthetic reviewer", "email": "synthetic@example.org",
        "organizations": organizations})
    def app_shell(token, *, organization_id, product_code, workspace_id):
        value = shell(product_code, ["analysis.read"])
        value["organization"] = {"id": organization_id, "name": organization_id}
        value["workspace"] = {"id": workspace_id, "name": str(workspace_id)}
        return value
    monkeypatch.setattr(api_client, "app_shell", app_shell)
    def overview(*, token, shell):
        st.write(shell["workspace"]["id"])
        st.text_input("Synthetic draft", key="synthetic_draft")
    monkeypatch.setattr(simpa_workspace, "render_simpa_overview", overview)
    monkeypatch.setattr(ordo_workspace, "render_ordo_overview", overview)
    def logout(token):
        if expired_logout:
            raise api_client.AuthenticationRequired("Synthetic expired session")
    monkeypatch.setattr(api_client, "logout", logout)
    app = AppTest.from_file(Path("src/streamlit_app/app.py").resolve(), default_timeout=10)
    app.session_state["isi_access_token"] = "synthetic-placeholder"
    app.run()
    assert not app.exception
    app.text_input(key="synthetic_draft").input("Synthetic old workspace draft").run()
    app.selectbox(key="isi_workspace_selector").select("org-a-SIMPA-2").run()
    assert not app.exception
    assert app.text_input(key="synthetic_draft").value == ""
    assert "org-a-SIMPA-2" in [x.value for x in app.markdown]
    app.text_input(key="synthetic_draft").input("Synthetic old product draft").run()
    app.button(key="isi_product_button_ORDO").click().run()
    assert app.selectbox(key="isi_workspace_selector").value == "org-a-ORDO-1"
    assert not app.exception
    assert app.text_input(key="synthetic_draft").value == ""
    app.selectbox(key="isi_org_selector").select("org-b").run()
    assert app.selectbox(key="isi_workspace_selector").value == "org-b-ORDO-1"
    assert not app.exception
    assert "org-b-ORDO-1" in [x.value for x in app.markdown]
    app.text_input(key="synthetic_draft").input("Synthetic draft before refresh").run()
    next(b for b in app.button if b.label == "Osveži pristup").click().run()
    assert not app.exception
    assert app.text_input(key="synthetic_draft").value == ""
    next(b for b in app.button if b.label == "Odjavi se").click().run()
    assert not app.exception
    assert "isi_access_token" not in app.session_state
    assert "synthetic_draft" not in app.session_state


def test_confirmed_scenario_status_and_review_use_existing_scoped_apis(monkeypatch):
    app = scenario_app(monkeypatch, ["analysis.read", "analysis.run"])
    monkeypatch.setattr(ordo_analytics_api, "scenarios", lambda *a: [
        {"id": "scenario", "name": "Synthetic scenario", "status": "draft"}])
    monkeypatch.setattr(ordo_analytics_api, "assessments", lambda *a: [
        {"id": "assessment", "impact": "NOT_ESTIMATED", "forecast_performed": False, "status": "pending"}])
    seen = []
    def change(*a, **kw):
        seen.append(kw)
        return {"status": "saved"}
    monkeypatch.setattr(ordo_analytics_api, "scenario_status", change)
    monkeypatch.setattr(ordo_analytics_api, "review_assessment", change)
    app.run()
    assert not app.exception
    next(c for c in app.checkbox if c.label == "Potvrđujem promenu statusa izabranog scenarija").check()
    next(b for b in app.button if b.label == "Sačuvaj status scenarija").click().run()
    assert not app.exception
    assert seen[-1] == {"scenario_id": "scenario", "organization_id": "org", "workspace_id": "ws", "status": "draft"}
    next(t for t in app.text_area if t.label == "Obrazloženje stručnog pregleda").input("Synthetic reviewed evidence")
    next(c for c in app.checkbox if c.label == "Pregledao/la sam izvore, ograničenja i izabranu procenu").check()
    next(b for b in app.button if b.label == "Sačuvaj stručni pregled").click().run()
    assert not app.exception
    assert seen[-1] == {"assessment_id": "assessment", "organization_id": "org", "workspace_id": "ws", "decision": "reviewed", "reviewer_note": "Synthetic reviewed evidence"}
