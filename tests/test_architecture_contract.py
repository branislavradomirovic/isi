from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_foundation_paths_exist():
    required = [
        "src/api/app.py",
        "src/public/templates/index.html",
        "src/public/static/css/site.css",
        "src/streamlit_app/app.py",
        "src/core/config.py",
        "src/core/database.py",
        "src/core/ai/__init__.py",
        "src/platform/__init__.py",
        "src/workers/worker.py",
        "src/domains/simpa/__init__.py",
        "src/domains/ordo/__init__.py",
        "automation/tasks.json",
        "automation/specs/ISI-00-01-FOUNDATION.md",
        "docs/architecture/ADR-0001-platform-baseline.md",
        "docs/architecture/ADR-0002-public-private-ui.md",
        "docs/architecture/ADR-0003-domain-boundaries.md",
        "docs/architecture/ADR-0004-service-topology.md",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    assert not missing, f"Missing foundation paths: {missing}"


def test_no_product_logic_is_smuggled_into_domain_boundaries():
    for product in ("simpa", "ordo"):
        content = (ROOT / "src" / "domains" / product / "__init__.py").read_text()
        assert content.strip() == ""
