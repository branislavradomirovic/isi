from __future__ import annotations

from typing import Protocol


class AuthDelivery(Protocol):
    def send_email_verification(self, *, email: str, token: str) -> None: ...

    def send_password_reset(self, *, email: str, token: str) -> None: ...


class NullAuthDelivery:
    """Default adapter until SMTP/provider infrastructure is explicitly implemented."""

    def send_email_verification(self, *, email: str, token: str) -> None:
        return None

    def send_password_reset(self, *, email: str, token: str) -> None:
        return None


_delivery = NullAuthDelivery()


def get_auth_delivery() -> AuthDelivery:
    return _delivery
