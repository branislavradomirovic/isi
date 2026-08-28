from __future__ import annotations

import os
import requests

BASE = os.environ.get("ISI_API_BASE_URL", "http://127.0.0.1:8011").rstrip("/")
PASSWORD = os.environ.get("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")


def call(method: str, path: str, *, token: str | None = None, expected: int = 200, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, BASE + path, headers=headers, timeout=30, **kwargs)
    if response.status_code != expected:
        raise SystemExit(f"{method} {path}: expected {expected}, got {response.status_code}: {response.text[:1200]}")
    return response.json() if response.content else None


def login(email: str) -> str:
    return call("POST", "/api/v1/auth/login", json={"email": email, "password": PASSWORD})["access_token"]


def scope(context: dict, product_code: str):
    org = context["organizations"][0]
    product = next(item for item in org["products"] if item["code"] == product_code)
    return str(org["id"]), product


dual = login("isi05-dual@example.com")
context = call("GET", "/api/v1/app-context", token=dual)
for product_code in ("SIMPA", "ORDO"):
    org_id, product = scope(context, product_code)
    snapshot = call("GET", "/api/v1/administration/snapshot", token=dual, params={"organization_id": org_id, "product_code": product_code})
    if snapshot["product_code"] != product_code or snapshot["organization"]["id"] != org_id:
        raise SystemExit(f"{product_code}: administration scope mismatch")
    if not snapshot.get("entitlement") or not snapshot["entitlement"].get("is_active"):
        raise SystemExit(f"{product_code}: expected active read-only entitlement")
    if snapshot["capabilities"].get("members_manage"):
        response = requests.post(
            BASE + "/api/v1/administration/invitations",
            headers={"Authorization": f"Bearer {dual}"},
            timeout=30,
            json={"organization_id": org_id, "product_code": product_code, "email": f"isi13-{product_code.lower()}-guard@example.com", "role_code": "organization_admin"},
        )
        if response.status_code != 409 or response.json().get("detail") != "organization_admin_invitation_forbidden":
            raise SystemExit(f"{product_code}: organization-admin invitation escalation guard failed: {response.status_code} {response.text}")
    print(f"PASS {product_code} administration snapshot / entitlement boundary / escalation guard")

simpa = login("isi05-simpa@example.com")
ordo_org, _ = scope(context, "ORDO")
negative = requests.get(BASE + "/api/v1/administration/snapshot", headers={"Authorization": f"Bearer {simpa}"}, timeout=30, params={"organization_id": ordo_org, "product_code": "ORDO"})
if negative.status_code != 403:
    raise SystemExit(f"SIMPA-only -> ORDO administration negative control expected 403, got {negative.status_code}: {negative.text}")
print("PASS SIMPA-only -> ORDO administration negative control -> 403")
print("ISI-13 administration API smoke PASS")
