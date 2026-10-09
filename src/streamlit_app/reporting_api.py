from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Reporting pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Reporting request rejected")
        except Exception:
            detail = "Reporting request rejected"
        raise AccessDenied(str(detail))
    if response.status_code == 204:
        return None
    return response.json()


def sources(token: str, organization_id: str, workspace_id: str, product_code: str):
    return _checked(
        request("GET", "/api/v1/reporting/sources", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code}),
        unavailable="Nije moguće učitati reporting izvore.",
    )


def reports(token: str, organization_id: str, workspace_id: str, product_code: str):
    return _checked(
        request("GET", "/api/v1/reporting/reports", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code}),
        unavailable="Nije moguće učitati izveštaje.",
    )


def report(token: str, report_id: str, organization_id: str, workspace_id: str, product_code: str):
    return _checked(
        request("GET", f"/api/v1/reporting/reports/{report_id}", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code}),
        unavailable="Nije moguće učitati verzije izveštaja.",
    )


def generate(token: str, *, organization_id: str, workspace_id: str, product_code: str, title: str, report_type: str, source_kind: str, source_id: str, evidence_link=None):
    return _checked(
        request("POST", "/api/v1/reporting/reports", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code, "title": title, "report_type": report_type, "source_kind": source_kind, "source_id": source_id, "evidence_link": evidence_link}),
        unavailable="Nije moguće generisati verzionisani izveštaj.",
    )


def new_version(token: str, *, report_id: str, organization_id: str, workspace_id: str, product_code: str, source_kind: str, source_id: str, evidence_link=None):
    return _checked(
        request("POST", f"/api/v1/reporting/reports/{report_id}/versions", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code, "source_kind": source_kind, "source_id": source_id, "evidence_link": evidence_link}),
        unavailable="Nije moguće kreirati novu verziju izveštaja.",
    )


def submit(token: str, *, version_id: str, organization_id: str, workspace_id: str, product_code: str):
    return _checked(
        request("POST", f"/api/v1/reporting/versions/{version_id}/submit", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code}),
        unavailable="Nije moguće poslati verziju na review.",
    )


def review(token: str, *, version_id: str, organization_id: str, workspace_id: str, product_code: str, decision: str, note: str):
    return _checked(
        request("POST", f"/api/v1/reporting/versions/{version_id}/review", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code, "decision": decision, "note": note}),
        unavailable="Nije moguće evidentirati review izveštaja.",
    )


def publish(token: str, *, version_id: str, organization_id: str, workspace_id: str, product_code: str):
    return _checked(
        request("POST", f"/api/v1/reporting/versions/{version_id}/publish", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code}),
        unavailable="Nije moguće publikovati verziju izveštaja.",
    )


def export(token: str, *, version_id: str, organization_id: str, workspace_id: str, product_code: str, format: str):
    return _checked(
        request("POST", f"/api/v1/reporting/versions/{version_id}/exports", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "product_code": product_code, "format": format}),
        unavailable="Nije moguće generisati reporting artefakt.",
    )


def linked_preview(token, *, organization_id, workspace_id, product_code, request_id, evidence_link):
    return _checked(request("POST", "/api/v1/reporting/linked-preview", token=token,
                            json={"organization_id": organization_id, "workspace_id": workspace_id,
                                  "product_code": product_code, "request_id": request_id, "evidence_link": evidence_link}),
                    unavailable="Povezani dokaz trenutno nije dostupan.")
