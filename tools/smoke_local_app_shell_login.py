from __future__ import annotations

import argparse
import os
from typing import Any

import httpx


PROFILES = {
    "simpa": ("isi05-simpa@example.com", {"SIMPA"}),
    "ordo": ("isi05-ordo@example.com", {"ORDO"}),
    "dual": ("isi05-dual@example.com", {"SIMPA", "ORDO"}),
}


def _expect(response: httpx.Response, status: int, label: str) -> Any:
    if response.status_code != status:
        body = response.text[:1000]
        raise SystemExit(f"{label}: expected HTTP {status}, got {response.status_code}: {body}")
    if status == 204:
        return None
    return response.json()


def smoke(base_url: str, password: str) -> None:
    base_url = base_url.rstrip("/")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        health = client.get("/api/v1/health")
        _expect(health, 200, "health")

        for profile, (email, expected_products) in PROFILES.items():
            login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            payload = _expect(login, 200, f"{profile} login")
            token = payload.get("access_token")
            if not token:
                raise SystemExit(f"{profile} login: access_token missing")
            headers = {"Authorization": f"Bearer {token}"}

            me = _expect(client.get("/api/v1/auth/me", headers=headers), 200, f"{profile} me")
            if me.get("email") != email:
                raise SystemExit(f"{profile} me: expected {email}, got {me.get('email')}")

            context = _expect(client.get("/api/v1/app-context", headers=headers), 200, f"{profile} context")
            organizations = context.get("organizations") or []
            if len(organizations) != 1:
                raise SystemExit(f"{profile} context: expected exactly one demo organization, got {len(organizations)}")
            organization = organizations[0]
            actual_products = {item.get("code") for item in organization.get("products", [])}
            if actual_products != expected_products:
                raise SystemExit(
                    f"{profile} context: expected products {sorted(expected_products)}, got {sorted(actual_products)}"
                )

            for product in organization.get("products", []):
                workspaces = product.get("workspaces") or []
                if not workspaces:
                    raise SystemExit(f"{profile}/{product['code']}: no active demo workspace")
                params = {
                    "organization_id": organization["id"],
                    "product_code": product["code"],
                    "workspace_id": workspaces[0]["id"],
                }
                shell = _expect(
                    client.get("/api/v1/app-shell", headers=headers, params=params),
                    200,
                    f"{profile}/{product['code']} shell",
                )
                if shell.get("product", {}).get("code") != product["code"]:
                    raise SystemExit(f"{profile}/{product['code']}: shell product mismatch")

            _expect(client.post("/api/v1/auth/logout", headers=headers), 204, f"{profile} logout")
            print(f"PASS {profile}: {email} -> {', '.join(sorted(expected_products))}")

        bad = client.post(
            "/api/v1/auth/login",
            json={"email": PROFILES["dual"][0], "password": password + "-WRONG"},
        )
        _expect(bad, 401, "wrong-password negative control")
        print("PASS wrong-password negative control -> 401")


def main() -> None:
    parser = argparse.ArgumentParser(description="HTTP smoke test for ISI-05 local app-shell demo login")
    parser.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8002"))
    parser.add_argument("--password", default=os.getenv("ISI_DEMO_PASSWORD"))
    args = parser.parse_args()
    if not args.password:
        raise SystemExit("Provide --password or ISI_DEMO_PASSWORD")
    smoke(args.base_url, args.password)
    print("ISI-05 local demo auth smoke PASS")


if __name__ == "__main__":
    main()
