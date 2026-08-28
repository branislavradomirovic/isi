from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def require(path: str, *tokens: str):
    text = (ROOT / path).read_text()
    for token in tokens:
        if token not in text: raise SystemExit(f"missing-token:{path}:{token}")

require("src/domains/ordo/catalog.py", "PILLAR_CATALOG", "DIMENSION_CATALOG", "INDICATOR_CATALOG", "Conceptual registry only")
require("src/domains/ordo/models.py", "ordo_destination_profiles", "ordo_assets", "ordo_stakeholders", "ordo_indicator_observations")
require("src/domains/ordo/service.py", "validate_ordo_scope", 'Workspace.product_code == "ORDO"', 'DataSource.product_code == "ORDO"')
require("src/api/ordo_routes.py", 'prefix="/api/v1/ordo"', 'product_code="ORDO"')
require("src/streamlit_app/ordo_workspace.py", "Razvoj destinacije kao povezan sistem", "conceptual indicator registry")
if (ROOT / "src/domains/ordo/__init__.py").read_text().strip(): raise SystemExit("ORDO package boundary must remain empty")
print("ISI-10 ORDO domain foundation static audit PASS")
