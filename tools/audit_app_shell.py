from __future__ import annotations

from pathlib import Path


REQUIRED = [
    "src/api/app_shell_routes.py",
    "src/platform/app_shell/schemas.py",
    "src/platform/app_shell/service.py",
    "src/streamlit_app/api_client.py",
    "src/streamlit_app/selection.py",
    "src/streamlit_app/style.py",
    "src/streamlit_app/assets/app-shell.css",
    "src/streamlit_app/app.py",
    "docs/architecture/ADR-0013-authenticated-app-shell.md",
    "docs/qa/ISI-05-BROWSER-QA-MATRIX.md",
]


def main() -> None:
    for value in REQUIRED:
        path = Path(value)
        if not path.exists():
            raise SystemExit(f"missing required ISI-05 file: {value}")

    app = Path("src/streamlit_app/app.py").read_text()
    for token in (
        "isi-logo-transparent.svg",
        "simpa-mark.svg",
        "ordo-mark.svg",
        "/api/v1/app-shell",
        "product entitlement",
        "_render_no_access",
        "_logout",
    ):
        if token not in app and token not in Path("src/streamlit_app/api_client.py").read_text():
            raise SystemExit(f"missing authenticated shell marker: {token}")

    service = Path("src/platform/app_shell/service.py").read_text()
    if "resolve_selection" not in service:
        raise SystemExit("app shell must revalidate via resolve_selection")
    if "ADMIN_PERMISSION_CODES" not in service:
        raise SystemExit("permission-driven admin navigation contract missing")

    print("ISI-05 authenticated app-shell static audit PASS")


if __name__ == "__main__":
    main()
