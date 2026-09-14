from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_domain_analytics_have_no_observation_or_raw_source_bypass():
    simpa = (ROOT / "src/domains/simpa/analytics_service.py").read_text()
    ordo = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    for text, forbidden in (
        (simpa, "SimpaIndicatorObservation"),
        (ordo, "OrdoIndicatorObservation"),
        (simpa, "DataSourceVersion"),
        (ordo, "DataSourceVersion"),
    ):
        assert forbidden not in text
    assert "source_observation_ids=[]" in simpa
    assert "source_observation_ids=[]" in ordo


def test_all_new_downstream_paths_revalidate_governed_runs():
    simpa = (ROOT / "src/domains/simpa/analytics_service.py").read_text()
    ordo = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
    simpa_reporting = (ROOT / "src/domains/simpa/reporting_adapter.py").read_text()
    ordo_reporting = (ROOT / "src/domains/ordo/reporting_adapter.py").read_text()
    assert simpa.count("revalidate_analytics_run(") >= 3
    assert ordo.count("revalidate_analytics_run(") >= 4
    assert "analytical_snapshot" in simpa_reporting
    assert "analytical_feature_version" in simpa_reporting
    assert "analytical_snapshot" in ordo_reporting
    assert "analytical_feature_version" in ordo_reporting
