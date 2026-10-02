from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import api_client
from src.streamlit_app.shared_help_workspace import PUBLIC_HELP_TOPIC_IDS


@pytest.mark.parametrize("locale,label", [("sr-Latn", "Pomoć"), ("en", "Help (Serbian)")])
@pytest.mark.parametrize("template", ["header.html", "footer.html"])
def test_public_templates_render_application_help_entry(template, locale, label):
    env = Environment(loader=FileSystemLoader("src/public/templates/partials"), autoescape=select_autoescape())
    rendered = env.get_template(template).render(
        locale=locale, app_url="https://example.test/app/", page={"page_key": "home"},
        navigation=[], alternate_path=None,
    )
    assert 'href="https://example.test/app/?help=public"' in rendered
    assert label in rendered
    assert "invitation_token=" not in rendered


@pytest.mark.parametrize("authenticated", [False, True])
def test_public_help_precedes_auth_and_private_context(monkeypatch, authenticated):
    def forbidden(*args, **kwargs):
        pytest.fail("Public Help attempted authentication or tenant access")
    for fn in ("app_context", "app_shell", "login", "accept_invitation", "confirm_email_verification", "confirm_password_reset"):
        monkeypatch.setattr(api_client, fn, forbidden)
    app = AppTest.from_file(str(Path("src/streamlit_app/app.py").resolve()), default_timeout=20)
    app.query_params["help"] = "public"
    if authenticated:
        import secrets
        app.session_state["isi_access_token"] = secrets.token_urlsafe(32)
    app.run()
    assert not app.exception
    assert not app.text_input
    assert len(app.selectbox) == 1
    assert len(app.selectbox[0].options) == 6
    assert PUBLIC_HELP_TOPIC_IDS == ("ISI-H01", "ISI-H02", "ISI-H03", "ISI-H04", "ISI-H05", "ISI-H11")
    for topic_id in PUBLIC_HELP_TOPIC_IDS:
        app.selectbox[0].select(topic_id).run()
        assert not app.exception
    assert all("ISI-H07" not in option and "ISI-H09" not in option for option in app.selectbox[0].options)


def test_public_return_clears_sensitive_link_without_consuming_it(monkeypatch):
    import secrets
    monkeypatch.setattr(api_client, "confirm_email_verification", lambda *args: pytest.fail("No implicit confirmation"))
    app = AppTest.from_file(str(Path("src/streamlit_app/app.py").resolve()), default_timeout=20)
    app.query_params.update({"help": "public", "verify_token": secrets.token_urlsafe(32)})
    app.run()
    next(b for b in app.button if b.label == "Nazad na platformu").click().run()
    assert not app.exception
    assert not app.query_params
    assert any(b.label == "Prijavi se" for b in app.button)


@pytest.mark.parametrize("product", ["simpa", "ordo"])
def test_existing_domain_help_still_rejects_other_product(product):
    other = "ORDO" if product == "simpa" else "SIMPA"
    script = f'from src.streamlit_app.{product}_help_workspace import render_{product}_help\nrender_{product}_help(shell={{"product": {{"code": "{other}"}}}})'
    app = AppTest.from_string(script).run()
    assert not app.exception
    assert not app.selectbox
    assert "samo" in app.info[0].value
    guide = Path(f"docs/help/{product.upper()}-USER-GUIDE.md").read_text()
    assert "human" in guide.casefold()
