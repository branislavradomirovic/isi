from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401 - register FK targets
from src.core.database import Base
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import (
    SimpaAnalyticsError,
    create_methodology,
    propose_methodology,
    retire_methodology,
    run_methodology_reference_check,
    set_methodology_contract,
    validate_methodology,
)
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.identity.models import Membership, Organization, User


def _contract(unit: str = "count", tolerance: float = 0.0) -> dict:
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Reproduce an approved aggregate observation.",
        "interpretation": "The value is passed through without inference.",
        "unit": unit,
        "scale": "Aggregate local-system value.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric"],
        "eligible_aggregate_scope": "Organization/local system only.",
        "time_aggregation": "As reported for the governed period.",
        "geographic_aggregation": "Authorized aggregate geography.",
        "missing_data_rule": "Missing remains missing and is never zero-filled.",
        "suppression_privacy_rule": "Suppress data below the approved aggregate boundary.",
        "quality_preconditions": "quality_status must be validated.",
        "reference_dataset": "ISI-23A compact direct-observation reference fixture.",
        "accepted_tolerance": tolerance,
        "limitations": "Descriptive and non-causal; no person-level decision use.",
        "non_causal": True,
    }


@pytest.fixture
def methodology_case():
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


def _new(db, membership, indicator, *, contract=None):
    return create_methodology(
        db,
        indicator_code=indicator.code,
        computation_type="direct_observation",
        methodology_note="Human-authored aggregate method.",
        source_requirements={},
        computation_spec=contract if contract is not None else _contract(),
        actor_id=membership.id,
    )


def _pass_reference(db, row, indicator, *, value=10, expected=10):
    return run_methodology_reference_check(
        db,
        methodology_id=row.id,
        reference_record={
            "indicator_code": indicator.code,
            "quality_status": "validated",
            "value_numeric": value,
            "value_text": "",
        },
        expected_result={"value_numeric": expected, "value_text": ""},
    )


def test_new_draft_proposes_but_cannot_validate_directly(methodology_case):
    db, membership, indicator = methodology_case
    row = _new(db, membership, indicator)
    assert row.status == "draft"
    assert row.reference_check_status == "not_run"
    assert indicator.methodology_status == "draft"
    with pytest.raises(SimpaAnalyticsError, match="methodology_transition_forbidden"):
        validate_methodology(
            db,
            methodology_id=row.id,
            validation_note="Human approval note",
            actor_id=membership.id,
        )
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    assert row.status == "proposed"
    assert row.proposed_by_membership_id == membership.id
    assert row.proposed_at is not None
    assert indicator.methodology_status == "proposed"


def test_proposed_requires_passed_reference_before_human_validation(methodology_case):
    db, membership, indicator = methodology_case
    row = _new(db, membership, indicator)
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_check_required"):
        validate_methodology(
            db,
            methodology_id=row.id,
            validation_note="Human approval note",
            actor_id=membership.id,
        )
    _pass_reference(db, row, indicator, value="10.04", expected=10)
    assert row.reference_check_status == "failed"
    assert len(row.reference_check_fingerprint) == 64
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_check_required"):
        validate_methodology(
            db,
            methodology_id=row.id,
            validation_note="Human approval note",
            actor_id=membership.id,
        )
    with pytest.raises(SimpaAnalyticsError, match="methodology_reference_check_failed"):
        _pass_reference(db, row, indicator)


def test_reference_pass_validation_and_predecessor_retirement(methodology_case):
    db, membership, indicator = methodology_case
    predecessor = SimpaIndicatorMethodology(
        indicator_id=indicator.id,
        version_no=1,
        status="validated",
        computation_type="direct_observation",
        computation_spec={},
        contract_fingerprint="",
        source_requirements={},
        methodology_note="Legacy",
        validation_note="Historical approval",
        reference_check_status="legacy_unknown",
    )
    db.add(predecessor)
    db.flush()
    indicator.methodology_status = "validated"
    successor = _new(db, membership, indicator)
    assert indicator.methodology_status == "validated"
    propose_methodology(db, methodology_id=successor.id, actor_id=membership.id)
    assert indicator.methodology_status == "validated"
    _pass_reference(db, successor, indicator)
    validate_methodology(
        db,
        methodology_id=successor.id,
        validation_note="Approved after deterministic reference evidence.",
        actor_id=membership.id,
    )
    assert successor.status == "validated"
    assert successor.approved_by_membership_id == membership.id
    assert successor.approved_at is not None
    assert predecessor.status == "retired"
    assert predecessor.retired_by_membership_id == membership.id
    assert predecessor.retired_at is not None
    assert "Superseded" in predecessor.retirement_note
    assert indicator.methodology_status == "validated"


def test_explicit_retirement_never_reactivates_and_summary_is_deterministic(methodology_case):
    db, membership, indicator = methodology_case
    first = _new(db, membership, indicator)
    second = _new(db, membership, indicator)
    propose_methodology(db, methodology_id=second.id, actor_id=membership.id)
    assert indicator.methodology_status == "proposed"
    retire_methodology(
        db,
        methodology_id=second.id,
        retirement_note="Withdrawn after review.",
        actor_id=membership.id,
    )
    assert indicator.methodology_status == "draft"
    retire_methodology(
        db,
        methodology_id=first.id,
        retirement_note="No longer pursued.",
        actor_id=membership.id,
    )
    assert indicator.methodology_status == "retired"
    with pytest.raises(SimpaAnalyticsError, match="methodology_transition_forbidden"):
        propose_methodology(db, methodology_id=first.id, actor_id=membership.id)
    with pytest.raises(SimpaAnalyticsError, match="methodology_transition_forbidden"):
        retire_methodology(
            db,
            methodology_id=first.id,
            retirement_note="Again",
            actor_id=membership.id,
        )


def test_historical_conceptual_indicator_is_not_rewritten(methodology_case):
    db, _membership, indicator = methodology_case
    assert db.get(SimpaIndicatorDefinition, indicator.id).methodology_status == "conceptual"


def test_contract_is_immutable_after_proposal(methodology_case):
    db, membership, indicator = methodology_case
    row = _new(db, membership, indicator)
    propose_methodology(db, methodology_id=row.id, actor_id=membership.id)
    changed = _contract()
    changed["purpose"] = "A changed purpose requires a new version."
    with pytest.raises(SimpaAnalyticsError, match="methodology_contract_immutable"):
        set_methodology_contract(db, methodology_id=row.id, computation_spec=changed)


def test_api_exposes_explicit_managed_lifecycle_actions_and_safe_trace():
    routes = Path("src/api/simpa_analytics_routes.py").read_text()
    for endpoint in ("/propose", "/reference-check", "/retire", "/validate"):
        assert f'methodology_id}}{endpoint}"' in routes
    for field in (
        "contract_fingerprint",
        "reference_check_status",
        "reference_check_fingerprint",
        "proposed_at",
        "approved_at",
        "validation_note",
        "retired_at",
        "retirement_note",
    ):
        assert f'"{field}"' in routes
    assert routes.count('permission_code="indicator.manage"') >= 5
