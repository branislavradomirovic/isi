from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest
from streamlit.testing.v1 import AppTest

from src.domains.simpa.methodology_contracts import SimpaMethodologyContractV1
from src.domains.simpa.statistical_contracts import TARGET_SEMANTIC_FAMILIES
from src.streamlit_app import simpa_methodology_api as api, simpa_methodology_workspace as ui
from tests.test_isi_23a_methodology_contract import _contract

IDS = [str(uuid.UUID(int=i)) for i in range(1, 7)]
SCOPE = dict(organization_id=IDS[0], workspace_id=IDS[1])
METHOD = dict(
    id=IDS[2],
    indicator_code="synthetic",
    version_no=1,
    status="proposed",
    computation_spec=_contract(),
    contract_fingerprint="a" * 64,
    reference_evidence_mode="suite_v1",
)
STAT = dict(
    id=IDS[3],
    analysis_key="synthetic",
    version_no=1,
    status="proposed",
    contract={"purpose": "Synthetic test"},
    contract_fingerprint="b" * 64,
)
SUITE = dict(id=IDS[4], version_no=1, status="passed", cases=[], case_count=1)


def request_mock(monkeypatch):
    req = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"id": IDS[5]}))
    monkeypatch.setattr(api, "request", req)
    return req


def test_method_scope_cannot_be_overridden_and_contract_typed(monkeypatch):
    req = request_mock(monkeypatch)
    api.create_methodology(
        "synthetic",
        scope=SCOPE,
        unit_hint="count",
        fields=dict(
            organization_id=IDS[5],
            indicator_code="synthetic",
            methodology_note="Synthetic reference",
            computation_spec=_contract(),
            source_requirements={},
        ),
    )
    body = req.call_args.kwargs["json"]
    assert body["organization_id"] == IDS[0] and body["workspace_id"] == IDS[1]
    assert SimpaMethodologyContractV1.model_validate(body["computation_spec"]).non_causal


@pytest.mark.parametrize(
    "mutation",
    [
        {"accepted_tolerance": None},
        {"unit": "different"},
        {"non_causal": False},
        {"required_source_fields": ["person_id"]},
    ],
)
def test_invalid_method_never_transmits(monkeypatch, mutation):
    req = request_mock(monkeypatch)
    with pytest.raises(ValueError):
        api.create_methodology(
            "synthetic",
            scope=SCOPE,
            unit_hint="count",
            fields=dict(
                indicator_code="synthetic",
                methodology_note="Synthetic",
                computation_spec={**_contract(), **mutation},
            ),
        )
    req.assert_not_called()


@pytest.mark.parametrize("semantic,family", list(TARGET_SEMANTIC_FAMILIES.items()))
def test_four_statistical_pairs_explicit_author_parameters(monkeypatch, semantic, family):
    req = request_mock(monkeypatch)
    api.create_statistical(
        "synthetic",
        scope=SCOPE,
        fields=dict(
            indicator_code="synthetic",
            analysis_key="test",
            target_semantic=semantic,
            model_family=family,
            feature_fields=[" FEATURE_X "],
            confidence_level=0.9,
            covariance_type="HC3",
            purpose="Synthetic",
            limitations="Synthetic only",
            positive_outcome_definition="Synthetic positive" if semantic == "binary_system_state" else None,
        ),
    )
    body = req.call_args.kwargs["json"]
    assert body["feature_fields"] == ["feature_x"]
    assert body["model_family"] == family and body["non_causal"] and body["aggregate_only"]
    assert body["confidence_level"] == 0.9 and body["organization_id"] == IDS[0]


@pytest.mark.parametrize(
    "mutation",
    [
        {"feature_fields": ["value_numeric"]},
        {"feature_fields": ["x", " X "]},
        {"model_family": "poisson_glm"},
        {"confidence_level": 1},
        {"positive_outcome_definition": "invalid for continuous"},
    ],
)
def test_invalid_statistical_never_transmits(monkeypatch, mutation):
    req = request_mock(monkeypatch)
    with pytest.raises(ValueError):
        api.create_statistical(
            "synthetic",
            scope=SCOPE,
            fields={
                **dict(
                    indicator_code="synthetic",
                    analysis_key="test",
                    target_semantic="continuous",
                    model_family="ols",
                    feature_fields=["feature_x"],
                    confidence_level=0.9,
                    covariance_type="HC3",
                    purpose="Synthetic",
                    limitations="Synthetic only",
                ),
                **mutation,
            },
        )
    req.assert_not_called()


@pytest.mark.parametrize(
    "kind,action,fields",
    [
        ("methodologies", "propose", {}),
        ("methodologies", "validate", {"validation_note": "Human reviewed"}),
        ("methodologies", "retire", {"retirement_note": "Archived version"}),
        ("statistical-model-contracts", "propose", {}),
        (
            "statistical-model-contracts",
            "validate",
            {"validation_note": "Human reviewed", "validation_evidence_reference": "QA evidence"},
        ),
        ("statistical-model-contracts", "retire", {"retirement_note": "Archived version"}),
    ],
)
def test_lifecycle_typed_scoped_escaped(monkeypatch, kind, action, fields):
    req = request_mock(monkeypatch)
    api.transition(
        "synthetic", scope=SCOPE, record_id="id/+", kind=kind, action=action, fields={**fields, "workspace_id": IDS[5]}
    )
    assert req.call_args.args[1] == f"/api/v1/simpa/analytics/{kind}/id%2F%2B/{action}"
    assert req.call_args.kwargs["json"]["workspace_id"] == IDS[1]


def test_reference_cases_independently_authored_and_empty_no_zero(monkeypatch):
    req = request_mock(monkeypatch)
    rows = [
        dict(
            case_key="numeric",
            quality_status="validated",
            input_numeric=2,
            input_text=None,
            expected_numeric=3,
            expected_text=None,
        ),
        dict(
            case_key="text",
            quality_status="validated",
            input_numeric=None,
            input_text="input",
            expected_numeric=None,
            expected_text="output",
        ),
    ]
    cases = ui.reference_cases(rows, "synthetic")
    api.create_suite(
        "synthetic", scope=SCOPE, methodology_id="m/+", fields=dict(reference_dataset_version="QA-v1", cases=cases)
    )
    body = req.call_args.kwargs["json"]
    assert body["cases"][0]["expected_result"]["value_numeric"] == 3
    assert body["cases"][1]["reference_record"]["value_numeric"] is None
    assert "/m%2F%2B/" in req.call_args.args[1]
    assert ui.reference_cases([dict.fromkeys(rows[0])], "synthetic") == []


def test_duplicate_reference_case_no_request(monkeypatch):
    req = request_mock(monkeypatch)
    case = dict(
        case_key="same",
        reference_record=dict(indicator_code="synthetic", quality_status="validated", value_numeric=1),
        expected_result=dict(value_numeric=1),
    )
    with pytest.raises(ValueError):
        api.create_suite(
            "synthetic",
            scope=SCOPE,
            methodology_id=IDS[2],
            fields=dict(reference_dataset_version="QA", cases=[case, case]),
        )
    req.assert_not_called()


def app(monkeypatch, *, product="SIMPA", permissions=None, method=None, suites=None, contracts=None):
    monkeypatch.setattr(
        ui.simpa_api,
        "catalog",
        lambda *a, **kw: dict(indicators=[dict(code="synthetic", unit_hint="count", active=True)]),
    )
    monkeypatch.setattr(ui.read_api, "methodologies", lambda *a, **kw: [method or METHOD])
    monkeypatch.setattr(
        ui.read_api, "statistical_model_contracts", lambda *a, **kw: contracts if contracts is not None else [STAT]
    )
    monkeypatch.setattr(ui.read_api, "reference_suites", lambda *a, **kw: suites if suites is not None else [SUITE])
    shell = dict(
        organization={"id": IDS[0]},
        workspace={"id": IDS[1]},
        product=dict(
            code=product,
            permission_codes=permissions if permissions is not None else ["analysis.read", "indicator.manage"],
        ),
    )
    return AppTest.from_string(
        "from src.streamlit_app.simpa_methodology_workspace import render_methodology_authoring\n"
        f'render_methodology_authoring(token="synthetic",shell={shell!r})'
    ).run()


def button(at, name):
    return next(x for x in at.button if x.label == name)


def checkbox(at, name):
    return next(x for x in at.checkbox if x.label == name)


def textbox(at, name):
    return next(x for x in [*at.text_input, *at.text_area] if x.label == name)


@pytest.mark.parametrize(
    "product,permissions",
    [("ORDO", ["analysis.read", "indicator.manage"]), ("SIMPA", ["analysis.read"]), ("SIMPA", ["indicator.manage"])],
)
def test_wrong_scope_and_readonly_no_authoring(monkeypatch, product, permissions):
    at = app(monkeypatch, product=product, permissions=permissions)
    assert not at.exception and not at.button and not at.text_input


def test_no_automatic_reads_no_institutional_defaults(monkeypatch):
    at = app(monkeypatch)
    assert len(at.button) == 1 and not at.get("form")
    button(at, "Učitaj / osveži metodološki registar").click().run()
    assert not at.exception
    assert all(x.value is None for x in at.number_input)
    assert not any(x.value for x in at.checkbox)
    assert "globalni" in at.warning[0].value


def test_validate_requires_passed_suite_human_note_and_confirm(monkeypatch):
    change = Mock(return_value={"id": IDS[2]})
    monkeypatch.setattr(ui.api, "transition", change)
    at = app(monkeypatch, contracts=[])
    button(at, "Učitaj / osveži metodološki registar").click().run()
    assert not any(x.label == "Odobri VALIDATED" for x in at.button)
    button(at, "Učitaj / osveži referentne suite-ove").click().run()
    textbox(at, "Obrazloženje ljudskog odobrenja").input("Human reviewed synthetic").run()
    button(at, "Odobri VALIDATED").click().run()
    change.assert_not_called()
    checkbox(at, "Potvrđujem prelaz VALIDATE ovog zapisa").check().run()
    button(at, "Odobri VALIDATED").click().run()
    assert change.call_args.kwargs["record_id"] == IDS[2]
    assert change.call_args.kwargs["fields"]["validation_note"] == "Human reviewed synthetic"
    button(at, "Učitaj / osveži referentne suite-ove").click().run()
    assert not checkbox(at, "Potvrđujem prelaz VALIDATE ovog zapisa").value
    assert not at.exception


def test_failed_suite_does_not_enable_validation(monkeypatch):
    at = app(monkeypatch, suites=[{**SUITE, "status": "failed"}], contracts=[])
    button(at, "Učitaj / osveži metodološki registar").click().run()
    button(at, "Učitaj / osveži referentne suite-ove").click().run()
    assert not any(x.label == "Odobri VALIDATED" for x in at.button)
    assert not at.exception


def test_statistical_binary_definition_reachable_not_continuous(monkeypatch):
    at = app(monkeypatch, method={**METHOD, "status": "validated"})
    button(at, "Učitaj / osveži metodološki registar").click().run()
    selector = next(x for x in at.selectbox if x.label == "Semantika statističkog cilja")
    selector.select("binary_system_state").run()
    assert any(x.label == "Definicija pozitivnog sistemskog ishoda" for x in at.text_area)
    next(x for x in at.selectbox if x.label == "Semantika statističkog cilja").select("continuous").run()
    assert not any(x.label == "Definicija pozitivnog sistemskog ishoda" for x in at.text_area)
    assert not at.exception
