from __future__ import annotations

import time

import httpx

from src.platform.auth.delivery import get_auth_delivery

EXPECTED = {"ISI email verification", "ISI password reset", "ISI organization invitation"}
RECIPIENT = "isi15-mailpit@example.com"


def _subjects(payload: object) -> set[str]:
    found: set[str] = set()
    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).casefold() == "subject" and isinstance(child, str):
                    found.add(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(payload)
    return found


def main() -> int:
    delivery = get_auth_delivery()
    delivery.send_email_verification(email=RECIPIENT, token="isi15-verification-probe")
    delivery.send_password_reset(email=RECIPIENT, token="isi15-reset-probe")
    delivery.send_invitation(email=RECIPIENT, token="isi15-invitation-probe")

    deadline = time.time() + 15
    last: set[str] = set()
    while time.time() < deadline:
        response = httpx.get("http://mailpit:8025/api/v1/messages", timeout=3)
        response.raise_for_status()
        last = _subjects(response.json())
        if EXPECTED.issubset(last):
            print("PASS SMTP verification/reset/invitation captured by Mailpit")
            return 0
        time.sleep(0.25)
    raise RuntimeError(f"Mailpit did not expose all expected messages; subjects={sorted(last)}")


if __name__ == "__main__":
    raise SystemExit(main())
