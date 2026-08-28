from __future__ import annotations

import os
import uuid

import requests

BASE = os.environ.get("ISI_API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
PASSWORD = os.environ.get("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")
EMAIL = "isi05-dual@example.com"


def call(method: str, path: str, *, token: str | None = None, expected: int = 200, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, BASE + path, headers=headers, timeout=60, **kwargs)
    if response.status_code != expected:
        raise SystemExit(f"{method} {path}: expected {expected}, got {response.status_code}: {response.text[:1600]}")
    return response.json() if response.content else None


def product_scope(context: dict, code: str):
    org = context["organizations"][0]
    product = next(item for item in org["products"] if item["code"] == code)
    workspace = product["workspaces"][0]
    return str(org["id"]), str(workspace["id"])


login = call("POST", "/api/v1/auth/login", expected=200, json={"email": EMAIL, "password": PASSWORD})
token = login["access_token"]
context = call("GET", "/api/v1/app-context", token=token)

created = {}
for product_code in ("SIMPA", "ORDO"):
    org_id, ws_id = product_scope(context, product_code)
    analytics_path = "/api/v1/simpa/analytics/runs" if product_code == "SIMPA" else "/api/v1/ordo/analytics/runs"
    run = call("POST", analytics_path, token=token, expected=201, json={"organization_id": org_id, "workspace_id": ws_id, "monitoring_cycle_id": None})
    report_type = "monitoring_summary" if product_code == "SIMPA" else "destination_snapshot"
    title = f"{product_code} reporting QA {uuid.uuid4().hex[:8]}"
    report = call(
        "POST",
        "/api/v1/reporting/reports",
        token=token,
        expected=201,
        json={
            "organization_id": org_id,
            "workspace_id": ws_id,
            "product_code": product_code,
            "title": title,
            "report_type": report_type,
            "source_kind": "analytics_run",
            "source_id": run["id"],
        },
    )
    version = report["version"]
    if version["status"] != "draft":
        raise SystemExit(f"{product_code}: expected draft, got {version['status']}")
    if not version["source_manifest"] or any(item["product_code"] != product_code for item in version["source_manifest"]):
        raise SystemExit(f"{product_code}: provenance product isolation failed: {version['source_manifest']}")
    if len(version["content_sha256"]) != 64 or len(version["source_manifest_sha256"]) != 64:
        raise SystemExit(f"{product_code}: missing immutable checksums")
    if product_code == "ORDO" and version["content"].get("forecast_performed") is not False:
        raise SystemExit(f"ORDO report illegally claims forecast: {version['content']}")
    print(f"PASS {product_code} draft reporting version -> {version['id']}")

    submitted = call(
        "POST",
        f"/api/v1/reporting/versions/{version['id']}/submit",
        token=token,
        json={"organization_id": org_id, "workspace_id": ws_id, "product_code": product_code},
    )
    if submitted["status"] != "in_review":
        raise SystemExit(f"{product_code}: submit lifecycle failed: {submitted}")
    reviewed = call(
        "POST",
        f"/api/v1/reporting/versions/{version['id']}/review",
        token=token,
        json={"organization_id": org_id, "workspace_id": ws_id, "product_code": product_code, "decision": "approved", "note": "ISI-12 local QA review"},
    )
    if reviewed["version"]["status"] != "approved":
        raise SystemExit(f"{product_code}: review lifecycle failed: {reviewed}")
    artifact = call(
        "POST",
        f"/api/v1/reporting/versions/{version['id']}/exports",
        token=token,
        expected=201,
        json={"organization_id": org_id, "workspace_id": ws_id, "product_code": product_code, "format": "html"},
    )
    if "<!doctype html>" not in artifact["content_text"] or len(artifact["sha256"]) != 64:
        raise SystemExit(f"{product_code}: export artifact failed")
    published = call(
        "POST",
        f"/api/v1/reporting/versions/{version['id']}/publish",
        token=token,
        json={"organization_id": org_id, "workspace_id": ws_id, "product_code": product_code},
    )
    if published["status"] != "published":
        raise SystemExit(f"{product_code}: publish lifecycle failed: {published}")
    detail = call(
        "GET",
        f"/api/v1/reporting/reports/{report['id']}",
        token=token,
        params={"organization_id": org_id, "workspace_id": ws_id, "product_code": product_code},
    )
    if detail["product_code"] != product_code or detail["versions"][0]["status"] != "published":
        raise SystemExit(f"{product_code}: final report state invalid: {detail}")
    print(f"PASS {product_code} reporting lifecycle -> draft / in_review / approved / published / html artifact")
    created[product_code] = {"org_id": org_id, "ws_id": ws_id, "report_id": report["id"]}

simpa_login = call("POST", "/api/v1/auth/login", expected=200, json={"email": "isi05-simpa@example.com", "password": PASSWORD})
negative = requests.get(
    BASE + "/api/v1/reporting/reports",
    headers={"Authorization": f"Bearer {simpa_login['access_token']}"},
    timeout=30,
    params={
        "organization_id": created["ORDO"]["org_id"],
        "workspace_id": created["ORDO"]["ws_id"],
        "product_code": "ORDO",
    },
)
if negative.status_code != 403:
    raise SystemExit(f"SIMPA-only -> ORDO reporting negative control expected 403, got {negative.status_code}: {negative.text}")
print("PASS SIMPA-only -> ORDO reporting negative control -> 403")
print("ISI-12 shared reporting API smoke PASS")
