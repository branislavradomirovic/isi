"""Typed customer transport; scope overrides are never accepted from definitions."""

from urllib.parse import quote
from src.domains.ordo.statistical_authoring import StatisticalCreate, StatisticalTransition
from src.streamlit_app.api_client import request
from src.streamlit_app.ordo_analytics_api import _checked

PATH = "/api/v1/ordo/analytics/statistical-model-contracts"


def list_contracts(token, *, scope, offset=0):
    return _checked(
        request("GET", PATH, token=token, params={**scope, "offset": offset}),
        unavailable="Nije moguće učitati ORDO statističke specifikacije.",
    )


def create(token, *, scope, analytics_run_id, reviewed_methodology_id, definition):
    body = StatisticalCreate.model_validate(
        {
            **scope,
            "analytics_run_id": analytics_run_id,
            "reviewed_methodology_id": reviewed_methodology_id,
            "definition": definition,
        }
    ).model_dump(mode="json")
    return _post(token, "", body)


def transition(token, *, scope, row, action, fields):
    if action not in {"propose", "validate", "retire"}:
        raise ValueError("Nepodržan prelaz.")
    body = StatisticalTransition.model_validate(
        {**fields, **scope, "reviewed_status": row["status"], "reviewed_fingerprint": row["contract_fingerprint"]}
    ).model_dump(mode="json")
    return _post(token, f"/{quote(str(row['id']), safe='')}/{action}", body)


def _post(token, suffix, body):
    return _checked(
        request("POST", PATH + suffix, token=token, json=body),
        unavailable="Promena je možda registrovana. Osvežite pregled pre ponavljanja.",
    )
