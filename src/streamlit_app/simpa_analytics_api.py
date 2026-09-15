from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("SIMPA analytics pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "SIMPA analytics request rejected")
        except Exception:
            detail = "SIMPA analytics request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def summary(
    token: str,
    organization_id: str,
    workspace_id: str,
    *,
    analytical_artifact_type: str,
    analytical_artifact_id: str,
    monitoring_cycle_id: str | None = None,
):
    params = {
        "organization_id": organization_id,
        "workspace_id": workspace_id,
        "analytical_artifact_type": analytical_artifact_type,
        "analytical_artifact_id": analytical_artifact_id,
    }
    if monitoring_cycle_id:
        params["monitoring_cycle_id"] = monitoring_cycle_id
    return _checked(
        request("GET", "/api/v1/simpa/analytics/summary", token=token, params=params),
        unavailable="Nije moguće učitati SIMPA analitički pregled.",
    )


def runs(token: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET",
            "/api/v1/simpa/analytics/runs",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati SIMPA analitičke snapshot-e.",
    )


def create_run(
    token: str,
    *,
    organization_id: str,
    workspace_id: str,
    analytical_artifact_type: str,
    analytical_artifact_id: str,
    monitoring_cycle_id: str | None = None,
):
    return _checked(
        request(
            "POST",
            "/api/v1/simpa/analytics/runs",
            token=token,
            json={
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "analytical_artifact_type": analytical_artifact_type,
                "analytical_artifact_id": analytical_artifact_id,
                "monitoring_cycle_id": monitoring_cycle_id,
            },
        ),
        unavailable="Nije moguće kreirati SIMPA monitoring snapshot.",
    )


def methodologies(token: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET",
            "/api/v1/simpa/analytics/methodologies",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati SIMPA metodologije.",
    )


def reference_suites(token: str, methodology_id: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET",
            f"/api/v1/simpa/analytics/methodologies/{methodology_id}/reference-suites",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati SIMPA referentne suite-ove.",
    )


def create_reference_suite(
    token: str,
    *,
    methodology_id: str,
    organization_id: str,
    workspace_id: str,
    reference_dataset_version: str,
    cases: list[dict],
):
    return _checked(
        request(
            "POST",
            f"/api/v1/simpa/analytics/methodologies/{methodology_id}/reference-suites",
            token=token,
            json={
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "reference_dataset_version": reference_dataset_version,
                "cases": cases,
            },
        ),
        unavailable="Nije moguće kreirati SIMPA referentni suite.",
    )


def run_reference_suite(
    token: str,
    *,
    methodology_id: str,
    suite_id: str,
    organization_id: str,
    workspace_id: str,
):
    return _checked(
        request(
            "POST",
            f"/api/v1/simpa/analytics/methodologies/{methodology_id}/reference-suites/{suite_id}/run",
            token=token,
            json={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće izvršiti SIMPA referentni suite.",
    )


def syntheses(token: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET",
            "/api/v1/simpa/analytics/syntheses",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati SIMPA AI sinteze.",
    )


def create_synthesis(
    token: str, *, organization_id: str, workspace_id: str, analytics_run_id: str, sensitivity: str = "sensitive"
):
    return _checked(
        request(
            "POST",
            "/api/v1/simpa/analytics/syntheses",
            token=token,
            json={
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "analytics_run_id": analytics_run_id,
                "sensitivity": sensitivity,
            },
        ),
        unavailable="Nije moguće pokrenuti SIMPA AI sintezu.",
    )


def review_synthesis(
    token: str, *, synthesis_id: str, organization_id: str, workspace_id: str, decision: str, reviewer_note: str = ""
):
    return _checked(
        request(
            "POST",
            f"/api/v1/simpa/analytics/syntheses/{synthesis_id}/review",
            token=token,
            json={
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "decision": decision,
                "reviewer_note": reviewer_note,
            },
        ),
        unavailable="Nije moguće evidentirati human review.",
    )
