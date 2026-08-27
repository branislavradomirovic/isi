from __future__ import annotations

from typing import Any

import streamlit as st

from src.streamlit_app import data_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired


def _scope(shell: dict[str, Any]) -> tuple[str, str, str] | None:
    workspace = shell.get("workspace")
    if workspace is None:
        st.info("Izaberite ili konfigurišite workspace pre rada sa podacima.")
        return None
    return str(shell["organization"]["id"]), str(shell["product"]["code"]), str(workspace["id"])


def _status_badge(status: str) -> str:
    labels = {
        "succeeded": "obrađeno",
        "failed": "greška",
        "queued": "na čekanju",
        "running": "obrada",
        "uploaded": "učitano",
    }
    return labels.get(status, status)


def _render_catalog(sources: list[dict[str, Any]]) -> None:
    st.markdown("### Izvori u aktivnom workspace-u")
    if not sources:
        st.caption("Još nema učitanih izvora. Katalog prikazuje samo stvarno registrovane izvore.")
        return
    rows: list[dict[str, Any]] = []
    for source in sources:
        latest = source.get("latest_version") or {}
        rows.append(
            {
                "Naziv": source["name"],
                "Tip": source["source_kind"],
                "Verzija": latest.get("version_no", "—"),
                "Format": latest.get("detected_format") or latest.get("extension") or "—",
                "Status": _status_badge(latest.get("ingest_status", "—")),
                "Redovi": latest.get("row_count") if latest.get("row_count") is not None else "—",
                "Kolone": latest.get("column_count") if latest.get("column_count") is not None else "—",
                "Veličina": latest.get("size_bytes", "—"),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_upload(token: str, shell: dict[str, Any], scope: tuple[str, str, str]) -> None:
    organization_id, product_code, workspace_id = scope
    permissions = set(shell["product"].get("permission_codes", []))
    if "data.upload" not in permissions:
        st.caption("Vaša rola ima read-only pristup podacima.")
        return

    st.markdown("### Novi izvor podataka")
    with st.form("isi06_data_upload", clear_on_submit=True):
        name = st.text_input("Naziv izvora", placeholder="npr. Lokalni indikatori 2026")
        uploaded = st.file_uploader(
            "Datoteka",
            type=["csv", "json", "xlsx", "pdf", "docx", "txt"],
            help="Podržani formati u ISI-06: CSV, JSON, XLSX, PDF, DOCX i TXT.",
        )
        submitted = st.form_submit_button("Učitaj i proveri", use_container_width=True)
    if not submitted:
        return
    if not name.strip() or uploaded is None:
        st.error("Unesite naziv izvora i izaberite datoteku.")
        return
    try:
        response = data_api.create_data_source(
            token,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
            source_name=name.strip(),
            filename=uploaded.name,
            content_type=uploaded.type or "application/octet-stream",
            payload=uploaded.getvalue(),
        )
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
        return
    except AccessDenied as exc:
        st.error(str(exc))
        return
    except ApiUnavailable as exc:
        st.error(str(exc))
        return
    version = response.get("version", {})
    job = response.get("job", {})
    st.success(
        f"Izvor je registrovan. Verzija {version.get('version_no', '—')} · "
        f"status: {_status_badge(job.get('status', version.get('ingest_status', '—')))}."
    )
    if response.get("storage_reused"):
        st.caption("Isti sadržaj je već postojao u ovom workspace-u; skladišni blob je bezbedno ponovo iskorišćen.")
    st.rerun()


def render_data_workspace(*, token: str, shell: dict[str, Any]) -> None:
    product = shell["product"]
    organization = shell["organization"]
    workspace = shell.get("workspace")
    st.markdown(f'<div class="isi-eyebrow">{product["code"]} · Podaci</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Shared Data Platform</h1>', unsafe_allow_html=True)
    st.caption("Izvori, verzije, integritet, ingestion status i osnovni quality checks u jednom tenant-safe sloju.")

    scope = _scope(shell)
    if scope is None:
        return
    organization_id, product_code, workspace_id = scope
    st.info(f"Organizacija: {organization['name']} · Platforma: {product_code} · Workspace: {workspace['name']}")

    try:
        sources = data_api.list_data_sources(
            token,
            organization_id=organization_id,
            product_code=product_code,
            workspace_id=workspace_id,
        )
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
        return
    except AccessDenied as exc:
        st.error(str(exc))
        return
    except ApiUnavailable as exc:
        st.error(str(exc))
        return

    metric_cols = st.columns(3)
    metric_cols[0].metric("Izvori", len(sources))
    succeeded = sum(1 for item in sources if (item.get("latest_version") or {}).get("ingest_status") == "succeeded")
    metric_cols[1].metric("Obrađeno", succeeded)
    metric_cols[2].metric("Aktivni workspace", product_code)
    _render_catalog(sources)
    _render_upload(token, shell, scope)
