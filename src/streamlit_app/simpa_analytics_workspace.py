from __future__ import annotations

from typing import Any

import streamlit as st

from src.streamlit_app import data_api, simpa_analytics_api


def _scope(shell: dict[str, Any]) -> tuple[str, str] | None:
    workspace = shell.get("workspace")
    if not workspace or shell.get("product", {}).get("code") != "SIMPA":
        return None
    return str(shell["organization"]["id"]), str(workspace["id"])


def _safe(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except Exception as exc:
        st.error(str(exc))
        return None


def _pct(value: float | int | None) -> str:
    return f"{float(value or 0) * 100:.0f}%"


def _eligible_artifacts(token: str, organization_id: str, workspace_id: str) -> list[dict]:
    items: list[dict] = []
    eligible_snapshot_ids: set[str] = set()
    datasets = _safe(data_api.list_analytical_datasets, token, organization_id=organization_id,
                     product_code="SIMPA", workspace_id=workspace_id) or []
    for dataset in datasets:
        snapshots = _safe(data_api.list_analytical_snapshots, token, dataset_id=dataset["id"],
                          organization_id=organization_id, product_code="SIMPA",
                          workspace_id=workspace_id) or []
        eligible = [row for row in snapshots if row.get("state") in {"VALIDATED", "FROZEN"}
                    and not row.get("invalidated")]
        eligible_snapshot_ids.update(row["id"] for row in eligible)
        items.extend({"type": "snapshot", "id": row["id"], "fingerprint": row["fingerprint"]}
                     for row in eligible)
    features = _safe(data_api.list_analytical_features, token, organization_id=organization_id,
                     product_code="SIMPA", workspace_id=workspace_id) or []
    for feature in features:
        versions = _safe(data_api.list_analytical_feature_versions, token, feature_id=feature["id"],
                         organization_id=organization_id, product_code="SIMPA",
                         workspace_id=workspace_id) or []
        items.extend({"type": "feature_version", "id": row["id"], "fingerprint": row["fingerprint"]}
                     for row in versions if row.get("state") in {"GOVERNED", "FROZEN"}
                     and not row.get("invalidated") and len(row.get("snapshot_inputs") or []) == 1
                     and row["snapshot_inputs"][0].get("snapshot_id") in eligible_snapshot_ids)
    return items


def render_simpa_analytics(*, token: str, shell: dict[str, Any]) -> None:
    scope = _scope(shell)
    st.markdown('<div class="isi-eyebrow">SIMPA · Analitika + AI</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Monitoring zasnovan na dokazima</h1>', unsafe_allow_html=True)
    st.caption("ISI-09 meri kvalitet i pokrivenost dokaza, primenjuje samo eksplicitno validirane metodologije i koristi AI isključivo kao lokalni decision-support uz human review.")
    if scope is None:
        st.info("SIMPA workspace nije izabran.")
        return
    organization_id, workspace_id = scope
    permissions = set(shell.get("product", {}).get("permission_codes", []))
    runs = _safe(simpa_analytics_api.runs, token, organization_id, workspace_id) or []

    artifacts = _eligible_artifacts(token, organization_id, workspace_id)
    selected_artifact = None
    snapshot = None
    if not artifacts:
        st.info("Nema validiranog governed analytical snapshot-a ili eligible feature verzije za analitiku.")
    else:
        selected_artifact = st.selectbox(
            "Governed analytical artefakt",
            artifacts,
            format_func=lambda row: f"{row['type']} · {row['id']} · {row['fingerprint']}",
        )
        snapshot = _safe(
            simpa_analytics_api.summary, token, organization_id, workspace_id,
            analytical_artifact_type=selected_artifact["type"],
            analytical_artifact_id=selected_artifact["id"],
        )
    if snapshot:
        cols = st.columns(4)
        cards = [
            ("Opservacije", snapshot.get("observation_count", 0)),
            ("Validirane", _pct(snapshot.get("validated_observation_ratio"))),
            ("Provenance", _pct(snapshot.get("provenance_coverage"))),
            ("Pokrivenost indikatora", _pct(snapshot.get("indicator_coverage"))),
        ]
        for col, (label, value) in zip(cols, cards):
            col.metric(label, value)
        st.progress(float(snapshot.get("evidence_quality_score", 0.0)), text=f"Kvalitet dokaza: {snapshot.get('evidence_quality_band', 'no_evidence')} · {_pct(snapshot.get('evidence_quality_score'))}")
        st.caption(snapshot.get("semantic_notice", "Ovo nije skor socijalnog rizika."))

    st.markdown("### Metodološki status")
    if snapshot:
        m1, m2, m3 = st.columns(3)
        m1.metric("Aktivni indikatori", snapshot.get("active_indicator_count", 0))
        m2.metric("Konceptualni", snapshot.get("conceptual_indicator_count", 0))
        m3.metric("Sa validiranom metodologijom", snapshot.get("validated_methodology_indicator_count", 0))
    methods = _safe(simpa_analytics_api.methodologies, token, organization_id, workspace_id) or []
    if methods:
        st.dataframe(methods, use_container_width=True, hide_index=True)
    else:
        st.info("Nema validiranih ili draft metodologija u analytics registru. ISI-09 ne izmišlja formule niti automatski validira konceptualne indikatore.")

    st.markdown("### Monitoring snapshot-i")
    if snapshot and selected_artifact is not None and "analysis.run" in permissions:
        if st.button("Sačuvaj trenutni monitoring snapshot", type="primary", use_container_width=True):
            result = _safe(simpa_analytics_api.create_run, token, organization_id=organization_id, workspace_id=workspace_id, analytical_artifact_type=selected_artifact["type"], analytical_artifact_id=selected_artifact["id"])
            if result is not None:
                st.success("Monitoring snapshot je sačuvan.")
                st.rerun()
    if runs:
        compact = [{"id": item["id"], "artefakt": item.get("analytical_artifact_type"), "artifact_id": item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"), "fingerprint": item.get("analytical_artifact_fingerprint"), "kvalitet_dokaza": item["evidence_quality_score"], "validirane_opservacije": item["validated_observation_ratio"], "provenance": item["provenance_coverage"], "pokrivenost_indikatora": item["indicator_coverage"], "kreirano": item["created_at"]} for item in runs]
        st.dataframe(compact, use_container_width=True, hide_index=True)
    else:
        st.info("Još nema sačuvanih analitičkih snapshot-a.")

    st.markdown("### Lokalna AI podržana sinteza")
    st.warning("AI izlaz nije institucionalni zaključak. Za osetljive SIMPA podatke provider je prinudno local-only, a rezultat zahteva human review.")
    st.caption("Trenutni lokalni QA model: qwen2.5:7b-instruct preko shared ISI Ollama gateway-a. Produkcioni SIMPA model biće zaključan kasnije.")
    eligible_artifacts = {
        (("ANALYTICAL_SNAPSHOT" if item["type"] == "snapshot" else "ANALYTICAL_FEATURE_VERSION"), item["id"])
        for item in artifacts
    }
    governed_runs = [
        item for item in runs
        if (
            item.get("analytical_artifact_type"),
            item.get("analytical_snapshot_id") or item.get("analytical_feature_version_id"),
        ) in eligible_artifacts
    ]
    if governed_runs and "analysis.run" in permissions:
        run_ids = [item["id"] for item in governed_runs]
        selected_run = st.selectbox("Monitoring snapshot za sintezu", run_ids, format_func=lambda value: f"Snapshot {value[:8]}")
        if st.button("Pokreni lokalnu SIMPA AI sintezu", use_container_width=True):
            result = _safe(simpa_analytics_api.create_synthesis, token, organization_id=organization_id, workspace_id=workspace_id, analytics_run_id=selected_run, sensitivity="sensitive")
            if result is not None:
                st.success("AI sinteza je izvršena kroz shared gateway. Rezultat ostaje na human review-u.")
                st.rerun()

    syntheses = _safe(simpa_analytics_api.syntheses, token, organization_id, workspace_id) or []
    if not syntheses:
        st.info("Nema AI sinteza u aktivnom workspace-u.")
        return
    for item in syntheses:
        job = item.get("job", {})
        with st.expander(f"Sinteza {item['id'][:8]} · {job.get('status', 'unknown')} · review: {item.get('review_status')}"):
            st.caption(f"provider={job.get('provider_name') or '-'} · model={job.get('model_name') or '-'} · policy={job.get('effective_provider_policy')} · prompt={job.get('prompt_key')} v{job.get('prompt_version')}")
            structured = job.get("structured_output")
            if structured:
                st.markdown("**Sažetak**")
                st.write(structured.get("executive_summary", ""))
                st.markdown("**Kvalitet dokaza**")
                st.write(structured.get("evidence_quality", ""))
                points = structured.get("attention_points") or []
                if points:
                    st.markdown("**Tačke za stručnu pažnju**")
                    for point in points:
                        st.write(f"- {point}")
                limitations = structured.get("limitations") or []
                if limitations:
                    st.markdown("**Ograničenja**")
                    for limitation in limitations:
                        st.write(f"- {limitation}")
            elif job.get("error_message"):
                st.error(job.get("error_message"))
            else:
                st.caption("AI rezultat još nije dostupan.")
            if item.get("review_status") == "pending" and job.get("status") in {"review_required", "succeeded"} and "analysis.run" in permissions:
                note = st.text_area("Napomena review-a", key=f"simpa_review_note_{item['id']}")
                left, right = st.columns(2)
                if left.button("Prihvati kao pregledano", key=f"simpa_accept_{item['id']}", use_container_width=True):
                    result = _safe(simpa_analytics_api.review_synthesis, token, synthesis_id=item["id"], organization_id=organization_id, workspace_id=workspace_id, decision="accepted", reviewer_note=note)
                    if result is not None:
                        st.rerun()
                if right.button("Odbaci", key=f"simpa_reject_{item['id']}", use_container_width=True):
                    result = _safe(simpa_analytics_api.review_synthesis, token, synthesis_id=item["id"], organization_id=organization_id, workspace_id=workspace_id, decision="rejected", reviewer_note=note)
                    if result is not None:
                        st.rerun()
def render_ordo_analytics_placeholder() -> None:
    st.markdown('<div class="isi-eyebrow">ORDO · Analitika</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">ORDO analytics foundation</h1>', unsafe_allow_html=True)
    st.info("ORDO domain analytics dolazi u ISI-11. SIMPA analytics modeli, metodologije i AI sinteze se ne koriste kao ORDO analitika.")
