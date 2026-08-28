from pathlib import Path


def test_simpa_reporting_does_not_recast_evidence_quality_as_social_risk():
    text = Path("src/domains/simpa/reporting_adapter.py").read_text()
    assert "ne predstavljaju skor socijalnog rizika" in text
    assert "Konceptualni indikatori bez validirane metodologije" in text


def test_ordo_reporting_preserves_no_forecast_invariant():
    text = Path("src/domains/ordo/reporting_adapter.py").read_text()
    assert "ordo_report_forecast_forbidden" in text
    assert "ordo_report_ai_forecast_forbidden" in text
    assert '"forecast_performed": False' in text
    assert "forecast_performed=false je hard invariant" in text
