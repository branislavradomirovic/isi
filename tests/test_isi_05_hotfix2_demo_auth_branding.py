from pathlib import Path

from pydantic import TypeAdapter, EmailStr

from tools.provision_local_app_shell_demo import PROFILE_EMAILS, PROFILE_PRODUCTS


ROOT = Path(__file__).resolve().parents[1]


def test_demo_emails_are_accepted_by_fastapi_email_contract():
    adapter = TypeAdapter(EmailStr)
    for email in PROFILE_EMAILS.values():
        assert str(adapter.validate_python(email)) == email
        assert not email.endswith(".local")


def test_demo_org_entitlement_is_not_profile_specific_anymore():
    source = (ROOT / "tools" / "provision_local_app_shell_demo.py").read_text()
    assert "entitlement.is_active = True" in source
    assert "entitlement.is_active = product_code in products" not in source
    assert PROFILE_PRODUCTS["simpa"] == ("SIMPA",)
    assert PROFILE_PRODUCTS["ordo"] == ("ORDO",)
    assert PROFILE_PRODUCTS["dual"] == ("SIMPA", "ORDO")


def test_login_brand_uses_centered_official_asset_without_visible_white_artboard():
    app = (ROOT / "src" / "streamlit_app" / "app.py").read_text()
    css = (ROOT / "src" / "streamlit_app" / "assets" / "app-shell.css").read_text()
    assert "isi-logo-transparent.svg" in app
    assert "isi-brand-lockup" in app
    assert "data:image/svg+xml;base64" in app
    assert "justify-content: center" in css
    assert "mix-blend-mode: multiply" in css
    assert "background: transparent !important" in css


def test_local_http_smoke_gate_exists_and_covers_three_profiles():
    smoke = (ROOT / "tools" / "smoke_local_app_shell_login.py").read_text()
    for email in PROFILE_EMAILS.values():
        assert email in smoke
    assert "/api/v1/auth/login" in smoke
    assert "/api/v1/auth/me" in smoke
    assert "/api/v1/app-context" in smoke
    assert "/api/v1/app-shell" in smoke
    assert "wrong-password negative control" in smoke
