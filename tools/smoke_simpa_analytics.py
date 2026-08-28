from __future__ import annotations

import os
import time
import requests

BASE = os.environ.get("ISI_API_BASE_URL", "http://127.0.0.1:8007").rstrip("/")
PASSWORD = os.environ.get("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")
EMAIL = "isi05-simpa@example.com"


def call(method: str, path: str, *, token: str | None = None, expected: int = 200, **kwargs):
    headers = kwargs.pop("headers", {})
    if token: headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, BASE + path, headers=headers, timeout=180, **kwargs)
    if response.status_code != expected:
        raise SystemExit(f"{method} {path}: expected {expected}, got {response.status_code}: {response.text[:1200]}")
    return response.json() if response.content else None


login = call("POST", "/api/v1/auth/login", expected=200, json={"email": EMAIL, "password": PASSWORD})
token = login["access_token"]
context = call("GET", "/api/v1/app-context", token=token)
org = context["organizations"][0]
product = next(item for item in org["products"] if item["code"] == "SIMPA")
workspace = product["workspaces"][0]
org_id, ws_id = str(org["id"]), str(workspace["id"])

summary = call("GET", "/api/v1/simpa/analytics/summary", token=token, params={"organization_id": org_id, "workspace_id": ws_id})
assert "evidence_quality_score" in summary
assert summary["semantic_notice"].startswith("This score measures evidence quality")
print(f"PASS SIMPA analytics summary -> observations={summary['observation_count']} quality={summary['evidence_quality_score']}")

run = call("POST", "/api/v1/simpa/analytics/runs", token=token, expected=201, json={"organization_id": org_id, "workspace_id": ws_id, "monitoring_cycle_id": None})
print(f"PASS monitoring snapshot -> {run['id']}")

catalog = call("GET", "/api/v1/simpa/catalog", token=token, params={"organization_id": org_id, "workspace_id": ws_id})
conceptual = next(item for item in catalog["indicators"] if item["methodology_status"] == "conceptual")
blocked = requests.post(BASE + "/api/v1/simpa/analytics/compute", headers={"Authorization": f"Bearer {token}"}, timeout=30, json={"organization_id": org_id, "workspace_id": ws_id, "indicator_code": conceptual["code"], "monitoring_cycle_id": None, "analytics_run_id": run["id"]})
if blocked.status_code != 409 or blocked.json().get("detail") != "methodology_not_validated":
    raise SystemExit(f"unvalidated methodology negative control failed: {blocked.status_code} {blocked.text}")
print("PASS conceptual indicator computation blocked -> methodology_not_validated")

synthesis = call("POST", "/api/v1/simpa/analytics/syntheses", token=token, expected=202, json={"organization_id": org_id, "workspace_id": ws_id, "analytics_run_id": run["id"], "sensitivity": "sensitive", "model_key": "isi-ollama-chat-default"})
job = synthesis["job"]
if job["effective_provider_policy"] != "local_only": raise SystemExit(f"expected local_only, got {job['effective_provider_policy']}")
if job["human_review_status"] != "pending": raise SystemExit(f"expected pending review, got {job['human_review_status']}")
if job["provider_name"] != "ollama": raise SystemExit(f"expected real Ollama provider, got {job['provider_name']}")
if job["model_name"] != "qwen2.5:7b-instruct": raise SystemExit(f"expected qwen2.5:7b-instruct, got {job['model_name']}")
if job["status"] != "review_required": raise SystemExit(f"expected review_required, got {job['status']}: {job.get('error_message')}")
structured = job.get("structured_output") or {}
if structured.get("human_review_required") is not True: raise SystemExit(f"structured output did not require human review: {structured}")
print(f"PASS real SIMPA Ollama synthesis -> provider={job['provider_name']} model={job['model_name']} status={job['status']}")

review = call("POST", f"/api/v1/simpa/analytics/syntheses/{synthesis['id']}/review", token=token, json={"organization_id": org_id, "workspace_id": ws_id, "decision": "accepted", "reviewer_note": "ISI-09 local QA human review"})
assert review["review_status"] == "accepted" and review["human_review_status"] == "accepted"
print("PASS explicit human review -> accepted")

ordo_login = call("POST", "/api/v1/auth/login", expected=200, json={"email": "isi05-ordo@example.com", "password": PASSWORD})
ordo_context = call("GET", "/api/v1/app-context", token=ordo_login["access_token"])
ordo_org = ordo_context["organizations"][0]
ordo_product = next(item for item in ordo_org["products"] if item["code"] == "ORDO")
ordo_ws = ordo_product["workspaces"][0]
negative = requests.get(BASE + "/api/v1/simpa/analytics/summary", headers={"Authorization": f"Bearer {ordo_login['access_token']}"}, timeout=30, params={"organization_id": str(ordo_org["id"]), "workspace_id": str(ordo_ws["id"])})
if negative.status_code != 403:
    raise SystemExit(f"ORDO negative control expected 403, got {negative.status_code}: {negative.text}")
print("PASS ORDO negative control -> 403")
print("ISI-09 SIMPA analytics + AI API smoke PASS")
