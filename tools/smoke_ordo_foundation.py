from __future__ import annotations

import os
import httpx

BASE = os.getenv("ISI_API_BASE_URL", "http://127.0.0.1:8008").rstrip("/")
PASSWORD = os.getenv("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")

def login(email: str) -> str:
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": email, "password": PASSWORD}, timeout=10)
    if r.status_code != 200: raise SystemExit(f"login failed {email}: {r.status_code} {r.text[:300]}")
    return r.json()["access_token"]

def context(token: str):
    r = httpx.get(f"{BASE}/api/v1/app-context", headers={"Authorization": f"Bearer {token}"}, timeout=10); r.raise_for_status(); return r.json()

def scope(ctx: dict, code: str):
    for org in ctx.get("organizations", []):
        for product in org.get("products", []):
            if product.get("code") == code and product.get("workspaces"): return str(org["id"]), str(product["workspaces"][0]["id"])
    raise SystemExit(f"{code} scope missing")

def main() -> int:
    ordo_token = login("isi05-ordo@example.com"); simpa_token = login("isi05-simpa@example.com")
    org_id, workspace_id = scope(context(ordo_token), "ORDO")
    headers = {"Authorization": f"Bearer {ordo_token}"}; params = {"organization_id": org_id, "workspace_id": workspace_id}
    r = httpx.get(f"{BASE}/api/v1/ordo/catalog", headers=headers, params=params, timeout=10); r.raise_for_status(); cat = r.json()
    assert len(cat["pillars"]) == 5 and len(cat["dimensions"]) == 9 and len(cat["source_types"]) == 12 and len(cat["indicators"]) == 15
    assert all(x["methodology_status"] == "conceptual" for x in cat["indicators"])
    print("PASS ORDO conceptual catalog -> 5 pillars / 9 dimensions / 12 source types / 15 indicators")
    r = httpx.get(f"{BASE}/api/v1/ordo/foundation", headers=headers, params=params, timeout=10); r.raise_for_status(); data = r.json(); assert data["product_code"] == "ORDO"
    print(f"PASS ORDO foundation -> configured={data['configured']} assets={data['asset_count']} stakeholders={data['stakeholder_count']}")
    denied = httpx.get(f"{BASE}/api/v1/ordo/catalog", headers={"Authorization": f"Bearer {simpa_token}"}, params=params, timeout=10)
    assert denied.status_code == 403, (denied.status_code, denied.text[:300])
    print("PASS SIMPA-only negative control -> ORDO scope 403")
    print("ISI-10 ORDO domain API smoke PASS")
    return 0

if __name__ == "__main__": raise SystemExit(main())
