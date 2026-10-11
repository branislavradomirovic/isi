"""Trusted illustrated manual shared by the existing product Help surfaces."""

from pathlib import Path
import hashlib
import json
import re
import streamlit as st

ROOT = Path(__file__).resolve().parents[2] / "docs/help"
PUBLIC = frozenset({"ISI-H01", "ISI-H02", "ISI-H03", "ISI-H04", "ISI-H05", "ISI-H11"})
LABELS = (
    ("Šta funkcija radi", "what"),
    ("Kada se koristi", "when"),
    ("Pristup i odgovornost", "roles_permissions"),
    ("Postupak korak po korak", "steps"),
    ("Polja i statusi", "fields_statuses"),
    ("Primer upotrebe", "example"),
    ("Granice funkcije", "non_goals"),
    ("Greške i oporavak", "errors_recovery"),
    ("Ograničenja", "limitations"),
    ("Izvori i ljudski pregled", "provenance_review"),
)


def manual():
    value = json.loads((ROOT / "ISI-ILLUSTRATED-MANUAL.json").read_text())
    if value["schema"] != "ISI-HELP-MANUAL-v1":
        raise ValueError("help_schema_invalid")
    return value


def image_bytes(name, metadata):
    if Path(name).name != name or not name.endswith(".jpg"):
        raise ValueError("help_asset_invalid")
    path = ROOT / "screens" / name
    if path.is_symlink():
        raise ValueError("help_asset_invalid")
    value = path.read_bytes()
    if len(value) > 2_000_000 or hashlib.sha256(value).hexdigest() != metadata["sha256"]:
        raise ValueError("help_asset_changed")
    return value


def _screens(data, names):
    for name in names:
        metadata = data["assets"][name]
        kind = (
            "lokalni sintetički primer"
            if metadata["kind"] == "SYNTHETIC"
            else "ranije pregledan server — stanje podataka iz tog pregleda"
        )
        st.image(
            image_bytes(name, metadata),
            caption=f"{metadata['caption']} · {kind} · {metadata['captured']}",
            width="stretch",
        )


def render_topic(topic, *, public=False):
    if public and topic["id"] not in PUBLIC:
        st.info("Ova tema zahteva prijavu u platformu.")
        return
    data = manual()
    detail = data["topics"][topic["id"]]
    st.markdown(f"### {topic['title']}")
    st.info(
        "Ekrani u uputstvu prikazuju dokumentovani primer i datum snimanja. Stvarni podaci i dostupne radnje zavise od vašeg konteksta i dozvola."
    )
    for label, field in LABELS:
        st.markdown(f"**{label}**")
        if field == "steps":
            steps = [x.strip() for x in re.split(r"\s*\d+\)\s*", topic[field]) if x.strip()]
            for i, step in enumerate(steps, 1):
                st.write(f"{i}. {step}")
            _screens(data, detail["screens"])
        else:
            st.write(topic[field])
        if field == "fields_statuses" and detail["fields"]:
            st.table([{"Polje ili opcija": key, "Značenje": text} for key, text in detail["fields"]])
    st.markdown("**Dostupnost i datum prikaza**")
    st.write(detail["availability"])
    if topic["id"] in {"ISI-H03", "ISI-H04", "ISI-H05", "ISI-H11"}:
        st.warning("SMTP je pending po odluci vlasnika. Ne očekujte novu produkcionu email isporuku.")
    if detail.get("related_chapters"):
        st.caption(
            "Detaljni korisnički tokovi: "
            + "; ".join(data["chapters"][code]["title"] for code in detail["related_chapters"])
        )
    for title, text in detail.get("sections", []):
        st.markdown("#### " + title)
        st.write(text)


def chapters(product):
    return {key: value for key, value in manual()["chapters"].items() if product in value["products"]}


def render_chapter(code, *, product):
    values = chapters(product)
    if code not in values:
        st.info("Tema nije dostupna u aktivnom proizvodu.")
        return
    data = manual()
    chapter = values[code]
    st.markdown("### " + chapter["title"])
    st.caption(
        "Detaljno uputstvo sa označenim sintetičkim ekranima. Primer ne potvrđuje stvarne institucionalne podatke ili metodologiju."
    )
    for i, (title, body) in enumerate(chapter["sections"], 1):
        st.markdown("#### " + title)
        st.markdown(body)
        mapping = chapter.get("screen_sections")
        if mapping is not None:
            _screens(data, mapping.get(str(i), []))
        elif i == 4:
            _screens(data, chapter["screens"])
