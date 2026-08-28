from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    "src/domains/ordo/analytics_models.py",
    "src/domains/ordo/analytics_schemas.py",
    "src/domains/ordo/analytics_service.py",
    "src/api/ordo_analytics_routes.py",
    "src/streamlit_app/ordo_analytics_api.py",
    "src/streamlit_app/ordo_analytics_workspace.py",
    "migrations/versions/20260828_0010_ordo_analytics_ai.py",
]
for item in required:
    if not (ROOT / item).exists():
        raise SystemExit(f"missing ISI-11 artifact: {item}")

if (ROOT / "src/domains/ordo/__init__.py").read_text().strip():
    raise SystemExit("ORDO domain boundary contract requires empty src/domains/ordo/__init__.py")

service = (ROOT / "src/domains/ordo/analytics_service.py").read_text()
migration = (ROOT / "migrations/versions/20260828_0010_ordo_analytics_ai.py").read_text()
ui = (ROOT / "src/streamlit_app/ordo_analytics_workspace.py").read_text()
api = (ROOT / "src/api/ordo_analytics_routes.py").read_text()

checks = {
    "ORDO product scope": 'product_code="ORDO"' in service and 'product_code="ORDO"' in api,
    "validated methodology guard": 'raise OrdoAnalyticsError("methodology_not_validated")' in service,
    "evidence-only scenario assessment": '"assessment_mode": "evidence_readiness_only"' in service,
    "no scenario forecasting": '"forecast_performed": False' in service and "forecast_performed = false" in migration,
    "local-only ORDO policy": '"provider_policy": "local_only"' in migration and '"allow_external": False' in migration,
    "mandatory human review": '"require_human_review": True' in migration and "human_review_required must be true" in migration,
    "offline JSON-safe prompt seed": "CAST(:output_schema AS JSON)" in migration,
    "ORDO namespace contract": 'private_namespace(organization_id, "ORDO")' in service and 'public_namespace("ORDO")' in service,
    "no SIMPA namespace": 'public_namespace("SIMPA")' not in service and 'private_namespace(organization_id, "SIMPA")' not in service,
    "UI safety notice": "ne prognozira efekte" in ui and "human review" in ui.lower(),
    "no hardcoded direct Ollama in domain service": "ollama" not in service.lower(),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("ISI-11 static audit FAILED: " + ", ".join(failed))
print("ISI-11 ORDO analytics + AI static audit PASS")
