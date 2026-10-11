"""Explicit source inspection and review. Quoted source text never rendered as HTML."""

from uuid import uuid4
from datetime import date
import streamlit as st
from src.streamlit_app.evidence_view import render_evidence
from src.streamlit_app import extraction_api, spatial_api, ai_api
from src.streamlit_app.api_client import AuthenticationRequired, AccessDenied, ApiUnavailable

HELP = (
    (
        "1. Svrha",
        "Izvlači citirane entitete i atomske nalaze iz digitalnog TXT dokumenta ili ćelija governed snapshot-a. AI nije numerička ni institucionalna vlast.",
    ),
    (
        "2. Kada koristiti",
        "Za dokumentovane zbirne nalaze sa izvorom, periodom i teritorijom. Realna tačnost modela još je UNCALIBRATED.",
    ),
    (
        "3. Prava",
        "data.read za pregled; ai.run za kreiranje/otkazivanje; data.validate za ljudski pregled. Backend proverava organizaciju, proizvod i workspace.",
    ),
    (
        "4. Koraci",
        "Učitajte dozvoljen izvor, uredite governance, izaberite njegov tačan UUID, format, jezik i lokalni model. Pokrenite, osvežite listu, učitajte nalaz, proverite citate, pa prihvatite ili odbijte.",
    ),
    (
        "5. Polja i statusi",
        "queued/running/failed označavaju AI posao; EXTRACTED_UNVERIFIED čeka pregled; REVIEWED_ACCEPTED potvrđuje ekstrakciju; REJECTED isključuje nalaze; CANCELLED otkazuje pending posao. Null je nedostajuće, ne nula.",
    ),
    (
        "6. Primer",
        "Sintetičko: 'Grad A ima 12 usluga u 2025.' — 12/usluga/2025 moraju ostati tačno citirani. Isto ime u dve jedinice ostaje AMBIGUOUS.",
    ),
    (
        "7. Granice",
        "Nema OCR/PDF/DOCX, geokodera, nagađanja koordinata, uzročne analize, citizen scoring-a ni automatske VALIDATED metodologije. SHAP ne proverava istinu LLM tvrdnje.",
    ),
    (
        "8. Greške i oporavak",
        "Prevelik ili neodobren izvor, netačan citat i promenjena verzija blokiraju rezultat. Za failed posao ili ispravku kreirajte novu verziju/zahtev; ponovljen request key ne ponavlja izvršenje.",
    ),
    (
        "9. Privatnost",
        "Samo aggregate nonpersonal dozvoljeni izvori; local_only AI. Citati su privatni po proizvodu/workspace-u. Povlačenje/purge/reklasifikacija izvora blokira aktuelni pregled.",
    ),
    (
        "10. Poreklo i pregled",
        "Proverite source/version/hash, Unicode span/cell, jezik, model/prompt/policy/code, posao/pokušaj i fingerprint. Teritoriju nalaza vežite posebno uz reviewed polygon i datum; lokacija ustanove nije obuhvat tvrdnje. Prihvatanje nije potvrda istine ni metodologije.",
    ),
)


def safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (AuthenticationRequired, AccessDenied, ApiUnavailable):
        st.error("Ekstrakcija nije dostupna. Proverite sesiju, ovlašćenja i verziju izvora; osvežite pre ponavljanja.")
        return None


def render_detail(value):
    st.text("Status: " + value["state"])
    artifact = value.get("artifact")
    if not artifact:
        st.info("Nema prihvaćenog strukturiranog artefakta; osvežite nakon završetka posla.")
        return
    st.warning("Prihvatanje ekstrakcije nije potvrda istinitosti nalaza ili validacija metodologije.")
    for mention in artifact["output"]["mentions"]:
        with st.expander("Entitet " + mention["id"]):
            st.text(mention["anchor"]["quote"])
            render_evidence(
                "Dokaz, izvor i ograničenja",
                {"anchor": mention["anchor"], "kind": mention["kind"], "link": artifact["links"][mention["id"]]},
            )
    for claim in artifact["output"]["claims"]:
        with st.expander("Nalaz " + claim["id"], expanded=True):
            st.text(claim["statement"]["quote"])
            st.text("Tip: " + claim["kind"])
            st.text("Ograničenja: " + claim["limitations"])
            for field, label in [
                ("subject", "Subjekat"),
                ("predicate", "Predikat"),
                ("value", "Vrednost"),
                ("unit", "Jedinica"),
                ("period", "Period"),
            ]:
                st.text(label + ": " + (claim[field]["quote"] if claim[field] is not None else "Nije navedeno"))
            for citation in claim["citations"]:
                st.text(
                    ("Podržava: " if citation["relation"] == "supporting" else "Protivreči: ")
                    + citation["anchor"]["quote"]
                )
            with st.expander("Tačni citati i lokatori " + claim["id"]):
                render_evidence("Tačni citati i lokatori nalaza", claim)
    with st.expander("Verzije i poreklo"):
        render_evidence(
            "Dokaz, izvor i ograničenja", {k: v for k, v in artifact.items() if k not in {"output", "links"}}
        )
        st.text(value["artifact_fingerprint"])
        if value.get("review"):
            render_evidence("Ljudski pregled ekstrakcije", value["review"])


def render_extraction_workspace(*, token, shell):
    product = shell["product"]["code"]
    org = shell["organization"]["id"]
    workspace = shell.get("workspace")
    if not workspace:
        return
    ws = workspace["id"]
    permissions = set(shell["product"].get("permission_codes", []))
    prefix = f"extract:{org}:{product}:{ws}"
    st.subheader("Entiteti i geografski nalazi — izvori i ljudski pregled")
    with st.expander("Help — ekstrakcija i pregled"):
        for title, text in HELP:
            st.markdown("**" + title + "**")
            st.text(text)
    if "data.read" not in permissions:
        st.info("Nedostaje pravo data.read.")
        return
    if not st.checkbox("Učitaj ekstrakcije ovog workspace-a", key=prefix + ":load"):
        return
    params = dict(organization_id=org, workspace_id=ws)

    def call(path, **kw):
        return safe(extraction_api.call, token, product, path, **params, **kw)

    if "ai.run" in permissions:
        models = safe(ai_api.models, token, organization_id=org, product_code=product, workspace_id=ws) or []
        local = [
            m
            for m in models
            if m.get("local_provider") and m.get("purpose") == "chat" and not m.get("development_only")
        ]
        with st.form(prefix + ":create"):
            kind = st.selectbox("Ulaz", ["document", "snapshot"])
            identity = st.text_input("Tačan UUID verzije TXT dokumenta ili governed snapshot-a")
            language = st.selectbox("Jezik", ["sr-Latn", "sr-Cyrl", "en"])
            model = st.selectbox("Registrovani lokalni model", [m["model_key"] for m in local]) if local else None
            submitted = st.form_submit_button("Pokreni novu ekstrakciju", disabled=not local)
        if submitted:
            from uuid import UUID

            try:
                UUID(identity)
            except ValueError:
                st.error("Unesite validan UUID izvora.")
            else:
                value = call(
                    "requests",
                    method="POST",
                    payload=dict(
                        params,
                        input_kind=kind,
                        input_id=identity,
                        language=language,
                        model_key=model,
                        request_key=str(uuid4()),
                    ),
                )
                if value:
                    st.success("Zahtev registrovan; status: " + value["state"])
    rows = call("requests")
    if rows is None:
        return
    if rows["truncated"]:
        st.warning("Prikazano je najnovijih 100 zahteva.")
    if not rows["items"]:
        st.info("Nema ekstrakcija u ovom kontekstu.")
        return
    st.dataframe(rows["items"], hide_index=True, width="stretch")
    selected = st.selectbox(
        "Zahtev za pregled", rows["items"], format_func=lambda x: x["id"] + " · " + x["state"], key=prefix + ":selected"
    )
    if (
        "ai.run" in permissions
        and selected["state"] == "queued"
        and st.button("Otkaži pending zahtev", key=prefix + ":cancel")
    ):
        if call("requests/" + selected["id"] + "/cancel", method="POST"):
            st.rerun()
    if st.checkbox("Otvori izvore i citate izabranog zahteva", key=prefix + selected["id"] + ":detail"):
        value = call("requests/" + selected["id"])
        if value:
            render_detail(value)
            if "data.validate" in permissions and value["state"] == "EXTRACTED_UNVERIFIED":
                with st.form(prefix + selected["id"] + ":review"):
                    decision = st.selectbox("Odluka", ["REJECTED", "REVIEWED_ACCEPTED"])
                    attested = st.checkbox("Proverio/la sam sve citate, vrednosti, jedinice, periode i ograničenja.")
                    note = st.text_area("Obrazloženje pregleda", max_chars=1000)
                    entity_links = []
                    targets = safe(spatial_api.call, token, product, "targets", **params) or []
                    for mention in value["artifact"]["output"]["mentions"]:
                        target = st.selectbox(
                            "Identitet entiteta " + mention["id"],
                            [None] + targets,
                            format_func=lambda t: (
                                "UNRESOLVED" if t is None else t["kind"] + " · " + t["key"] + " · " + t["name"]
                            ),
                            key=prefix + selected["id"] + mention["id"] + ":identity",
                        )
                        proof = st.text_input("Dokaz identiteta " + mention["id"], max_chars=1000)
                        if target:
                            entity_links.append(
                                dict(
                                    mention_id=mention["id"],
                                    domain_kind=target["kind"],
                                    domain_id=target["id"],
                                    evidence_note=proof,
                                )
                            )
                    territories = []
                    geos = safe(spatial_api.call, token, product, "list", **params) or []
                    areas = [g for g in geos if g["state"] == "VALIDATED" and g["geometry_type"] != "Point"]
                    for claim in value["artifact"]["output"]["claims"]:
                        geo = st.selectbox(
                            "Obuhvat nalaza " + claim["id"],
                            [None] + areas,
                            format_func=lambda g: (
                                "UNRESOLVED" if g is None else str(g["domain_binding"]["key"]) + " · " + g["version"]
                            ),
                            key=prefix + selected["id"] + claim["id"],
                        )
                        when = st.date_input("Datum granice " + claim["id"], value=date.today())
                        why = st.text_input("Dokaz obuhvata " + claim["id"], max_chars=1000)
                        if geo:
                            territories.append(
                                dict(claim_id=claim["id"], geometry_id=geo["id"], at_date=str(when), scope_note=why)
                            )
                    save = st.form_submit_button("Sačuvaj konačan pregled")
                if save:
                    result = call(
                        "requests/" + selected["id"] + "/review",
                        method="POST",
                        payload=dict(
                            fingerprint=value["artifact_fingerprint"],
                            decision=decision,
                            attested=attested,
                            note=note,
                            territories=territories if decision == "REVIEWED_ACCEPTED" else [],
                            entity_links=entity_links if decision == "REVIEWED_ACCEPTED" else [],
                        ),
                    )
                    if result:
                        st.rerun()
    with st.expander("Prihvaćeni nalazi — filteri"):
        period = st.text_input("Tačan citirani period (prazno: svi)", key=prefix + ":period", max_chars=100)
        geo_id = st.text_input("UUID pregledane geometrije (prazno: sve)", key=prefix + ":geometry")
        if st.button("Učitaj samo prihvaćene nalaze", key=prefix + ":retrieve"):
            values = call("claims", filters={k: v for k, v in {"period": period, "geometry_id": geo_id}.items() if v})
            if values is not None:
                render_evidence("Pregledani nalazi i obuhvat", values)
