from src.platform.auth.delivery import SMTPAuthDelivery


class FakeSMTP:
    messages = []

    def __init__(self, host, port, timeout=None, **kwargs):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        return None

    def starttls(self, context=None):
        return None

    def login(self, username, password):
        return None

    def send_message(self, message):
        self.messages.append(message)


def test_smtp_adapter_builds_all_auth_messages(monkeypatch):
    import src.platform.auth.delivery as delivery

    FakeSMTP.messages = []
    monkeypatch.setattr(delivery.smtplib, "SMTP", FakeSMTP)
    adapter = SMTPAuthDelivery(
        host="mailpit",
        port=1025,
        from_email="staging@isi.example",
        app_base_url="https://localhost:8443/app",
    )
    adapter.send_email_verification(email="qa@example.com", token="verify")
    adapter.send_password_reset(email="qa@example.com", token="reset")
    adapter.send_invitation(email="qa@example.com", token="invite")
    assert [m["Subject"] for m in FakeSMTP.messages] == [
        "ISI email verification",
        "ISI password reset",
        "ISI organization invitation",
    ]
    bodies = "\n".join(m.get_content() for m in FakeSMTP.messages)
    assert "verify_token=verify" in bodies
    assert "reset_token=reset" in bodies
    assert "invitation_token=invite" in bodies
