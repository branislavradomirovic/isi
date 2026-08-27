from __future__ import annotations

import argparse
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8003")
    parser.add_argument("--email", default="isi05-dual@example.com")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    login = httpx.post(f"{base}/api/v1/auth/login", json={"email": args.email, "password": args.password}, timeout=10)
    if login.status_code != 200:
        print(f"FAIL login: {login.status_code} {login.text}")
        return 1
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    context = httpx.get(f"{base}/api/v1/app-context", headers=headers, timeout=10)
    if context.status_code != 200:
        print(f"FAIL app-context: {context.status_code} {context.text}")
        return 1
    payload = context.json()
    checked = 0
    for org in payload.get("organizations", []):
        for product in org.get("products", []):
            workspaces = product.get("workspaces", [])
            if not workspaces:
                continue
            params = {
                "organization_id": str(org["id"]),
                "product_code": product["code"],
                "workspace_id": str(workspaces[0]["id"]),
            }
            response = httpx.get(f"{base}/api/v1/data/sources", headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                print(f"FAIL {product['code']} data catalog: {response.status_code} {response.text}")
                return 1
            print(f"PASS {product['code']} data catalog -> {len(response.json())} source(s)")
            checked += 1
    if checked == 0:
        print("FAIL no accessible workspace found for data smoke")
        return 1
    httpx.post(f"{base}/api/v1/auth/logout", headers=headers, timeout=10)
    print("ISI-06 shared data API smoke PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
