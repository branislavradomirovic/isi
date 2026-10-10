"""Typed existing source governance and quarantine APIs."""

from urllib.parse import quote

from src.platform.data.schemas import SourceGovernanceUpdate, RecordResolutionCreate
from src.streamlit_app.api_client import request
from src.streamlit_app.data_api import _checked


def _path(source_id):
    return "/api/v1/data/sources/" + quote(str(source_id), safe="")


def read_profile(token, *, source_id, scope):
    return _checked(
        request("GET", _path(source_id) + "/governance", token=token, params=scope),
        unavailable="Nije moguće učitati governance profil.",
    )


def list_retention_policies(token, *, scope):
    return _checked(
        request("GET", "/api/v1/data/retention-policies", token=token, params=scope),
        unavailable="Nije moguće učitati politike čuvanja.",
    )


def update_profile(token, *, source_id, scope, revision, fields):
    payload = SourceGovernanceUpdate.model_validate({**fields, "expected_revision": revision}).model_dump(
        mode="json", exclude_unset=True
    )
    return _checked(
        request("PUT", _path(source_id) + "/governance", token=token, params=scope, json=payload),
        unavailable="Promena je možda registrovana. Osvežite profil pre ponavljanja.",
    )


def list_quarantine(token, *, source_id, scope):
    return _checked(
        request("GET", _path(source_id) + "/record-quarantine", token=token, params=scope),
        unavailable="Nije moguće učitati karantin.",
    )


def read_quarantine(token, *, source_id, record_id, scope):
    return _checked(
        request(
            "GET", _path(source_id) + "/record-quarantine/" + quote(str(record_id), safe=""), token=token, params=scope
        ),
        unavailable="Nije moguće učitati zapis za pregled.",
    )


def resolve_record(token, *, source_id, record_id, scope, fields):
    payload = RecordResolutionCreate.model_validate({**fields, **scope}).model_dump(mode="json")
    return _checked(
        request(
            "POST",
            _path(source_id) + "/record-quarantine/" + quote(str(record_id), safe="") + "/resolve",
            token=token,
            json=payload,
        ),
        unavailable="Odluka je možda registrovana. Osvežite karantin pre ponavljanja.",
    )
