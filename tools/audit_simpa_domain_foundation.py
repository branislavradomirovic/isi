from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *tokens: str) -> None:
    text = (ROOT / path).read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"missing-token:{path}:{token}")


def main() -> int:
    require("src/domains/simpa/catalog.py", "DIMENSION_CATALOG", "SOURCE_TYPE_CATALOG", "INDICATOR_CATALOG", "family_vulnerability_index")
    require("src/domains/simpa/models.py", "simpa_indicator_definitions", "simpa_indicator_observations", "simpa_data_mappings")
    require("src/domains/simpa/service.py", 'Workspace.product_code == "SIMPA"', 'DataSource.product_code == "SIMPA"', "provenance_note")
    require("src/api/simpa_routes.py", 'prefix="/api/v1/simpa"', 'product_code="SIMPA"', 'permission_code="indicator.read"')
    require("src/streamlit_app/simpa_workspace.py", "SIMPA indicator registry", "ISI-08 ne upisuje izmišljenu JLS", "ORDO domain indicator model dolazi u ISI-10")
    require("migrations/versions/20260828_0007_simpa_domain_foundation.py", 'revision = "20260828_0007"', 'down_revision = "20260828_0006"', '"methodology_status": "conceptual"')
    for path in ["src/domains/simpa/catalog.py", "src/domains/simpa/models.py", "src/domains/simpa/service.py", "src/streamlit_app/simpa_workspace.py"]:
        text = (ROOT / path).read_text().upper()
        if "COSMOS" in text:
            raise SystemExit(f"retired-brand-token:{path}:COSMOS")
    print("ISI-08 SIMPA domain foundation static audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
