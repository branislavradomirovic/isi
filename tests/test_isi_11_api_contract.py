from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_api_is_ordo_scoped_permission_guarded_and_has_scenario_routes():
    text = (ROOT / "src/api/ordo_analytics_routes.py").read_text()
    assert 'prefix="/api/v1/ordo/analytics"' in text
    assert 'product_code="ORDO"' in text
    assert 'permission_code="analysis.read"' in text
    assert 'permission_code="analysis.run"' in text
    assert 'permission_code="indicator.manage"' in text
    assert '@router.post("/scenario-assessments"' in text
    assert '@router.post("/syntheses"' in text
    assert 'status_code=status.HTTP_202_ACCEPTED' in text
