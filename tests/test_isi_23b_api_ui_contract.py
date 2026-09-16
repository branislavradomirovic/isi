from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.domains.simpa.analytics_schemas import MethodologyReferenceSuiteCreateRequest


ROUTES = Path("src/api/simpa_analytics_routes.py")
API = Path("src/streamlit_app/simpa_analytics_api.py")
UI = Path("src/streamlit_app/simpa_analytics_workspace.py")
HELP_MATRIX = Path("docs/help/ISI-HELP-COVERAGE-MATRIX.md")
USER_GUIDE = Path("docs/help/SIMPA-USER-GUIDE.md")


def _payload():
    return {
        "organization_id": str(uuid.uuid4()),
        "workspace_id": str(uuid.uuid4()),
        "reference_dataset_version": "v1",
        "cases": [
            {
                "case_key": "numeric",
                "reference_record": {
                    "indicator_code": "SIMPA.TEST",
                    "quality_status": "validated",
                    "value_numeric": 1,
                    "value_text": None,
                },
                "expected_result": {"value_numeric": 1, "value_text": None},
            }
        ],
    }


def test_reference_suite_request_is_strict_and_case_keys_are_unique():
    assert MethodologyReferenceSuiteCreateRequest.model_validate(_payload()).cases[0].case_key == "numeric"
    extra = _payload()
    extra["unexpected"] = True
    with pytest.raises(ValidationError):
        MethodologyReferenceSuiteCreateRequest.model_validate(extra)
    duplicate = _payload()
    duplicate["cases"] *= 2
    with pytest.raises(ValidationError, match="unique"):
        MethodologyReferenceSuiteCreateRequest.model_validate(duplicate)
    blank_version = _payload()
    blank_version["reference_dataset_version"] = " "
    with pytest.raises(ValidationError):
        MethodologyReferenceSuiteCreateRequest.model_validate(blank_version)


def test_api_exposes_create_run_and_read_routes_with_locked_permissions_and_provenance():
    text = ROUTES.read_text()
    assert '@router.post("/methodologies/{methodology_id}/reference-suites"' in text
    assert '@router.post("/methodologies/{methodology_id}/reference-suites/{suite_id}/run")' in text
    assert '@router.get("/methodologies/{methodology_id}/reference-suites")' in text
    create_start = text.index("def post_methodology_reference_suite(")
    run_start = text.index("def post_run_methodology_reference_suite(")
    validate_start = text.index('@router.post("/methodologies/{methodology_id}/validate")')
    assert 'permission_code="indicator.manage"' in text[create_start:run_start]
    assert 'permission_code="indicator.manage"' in text[run_start:validate_start]
    get_start = text.index("def get_methodology_reference_suites(")
    assert 'permission_code="analysis.read"' in text[get_start:create_start]
    for field in (
        "reference_evidence_mode",
        "reference_dataset_version",
        "suite_fingerprint",
        "result_fingerprint",
        "case_fingerprint",
        "created_by_membership_id",
        "executed_by_membership_id",
    ):
        assert f'"{field}"' in text


def test_streamlit_client_and_ui_expose_suite_case_provenance_without_false_approval():
    api = API.read_text()
    ui = UI.read_text()
    for function in ("reference_suites", "create_reference_suite", "run_reference_suite"):
        assert f"def {function}(" in api
    for field in (
        'item.get("reference_evidence_mode")',
        'suite.get("reference_dataset_version")',
        'suite.get("suite_fingerprint")',
        'suite.get("result_fingerprint")',
        'suite.get("case_count")',
        'case.get("case_fingerprint")',
        'case.get("result_fingerprint")',
    ):
        assert field in ui
    assert "PASSED reference suite nije institucionalno odobrenje" in ui
    assert "PROPOSED ostaje različit od VALIDATED" in ui


def test_masterplan_preserves_23b_scope_without_freezing_later_help_state():
    master = Path("docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md").read_text()
    for row_id in ("INV-A11", "INV-B18", "INV-C26", "INV-C31", "INV-M07"):
        assert f"| {row_id} |" in master
    assert "tests/test_isi_23b*.py" in master
    assert "Accepted ISI-23B as-built boundary" in master
    assert "ISI-25 evaluation-set/model-promotion scope" in master
    matrix = HELP_MATRIX.read_text()
    help_row = next(line for line in matrix.splitlines() if line.startswith("| INV-A18 |"))
    assert "| VERIFIED |" in help_row
    assert USER_GUIDE.is_file()
