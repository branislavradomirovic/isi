from pathlib import Path

from src.streamlit_app.simpa_help_workspace import HELP_REQUIRED_FIELDS, SIMPA_HELP_TOPICS
from src.streamlit_app.ordo_help_workspace import ORDO_HELP_TOPICS


def test_graphical_actions_have_ten_help_fields_and_truthful_limits():
    for topics, key, product in ((SIMPA_HELP_TOPICS, "SIMPA-H11", "SIMPA"), (ORDO_HELP_TOPICS, "ORDO-H10", "ORDO")):
        topic = next(t for t in topics if t["id"] == key)
        assert all(topic[field].strip() for field in HELP_REQUIRED_FIELDS)
        assert all(
            "29A" in topic[field]
            or "grafikon" in topic[field]
            or "interval" in topic[field]
            or "zero" in topic[field]
            or "Grafikoni" in topic[field]
            for field in HELP_REQUIRED_FIELDS
        )
        guide = Path(f"docs/help/{product}-USER-GUIDE.md").read_text()
        for phrase in (
            "29A Graphical XAI",
            "24 koeficijenta",
            "60 tačaka",
            "40 selectable origins",
            "SHAP",
            "analysis.read",
            "fingerprint",
            "human review",
        ):
            assert phrase in guide
    matrix = Path("docs/help/ISI-HELP-COVERAGE-MATRIX.md").read_text()
    for action in ("SIMPA-29A-COEFFICIENT-CHART", "ORDO-29A-FORECAST-CHART", "ORDO-29A-ORIGIN-SELECT"):
        row = next(line for line in matrix.splitlines() if line.startswith(f"| {action} |"))
        assert "| PARTIAL |" in row


def test_shap_guidance_matches_delivered_product_boundary():
    simpa = Path("docs/help/SIMPA-USER-GUIDE.md").read_text()
    ordo = Path("docs/help/ORDO-USER-GUIDE.md").read_text()
    assert "SHAP ostaje pending 29D" not in simpa + ordo
    assert "podržani numerički model" in simpa
    assert "SIMPA numeričkom modelu" in ordo
