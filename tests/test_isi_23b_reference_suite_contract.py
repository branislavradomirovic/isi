from __future__ import annotations

import inspect as pyinspect
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import src.platform.models  # noqa: F401 - register FK targets
from src.core.database import Base
from src.domains.simpa.analytics_schemas import (
    DirectObservationExpectedResult,
    DirectObservationReferenceRecord,
)
from src.domains.simpa.analytics_service import create_methodology
from src.domains.simpa.models import SimpaDimension, SimpaIndicatorDefinition
from src.domains.simpa.reference_calculations import (
    REFERENCE_SUITE_SCHEMA_VERSION,
    ReferenceCalculationError,
    calculate_direct_observation,
    compare_direct_observation,
    reference_case_fingerprint,
    reference_suite_fingerprint,
    reference_suite_result_fingerprint,
)
from src.platform.identity.models import Membership, Organization, User


def _record(*, numeric=None, text=None):
    return {
        "indicator_code": "SIMPA.TEST",
        "quality_status": "validated",
        "value_numeric": numeric,
        "value_text": text,
    }


def test_reference_case_and_suite_fingerprints_are_semantic_ordered_and_uuid_independent():
    first = reference_case_fingerprint(
        case_key="numeric",
        indicator_code="SIMPA.TEST",
        reference_record=_record(numeric="10.0"),
        expected_result={"value_numeric": 10, "value_text": None},
    )
    second = reference_case_fingerprint(
        case_key="text",
        indicator_code="SIMPA.TEST",
        reference_record=_record(text="  Ready  "),
        expected_result={"value_numeric": None, "value_text": "Ready"},
    )
    kwargs = {
        "methodology_contract_fingerprint": "a" * 64,
        "reference_dataset": "Approved compact reference data",
        "reference_dataset_version": "2026.09-v1",
    }
    forward = reference_suite_fingerprint(
        **kwargs,
        cases=[
            {"case_key": "numeric", "case_fingerprint": first, "database_id": "ignored-a"},
            {"case_key": "text", "case_fingerprint": second, "database_id": "ignored-b"},
        ],
    )
    reverse = reference_suite_fingerprint(
        **kwargs,
        cases=[
            {"case_key": "text", "case_fingerprint": second, "database_id": "other-b"},
            {"case_key": "numeric", "case_fingerprint": first, "database_id": "other-a"},
        ],
    )
    assert REFERENCE_SUITE_SCHEMA_VERSION == "SIMPA-REFERENCE-SUITE-v1"
    assert forward == reverse
    assert len(forward) == 64


def test_direct_observation_numeric_tolerance_and_normalized_text_exact():
    numeric = calculate_direct_observation(_record(numeric="10.04"), indicator_code="SIMPA.TEST")
    assert compare_direct_observation(numeric, {"value_numeric": 10, "value_text": None}, accepted_tolerance=0.05)[
        "passed"
    ]
    assert not compare_direct_observation(numeric, {"value_numeric": 10, "value_text": None}, accepted_tolerance=0.01)[
        "passed"
    ]
    text = calculate_direct_observation(_record(text="  Ready  "), indicator_code="SIMPA.TEST")
    assert compare_direct_observation(text, {"value_numeric": None, "value_text": "Ready"}, accepted_tolerance=0)[
        "passed"
    ]
    assert not compare_direct_observation(text, {"value_numeric": None, "value_text": "ready"}, accepted_tolerance=0)[
        "passed"
    ]


def test_actual_direct_observation_accepts_numeric_text_or_both_but_not_neither():
    numeric = DirectObservationReferenceRecord(**_record(numeric=10))
    text = DirectObservationReferenceRecord(**_record(text="  Ready  "))
    both = DirectObservationReferenceRecord(**_record(numeric=10, text="  Ready  "))
    assert numeric.value_numeric == 10 and numeric.value_text is None
    assert text.value_numeric is None and text.value_text == "Ready"
    assert both.value_numeric == 10 and both.value_text == "Ready"
    with pytest.raises(ValidationError, match="at least one value channel"):
        DirectObservationReferenceRecord(**_record())


def test_expected_direct_observation_remains_exactly_one_channel():
    with pytest.raises(ValidationError, match="exactly one value channel"):
        DirectObservationExpectedResult(value_numeric=10, value_text="Ready")


def test_dual_channel_actual_compares_only_the_expected_channel_without_dropping_evidence():
    actual = calculate_direct_observation(_record(numeric="10.04", text="  Ready  "), indicator_code="SIMPA.TEST")
    numeric = compare_direct_observation(actual, {"value_numeric": 10}, accepted_tolerance=0.05)
    textual = compare_direct_observation(actual, {"value_text": "Ready"}, accepted_tolerance=0)
    assert numeric["passed"] is True and numeric["actual"] == {"value_numeric": 10.04, "value_text": "Ready"}
    assert textual["passed"] is True and textual["actual"] == {"value_numeric": 10.04, "value_text": "Ready"}


@pytest.mark.parametrize(
    "record",
    [
        _record(numeric=float("nan")),
        _record(numeric=float("inf")),
        _record(numeric=True),
        _record(),
        {**_record(numeric=1), "indicator_code": "OTHER"},
        {**_record(numeric=1), "quality_status": "draft"},
    ],
)
def test_direct_observation_is_finite_exact_identity_validated_and_single_channel(record):
    with pytest.raises(ReferenceCalculationError):
        calculate_direct_observation(record, indicator_code="SIMPA.TEST")


def test_case_keys_and_dataset_versions_are_required_and_unique():
    fingerprint = reference_case_fingerprint(
        case_key="one",
        indicator_code="SIMPA.TEST",
        reference_record=_record(numeric=1),
        expected_result={"value_numeric": 1},
    )
    with pytest.raises(ReferenceCalculationError):
        reference_case_fingerprint(
            case_key=" ",
            indicator_code="SIMPA.TEST",
            reference_record=_record(numeric=1),
            expected_result={"value_numeric": 1},
        )
    for cases, version in (
        ([{"case_key": "one", "case_fingerprint": fingerprint}] * 2, "v1"),
        ([{"case_key": "one", "case_fingerprint": fingerprint}], " "),
    ):
        with pytest.raises(ReferenceCalculationError):
            reference_suite_fingerprint(
                methodology_contract_fingerprint="b" * 64,
                reference_dataset="dataset",
                reference_dataset_version=version,
                cases=cases,
            )


def test_dual_channel_case_fingerprint_and_normalized_key_ordering_are_deterministic():
    dual = reference_case_fingerprint(
        case_key=" dual ",
        indicator_code="SIMPA.TEST",
        reference_record=_record(numeric="10.0", text=" Ready "),
        expected_result={"value_text": "Ready"},
    )
    assert dual == reference_case_fingerprint(
        case_key="dual",
        indicator_code=" SIMPA.TEST ",
        reference_record=_record(numeric=10, text="Ready"),
        expected_result={"value_numeric": None, "value_text": " Ready "},
    )
    kwargs = {
        "methodology_contract_fingerprint": "c" * 64,
        "reference_dataset": "dataset",
        "reference_dataset_version": "v1",
    }
    normalized = reference_suite_fingerprint(
        **kwargs,
        cases=[
            {"case_key": " z ", "case_fingerprint": "z" * 64},
            {"case_key": "a", "case_fingerprint": "a" * 64},
        ],
    )
    canonical = reference_suite_fingerprint(
        **kwargs,
        cases=[
            {"case_key": "a", "case_fingerprint": "a" * 64},
            {"case_key": "z", "case_fingerprint": "z" * 64},
        ],
    )
    assert normalized == canonical
    with pytest.raises(ReferenceCalculationError, match="reference_case_keys_invalid"):
        reference_suite_fingerprint(
            **kwargs,
            cases=[
                {"case_key": "duplicate", "case_fingerprint": "a" * 64},
                {"case_key": " duplicate ", "case_fingerprint": "b" * 64},
            ],
        )


def test_new_methodology_creation_has_no_evidence_mode_escape_hatch_and_defaults_to_suite_v1():
    assert "reference_evidence_mode" not in pyinspect.signature(create_methodology).parameters
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        marker = uuid.uuid4().hex
        user = User(email=f"contract-{marker}@example.test", display_name="Reviewer")
        organization = Organization(slug=f"contract-{marker}", name="Contract test")
        db.add_all([user, organization])
        db.flush()
        membership = Membership(user_id=user.id, organization_id=organization.id)
        dimension = SimpaDimension(code=f"CONTRACT_{marker}", name_sr="Contract")
        db.add_all([membership, dimension])
        db.flush()
        indicator = SimpaIndicatorDefinition(
            code=f"CONTRACT_IND_{marker}",
            name_sr="Contract",
            dimension_code=dimension.code,
            unit_hint="count",
            methodology_status="conceptual",
            methodology_note="",
        )
        db.add(indicator)
        db.flush()
        row = create_methodology(
            db,
            indicator_code=indicator.code,
            computation_type="direct_observation",
            methodology_note="New suite-backed methodology.",
            source_requirements={},
            actor_id=membership.id,
        )
        assert row.reference_evidence_mode == "suite_v1"


def test_result_fingerprint_is_deterministic():
    assert reference_suite_result_fingerprint({"passed": True, "cases": ["a", "b"]}) == (
        reference_suite_result_fingerprint({"cases": ["a", "b"], "passed": True})
    )


def test_production_and_suite_execution_import_the_same_calculator():
    service = Path("src/domains/simpa/analytics_service.py").read_text()
    assert "from src.domains.simpa.reference_calculations import (" in service
    assert service.count("calculate_direct_observation(") >= 3
    assert 'value_numeric=calculated["value_numeric"]' in service
    assert 'value_text=str(calculated["value_text"] or "")' in service
    assert "_normalize_direct_observation_value" not in service
