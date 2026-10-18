from __future__ import annotations

from typing import Any

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


ORDO_HELP_TOPICS = (
    {
        "id": "ORDO-H01",
        "title": "Pristup i workspace kontekst",
        "coverage": "VERIFIED",
        "what": "Objasnjava kako organizacija, ORDO entitlement, workspace i backend dozvole ogranicavaju svaki prikaz i postupak.",
        "when": "Koristite pre ORDO rada i kada modul, podatak ili akcija nisu dostupni.",
        "roles_permissions": "Backend je autoritet; UI vidljivost nije dozvola. Pregled tipicno zahteva indicator.read ili analysis.read, a izmene workspace.manage, indicator.manage ili analysis.run.",
        "steps": "1) Prijavite se. 2) Izaberite organizaciju. 3) Izaberite ORDO. 4) Izaberite workspace. 5) Otvorite samo dozvoljeni modul.",
        "fields_statuses": "Organization, product, workspace, role_codes i permission_codes cine aktivni autorizacioni scope.",
        "example": "Korisnik sa analysis.read moze citati sacuvani forecast, ali bez analysis.run ne moze kreirati analiticki snapshot ili scenario procenu.",
        "non_goals": "Help ne dodeljuje prava, ne zaobilazi RBAC i ne prosiruje pristup drugoj organizaciji ili SIMPA podacima.",
        "errors_recovery": "Ako kontekst nedostaje, izaberite dozvoljeni workspace ili trazite administratoru ispravnu rolu/entitlement; ne menjajte URL ili identifikatore radi zaobilazenja.",
        "limitations": "Svi podaci ostaju organization/product/workspace scoped; kopiranje izvan ovlascenog konteksta nije dozvoljeno.",
        "provenance_review": "App-context, app-shell i backend RBAC odluke su autoritet; ljudska odgovornost ostaje obavezna.",
    },
    {
        "id": "ORDO-H02",
        "title": "Profil destinacije, resursi i akteri",
        "coverage": "VERIFIED",
        "what": "Prikazuje i, kada je dozvoljeno, uredjuje profil destinacije, resurse i stakeholder registar.",
        "when": "Koristite za institucionalni kontekst destinacije pre monitoringa i analitike.",
        "roles_permissions": "Pregled je ORDO workspace-scoped; UI konfiguracija profila, resursa i aktera zahteva workspace.manage.",
        "steps": "1) Otvorite ORDO Pregled. 2) Proverite profil/resurse/aktere. 3) Sa workspace.manage otvorite konfiguraciju. 4) Unesite stvarne podatke. 5) Sacuvajte.",
        "fields_statuses": "Naziv destinacije/resursa/aktera je obavezan; tipovi su kontrolisane kategorije; referentna godina i lokacija opisuju kontekst.",
        "example": "Evidentirajte kulturno nasledje i upravljaca kao dva odvojena zapisa bez dodeljivanja ocene uspesnosti.",
        "non_goals": "Registar ne racuna vrednost resursa, rang destinacije, uticaj mere ili forecast.",
        "errors_recovery": "Prazan obavezni naziv se odbija; ispravite unos ili proverite scope/dozvolu, bez izmisljanja podataka.",
        "limitations": "Unosite samo dozvoljene institucionalne podatke; opis nije verifikovana analiticka tvrdnja.",
        "provenance_review": "Zapisi poticu iz aktivnog workspace-a; organizacija i ljudski reviewer odgovaraju za tacnost.",
    },
    {
        "id": "ORDO-H03",
        "title": "Monitoring ciklusi",
        "coverage": "VERIFIED",
        "what": "Evidentira period i lifecycle status ORDO monitoring ciklusa.",
        "when": "Koristite za organizovanje evidence-a i analitike po odobrenom vremenskom periodu.",
        "roles_permissions": "Pregled je workspace-scoped; kreiranje kroz UI zahteva indicator.manage.",
        "steps": "1) Otvorite Pregled. 2) Proverite cikluse. 3) Otvorite Novi monitoring ciklus. 4) Unesite kod, naziv, datume i status. 5) Kreirajte.",
        "fields_statuses": "Statusi planned/open/closed organizuju rad; datum kraja ne sme prethoditi pocetku.",
        "example": "Ciklus 2026-Q1 moze obuhvatiti januar-mart, ali closed ne znaci da je cilj ostvaren.",
        "non_goals": "Status ciklusa nije kvalitet dokaza, performans destinacije, prognoza ili policy odluka.",
        "errors_recovery": "Ispravite prazne kod/naziv ili neispravan period; ne prepravljajte istorijske analiticke rezultate.",
        "limitations": "Period mora odgovarati metodologiji i vremenskoj granularnosti stvarnih izvora.",
        "provenance_review": "Cycle ID i datumi moraju ostati povezani sa run-om gde su korisceni i biti predmet ljudskog review-a.",
    },
    {
        "id": "ORDO-H04",
        "title": "Indikatori, opservacije i metodoloski status",
        "coverage": "VERIFIED",
        "what": "Prikazuje ORDO indicator registry i provenance-ready opservacije sa odvojenim metodoloskim stanjem.",
        "when": "Koristite pre racunanja ili analitike da proverite oblast, jedinicu, status i dostupnu evidenciju.",
        "roles_permissions": "Pregled zahteva ORDO indicator.read u autorizovanom workspace-u.",
        "steps": "1) Otvorite Indikatori. 2) Filtrirajte oblast. 3) Procitajte stub, jedinicu i status metodologije. 4) Pregledajte opservacije/provenance.",
        "fields_statuses": "Conceptual nije validated; DRAFT/PROPOSED/VALIDATED/RETIRED su lifecycle stanja metodologije. Missing nije nula.",
        "example": "Konceptualni indikator moze biti vidljiv, ali bez VALIDATED metodologije ne autorizuje production calculation.",
        "non_goals": "Naziv indikatora ne definise formulu, tezinu, prag, ciljnu vrednost ili rang.",
        "errors_recovery": "Ako nema opservacija ili jedinice, obezbedite governed izvor/metodologiju; sistem namerno ne popunjava vrednosti.",
        "limitations": "Tumacenje zavisi od metodoloskog statusa, kvaliteta i vremensko-prostornog scope-a izvora.",
        "provenance_review": "Produkcioni rezultat mora vezati exact methodology version/fingerprint i governed evidence; VALIDATED zahteva human approval.",
    },
    {
        "id": "ORDO-H05",
        "title": "Governed artefakti i kvalitet dokaza",
        "coverage": "VERIFIED",
        "what": "Bira eligible analytical snapshot/feature i prikazuje evidence-quality coverage pre downstream rada.",
        "when": "Koristite pre cuvanja ORDO snapshot-a, scenario procene ili lokalne AI sinteze.",
        "roles_permissions": "Pregled zahteva analysis.read; cuvanje snapshot-a zahteva analysis.run.",
        "steps": "1) Otvorite Analitika. 2) Izaberite eligible artefakt. 3) Proverite fingerprint i quality state. 4) Procitajte coverage/missing evidence. 5) Po potrebi sacuvajte snapshot.",
        "fields_statuses": "VALIDATED/FROZEN snapshot ili GOVERNED/FROZEN single-snapshot feature mora biti neinvalidiran; evidence_quality nije destination-performance score.",
        "example": "Strong provenance coverage moze postojati i kada neke dimenzije nemaju dokaz; to nije dokaz uspesne politike.",
        "non_goals": "UI ne cita raw upload mimo governed boundary-ja i ne pretvara coverage u konkurentnost, odrzivost ili kvalitet zivota.",
        "errors_recovery": "Ako nema eligible artefakta, zavrsite data-governance validaciju/freeze; ne koristite legacy ili invalidated run.",
        "limitations": "Kvalitet dokaza meri implementiranu dostupnost/validaciju/provenance, ne istinitost svake institucionalne interpretacije.",
        "provenance_review": "Artifact, dataset-contract i snapshot fingerprints ostaju reproduktivni autoritet i zahtevaju ljudski pregled.",
    },
    {
        "id": "ORDO-H06",
        "title": "Metodoloski lifecycle i ljudsko odobrenje",
        "coverage": "VERIFIED",
        "what": "Omogucava review, authoring i DRAFT -> PROPOSED -> VALIDATED -> RETIRED lifecycle time-series specifikacije uz immutable verziju/fingerprint.",
        "when": "Koristite pre forecast izvrsenja da vezete stvarni governed run, ciljni indikator i ljudski odobrenu specifikaciju.",
        "roles_permissions": "analysis.read cita specifikacije; indicator.manage kreira, predlaze, validira i povlaci. Backend je autoritet za svaku mutaciju.",
        "steps": "1) Izaberite postojeci governed run. 2) Unesite customer-controlled time-series polja. 3) Kreirajte DRAFT; backend vezuje current VALIDATED metodologiju/fingerprint i locked semantics. 4) Predlozite. 5) Validirajte uz neblank note i evidence reference ili povucite VALIDATED uz retirement note.",
        "fields_statuses": "DRAFT=izrada; PROPOSED=kontrolisan review/test; VALIDATED=ljudski odobrena specifikacija uz actor/time/evidence; RETIRED=istorijska reprodukcija. Promena znacenja zahteva novu verziju/fingerprint.",
        "example": "Manager kreira mesecnu demand specifikaciju vezanu za governed run; reviewer validira plan i evidence, ali time ne promovise model niti garantuje buducu tacnost.",
        "non_goals": "Implementacija, Help ili AI tekst ne validiraju metodologiju i ne stvaraju novu formulu/model.",
        "errors_recovery": "Ako nema current VALIDATED metodologije ili run/binding/fingerprint vise ne odgovara, popravite governed evidence/metodologiju i kreirajte novu verziju; ne prevezujte istoriju.",
        "limitations": "Korisnik ne unosi methodology UUID/fingerprint ni locked booleans. VALIDATED je approval specifikacije, ne champion/model promotion, dokaz buduce performanse ili kauzalnosti.",
        "provenance_review": "Run, methodology ID/version/fingerprint, input SHA, contract/version/fingerprint, evidence reference, actor i timestamp moraju ostati vidljivi i pregledani.",
    },
    {
        "id": "ORDO-H07",
        "title": "Analiticki snapshot i provenance",
        "coverage": "VERIFIED",
        "what": "Cita/cuva immutable ORDO evidence snapshot vezan za exact governed analytical artifact.",
        "when": "Koristite za reproduktivan checkpoint pre scenarija, forecast prezentacije ili AI sinteze.",
        "roles_permissions": "analysis.read za pregled; analysis.run za cuvanje novog snapshot-a.",
        "steps": "1) Izaberite eligible artefakt. 2) Proverite metrics i missing dimenzije. 3) Sacuvajte snapshot ako imate dozvolu. 4) Proverite run/artifact/dataset fingerprints.",
        "fields_statuses": "Run status, quality/coverage metrics i analytical source identity su odvojena stanja; legacy run nije eligible za nov downstream rad.",
        "example": "Snapshot moze zabeleziti 80% dimension coverage bez zakljucka da je destinacija 80% uspesna.",
        "non_goals": "Snapshot nije forecast, scenario effect, rang, investiciona preporuka ili kauzalni rezultat.",
        "errors_recovery": "Promenjen/invalidiran binding fail-closed; napravite novi governed artefakt/run, ne menjajte stari fingerprint.",
        "limitations": "Rezultat odrazava samo zapise u exact snapshot-u i implementirani evidence contract.",
        "provenance_review": "Run ID, artifact/dataset fingerprints, quality state i normalized lineage su osnova reprodukcije i human review-a.",
    },
    {
        "id": "ORDO-H08",
        "title": "Razvojni ciljevi i scenariji",
        "coverage": "VERIFIED",
        "what": "Evidentira cilj i korisnicki napisane scenario pretpostavke/mere kao planning input.",
        "when": "Koristite za strukturisanje pravca koji ce se pregledati naspram raspolozivih dokaza.",
        "roles_permissions": "Pregled zahteva analysis.read; kreiranje cilja/scenarija zahteva analysis.run.",
        "steps": "1) Kreirajte cilj sa kodom/fokusom. 2) Izaberite cilj. 3) Unesite scenario, pretpostavke i mere. 4) Sacuvajte draft. 5) Pregledajte pre procene.",
        "fields_statuses": "Goal draft/active/closed i scenario draft/review_ready/accepted/rejected su workflow stanja, ne analiticki rezultat.",
        "example": "Pretpostavka 'nova linija prevoza' je planirana pretpostavka, ne dokaz da linija postoji ili da ce promeniti posetu.",
        "non_goals": "Scenario nije forecast i njegovo prihvatanje ne procenjuje uticaj, trosak ili verovatnocu uspeha.",
        "errors_recovery": "Ako cilj nedostaje ili unos nije dovoljan, dopunite stvarne planning podatke; ne predstavljajte pretpostavku kao evidence.",
        "limitations": "Regulatorna, finansijska, ekoloska i drustvena procena mora se uraditi van ovog evidence-only workflow-a gde je primenljivo.",
        "provenance_review": "Scenario ID, goal ID, autorovi unosi i lifecycle zahtevaju ljudski ownership/review.",
    },
    {
        "id": "ORDO-H09",
        "title": "Evidence-only scenario procena",
        "coverage": "VERIFIED",
        "what": "Uporedjuje scenario sa sacuvanim evidence snapshot-om i cuva eksplicitno neprocenjen uticaj bez forecast-a.",
        "when": "Koristite da identifikujete evidence readiness/missing dimenzije, ne da predvidite efekat mere.",
        "roles_permissions": "Pregled zahteva analysis.read; kreiranje evidence-only procene zahteva analysis.run.",
        "steps": "1) Izaberite scenario. 2) Izaberite eligible snapshot. 3) Kreirajte procenu. 4) Proverite forecast_performed=false. 5) Procitajte impact/reason/limitations/provenance.",
        "fields_statuses": "impact=NOT_ESTIMATED i NO_APPROVED_RESPONSE_MODEL znace namerno neprocenjen uticaj; LEGACY_NOT_EVALUATED ostaje istorijsko stanje; missing numeric ostaje missing.",
        "example": "Procena moze pokazati nedostajucu evidence dimenziju, ali ne sme reci da ce mera povecati indikator za 5%.",
        "non_goals": "Nema causal/predictive impact-a, intervala, confidence score-a, rangiranja ili policy preporuke.",
        "errors_recovery": "Ako je snapshot legacy/invalidiran, kreirajte novi governed run; ne prepisujte legacy stanje kao kasnije izvrsenje.",
        "limitations": "Pretpostavke nisu dokazi; bez posebno odobrenog response modela nema numerickog uticaja.",
        "provenance_review": "Scenario contract, methodology key/version, input SHA/reference identities i human-review state moraju ostati vidljivi.",
    },
    {
        "id": "ORDO-H10",
        "title": "Persistirani forecast, backtest i intervali",
        "coverage": "VERIFIED",
        "what": "Pokreće podržani model iz validirane specifikacije i prikazuje persistirani ESTIMATED ili NOT_ESTIMATED ishod sa intervalima, backtestom, dijagnostikom i fingerprints. Grafički XAI dodaje grafikon uz izvornu tabelu; ne menja rezultat.",
        "when": "Koristite kada postoji VALIDATED time-series specifikacija i backend je otkrio eligible identitet serije iz exact governed binding-a. Koristite grafikon za pregled sačuvanih rezultata pre institucionalnog zaključka.",
        "roles_permissions": "analysis.read cita specifikacije, identitete i rezultate; analysis.run izvrsava forecast. UI vidljivost ne zamenjuje backend autorizaciju. Pregled grafikona ima iste analysis.read i organization/product/workspace granice kao tabela.",
        "steps": "1) Izaberite human-readable VALIDATED spec. 2) Izaberite backend-discovered series identity. 3) Eksplicitno izaberite family iz candidate_families. 4) Izaberite 0.80/0.90/0.95 interval. 5) Pokrenite. 6) Pregledajte persistirani status/reason, points/intervals/backtest i provenance. Otvorite sačuvani rezultat; pročitajte skalu/legendu, uporedite grafikon sa tabelom i pregledajte provenance.",
        "fields_statuses": "ESTIMATED ima persisted points i intervals; NOT_ESTIMATED ima reason i nema zamenske tacke. Interval level/method nisu verovatnoca da je forecast tacan. Backtest je istorijska dijagnostika. Nedostajući interval je unavailable, zero ostaje zero; neispravan format daje bezbednu poruku. ORDO prognoze prikazuju sačuvane tačke i intervale; SHAP matrice pripadaju podržanom SIMPA numeričkom modelu i nisu objašnjenje ORDO prognoze ili LLM teksta.",
        "example": "Naive ESTIMATED run moze imati 90% configured empirical interval; to nije 90% generic confidence niti garancija buduce performanse. Numerička nula (zero) prikazuje se kao stvarna tačka; NOT_ESTIMATED ne dobija zamensku nulu.",
        "non_goals": "Nema rucnog spec UUID unosa, automatic model selection/fallback-a, feature importance-a, causal effect-a, ranga, generic confidence-a ili preporuke. Sam grafikon ne računa SHAP, GIS, nove modele, residual ili calibration tačke kojih nema u dokazu.",
        "errors_recovery": "Ako nema identity-ja, proverite indikator/validated quality/window/as-of evidence u exact binding-u. Za NOT_ESTIMATED procitajte stable reason i korigujte evidence ili novu spec verziju; nikada ne zamenjujte prazno nulom. Ako grafikon nije dostupan, pročitajte izvornu tabelu/JSON i proverite schema/version; ne popravljajte istorijski dokaz.",
        "limitations": "Samo naive/seasonal-naive mogu biti izvršene u ovom toku; rolling-origin rezultat ne dokazuje buducu performansu i dijagnostika nema izmisljen threshold. Prikaz: grafikon ima ograničen broj redova i oznaka, uz izričito obaveštenje; full table/source evidence ostaje dostupna. Tabelarni pregled je dostupan i za rad tastaturom.",
        "provenance_review": "Exact spec/methodology/input/request/result fingerprints, series identity, engine/version i human methodology approval omogucavaju reprodukciju/review. Grafikoni prikazuju samo persistirane vrednosti; contribution nije causality, a human review i result fingerprint ostaju obavezni.",
    },
    {
        "id": "ORDO-H11",
        "title": "Lokalna AI sinteza i human review",
        "coverage": "VERIFIED",
        "what": "Pokrece/prikazuje bounded local-only ORDO evidence synthesis sa provider/model/policy/prompt/provenance i review stanjem.",
        "when": "Koristite posle governed snapshot-a za pomocno citanje evidence-a ili scenario pitanja.",
        "roles_permissions": "Pregled zahteva analysis.read; pokretanje i accept/reject review zahtevaju analysis.run.",
        "steps": "1) Izaberite governed snapshot. 2) Izaberite monitoring/scenario_review. 3) Pokrenite sintezu. 4) Proverite source SHA, provider/model/policy/prompt i output/failure. 5) Prihvatite ili odbacite uz napomenu.",
        "fields_statuses": "Job status/error, provider/model, effective policy, prompt key/version, structured output i review_status su odvojena stanja; pending nije accepted.",
        "example": "AI moze navesti koje evidence nedostaje, ali ne sme izmisliti forecast, scenario impact, izvor ili institucionalnu odluku.",
        "non_goals": "Lokalna sinteza ne promoviše model, ne daje oznaku njegove stvarne pouzdanosti i ne menja politiku provider-a. Evaluacija i izbor modela su zaseban zajednički AI tok.",
        "errors_recovery": "Provider/queue/output failure ostaje vidljiv; ponovite samo po odobrenom policy-ju i ne zamenjujte failure izmisljenim tekstom.",
        "limitations": "AI nije numericki autoritet niti donosilac odluke; izlaz je evidence-bounded i local-only prema ORDO policy-ju.",
        "provenance_review": "source_snapshot_sha256, provider/model/policy/prompt, structured-output/failure i human_review_status moraju biti vidljivi; human review je obavezan.",
    },
    {
        "id": "ORDO-H12",
        "title": "Koriscenje Help-a i User Guide-a",
        "coverage": "VERIFIED",
        "what": "Povezuje dvanaest in-app tema sa repository ORDO User Guide-om i matricom pokrivenosti.",
        "when": "Koristite pre nepoznatog workflow-a, tumacenja statusa ili bezbednog oporavka od greske.",
        "roles_permissions": "ORDO Help je vidljiv samo u aktivnom ORDO kontekstu; Help ne menja backend permissions.",
        "steps": "1) U ORDO navigaciji otvorite ORDO Help. 2) Izaberite temu H01-H12. 3) Pratite korake/granice. 4) Za detalje koristite docs/help/ORDO-USER-GUIDE.md. 5) Ako runtime odstupa, prekinite i prijavite drift.",
        "fields_statuses": "Coverage VERIFIED znaci da je tema implementirana/testirana; globalna INV-A21 matrica ostaje PARTIAL dok shared povrsine nisu verifikovane.",
        "example": "Pre tumacenja NOT_ESTIMATED otvorite H09 ili H10 umesto da pretpostavite nulu ili failure.",
        "non_goals": "Help nije pravni savet, metodolosko odobrenje, automatski model selection niti zamena za obuku i ljudsku procenu.",
        "errors_recovery": "Ako Help i UI nisu uskladjeni, sacuvajte nesenzitivan opis, zaustavite odluku i prijavite governance drift; ne improvizujte.",
        "limitations": "Uputstvo opisuje postojeće funkcije; raspoloživost zavisi od objavljene verzije, dozvola i stvarnih ulaznih dokaza. Uputstvo ne potvrđuje institucionalnu metodologiju ili performanse modela.",
        "provenance_review": "Za proveru koristite oznaku teme, datum ilustracije i sačuvani rezultat sa poreklom. Izmene uputstva prolaze pregled uz proveru postojeće funkcije.",
    },
)


def _topic(topic_id: str) -> dict[str, str]:
    return next(topic for topic in ORDO_HELP_TOPICS if topic["id"] == topic_id)


def render_ordo_help(*, shell: dict[str, Any]) -> None:
    if shell.get("product", {}).get("code") != "ORDO":
        st.info("ORDO Help je dostupan samo u aktivnom ORDO kontekstu.")
        return
    st.markdown('<div class="isi-eyebrow">ORDO · Help / User Guide</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">ORDO — detaljno uputstvo, metodologija i XAI</h1>', unsafe_allow_html=True)
    st.caption(
        "Izaberite temu za postupak korak po korak, objašnjenje polja, korisničke ekrane, primere i rešavanje problema."
    )
    from src.streamlit_app.help_manual import chapters, render_chapter, render_topic, topic_label, workflow_selector

    extra = chapters("ORDO")
    topic_col, detail_col = st.columns(2)
    with topic_col:
        selected = st.selectbox(
            f"Kratke teme ({len(ORDO_HELP_TOPICS)} dostupno)",
            [topic["id"] for topic in ORDO_HELP_TOPICS],
            format_func=lambda value: topic_label(_topic(value)),
            key="ordo_illustrated_help_topic",
        )
    with detail_col:
        detailed = workflow_selector(extra, key="ordo_illustrated_help_workflow")
    if detailed is not None:
        render_chapter(detailed, product="ORDO")
    else:
        render_topic(_topic(selected))


__all__ = ["HELP_REQUIRED_FIELDS", "ORDO_HELP_TOPICS", "render_ordo_help"]
