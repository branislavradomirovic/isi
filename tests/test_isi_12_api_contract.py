from pathlib import Path


def test_reporting_api_scope_and_permissions():
    text = Path("src/api/reporting_routes.py").read_text()
    assert 'prefix="/api/v1/reporting"' in text
    assert 'permission_code="report.read"' in text
    assert 'permission_code="analysis.run"' in text
    assert 'permission_code="organization.manage"' in text
    assert "resolve_selection(" in text
    assert "product_code=product_code" in text
    for route in ("/sources", '"/reports"', "/versions/{version_id}/submit", "/versions/{version_id}/review", "/versions/{version_id}/publish", "/versions/{version_id}/exports"):
        assert route in text
