from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_r4_contract_and_docs_define_runtime_and_authority_boundary():
    contract_path = ROOT / "automation/specs/ISI-25A-AI-MLOPS-GOVERNANCE-EVALUATION-FOUNDATION.md"
    contract = contract_path.read_text(encoding="utf-8")
    registry = _text("docs/roadmap/ISI-25-MODEL-REGISTRY.md")
    promotion = _text("docs/roadmap/ISI-25-PROMOTION-POLICY.md")
    assert "provider gateway remains the single provider invocation boundary" in registry
    assert "SIMPA-EVAL-v1" in registry and "ORDO-EVAL-v1" in registry
    assert "CONTRACT/FIXTURE" in registry and "foundation_only_not_production_promotion_evidence=true" in registry
    assert "No permanent or hard-coded champion exists" in registry
    assert "selected/default runtime model only" in registry
    assert "platform-admin-only" in registry
    assert "report.publish" in registry
    assert "Capability-bound registered fallback execution" in contract
    assert "PROMOTION EXECUTION / WINNER SELECTION NOT IMPLEMENTED IN ISI-25A" in promotion
    for deferred in ("evaluator engines", "circuit-breaker", "drift", "dashboards"):
        assert deferred in (registry + promotion)


def test_system_inventory_records_25a_as_built_and_future_boundary():
    master = _text("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md")
    assert "INV-C40 | AI capability/model registration + fallback + prompt rollback" in master
    assert "INV-C41 | AI evaluation dataset/run/result/review foundation" in master
    assert "INV-E05 | Selected-model-only runtime + persisted fallback policy" in master
    assert "INV-E06 | AI runtime model/prompt/policy + capability governance registry" in master
    assert "Status: **IN PROGRESS**" in master
    assert "ISI-25B remains required" in master
    assert "Dedicated Vision provider/service | AI modality | NOT_PRESENT" in master
    assert "Dedicated Audio provider/service | AI modality | NOT_PRESENT" in master


def test_eval_manifests_are_explicit_non_production_foundation_contracts():
    for filename, product in (("SIMPA-EVAL-v1.json", "SIMPA"), ("ORDO-EVAL-v1.json", "ORDO")):
        manifest = json.loads((ROOT / "tests/evals" / filename).read_text(encoding="utf-8"))
        assert manifest["dataset_key"] == filename.removesuffix(".json")
        assert manifest["product_code"] == product
        assert manifest["sensitivity_classification"] == "synthetic_non_production"
        assert manifest["foundation_only_not_production_promotion_evidence"] is True
        assert manifest["frozen"] is True and manifest["approval_state"] == "approved"


def test_no_permanent_champion_or_promotion_execution_exists():
    governance = _text("src/platform/ai/governance.py")
    service = _text("src/platform/ai/service.py")
    routes = _text("src/api/ai_routes.py")
    assert "CHAMPION_FORBIDDEN_REASON" in governance
    assert "champion_promotion_requires_isi_25b_evaluation_and_approval_evidence" in governance
    assert "authorized_runtime_fallbacks" in governance
    assert "runtime_fallback_allows_error" in governance
    assert "authorized_runtime_fallbacks" not in service
    assert "runtime_fallback_allows_error" not in service
    assert "return [selected]" in service
    assert "promote_to_champion" not in governance + service + routes
    assert "select_winner" not in governance + service + routes
    assert "deployment" not in routes.lower()


def test_ordo_24c_24e_semantics_remain_authoritative():
    master = _text("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md")
    migration_32 = _text("migrations/versions/20260916_0032_ordo_forecast_backtest_uncertainty.py")
    combined = master + migration_32
    for marker in (
        "scenario is not forecast",
        "NOT_ESTIMATED",
        "NO_APPROVED_RESPONSE_MODEL",
        "LEGACY_NOT_EVALUATED",
        "automatic_model_selection = false",
    ):
        assert marker in combined
    assert "no automatic selection/fallback" in master


def test_ci_and_server_boundaries_remain_frozen():
    workflow = _text(".github/workflows/ci.yml")
    on_block = workflow.split("concurrency:", 1)[0]
    assert "workflow_dispatch:" in on_block
    for automatic in ("push:", "pull_request:", "schedule:", "workflow_run:", "merge_group:"):
        assert automatic not in on_block
    status = _text("automation/STATUS.md")
    assert "no GitHub-hosted acceptance" in status
    assert "DEFERRED_SERVER_VERIFICATION" in status
    assert "server/DNS/ingress/real SMTP/production secrets/data/server Ollama remain frozen" in status


def test_migration_is_single_additive_25a_revision():
    migration = _text("migrations/versions/20260917_0033_ai_mlops_governance_evaluation_foundation.py")
    assert 'revision = "20260917_0033"' in migration
    assert 'down_revision = "20260916_0032"' in migration
    for table in (
        "core_ai_model_registrations",
        "core_ai_model_fallbacks",
        "core_ai_prompt_rollback_targets",
        "core_ai_evaluation_datasets",
        "core_ai_evaluation_runs",
        "core_ai_evaluation_results",
        "core_ai_evaluation_reviews",
    ):
        assert table in migration
    assert "DROP TABLE" not in migration.split("def downgrade", 1)[0].upper()
