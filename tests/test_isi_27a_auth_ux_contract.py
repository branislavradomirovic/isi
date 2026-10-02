from __future__ import annotations

import ast
from pathlib import Path
import secrets

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from src.streamlit_app import api_client, security_api

APP = "src/streamlit_app/app.py"
TOKEN_KEY = "isi_access_token"
QUERY_KEYS = ("invitation_token", "verify_token", "reset_token")


def _secret():
    return secrets.token_urlsafe(32)


def _app(key=None, *, authenticated=False):
    app = AppTest.from_file(str(Path(APP).resolve()), default_timeout=20)
    if key:
        app.query_params[key] = _secret()
    if authenticated:
        app.session_state[TOKEN_KEY] = _secret()
    return app


def _button(app, label):
    return next(button for button in app.button if button.label == label)


def _input(app, label, value):
    next(field for field in app.text_input if field.label == label).set_value(value)


def _no_exception(app):
    assert len(app.exception) == 0


@pytest.mark.parametrize("key", QUERY_KEYS)
def test_explicit_token_flow_does_not_execute_on_open_or_replace_active_session(monkeypatch, key):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected auth or private-context call")
    for name in ("accept_invitation", "confirm_email_verification", "confirm_password_reset", "app_context"):
        monkeypatch.setattr(api_client, name, forbidden)
    app = _app(key).run()
    _no_exception(app)
    assert key in app.query_params
    assert TOKEN_KEY not in app.session_state
    active = _app(key, authenticated=True)
    original = active.session_state[TOKEN_KEY]
    active.run()
    _no_exception(active)
    assert bool(active.session_state[TOKEN_KEY] == original)
    assert len(active.text_input) == 0
    assert "Već ste prijavljeni" in active.warning[0].value


def test_invitation_success_uses_only_returned_session_and_clears_query(monkeypatch):
    returned = _secret()
    received = []

    def accept(value, name, password):
        received.append(bool(value and name == "Test korisnik" and password))
        return {"access_token": returned}

    monkeypatch.setattr(api_client, "accept_invitation", accept)
    monkeypatch.setattr(api_client, "app_context", lambda token: {"organizations": []})
    monkeypatch.setattr(security_api, "list_sessions", lambda token: [])
    app = _app("invitation_token").run()
    _input(app, "Ime za prikaz", "Test korisnik")
    _input(app, "Lozinka", _secret())
    _button(app, "Prihvati poziv").click().run()
    _no_exception(app)
    assert received == [True]
    assert bool(app.session_state[TOKEN_KEY] == returned)
    assert not any(key in app.query_params for key in QUERY_KEYS)


def test_existing_invitee_can_omit_new_account_fields(monkeypatch):
    calls = []

    def accept(value, name, password):
        calls.append(name is None and password is None)
        return {"access_token": _secret()}

    monkeypatch.setattr(api_client, "accept_invitation", accept)
    monkeypatch.setattr(api_client, "app_context", lambda token: {"organizations": []})
    monkeypatch.setattr(security_api, "list_sessions", lambda token: [])
    app = _app("invitation_token").run()
    _button(app, "Prihvati poziv").click().run()
    _no_exception(app)
    assert calls == [True]


@pytest.mark.parametrize("key,method,label", [
    ("verify_token", "confirm_email_verification", "Potvrdi email"),
    ("reset_token", "confirm_password_reset", "Sačuvaj novu lozinku"),
])
def test_confirmation_success_clears_query_without_session(monkeypatch, key, method, label):
    calls = []
    monkeypatch.setattr(api_client, method, lambda *args: calls.append(len(args)))
    app = _app(key).run()
    if key == "reset_token":
        password = _secret()
        _input(app, "Nova lozinka", password)
        _input(app, "Potvrdite novu lozinku", password)
    _button(app, label).click().run()
    _no_exception(app)
    assert calls == [2 if key == "reset_token" else 1]
    assert not any(key in app.query_params for key in QUERY_KEYS)
    assert TOKEN_KEY not in app.session_state
    assert any(button.label == "Prijavi se" for button in app.button)
    assert "Promena je potvrđena" in app.success[0].value


def test_mismatched_password_does_not_call_backend(monkeypatch):
    def forbidden(*args):
        pytest.fail("Mismatched confirmation reached backend")
    monkeypatch.setattr(api_client, "confirm_password_reset", forbidden)
    app = _app("reset_token").run()
    _input(app, "Nova lozinka", _secret())
    _input(app, "Potvrdite novu lozinku", _secret())
    _button(app, "Sačuvaj novu lozinku").click().run()
    _no_exception(app)
    assert "nisu jednake" in app.error[0].value
    assert "reset_token" in app.query_params


@pytest.mark.parametrize("key,method,label", [
    ("invitation_token", "accept_invitation", "Prihvati poziv"),
    ("verify_token", "confirm_email_verification", "Potvrdi email"),
    ("reset_token", "confirm_password_reset", "Sačuvaj novu lozinku"),
])
@pytest.mark.parametrize("failure", [api_client.AuthFlowRejected, api_client.ApiUnavailable])
def test_failed_flow_is_bounded_and_does_not_clear_or_establish_session(monkeypatch, key, method, label, failure, caplog):
    sensitive = _secret()

    def reject(*args):
        raise failure(sensitive)

    monkeypatch.setattr(api_client, method, reject)
    app = _app(key).run()
    _button(app, label).click().run()
    _no_exception(app)
    assert key in app.query_params
    assert TOKEN_KEY not in app.session_state
    visible = " ".join(item.value for kind in (app.error, app.info, app.markdown, app.caption) for item in kind)
    assert sensitive not in visible and sensitive not in caplog.text
    assert "Zahtev nije potvrđen" in app.error[0].value


@pytest.mark.parametrize("query", [
    {"invitation_token": ""},
    {"reset_token": "short"},
    {"verify_token": ["a" * 21, "b" * 21]},
    {"verify_token": "a" * 21, "reset_token": "b" * 21},
])
def test_ambiguous_or_malformed_link_fails_closed(query):
    app = _app()
    app.query_params.update(query)
    app.run()
    _no_exception(app)
    assert app.error
    assert not app.text_input
    _button(app, "Nazad na prijavu").click().run()
    _no_exception(app)
    assert not any(key in app.query_params for key in QUERY_KEYS)


@pytest.mark.parametrize("code,method", [("reset", "request_password_reset"), ("verify", "request_email_verification")])
def test_login_recovery_never_renders_response_or_account_existence(monkeypatch, code, method):
    calls = []
    monkeypatch.setattr(api_client, method, lambda email: calls.append(bool(email)) or {"private": _secret()})
    app = _app().run()
    app.text_input(key=f"isi_recovery_email_{code}").set_value("reader@example.test")
    app.button(key=f"FormSubmitter:isi_recovery_{code}-Pošalji zahtev").click().run()
    _no_exception(app)
    assert calls == [True]
    assert "ne potvrđuje postojanje naloga niti isporuku" in app.info[0].value
    assert TOKEN_KEY not in app.session_state


@pytest.mark.parametrize("name,path,fields,status", [
    ("accept_invitation", "/invitations/accept", ("token", "display_name", "password"), 200),
    ("confirm_email_verification", "/email-verification/confirm", ("token",), 200),
    ("confirm_password_reset", "/password-reset/confirm", ("token", "new_password"), 200),
    ("request_password_reset", "/password-reset/request", ("email",), 202),
    ("request_email_verification", "/email-verification/request", ("email",), 202),
])
def test_client_calls_exact_existing_endpoint_without_bearer_or_query(monkeypatch, name, path, fields, status):
    calls = []
    value = _secret()

    def request(method, url, **kwargs):
        calls.append((method, url, set(kwargs["json"]), kwargs["headers"], kwargs["timeout"]))
        return httpx.Response(status, json={"access_token": value})

    monkeypatch.setattr(httpx, "request", request)
    result = getattr(api_client, name)(*(_secret() for _ in fields))
    assert calls == [("POST", api_client.API_BASE_URL + "/api/v1/auth" + path, set(fields), {}, 10.0)]
    if name == "accept_invitation":
        assert set(result) == {"access_token"}
        assert bool(result["access_token"] == value)
    else:
        assert result is None


@pytest.mark.parametrize("status", [400, 401, 403, 422, 429, 500, 503])
def test_client_errors_never_echo_response_payload(monkeypatch, status):
    sensitive = _secret()
    monkeypatch.setattr(api_client, "request", lambda *args, **kwargs: httpx.Response(status, text=sensitive))
    with pytest.raises((api_client.AuthFlowRejected, api_client.ApiUnavailable)) as error:
        api_client.confirm_password_reset(_secret(), _secret())
    assert sensitive not in str(error.value)


@pytest.mark.parametrize("body", [{}, {"access_token": None}, {"access_token": ""}, [], "invalid"])
def test_invitation_malformed_success_does_not_establish_session(monkeypatch, body):
    monkeypatch.setattr(api_client, "request", lambda *args, **kwargs: httpx.Response(200, json=body))
    with pytest.raises(api_client.ApiUnavailable):
        api_client.accept_invitation(_secret(), None, None)


def test_route_authority_has_exact_accepted_set_and_no_public_signup():
    tree = ast.parse(Path("src/api/auth_routes.py").read_text())
    routes = {
        (d.func.attr, ast.literal_eval(d.args[0]))
        for node in tree.body if isinstance(node, ast.FunctionDef)
        for d in node.decorator_list if isinstance(d, ast.Call)
        and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name)
        and d.func.value.id == "router"
    }
    assert routes == {
        ("post", "/login"), ("post", "/logout"), ("get", "/me"), ("get", "/sessions"),
        ("delete", "/sessions/{session_id}"), ("post", "/sessions/revoke-others"),
        ("post", "/assurance/password"), ("post", "/email-verification/request"),
        ("post", "/email-verification/confirm"), ("post", "/password-reset/request"),
        ("post", "/password-reset/confirm"), ("post", "/invitations/accept"),
    }
    app = _app().run()
    labels = [button.label.casefold() for button in app.button]
    assert not any("signup" in label or "register" in label or "registruj" in label for label in labels)
    delivery = Path("src/platform/auth/delivery.py").read_text()
    assert all(f'"{key}"' in delivery for key in QUERY_KEYS)


def test_auth_presentation_contains_no_secret_output_logging_or_file_write():
    source = Path(APP).read_text()
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"_render_auth_intent", "_render_recovery_requests", "_complete_auth_confirmation"}]
    assert len(functions) == 3
    for fn in functions:
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"print", "open"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"write_text", "write_bytes", "exception", "debug"}
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "st" and node.func.attr in {"write", "error", "info", "code", "markdown"}:
                    assert not any(isinstance(arg, ast.Name) and arg.id in {"value", "password", "confirmation", "result"} for arg in node.args)
    admin = Path("src/streamlit_app/administration_workspace.py").read_text()
    assert 'st.code(result["development_token"])' not in admin


def test_active_session_can_close_link_without_auth_mutation(monkeypatch):
    monkeypatch.setattr(api_client, "app_context", lambda token: {"organizations": []})
    monkeypatch.setattr(security_api, "list_sessions", lambda token: [])
    app = _app("invitation_token", authenticated=True)
    original = app.session_state[TOKEN_KEY]
    app.run()
    _button(app, "Zatvori link i nastavi postojeću sesiju").click().run()
    _no_exception(app)
    assert bool(app.session_state[TOKEN_KEY] == original)
    assert not any(key in app.query_params for key in QUERY_KEYS)
    assert any("Pristup nije dodeljen" in item.value for item in app.markdown)
    _button(app, "ISI Help · Pomoć").click().run()
    _no_exception(app)
    assert len(app.selectbox[0].options) == 12
    assert any(button.label == "Odjavi se" for button in app.button)


def test_login_still_establishes_existing_session_and_no_access_help(monkeypatch):
    returned = _secret()
    monkeypatch.setattr(api_client, "login", lambda *args: {"access_token": returned})
    monkeypatch.setattr(api_client, "app_context", lambda token: {"organizations": []})
    monkeypatch.setattr(security_api, "list_sessions", lambda token: [])
    app = _app().run()
    _input(app, "Email", "reader@example.test")
    _input(app, "Lozinka", _secret())
    _button(app, "Prijavi se").click().run()
    _no_exception(app)
    assert bool(app.session_state[TOKEN_KEY] == returned)
    assert any("Pristup nije dodeljen" in item.value for item in app.markdown)
    _button(app, "ISI Help · Pomoć").click().run()
    _no_exception(app)
    assert len(app.selectbox[0].options) == 12
