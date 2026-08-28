from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def _login(client: httpx.Client, base: str, email: str, password: str, expected: set[str]) -> None:
    response = client.post(f"{base}/api/v1/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise RuntimeError(f"login failed for {email}: {response.status_code} {response.text[:300]}")
    payload = response.json()
    token = payload.get("access_token") or payload.get("token")
    if not token:
        raise RuntimeError(f"login response did not contain an opaque access token for {email}")
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get(f"{base}/api/v1/auth/me", headers=headers)
    me.raise_for_status()
    context = client.get(f"{base}/api/v1/app-context", headers=headers)
    context.raise_for_status()
    data = context.json()
    text = json.dumps(data, sort_keys=True)
    present = {code for code in {"SIMPA", "ORDO"} if code in text}
    if present != expected:
        raise RuntimeError(f"product context mismatch for {email}: expected={sorted(expected)} got={sorted(present)}")
    logout = client.post(f"{base}/api/v1/auth/logout", headers=headers)
    if logout.status_code not in {200, 204}:
        raise RuntimeError(f"logout failed for {email}: {logout.status_code}")
    print(f"PASS auth context {email} -> {','.join(sorted(expected))}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://localhost:8443")
    parser.add_argument("--credentials", required=True, type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    credentials = json.loads(args.credentials.read_text())
    with httpx.Client(verify=False, timeout=10, follow_redirects=True) as client:
        health = client.get(f"{base}/api/v1/health")
        health.raise_for_status()
        for header, expected in {
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
        }.items():
            if health.headers.get(header, "").casefold() != expected.casefold():
                raise RuntimeError(f"missing/incorrect security header {header}: {health.headers.get(header)!r}")
        if not health.headers.get("x-request-id"):
            raise RuntimeError("X-Request-ID missing")
        if not health.headers.get("strict-transport-security"):
            raise RuntimeError("HSTS missing in production-shaped staging")
        print("PASS HTTPS health + ISI-14 security headers")

        ready = client.get(f"{base}/api/v1/readiness")
        ready.raise_for_status()
        if ready.json().get("status") != "ready":
            raise RuntimeError(f"readiness not ready: {ready.text}")
        print("PASS readiness postgres/redis/object-storage")

        robots = client.get(f"{base}/robots.txt")
        robots.raise_for_status()
        if "Disallow: /" not in robots.text or "noindex" not in robots.headers.get("x-robots-tag", ""):
            raise RuntimeError("staging robots/noindex contract failed")
        print("PASS staging robots/noindex")

        public_statuses = {}
        draft_markers = (
            "LOCAL PREVIEW",
            "DRAFT CONTENT",
            "PUBLIC_PREVIEW_DRAFTS",
        )
        for public_path in ("/", "/en/", "/simpa/", "/ordo/"):
            public = client.get(f"{base}{public_path}")
            if public.status_code not in {200, 404}:
                raise RuntimeError(
                    f"unexpected production-mode public route status {public_path}: {public.status_code}"
                )
            upper_body = public.text.upper()
            leaked = [marker for marker in draft_markers if marker in upper_body]
            if leaked:
                raise RuntimeError(f"draft preview leaked on {public_path}: {leaked}")
            public_statuses[public_path] = public.status_code
        print(f"PASS public draft-publication safety statuses={public_statuses}")

        app = client.get(f"{base}/app/")
        if app.status_code >= 500:
            raise RuntimeError(f"Streamlit proxy failed: {app.status_code}")
        print(f"PASS /app proxy status={app.status_code}")

        _login(client, base, credentials["simpa_email"], credentials["password"], {"SIMPA"})
        _login(client, base, credentials["ordo_email"], credentials["password"], {"ORDO"})
        _login(client, base, credentials["dual_email"], credentials["password"], {"SIMPA", "ORDO"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
