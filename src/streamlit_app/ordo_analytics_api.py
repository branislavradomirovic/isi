from __future__ import annotations

from typing import Any

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("ORDO analytics pristup nije dozvoljen u izabranom kontekstu.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "ORDO analytics request rejected")
        except Exception:
            detail = "ORDO analytics request rejected"
        raise AccessDenied(str(detail))
    return response.json()


def summary(token: str, organization_id: str, workspace_id: str, *, analytical_artifact_type: str, analytical_artifact_id: str, monitoring_cycle_id: str | None = None):
    params = {"organization_id": organization_id, "workspace_id": workspace_id, "analytical_artifact_type": analytical_artifact_type, "analytical_artifact_id": analytical_artifact_id}
    if monitoring_cycle_id:
        params["monitoring_cycle_id"] = monitoring_cycle_id
    return _checked(request("GET", "/api/v1/ordo/analytics/summary", token=token, params=params), unavailable="Nije moguće učitati ORDO analitički pregled.")


def runs(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/runs", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO analitičke snapshot-e.")


def forecasts(token: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET",
            "/api/v1/ordo/analytics/forecasts",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati persistirane ORDO forecast rezultate.",
    )


def forecast_detail(
    token: str,
    *,
    forecast_run_id: str,
    organization_id: str,
    workspace_id: str,
):
    return _checked(
        request(
            "GET",
            f"/api/v1/ordo/analytics/forecasts/{forecast_run_id}",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati detalj ORDO forecast rezultata.",
    )


def create_run(token: str, *, organization_id: str, workspace_id: str, analytical_artifact_type: str, analytical_artifact_id: str, monitoring_cycle_id: str | None = None):
    return _checked(request("POST", "/api/v1/ordo/analytics/runs", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "analytical_artifact_type": analytical_artifact_type, "analytical_artifact_id": analytical_artifact_id, "monitoring_cycle_id": monitoring_cycle_id}), unavailable="Nije moguće kreirati ORDO monitoring snapshot.")


def time_series_specs(token: str, organization_id: str, workspace_id: str):
    return _checked(
        request(
            "GET", "/api/v1/ordo/analytics/time-series-specs", token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati ORDO time-series specifikacije.",
    )


def time_series_spec_detail(
    token: str, *, time_series_spec_id: str, organization_id: str, workspace_id: str,
):
    return _checked(
        request(
            "GET", f"/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće učitati detalj time-series specifikacije.",
    )


def create_time_series_spec(
    token: str, *, organization_id: str, workspace_id: str, spec: dict[str, Any],
):
    return _checked(
        request(
            "POST", "/api/v1/ordo/analytics/time-series-specs", token=token,
            json={"organization_id": organization_id, "workspace_id": workspace_id, **spec},
        ),
        unavailable="Nije moguće kreirati ORDO time-series specifikaciju.",
    )


def propose_time_series_spec(
    token: str, *, time_series_spec_id: str, organization_id: str, workspace_id: str,
):
    return _checked(
        request(
            "POST", f"/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/propose",
            token=token, json={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće predložiti time-series specifikaciju.",
    )


def validate_time_series_spec(
    token: str, *, time_series_spec_id: str, organization_id: str, workspace_id: str,
    validation_note: str, validation_evidence_reference: str,
):
    return _checked(
        request(
            "POST", f"/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/validate",
            token=token,
            json={
                "organization_id": organization_id, "workspace_id": workspace_id,
                "validation_note": validation_note,
                "validation_evidence_reference": validation_evidence_reference,
            },
        ),
        unavailable="Nije moguće validirati time-series specifikaciju.",
    )


def retire_time_series_spec(
    token: str, *, time_series_spec_id: str, organization_id: str, workspace_id: str,
    retirement_note: str,
):
    return _checked(
        request(
            "POST", f"/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/retire",
            token=token,
            json={
                "organization_id": organization_id, "workspace_id": workspace_id,
                "retirement_note": retirement_note,
            },
        ),
        unavailable="Nije moguće povući time-series specifikaciju.",
    )


def time_series_identities(
    token: str, *, time_series_spec_id: str, organization_id: str, workspace_id: str,
):
    return _checked(
        request(
            "GET", f"/api/v1/ordo/analytics/time-series-specs/{time_series_spec_id}/series-identities",
            token=token,
            params={"organization_id": organization_id, "workspace_id": workspace_id},
        ),
        unavailable="Nije moguće otkriti eligible identitete serije.",
    )


def execute_forecast(
    token: str, *, organization_id: str, workspace_id: str,
    time_series_spec_id: str, requested_family: str,
    series_identity: dict[str, Any], interval_level: float,
):
    return _checked(
        request(
            "POST", "/api/v1/ordo/analytics/forecasts", token=token,
            json={
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "time_series_spec_id": time_series_spec_id,
                "requested_family": requested_family,
                "series_identity": series_identity,
                "interval_level": interval_level,
            },
        ),
        unavailable="Nije moguće izvršiti ORDO forecast.",
    )


def methodologies(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/methodologies", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO metodologije.")


def goals(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/goals", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati razvojne ciljeve.")


def create_goal(token: str, *, organization_id: str, workspace_id: str, code: str, title: str, description: str, focus_area: str, status: str = "draft"):
    return _checked(request("POST", "/api/v1/ordo/analytics/goals", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "code": code, "title": title, "description": description, "focus_area": focus_area, "target_horizon": None, "status": status}), unavailable="Nije moguće sačuvati razvojni cilj.")


def scenarios(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/scenarios", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati scenarije.")


def create_scenario(token: str, *, organization_id: str, workspace_id: str, goal_id: str, name: str, description: str, assumptions: list[str], measures: list[str]):
    return _checked(request("POST", "/api/v1/ordo/analytics/scenarios", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "goal_id": goal_id, "name": name, "description": description, "assumptions": assumptions, "measures": measures}), unavailable="Nije moguće sačuvati ORDO scenario.")


def assessments(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/scenario-assessments", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati procene scenarija.")


def create_assessment(token: str, *, organization_id: str, workspace_id: str, scenario_id: str, analytics_run_id: str):
    return _checked(request("POST", "/api/v1/ordo/analytics/scenario-assessments", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "scenario_id": scenario_id, "analytics_run_id": analytics_run_id}), unavailable="Nije moguće kreirati evidence-only procenu scenarija.")


def syntheses(token: str, organization_id: str, workspace_id: str):
    return _checked(request("GET", "/api/v1/ordo/analytics/syntheses", token=token, params={"organization_id": organization_id, "workspace_id": workspace_id}), unavailable="Nije moguće učitati ORDO AI sinteze.")


def create_synthesis(token: str, *, organization_id: str, workspace_id: str, analytics_run_id: str, synthesis_type: str, scenario_id: str | None = None):
    return _checked(request("POST", "/api/v1/ordo/analytics/syntheses", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "analytics_run_id": analytics_run_id, "scenario_id": scenario_id, "synthesis_type": synthesis_type, "model_key": None}), unavailable="Nije moguće pokrenuti ORDO AI sintezu.")


def review_synthesis(token: str, *, synthesis_id: str, organization_id: str, workspace_id: str, decision: str, reviewer_note: str = ""):
    return _checked(request("POST", f"/api/v1/ordo/analytics/syntheses/{synthesis_id}/review", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "decision": decision, "reviewer_note": reviewer_note}), unavailable="Nije moguće evidentirati human review.")


def scenario_status(token: str, *, scenario_id: str, organization_id: str, workspace_id: str, status: str):
    return _checked(request("POST", f"/api/v1/ordo/analytics/scenarios/{scenario_id}/status", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "status": status}), unavailable="Nije moguće promeniti status scenarija.")


def review_assessment(token: str, *, assessment_id: str, organization_id: str, workspace_id: str, decision: str, reviewer_note: str):
    return _checked(request("POST", f"/api/v1/ordo/analytics/scenario-assessments/{assessment_id}/review", token=token, json={"organization_id": organization_id, "workspace_id": workspace_id, "decision": decision, "reviewer_note": reviewer_note}), unavailable="Nije moguće sačuvati pregled procene.")
