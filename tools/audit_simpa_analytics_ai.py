from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *tokens: str) -> None:
    text = (ROOT / path).read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"missing-token:{path}:{token}")


def main() -> int:
    require("src/domains/simpa/analytics_models.py", "simpa_indicator_methodologies", "simpa_analytics_runs", "simpa_indicator_results", "simpa_ai_syntheses")
    require("src/domains/simpa/analytics_service.py", "methodology_not_validated", "evidence_quality_score", "simpa.monitoring.synthesis", 'product_code="SIMPA"')
    require("src/api/simpa_analytics_routes.py", '/api/v1/simpa/analytics', 'permission_code="analysis.read"', 'permission_code="analysis.run"')
    require("src/streamlit_app/simpa_analytics_workspace.py", "Kvalitet dokaza", "local-only", "human review", "qwen2.5:7b-instruct")
    require("migrations/versions/20260828_0008_simpa_analytics_ai.py", 'revision = "20260828_0008"', 'down_revision = "20260828_0007"', "simpa.monitoring.synthesis")
    simpa_init = (ROOT / "src/domains/simpa/__init__.py").read_text()
    if simpa_init.strip():
        raise SystemExit("SIMPA package boundary must remain empty")
    print("ISI-09 SIMPA analytics + AI static audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
