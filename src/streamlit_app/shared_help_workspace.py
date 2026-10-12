"""Static shared guidance. No identity, tenant data, API calls or mutation authority."""

from __future__ import annotations

import streamlit as st

HELP_REQUIRED_FIELDS = (
    "what",
    "when",
    "roles_permissions",
    "steps",
    "fields_statuses",
    "example",
    "non_goals",
    "errors_recovery",
    "limitations",
    "provenance_review",
)
HELP_LABELS = (
    "Šta radi",
    "Kada se koristi",
    "Role i dozvole",
    "Koraci",
    "Polja i stanja",
    "Primer",
    "Šta sistem ne radi",
    "Greške i bezbedan oporavak",
    "Ograničenja",
    "Poreklo i ljudski pregled",
)
SHARED_HELP_TOPICS = (
    {
        "id": "ISI-H01",
        "inventory_id": "INV-A01",
        "title": "Javni sajt",
        "coverage": "VERIFIED",
        "what": "Javni institucionalni sajt predstavlja ISI, SIMPA i ORDO, dokumente, biblioteku i aktivnosti.",
        "when": "Pre prijave, za upoznavanje sa Institutom i pronalaženje objavljenih izvora.",
        "roles_permissions": "Objavljeni sadržaj i javna Pomoć dostupni su bez naloga. Privatni rad zahteva institucionalni pristup.",
        "steps": "1) Otvorite početnu stranicu. 2) Izaberite SIMPA, ORDO ili rubriku u meniju. 3) Koristite SR/EN gde postoji prevod. 4) Pomoć otvara javna uputstva; Otvori platformu vodi na prijavu.",
        "fields_statuses": "Dokumenti, biblioteka i aktivnosti predstavljaju objavljeni sadržaj. Jezički izbor menja javnu stranicu; aplikaciona Pomoć je na srpskom.",
        "example": "Posetilac čita opis SIMPA, zatim otvara Pomoć da sazna kako se prihvata institucionalni poziv.",
        "non_goals": "Sajt ne otvara privatne podatke, ne dodeljuje pristup i nema javnu registraciju.",
        "errors_recovery": "Ako stranica ili dokument nisu dostupni, vratite se u meni ili kontaktirajte Institut preko objavljenog kontakta. Za problem sa nalogom koristite uputstva za prijavu.",
        "limitations": "Javni opis proizvoda nije dokaz validacije svake metodologije ili produkcionog izvršenja. Ne šaljite lozinke ili jednokratne linkove kontaktu.",
        "provenance_review": "Autoritet je objavljeni institucionalni sadržaj i njegov navedeni izvor; proverite datum i poreklo dokumenta pre stručne upotrebe.",
    },
    {
        "id": "ISI-H02",
        "inventory_id": "INV-A02",
        "title": "Prijava",
        "coverage": "VERIFIED",
        "what": "Prijava institucionalnim emailom i lozinkom otvara postojeću ISI sesiju za SIMPA i ORDO.",
        "when": "Posle prihvatanja poziva ili kada je prethodna sesija istekla/opozvana.",
        "roles_permissions": "Nalog mora biti aktivan i spreman za prijavu; pristup proizvodu zasebno zavisi od članstva, entitlement-a i rola.",
        "steps": "1) Otvorite platformu. 2) Unesite Email i Lozinku. 3) Izaberite Prijavi se. 4) Proverite organizaciju, proizvod i workspace. Oporavak naloga sadrži zahteve za novu lozinku i potvrdu emaila.",
        "fields_statuses": "Email je institucionalni identitet. Lozinka je skriven unos. Greška prijave namerno ne potvrđuje postojanje naloga. Aktivna sesija nije isto što i dodeljen pristup proizvodu.",
        "example": "Član sa aktivnim nalogom, ali bez pristupa proizvodu, dobija objašnjenje da administrator treba da dodeli pristup.",
        "non_goals": "Prijava ne kreira nalog, ne dodeljuje rolu i ne aktivira javni signup.",
        "errors_recovery": "Proverite unos; kod privremene blokade sačekajte, bez ponovljenih pokušaja. Za zaboravljenu lozinku koristite Oporavak naloga. Ako API nije dostupan, pokušajte kasnije ili prijavite problem bez tajnih podataka.",
        "limitations": "Ne delite lozinku ili sesiju. Odjavite se na deljenom uređaju. Produkcioni SMTP i stvarni MFA provajder nisu verifikovani ovim uputstvom.",
        "provenance_review": "Backend proverava identitet, rok i opoziv sesije; bezbednosni događaji ostaju njegov autoritet. Help ne potvrđuje identitet korisnika.",
    },
    {
        "id": "ISI-H03",
        "inventory_id": "INV-A03",
        "title": "Prihvatanje poziva",
        "coverage": "VERIFIED",
        "what": "Jednokratni poziv pridružuje korisnika organizaciji i primenjuje već odobrene pristupe i role.",
        "when": "Kada ovlašćeni administrator pošalje institucionalni poziv.",
        "roles_permissions": "Pristup je invitation-only. Link nosi postojeće ovlašćenje poziva; korisnik ne bira organizaciju, email ni rolu u obrascu prihvatanja.",
        "steps": "1) Otvorite originalni link iz poruke bez aktivne prijave. 2) Za novi nalog unesite Ime za prikaz i Lozinku. Postojeći nalog može ostaviti oba polja prazna. 3) Kliknite Prihvati poziv. 4) Posle uspeha proverite dostupni kontekst.",
        "fields_statuses": "Ime i lozinka potrebni su za nov nalog. Za postojeći nalog backend zadržava postojeće ime/lozinku. Poziv mora biti pending, neistekao i neopozvan; uspeh ga troši i vraća sesiju.",
        "example": "Poziv sa SIMPA product rolom otvara samo odobreni pristup; ne daje automatski ORDO pristup.",
        "non_goals": "Ovo nije javno kreiranje naloga niti proizvoljan ulazak u tenant; prihvatanje ne menja prava mimo poziva.",
        "errors_recovery": "Za istekao, iskorišćen ili opozvan link tražite novi poziv od administratora. Za odbijen nov nalog proverite ime i lozinku prema politici. Ako ste prijavljeni, zatvorite link, odjavite se i ponovo otvorite originalnu poruku.",
        "limitations": "Ne prosleđujte link, ne kopirajte njegov sadržaj u prijavu greške. Lozinku proverava backend (12–256 znakova). SMTP je pending po odluci vlasnika; postojeći validni jednokratni linkovi zadržavaju svoj tok.",
        "provenance_review": "Poziv, organizacija i dodeljene role potiču iz administrativnog traga; samo uspešan API odgovor uspostavlja sesiju. Administrator odgovara za ispravnost dodele.",
    },
    {
        "id": "ISI-H04",
        "inventory_id": "INV-A04",
        "title": "Potvrda emaila",
        "coverage": "VERIFIED",
        "what": "Potvrđuje email postojećeg naloga jednokratnim linkom, bez stvaranja sesije.",
        "when": "Kada je potrebna potvrda emaila ili novi link za potvrdu.",
        "roles_permissions": "Zahtev se šalje bez prijave; odgovor ne otkriva da li nalog postoji ili je već potvrđen.",
        "steps": "1) Na prijavi otvorite Oporavak naloga i Potvrda emaila. 2) Unesite email i pošaljite zahtev. 3) Otvorite najnoviji primljeni link. 4) Eksplicitno kliknite Potvrdi email. 5) Vratite se na prijavu.",
        "fields_statuses": "Zahtev je neutralan; nije potvrda isporuke. Jednokratni link ima rok i troši se uspešnom potvrdom. Potvrđen email nije product entitlement.",
        "example": "Posle uspešne potvrde korisnik i dalje sam unosi email i lozinku na prijavi.",
        "non_goals": "Potvrda ne kreira nalog, novu sesiju, članstvo ili administratorska prava.",
        "errors_recovery": "Za istekao ili već iskorišćen link zatražite novi. Ako poruka ne stiže, proverite sanduče/neželjenu poštu i obratite se administratoru bez linka. Aktivnu sesiju prvo odjavite i ponovo otvorite originalni link.",
        "limitations": "Isti odgovor važi za nepoznat, potvrđen ili nepotvrđen nalog. Link je tajan; ne prilažite ga screenshot-u. Produkcioni SMTP nije ovde verifikovan.",
        "provenance_review": "Backend čuva verifikaciono stanje i jednokratnost; korisnik proverava da je otvorio očekivanu institucionalnu aplikaciju.",
    },
    {
        "id": "ISI-H05",
        "inventory_id": "INV-A05",
        "title": "Oporavak lozinke",
        "coverage": "VERIFIED",
        "what": "Traži i potvrđuje promenu lozinke preko postojećeg jednokratnog reset toka.",
        "when": "Kada ste zaboravili lozinku ili treba bezbedno obnoviti pristup.",
        "roles_permissions": "Zahtev po emailu je dostupan bez prijave; potvrda zahteva važeći jednokratni link. Odgovor ne otkriva postojanje naloga.",
        "steps": "1) Otvorite Oporavak naloga na prijavi. 2) U Promena lozinke unesite email i pošaljite zahtev. 3) Otvorite najnoviji primljeni link. 4) Unesite Novu lozinku i potvrdu. 5) Sačuvajte i prijavite se novom lozinkom.",
        "fields_statuses": "Oba unosa moraju biti jednaka. Backend proverava politiku (12–256 znakova), rok i jednokratnost linka. Uspešan reset opoziva postojeće sesije; nije automatska prijava.",
        "example": "Posle resetovanja na jednom uređaju druga postojeća sesija više ne autorizuje API pozive.",
        "non_goals": "Reset ne kreira korisnika, ne menja role i ne prikazuje privremenu ili staru lozinku.",
        "errors_recovery": "Ispravite nejednake unose. Za nevažeći/istekao link zatražite novi; za nedostupnu uslugu pokušajte kasnije. Ako je odgovor izgubljen nakon slanja, pokušajte prijavu novom lozinkom ili zatražite novi link. Aktivnu sesiju prvo odjavite.",
        "limitations": "Ne delite link ni lozinku. Neutralan odgovor ne garantuje isporuku. SMTP ostaje pending po odluci vlasnika.",
        "provenance_review": "Backend troši token, primenjuje password policy, opoziv sesija i bezbednosni audit; Help i klijent ne menjaju tu semantiku.",
    },
    {
        "id": "ISI-H06",
        "inventory_id": "INV-A06",
        "title": "Organizacija, platforma i workspace",
        "coverage": "VERIFIED",
        "what": "Zajednički shell bira dozvoljeni organizacioni, SIMPA/ORDO i workspace kontekst.",
        "when": "Pre svakog rada i nakon promene organizacije, proizvoda ili dodeljenih prava.",
        "roles_permissions": "Organization -> Membership -> Role/Permission -> Product entitlement -> Workspace određuju pristup. Vidljivost u UI nije autorizacija; backend je autoritet.",
        "steps": "1) Proverite organizaciju u bočnoj traci. 2) Izaberite SIMPA ili ORDO ako su oba dostupna. 3) Izaberite workspace. 4) Otvorite dozvoljeni modul. 5) ISI Help je zajednička Pomoć, a SIMPA Help i ORDO Help ostaju zasebni.",
        "fields_statuses": "Jedna dostupna opcija bira se automatski; više opcija daje izbor. Bez workspace-a domenski rad nije dostupan. Bez pristupa proizvodu prikazuje se no-access stanje, uz Help i bezbednost naloga.",
        "example": "Analitičar menja SIMPA u ORDO samo ako mu je ORDO dodeljen; prethodni workspace nije dozvola za drugi proizvod.",
        "non_goals": "Shell ne dodeljuje prava, ne spaja tenant podatke i ne prenosi metodologiju između proizvoda.",
        "errors_recovery": "Proverite aktivni izbor; za nedodeljen pristup kontaktirajte administratora. Posle promene prava odjavite se i prijavite ponovo radi osvežavanja konteksta. Istekla sesija zahteva novu prijavu.",
        "limitations": "Help je statičan i ne potvrđuje da imate dozvolu za opisanu akciju. Backend ponovo proverava scope svakog zahteva.",
        "provenance_review": "App-context/app-shell i RBAC čine autoritet; proverite kontekst pre izvoza ili mutacije. Institucionalne odluke i human accountability ostaju ljudski.",
    },
    {
        "id": "ISI-H07",
        "inventory_id": "INV-A08",
        "title": "Podaci i poreklo",
        "coverage": "VERIFIED",
        "what": "Data prikazuje izvore/verzije i ingestion stanje, prima upload i prikazuje analitičke registre, lineage i AI/RAG eligibility.",
        "when": "Pre analitike, pri proveri kvaliteta i kada treba razumeti zašto artefakt nije podoban.",
        "roles_permissions": "data.read za katalog, kontrolisani pregled i eligibility; data.upload za upload; data.governance.manage za dozvoljene obrasce upravljanja. Server pri svakoj radnji ponovo proverava organizaciju, proizvod i radni prostor.",
        "steps": "1) Izaberite workspace i Podaci. 2) Proverite katalog. 3) Sa data.upload unesite naziv, izaberite CSV/JSON/XLSX/PDF/DOCX/TXT i Učitaj i proveri. 4) U pripremi ugovora pregledajte konektor, mapiranje, identitet i operativnu politiku; registraciju i aktiviranje zasebno potvrdite. 5) Pregledajte Analytical datasets i Feature registry i njihove ugovore/životni ciklus. 6) Izaberite Snapshot for lineage. 7) U AI / RAG eligibility izaberite artefakt i akciju, pa Evaluate deterministic eligibility.",
        "fields_statuses": "uploaded/queued/running/succeeded/failed opisuju tehničku obradu, ne metodološku validaciju. Verzija, fingerprint, state, classification, privacy, AI policy i invalidation su odvojeni. Eligibility prikazuje allowed, reason_code, separate approval i human review. Missing nije nula.",
        "example": "Uspešan CSV upload može biti tehnički obrađen, a ipak nije VALIDATED/FROZEN analitički snapshot dozvoljen za SIMPA/ORDO.",
        "non_goals": "Eligibility proverava podobnost, ne izvršava model. Odvojeni obrasci upravljaju konektorom, mapiranjem, ugovorima i izvorima prema dozvolama. Zahtev za purge ne izvršava fizičko brisanje; to ostaje zaseban operator postupak.",
        "errors_recovery": "Za prazan naziv ili datoteku ispravite unos. Za odbijen format, veličinu ili neuspešnu obradu proverite izvor sa administratorom podataka. Ako artefakt nije podoban, ovlašćeni korisnik završava pregled ugovora, kvaliteta i životnog ciklusa u odgovarajućim obrascima. Posle prekida prvo osvežite status; ne zaobilazite proveru sirovim uploadom.",
        "limitations": "Upload nije pravni osnov obrade. Poštujte klasifikaciju, privatnost, retention i AI policy; osetljivi SIMPA ostaje local-only. Legacy source-version lineage je čitljiva istorija, ne dozvola za nov governed rad.",
        "provenance_review": "Proverite dataset contract, governed output/run/evaluation i source fingerprints, temporal/granularity keys, quality i dependent features. Čovek proverava poreklo i podobnost pre downstream upotrebe.",
    },
    {
        "id": "ISI-H08",
        "inventory_id": "INV-A14",
        "title": "Izveštaji, pregled i izvoz",
        "coverage": "VERIFIED",
        "what": "Reporting pravi nepromenljive verzije iz postojećih domain snapshot-a, vodi review/publication i deterministički izvoz.",
        "when": "Kada treba sačuvati, pregledati i podeliti autorizovani rezultat sa jasnim poreklom.",
        "roles_permissions": "report.read čita izvore/izveštaje i izvozi; analysis.run kreira verzije i šalje na review; organization.manage odobrava/odbija i publikuje. Backend proverava org/product/workspace.",
        "steps": "1) Otvorite Izveštaji u workspace-u. 2) Eksplicitno izaberite Izvor i Naslov, pregledajte povezani dokaz gde je primenljiv, potvrdite i kreirajte draft. 3) U registru otvorite verziju, sadržaj i Provenance. 4) Pregledajte sadržaj i potvrdite slanje na review. 5) Ovlašćeni reviewer bira odluku, unosi napomenu, potvrđuje pregled i čuva odluku. 6) Odobrenu verziju zasebno potvrdite i eksplicitno publikujte. 7) Izaberite html/markdown/json, Pripremi download artefakt i Preuzmi artefakt.",
        "fields_statuses": "draft je nacrt; in_review čeka pregled; approved je odobren ali nije published; rejected je odbijen; superseded čuva raniju publikaciju. Izvoz je dostupan za approved/published/superseded. Content, provenance i export SHA-256 su različiti identiteti.",
        "example": "SIMPA monitoring_summary nastaje iz analytics_run; ORDO destination_snapshot iz analytics_run, a scenario_review iz scenario_assessment. Nova verzija koristi eksplicitno izabrani snapshot odgovarajućeg tipa; prvi ponuđeni izvor nije dokaz da je najnoviji.",
        "non_goals": "Reporting ne pokreće novu AI inferenciju, ne računa novu metodologiju i nema PDF renderer. Publikacija ne šalje automatski email niti znači javno objavljivanje na sajtu.",
        "errors_recovery": "Bez odgovarajućeg snapshot-a prvo završite domain workflow. Za neispravan scope/checksum ili neprihvaćen AI review rešite upstream dokaz; ne prepisujte istoriju. Odbijenu verziju zamenite novom i ponovite review.",
        "limitations": "Sadržaj ostaje tenant/product ograničen i deterministički dostupan bez aktivnog AI provajdera. Prethodni AI sadržaj zahteva postojeći ljudski review; izvoz nije metodološko odobrenje.",
        "provenance_review": "Proverite content_sha256, source_manifest_sha256, identitete izvora, review trag i export SHA-256 pre distribucije; čovek odgovara za tumačenje i deljenje.",
    },
    {
        "id": "ISI-H09",
        "inventory_id": "INV-A15",
        "title": "Administracija",
        "coverage": "VERIFIED",
        "what": "Administracija upravlja članovima, product access-om, rolama, pozivima, workspace-ima i nazivom organizacije uz audit.",
        "when": "Za odobrenu institucionalnu promenu pristupa ili proveru administrativnog traga.",
        "roles_permissions": "Backend capabilities određuju članstvo members.read/members.manage, workspace.manage, audit.read i organization.manage. Membership status i naziv zahtevaju organization-wide dozvolu; osetljive izmene mogu zahtevati potvrdu lozinke.",
        "steps": "1) Proverite organizaciju/proizvod. 2) Članovi: izaberite člana, membership status/product access ili dodelite/uklonite rolu i scope. 3) Pozivi: unesite email i početnu product rolu, kreirajte ili opozovite pending poziv. 4) Workspace-i: unesite naziv/slug, kreirajte, arhivirajte ili reaktivirajte. 5) Organizacija: ovlašćeno promenite naziv. 6) Audit: proverite trag.",
        "fields_statuses": "Membership active/suspended, product access active, role scope product/organization i entitlement su različiti slojevi. Pozivi imaju pending/accepted/revoked/expired stanje; workspace active/archived. Entitlement je read-only.",
        "example": "Dodela product role ne zamenjuje aktivan entitlement ili membership product access. Poziv ne može dodeliti organization_admin rolu.",
        "non_goals": "Organization admin nije platform superadmin; UI ne menja is_platform_admin, entitlement, slug/status organizacije ili audit zapise. Nema javnog tenant join-a.",
        "errors_recovery": "Za zabranu proverite scope i capability. Ako se traži step-up otvorite Bezbednost naloga i potvrdite lozinku. Za zaštitu poslednjeg administratora prvo obezbedite drugog ovlašćenog administratora. Za istekao poziv izdajte novi, bez deljenja tokena.",
        "limitations": "Ne pokušavajte zaobići last-admin zaštitu. Kreiranje poziva ne dokazuje produkcioni SMTP; razvojna isporuka nije produkciona. Unosite samo odobrene institucionalne podatke.",
        "provenance_review": "Uspešne mutacije imaju append-only admin audit trag; proverite aktera, akciju i scope. Administrator je odgovoran za najmanji potreban pristup.",
    },
    {
        "id": "ISI-H10",
        "inventory_id": "INV-A16",
        "title": "Bezbednost naloga",
        "coverage": "VERIFIED",
        "what": "Prikazuje sopstvene sesije, opoziva druge sesije i osvežava potvrdu identiteta lozinkom.",
        "when": "Pre privilegovanog rada ili ako uređaj više ne treba da ima pristup.",
        "roles_permissions": "Samo sopstveni nalog sa važećom sesijom; step-up ne daje nove role. Stvarni MFA provajder još nije verifikovan.",
        "steps": "1) Otvorite Bezbednost naloga. 2) Za step-up unesite Trenutnu lozinku i Potvrdi identitet. 3) Pregledajte sesije. 4) Potvrdite opoziv izabrane druge aktivne sesije pa Opozovi sesiju, ili zasebno potvrdite sve druge sesije pa Opozovi sve druge sesije. Pregledajte potvrdu i nov status. 5) Za trenutnu sesiju koristite Odjavi se.",
        "fields_statuses": "Opis uređaja je ograničen; created_at, last_seen_at, expires_at, opozvana/aktivna i trenutna sesija opisuju različite činjenice. Neopozvana sesija može biti istekla; backend proverava rok i idle timeout.",
        "example": "Sa sadašnjeg uređaja opozovite raniju sesiju izgubljenog uređaja bez prikazivanja pune mrežne adrese ili user-agent-a.",
        "non_goals": "Ekran ne upravlja tuđim sesijama, ne prikazuje tokene i nije aktivacija produkcionog MFA.",
        "errors_recovery": "Ako lozinka nije potvrđena, proverite unos ili koristite oporavak nakon odjave. Za isteklu sesiju prijavite se ponovo; kod izgubljenog odgovora proverite ponovo listu pre ponavljanja opoziva.",
        "limitations": "Ne delite lozinku ili opis privatnih sesija. UI oznaka aktivna ne zaobilazi backend expiry/revocation. MFA provider integration ostaje odložen; SMTP je pending po odluci vlasnika; završni server dokaz novih tokova vodi se zasebno.",
        "provenance_review": "Backend AuthSession i bezbednosni događaji su autoritet; opoziv i password assurance ostaju auditable, bez beleženja sirovih tajni u Help-u.",
    },
    {
        "id": "ISI-H11",
        "inventory_id": "INV-A17",
        "title": "Pristup samo po pozivu",
        "coverage": "VERIFIED",
        "what": "Institucionalni pristup je invitation-only; javna samoregistracija nije prisutna (NOT_PRESENT).",
        "when": "Kada želite institucionalni pristup, ali nemate nalog ili odobreno članstvo.",
        "roles_permissions": "Ovlašćeni administrator upravlja pozivima i pristupom. Posetilac ne može sam kreirati tenant, članstvo ili rolu.",
        "steps": "1) Obratite se administratoru institucije. 2) Sačekajte odobreni poziv. 3) Pratite ISI-H03. 4) Proverite dodeljeni pristup posle prihvatanja.",
        "fields_statuses": "NOT_PRESENT je runtime status javne registracije. VERIFIED ovde potvrđuje dokumentovano i testirano odsustvo, a ne postojanje signup funkcije.",
        "example": "Posetilac bez poziva može pročitati javnu Pomoć, ali ne može otvoriti privatni workspace.",
        "non_goals": "Nema signup/register forme, javnog kreiranja naloga, kupovine pristupa ili anonimnog pridruživanja organizaciji.",
        "errors_recovery": "Ako očekujete poziv, proverite sa administratorom odobrenje i adresu. Reset ili email-verification zahtev ne kreira novi nalog.",
        "limitations": "Za nepostojeću signup akciju polja, tokeni i numerički model nisu primenljivi: NOT_APPLICABLE jer akcija ne postoji. Ne koristite tuđi poziv.",
        "provenance_review": "Javna samoregistracija nije dostupna. Poziv i odobrenje ovlašćenog administratora ostaju obavezni; čitanje javne pomoći ne dodeljuje pristup.",
    },
    {
        "id": "ISI-H12",
        "inventory_id": "INV-A21",
        "title": "Kako koristiti zajedničku Pomoć",
        "coverage": "VERIFIED",
        "what": "Povezuje osnovne zajedničke teme sa detaljnim korisničkim tokovima, objašnjenjima polja i datiranim ilustracijama. SIMPA i ORDO imaju zasebnu pomoć za svoje metodologije.",
        "when": "Pre nepoznate akcije, pri grešci ili proveri granica podržanog ponašanja.",
        "roles_permissions": "Javna Pomoć prikazuje samo H01–H05 i H11. Prijavljena ISI Help navigacija prikazuje sve teme, bez pristupa tenant podacima i bez dodeljivanja prava.",
        "steps": "1) Otvorite ISI Help ili kontekstualnu Pomoć u Podaci/Izveštaji/Administracija/Bezbednost. 2) Izaberite osnovnu temu. 3) Za opširniji postupak izaberite Detaljan korisnički tok i pročitajte korake, polja, ilustracije i oporavak. 4) Za metodologiju otvorite SIMPA Help ili ORDO Help, gde je spisak ograničen na odgovarajući proizvod. 5) Proverite datum ilustracije i stvarni status svog izvora pre rada.",
        "fields_statuses": "Tema pomoći otvara sažeto uputstvo; Detaljan korisnički tok otvara prošireno poglavlje. Ilustracije označavaju datum i da li prikazuju sintetički primer ili ranije pregledan server. Primer ne potvrđuje stanje vašeg naloga, podataka ili metodologije.",
        "example": "Pre izvoza otvorite H08; pre tumačenja forecast-a koristite ORDO-H10, bez prepisivanja njegove metodologije u shared Help.",
        "non_goals": "Help nije pravni savet, metodološko odobrenje ili automatska institucionalna odluka; ne uvodi novi model ili domen.",
        "errors_recovery": "Ako UI i Help odstupaju, zaustavite pogođenu akciju i prijavite nesenzitivan opis uz temu i verziju aplikacije, bez lozinki, linkova ili privatnih podataka.",
        "limitations": "Pomoć ne računa analitičke rezultate i ne potvrđuje tačnost AI nalaza. Raspoloživost radnje zavisi od objavljene aplikacije, vašeg konteksta i dozvola; datirani ekrani mogu sadržati ranije nazive menija.",
        "provenance_review": "Uputstvo se usaglašava sa pregledanom implementacijom. Za stručne zaključke proverite originalne izvore, verziju metodologije i sačuvani rezultat. Ljudski pregled podataka i odobrenje institucionalne upotrebe ostaju zasebne odgovornosti.",
    },
)
PUBLIC_HELP_TOPIC_IDS = ("ISI-H01", "ISI-H02", "ISI-H03", "ISI-H04", "ISI-H05", "ISI-H11")


def shared_help_topic(topic_id: str) -> dict[str, str]:
    return next(topic for topic in SHARED_HELP_TOPICS if topic["id"] == topic_id)


def _render_topic(topic: dict[str, str], *, public: bool = False) -> None:
    from src.streamlit_app.help_manual import render_topic

    render_topic(topic, public=public)


def render_shared_help(*, public: bool = False) -> None:
    """Public mode is an explicit allowlist, independent of auth/context state."""
    st.title("ISI Help · Pomoć")
    st.caption("Institucionalni pristup je isključivo po pozivu; nema javne registracije.")
    topics = [topic for topic in SHARED_HELP_TOPICS if not public or topic["id"] in PUBLIC_HELP_TOPIC_IDS]
    selected = st.selectbox(
        "Tema pomoći",
        [topic["id"] for topic in topics],
        format_func=lambda value: f"{value} · {shared_help_topic(value)['title']}",
        key="isi_public_help_topic" if public else "isi_shared_help_topic",
    )
    _render_topic(next(topic for topic in topics if topic["id"] == selected), public=public)
    if not public:
        from src.streamlit_app.help_manual import chapters, render_chapter

        extra = {key: value for key, value in chapters("SIMPA").items() if "ORDO" in value["products"]}
        detailed = st.selectbox(
            "Detaljan korisnički tok",
            list(extra),
            index=None,
            format_func=lambda key: extra[key]["title"],
            key="isi_shared_workflow",
        )
        if detailed is not None:
            render_chapter(detailed, product="SIMPA")


def render_topic_summary(topic_id: str) -> None:
    """A compact entry point with full guidance available without API calls."""
    topic = shared_help_topic(topic_id)
    with st.expander(f"Pomoć · {topic['title']} · {topic_id}"):
        _render_topic(topic)
