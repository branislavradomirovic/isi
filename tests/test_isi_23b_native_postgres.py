from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.domains.simpa.analytics_models import (
    SimpaIndicatorMethodology,
    SimpaMethodologyReferenceCase,
    SimpaMethodologyReferenceSuite,
)
from src.domains.simpa.analytics_service import (
    SimpaAnalyticsError,
    create_methodology,
    create_methodology_reference_suite,
    propose_methodology,
    run_methodology_reference_suite,
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
        "purpose": "Native aggregate pass-through suite.",
        "interpretation": "Descriptive observation only.",
        "unit": "count",
        "scale": "Aggregate.",
        "required_source_fields": ["indicator_code", "quality_status", "value_numeric", "value_text"],
        "eligible_aggregate_scope": "Organization/local system.",
        "time_aggregation": "Reported period.",
        "geographic_aggregation": "Approved aggregate geography.",
        "missing_data_rule": "Preserve missing.",
        "suppression_privacy_rule": "Suppress disallowed granularity.",
        "quality_preconditions": "Validated evidence.",
        "reference_dataset": "ISI-23B native suite fixture.",
        "accepted_tolerance": 0.05,
        "limitations": "Non-causal and not person-level.",
        "non_causal": True,
    }


def _seed(db: Session, label: str) -> tuple[Membership, SimpaIndicatorDefinition]:
    marker = uuid.uuid4().hex
    user = User(email=f"isi23b-{label}-{marker}@example.test", display_name="ISI-23B")
    organization = Organization(slug=f"isi23b-{label}-{marker}", name="ISI-23B")
    db.add_all([user, organization])
    db.flush()
    membership = Membership(user_id=user.id, organization_id=organization.id)
    dimension = SimpaDimension(code=f"ISI23B_{label}_{marker}", name_sr="ISI-23B")
    db.add_all([membership, dimension])
    db.flush()
    indicator = SimpaIndicatorDefinition(
        code=f"ISI23B_IND_{label}_{marker}",
        name_sr="ISI-23B",
        dimension_code=dimension.code,
        unit_hint="count",
        methodology_status="conceptual",
        methodology_note="",
    )
    db.add(indicator)
    db.flush()
    return membership, indicator


def _new_methodology(
    db: Session, membership: Membership, indicator: SimpaIndicatorDefinition
) -> SimpaIndicatorMethodology:
    methodology = create_methodology(
        db,
        indicator_code=indicator.code,
        computation_type="direct_observation",
        methodology_note="Native suite methodology",
        source_requirements={},
        computation_spec=_contract(),
        actor_id=membership.id,
    )
    propose_methodology(db, methodology_id=methodology.id, actor_id=membership.id)
    return methodology


def _cases(indicator: SimpaIndicatorDefinition, *, numeric_actual: float = 12.04) -> list[dict]:
    return [
        {
            "case_key": "numeric-dual",
            "reference_record": {
                "indicator_code": indicator.code,
                "quality_status": "validated",
                "value_numeric": numeric_actual,
                "value_text": "Preserved evidence",
            },
            "expected_result": {"value_numeric": 12},
        },
        {
            "case_key": "text-dual",
            "reference_record": {
                "indicator_code": indicator.code,
                "quality_status": "validated",
                "value_numeric": 99,
                "value_text": " Ready ",
            },
            "expected_result": {"value_text": "Ready"},
        },
    ]


def test_native_postgres_0028_schema_constraints_indexes_and_foreign_keys():
    inspector = inspect(build_engine())
    methodology_columns = {item["name"] for item in inspector.get_columns("simpa_indicator_methodologies")}
    assert "reference_evidence_mode" in methodology_columns
    methodology_checks = {
        item["name"]: item["sqltext"] for item in inspector.get_check_constraints("simpa_indicator_methodologies")
    }
    assert "legacy_unknown" in methodology_checks["ck_simpa_methodology_reference_evidence_mode"]
    assert "legacy_inline" in methodology_checks["ck_simpa_methodology_reference_evidence_mode"]
    assert "suite_v1" in methodology_checks["ck_simpa_methodology_reference_evidence_mode"]

    assert {
        "simpa_methodology_reference_suites",
        "simpa_methodology_reference_cases",
    } <= set(inspector.get_table_names())
    suite_columns = {item["name"] for item in inspector.get_columns("simpa_methodology_reference_suites")}
    assert {
        "methodology_contract_fingerprint",
        "reference_dataset_version",
        "suite_fingerprint",
        "result_fingerprint",
        "created_by_membership_id",
        "executed_by_membership_id",
    } <= suite_columns
    suite_checks = {item["name"] for item in inspector.get_check_constraints("simpa_methodology_reference_suites")}
    assert {
        "ck_simpa_reference_suite_schema_version",
        "ck_simpa_reference_suite_contract_fingerprint",
        "ck_simpa_reference_suite_fingerprint",
        "ck_simpa_reference_suite_status",
        "ck_simpa_reference_suite_terminal",
    } <= suite_checks
    suite_uniques = {
        tuple(item["column_names"]) for item in inspector.get_unique_constraints("simpa_methodology_reference_suites")
    }
    assert {("methodology_id", "version_no"), ("methodology_id", "suite_fingerprint")} <= suite_uniques
    case_uniques = {
        tuple(item["column_names"]) for item in inspector.get_unique_constraints("simpa_methodology_reference_cases")
    }
    assert {("suite_id", "case_key"), ("suite_id", "case_index")} <= case_uniques
    suite_fks = {
        tuple(item["constrained_columns"]): (item["referred_table"], item["options"].get("ondelete"))
        for item in inspector.get_foreign_keys("simpa_methodology_reference_suites")
    }
    assert suite_fks["methodology_id",] == ("simpa_indicator_methodologies", "CASCADE")
    assert suite_fks["created_by_membership_id",] == ("core_memberships", "SET NULL")
    assert suite_fks["executed_by_membership_id",] == ("core_memberships", "SET NULL")
    case_fks = {
        tuple(item["constrained_columns"]): (item["referred_table"], item["options"].get("ondelete"))
        for item in inspector.get_foreign_keys("simpa_methodology_reference_cases")
    }
    assert case_fks["suite_id",] == ("simpa_methodology_reference_suites", "CASCADE")
    assert "ix_simpa_reference_suite_methodology_status" in {
        item["name"] for item in inspector.get_indexes("simpa_methodology_reference_suites")
    }
    assert "ix_simpa_reference_case_suite" in {
        item["name"] for item in inspector.get_indexes("simpa_methodology_reference_cases")
    }


def test_native_postgres_legacy_modes_remain_representable_without_fabricated_suites():
    connection = build_engine().connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        _membership, indicator = _seed(db, "legacy")
        legacy_unknown = SimpaIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=1,
            status="retired",
            computation_type="direct_observation",
            computation_spec={},
            contract_fingerprint="",
            source_requirements={},
            methodology_note="Historical unknown evidence",
            reference_check_status="legacy_unknown",
            reference_check_fingerprint="",
            reference_check_detail={},
            reference_evidence_mode="legacy_unknown",
        )
        legacy_inline = SimpaIndicatorMethodology(
            indicator_id=indicator.id,
            version_no=2,
            status="retired",
            computation_type="direct_observation",
            computation_spec={},
            contract_fingerprint="",
            source_requirements={},
            methodology_note="Historical inline evidence",
            reference_check_status="not_run",
            reference_check_fingerprint="",
            reference_check_detail={},
            reference_evidence_mode="legacy_inline",
        )
        db.add_all([legacy_unknown, legacy_inline])
        db.flush()
        db.expire_all()
        assert db.get(SimpaIndicatorMethodology, legacy_unknown.id).reference_evidence_mode == "legacy_unknown"
        assert db.get(SimpaIndicatorMethodology, legacy_inline.id).reference_evidence_mode == "legacy_inline"
        assert (
            db.scalar(
                select(func.count())
                .select_from(SimpaMethodologyReferenceSuite)
                .where(SimpaMethodologyReferenceSuite.methodology_id.in_([legacy_unknown.id, legacy_inline.id]))
            )
            == 0
        )
    finally:
        transaction.rollback()
        connection.close()


def test_native_postgres_passed_suite_reload_fingerprints_tamper_gate_and_human_validation():
    connection = build_engine().connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        membership, indicator = _seed(db, "passed")
        methodology = _new_methodology(db, membership, indicator)
        with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_required"):
            validate_methodology(
                db,
                methodology_id=methodology.id,
                validation_note="Human validation is premature.",
                actor_id=membership.id,
            )
        suite = create_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            reference_dataset_version="native-v1",
            cases=_cases(indicator),
            actor_id=membership.id,
        )
        run_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            suite_id=suite.id,
            actor_id=membership.id,
        )
        db.flush()
        methodology_id, suite_id = methodology.id, suite.id
        db.expire_all()
        persisted_suite = db.get(SimpaMethodologyReferenceSuite, suite_id)
        persisted_cases = list(
            db.scalars(
                select(SimpaMethodologyReferenceCase)
                .where(SimpaMethodologyReferenceCase.suite_id == suite_id)
                .order_by(SimpaMethodologyReferenceCase.case_index)
            ).all()
        )
        assert persisted_suite is not None and persisted_suite.status == "passed"
        assert len(persisted_suite.suite_fingerprint) == len(persisted_suite.result_fingerprint) == 64
        assert persisted_suite.created_by_membership_id == membership.id
        assert persisted_suite.executed_by_membership_id == membership.id
        assert persisted_suite.executed_at is not None
        assert [case.status for case in persisted_cases] == ["passed", "passed"]
        assert all(len(case.case_fingerprint) == len(case.result_fingerprint) == 64 for case in persisted_cases)
        assert persisted_cases[0].reference_record == {
            "indicator_code": indicator.code,
            "quality_status": "validated",
            "value_numeric": 12.04,
            "value_text": "Preserved evidence",
        }

        original_expected = dict(persisted_cases[0].expected_result)
        persisted_cases[0].expected_result = {"value_numeric": 13.0, "value_text": ""}
        db.flush()
        with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_evidence_invalid"):
            validate_methodology(
                db,
                methodology_id=methodology_id,
                validation_note="Human approval must reject persisted tampering.",
                actor_id=membership.id,
            )
        persisted_cases[0].expected_result = original_expected
        db.flush()
        with pytest.raises(SimpaAnalyticsError, match="methodology_actor_required"):
            validate_methodology(
                db,
                methodology_id=methodology_id,
                validation_note="A note without a human actor is insufficient.",
                actor_id=None,
            )
        with pytest.raises(SimpaAnalyticsError, match="validation_note_required"):
            validate_methodology(
                db,
                methodology_id=methodology_id,
                validation_note=" ",
                actor_id=membership.id,
            )
        validated = validate_methodology(
            db,
            methodology_id=methodology_id,
            validation_note="Native human approval after intact persisted reference evidence.",
            actor_id=membership.id,
        )
        db.flush()
        assert validated.status == "validated"
        assert validated.approved_by_membership_id == membership.id
        assert validated.approved_at is not None
    finally:
        transaction.rollback()
        connection.close()


def test_native_postgres_failed_suite_is_terminal_and_new_version_can_recover_while_proposed():
    connection = build_engine().connect()
    transaction = connection.begin()
    try:
        db = Session(bind=connection)
        membership, indicator = _seed(db, "failed")
        methodology = _new_methodology(db, membership, indicator)
        failed = create_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            reference_dataset_version="native-failed-v1",
            cases=_cases(indicator, numeric_actual=13),
            actor_id=membership.id,
        )
        run_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            suite_id=failed.id,
            actor_id=membership.id,
        )
        db.flush()
        db.expire_all()
        persisted_failed = db.get(SimpaMethodologyReferenceSuite, failed.id)
        assert persisted_failed is not None and persisted_failed.status == "failed"
        assert len(persisted_failed.result_fingerprint) == 64
        failed_cases = list(
            db.scalars(
                select(SimpaMethodologyReferenceCase).where(
                    SimpaMethodologyReferenceCase.suite_id == persisted_failed.id
                )
            ).all()
        )
        assert "failed" in {case.status for case in failed_cases}
        assert all(len(case.result_fingerprint) == 64 for case in failed_cases)
        with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_terminal"):
            run_methodology_reference_suite(
                db,
                methodology_id=methodology.id,
                suite_id=persisted_failed.id,
                actor_id=membership.id,
            )
        with pytest.raises(SimpaAnalyticsError, match="methodology_reference_suite_required"):
            validate_methodology(
                db,
                methodology_id=methodology.id,
                validation_note="Failed terminal evidence cannot authorize validation.",
                actor_id=membership.id,
            )

        recovered = create_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            reference_dataset_version="native-recovery-v2",
            cases=_cases(indicator),
            actor_id=membership.id,
        )
        run_methodology_reference_suite(
            db,
            methodology_id=methodology.id,
            suite_id=recovered.id,
            actor_id=membership.id,
        )
        db.flush()
        db.expire_all()
        assert db.get(SimpaMethodologyReferenceSuite, recovered.id).status == "passed"
        assert db.get(SimpaMethodologyReferenceSuite, recovered.id).version_no == 2
        assert db.get(SimpaIndicatorMethodology, methodology.id).status == "proposed"
    finally:
        transaction.rollback()
        connection.close()
