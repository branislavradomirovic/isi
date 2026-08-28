from pathlib import Path


def require(path: str, *tokens: str) -> None:
    text = Path(path).read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"ISI-12 reporting audit FAILED: {path} missing {token!r}")


for path in (
    "src/platform/reporting/models.py",
    "src/platform/reporting/service.py",
    "src/platform/reporting/render.py",
    "src/domains/simpa/reporting_adapter.py",
    "src/domains/ordo/reporting_adapter.py",
    "src/api/reporting_routes.py",
    "src/streamlit_app/reporting_workspace.py",
    "migrations/versions/20260828_0011_reporting.py",
):
    if not Path(path).exists():
        raise SystemExit(f"ISI-12 reporting audit FAILED: missing {path}")

if Path("src/platform/reporting/__init__.py").read_text().strip():
    raise SystemExit("ISI-12 reporting audit FAILED: reporting package boundary __init__.py must stay empty")

require("src/platform/reporting/models.py", "core_reports", "core_report_versions", "core_report_reviews", "core_report_exports")
require("src/platform/reporting/service.py", "report_source_cross_tenant", "report_source_cross_workspace", "report_source_cross_product", "report_provenance_required", "superseded")
require("src/platform/reporting/render.py", '"json"', '"markdown"', '"html"')
require("src/domains/simpa/reporting_adapter.py", '"product_code": "SIMPA"', "skor socijalnog rizika")
require("src/domains/ordo/reporting_adapter.py", '"product_code": "ORDO"', "forecast_performed", "ordo_report_forecast_forbidden")
require("src/api/reporting_routes.py", 'prefix="/api/v1/reporting"', 'permission_code="report.read"', 'permission_code="analysis.run"', 'permission_code="organization.manage"')
require("src/streamlit_app/reporting_workspace.py", "Izveštaji", "Provenance", "Pošalji na review", "Publikuj verziju")
require("migrations/versions/20260828_0011_reporting.py", 'revision = "20260828_0011"', 'down_revision = "20260828_0010"')
print("ISI-12 shared reporting static audit PASS")
