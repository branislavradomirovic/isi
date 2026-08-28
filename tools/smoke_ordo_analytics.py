from __future__ import annotations

import os
import uuid

import requests

BASE = os.environ.get("ISI_API_BASE_URL", "http://127.0.0.1:8009").rstrip("/")
PASSWORD = os.environ.get("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")
EMAIL = "isi05-ordo@example.com"


def call(method: str, path: str, *, token: str | None = None, expected: int = 200, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, BASE + path, headers=headers, timeout=180, **kwargs)
    if response.status_code != expected:
        raise SystemExit(f"{method} {path}: expected {expected}, got {response.status_code}: {response.text[:1200]}")
    return response.json() if response.content else None


login = call("POST", "/api/v1/auth/login", expected=200, json={"email": EMAIL, "password": PASSWORD})
token = login["access_token"]
context = call("GET", "/api/v1/app-context", token=token)
org = context["organizations"][0]
product = next(item for item in org["products"] if item["code"] == "ORDO")
workspace = product["workspaces"][0]
org_id, ws_id = str(org["id"]), str(workspace["id"])

summary = call("GET", "/api/v1/ordo/analytics/summary", token=token, params={"organization_id": org_id, "workspace_id": ws_id})
assert "evidence_quality_score" in summary
assert "not a competitiveness" in summary["semantic_notice"]
assert "dimension_coverage" in summary and "pillar_coverage" in summary
print(f"PASS ORDO analytics summary -> observations={summary['observation_count']} quality={summary['evidence_quality_score']}")

run = call("POST", "/api/v1/ordo/analytics/runs", token=token, expected=201, json={"organization_id": org_id, "workspace_id": ws_id, "monitoring_cycle_id": None})
print(f"PASS ORDO analytics snapshot -> {run['id']}")

catalog = call("GET", "/api/v1/ordo/catalog", token=token, params={"organization_id": org_id, "workspace_id": ws_id})
conceptual = next(item for item in catalog["indicators"] if item["methodology_status"] == "conceptual")
blocked = requests.post(
    BASE + "/api/v1/ordo/analytics/compute",
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "indicator_code": conceptual["code"],
        "monitoring_cycle_id": None,
        "analytics_run_id": run["id"],
    },
)
if blocked.status_code != 409 or blocked.json().get("detail") != "methodology_not_validated":
    raise SystemExit(f"unvalidated ORDO methodology negative control failed: {blocked.status_code} {blocked.text}")
print("PASS conceptual ORDO indicator computation blocked -> methodology_not_validated")

suffix = uuid.uuid4().hex[:8]
goal = call(
    "POST",
    "/api/v1/ordo/analytics/goals",
    token=token,
    expected=201,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "code": f"QA-{suffix}",
        "title": "QA razvojni cilj destinacije",
        "description": "Testira evidence-bounded ORDO scenario workflow bez predikcije.",
        "focus_area": "destination_development",
        "target_horizon": None,
        "status": "draft",
    },
)
scenario = call(
    "POST",
    "/api/v1/ordo/analytics/scenarios",
    token=token,
    expected=201,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "goal_id": goal["id"],
        "name": f"QA scenario {suffix}",
        "description": "User-authored scenario used only for QA.",
        "assumptions": ["Pretpostavka za QA, nije činjenica"],
        "measures": ["Mera za razmatranje u QA"],
    },
)
assessment = call(
    "POST",
    "/api/v1/ordo/analytics/scenario-assessments",
    token=token,
    expected=201,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "scenario_id": scenario["id"],
        "analytics_run_id": run["id"],
    },
)
if assessment["forecast_performed"] is not False:
    raise SystemExit(f"scenario assessment illegally forecasted: {assessment}")
if assessment["assessment"].get("assessment_mode") != "evidence_readiness_only":
    raise SystemExit(f"unexpected scenario assessment mode: {assessment}")
print("PASS ORDO scenario evidence-only assessment -> forecast_performed=false")

synthesis = call(
    "POST",
    "/api/v1/ordo/analytics/syntheses",
    token=token,
    expected=202,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "analytics_run_id": run["id"],
        "scenario_id": scenario["id"],
        "synthesis_type": "scenario_review",
        "model_key": "isi-ollama-chat-default",
    },
)
job = synthesis["job"]
if job["effective_provider_policy"] != "local_only":
    raise SystemExit(f"expected local_only, got {job['effective_provider_policy']}")
if job["human_review_status"] != "pending":
    raise SystemExit(f"expected pending review, got {job['human_review_status']}")
if job["provider_name"] != "ollama":
    raise SystemExit(f"expected real Ollama provider, got {job['provider_name']}")
if job["model_name"] != "qwen2.5:7b-instruct":
    raise SystemExit(f"expected qwen2.5:7b-instruct, got {job['model_name']}")
if job["status"] != "review_required":
    raise SystemExit(f"expected review_required, got {job['status']}: {job.get('error_message')}")
structured = job.get("structured_output") or {}
if structured.get("human_review_required") is not True:
    raise SystemExit(f"structured output did not require human review: {structured}")
if structured.get("forecast_performed") is not False:
    raise SystemExit(f"structured output claimed forecast: {structured}")
print(f"PASS real ORDO Ollama scenario synthesis -> provider={job['provider_name']} model={job['model_name']} status={job['status']}")

review = call(
    "POST",
    f"/api/v1/ordo/analytics/syntheses/{synthesis['id']}/review",
    token=token,
    json={
        "organization_id": org_id,
        "workspace_id": ws_id,
        "decision": "accepted",
        "reviewer_note": "ISI-11 local QA human review",
    },
)
assert review["review_status"] == "accepted" and review["human_review_status"] == "accepted"
print("PASS explicit ORDO human review -> accepted")

simpa_login = call("POST", "/api/v1/auth/login", expected=200, json={"email": "isi05-simpa@example.com", "password": PASSWORD})
simpa_context = call("GET", "/api/v1/app-context", token=simpa_login["access_token"])
simpa_org = simpa_context["organizations"][0]
simpa_product = next(item for item in simpa_org["products"] if item["code"] == "SIMPA")
simpa_ws = simpa_product["workspaces"][0]
negative = requests.get(
    BASE + "/api/v1/ordo/analytics/summary",
    headers={"Authorization": f"Bearer {simpa_login['access_token']}"},
    timeout=30,
    params={"organization_id": str(simpa_org["id"]), "workspace_id": str(simpa_ws["id"])},
)
if negative.status_code != 403:
    raise SystemExit(f"SIMPA negative control expected 403, got {negative.status_code}: {negative.text}")
print("PASS SIMPA negative control -> 403")
print("ISI-11 ORDO analytics + AI API smoke PASS")
