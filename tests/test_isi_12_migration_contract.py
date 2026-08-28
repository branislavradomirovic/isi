from pathlib import Path


def test_reporting_migration_contract():
    text = Path("migrations/versions/20260828_0011_reporting.py").read_text()
    assert 'revision = "20260828_0011"' in text
    assert 'down_revision = "20260828_0010"' in text
    for table in ("core_reports", "core_report_versions", "core_report_reviews", "core_report_exports"):
        assert f'"{table}"' in text
    assert "product_code IN ('SIMPA','ORDO')" in text
    assert "draft','in_review','approved','rejected','published','superseded" in text
    assert "format IN ('json','markdown','html')" in text
