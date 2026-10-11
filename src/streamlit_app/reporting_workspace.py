from __future__ import annotations
import hashlib
import json
from pathlib import Path
import streamlit as st
from pydantic import ValidationError
from src.platform.reporting.schemas import EvidenceLink
from src.streamlit_app.shared_help_workspace import render_topic_summary
from src.streamlit_app import reporting_api, linked_reporting_workspace as linked
from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired

REPORT_TYPES = {
    "SIMPA": {
        "analytics_run": ("monitoring_summary", "Monitoring summary"),
        "extraction_request": ("linked_evidence", "Povezani nalaz i dokaz"),
    },
    "ORDO": {
        "extraction_request": ("linked_evidence", "Povezani nalaz i dokaz"),
        "analytics_run": ("destination_snapshot", "Destination snapshot"),
        "scenario_assessment": ("scenario_review", "Scenario review"),
    },
}


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AuthenticationRequired:
        st.error("Sesija je istekla. Prijavite se ponovo.")
    except (ValidationError, ValueError):
        st.error("Proverite obavezna polja, tačne identitete i eksplicitne potvrde. Zahtev nije poslat.")
    except (AccessDenied, ApiUnavailable):
        st.error(
            "Izveštaj ili operacija nisu dostupni. Osvežite status i proverite prava, izvor, pregled i granice pre ponavljanja."
        )
    return None


def _link_complete(value):
    if value is None:
        return True
    try:
        EvidenceLink.model_validate(value)
        return True
    except ValidationError:
        return False


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _confirm(key, values, label):
    binding = _hash(values)
    previous, revision = st.session_state.get(key + ":binding", (None, 0))
    if previous != binding:
        revision += 1
        st.session_state[key + ":binding"] = (binding, revision)
    return st.checkbox(label, key=key + f":confirmation:{revision}")


def _success(key, message):
    st.session_state[key + ":receipt"] = message
    st.session_state[key + ":generation"] = st.session_state.get(key + ":generation", 0) + 1
    st.rerun()


def _section(section):
    st.markdown(f"#### {section.get('title', section.get('key', 'Sekcija'))}")
    if section.get("text"):
        st.write(section["text"])
    metrics = section.get("metrics") or {}
    if metrics:
        cols = st.columns(min(4, len(metrics)))
        for index, (key, value) in enumerate(metrics.items()):
            cols[index % len(cols)].metric(key.replace("_", " "), value)
    if section.get("rows"):
        st.dataframe(section["rows"], width="stretch", hide_index=True)
    for item in section.get("bullets") or []:
        st.write(f"- {item}")


def render_reporting(*, token, shell):
    render_topic_summary("ISI-H08")
    product = shell["product"]["code"]
    permissions = set(shell["product"].get("permission_codes", []))
    st.title("Izveštaji")
    st.caption(
        "Izaberite tačan izvor, pregledajte nacrt, donesite odluku, pa zasebno objavite odobrenu verziju. SIMPA i ORDO dele engine, ali ne dele domain sadržaj."
    )
    with st.expander("Uputstvo za verzionisane izveštaje"):
        st.markdown(
            Path(__file__).resolve().parents[2].joinpath("docs/help/ISI-REPORTING-WORKFLOWS-GUIDE.md").read_text()
        )
    if shell.get("workspace") is None:
        st.info("Izaberite workspace pre rada sa izveštajima.")
        return
    scope = dict(
        organization_id=str(shell["organization"]["id"]),
        workspace_id=str(shell["workspace"]["id"]),
        product_code=product,
    )
    key = "report:" + _hash([scope, sorted(permissions)])
    if st.session_state.get("report:active") != key:
        st.session_state["report:active"] = key
        st.session_state[key + ":generation"] = st.session_state.get(key + ":generation", 0) + 1
    if st.session_state.get(key + ":receipt"):
        st.success(st.session_state[key + ":receipt"])
    generation = st.session_state.get(key + ":generation", 0)
    prefix = key + f":{generation}:"
    sources = _safe(reporting_api.sources, token, scope["organization_id"], scope["workspace_id"], product)
    reports = _safe(reporting_api.reports, token, scope["organization_id"], scope["workspace_id"], product)
    if sources is None or reports is None:
        st.info("Pregled nije učitan. Ovo nije potvrda da je registar prazan.")
        return
    cols = st.columns(3)
    cols[0].metric("Izveštaji", len(reports))
    cols[1].metric("Dostupni snapshot izvori", len(sources))
    cols[2].metric("Platforma", product)
    if "analysis.run" in permissions:
        st.subheader("Nova verzionisana publikacija")
        if not sources:
            st.info(
                "Nema odgovarajućeg analytics/scenario snapshot-a. Reporting namerno ne generiše izveštaj bez provenance izvora."
            )
        else:
            by_id = {row["id"]: row for row in sources if row["kind"] in REPORT_TYPES[product]}
            source_id = st.selectbox(
                "Izvor", list(by_id), index=None, format_func=lambda v: by_id[v]["label"], key=prefix + "source"
            )
            if source_id is not None:
                source = by_id[source_id]
                report_type, label = REPORT_TYPES[product][source["kind"]]
                st.caption(f"Tip: {label} · izvor: {source_id} · {source['kind']}")
                title = st.text_input("Naslov izveštaja", max_chars=500, key=prefix + "title")
                evidence_link = None
                link_key = prefix + source_id + ":link:"
                if source["kind"] == "extraction_request":
                    evidence_link = linked.inputs(link_key)
                    if st.button(
                        "Pregledaj povezani dokaz", key=link_key + "preview", disabled=not _link_complete(evidence_link)
                    ):
                        preview = _safe(
                            reporting_api.linked_preview,
                            token,
                            **scope,
                            request_id=source_id,
                            evidence_link=evidence_link,
                        )
                        if preview:
                            linked.preview(preview["content"], link_key)
                confirmed = _confirm(
                    prefix + "create",
                    [scope, source, title, evidence_link],
                    "Potvrđujem tačan izvor, naslov i kreiranje ovog nacrta",
                )
                if st.button(
                    "Kreiraj draft izveštaj",
                    width="stretch",
                    key=prefix + "create",
                    disabled=not (confirmed and len(title.strip()) >= 3 and _link_complete(evidence_link)),
                ):
                    result = _safe(
                        reporting_api.generate,
                        token,
                        **scope,
                        title=title.strip(),
                        report_type=report_type,
                        source_kind=source["kind"],
                        source_id=source_id,
                        evidence_link=evidence_link,
                    )
                    if result is not None:
                        _success(
                            key,
                            "Nacrt izveštaja je kreiran. Pregledajte novu verziju; nacrt nije odobren niti objavljen.",
                        )
    st.subheader("Registry izveštaja")
    if not reports:
        st.info("Još nema izveštaja u aktivnom workspace-u.")
        return
    for summary in reports:
        with st.expander(f"{summary['title']} · {summary['report_type']} · {summary['id'][:8]}"):
            detail = _safe(
                reporting_api.report, token, summary["id"], scope["organization_id"], scope["workspace_id"], product
            )
            if detail is None:
                continue
            identity = prefix + detail["id"] + ":"
            st.caption(
                f"product={detail['product_code']} · workspace={detail['workspace_id']} · status={detail['status']}"
            )
            compatible = {
                row["id"]: row
                for row in sources
                if row["kind"] in REPORT_TYPES[product]
                and REPORT_TYPES[product][row["kind"]][0] == detail["report_type"]
            }
            if compatible and "analysis.run" in permissions:
                selected = st.selectbox(
                    "Izvor za novu verziju",
                    list(compatible),
                    index=None,
                    format_func=lambda v: compatible[v]["label"],
                    key=identity + "source",
                )
                if selected is not None:
                    source = compatible[selected]
                    link = (
                        linked.inputs(identity + selected + ":link:")
                        if source["kind"] == "extraction_request"
                        else None
                    )
                    confirmed = _confirm(
                        identity + "new",
                        [scope, detail, source, link],
                        "Potvrđujem izabrani izvor za zasebnu novu verziju",
                    )
                    if st.button(
                        "Kreiraj novu verziju iz izabranog izvora",
                        key=identity + "new",
                        disabled=not (confirmed and _link_complete(link)),
                    ):
                        result = _safe(
                            reporting_api.new_version,
                            token,
                            **scope,
                            report_id=summary["id"],
                            source_kind=source["kind"],
                            source_id=selected,
                            evidence_link=link,
                        )
                        if result is not None:
                            _success(key, "Nova zasebna verzija nacrta je kreirana; prethodni dokaz nije prepisan.")
            for version in detail.get("versions", []):
                _version(token, scope, permissions, version, identity, key)


def _version(token, scope, permissions, version, prefix, receipt_key):
    st.markdown(f"### Verzija {version['version_no']} · `{version['status']}`")
    st.caption(
        f"content SHA-256: {version['content_sha256']} · provenance SHA-256: {version['source_manifest_sha256']}"
    )
    for section in (version.get("content") or {}).get("sections", []):
        _section(section)
    identity = prefix + version["id"] + ":"
    if (version.get("content") or {}).get("schema") == "ISI-LINKED-EVIDENCE-v1":
        linked.preview(version["content"], identity)
    st.markdown("**Provenance**")
    provenance = [
        {
            "kind": row.get("kind"),
            "id": row.get("id"),
            "product": row.get("product_code"),
            "checksum": row.get("checksum"),
        }
        for row in version.get("source_manifest", [])
    ]
    if provenance:
        st.dataframe(provenance, width="stretch", hide_index=True)
    common = dict(scope, version_id=version["id"], version=version)
    status = version["status"]
    if status == "draft" and "analysis.run" in permissions:
        confirmed = _confirm(
            identity + "submit", [scope, version], "Potvrđujem slanje ove pregledane verzije na review"
        )
        if st.button("Pošalji na review", key=identity + "submit", disabled=not confirmed):
            if _safe(reporting_api.submit, token, **common) is not None:
                _success(receipt_key, "Verzija je poslata na review; odobrenje je zaseban korak.")
    if status == "in_review" and "organization.manage" in permissions:
        decision = st.selectbox(
            "Odluka o verziji",
            ["approved", "rejected"],
            index=None,
            format_func=lambda value: {"approved": "Odobri verziju", "rejected": "Odbij verziju"}[value],
            key=identity + "decision",
        )
        note = st.text_area("Review napomena", max_chars=4000, key=identity + "note")
        confirmed = _confirm(
            identity + "review",
            [scope, version, decision, note],
            "Potvrđujem pregled sadržaja, porekla i ovu odluku o verziji",
        )
        if st.button(
            "Sačuvaj odluku o verziji",
            key=identity + "review",
            disabled=not (confirmed and decision is not None and len(note.strip()) >= 3),
        ):
            if _safe(reporting_api.review, token, **common, decision=decision, note=note.strip()) is not None:
                _success(receipt_key, "Odluka o pregledanoj verziji je sačuvana; odobrenje nije objavljivanje.")
    if status == "approved" and "organization.manage" in permissions:
        st.warning(
            "Odobrena verzija još nije publikovana. Publication je eksplicitna operacija unutar platforme; nije javna objava ili email slanje."
        )
        confirmed = _confirm(
            identity + "publish", [scope, version], "Potvrđujem objavljivanje ove odobrene verzije unutar platforme"
        )
        if st.button("Publikuj verziju", key=identity + "publish", disabled=not confirmed):
            if _safe(reporting_api.publish, token, **common) is not None:
                _success(
                    receipt_key,
                    "Odobrena verzija je objavljena unutar platforme. Ponovo pregledajte status i prava izvoza.",
                )
    if status in {"approved", "published", "superseded"} and "report.read" in permissions:
        fmt = st.selectbox("Format artefakta", ["html", "markdown", "json"], key=identity + "format")
        # Revalidate each render; never cache linked quotations or downloadable content.
        if st.checkbox("Pripremi download artefakt", key=identity + "export"):
            artifact = _safe(reporting_api.export, token, version_id=version["id"], **scope, format=fmt)
            if artifact:
                st.download_button(
                    "Preuzmi artefakt",
                    data=artifact["content_text"],
                    file_name=artifact["filename"],
                    mime=artifact["mime_type"],
                    width="stretch",
                    key=identity + artifact["sha256"],
                )
                st.caption(f"Export SHA-256: {artifact['sha256']}")
    if version.get("reviews"):
        st.markdown("**Review trag**")
        st.dataframe(version["reviews"], width="stretch", hide_index=True)
