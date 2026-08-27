from pathlib import Path

required = [
    Path("src/platform/data/models.py"),
    Path("src/platform/data/storage.py"),
    Path("src/platform/data/ingestion.py"),
    Path("src/platform/data/service.py"),
    Path("src/platform/data/queue.py"),
    Path("src/api/data_routes.py"),
    Path("src/workers/data_jobs.py"),
    Path("src/streamlit_app/data_workspace.py"),
    Path("migrations/versions/20260828_0005_shared_data_platform.py"),
]
for path in required:
    if not path.exists():
        raise SystemExit(f"missing required artifact: {path}")

models = Path("src/platform/data/models.py").read_text()
for token in ("organization_id", "workspace_id", "product_code", "sha256", "storage_key"):
    if token not in models:
        raise SystemExit(f"missing data model scope/integrity field: {token}")

routes = Path("src/api/data_routes.py").read_text()
for token in ('"data.read"', '"data.upload"', '"data.validate"', "resolve_selection", "has_permission"):
    if token not in routes:
        raise SystemExit(f"missing server-side auth contract: {token}")

storage = Path("src/platform/data/storage.py").read_text()
if "organization_id" not in storage or "workspace_id" not in storage or "sha256" not in storage:
    raise SystemExit("storage key is not tenant/workspace content-addressed")

all_data_code = "\n".join(path.read_text() for path in Path("src/platform/data").glob("*.py"))
for prohibited in ("openai", "ollama", "embedding", "pgvector"):
    if prohibited in all_data_code.lower():
        raise SystemExit(f"AI concern leaked into ISI-06 shared data layer: {prohibited}")

print("ISI-06 shared data platform static audit PASS")
