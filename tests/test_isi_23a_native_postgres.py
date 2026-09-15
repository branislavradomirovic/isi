from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.domains.simpa.analytics_models import SimpaIndicatorMethodology
from src.domains.simpa.analytics_service import (
    create_methodology,
    propose_methodology,
    run_methodology_reference_check,
    validate_methodology,
)
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.platform.identity.models import Membership, Organization, User


pytestmark = pytest.mark.skipif(
    os.getenv("ISI_NATIVE_POSTGRES_TEST") != "1",
    reason="native PostgreSQL acceptance only",
)


def _contract() -> dict:
    return {
        "schema_version": "SIMPA-METHODOLOGY-CONTRACT-v1",
        "computation_type": "direct_observation",
        "purpose": "Native aggregate pass-through test.",
        "interpretation": "Descriptive observation only.",
        "unit": "count",
        "scale": "Aggregate.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric"],
        "eligible_aggregate_scope": "Organization/local system.",
        "time_aggregation": "Reported period.",
        "geographic_aggregation": "Approved aggregate geography.",
        "missing_data_rule": "Preserve missing.",
        "suppression_privacy_rule": "Suppress disallowed granularity.",
        "quality_preconditions": "Validated evidence.",
        "reference_dataset": "ISI-23A native compact fixture.",
        "accepted_tolerance": 0.0,
        "limitations": "Non-causal and not person-level.",
        "non_causal": True,
    }


def test_native_postgres_0027_schema_constraints_and_foreign_keys():
    inspector = inspect(build_engine())
    columns = {item["name"] for item in inspector.get_columns("simpa_indicator_methodologies")}
    assert {
        "contract_fingerprint",
        "proposed_by_membership_id",
        "proposed_at",
        "reference_check_status",
        "reference_check_fingerprint",
        "reference_check_detail",
        "retired_by_membership_id",
        "retired_at",
        "retirement_note",
    } <= columns
    checks = {
        item["name"]: item["sqltext"] for item in inspector.get_check_constraints("simpa_indicator_methodologies")
    }
    assert "proposed" in checks["ck_simpa_indicator_methodology_status"]
    assert "legacy_unknown" in checks["ck_simpa_methodology_reference_status"]
    fk_columns = {
        tuple(item["constrained_columns"]): item["referred_table"]
        for item in inspector.get_foreign_keys("simpa_indicator_methodologies")
    }
    assert fk_columns[("proposed_by_membership_id",)] == "core_memberships"
    assert fk_columns[("retired_by_membership_id",)] == "core_memberships"
    indicator_check = {
        item["name"]: item["sqltext"] for item in inspector.get_check_constraints("simpa_indicator_definitions")
    }
    assert "proposed" in indicator_check["ck_simpa_indicator_methodology_status"]


def test_native_postgres_legacy_validated_compatibility_and_new_trace_persistence():
    engine = build_engine()
    connection = engine.connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        marker = uuid.uuid4().hex
        user = User(email=f"isi23a-{marker}@example.test", display_name="ISI-23A")
        organization = Organization(slug=f"isi23a-{marker}", name="ISI-23A")
        db.add_all([user, organization])
        db.flush()
        membership = Membership(user_id=user.id, organization_id=organization.id)
        dimension = SimpaDimension(code=f"ISI23A_{marker}", name_sr="ISI-23A")
        db.add_all([membership, dimension])
        db.flush()
        indicator = SimpaIndicatorDefinition(
            code=f"ISI23A_IND_{marker}",
            name_sr="ISI-23A",
            dimension_code=dimension.code,
            unit_hint="count",
            methodology_status="validated",
            methodology_note="Historical",
        )
        db.add(indicator)
        db.flush()
        legacy = SimpaIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=1,
            status="validated",
            computation_type="direct_observation",
            computation_spec={},
            contract_fingerprint="",
            source_requirements={},
            methodology_note="Historical",
            validation_note="Historical human approval",
            reference_check_status="legacy_unknown",
            reference_check_fingerprint="",
            reference_check_detail={},
            reference_evidence_mode="legacy_unknown",
        )
        db.add(legacy)
        db.flush()
        assert legacy.status == "validated"
        assert legacy.reference_check_status == "legacy_unknown"

        candidate = create_methodology(
            db,
            indicator_code=indicator.code,
            computation_type="direct_observation",
            methodology_note="New governed version",
            source_requirements={},
            computation_spec=_contract(),
            actor_id=membership.id,
        )
        # Emulate a persisted 23A row that migration 0028 classified as historical inline evidence.
        candidate.reference_evidence_mode = "legacy_inline"
        assert indicator.methodology_status == "validated"
        propose_methodology(db, methodology_id=candidate.id, actor_id=membership.id)
        run_methodology_reference_check(
            db,
            methodology_id=candidate.id,
            reference_record={
                "indicator_code": indicator.code,
                "quality_status": "validated",
                "value_numeric": 12,
                "value_text": "",
            },
            expected_result={"value_numeric": 12, "value_text": ""},
        )
        validate_methodology(
            db,
            methodology_id=candidate.id,
            validation_note="Native human approval after reference pass.",
            actor_id=membership.id,
        )
        db.flush()
        assert len(candidate.contract_fingerprint) == 64
        assert candidate.reference_check_status == "passed"
        assert len(candidate.reference_check_fingerprint) == 64
        assert candidate.proposed_by_membership_id == membership.id
        assert candidate.approved_by_membership_id == membership.id
        assert legacy.status == "retired"
        assert legacy.retired_by_membership_id == membership.id
    finally:
        transaction.rollback()
        connection.close()
