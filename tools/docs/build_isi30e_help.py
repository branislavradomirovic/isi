"""Build governed Help from locked guides and previously reviewed screenshots."""

from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "automation/contracts/ISI-30E-ASSET-PLAN.json"


def sections(guide):
    text = (ROOT / "docs/help" / guide).read_text()
    if guide == "ISI-WORKFLOW-SHELL-GUIDE.md":
        context, scenario = text.split("## Scenariji — ORDO")
        context = context.split("## Radni kontekst")[1].strip()
        return [
            [
                "Svrha i izbor konteksta",
                "Jedan nalog koristi odobrene proizvode, dok organizacija i workspace ostaju odvojene granice podataka. Proverite kontekst pre svakog rada.",
            ],
            [
                "Pristup i preduslovi",
                "Server određuje članstvo, entitlement, pristup proizvodu, role i radni prostor. Vidljiva stavka ne daje pravo za zabranjenu operaciju.",
            ],
            ["Radni kontekst i polja", context],
            ["ORDO scenariji korak po korak", scenario.strip()],
            [
                "Status i sačuvani rezultat",
                "draft/review_ready/accepted/rejected su stanja scenarija. NOT_ESTIMATED znači da efekat nije izračunat, ne nulu. Procena i njen stručni pregled su zasebni.",
            ],
            [
                "Primer i izvori",
                "Sintetički scenario beleži pretpostavke i povezuje prihvatljiv snimak. Autor čita originalne izvore i ne upisuje izmišljeni procenat poboljšanja.",
            ],
            [
                "Mobilni i tastaturni pristup",
                "Otvorite bočni meni na telefonu. Tab i Shift Tab menjaju fokus; Enter i Space aktiviraju kontrolu. Tabela ostaje dostupna uz grafički prikaz.",
            ],
            [
                "Greške i oporavak",
                "Bez cilja prvo sačuvajte cilj; bez snimka pripremite izvor. Posle prekida osvežite status pre ponovnog slanja. Osveži pristup ponovo učitava backend odluku.",
            ],
            [
                "Ograničenja i privatnost",
                "SIMPA nema scenario modul. ORDO scenario nije prognoza, uzročni efekat ili automatska preporuka. Promena konteksta odbacuje nezavršene unose; prvo sačuvajte dozvoljenim obrascem.",
            ],
            [
                "Poreklo i ljudska odgovornost",
                "Identitet snimka, metodologija i stručni pregled ostaju proverljivi. Lokalni sintetički primer nije institucionalno odobrenje niti server potvrda.",
            ],
        ]
    chunks = re.split(r"^## (.+)$", text, flags=re.M)
    result = [[chunks[i], chunks[i + 1].strip()] for i in range(1, len(chunks), 2)]
    if not result:
        chunks = re.split(r"^\d+\. \*\*([^*]+)\*\*", text, flags=re.M)
        result = [[chunks[i].rstrip(":"), chunks[i + 1].strip()] for i in range(1, len(chunks), 2)]
    if len(result) == 7:
        result.extend(
            [
                [
                    "Svež pregled i potvrde",
                    "Posle čuvanja ili prekida osvežite status i identitet izabranog izvora. Ponovo pregledajte izmenjenu verziju pre potvrde; raniji pregled nije novo odobrenje.",
                ],
                [
                    "Proizvod i radni prostor",
                    "Proverite organizaciju, SIMPA ili ORDO i radni prostor. Ne koristite drugi kontekst da biste zaobišli zabranu; backend ostaje autoritet.",
                ],
                [
                    "Odgovornost i dokaz upotrebe",
                    "Sačuvani ID, verzija, otisak i status služe proveri porekla. Tehnički uspeh nije institucionalna metodološka validacija. Za nedostajuća prava obratite se administratoru.",
                ],
            ]
        )
    assert len(result) == 10, (guide, len(result))
    for row in result:
        row[1] = re.sub(
            r"(?m)^Nove ilustracije i Word pokrivenost ovog toka pripadaju30E; ovaj tekst sam nije\n?potpuno završena vizuelna acceptance evidencija\.?",
            "",
            row[1],
        )
        row[1] = row[1].replace(
            "Screenshots/Word parity za ovaj novi tok ostaju30E.",
            "Za ovaj tok pogledajte datirane ilustracije u ovom poglavlju.",
        )
    return result


def build():
    plan = json.loads(PLAN.read_text())
    data = json.loads(
        subprocess.check_output(
            ["git", "show", plan["baseline"] + ":docs/help/ISI-ILLUSTRATED-MANUAL.json"], cwd=ROOT, text=True
        )
    )
    dest = ROOT / "docs/help/screens"
    for name, item in plan["assets"].items():
        source = ROOT / item["source"]
        raw = source.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["source_sha256"]
        if raw.startswith(b"\xff\xd8"):
            (dest / name).write_bytes(raw)
        else:
            Image.open(source).convert("RGB").save(dest / name, quality=94)
        assert (dest / name).stat().st_size <= 2_000_000
        data["assets"][name] = {k: v for k, v in item.items() if k not in {"source", "source_sha256"}}
        data["assets"][name]["sha256"] = hashlib.sha256((dest / name).read_bytes()).hexdigest()
    for chapter in plan["chapters"]:
        value = {k: chapter[k] for k in ("title", "products", "screens", "guide")}
        value["sections"] = sections(chapter["guide"])
        groups = {str(i): [] for i in (4, 5, 8, 10)}
        for name in chapter["screens"]:
            slot = (
                "8"
                if any(x in name for x in ["readonly", "read-only", "invalid", "reset"])
                else "5"
                if any(x in name for x in ["success", "created", "receipt", "output", "export"])
                else "10"
                if "mobile" in name
                else "4"
            )
            groups[slot].append(name)
        value["screen_sections"] = {k: v for k, v in groups.items() if v}
        data["chapters"][chapter["code"]] = value
    related = {
        "ISI-H06": ["SHELL"],
        "ISI-H07": ["DATA", "INGESTION", "DATASETS", "RECOVERY", "GOVERNANCE", "PRIVACY", "GIS", "EXTRACTION"],
        "ISI-H08": ["LINKED", "RESULTS"],
        "ISI-H09": ["ADMIN"],
        "ISI-H10": ["SECURITY"],
        "ISI-H12": ["AI_REVIEW", "RESULTS"],
    }
    for code, keys in related.items():
        d = data["topics"][code]
        d["related_chapters"] = keys
        d["screens"] = data["chapters"][keys[0]]["screens"][:2]
        d["availability"] = (
            "Uputstvo opisuje lokalno provereni korisnički tok. Dostupnost u vašem okruženju zavisi od objavljene verzije, prava, stvarnih izvora i institucionalnih preduslova."
        )
        d["fields"] = [
            ["Organizacija i proizvod", "Zasebna autorizaciona granica za SIMPA i ORDO"],
            ["Verzija i otisak", "Identitet dokaza koji treba pregledati pre potvrde"],
            ["Status i potvrda", "Izvršena operacija se proverava novim odgovorom; nacrt nije odobrenje"],
        ]
    data["topics"]["ISI-H07"]["sections"] = [
        [
            "Detaljni postojeći tokovi",
            "Otvorite odgovarajuće ilustrativno poglavlje: izvori/verzije, konektor/mapiranje, kontrolisana obrada, dataset/feature, recovery, governance, privatnost, GIS ili ekstrakcija. Fizički purge ostaje zaseban operator postupak; postojeći korisnički ekran samo podnosi zahtev.",
        ]
    ]
    data["topics"]["ISI-H08"]["sections"] = [
        [
            "Izričit izbor izvora",
            "Prvi ponuđeni izvor nije automatski najnoviji. Izaberite tačan izvor i zasebno potvrdite kreiranje, pregled i objavljivanje. Pogledajte poglavlje Izveštaji pregled objavljivanje i izvoz.",
        ]
    ]
    (ROOT / "docs/help/ISI-ILLUSTRATED-MANUAL.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(len(data["topics"]), len(data["chapters"]), len(data["assets"]))


if __name__ == "__main__":
    build()
