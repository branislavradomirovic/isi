"""GIS Data workspace: scoped geometry review, map/table and exact result binding."""

from __future__ import annotations
from datetime import date
import json
import streamlit as st
from src.streamlit_app import spatial_api
from src.streamlit_app.spatial_view import collection, build_map, map_component, map_key, selection_id, MAX_FEATURES
from src.streamlit_app.api_client import AuthenticationRequired, AccessDenied, ApiUnavailable
from src.platform.spatial.contracts import GeometryCreate, GeometryError, MAX_BYTES

ERRORS = (AuthenticationRequired, AccessDenied, ApiUnavailable)


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ERRORS as exc:
        st.warning(str(exc))
        return None


def _import(call, params, targets, prefix):
    if not targets:
        st.info("Nema domenskog identiteta sa potvrđenom šifrom. Prvo podesite profil/objekat ili ORDO jedinicu.")
        return
    st.caption(
        "Izbor identiteta prikazuje do 101 zapis po domenskoj vrsti. Za ORDO granicu unesite isti izvor i verziju kao u potvrđenom identitetu."
    )
    with st.expander("Uvoz nove verzije geometrije"):
        with st.form(prefix + "-import"):
            target = st.selectbox(
                "Domenski identitet", targets, format_func=lambda x: f"{x['kind']} · {x['key']} · {x['name']}"
            )
            version = st.text_input("Verzija geometrije")
            uri = st.text_input("HTTPS izvor bez tokena")
            source_version = st.text_input("Verzija izvora")
            source_hash = st.text_input("SHA-256 originalnog izvora")
            license_id = st.text_input("Identifikator licence / odobrenja")
            crs = st.selectbox("Originalni CRS", ["OGC:CRS84", "EPSG:4326"])
            axis = st.checkbox("Potvrđujem redosled longitude / latitude")
            start = st.date_input("Važi od", date.today())
            finite = st.checkbox("Definisan kraj važenja")
            end = st.date_input("Važi do", date.today())
            upload = st.file_uploader(
                "Jedna GeoJSON geometrija (Point, Polygon ili MultiPolygon)", type=["json", "geojson"]
            )
            if st.form_submit_button("Registruj DRAFT"):
                try:
                    if not axis or upload is None or upload.size > MAX_BYTES:
                        raise ValueError("Potvrdite ose i izaberite datoteku do 200000 bajtova.")
                    body = GeometryCreate(
                        **params,
                        domain_kind=target["kind"],
                        domain_id=target["id"],
                        version=version,
                        source_uri=uri,
                        source_version=source_version,
                        declared_source_sha256=source_hash,
                        license_identifier=license_id,
                        original_crs=crs,
                        axis_order="longitude_latitude",
                        valid_from=start,
                        valid_to=end if finite else None,
                        geometry=json.loads(upload.getvalue()),
                    )
                except (ValueError, TypeError, RecursionError):
                    st.error(
                        "Neispravan uvoz. Proverite obavezna polja, veličinu, tip, ose, CRS i datume prema Help-u."
                    )
                else:
                    if _safe(call, "create", method="POST", payload=body.model_dump(mode="json")) is not None:
                        st.success("DRAFT registrovan. Pregled i potvrda su zasebni koraci.")
                        st.rerun()


def _review(call, rows, permissions, prefix):
    if not rows or not permissions.intersection({"data.governance.manage", "data.validate"}):
        return
    with st.expander("Ljudski pregled i povlačenje geometrije"):
        row = st.selectbox(
            "Verzija za pregled",
            rows,
            key=prefix + "-review-id",
            format_func=lambda x: f"{x['domain_binding']['key']} · {x['version']} · {x['state']}",
        )
        st.json(row)
        options = []
        if "data.governance.manage" in permissions and row["state"] != "RETIRED":
            options.append("RETIRED")
            if row["state"] == "DRAFT":
                options.insert(0, "PROPOSED")
        if "data.validate" in permissions and row["state"] == "PROPOSED":
            options.insert(0, "VALIDATED")
        if options:
            with st.form(prefix + "-review-" + row["id"]):
                state = st.selectbox("Odluka", options)
                attested = st.checkbox("Proverio/la sam izvor, licencu, identitet, lokaciju i važenje")
                if st.form_submit_button("Evidentiraj odluku"):
                    if state == "VALIDATED" and not attested:
                        st.error("Potvrda zahteva izričitu stručnu proveru izvora i lokacije.")
                    elif (
                        _safe(
                            call,
                            "review",
                            method="POST",
                            geometry_id=row["id"],
                            payload={
                                "state": state,
                                "revision": row["revision"],
                                "source_license_location_attested": attested,
                            },
                        )
                        is not None
                    ):
                        st.rerun()
        else:
            st.caption("Nema dozvoljene promene stanja za ovu verziju i vašu rolu.")


def _units(call, params, permissions, prefix):
    with st.expander("ORDO prostorne jedinice — identitet pre geometrije"):
        value = _safe(call, "units")
        if value is None:
            return
        rows = value["items"]
        st.dataframe(rows, hide_index=True, width="stretch")
        if value["truncated"]:
            st.warning("Prikazano je prvih 100 jedinica; katalog nije potpun.")
        if "data.governance.manage" in permissions:
            with st.form(prefix + "-unit-create"):
                key = st.text_input("Stabilna šifra jedinice")
                name = st.text_input("Naziv jedinice")
                kind = st.selectbox(
                    "Tip jedinice", ["national", "macro_region", "region", "local_government", "custom"]
                )
                uri = st.text_input("HTTPS izvor granice")
                version = st.text_input("Verzija granice")
                gid = st.text_input("Izvorni identifikator geometrije")
                sha = st.text_input("SHA-256 graničnog artefakta")
                crs = st.selectbox("CRS granice", ["OGC:CRS84", "EPSG:4326"])
                start = st.date_input("Jedinica važi od", date.today())
                finite = st.checkbox("Jedinica ima kraj važenja")
                end = st.date_input("Jedinica važi do", date.today())
                if st.form_submit_button("Registruj identitet jedinice"):
                    body = dict(
                        params,
                        spatial_unit_key=key,
                        spatial_unit_type=kind,
                        name=name,
                        boundary_source=uri,
                        boundary_version=version,
                        geometry_id=gid,
                        crs=crs,
                        artifact_sha256=sha,
                        valid_from=str(start),
                        valid_to=str(end) if finite else None,
                    )
                    if _safe(call, "unit_create", method="POST", payload=body) is not None:
                        st.rerun()
        if rows and permissions.intersection({"data.validate", "data.governance.manage"}):
            row = st.selectbox(
                "Identitet za pregled",
                rows,
                key=prefix + "-unit-review-id",
                format_func=lambda x: f"{x['name']} · {x['lifecycle_status']}",
            )
            choices = []
            if "data.governance.manage" in permissions:
                if row["lifecycle_status"] == "draft":
                    choices.append("proposed")
                if row["lifecycle_status"] == "validated":
                    choices.append("retired")
            if "data.validate" in permissions and row["lifecycle_status"] == "proposed":
                choices.append("validated")
            if choices:
                with st.form(prefix + "-unit-review-" + row["id"]):
                    state = st.selectbox("Stanje identiteta", choices)
                    note = st.text_area("Obrazloženje pregleda identiteta")
                    if st.form_submit_button("Sačuvaj pregled identiteta"):
                        if (
                            _safe(
                                call,
                                "unit_review",
                                geometry_id=row["id"],
                                method="POST",
                                payload={"state": state, "note": note},
                            )
                            is not None
                        ):
                            st.rerun()
            else:
                st.caption("Nema dozvoljene promene identiteta u ovom stanju i vašoj roli.")
        st.caption("Potvrda identiteta nije potvrda koordinata/licence. Geometrija se uvozi i pregleda zasebno.")


def render_map_table(details, *, scope, at_date):
    data = collection(details)
    ids = [f["id"] for f in data["features"]]
    prefix = map_key(scope, at_date, details)
    selector = prefix + "-selected"
    labels = {f["id"]: f["properties"]["label"] for f in data["features"]}
    st.selectbox("Izabrana teritorija / objekat / verzija", ids, format_func=labels.get, key=selector)

    def changed(widget_key, table=False):
        event = st.session_state.get(widget_key, {})
        selection = event.get("selection", {})
        index = selection.get("rows", []) if table else selection.get("indices", {}).get("geometry-layer", [])
        chosen = selection_id(index, ids)
        if chosen is not None:
            st.session_state[selector] = chosen

    selected = st.session_state[selector]
    st.caption(
        "Legenda: plavo = granica, oker = institucionalni objekat, ljubičasta ivica = izbor. Boje ne označavaju rizik."
    )
    if st.checkbox("Prikaži interaktivnu kartu", value=True, key=prefix + "-visible"):
        try:
            map_widget = prefix + "-map"

            def map_changed():
                picked = st.session_state.get(map_widget, {}).get("picked")
                if picked in ids:
                    st.session_state[selector] = picked

            map_component()(
                data={**build_map(data, selected), "dataset": prefix},
                height=420,
                width="stretch",
                key=map_widget,
                on_picked_change=map_changed,
            )
        except (GeometryError, RuntimeError, ValueError):
            st.warning("Karta nije dostupna. Koristite tabelu i izbor verzije; podaci nisu zamenjeni.")
    st.caption(
        "Karta prikazuje isključivo vaše potvrđene geometrije, bez spoljne podloge. Tabela ostaje dostupna bez WebGL-a."
    )
    rows = [
        {
            "id": x["metadata"]["id"],
            "izabrano": x["metadata"]["id"] == selected,
            "ključ": x["metadata"]["domain_binding"]["key"],
            "verzija": x["metadata"]["version"],
            "tip": x["geometry"]["type"],
            "važi od": x["metadata"]["valid_from"],
            "važi do": x["metadata"].get("valid_to"),
        }
        for x in details
    ]
    widget = prefix + "-table"
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        key=widget,
        selection_mode="single-row",
        on_select=lambda: changed(widget, True),
    )
    st.caption("Izabrani red — isti identitet kao figura i poreklo ispod")
    st.table([r for r in rows if r["id"] == selected])
    return next(x for x in details if x["metadata"]["id"] == selected)


def render_spatial_workspace(*, token, shell):
    workspace = shell.get("workspace") or {}
    if not workspace.get("id"):
        st.info("GIS zahteva izabran radni prostor.")
        return
    product = shell["product"]["code"]
    params = {"organization_id": str(shell["organization"]["id"]), "workspace_id": str(workspace["id"])}
    scope = (params["organization_id"], product, params["workspace_id"])
    prefix = "gis-" + "-".join(scope)
    permissions = set(shell["product"].get("permission_codes", []))
    if "data.read" not in permissions:
        st.info("Nemate pravo čitanja GIS podataka.")
        return
    st.subheader(f"{product} · GIS i verzionisani prostorni podaci")
    st.caption("Podaci → GIS. Help: uvoz, review i karta; nedostajuća geometrija nije nula.")
    with st.expander("GIS Help — koraci, dozvole i ograničenja"):
        from pathlib import Path

        st.markdown(Path(__file__).resolve().parents[2].joinpath("docs/help/ISI-SPATIAL-DATA-GUIDE.md").read_text())

    def call(action, **kwargs):
        return spatial_api.call(token, product, action, **params, **kwargs)

    rows = _safe(call, "list")
    if rows is None:
        return
    if len(rows) == 100:
        st.warning("Katalog je ograničen na 100 najnovijih verzija; moguće su dodatne verzije.")
    if product == "ORDO":
        _units(call, params, permissions, prefix)
    if "data.upload" in permissions:
        targets = _safe(call, "targets")
        if targets is not None:
            _import(call, params, targets, prefix)
    _review(call, rows, permissions, prefix)
    at_date = st.date_input(
        "Datum važenja geometrije (nije period analitičkog nalaza)", date.today(), key=prefix + "-date"
    )
    kinds = sorted({x["domain_kind"] for x in rows})
    layers = st.multiselect("Slojevi", kinds, default=kinds, key=prefix + "-layers")
    eligible = [
        x
        for x in rows
        if x["state"] == "VALIDATED"
        and x["domain_kind"] in layers
        and date.fromisoformat(x["valid_from"]) <= at_date
        and (not x.get("valid_to") or at_date <= date.fromisoformat(x["valid_to"]))
    ]
    st.caption(
        f"Verzije u katalogu: {len(rows)} · važeće za izbor: {len(eligible)} · van izbora: {len(rows) - len(eligible)}"
    )
    if not eligible:
        st.info(
            "Nema potvrđene geometrije za izabrani datum i sloj. Uvezite stvarni dozvoljeni izvor i završite review."
        )
        return
    options = {x["id"]: x for x in eligible}
    ids = st.multiselect(
        "Verzije na karti (najviše 25)",
        list(options),
        default=list(options)[:MAX_FEATURES],
        format_func=lambda x: f"{options[x]['domain_binding']['key']} · {options[x]['version']}",
        max_selections=MAX_FEATURES,
        key=prefix + "-versions-" + str(at_date) + "-" + "-".join(layers),
    )
    details, unavailable = [], 0
    for gid in ids:
        detail = _safe(call, "detail", geometry_id=gid, at_date=at_date)
        if detail is None:
            unavailable += 1
        else:
            details.append(detail)
    st.caption(f"Učitane geometrije: {len(details)} · nedostupne/nepodobne: {unavailable}")
    if not details:
        return
    try:
        chosen = render_map_table(details, scope=scope, at_date=at_date)
    except GeometryError:
        st.warning("Izbor prelazi granice bezbednog prikaza. Smanjite broj verzija; nema tihog uprošćavanja.")
        st.dataframe([x["metadata"] for x in details], hide_index=True, width="stretch")
        return
    row = chosen["metadata"]
    st.subheader("Poreklo izabrane verzije")
    st.json(row)
    with st.expander("Tačna geometrija izabrane verzije"):
        st.json(chosen["geometry"])
    if "analysis.read" in permissions:
        result = _safe(call, "results", geometry_id=row["id"], at_date=at_date)
        if result is not None:
            if not result["results"]:
                st.info("Analitički sloj nije dostupan: " + result["reason"])
            else:
                st.caption(
                    "Sačuvane identity-only agregacije. Datum karte nije period opservacija; bez spatial join-a/kauzalnih zaključaka."
                )
                selected = st.selectbox(
                    "Analitički rezultat",
                    result["results"],
                    format_func=lambda x: f"{x['indicator']} · {x['rule']} · {x['id']}",
                    key=prefix + "-result-" + row["id"],
                )
                st.dataframe([selected], hide_index=True, width="stretch")
                st.bar_chart(
                    [{"rezultat": selected["indicator"], "vrednost": selected["value"]}],
                    x="rezultat",
                    y="vrednost",
                    x_label="Indikator",
                    y_label=selected["unit"] or "Jedinica nije navedena",
                )
            if result.get("ineligible_count"):
                st.warning(f"Nepodobnih istorijskih rezultata: {result['ineligible_count']}; nisu prikazani.")
            if result.get("truncated"):
                st.warning("Prikazano najviše 10 najnovijih analitičkih rezultata.")
    if "data.export" in permissions and st.button("Pripremi izvoz izabrane geometrije", key=prefix + "-export"):
        payload = _safe(call, "export", geometry_id=row["id"], at_date=at_date)
        if payload is not None:
            st.download_button(
                "Preuzmi GeoJSON sa poreklom",
                json.dumps(payload, ensure_ascii=False, allow_nan=False),
                file_name=f"{product}-{row['id']}.geojson",
                mime="application/geo+json",
                key=prefix + "-download",
                on_click="ignore",
            )
