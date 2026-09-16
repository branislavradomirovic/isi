from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domains.simpa.analytics_schemas import (
    StatisticalModelContractCreateRequest,
    StatisticalModelRunRequest,
)


ROUTES = Path("src/api/simpa_analytics_routes.py")
CLIENT = Path("src/streamlit_app/simpa_analytics_api.py")
UI = Path("src/streamlit_app/simpa_analytics_workspace.py")
SERVICE = Path("src/domains/simpa/analytics_service.py")


def _create_payload():
    return {
        "organization_id": str(uuid.uuid4()),
        "workspace_id": str(uuid.uuid4()),
        "indicator_code": "SIMPA.TEST",
        "analysis_key": "association",
        "target_semantic": "continuous",
        "model_family": "ols",
        "feature_fields": ["capacity"],
        "confidence_level": 0.95,
        "covariance_type": "HC3",
        "purpose": "Aggregate association.",
        "limitations": "Non-causal.",
    }


def test_new_request_schemas_are_strict_and_no_threshold_formula_or_weight_is_accepted():
    assert StatisticalModelContractCreateRequest.model_validate(_create_payload()).analysis_key == "association"
    for field in ("formula", "weight", "threshold", "predicted_class_threshold"):
        payload = _create_payload()
        payload[field] = 0.5
        with pytest.raises(ValidationError):
            StatisticalModelContractCreateRequest.model_validate(payload)
    run = {
        "organization_id": str(uuid.uuid4()),
        "workspace_id": str(uuid.uuid4()),
        "analytics_run_id": str(uuid.uuid4()),
        "statistical_model_contract_id": str(uuid.uuid4()),
        "controlled_testing_ack": True,
    }
    assert StatisticalModelRunRequest.model_validate(run).controlled_testing_ack is True
    with pytest.raises(ValidationError):
        StatisticalModelRunRequest.model_validate({**run, "extra": True})


def test_api_exposes_locked_read_lifecycle_and_execution_permission_boundaries():
    text = ROUTES.read_text()
    for endpoint in (
        '@router.get("/statistical-model-contracts")',
        '@router.get("/statistical-model-results")',
        '@router.post("/statistical-model-contracts"',
        '@router.post("/statistical-model-contracts/{contract_id}/propose")',
        '@router.post("/statistical-model-contracts/{contract_id}/validate")',
        '@router.post("/statistical-model-contracts/{contract_id}/retire")',
        '@router.post("/statistical-model-results/run"',
    ):
        assert endpoint in text
    contracts_get = text.index("def get_statistical_model_contracts(")
    contracts_post = text.index("def post_statistical_model_contract(")
    results_get = text.index("def get_statistical_model_results(")
    results_run = text.index("def post_run_statistical_model(")
    assert 'permission_code="analysis.read"' in text[contracts_get:contracts_post]
    assert text[contracts_post:results_get].count('permission_code="indicator.manage"') == 4
    assert 'permission_code="analysis.read"' in text[results_get:results_run]
    assert 'permission_code="analysis.run"' in text[results_run:]
    for field in (
        "target_methodology_contract_fingerprint",
        "validation_evidence_reference",
        "result_fingerprint",
        "production_eligible",
        "statsmodels_version",
    ):
        assert f'"{field}"' in text


def test_streamlit_client_and_ui_preserve_evidence_first_noncausal_contract():
    client = CLIENT.read_text()
    ui = UI.read_text()
    for function in (
        "statistical_model_contracts",
        "create_statistical_model_contract",
        "propose_statistical_model_contract",
        "validate_statistical_model_contract",
        "retire_statistical_model_contract",
        "statistical_model_results",
        "run_statistical_model",
    ):
        assert f"def {function}(" in client
    statistical = ui.index('st.markdown("### Statistički metodološki ugovori i rezultati")')
    ai = ui.index('st.markdown("### Lokalna AI podržana sinteza")')
    assert statistical < ai
    section = ui[statistical:ai]
    for text in (
        "PROPOSED = samo kontrolisano testiranje",
        "controlled_testing_ack",
        "production_eligible",
        "coefficients",
        "metrics",
        "diagnostics",
        "calibration",
        "result_fingerprint",
        "does not by itself establish causal effect",
    ):
        assert text in section
    assert "predicted_class" not in section
    assert "risk_label" not in section


def test_statistical_outputs_are_not_added_to_existing_ai_synthesis_input():
    service = SERVICE.read_text()
    start = service.index("def _synthesis_input(")
    end = service.index("def create_synthesis(", start)
    synthesis = service[start:end]
    assert "statistical" not in synthesis.casefold()
    assert "evidence-quality state" in synthesis


def test_masterplan_inventory_is_synchronized_while_isi25_scope_remains_open():
    master = Path("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    for row_id in ("INV-A11", "INV-B18", "INV-C26", "INV-C32", "INV-M07"):
        assert f"| {row_id} |" in master
    assert "tests/test_isi_23c*.py" in master
    assert "ISI-23C R1 implementation boundary" in master
    assert "champion/evaluation/promotion" in master
    assert "whole ISI-23 phase remains in progress" in master
