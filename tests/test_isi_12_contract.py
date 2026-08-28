from pathlib import Path


def test_reporting_foundation_files_and_shared_boundary():
    for path in (
        "src/platform/reporting/models.py",
        "src/platform/reporting/service.py",
        "src/platform/reporting/render.py",
        "src/platform/reporting/schemas.py",
        "src/api/reporting_routes.py",
        "src/streamlit_app/reporting_workspace.py",
        "src/domains/simpa/reporting_adapter.py",
        "src/domains/ordo/reporting_adapter.py",
    ):
        assert Path(path).exists(), path
    assert Path("src/platform/reporting/__init__.py").read_text().strip() == ""


def test_reporting_is_versioned_and_human_governed():
    service = Path("src/platform/reporting/service.py").read_text()
    assert "create_new_version" in service
    assert "report_provenance_required" in service
    assert "report_version_not_reviewable" in service
    assert "report_version_not_publishable" in service
    assert "status=\"superseded\"" in service
    assert "report_export_requires_approved_version" in service
