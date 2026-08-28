from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode

from src.core.config import get_settings


class AuthDeliveryError(RuntimeError):
    pass


class AuthDelivery(Protocol):
    def send_email_verification(self, *, email: str, token: str) -> None: ...
    def send_password_reset(self, *, email: str, token: str) -> None: ...
    def send_invitation(self, *, email: str, token: str) -> None: ...


class NullAuthDelivery:
    """Development adapter. Production/staging deployment must use a real adapter."""

    def send_email_verification(self, *, email: str, token: str) -> None:
        return None

    def send_password_reset(self, *, email: str, token: str) -> None:
        return None

    def send_invitation(self, *, email: str, token: str) -> None:
        return None


@dataclass(frozen=True)
class SMTPAuthDelivery:
    host: str
    port: int
    from_email: str
    app_base_url: str
    username: str = ""
    password: str = ""
    use_tls: bool = False
    starttls: bool = False
    timeout_seconds: int = 10

    def _send(self, *, email: str, subject: str, body: str) -> None:
        if not self.host or not self.from_email:
            raise AuthDeliveryError("SMTP delivery is not fully configured")
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

        smtp_class = smtplib.SMTP_SSL if self.use_tls else smtplib.SMTP
        context = ssl.create_default_context()
        try:
            if self.use_tls:
                client = smtp_class(self.host, self.port, timeout=self.timeout_seconds, context=context)
            else:
                client = smtp_class(self.host, self.port, timeout=self.timeout_seconds)
            with client:
                client.ehlo()
                if self.starttls and not self.use_tls:
                    client.starttls(context=context)
                    client.ehlo()
                if self.username:
                    client.login(self.username, self.password)
                client.send_message(message)
        except Exception as exc:
            raise AuthDeliveryError("SMTP delivery failed") from exc

    def _link(self, key: str, token: str) -> str:
        base = self.app_base_url.rstrip("/") + "/"
        return f"{base}?{urlencode({key: token})}"

    def send_email_verification(self, *, email: str, token: str) -> None:
        link = self._link("verify_token", token)
        self._send(
            email=email,
            subject="ISI email verification",
            body=f"Verify your ISI email address using this one-time link:\n\n{link}\n",
        )

    def send_password_reset(self, *, email: str, token: str) -> None:
        link = self._link("reset_token", token)
        self._send(
            email=email,
            subject="ISI password reset",
            body=f"Reset your ISI password using this one-time link:\n\n{link}\n",
        )

    def send_invitation(self, *, email: str, token: str) -> None:
        link = self._link("invitation_token", token)
        self._send(
            email=email,
            subject="ISI organization invitation",
            body=(
                "You have been invited to an ISI organization. "
                "Use the one-time invitation link below.\n\n"
                f"{link}\n"
            ),
        )


_delivery = NullAuthDelivery()


def auth_delivery_configured() -> bool:
    settings = get_settings()
    mode = str(getattr(settings, "auth_delivery_mode", "null") or "null").strip().casefold()
    if mode == "smtp":
        return bool(str(getattr(settings, "smtp_host", "") or "").strip()) and bool(
            str(getattr(settings, "smtp_from_email", "") or "").strip()
        )
    return False


def get_auth_delivery() -> AuthDelivery:
    settings = get_settings()
    mode = str(getattr(settings, "auth_delivery_mode", "null") or "null").strip().casefold()
    if mode in {"", "null", "none", "development"}:
        return _delivery
    if mode == "smtp":
        if not auth_delivery_configured():
            raise AuthDeliveryError("SMTP auth delivery is not configured")
        return SMTPAuthDelivery(
            host=str(getattr(settings, "smtp_host", "")),
            port=int(getattr(settings, "smtp_port", 25)),
            from_email=str(getattr(settings, "smtp_from_email", "")),
            app_base_url=str(getattr(settings, "app_base_url", "")),
            username=str(getattr(settings, "smtp_username", "")),
            password=str(getattr(settings, "smtp_password", "")),
            use_tls=bool(getattr(settings, "smtp_use_tls", False)),
            starttls=bool(getattr(settings, "smtp_starttls", False)),
            timeout_seconds=int(getattr(settings, "smtp_timeout_seconds", 10)),
        )
    raise AuthDeliveryError(f"unsupported AUTH_DELIVERY_MODE: {mode}")
