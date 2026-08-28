from __future__ import annotations

import streamlit as st

from src.streamlit_app import reporting_api
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired


REPORT_TYPES = {
    "SIMPA": {"analytics_run": ("monitoring_summary", "Monitoring summary")},
    "ORDO": {
        "analytics_run": ("destination_snapshot", "Destination snapshot"),
        "scenario_assessment": ("scenario_review", "Scenario review"),
    },
}


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except AccessDenied as exc:
        st.error(str(exc))
    except ApiUnavailable as exc:
        st.error(str(exc))
    return None


def _section(section: dict) -> None:
    st.markdown(f"#### {section.get('title', section.get('key', 'Sekcija'))}")
    if section.get("text"):
        st.write(section["text"])
    metrics = section.get("metrics") or {}
    if metrics:
        cols = st.columns(min(4, max(1, len(metrics))))
        for index, (key, value) in enumerate(metrics.items()):
            cols[index % len(cols)].metric(key.replace("_", " "), value)
    rows = section.get("rows") or []
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    bullets = section.get("bullets") or []
    for item in bullets:
        st.write(f"- {item}")


def render_reporting(*, token: str, shell: dict) -> None:
    product = shell["product"]
    product_code = product["code"]
    organization_id = str(shell["organization"]["id"])
    workspace = shell.get("workspace")
    permissions = set(product.get("permission_codes", []))

    st.markdown(f'<div class="isi-eyebrow">{product_code} · Reporting</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">Izveštaji</h1>', unsafe_allow_html=True)
    st.caption("Verzionisani, provenance-aware reporting engine sa eksplicitnim review/publish lifecycle-om. SIMPA i ORDO dele engine, ali ne dele domain sadržaj.")

    if workspace is None:
        st.info("Izaberite workspace pre rada sa izveštajima.")
        return
    workspace_id = str(workspace["id"])

    sources = _safe(reporting_api.sources, token, organization_id, workspace_id, product_code) or []
    reports = _safe(reporting_api.reports, token, organization_id, workspace_id, product_code) or []

    create_col, state_col, export_col = st.columns(3)
    create_col.metric("Izveštaji", len(reports))
    state_col.metric("Dostupni snapshot izvori", len(sources))
    export_col.metric("Platforma", product_code)

    if "analysis.run" in permissions:
        st.markdown("### Nova verzionisana publikacija")
        if not sources:
            st.info("Nema odgovarajućeg analytics/scenario snapshot-a. Reporting namerno ne generiše izveštaj bez provenance izvora.")
        else:
            source_map = {item["id"]: item for item in sources}
            source_id = st.selectbox("Izvor", list(source_map), format_func=lambda value: source_map[value]["label"], key=f"report_source_{product_code}")
            source = source_map[source_id]
            report_type, report_label = REPORT_TYPES[product_code][source["kind"]]
            st.caption(f"Tip: {report_label} · source kind: {source['kind']}")
            title = st.text_input("Naslov izveštaja", value=f"{product_code} · {report_label}", key=f"report_title_{product_code}")
            if st.button("Kreiraj draft izveštaj", use_container_width=True, key=f"report_create_{product_code}"):
                result = _safe(
                    reporting_api.generate,
                    token,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    product_code=product_code,
                    title=title,
                    report_type=report_type,
                    source_kind=source["kind"],
                    source_id=source_id,
                )
                if result is not None:
                    st.success("Draft verzija izveštaja je kreirana iz realnog provenance snapshot-a.")
                    st.rerun()

    st.markdown("### Registry izveštaja")
    if not reports:
        st.info("Još nema izveštaja u aktivnom workspace-u.")
        return

    for summary in reports:
        with st.expander(f"{summary['title']} · {summary['report_type']} · {summary['id'][:8]}"):
            detail = _safe(reporting_api.report, token, summary["id"], organization_id, workspace_id, product_code)
            if not detail:
                continue
            versions = detail.get("versions", [])
            st.caption(f"product={detail['product_code']} · workspace={detail['workspace_id']} · status={detail['status']}")

            if sources and "analysis.run" in permissions:
                latest_source = sources[0]
                expected_type, _ = REPORT_TYPES[product_code][latest_source["kind"]]
                if expected_type == detail["report_type"] and st.button("Nova verzija iz najnovijeg snapshot-a", key=f"new_version_{summary['id']}"):
                    result = _safe(
                        reporting_api.new_version,
                        token,
                        report_id=summary["id"],
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        product_code=product_code,
                        source_kind=latest_source["kind"],
                        source_id=latest_source["id"],
                    )
                    if result is not None:
                        st.success("Kreirana je nova immutable draft verzija.")
                        st.rerun()

            for version in versions:
                st.markdown(f"### Verzija {version['version_no']} · `{version['status']}`")
                st.caption(f"content SHA-256: {version['content_sha256']} · provenance SHA-256: {version['source_manifest_sha256']}")
                for section in (version.get("content") or {}).get("sections", []):
                    _section(section)

                st.markdown("**Provenance**")
                provenance = [
                    {
                        "kind": item.get("kind"),
                        "id": item.get("id"),
                        "product": item.get("product_code"),
                        "checksum": item.get("checksum"),
                    }
                    for item in version.get("source_manifest", [])
                ]
                if provenance:
                    st.dataframe(provenance, use_container_width=True, hide_index=True)

                if version["status"] == "draft" and "analysis.run" in permissions:
                    if st.button("Pošalji na review", key=f"submit_{version['id']}"):
                        if _safe(reporting_api.submit, token, version_id=version["id"], organization_id=organization_id, workspace_id=workspace_id, product_code=product_code) is not None:
                            st.rerun()

                if version["status"] == "in_review" and "organization.manage" in permissions:
                    note = st.text_area("Review napomena", key=f"review_note_{version['id']}")
                    approve, reject = st.columns(2)
                    if approve.button("Odobri verziju", key=f"approve_{version['id']}", use_container_width=True):
                        if _safe(reporting_api.review, token, version_id=version["id"], organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, decision="approved", note=note) is not None:
                            st.rerun()
                    if reject.button("Odbij verziju", key=f"reject_{version['id']}", use_container_width=True):
                        if _safe(reporting_api.review, token, version_id=version["id"], organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, decision="rejected", note=note) is not None:
                            st.rerun()

                if version["status"] == "approved" and "organization.manage" in permissions:
                    st.warning("Odobrena verzija još nije publikovana. Publication je eksplicitna operacija.")
                    if st.button("Publikuj verziju", key=f"publish_{version['id']}"):
                        if _safe(reporting_api.publish, token, version_id=version["id"], organization_id=organization_id, workspace_id=workspace_id, product_code=product_code) is not None:
                            st.rerun()

                if version["status"] in {"approved", "published", "superseded"}:
                    fmt = st.selectbox("Format artefakta", ["html", "markdown", "json"], key=f"export_format_{version['id']}")
                    if st.button("Pripremi download artefakt", key=f"export_{version['id']}"):
                        artifact = _safe(reporting_api.export, token, version_id=version["id"], organization_id=organization_id, workspace_id=workspace_id, product_code=product_code, format=fmt)
                        if artifact is not None:
                            st.session_state[f"report_export_{version['id']}"] = artifact
                    artifact = st.session_state.get(f"report_export_{version['id']}")
                    if artifact:
                        st.download_button(
                            "Preuzmi artefakt",
                            data=artifact["content_text"],
                            file_name=artifact["filename"],
                            mime=artifact["mime_type"],
                            use_container_width=True,
                            key=f"download_{version['id']}_{artifact['sha256']}",
                        )
                        st.caption(f"Export SHA-256: {artifact['sha256']}")

                reviews = version.get("reviews", [])
                if reviews:
                    st.markdown("**Review trag**")
                    st.dataframe(reviews, use_container_width=True, hide_index=True)
