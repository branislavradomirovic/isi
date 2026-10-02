from __future__ import annotations

from typing import Any

import streamlit as st

from src.streamlit_app.shared_help_workspace import render_topic_summary

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


def _registry_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "Code": item.get("code", "—"),
        "Name": item.get("name", "—"),
        "Methodology reference": item.get("methodology_reference", "—"),
        "Methodology version": item.get("methodology_version", "—"),
        "Registry revision": item.get("revision", "—"),
    } for item in items]


def _version_rows(items: list[dict[str, Any]], *, identity_key: str) -> list[dict[str, Any]]:
    return [{
        "Artifact ID": item.get("id", "—"),
        "Registry ID": item.get(identity_key, "—"),
        "Version": item.get("version_no", "—"),
        "State": item.get("state", "—"),
        "Classification": item.get("classification", "—"),
        "Privacy": item.get("privacy_category", "—"),
        "AI policy": item.get("ai_use_policy", "—"),
        "Methodology reference": item.get("methodology_reference", "—"),
        "Methodology version": item.get("methodology_version", "—"),
        "Invalidated": item.get("invalidated", False),
        "Invalidation reason": item.get("invalidation_reason") or "—",
        "Fingerprint / provenance": item.get("fingerprint", "—"),
    } for item in items]


def _artifact_label(item: dict[str, Any]) -> str:
    return f"v{item.get('version_no', '—')} · {item.get('state', '—')} · {item.get('id', '—')}"


def _render_lineage(lineage: dict[str, Any]) -> None:
    snapshot = lineage.get("snapshot") or {}
    lineage_mode = snapshot.get("lineage_mode", "LEGACY_SOURCE_VERSION")
    st.caption(
        f"Snapshot v{snapshot.get('version_no', '—')} · lineage: {lineage_mode} · provenance fingerprint: "
        f"{snapshot.get('fingerprint', '—')}"
    )
    if lineage_mode == "LEGACY_SOURCE_VERSION":
        st.warning(
            "Historical legacy source-version lineage. This snapshot is readable history, "
            "but is not a governed-output reproducible artifact."
        )
    else:
        st.markdown("**Pinned analytical dataset contract**")
        st.dataframe([{
            "Contract version ID": snapshot.get("dataset_contract_version_id", "—"),
            "Contract fingerprint": snapshot.get("dataset_contract_fingerprint", "—"),
            "Temporal mode": snapshot.get("temporal_mode", "—"),
            "Temporal keys": ", ".join(snapshot.get("temporal_key_fields", [])) or "—",
            "Granularity / entity keys": ", ".join(snapshot.get("granularity_key_fields", [])) or "—",
            "Missing-value policy": snapshot.get("missing_value_policy", "—"),
            "Quality state": snapshot.get("analytical_quality_state", "—"),
            "Persisted record count": snapshot.get("record_count", 0),
        }], use_container_width=True, hide_index=True)
        output_rows = [{
            "Governed output ID": edge.get("governed_output_id", "—"),
            "Output fingerprint": edge.get("governed_output_fingerprint", "—"),
            "Source version ID": edge.get("source_version_id", "—"),
            "Ingestion run ID": edge.get("ingestion_run_id", "—"),
            "Evaluation ID": edge.get("evaluation_id", "—"),
            "Decision": edge.get("evaluation_decision", "—"),
        } for edge in snapshot.get("governed_outputs", [])]
        st.markdown("**Governed-output lineage**")
        st.dataframe(output_rows, use_container_width=True, hide_index=True)
    source_rows = [{
        "Source ID": edge.get("source_id", "—"),
        "Source version ID": edge.get("source_version_id", "—"),
        "Source version": edge.get("source_version_no", "—"),
        "Classification": edge.get("classification", "—"),
        "Privacy": edge.get("privacy_category", "—"),
        "AI policy": edge.get("ai_use_policy", "—"),
        "Source fingerprint": edge.get("source_fingerprint", "—"),
    } for edge in snapshot.get("source_versions", [])]
    if lineage_mode == "LEGACY_SOURCE_VERSION":
        st.markdown("**Historical source-version lineage**")
        st.dataframe(source_rows, use_container_width=True, hide_index=True)
    st.markdown("**Dependent feature versions**")
    st.dataframe(
        _version_rows(lineage.get("dependent_feature_versions", []), identity_key="feature_id"),
        use_container_width=True,
        hide_index=True,
    )


def _render_eligibility_result(result: dict[str, Any]) -> None:
    st.dataframe([{
        "Allowed": result.get("allowed", False),
        "Reason code": result.get("reason_code", "—"),
        "Separate approval": result.get("requires_separate_approval", False),
        "Human review required": result.get("human_review_required", True),
        "Artifact version": result.get("artifact_version", "—"),
        "Lifecycle state": result.get("lifecycle_state", "—"),
        "Classification": result.get("classification", "—"),
        "Privacy": result.get("privacy_category", "—"),
        "AI policy": result.get("ai_use_policy", "—"),
        "Provenance fingerprint": result.get("provenance_fingerprint", "—"),
    }], use_container_width=True, hide_index=True)


def _render_analytical_governance(token: str, shell: dict[str, Any], scope: tuple[str, str, str]) -> None:
    organization_id, product_code, workspace_id = scope
    params = {"organization_id": organization_id, "product_code": product_code, "workspace_id": workspace_id}
    try:
        datasets = data_api.list_analytical_datasets(token, **params)
        features = data_api.list_analytical_features(token, **params)
        snapshots = [
            snapshot
            for dataset in datasets
            for snapshot in data_api.list_analytical_snapshots(
                token, dataset_id=str(dataset["id"]), **params,
            )
        ]
        feature_versions = [
            version
            for feature in features
            for version in data_api.list_analytical_feature_versions(
                token, feature_id=str(feature["id"]), **params,
            )
        ]
    except (AuthenticationRequired, AccessDenied, ApiUnavailable) as exc:
        st.error(str(exc))
        return

    st.markdown("### Analytical datasets")
    st.dataframe(_registry_rows(datasets), use_container_width=True, hide_index=True)
    st.dataframe(_version_rows(snapshots, identity_key="dataset_id"), use_container_width=True, hide_index=True)
    st.markdown("### Feature registry")
    st.dataframe(_registry_rows(features), use_container_width=True, hide_index=True)
    st.dataframe(
        _version_rows(feature_versions, identity_key="feature_id"),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Lineage / provenance")
    if snapshots:
        selected_snapshot = st.selectbox(
            "Snapshot for lineage",
            snapshots,
            format_func=_artifact_label,
            key="analytical_lineage_snapshot",
        )
        try:
            lineage = data_api.get_analytical_lineage(
                token, snapshot_id=str(selected_snapshot["id"]), **params,
            )
            _render_lineage(lineage)
        except (AuthenticationRequired, AccessDenied, ApiUnavailable) as exc:
            st.error(str(exc))
    else:
        st.caption("No versioned snapshot is available in the active governed scope.")

    st.markdown("### AI / RAG eligibility")
    artifacts = [
        {**item, "artifact_type": "snapshot"} for item in snapshots
    ] + [
        {**item, "artifact_type": "feature_version"} for item in feature_versions
    ]
    if artifacts:
        selected_artifact = st.selectbox(
            "Governed artifact",
            artifacts,
            format_func=lambda item: f"{item['artifact_type']} · {_artifact_label(item)}",
            key="analytical_eligibility_artifact",
        )
        action = st.selectbox(
            "Governed AI action",
            ("LOCAL_ANALYSIS", "RAG_RETRIEVAL", "MODEL_EVALUATION", "MODEL_TRAINING"),
            key="analytical_eligibility_action",
        )
        if st.button("Evaluate deterministic eligibility", key="analytical_eligibility_evaluate"):
            try:
                result = data_api.evaluate_ai_eligibility(token, **params,
                    artifact_type=selected_artifact["artifact_type"],
                    artifact_id=str(selected_artifact["id"]), action=action,
                    namespace=f"ORG-{organization_id}/{product_code}")
                _render_eligibility_result(result)
            except (AuthenticationRequired, AccessDenied, ApiUnavailable) as exc:
                st.error(str(exc))
    else:
        st.caption("No versioned governed artifact is available for deterministic eligibility evaluation.")

    st.markdown("### Human review")
    st.info(
        "Eligibility never executes a model. Analytical and AI outputs remain evidence-bounded, attributable, "
        "auditable, and subject to the human-review decision shown above."
    )

    if "data.governance.manage" in set(shell["product"].get("permission_codes", [])):
        with st.expander("Registry governance controls"):
            st.caption("Mutations are submitted to API endpoints that enforce data.governance.manage server-side.")


def render_data_workspace(*, token: str, shell: dict[str, Any]) -> None:
    render_topic_summary("ISI-H07")
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
    _render_analytical_governance(token, shell, scope)
