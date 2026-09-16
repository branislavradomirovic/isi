import uuid
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domains.ordo.analytics_models import OrdoStatisticalModelContract
from src.domains.ordo.statistical_contracts import OrdoStatisticalModelContractV1, contract_fingerprint


def _contract(**changes):
    value = {
        "analysis_key": "demand-drivers", "purpose": "Specify non-causal aggregate associations.",
        "target_indicator_code": "arrivals", "target_methodology_id": uuid.UUID(int=1),
        "target_methodology_version": 2, "target_methodology_fingerprint": "a" * 64,
        "target_semantic": "count", "analysis_structure": "cross_sectional",
        "model_family": "poisson_glm", "response_family": "poisson",
        "features": [{"feature_key": "capacity", "role": "predictor", "source_field": "capacity", "version_identity": "capacity-v1", "transformation": "log1p", "missing_rule": "complete_case"}],
        "analysis_window_start": date(2024, 1, 1), "analysis_window_end": date(2025, 1, 1),
        "analysis_as_of": date(2025, 2, 1), "assumptions": ["Aggregate records."],
        "required_diagnostics": ["dispersion"], "limitations": ["No causal interpretation."],
        "non_causal": True, "automatic_policy_recommendation": False,
    }
    value.update(changes); return value


def test_statistical_family_target_compatibility_and_fingerprint():
    first = OrdoStatisticalModelContractV1.model_validate(_contract())
    second = OrdoStatisticalModelContractV1.model_validate(dict(reversed(list(_contract().items()))))
    assert contract_fingerprint(first) == contract_fingerprint(second)
    with pytest.raises(ValidationError):
        OrdoStatisticalModelContractV1.model_validate(_contract(model_family="linear_regression"))
    panel = OrdoStatisticalModelContractV1.model_validate(_contract(analysis_structure="panel", model_family="fixed_effects"))
    assert panel.response_family == "poisson"


def test_persistence_binds_methodology_run_and_has_no_result_entity():
    columns = OrdoStatisticalModelContract.__table__.columns
    for name in ("organization_id", "workspace_id", "analytics_run_id", "target_methodology_id", "target_methodology_version", "methodology_fingerprint", "input_snapshot_sha256", "contract_fingerprint"):
        assert name in columns
    models = Path("src/domains/ordo/analytics_models.py").read_text()
    assert "OrdoStatisticalModelResult" not in models
    for forbidden in ("statsmodels", "sklearn", "scipy", "prophet", "pmdarima"):
        assert forbidden not in Path("src/domains/ordo/statistical_contracts.py").read_text().lower()
