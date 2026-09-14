from pathlib import Path

import pytest

from src.streamlit_app import ordo_analytics_workspace, simpa_analytics_workspace


class _FakeStreamlit:
    def __init__(self):
        self.dataframes = []

    def markdown(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def dataframe(self, value, **_kwargs):
        self.dataframes.append(value)

    def selectbox(self, _label, options, **_kwargs):
        return options[0]


def _historical_run() -> dict:
    return {
        "id": "historical-run",
        "status": "completed",
        "analytical_artifact_type": "LEGACY_OBSERVATION",
        "analytical_snapshot_id": None,
        "analytical_feature_version_id": None,
        "analytical_artifact_fingerprint": "",
        "evidence_quality_score": 0.5,
        "validated_observation_ratio": 0.5,
        "provenance_coverage": 0.5,
        "indicator_coverage": 0.5,
        "dimension_coverage": 0.5,
        "pillar_coverage": 0.5,
        "created_at": "2026-09-14T00:00:00Z",
    }


def test_both_workspaces_select_registry_backed_governed_artifacts():
    for product in ("simpa", "ordo"):
        text = Path(f"src/streamlit_app/{product}_analytics_workspace.py").read_text()
        assert "data_api.list_analytical_datasets" in text
        assert "data_api.list_analytical_snapshots" in text
        assert "data_api.list_analytical_features" in text
        assert "data_api.list_analytical_feature_versions" in text
        assert '"VALIDATED", "FROZEN"' in text
        assert '"GOVERNED", "FROZEN"' in text
        assert "analytical_artifact_type" in text
        assert "analytical_artifact_id" in text
        assert "analytical_artifact_fingerprint" in text


@pytest.mark.parametrize("summary_failure", [False, True])
@pytest.mark.parametrize(
    "workspace,product,independent_calls",
    [
        (simpa_analytics_workspace, "SIMPA", {"methodologies", "syntheses"}),
        (
            ordo_analytics_workspace,
            "ORDO",
            {"methodologies", "goals", "scenarios", "assessments", "syntheses"},
        ),
    ],
)
def test_artifact_absence_or_summary_failure_preserves_independent_workspace_content(
    monkeypatch, workspace, product, independent_calls, summary_failure
):
    fake_st = _FakeStreamlit()
    calls = []
    api = workspace.simpa_analytics_api if product == "SIMPA" else workspace.ordo_analytics_api

    monkeypatch.setattr(workspace, "st", fake_st)
    monkeypatch.setattr(
        workspace,
        "_eligible_artifacts",
        lambda *_args: ([{"type": "snapshot", "id": "artifact", "fingerprint": "a" * 64}]
                       if summary_failure else []),
    )
    monkeypatch.setattr(api, "runs", lambda *_args, **_kwargs: [_historical_run()])

    def record(name, result):
        def call(*_args, **_kwargs):
            calls.append(name)
            return result
        return call

    monkeypatch.setattr(api, "methodologies", record("methodologies", []))
    monkeypatch.setattr(api, "syntheses", record("syntheses", []))
    if summary_failure:
        monkeypatch.setattr(api, "summary", record("summary", None))
    if product == "ORDO":
        monkeypatch.setattr(api, "goals", record("goals", []))
        monkeypatch.setattr(api, "scenarios", record("scenarios", []))
        monkeypatch.setattr(api, "assessments", record("assessments", []))

    renderer = (workspace.render_simpa_analytics if product == "SIMPA"
                else workspace.render_ordo_analytics)
    renderer(
        token="token",
        shell={
            "organization": {"id": "organization"},
            "workspace": {"id": "workspace"},
            "product": {"code": product, "permission_codes": []},
        },
    )

    assert independent_calls <= set(calls)
    assert any(rows and rows[0].get("id") == "historical-run" for rows in fake_st.dataframes)
