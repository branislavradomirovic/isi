from __future__ import annotations

import os
import sys
import httpx

BASE = os.getenv("ISI_API_BASE_URL", "http://127.0.0.1:8006").rstrip("/")
PASSWORD = os.getenv("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")


def login(email: str) -> str:
    r = httpx.post(f"{BASE}/api/v1/auth/login", json={"email": email, "password": PASSWORD}, timeout=10)
    if r.status_code != 200:
        raise SystemExit(f"login failed {email}: {r.status_code} {r.text[:300]}")
    return r.json()["access_token"]


def get_context(token: str):
    r = httpx.get(f"{BASE}/api/v1/app-context", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status(); return r.json()


def simpa_scope(context: dict):
    for org in context.get("organizations", []):
        for product in org.get("products", []):
            if product.get("code") == "SIMPA" and product.get("workspaces"):
                return str(org["id"]), str(product["workspaces"][0]["id"])
    raise SystemExit("SIMPA scope missing from QA identity")


def main() -> int:
    simpa_token = login("isi05-simpa@example.com")
    ordo_token = login("isi05-ordo@example.com")
    org_id, workspace_id = simpa_scope(get_context(simpa_token))
    headers = {"Authorization": f"Bearer {simpa_token}"}
    params = {"organization_id": org_id, "workspace_id": workspace_id}
    r = httpx.get(f"{BASE}/api/v1/simpa/catalog", headers=headers, params=params, timeout=10)
    r.raise_for_status(); catalog = r.json()
    assert len(catalog["dimensions"]) == 9
    assert len(catalog["source_types"]) == 9
    assert len(catalog["indicators"]) == 15
    print("PASS SIMPA conceptual catalog -> 9 dimensions / 9 source types / 15 indicators")
    r = httpx.get(f"{BASE}/api/v1/simpa/foundation", headers=headers, params=params, timeout=10)
    r.raise_for_status(); foundation = r.json()
    assert foundation["product_code"] == "SIMPA"
    print(f"PASS SIMPA foundation -> configured={foundation['configured']} actors={foundation['actor_count']} observations={foundation['observation_count']}")
    denied = httpx.get(f"{BASE}/api/v1/simpa/catalog", headers={"Authorization": f"Bearer {ordo_token}"}, params=params, timeout=10)
    assert denied.status_code == 403, (denied.status_code, denied.text[:300])
    print("PASS ORDO-only negative control -> SIMPA scope 403")
    print("ISI-08 SIMPA domain API smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
