"""Author current Word edition with the same governed Help content and figures.
Run with bundled document runtime; no production data or credentials.
"""

from pathlib import Path
import hashlib
import json
import re
import ast
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def topic_source(module, name):
    tree = ast.parse((ROOT / "src/streamlit_app" / (module + ".py")).read_text())
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)
    )
    return ast.literal_eval(node.value)


SHARED_HELP_TOPICS = topic_source("shared_help_workspace", "SHARED_HELP_TOPICS")
SIMPA_HELP_TOPICS = topic_source("simpa_help_workspace", "SIMPA_HELP_TOPICS")
ORDO_HELP_TOPICS = topic_source("ordo_help_workspace", "ORDO_HELP_TOPICS")

FIELDS = [
    ("Svrha funkcije", "what"),
    ("Kada koristiti funkciju", "when"),
    ("Pristup i odgovornost", "roles_permissions"),
    ("Postupak korak po korak", "steps"),
    ("Polja i statusi", "fields_statuses"),
    ("Primer upotrebe", "example"),
    ("Granice funkcije", "non_goals"),
    ("Greške i oporavak", "errors_recovery"),
    ("Ograničenja", "limitations"),
    ("Poreklo i ljudski pregled", "provenance_review"),
]


def clean(text):
    text = re.sub(r"`([^`]+)`", r"\1", text).replace("**", "")
    return text


def heading(text):
    return re.sub(r"[^\w\sČĆŠĐŽčćšđž]", " ", text).strip()


def build():
    output = ROOT / "automation/evidence/ISI-30F/desktop-docs/ISI_prirucnik_desktop.docx"
    base = ROOT / "docs/help/templates/ISI-MANUAL-TEMPLATE.docx"
    d = Document(base)
    # Preserve approved typography/page/header styles; current edition replaces stale workflows.
    body = d._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"]:
        style = d.styles[name]
        style.font.name = "Calibri"
        style.font.color.rgb = RGBColor(0, 0, 0)
    d.styles["Normal"].font.size = Pt(11)
    d.styles["Normal"].paragraph_format.space_after = Pt(7)
    d.styles["Normal"].paragraph_format.line_spacing = 1.08
    for name, size in [("Title", 28), ("Heading 1", 21), ("Heading 2", 15), ("Heading 3", 12)]:
        d.styles[name].font.size = Pt(size)
    for el in list(d.styles.element.iter(qn("w:pBdr"))):
        el.getparent().remove(el)
    for sec in d.sections:
        sec.bottom_margin = Cm(2.5)
        sec.footer_distance = Cm(1.0)
        sec.header.paragraphs[0].text = "ISI  Korisnički i administratorski priručnik"
        for p in sec.footer.paragraphs:
            p.text = "12. oktobar 2026  |  Desktop izdanje  |  "
            page = OxmlElement("w:fldSimple")
            page.set(qn("w:instr"), "PAGE")
            p._p.append(page)
    data = json.loads((ROOT / "docs/help/ISI-ILLUSTRATED-MANUAL.json").read_text())
    figures = []
    topics = []
    chapters = []

    def para(text, style=None):
        return d.add_paragraph(clean(text), style=style)

    index_entries = []
    def bookmark(p, name, identity):
        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), str(identity))
        start.set(qn("w:name"), name)
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), str(identity))
        p._p.insert(0, start)
        p._p.append(end)

    def link(p, label, target):
        el = OxmlElement("w:hyperlink")
        el.set(qn("w:anchor"), target)
        el.set(qn("w:history"), "1")
        run = OxmlElement("w:r")
        prop = OxmlElement("w:rPr")
        style = OxmlElement("w:rStyle")
        style.set(qn("w:val"), "Hyperlink")
        prop.append(style)
        run.append(prop)
        value = OxmlElement("w:t")
        value.text = label
        run.append(value)
        el.append(run)
        p._p.append(el)

    def h(text, level):
        p = d.add_heading(heading(text), level)
        if level <= 2:
            target = "Section" + str(len(index_entries) + 1)
            bookmark(p, target, len(index_entries) + 2)
            index_entries.append((heading(text), target, level))
            back = d.add_paragraph()
            back.paragraph_format.space_after = Pt(3)
            link(back, "Povratak na sadržaj", "ManualContents")
        return p

    def chapter(title):
        d.add_page_break()
        h(title, 1)

    def image(name):
        item = data["assets"][name]
        path = ROOT / "docs/help/screens" / name
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        width, height = Image.open(path).size
        assert width >= 1200, "Authenticated manual requires contextual desktop screenshots"
        w = 17.1
        w = min(w, 17.8 * width / height)
        p = d.add_paragraph()
        p.paragraph_format.keep_with_next = True
        run = p.add_run()
        shape = run.add_picture(str(path), width=Cm(w))
        shape._inline.docPr.set("descr", item["caption"])
        kind = "lokalni sintetički primer" if item["kind"] == "SYNTHETIC" else "ranije pregledan server"
        para(f"Slika {len(figures) + 1}  {item['caption']} · {kind} · {item['captured']}", style="Caption")
        figures.append({"asset": name, "sha256": item["sha256"]})

    def text(body):
        if re.match(r"^1\)", body.strip()):
            for step in re.split(r"\s+(?=\d+\))", body.strip()):
                para(step)
            return
        # Keep instructions as native prose/lists; render real field matrices as tables.
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("|"):
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    row = [clean(x.strip()) for x in lines[i].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r"[:\- ]+", x) for x in row):
                        rows.append(row)
                    i += 1
                if rows:
                    t = d.add_table(rows=0, cols=len(rows[0]))
                    t.autofit = False
                    for row in rows:
                        cells = t.add_row().cells
                        for cell, value in zip(cells, row):
                            cell.text = value
                    for ri, row in enumerate(t.rows):
                        pr = row._tr.get_or_add_trPr()
                        pr.append(OxmlElement("w:cantSplit"))
                        if ri == 0:
                            pr.append(OxmlElement("w:tblHeader"))
                        for ci, cell in enumerate(row.cells):
                            cell.width = Cm(5 if ci == 0 else 12.1)
                            tc = cell._tc.get_or_add_tcPr()
                            margins = OxmlElement("w:tcMar")
                            for edge in ["top", "bottom", "left", "right"]:
                                el = OxmlElement("w:" + edge)
                                el.set(qn("w:w"), "100")
                                el.set(qn("w:type"), "dxa")
                                margins.append(el)
                            tc.append(margins)
                            if ri == 0:
                                fill = OxmlElement("w:shd")
                                fill.set(qn("w:fill"), "E7E6E6")
                                tc.append(fill)
                                for run in cell.paragraphs[0].runs:
                                    run.bold = True
                    para("")
                continue
            # Preserve numbered steps and combine continuation lines into one readable paragraph.
            parts = [line]
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].lstrip().startswith(("|", "- "))
                and not re.match(r"^\d+\.", lines[i].strip())
            ):
                parts.append(lines[i].strip())
                i += 1
            para(" ".join(parts))

    d.add_paragraph("Detaljno uputstvo za ISI platformu SIMPA i ORDO", style="Title")
    d.add_paragraph("Korisnički i administratorski priručnik", style="Subtitle")
    para("Desktop izdanje za preprodukcijsko testiranje · 12. oktobar 2026")
    para("SIMPA i ORDO su dokumentovani za desktop/laptop rad. Sve ilustracije prikazuju desktop ekran u normalnoj razmeri. Mobilni prikaz se odnosi samo na javni ISI landing portal.")
    para(
        "Priručnik opisuje implementirane korisničke tokove, kontrolisani rad sa podacima, SIMPA i ORDO analitiku, XAI, GIS, nalaze, izveštaje i administraciju. Dostupnost zavisi od stvarnih dozvola, izvora, metodologije i modela u izabranom radnom prostoru."
    )
    para(
        "Nove ilustracije su lokalni sintetički primeri sa proverene implementacije. Raniji serverski snimci iz oktobra 2026 prikazuju tadašnje stanje podataka i nose svoj datum. Oni ne potvrđuju da su vaši registri popunjeni. Završni acceptance i deployment vode se zasebno; ovaj dokument ne sertifikuje punu institucionalnu produkciju."
    )
    para(
        "SMTP i rezervne kopije ostaju odloženi po odluci vlasnika. Stvarni MFA provajder, institucionalna kalibracija i stručna validacija nisu zamenjeni demonstracionim ekranima. Lozinke, jednokratni linkovi, sesije i tajni parametri ne pripadaju priručniku."
    )
    d.add_page_break()
    toc_title = d.add_heading("Sadržaj i indeks", 1)
    bookmark(toc_title, "ManualContents", 1)
    para("Kliknite naslov da otvorite poglavlje ili postupak. Link Povratak na sadržaj vraća vas na ovaj indeks. Word panel Navigacija prikazuje isti raspored naslova; brojevi stranica su u podnožju.")
    toc_marker = d.add_paragraph()
    chapter("Kako koristiti priručnik")
    para(
        "Najpre proverite organizaciju, proizvod i radni prostor. Jedan ISI nalog može imati zaseban pristup SIMPA i ORDO. Prijava nije dodela prava; administrator proverava članstvo, role, entitlement, pristup proizvodu i workspace."
    )
    para(
        "Osnovne teme opisuju svrhu, pristup, postupak, polja, oporavak i ljudsku odgovornost. Detaljna poglavlja zatim prikazuju nove tokove sa popunjenim sintetičkim primerima i kontrolama potvrde. Za promenjene tokove sledite aktuelna detaljna poglavlja ovog izdanja."
    )
    para(
        "U aplikaciji otvorite Pomoć. U ISI Help-u izaberite osnovnu temu ili zaseban Detaljan korisnički tok; u SIMPA/ORDO Help-u dostupna su samo pripadajuća poglavlja. Javna Pomoć prikazuje šest tema pristupa i ne otvara privatne operacije."
    )
    for group, values in [
        ("ISI zajedničke teme", SHARED_HELP_TOPICS),
        ("SIMPA aplikacija", SIMPA_HELP_TOPICS),
        ("ORDO aplikacija", ORDO_HELP_TOPICS),
    ]:
        chapter(group)
        for topic in values:
            h(topic["title"], 2)
            topics.append(topic["id"])
            detail = data["topics"][topic["id"]]
            para("Tema " + topic["id"])
            for label, key in FIELDS:
                h(label, 3)
                text(topic[key])
                if key == "steps":
                    for name in detail["screens"]:
                        image(name)
                if key == "fields_statuses" and detail["fields"]:
                    text(
                        "| Polje | Značenje |\n|---|---|\n"
                        + "\n".join("| " + k + " | " + v + " |" for k, v in detail["fields"])
                    )
            para(detail["availability"])
            if detail.get("related_chapters"):
                para(
                    "Detaljno uputstvo: "
                    + "; ".join(data["chapters"][key]["title"] for key in detail["related_chapters"])
                )
            for title, body in detail.get("sections", []):
                h(title, 3)
                text(body)
    for code, c in data["chapters"].items():
        chapter(c["title"])
        chapters.append(code)
        para("Proizvodi: " + ", ".join(c["products"]))
        mapping = c.get("screen_sections", {"4": c["screens"]})
        for i, (title, body) in enumerate(c["sections"], 1):
            h(title, 2)
            text(body)
            for name in mapping.get(str(i), []):
                image(name)
    chapter("Kontrolna lista pre institucionalne upotrebe")
    for line in [
        "Proverite identitet izvora i njegovu dozvoljenu namenu.",
        "Proverite metodologiju, verziju rezultata, vreme i teritorijalni obuhvat.",
        "Missing UNAVAILABLE i NOT_ESTIMATED nisu nula.",
        "SHAP objašnjava podržani numerički model, ne istinitost LLM nalaza.",
        "Ekstrakcija zahteva citate i zaseban ljudski pregled; prihvatanje nije dokaz institucionalne istine.",
        "Nacrt, review, odobrenje i objavljivanje izveštaja su zasebni koraci.",
        "Objavljen status unutar platforme nije javna objava niti dozvola za deljenje van organizacije.",
        "Posle prekida proverite svež status pre ponavljanja; nemojte preskakati kontrolu ili menjati izvor da biste uklonili zabranu.",
        "Operativne i institucionalne odgovornosti, stvarni MFA i kalibracija ostaju zasebno proverljivi preduslovi.",
    ]:
        para(line)
    page_map_path = output.parent / "index-pages.json"
    page_map = json.loads(page_map_path.read_text()) if page_map_path.exists() else {}
    for label, target, level in index_entries:
        p = d.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.45 if level == 2 else 0)
        p.paragraph_format.space_after = Pt(2)
        link(p, label, target)
        if target in page_map:
            p.paragraph_format.tab_stops.add_tab_stop(Cm(17.1), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            p.add_run("\t" + str(page_map[target]))
        toc_marker._p.addprevious(p._p)
    toc_marker._p.getparent().remove(toc_marker._p)
    d.core_properties.title = "Detaljno uputstvo za ISI platformu SIMPA i ORDO"
    d.core_properties.subject = "Aktuelni korisnički i administratorski tokovi sa ilustracijama"
    output.parent.mkdir(parents=True, exist_ok=True)
    d.save(output)
    manifest = {
        "filename": output.name,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "edition": "30F-DESKTOP",
        "navigation": [{"title": title, "anchor": target, "level": level} for title,target,level in index_entries],
        "index_page_numbers": bool(page_map),
        "topics": topics,
        "chapters": chapters,
        "figures": figures,
        "layout_review": "PENDING",
        "institutional_production_certification": False,
    }
    (ROOT / "automation/evidence/ISI-30F/desktop-docs/manual-authoring.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps({"filename": output.name, "figures": len(figures), "topics": len(topics), "chapters": len(chapters)})
    )


if __name__ == "__main__":
    build()
