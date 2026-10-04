from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DocumentItemView:
    title: str
    href: str
    institution_key: str
    institution_label: str
    institution_mark: str
    document_type: str
    year: str
    search_text: str


@dataclass(frozen=True)
class DocumentGroupView:
    key: str
    label: str
    mark: str
    description: str
    items: tuple[DocumentItemView, ...]


@dataclass(frozen=True)
class LibraryEntryView:
    title: str
    href: str
    image_src: str
    collection: str
    source_label: str
    year: str
    search_text: str


@dataclass(frozen=True)
class ActivityEntryView:
    title: str
    href: str
    image_src: str
    excerpt: str
    kind: str
    year: str
    date_text: str
    location: str
    search_text: str


INSTITUTIONS = {
    "sipru": (
        "SIPRU / Vlada Republike Srbije",
        "SIPRU",
        "Strategije, planovi i smernice povezani sa socijalnim uključivanjem i javnim politikama Republike Srbije.",
    ),
    "rzs": (
        "Republički zavod za statistiku",
        "RZS",
        "Zvanična statistika, metodologije i istraživanja relevantna za socijalnu uključenost i javne politike.",
    ),
    "undp": (
        "UNDP Srbija",
        "UNDP",
        "Analize, razvojni okviri i praktični resursi Programa Ujedinjenih nacija za razvoj.",
    ),
    "local": (
        "Lokalne samouprave",
        "JLS",
        "Lokalni planovi, vodiči, strateški dokumenti i primeri prakse gradova i opština.",
    ),
    "un": (
        "Ujedinjene nacije (UN)",
        "UN",
        "Globalni okviri, politike, izveštaji i smernice relevantni za socijalnu inkluziju i održivi razvoj.",
    ),
    "eu": (
        "Evropska unija",
        "EU",
        "Strategije, akcioni planovi, smernice i analize evropskih institucija.",
    ),
    "serbia": (
        "Republika Srbija",
        "RS",
        "Nacionalne strategije, propisi, planovi i javne politike Republike Srbije.",
    ),
    "unicef": (
        "UNICEF i partnerske organizacije",
        "UN+",
        "Izveštaji, smernice i analize međunarodnih i partnerskih organizacija.",
    ),
    "isi": (
        "Institut za socijalnu inkluziju",
        "ISI",
        "Dokumenti i materijali koje objavljuje ili kurira ISI.",
    ),
    "other": (
        "Ostali izvori",
        "•",
        "Dodatni institucionalni i stručni izvori iz migriranog sadržaja.",
    ),
}


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def _year(text: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", text or "")
    return match.group(0) if match else ""


def _date_text(text: str) -> str:
    compact = _clean(text)
    patterns = (
        r"\b\d{1,2}[.–-]\d{1,2}\.?\s+[A-Za-zČĆŽŠĐčćžšđ]+\s+20\d{2}\.?(?:\s+godine)?",
        r"\b\d{1,2}\.\s+[A-Za-zČĆŽŠĐčćžšđ]+\s+20\d{2}\.?(?:\s+godine)?",
        r"\b20\d{2}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            return match.group(0)
    return ""


def _document_type(title: str) -> str:
    low = title.casefold()
    labels = (
        (("strateg", "strategy"), "Strategija"),
        (("akcioni plan", "action plan"), "Akcioni plan"),
        (("zakon", "law ", "regulation"), "Propis"),
        (("izvešt", "izvjest", "report"), "Izveštaj"),
        (("smernic", "guideline", "framework", "policy"), "Smernice"),
        (("analiz", "analysis"), "Analiza"),
        (("agenda", "sdg"), "Okvir"),
    )
    for needles, label in labels:
        if any(needle in low for needle in needles):
            return label
    return "Dokument"


def _institution_key(title: str, href: str) -> str:
    value = f"{title} {href}".casefold()
    if any(token in value for token in ("sipru", "socijalno uključivanje i smanjenje siromaštva", "socijalno ukljucivanje i smanjenje siromastva")):
        return "sipru"
    if any(token in value for token in ("stat.gov.rs", "republički zavod za statistiku", "republicki zavod za statistiku", "statistički godišnjak", "statisticki godisnjak")):
        return "rzs"
    if any(token in value for token in ("undp", "undp.org")):
        return "undp"
    if any(token in value for token in ("lokalna samouprava", "lokalne samouprave", "opština", "opstina", "grad ", "lokalni akcioni", "lokalne usluge")):
        return "local"
    if any(token in value for token in ("unicef", "ilo", "who", "world bank", "svetska banka")):
        return "unicef"
    if any(token in value for token in ("european union", "evropska unija", "europa.eu", "european commission", "ec.europa.eu", "european parliament")):
        return "eu"
    if any(token in value for token in ("gov.rs", "republika srbija", "službeni glasnik", "sluzbeni glasnik")):
        return "serbia"
    if any(token in value for token in ("un.org", "united nations", "ujedinjene nacije", "agenda 2030", "sdg ", "human rights-based", "hrba")):
        return "un"
    if any(token in value for token in ("isi.rs", "institut za socijalnu inkluziju")):
        return "isi"
    return "other"


def _valid_href(href: str) -> bool:
    href = (href or "").strip()
    if not href or href.startswith(("#", "javascript:", "mailto:")):
        return False
    parsed = urlsplit(href)
    return parsed.scheme in {"", "http", "https"}


def document_catalog_from_html(body_html: str, *, max_items: int = 180) -> list[DocumentGroupView]:
    """Build a read-only presentation index over migrated legacy document links.

    No URL/title is invented: grouping enriches only anchors already present in the
    migrated page body.  The expanded institution registry makes the presentation
    useful for the new ISI design without changing the migration source of truth.
    """
    soup = BeautifulSoup(body_html or "", "html.parser")
    seen: set[tuple[str, str]] = set()
    grouped: dict[str, list[DocumentItemView]] = {key: [] for key in INSTITUTIONS}
    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True))
        if len(title) < 4:
            # The preserved legacy documents page uses icon-only links. Its
            # document title is the single preceding h3 in the smallest shared
            # container; category headings are excluded by requiring uniqueness.
            heading = anchor.find_previous("h3")
            if heading is not None:
                for container in anchor.parents:
                    headings = container.find_all("h3")
                    if (
                        heading in headings
                        and len(headings) == 1
                        and heading.parent is not container
                        and anchor.parent is not heading.parent
                    ):
                        title = _clean(heading.get_text(" ", strip=True))
                        break
                    if len(headings) > 1:
                        break
        href = (anchor.get("href") or "").strip()
        if not title or len(title) < 4 or not _valid_href(href):
            continue
        identity = (title.casefold(), href)
        if identity in seen:
            continue
        seen.add(identity)
        key = _institution_key(title, href)
        label, mark, _ = INSTITUTIONS[key]
        item = DocumentItemView(
            title=title,
            href=href,
            institution_key=key,
            institution_label=label,
            institution_mark=mark,
            document_type=_document_type(title),
            year=_year(title),
            search_text=f"{title} {label} {_document_type(title)} {_year(title)}".casefold(),
        )
        grouped[key].append(item)
        if sum(len(values) for values in grouped.values()) >= max_items:
            break

    result: list[DocumentGroupView] = []
    for key in ("sipru", "rzs", "undp", "local", "un", "eu", "serbia", "unicef", "isi", "other"):
        items = grouped[key]
        if not items:
            continue
        label, mark, description = INSTITUTIONS[key]
        result.append(DocumentGroupView(key=key, label=label, mark=mark, description=description, items=tuple(items)))
    return result


COLLECTIONS = (
    ("Socijalna inkluzija", ("inkluz", "siroma", "nejednak", "socijal")),
    ("Zapošljavanje i rad", ("zapošlj", "zaposlj", "rad", "employment", "labour", "labor")),
    ("Deca i porodica", ("deca", "djec", "porod", "child", "family")),
    ("Politike i upravljanje", ("polit", "upravlj", "govern", "strateg")),
    ("Održivi razvoj", ("održiv", "odrziv", "sustain", "sdg")),
)


def _collection(title: str) -> str:
    low = title.casefold()
    for label, needles in COLLECTIONS:
        if any(needle in low for needle in needles):
            return label
    return "Istraživanja i publikacije"


def library_catalog_from_html(body_html: str, *, max_items: int = 240) -> list[LibraryEntryView]:
    """Extract publication-like anchors and nearby images from migrated library HTML."""
    soup = BeautifulSoup(body_html or "", "html.parser")
    result: list[LibraryEntryView] = []
    seen: set[tuple[str, str]] = set()
    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        title = _clean(anchor.get_text(" ", strip=True))
        if not title or len(title) < 4 or not _valid_href(href):
            continue
        identity = (title.casefold(), href)
        if identity in seen:
            continue
        seen.add(identity)
        image = anchor.find("img")
        if image is None:
            parent = anchor.parent
            image = parent.find("img") if parent is not None else None
        image_src = (image.get("src") or "").strip() if image else ""
        collection = _collection(title)
        source_key = _institution_key(title, href)
        source_label = INSTITUTIONS[source_key][0]
        result.append(
            LibraryEntryView(
                title=title,
                href=href,
                image_src=image_src,
                collection=collection,
                source_label=source_label,
                year=_year(title),
                search_text=f"{title} {collection} {source_label} {_year(title)}".casefold(),
            )
        )
        if len(result) >= max_items:
            break
    return result


def _activity_kind(title: str) -> str:
    value = title.casefold()
    if any(token in value for token in ("konferenc", "conference", "forum", "skup")):
        return "Konferencija"
    if any(token in value for token in ("radionic", "workshop")):
        return "Radionica"
    if any(token in value for token in ("dijalog", "dialog", "okrugli sto", "roundtable")):
        return "Javni dijalog"
    if any(token in value for token in ("obuk", "training", "seminar")):
        return "Obuka"
    if any(token in value for token in ("publik", "publication", "zbornik", "policy brief")):
        return "Publikacija"
    return "Aktivnost"


def _nearby_excerpt(anchor) -> str:
    parent = anchor.parent
    if parent is None:
        return ""
    paragraphs = parent.find_all("p", limit=3)
    texts = [_clean(p.get_text(" ", strip=True)) for p in paragraphs]
    texts = [text for text in texts if text and text.casefold() not in _clean(anchor.get_text(" ", strip=True)).casefold()]
    return " ".join(texts)[:360]


def _nearby_location(anchor) -> str:
    parent = anchor.parent
    text = _clean(parent.get_text(" ", strip=True)) if parent is not None else ""
    for city in ("Beograd", "Novi Sad", "Niš", "Nis", "Kragujevac", "Subotica", "Srbija"):
        if city.casefold() in text.casefold():
            return "Niš" if city == "Nis" else city
    return ""


def activity_catalog_from_html(body_html: str, *, max_items: int = 18) -> list[ActivityEntryView]:
    """Extract activity links from migrated HTML with safe visual metadata.

    Existing migrated images are reused when present.  Missing images are deliberately
    left empty so the template can render a local semantic illustration rather than a
    broken image placeholder or an invented documentary photograph.
    """
    soup = BeautifulSoup(body_html or "", "html.parser")
    result: list[ActivityEntryView] = []
    seen: set[tuple[str, str]] = set()
    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        title = _clean(anchor.get_text(" ", strip=True))
        if not _valid_href(href) or len(title) < 12:
            continue
        identity = (title.casefold(), href)
        if identity in seen:
            continue
        seen.add(identity)
        parent = anchor.parent
        image = anchor.find("img")
        if image is None and parent is not None:
            image = parent.find("img")
        image_src = (image.get("src") or "").strip() if image else ""
        context_text = _clean(parent.get_text(" ", strip=True)) if parent is not None else title
        kind = _activity_kind(title)
        result.append(
            ActivityEntryView(
                title=title,
                href=href,
                image_src=image_src,
                excerpt=_nearby_excerpt(anchor),
                kind=kind,
                year=_year(context_text),
                date_text=_date_text(context_text),
                location=_nearby_location(anchor),
                search_text=f"{title} {kind} {context_text}".casefold(),
            )
        )
        if len(result) >= max_items:
            break
    return result
