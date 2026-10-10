"""Existing privacy mutation contracts and bounded governance inspection."""

from urllib.parse import quote

from src.platform.data.schemas import (
    RetentionPolicyCreate,
    RetentionMutationRequest,
    HoldPlaceRequest,
    AnonymizationProposalCreate,
    AnonymizationReviewRequest,
    ExportRequest,
)
from src.streamlit_app.api_client import request, ApiUnavailable
from src.streamlit_app.data_api import _checked


def _id(value):
    return quote(str(value), safe="")


def read_retention(token, *, version_id, scope):
    return _checked(
        request("GET", f"/api/v1/data/versions/{_id(version_id)}/retention", token=token, params=scope),
        unavailable="Nije moguće učitati retention stanje.",
    )


def create_policy(token, *, scope, fields):
    payload = RetentionPolicyCreate.model_validate(fields).model_dump(mode="json")
    return _checked(
        request("POST", "/api/v1/data/retention-policies", token=token, params=scope, json=payload),
        unavailable="Politika je možda registrovana. Osvežite katalog.",
    )


def retention_action(token, *, version_id, scope, revision, action, reason=None):
    schema = HoldPlaceRequest if action == "hold" else RetentionMutationRequest
    extra = dict(reason_reference=reason) if action == "hold" else {}
    payload = schema.model_validate({**extra, **scope, "expected_revision": revision}).model_dump(mode="json")
    suffix = {"hold": "hold", "release": "hold/release", "request": "purge/request"}[action]
    return _checked(
        request("POST", f"/api/v1/data/versions/{_id(version_id)}/{suffix}", token=token, json=payload),
        unavailable="Promena je možda registrovana. Osvežite stanje pre ponavljanja.",
    )


def list_records(token, *, scope, offset=0):
    if offset < 0:
        raise ValueError("Strana ne može biti negativna.")
    return _checked(
        request(
            "GET", "/api/v1/data/anonymization-records", token=token, params={**scope, "offset": offset, "limit": 50}
        ),
        unavailable="Nije moguće učitati dokaze anonimizacije.",
    )


def propose_anonymization(token, *, scope, fields):
    payload = AnonymizationProposalCreate.model_validate({**fields, **scope}).model_dump(mode="json")
    return _checked(
        request("POST", "/api/v1/data/anonymization-records", token=token, json=payload),
        unavailable="Predlog je možda registrovan. Osvežite evidenciju.",
    )


def review_anonymization(token, *, record_id, scope, fields):
    payload = AnonymizationReviewRequest.model_validate({**fields, **scope}).model_dump(mode="json")
    if payload["decision"] not in {"VERIFIED", "REJECTED"}:
        raise ValueError("Izaberite VERIFIED ili REJECTED.")
    return _checked(
        request("POST", f"/api/v1/data/anonymization-records/{_id(record_id)}/review", token=token, json=payload),
        unavailable="Odluka je možda registrovana. Osvežite evidenciju.",
    )


def export_version(token, *, version_id, scope, purpose):
    payload = ExportRequest.model_validate({**scope, "purpose_reference": purpose}).model_dump(mode="json")
    response = request("POST", f"/api/v1/data/versions/{_id(version_id)}/export", token=token, json=payload)
    if response.status_code >= 400:
        _checked(response, unavailable="Izvoz nije dostupan; proverite stanje i dozvole.")
    manifest = response.headers.get("X-Data-Export-Manifest-ID")
    if not manifest:
        raise ApiUnavailable("Nedostaje manifest izvoza. Preuzimanje nije prikazano.")
    return dict(
        payload=response.content,
        content_type=response.headers.get("content-type", "application/octet-stream"),
        manifest_id=manifest,
    )
