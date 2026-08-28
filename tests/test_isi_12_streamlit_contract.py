from pathlib import Path


def test_reporting_ui_exposes_provenance_review_publish_and_download():
    text = Path("src/streamlit_app/reporting_workspace.py").read_text()
    for token in (
        "Provenance",
        "Pošalji na review",
        "Odobri verziju",
        "Publikuj verziju",
        "Preuzmi artefakt",
        "SIMPA i ORDO dele engine, ali ne dele domain sadržaj",
    ):
        assert token in text
