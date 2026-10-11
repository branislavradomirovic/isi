import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import (
    ordo_analytics_workspace as ordo,
    simpa_analytics_workspace as simpa,
    extraction_workspace as extraction,
    spatial_workspace as spatial,
)
from src.streamlit_app.evidence_view import evidence_rows, render_evidence
from src.streamlit_app.api_client import ApiUnavailable
from tests.test_isi_24d_forecast_xai import _forecast

MODULES = [
    "simpa_analytics_workspace",
    "ordo_analytics_workspace",
    "spatial_workspace",
    "extraction_workspace",
    "linked_reporting_workspace",
    "attribution_view",
]


@pytest.mark.parametrize("name", MODULES)
def test_default_json_removed_with_technical_geometry_exception(name):
    tree = ast.parse(Path("src/streamlit_app/" + name + ".py").read_text())
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "st"
        and n.func.attr == "json"
    ]
    if name == "spatial_workspace":
        assert len(calls) == 1 and ast.unparse(calls[0].args[0]) == "chosen['geometry']"
    else:
        assert not calls
    if name == "ordo_analytics_workspace":
        assert 'st.write(xai["interval"])' not in ast.unparse(tree)
    assert any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "render_evidence"
        for n in ast.walk(tree)
    )


def test_injected_renderer_uses_ui_and_preserves_field_identity():
    ui = SimpleNamespace(markdown=Mock(), dataframe=Mock())
    render_evidence("Izvor", dict(source_hash="a" * 64, value=0, available=False), ui=ui)
    rows = ui.dataframe.call_args.args[0]
    assert rows == evidence_rows(dict(source_hash="a" * 64, value=0, available=False))
    assert ui.dataframe.call_args.kwargs == dict(width="stretch", hide_index=True)


@pytest.mark.parametrize("module", [ordo, simpa, extraction, spatial])
def test_failures_never_echo_private_body(monkeypatch, module):
    code = """
from tests.test_isi_30d3a_typed_result_views import raise_private
from src.streamlit_app import MODULE as module
SAFE(raise_private)
""".replace("MODULE", module.__name__.rsplit(".", 1)[-1]).replace(
        "SAFE", "module.safe" if module is extraction else "module._safe"
    )
    at = AppTest.from_string(code).run()
    assert not at.exception
    assert at.error or at.warning
    assert "SYNTHETIC_PRIVATE_BODY" not in repr([x.value for x in [*at.error, *at.warning]])


def raise_private():
    raise ApiUnavailable("SYNTHETIC_PRIVATE_BODY")


def forecast_app():
    from src.streamlit_app.ordo_analytics_workspace import _render_forecast_results

    _render_forecast_results(
        token="synthetic",
        organization_id="synthetic-org",
        workspace_id="synthetic-space",
        permissions={"analysis.read"},
        runs=[],
    )


@pytest.mark.parametrize("status", ["ESTIMATED", "NOT_ESTIMATED"])
def test_real_forecast_renderer_typed_provenance_no_fabricated_points(monkeypatch, status):
    value = _forecast(status)
    if status == "NOT_ESTIMATED":
        value["forecast_points"] = [dict(horizon_step=1, time="2025-01-01", point=999, lower=0, upper=1000)]
    before = deepcopy(value)
    monkeypatch.setattr(ordo, "_render_time_series_workflow", lambda **kw: None)
    monkeypatch.setattr(ordo.ordo_analytics_api, "forecasts", lambda *a: [value])
    monkeypatch.setattr(ordo.ordo_analytics_api, "forecast_detail", lambda *a, **kw: deepcopy(value))
    at = AppTest.from_function(forecast_app).run()
    assert not at.exception and not at.json
    tables = [x.value for x in at.dataframe if "Polje" in x.value.columns]
    assert tables
    text = " ".join(str(t.to_dict("records")) for t in tables)
    assert "e" * 64 in text and "generic_confidence_score" in text and "unavailable" in text
    if status == "ESTIMATED":
        assert any("point" in x.value.columns and x.value["point"].tolist() == [10.0] for x in at.dataframe)
    else:
        assert not any("point" in x.value.columns for x in at.dataframe)
        assert "999" not in text
        assert any("NOT_ESTIMATED" in x.value for x in at.info)
    assert value == before


def scenario_app():
    from src.streamlit_app.ordo_analytics_workspace import _render_scenario_assessments

    _render_scenario_assessments(
        [
            dict(
                id="synthetic",
                scenario_id="scenario",
                analytics_run_id="run",
                forecast_performed=False,
                impact="NOT_ESTIMATED",
                impact_estimation_reason_code="NO_APPROVED_RESPONSE_MODEL",
                impact_estimate_numeric=None,
                impact_estimate_unit="",
                assumptions=["Synthetic assumption"],
                provenance=dict(source_hash="f" * 64),
            )
        ]
    )


def test_real_scenario_renderer_retains_nonnumeric_boundary():
    at = AppTest.from_function(scenario_app).run()
    assert not at.exception and not at.json and not at.metric and at.warning
    assert any("nije zamenjen nulom" in x.value for x in at.info)
    assert len(at.dataframe) == 2


def extraction_app():
    from tests.test_isi_29e_contracts import example
    from src.streamlit_app.extraction_workspace import render_detail

    render_detail(
        dict(
            state="REVIEWED_ACCEPTED",
            artifact=dict(output=example(), links=dict(m1=dict(state="UNRESOLVED")), source_hash="a" * 64),
            artifact_fingerprint="b" * 64,
            review=dict(decision="accepted", note="Synthetic review"),
        )
    )


def test_real_extraction_renderer_quotes_locators_review_and_provenance():
    at = AppTest.from_function(extraction_app).run()
    assert not at.exception and not at.json
    tables = [x.value.to_dict("records") for x in at.dataframe]
    text = repr(tables)
    assert "statement.start" in text and "citations.0.anchor.quote" in text
    assert (
        "Synthetic has 12 services in 2025." in text
        and "UNRESOLVED" in text
        and "accepted" in text
        and "a" * 64 in text
    )
    assert any("nije potvrda istinitosti" in x.value for x in at.warning)


def test_typed_values_remain_text_not_html_or_inferred():
    text = "<script>SYNTHETIC_UNTRUSTED</script>"
    rows = evidence_rows(dict(quote=text, confidence=None, valid=False, value=0))
    assert rows[0]["Vrednost"] == text
    assert rows[1]["Vrednost"] == "Nije navedeno" and rows[2]["Vrednost"] == "False" and rows[3]["Vrednost"] == "0"


def test_guide_ten_items_and_limits():
    text = Path("docs/help/ISI-RESULT-EVIDENCE-GUIDE.md").read_text()
    assert all(f"## {i}." in text for i in range(1, 11))
    assert all(x in text for x in ["NOT_ESTIMATED", "GeoJSON", "SHAP", "UNCALIBRATED", "Datirane ilustracije"])
