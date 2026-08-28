from __future__ import annotations

import os
import time
import requests
from sqlalchemy.orm import Session

from src.core.database import build_engine
from src.platform.security.models import SecurityRateLimit
from src.platform.security.service import rate_limit_key

BASE = os.environ.get("ISI_API_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
PASSWORD = os.environ.get("ISI_DEMO_PASSWORD", "ISI05-Demo-QA-2026!")

health = requests.get(BASE + "/api/v1/health", timeout=20)
health.raise_for_status()
for header in ("x-content-type-options", "x-frame-options", "referrer-policy", "content-security-policy", "x-request-id"):
    if not health.headers.get(header):
        raise SystemExit(f"missing security header: {header}")
print("PASS security headers / request id")

valid = requests.post(BASE + "/api/v1/auth/login", timeout=30, json={"email": "isi05-dual@example.com", "password": PASSWORD})
if valid.status_code != 200:
    raise SystemExit(f"valid demo login failed: {valid.status_code} {valid.text[:500]}")
if valid.headers.get("cache-control") != "no-store":
    raise SystemExit("auth response missing Cache-Control: no-store")
token = valid.json()["access_token"]
me = requests.get(BASE + "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=20)
if me.status_code != 200:
    raise SystemExit(f"authenticated session smoke failed: {me.status_code} {me.text[:500]}")
print("PASS valid login / session / auth no-store")

email = f"isi14-throttle-{int(time.time())}@example.com"
ip = "127.0.0.1"
try:
    for attempt in range(5):
        r = requests.post(BASE + "/api/v1/auth/login", timeout=30, json={"email": email, "password": "wrong-password-value"})
        if r.status_code != 401:
            raise SystemExit(f"failed login #{attempt+1}: expected 401, got {r.status_code}: {r.text[:300]}")
    r = requests.post(BASE + "/api/v1/auth/login", timeout=30, json={"email": email, "password": "wrong-password-value"})
    if r.status_code != 429 or not r.headers.get("retry-after"):
        raise SystemExit(f"throttle gate: expected 429 + Retry-After, got {r.status_code}: {r.text[:300]}")
    print("PASS database-backed login throttle -> 429")
finally:
    key = rate_limit_key("login", email, ip)
    with Session(build_engine()) as db:
        row = db.get(SecurityRateLimit, key)
        if row is not None:
            db.delete(row)
            db.commit()

print("ISI-14 security hardening API smoke PASS")
