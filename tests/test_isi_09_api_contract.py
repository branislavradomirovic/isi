from pathlib import Path


def test_api_is_simpa_scoped_and_permission_guarded():
    text = Path("src/api/simpa_analytics_routes.py").read_text()
    assert 'prefix="/api/v1/simpa/analytics"' in text
    assert 'product_code="SIMPA"' in text
    assert 'permission_code="analysis.read"' in text
    assert 'permission_code="analysis.run"' in text
    assert 'permission_code="indicator.manage"' in text
    assert 'status_code=status.HTTP_202_ACCEPTED' in text
