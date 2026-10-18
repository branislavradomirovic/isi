"""Trusted illustrated manual shared by the existing product Help surfaces."""

from pathlib import Path
import hashlib
import json
import re
import unicodedata
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
        if metadata.get("view") != "DESKTOP" or metadata.get("width", 0) < 1200:
            raise ValueError("help_desktop_asset_required")
        kind = (
            "lokalni sintetički primer"
            if metadata["kind"] == "SYNTHETIC"
            else "ranije pregledan server — stanje podataka iz tog pregleda"
        )
        st.image(
            image_bytes(name, metadata),
            caption=f"{metadata['caption']} · {kind} · {metadata['captured']}",
            width=min(metadata.get("width", 1280), 960),
        )


def section_anchor(title):
    """Stable ASCII anchors, shared by the section index and rendered headings."""
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    return "help-" + re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def _section_index(titles):
    st.markdown(
        '<style>[data-testid="stImageContainer"] { max-width: 100%; }'
        '[data-testid="stImageContainer"] img { height: auto; }</style>',
        unsafe_allow_html=True,
    )
    with st.expander("Sadržaj ovog uputstva", expanded=True):
        st.markdown("\n".join(f"- [{title}](#{section_anchor(title)})" for title in titles))


def _section(title, level=4):
    st.subheader(title, anchor=section_anchor(title))


def render_topic(topic, *, public=False):
    if public and topic["id"] not in PUBLIC:
        st.info("Ova tema zahteva prijavu u platformu.")
        return
    data = manual()
    detail = data["topics"][topic["id"]]
    st.markdown(f"### {topic['title']}")
    _section_index([label for label, _ in LABELS])
    st.info(
        "Ekrani u uputstvu prikazuju dokumentovani primer i datum snimanja. Stvarni podaci i dostupne radnje zavise od vašeg konteksta i dozvola."
    )
    for label, field in LABELS:
        _section(label)
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
        related = [data["chapters"][code] for code in detail["related_chapters"]]
        image_count = sum(len(chapter["screens"]) for chapter in related)
        st.info(
            f"Povezani detaljni tokovi imaju ukupno {image_count} desktop snimaka. "
            "Izaberite tok u polju za detaljna poglavlja na vrhu Help-a: "
            + "; ".join(chapter["title"] for chapter in related)
        )
    for title, text in detail.get("sections", []):
        st.markdown("#### " + title)
        st.write(text)


def chapters(product):
    return {key: value for key, value in manual()["chapters"].items() if product in value["products"]}


def chapter_label(chapter):
    count = len(chapter["screens"])
    return f"{chapter['title']} · {count} desktop {screen_noun(count)}"


def topic_label(topic):
    count = len(manual()["topics"][topic["id"]]["screens"])
    return f"{topic['id']} · {topic['title']} · {count} desktop {screen_noun(count)}"


def screen_noun(count):
    if count % 10 == 1 and count % 100 != 11:
        return "snimak"
    if count % 10 in {2, 3, 4} and count % 100 not in {12, 13, 14}:
        return "snimka"
    return "snimaka"


def workflow_selector(values, *, key, label="Detaljni tok sa ekranima"):
    """Keep multi-screen procedures visible and separate from short topic summaries."""
    options = {chapter_label(chapter): code for code, chapter in values.items()}
    selected = st.selectbox(
        f"{label} ({len(values)} dostupno)",
        list(options),
        index=None,
        placeholder="Izaberite detaljno poglavlje",
        key=key,
    )
    return options.get(selected)


def render_chapter(code, *, product):
    values = chapters(product)
    if code not in values:
        st.info("Tema nije dostupna u aktivnom proizvodu.")
        return
    data = manual()
    chapter = values[code]
    st.markdown("### " + chapter["title"])
    _section_index([title for title, _ in chapter["sections"]])
    st.caption(
        "Snimci su označeni izvorom i datumom. Prikazuju dokumentovani desktop primer; "
        "ne potvrđuju stvarne institucionalne podatke, dozvole ili metodologiju."
    )
    for i, (title, body) in enumerate(chapter["sections"], 1):
        _section(title)
        st.markdown(body)
        mapping = chapter.get("screen_sections")
        if mapping is not None:
            _screens(data, mapping.get(str(i), []))
        elif i == 4:
            _screens(data, chapter["screens"])
