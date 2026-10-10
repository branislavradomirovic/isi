"""Typed adapters for existing global SIMPA methodology governance APIs."""

from urllib.parse import quote

from src.domains.simpa import analytics_schemas as schemas
from src.domains.simpa.methodology_contracts import normalize_methodology_contract
from src.domains.simpa.statistical_contracts import (
    TARGET_SEMANTIC_FAMILIES,
    FORBIDDEN_FEATURE_FIELDS,
)
from src.streamlit_app.api_client import request
from src.streamlit_app.simpa_analytics_api import _checked


def create_methodology(token, *, scope, fields, unit_hint=""):
    contract = normalize_methodology_contract(fields["computation_spec"], indicator_unit_hint=unit_hint)
    payload = schemas.MethodologyCreateRequest.model_validate(
        {**fields, **scope, "computation_spec": contract.model_dump(mode="json")}
    ).model_dump(mode="json")
    return _post(token, "/methodologies", payload)


def create_suite(token, *, scope, methodology_id, fields):
    payload = schemas.MethodologyReferenceSuiteCreateRequest.model_validate({**fields, **scope}).model_dump(mode="json")
    return _post(token, f"/methodologies/{quote(str(methodology_id), safe='')}/reference-suites", payload)


def run_suite(token, *, scope, methodology_id, suite_id):
    payload = schemas.MethodologyReferenceSuiteRunRequest.model_validate(scope).model_dump(mode="json")
    return _post(
        token,
        f"/methodologies/{quote(str(methodology_id), safe='')}/reference-suites/{quote(str(suite_id), safe='')}/run",
        payload,
    )


def create_statistical(token, *, scope, fields):
    payload = schemas.StatisticalModelContractCreateRequest.model_validate({**fields, **scope}).model_dump(mode="json")
    if TARGET_SEMANTIC_FAMILIES[payload["target_semantic"]] != payload["model_family"]:
        raise ValueError("Nepodržan par semantike i modela.")
    features = [x.strip().casefold() for x in payload["feature_fields"]]
    if any(not x or x in FORBIDDEN_FEATURE_FIELDS for x in features) or len(set(features)) != len(features):
        raise ValueError("Unesite jedinstvene dozvoljene nazive feature polja.")
    binary = payload["target_semantic"] == "binary_system_state"
    if binary != bool((payload["positive_outcome_definition"] or "").strip()):
        raise ValueError("Definicija pozitivnog ishoda obavezna je samo za binarni sistemski cilj.")
    payload["feature_fields"] = features
    return _post(token, "/statistical-model-contracts", payload)


def transition(token, *, scope, record_id, kind, action, fields=None):
    models = {
        ("methodologies", "propose"): schemas.MethodologyProposeRequest,
        ("methodologies", "validate"): schemas.MethodologyValidateRequest,
        ("methodologies", "retire"): schemas.MethodologyRetireRequest,
        ("statistical-model-contracts", "propose"): schemas.StatisticalModelContractProposeRequest,
        ("statistical-model-contracts", "validate"): schemas.StatisticalModelContractValidateRequest,
        ("statistical-model-contracts", "retire"): schemas.StatisticalModelContractRetireRequest,
    }
    payload = models[(kind, action)].model_validate({**(fields or {}), **scope}).model_dump(mode="json")
    return _post(token, f"/{kind}/{quote(str(record_id), safe='')}/{action}", payload)


def _post(token, path, payload):
    return _checked(
        request("POST", "/api/v1/simpa/analytics" + path, token=token, json=payload),
        unavailable="Promena je možda registrovana. Osvežite registar pre ponavljanja.",
    )
