from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401 - register FK targets
from src.core.database import Base
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import (
    SimpaAnalyticsError,
    create_methodology,
    create_methodology_reference_suite,
    list_methodology_reference_suites,
    propose_methodology,
    run_methodology_reference_check,
    run_methodology_reference_suite,
    validate_methodology,
)
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.identity.models import Membership, Organization, User


def _contract(tolerance: float = 0.05) -> dict:
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Reproduce approved aggregate observations.",
        "interpretation": "The observed aggregate value passes through without inference.",
        "unit": "count",
        "scale": "Aggregate local-system value.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric", "value_text"],
        "eligible_aggregate_scope": "Organization/local system only.",
        "time_aggregation": "As reported for the governed period.",
        "geographic_aggregation": "Authorized aggregate geography.",
        "missing_data_rule": "Missing remains missing and is never zero-filled.",
        "suppression_privacy_rule": "Suppress data below the approved aggregate boundary.",
        "quality_preconditions": "quality_status must be validated.",
        "reference_dataset": "ISI-23B deterministic reference suite.",
        "accepted_tolerance": tolerance,
        "limitations": "Descriptive and non-causal; no person-level decision use.",
        "non_causal": True,
    }


@pytest.fixture
def suite_case():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        user = User(email=f"{marker}@example.test", display_name="Reviewer")
        organization = Organization(slug=f"org-{marker}", name="Test organization")
        db.add_all([user, organization])
        db.flush()
        membership = Membership(user_id=user.id, organization_id=organization.id)
        dimension = SimpaDimension(code=f"DIM_{marker}", name_sr="Test")
        db.add_all([membership, dimension])
        db.flush()
        indicator = SimpaIndicatorDefinition(
            code=f"IND_{marker}",
            name_sr="Test indicator",
            dimension_code=dimension.code,
            unit_hint="count",
            methodology_status="conceptual",
            methodology_note="",
        )
        db.add(indicator)
        db.flush()
        yield db, membership, indicator


def _new(db, membership, indicator):
    return create_methodology(
        db,
        indicator_code=indicator.code,
        computation_type="direct_observation",
        methodology_note="Human-authored aggregate method.",
        source_requirements={},
        computation_spec=_contract(),
        actor_id=membership.id,
    )


def _cases(indicator, *, numeric_actual=10.04, numeric_expected=10):
    return [
        {
            "case_key": "numeric",
            "reference_record": {
                "indicator_code": indicator.code,
                "quality_status": "validated",
                "value_numeric": numeric_actual,
                "value_text": None,
            },
            "expected_result": {"value_numeric": numeric_expected, "value_text": None},
        },
        {
            "case_key": "text",
            "reference_record": {
                "indicator_code": indicator.code,
                "quality_status": "validated",
                "value_numeric": None,
                "value_text": " Ready ",
            },
            "expected_result": {"value_numeric": None, "value_text": "Ready"},
        },
    ]


def _create_and_run(db, membership, indicator, row, *, version="v1", cases=None):
    suite = create_methodology_reference_suite(
        db,
        methodology_id=row.id,
        reference_dataset_version=version,
        cases=cases or _cases(indicator),
        actor_id=membership.id,
    )
    run_methodology_reference_suite(
        db,
        methodology_id=row.id,
        suite_id=suite.id,
        actor_id=membership.id,
    )
    return suite


def test_new_methodology_defaults_to_suite_v1_and_inline_is_compatibility_only(suite_case):
    db, membership, indicator = suite_case
    row = _new(db, membership, indicator)
    assert row.reference_evidence_mode == "suite_v1"
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_required"):
        run_methodology_reference_check(
            db,
            methodology_id=row.id,
            reference_record={"indicator_code": indicator.code, "quality_status": "validated", "value_numeric": 1},
            expected_result={"value_numeric": 1},
        )


def test_suite_is_proposed_only_all_cases_execute_and_human_validation_retires_predecessor(suite_case):
    db, membership, indicator = suite_case
    predecessor = SimpaIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=1,
        status="validated",
        computation_type="direct_observation",
        computation_spec={},
        contract_fingerprint="",
        source_requirements={},
        methodology_note="Historical",
        validation_note="Historical approval",
        reference_check_status="legacy_unknown",
        reference_evidence_mode="legacy_unknown",
    )
    db.add(predecessor)
    db.flush()
    indicator.methodology_status = "validated"
    row = _new(db, membership, indicator)
    with pytest.raises(SimpaAnalyticsError, match="methodology_not_proposed"):
        create_methodology_reference_suite(
            db,
            methodology_id=row.id,
            reference_dataset_version="v1",
            cases=_cases(indicator),
            actor_id=membership.id,
        )
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    suite = _create_and_run(db, membership, indicator, row)
    assert suite.status == "passed"
    assert len(suite.suite_fingerprint) == len(suite.result_fingerprint) == 64
    persisted = list_methodology_reference_suites(db, methodology_id=row.id)
    assert [case.case_key for case in persisted[0][1]] == ["numeric", "text"]
    assert all(case.status == "passed" and len(case.result_fingerprint) == 64 for case in persisted[0][1])
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_terminal"):
        run_methodology_reference_suite(db, methodology_id=row.id, suite_id=suite.id, actor_id=membership.id)
    validate_methodology(
        db,
        methodology_id=row.id,
        validation_note="Human approval after every reference case passed.",
        actor_id=membership.id,
    )
    assert row.status == "validated"
    assert row.approved_by_membership_id == membership.id
    assert predecessor.status == "retired"


def test_failed_suite_allows_new_version_and_passed_suite_blocks_competitor(suite_case):
    db, membership, indicator = suite_case
    row = _new(db, membership, indicator)
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    failed = _create_and_run(
        db,
        membership,
        indicator,
        row,
        version="v1",
        cases=_cases(indicator, numeric_actual=11, numeric_expected=10),
    )
    assert failed.status == "failed"
    recovered = _create_and_run(db, membership, indicator, row, version="v2")
    assert recovered.version_no == 2
    assert recovered.status == "passed"
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_already_passed"):
        create_methodology_reference_suite(
            db,
            methodology_id=row.id,
            reference_dataset_version="v3",
            cases=_cases(indicator),
            actor_id=membership.id,
        )


def test_validation_recomputes_and_detects_case_or_result_tampering(suite_case):
    db, membership, indicator = suite_case
    row = _new(db, membership, indicator)
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    suite = _create_and_run(db, membership, indicator, row)
    cases = list_methodology_reference_suites(db, methodology_id=row.id)[0][1]
    cases[0].result_detail = {**cases[0].result_detail, "passed": False}
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_evidence_invalid"):
        validate_methodology(
            db,
            methodology_id=row.id,
            validation_note="Human approval must not accept tampering.",
            actor_id=membership.id,
        )
    assert suite.status == "passed"
    assert row.status == "proposed"
