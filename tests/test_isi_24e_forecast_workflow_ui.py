from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text()


def test_client_exposes_scoped_spec_lifecycle_identity_and_forecast_post_wrappers():
    client = _read("src/streamlit_app/ordo_analytics_api.py")
    for function in (
        "def time_series_specs(", "def time_series_spec_detail(",
        "def create_time_series_spec(", "def propose_time_series_spec(",
        "def validate_time_series_spec(", "def retire_time_series_spec(",
        "def time_series_identities(", "def execute_forecast(",
    ):
        assert function in client
    assert '"POST", "/api/v1/ordo/analytics/forecasts"' in client
    assert '"organization_id": organization_id' in client
    assert '"workspace_id": workspace_id' in client


def test_ui_uses_permissions_validated_spec_discovered_identity_and_explicit_choices():
    ui = _read("src/streamlit_app/ordo_analytics_workspace.py")
    assert '"indicator.manage" in permissions' in ui
    assert '"analysis.run" in permissions' in ui
    assert 'item.get("status") == "validated"' in ui
    assert "time_series_identities" in ui
    assert "contract.get(\"candidate_families\")" in ui
    assert '[0.80, 0.90, 0.95]' in ui
    assert "execute_forecast" in ui
    assert "automatic_model_selection" in ui
    assert "methodology_fingerprint" in ui
    assert "time_series_spec_id = st.text_input" not in ui
    assert "methodology fingerprint" not in ui.casefold()
    assert "ISI-11 povezuje" not in ui
    assert "read-only prikaz" not in ui.casefold()
    assert "nema forecast execution formu" not in ui.casefold()
    assert "niti time-series-spec authoring/discovery workflow" not in ui.casefold()


def test_authoring_ui_collects_customer_fields_but_not_server_authority_fields():
    ui = _read("src/streamlit_app/ordo_analytics_workspace.py")
    for marker in (
        "ordo_spec_series_key", "ordo_spec_indicator", "ordo_spec_target_semantic",
        "ordo_spec_time_field", "ordo_spec_frequency", "ordo_spec_series_fields",
        "ordo_spec_start", "ordo_spec_end", "ordo_spec_as_of", "ordo_spec_min_history",
        "ordo_spec_missing_ratio", "ordo_spec_missing_rule", "ordo_spec_outlier",
        "ordo_spec_revision", "ordo_spec_comparability", "ordo_spec_transformation",
        "ordo_spec_trend", "ordo_spec_seasonality", "ordo_spec_families",
        "ordo_spec_horizon", "ordo_spec_horizon_unit", "ordo_spec_diagnostics",
        "ordo_spec_limitations", "ordo_spec_initial_train", "ordo_spec_step",
        "ordo_spec_origins", "ordo_spec_metrics",
    ):
        assert marker in ui
    for forbidden_widget in (
        'st.text_input("Methodology UUID', 'st.text_input("Methodology fingerprint',
        'st.checkbox("Forecast execution', 'st.checkbox("Automatic model selection',
        'st.checkbox("Non causal',
    ):
        assert forbidden_widget not in ui


def test_h06_h10_and_user_guide_cover_reachable_workflow_and_safe_boundaries():
    help_source = _read("src/streamlit_app/ordo_help_workspace.py")
    guide = _read("docs/help/ORDO-USER-GUIDE.md")
    combined = f"{help_source}\n{guide}"
    for phrase in (
        "indicator.manage", "analysis.run", "analysis.read", "VALIDATED",
        "validation note", "evidence reference", "series identity", "candidate_families",
        "0.80", "0.90", "0.95", "ESTIMATED", "NOT_ESTIMATED",
        "automatic model selection", "fallback", "rolling-origin", "fingerprint",
        "future performance", "causal",
    ):
        assert phrase.casefold() in combined.casefold()
    for stale in (
        "The “Persistirani forecast rezultati” section is read-only",
        "There is no raw-UUID execution form, time-series-spec authoring/discovery workflow",
        "24D nema execution formu",
        "spec authoring/discovery-ja",
        "forecast execution workflow niti",
    ):
        assert stale not in combined


def test_help_matrix_keeps_frozen_statuses_and_updates_a13_evidence():
    matrix = _read("docs/help/ISI-HELP-COVERAGE-MATRIX.md")
    assert "| INV-A12 | ORDO indicators | VERIFIED |" in matrix
    assert "| INV-A13 | ORDO analytics and scenarios | VERIFIED |" in matrix
    assert "governed time-series-spec lifecycle" in matrix
    assert "explicit forecast execution" in matrix
    assert "tests/test_isi_24e_forecast_workflow_api.py" in matrix
    assert "tests/test_isi_24e_forecast_workflow_ui.py" in matrix
    assert "| INV-A19 | ORDO Help, User Guide and XAI interpretation | VERIFIED |" in matrix
    assert "| INV-A21 | Cross-product Help Coverage Matrix | PARTIAL |" in matrix
