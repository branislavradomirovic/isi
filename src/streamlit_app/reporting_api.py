"""Typed scoped report client; never reflect private response bodies."""

from __future__ import annotations
from uuid import UUID
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request
from src.platform.reporting.schemas import (
    EvidenceLink,
    ReportingScope,
    ReportGenerateRequest,
    ReportVersionGenerateRequest,
    ReportLifecycleRequest,
    ReportReviewRequest,
    ReportExportRequest,
)

MESSAGES = {
    "report_reviewed_evidence_changed": "Pregledana verzija se promenila. Osvežite dokaz i ponovo potvrdite odluku.",
    "linked_evidence_no_longer_available": "Povezani izvor više nije podoban. Proverite izvor, pregled, geometriju i prava.",
    "report_version_not_submittable": "Verzija više nije nacrt podoban za pregled.",
    "report_version_not_reviewable": "Verzija više nije u statusu za pregled.",
    "report_version_not_publishable": "Samo odobrena verzija može biti objavljena.",
    "report_export_requires_approved_version": "Izvoz zahteva odobrenu verziju i aktuelna prava.",
}


def _checked(response, *, unavailable):
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Pristup izveštaju nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            code = response.json().get("detail")
        except (ValueError, AttributeError):
            code = None
        message = MESSAGES.get(code) if isinstance(code, str) else None
        raise AccessDenied(
            message or "Zahtev za izveštaj nije potvrđen. Proverite izbor, obavezna polja i aktuelne izvore."
        )
    if response.status_code == 204:
        return {"completed": True}
    try:
        return response.json()
    except ValueError:
        raise ApiUnavailable(unavailable) from None


def _scope(organization_id, workspace_id, product_code):
    return ReportingScope(
        organization_id=organization_id, workspace_id=workspace_id, product_code=product_code
    ).model_dump(mode="json")


def _get(token, path, organization_id, workspace_id, product_code):
    return _checked(
        request(
            "GET", "/api/v1/reporting/" + path, token=token, params=_scope(organization_id, workspace_id, product_code)
        ),
        unavailable="Nije moguće učitati izveštaje ili njihove izvore.",
    )


def _post(token, path, payload):
    return _checked(
        request("POST", "/api/v1/reporting/" + path, token=token, json=payload.model_dump(mode="json")),
        unavailable="Operacija izveštaja trenutno nije dostupna. Proverite status pre ponavljanja.",
    )


def sources(token, organization_id, workspace_id, product_code):
    return _get(token, "sources", organization_id, workspace_id, product_code)


def reports(token, organization_id, workspace_id, product_code):
    return _get(token, "reports", organization_id, workspace_id, product_code)


def report(token, report_id, organization_id, workspace_id, product_code):
    return _get(token, "reports/" + str(UUID(str(report_id))), organization_id, workspace_id, product_code)


def generate(
    token,
    *,
    organization_id,
    workspace_id,
    product_code,
    title,
    report_type,
    source_kind,
    source_id,
    evidence_link=None,
):
    payload = ReportGenerateRequest(
        **_scope(organization_id, workspace_id, product_code),
        title=title,
        report_type=report_type,
        source_kind=source_kind,
        source_id=source_id,
        evidence_link=evidence_link,
    )
    return _post(token, "reports", payload)


def new_version(
    token, *, report_id, organization_id, workspace_id, product_code, source_kind, source_id, evidence_link=None
):
    path = "reports/" + str(UUID(str(report_id))) + "/versions"
    payload = ReportVersionGenerateRequest(
        **_scope(organization_id, workspace_id, product_code),
        source_kind=source_kind,
        source_id=source_id,
        evidence_link=evidence_link,
    )
    return _post(token, path, payload)


def _reviewed(version):
    if version is None:
        return {}
    return {"reviewed_" + field: version[field] for field in ("status", "content_sha256", "source_manifest_sha256")}


def submit(token, *, version_id, organization_id, workspace_id, product_code, version=None):
    payload = ReportLifecycleRequest(**_scope(organization_id, workspace_id, product_code), **_reviewed(version))
    return _post(token, "versions/" + str(UUID(str(version_id))) + "/submit", payload)


def review(token, *, version_id, organization_id, workspace_id, product_code, decision, note, version=None):
    payload = ReportReviewRequest(
        **_scope(organization_id, workspace_id, product_code), **_reviewed(version), decision=decision, note=note
    )
    return _post(token, "versions/" + str(UUID(str(version_id))) + "/review", payload)


def publish(token, *, version_id, organization_id, workspace_id, product_code, version=None):
    payload = ReportLifecycleRequest(**_scope(organization_id, workspace_id, product_code), **_reviewed(version))
    return _post(token, "versions/" + str(UUID(str(version_id))) + "/publish", payload)


def export(token, *, version_id, organization_id, workspace_id, product_code, format):
    payload = ReportExportRequest(**_scope(organization_id, workspace_id, product_code), format=format)
    return _post(token, "versions/" + str(UUID(str(version_id))) + "/exports", payload)


def linked_preview(token, *, organization_id, workspace_id, product_code, request_id, evidence_link):
    payload = dict(
        _scope(organization_id, workspace_id, product_code),
        request_id=str(UUID(str(request_id))),
        evidence_link=EvidenceLink.model_validate(evidence_link).model_dump(mode="json"),
    )
    return _checked(
        request("POST", "/api/v1/reporting/linked-preview", token=token, json=payload),
        unavailable="Povezani dokaz trenutno nije dostupan.",
    )
