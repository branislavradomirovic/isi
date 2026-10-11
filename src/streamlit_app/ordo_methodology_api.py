"""Typed wrappers for the existing ORDO global methodology registry."""

from urllib.parse import quote

from src.domains.ordo import analytics_schemas as schemas
from src.domains.ordo.spatial_processing import OrdoSpatialAggregationContractV1
from src.streamlit_app.api_client import request
from src.streamlit_app.ordo_analytics_api import _checked


def create_methodology(token, *, scope, indicator_code, note, spatial_rule=None):
    requirements = {}
    if spatial_rule is not None:
        requirements["spatial_aggregation"] = OrdoSpatialAggregationContractV1(
            aggregation_rule=spatial_rule
        ).model_dump(mode="json")
    payload = schemas.MethodologyCreateRequest.model_validate(
        {**scope, "indicator_code": indicator_code, "methodology_note": note, "source_requirements": requirements}
    ).model_dump(mode="json")
    return _post(token, "/methodologies", payload)


def transition(token, *, scope, record_id, action, fields=None):
    schema = {
        "propose": schemas.MethodologyProposeRequest,
        "validate": schemas.MethodologyValidateRequest,
        "retire": schemas.MethodologyRetireRequest,
    }[action]
    payload = schema.model_validate({**(fields or {}), **scope}).model_dump(mode="json")
    return _post(token, f"/methodologies/{quote(str(record_id), safe='')}/{action}", payload)


def _post(token, path, payload):
    return _checked(
        request("POST", "/api/v1/ordo/analytics" + path, token=token, json=payload),
        unavailable="Promena je možda sačuvana. Osvežite registar pre ponavljanja.",
    )
