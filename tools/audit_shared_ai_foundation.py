from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *tokens: str) -> None:
    target = ROOT / path
    if not target.exists():
        raise SystemExit(f"missing:{path}")
    text = target.read_text()
    for token in tokens:
        if token not in text:
            raise SystemExit(f"missing-token:{path}:{token}")


def main() -> int:
    require("src/platform/ai/policy.py", "SIMPA", "sensitive", "local_only")
    require("src/platform/ai/namespaces.py", "PUBLIC/ISI", "cross_tenant_namespace", "cross_product_private_namespace")
    require("src/platform/ai/providers.py", "class OllamaProvider", "class DevelopmentStubProvider")
    require("src/platform/ai/gateway.py", "development_stub_forbidden_in_production", "external_provider_not_configured")
    require("src/platform/ai/structured.py", "invalid_json", "missing_required")
    require("src/api/ai_routes.py", '"ai.run"', "resolve_selection", "has_permission")
    require("src/platform/ai/service.py", "request_sha256", "ai.job.completed", "provider_allowed")
    require("migrations/versions/20260828_0006_shared_ai_foundation.py", "core_ai_jobs", "core_ai_embeddings", "pg_extension", "core_ai_embedding_vectors")
    require(
        "src/streamlit_app/ai_workspace.py",
        "Shared AI Foundation",
        "Lokalni Ollama foundation test",
        "_render_local_ollama_diagnostic",
        'item.get("provider_type") == "ollama"',
    )
    print("ISI-07 shared AI foundation static audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
