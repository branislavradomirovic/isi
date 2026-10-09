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

SIMPA_HELP_TOPICS = (
    {
        "id": "SIMPA-H01",
        "title": "Pristup i workspace kontekst",
        "coverage": "VERIFIED",
        "what": "Objasnjava kako organizacija, SIMPA product entitlement, workspace i dozvole odredjuju sta korisnik vidi i sme da uradi.",
        "when": "Koristite pre svakog SIMPA rada i kada ekran ili akcija nisu dostupni.",
        "roles_permissions": "Backend je autoritet. Vidljivost u UI nije dozvola. Konkretne akcije zahtevaju odgovarajuce permission kodove, npr. indicator.read, analysis.read, analysis.run ili workspace.manage.",
        "steps": "1) Prijavite se institucionalnim nalogom. 2) Izaberite organizaciju. 3) Izaberite SIMPA. 4) Izaberite workspace. 5) Otvorite dozvoljeni modul.",
        "fields_statuses": "Organizacija, platforma, workspace, role_codes i permission_codes predstavljaju aktivni autorizacioni kontekst.",
        "example": "Korisnik sa analysis.read moze pregledati SIMPA analitiku, ali bez analysis.run ne moze pokrenuti monitoring snapshot ili statisticko izvrsenje.",
        "non_goals": "UI ne dodeljuje prava, ne zaobilazi backend RBAC i ne stvara javnu samoregistraciju.",
        "errors_recovery": "Ako workspace nije izabran ili pristup nije dodeljen, izaberite dozvoljeni kontekst ili zatrazite od administratora odgovarajuci entitlement/rolu; ne pokusavajte zaobilazenje API kontrole.",
        "limitations": "Pristup je organizaciono, product i workspace ogranicen; osetljivi podaci se ne smeju kopirati izvan dozvoljenog scope-a.",
        "provenance_review": "Backend app-context/app-shell i RBAC odluke su autoritet. Human accountability ostaje obavezna za institucionalne odluke.",
    },
    {
        "id": "SIMPA-H02",
        "title": "Profil lokalnog sistema i lokalni akteri",
        "coverage": "VERIFIED",
        "what": "Prikazuje i, kada je dozvoljeno, konfigurise profil lokalnog sistema i registar lokalnih aktera.",
        "when": "Koristite za uspostavljanje osnovnog institucionalnog konteksta SIMPA workspace-a.",
        "roles_permissions": "Pregled je vezan za SIMPA workspace; izmene profila/aktera u UI zahtevaju workspace.manage.",
        "steps": "1) Otvorite SIMPA Pregled. 2) Proverite profil i aktere. 3) Ako imate workspace.manage, otvorite konfiguraciju. 4) Unesite stvarne institucionalne podatke. 5) Sacuvajte.",
        "fields_statuses": "Naziv lokalnog sistema je obavezan; sifra je opciona; referentna godina i napomena opisuju kontekst. Tip aktera je kontrolisana kategorija.",
        "example": "Profil moze evidentirati naziv JLS i referentnu godinu bez dodavanja bilo kakve statistike o gradjanima.",
        "non_goals": "Ovaj ekran ne generise demo statistiku, rizik gradjana, podobnost za uslugu ili metodologiju indikatora.",
        "errors_recovery": "Prazan obavezan naziv se odbija. Ispravite unos ili proverite permission/workspace kontekst.",
        "limitations": "Unosite samo podatke dozvoljene politikom organizacije; profil nije analiticki rezultat.",
        "provenance_review": "Vrednosti poticu iz aktivnog SIMPA workspace-a; organizacija je odgovorna za tacnost konfiguracije.",
    },
    {
        "id": "SIMPA-H03",
        "title": "Monitoring ciklusi",
        "coverage": "VERIFIED",
        "what": "Evidentira vremenski okvir i status monitoring ciklusa koji se koristi za organizovanje SIMPA evidencije i analitike.",
        "when": "Koristite kada treba definisati ili pregledati period monitoringa lokalnog sistema.",
        "roles_permissions": "Pregled je workspace-scoped; kreiranje ciklusa u UI zahteva indicator.manage.",
        "steps": "1) Otvorite SIMPA Pregled. 2) Proverite postojece cikluse. 3) Sa indicator.manage otvorite Novi monitoring ciklus. 4) Unesite kod, naziv, pocetak, kraj i status. 5) Kreirajte ciklus.",
        "fields_statuses": "Statusi su planned, open i closed. Kraj perioda ne moze biti pre pocetka.",
        "example": "Ciklus 2026-H1 moze pokriti 1. januar do 30. jun 2026. bez ikakvog automatskog zakljucka o uspehu politike.",
        "non_goals": "Status ciklusa nije ocena ucinka, rizika ili kvaliteta usluge.",
        "errors_recovery": "Kod/naziv su obavezni; neispravan datum se odbija. Ispravite period i ponovite bez menjanja istorijskih rezultata.",
        "limitations": "Vremenski okvir mora odgovarati odobrenoj metodologiji i dostupnim izvorima.",
        "provenance_review": "Ciklus je deo workspace konteksta i mora se poklapati sa analitickim run-om kada se koristi u racunanju.",
    },
    {
        "id": "SIMPA-H04",
        "title": "Indikatori i opservacije",
        "coverage": "VERIFIED",
        "what": "Prikazuje konceptualni/aktivni SIMPA indicator registry i evidentirane opservacije sa metodoloskim statusom i provenance-ready podacima.",
        "when": "Koristite za pregled dostupnih indikatora, oblasti i opservacija pre analitike.",
        "roles_permissions": "Pristup indikatorima zahteva SIMPA indicator.read kroz autorizovani workspace.",
        "steps": "1) Otvorite Indikatori. 2) Filtrirajte oblast. 3) Procitajte naziv, jedinicu i metodoloski status. 4) Pregledajte evidentirane opservacije i izvorni kontekst.",
        "fields_statuses": "Metodoloski status nije isto sto i vrednost indikatora. Nedostajuca jedinica ostaje eksplicitno nezakljucana; missing nije nula.",
        "example": "Konceptualni indikator moze biti vidljiv u registru, ali bez VALIDATED metodologije ne postaje production calculation.",
        "non_goals": "Naziv indikatora ne autorizuje formulu, LISI tezinu, prag, risk band ili automatski policy zakljucak.",
        "errors_recovery": "Ako nema opservacija, prvo obezbedite dozvoljen izvor i governed ingestion; sistem namerno ne generise vrednosti.",
        "limitations": "Tumačenje je ograniceno statusom metodologije, kvalitetom izvora i odobrenim agregatnim scope-om.",
        "provenance_review": "Produkcioni rezultati moraju cuvati metodologiju i governed provenance; ljudska validacija ostaje odvojena od samog prikaza registra.",
    },
    {
        "id": "SIMPA-H05",
        "title": "Governed analiticki artefakt",
        "coverage": "VERIFIED",
        "what": "Bira VALIDATED/FROZEN analytical snapshot ili eligible governed feature verziju kao jedini dozvoljeni ulaz u SIMPA analitiku.",
        "when": "Koristite pre pregleda evidence-quality snapshot-a, cuvanja monitoring snapshot-a ili statistickog izvrsenja.",
        "roles_permissions": "Pregled analitike zahteva analysis.read; downstream izvrsenje zahteva analysis.run.",
        "steps": "1) Otvorite Analitika. 2) Izaberite eligible artefakt. 3) Proverite fingerprint i quality state. 4) Pregledajte evidence metrics pre bilo kog modela.",
        "fields_statuses": "Eligible snapshot mora biti VALIDATED/FROZEN i neinvalidiran; feature verzija mora biti GOVERNED/FROZEN, neinvalidirana i vezana za jedan eligible snapshot.",
        "example": "Validated snapshot sa stabilnim fingerprintom moze biti ulaz; raw upload ili invalidated snapshot ne moze.",
        "non_goals": "SIMPA analitika ne sme direktno zaobici governed analytical boundary i citati sirove source bytes.",
        "errors_recovery": "Ako nema eligible artefakta, vratite se u data governance tok i validirajte/freeze-ujte dozvoljeni analytical artifact; ne simulirajte podatke.",
        "limitations": "Eligibility artefakta ne znaci da je metodologija indikatora ili statisticki model VALIDATED.",
        "provenance_review": "Artifact, dataset-contract i input fingerprints omogucavaju reproduktivnost i moraju ostati vidljivi u rezultatu.",
    },
    {
        "id": "SIMPA-H06",
        "title": "Zivotni ciklus metodologije",
        "coverage": "VERIFIED",
        "what": "Objasnjava DRAFT -> PROPOSED -> VALIDATED -> RETIRED lifecycle metodologije indikatora.",
        "when": "Koristite pri citanju metodoloskog statusa i pre odluke da li rezultat sme u production calculation.",
        "roles_permissions": "Pregled zahteva analysis.read. Lifecycle mutacije zahtevaju indicator.manage kroz kontrolisani autorizovani workflow/API; analytics ekran ih trenutno prikazuje kao evidence state.",
        "steps": "1) Pronadjite metodologiju. 2) Proverite version i fingerprint. 3) Proverite lifecycle. 4) Za VALIDATED proverite reference evidence i human approval. 5) RETIRED koristite samo za istorijsku reprodukciju.",
        "fields_statuses": "DRAFT=authoring/test; PROPOSED=controlled testing; VALIDATED=human-approved nakon potrebnog deterministic reference gate-a; RETIRED=istorijski reproduktivan, nije za nova production racunanja.",
        "example": "PROPOSED metodologija sa passed reference suite-om i dalje nije VALIDATED dok autorizovani covek ne izvrsi odobrenje.",
        "non_goals": "Implementacija ili AI-generisan tekst ne validiraju metodologiju sami po sebi.",
        "errors_recovery": "Ako transition nije dozvoljen ili reference gate nedostaje, ne zaobilazite lifecycle; obezbedite zahtevani evidence/human approval.",
        "limitations": "VALIDATED je metodolosko odobrenje, ne dokaz kauzalnosti niti automatska potvrda svake buduce upotrebe.",
        "provenance_review": "Version, contract fingerprint, reference evidence, approver i timestamps cuvaju metodoloski trag.",
    },
    {
        "id": "SIMPA-H07",
        "title": "Referentni suite i PASS",
        "coverage": "VERIFIED",
        "what": "Prikazuje verzionirani reference suite/cases i deterministic PASS/FAIL dokaz da implementirani calculator reprodukuje ocekivani referentni rezultat.",
        "when": "Koristite pri metodoloskom review-u pre human VALIDATED transition-a.",
        "roles_permissions": "Pregled zahteva analysis.read; kreiranje/izvrsenje reference evidence-a pripada indicator.manage kontrolisanom workflow-u.",
        "steps": "1) Proverite suite version/dataset version. 2) Proverite case fingerprints. 3) Proverite result fingerprint. 4) Proverite PASS. 5) Odvojeno proverite human VALIDATED state.",
        "fields_statuses": "PASS znaci deterministic reference evidence. PASS nije institucionalna validacija i ne menja PROPOSED u VALIDATED automatski.",
        "example": "Svi reference cases mogu biti passed, dok metodologija i dalje ostaje PROPOSED do ljudskog odobrenja.",
        "non_goals": "Reference suite ne autorizuje LISI formulu, tezine, pragove ili druge metodologije koje nisu u njegovom contract-u.",
        "errors_recovery": "Failed/invalid evidence zahteva ispravku metodologije ili reference evidence-a i novo kontrolisano izvrsenje; ne editujte istorijski rezultat.",
        "limitations": "Reference suite proverava definisani calculator/fixture, ne celokupnu eksternu validnost ili kauzalni efekat.",
        "provenance_review": "Suite/case/result fingerprints, dataset version i execution metadata su autoritet za reproduktivnost; human review ostaje odvojen.",
    },
    {
        "id": "SIMPA-H08",
        "title": "Monitoring snapshot",
        "coverage": "VERIFIED",
        "what": "Cuvanje nepromenljivog SIMPA monitoring snapshot-a evidence-quality stanja za izabrani governed analytical artifact.",
        "when": "Koristite kada zelite reproduktivan evidence-quality checkpoint pre modela ili AI sinteze.",
        "roles_permissions": "Pregled zahteva analysis.read; dugme za cuvanje zahteva analysis.run.",
        "steps": "1) Izaberite eligible artefakt. 2) Proverite evidence metrics. 3) Kliknite Sacuvaj trenutni monitoring snapshot. 4) Proverite run ID i artifact fingerprint.",
        "fields_statuses": "Snapshot prikazuje evidence_quality_score/band, validated observation ratio, provenance coverage i indicator coverage; to nisu socijalni risk score-ovi.",
        "example": "Snapshot moze zabeleziti 100% provenance coverage bez tvrdnje da je lokalna politika uspesna.",
        "non_goals": "Monitoring snapshot nije prognoza, citizen score, policy evaluation niti automatski zakljucak.",
        "errors_recovery": "Ako artefakt vise nije eligible, ponovo validirajte governance state i kreirajte novi run; ne menjajte stari fingerprint.",
        "limitations": "Kvalitet evidence-a meri dostupnost/validaciju/provenance prema implementiranom contract-u, ne kvalitet zivota ili individualni rizik.",
        "provenance_review": "Run cuva exact analytical artifact/dataset fingerprints i koristi se kao reproduktivan downstream ulaz.",
    },
    {
        "id": "SIMPA-H09",
        "title": "Statisticki metodoloski ugovor",
        "coverage": "VERIFIED",
        "what": "Objasnjava immutable, versioned statistical contract vezan za exact VALIDATED target methodology fingerprint i model family izabranu po target semantici.",
        "when": "Koristite pre statistickog izvrsenja i pri review-u target/model/feature/covariance/missing-data specifikacije.",
        "roles_permissions": "Pregled zahteva analysis.read. Authoring/propose/validate/retire zahteva indicator.manage kroz kontrolisani API/workflow; ovaj ekran ih prikazuje, a izvrsava samo eligible contract-e.",
        "steps": "1) Proverite analysis_key. 2) Proverite target indicator/methodology fingerprint. 3) Proverite semantic-family pair. 4) Proverite features, confidence level, covariance i limitations. 5) Proverite lifecycle.",
        "fields_statuses": "continuous=OLS; count=Poisson GLM; binary_system_state=Binomial/Logit; proportion_rate=Fractional Logit. DRAFT nije executable; PROPOSED je controlled testing; VALIDATED je human-approved; RETIRED je istorijski.",
        "example": "Count target moze koristiti samo poisson_glm u v1; UI ne bira model po pogodnosti niti automatski prelazi na Negative Binomial.",
        "non_goals": "Contract v1 ne sadrzi formule/tezine/LISI, prediction threshold, predicted class, citizen scoring, causal design ili champion promotion.",
        "errors_recovery": "Ako se target methodology fingerprint promeni, stari contract fail-closed; kreirajte novu versioned specifikaciju umesto prevezivanja istorije.",
        "limitations": "VALIDATED contract je metodoloski odobren, ali nije ISI-25 champion/performance certification.",
        "provenance_review": "Contract ID/version/status/fingerprint i target methodology fingerprint moraju ostati vezani za svaki rezultat.",
    },
    {
        "id": "SIMPA-H10",
        "title": "Deterministicko statisticko izvrsenje",
        "coverage": "VERIFIED",
        "what": "Pokrece jedan od cetiri odobrena deterministicka aggregate model family contract-a nad governed monitoring run-om.",
        "when": "Koristite kada postoji PROPOSED contract za kontrolisano testiranje ili VALIDATED contract za production-eligible metodolosko izvrsenje.",
        "roles_permissions": "Izvrsenje zahteva analysis.run; pregled contract-a/run-a zahteva analysis.read.",
        "steps": "1) Izaberite executable contract. 2) Izaberite governed monitoring snapshot. 3) Ako je PROPOSED, eksplicitno potvrdite controlled testing. 4) Pokrenite model. 5) Pregledajte immutable rezultat i XAI.",
        "fields_statuses": "PROPOSED bez controlled_testing_ack se odbija. VALIDATED moze dati production_eligible=true. Rezultat je jedinstven za isti run+contract i cuva result fingerprint.",
        "example": "PROPOSED OLS se moze pokrenuti samo uz checkbox potvrdu i rezultat ostaje production_eligible=false.",
        "non_goals": "Izvrsenje ne bira prag, klasu, policy action, citizen eligibility, causal conclusion niti AI narrative.",
        "errors_recovery": "Not estimable/rank deficiency/invalid target ili numerical failure se fail-closed. Ispravite governed input ili metodoloski contract; ne popunjavajte missing nulama.",
        "limitations": "V1 koristi complete-case, no scaling i aggregate-only contract; statisticka validnost zavisi od approved specification i human review-a.",
        "provenance_review": "Result trace cuva contract/methodology/artifact/dataset/input/result fingerprints, engine schema i statsmodels version.",
    },
    {
        "id": "SIMPA-H11",
        "title": "Statisticki rezultat i metodoloski XAI",
        "coverage": "VERIFIED",
        "what": 'Tumaci stored deterministic model result bez generativnog prepisivanja numericke istine: coefficients, standard errors, confidence intervals, model-produced p-values, metrics, diagnostics, calibration, missingness i provenance. 29A Graphical XAI dodaje grafikon uz izvornu tabelu; ne menja rezultat.',
        "when": 'Koristite pri citanju svakog OLS, Poisson GLM, Binomial/Logit ili Fractional Logit rezultata. Koristite grafikon za pregled sačuvanih rezultata pre institucionalnog zaključka.',
        "roles_permissions": 'Pregled zahteva analysis.read u istom SIMPA workspace-u. Pregled grafikona ima iste analysis.read i organization/product/workspace granice kao tabela.',
        "steps": '1) Proverite model identity/target semantic. 2) Procitajte coefficient scale. 3) Proverite estimate/SE/CI/p-value status. 4) Proverite sample+dropped. 5) Proverite metrics/diagnostics/calibration. 6) Proverite fingerprints/production_eligible. 7) Procitajte limitations/non-causal notice. Otvorite sačuvani rezultat; pročitajte skalu/legendu, uporedite grafikon sa tabelom i pregledajte provenance.',
        "fields_statuses": 'P-value je model-produced association inference samo kada postoji; legacy immutable rezultat moze imati unavailable_legacy_result. Calibration moze biti not_applicable. production_eligible znaci VALIDATED contract state, ne champion certification. Nedostajući interval je unavailable, zero ostaje zero; neispravan format daje bezbednu poruku. SHAP je pending 29D.',
        "example": 'Pozitivan Binomial/Logit coefficient znaci pozitivnu asocijaciju na log-odds skali aggregate system-state ishoda; nije procentni poen, decision threshold ili causal effect. Numerička nula (zero) prikazuje se kao stvarna tačka; NOT_ESTIMATED ne dobija zamensku nulu.',
        "non_goals": 'XAI ne izmisljava feature importance, generic confidence score, probability threshold, policy preporuku ili causal effect. 29A ne računa SHAP, GIS, nove modele, residual ili calibration tačke kojih nema u dokazu.',
        "errors_recovery": 'Ako p-value nedostaje u istorijskom immutable rezultatu, prikazuje se unavailable; ne rekonstruišite ga. Ako diagnostics/calibration nisu supported, prikazite stvarni stored status. Ako grafikon nije dostupan, pročitajte izvornu tabelu/JSON i proverite schema/version; ne popravljajte istorijski dokaz.',
        "limitations": 'P-values/CI zavise od model/covariance pretpostavki; v1 ne kodira multiplicity adjustment niti univerzalni diagnostic threshold. Prikaz: grafikon ima ograničen broj redova i oznaka, uz izričito obaveštenje; full table/source evidence ostaje dostupna. Postoji tabelarni fallback za mobile/keyboard.',
        "provenance_review": 'Exact contract, methodology, artifact, dataset, input i result fingerprints plus engine/statsmodels version omogucavaju review/reprodukciju. Grafikoni prikazuju samo persistirane vrednosti; contribution nije causality, a human review i result fingerprint ostaju obavezni.',
    },
    {
        "id": "SIMPA-H12",
        "title": "Lokalna AI sinteza i human review",
        "coverage": "VERIFIED",
        "what": "Pokrece bounded SIMPA AI sintezu evidence-quality snapshot-a kroz shared gateway i prikazuje provider/model/policy/prompt/provenance/failure/human-review stanje.",
        "when": "Koristite nakon deterministic evidence snapshot-a kada je potrebna pomoc u strukturisanom citanju evidence-quality stanja.",
        "roles_permissions": "Pokretanje i review u ovom UI zahtevaju analysis.run; sensitive SIMPA policy je local-only.",
        "steps": "1) Izaberite governed monitoring snapshot. 2) Pokrenite lokalnu sintezu. 3) Proverite source snapshot hash, provider/model/policy/prompt i structured-output state. 4) Procitajte limitations. 5) Prihvatite ili odbacite uz review note.",
        "fields_statuses": "Job status/error, provider/model, effective policy, prompt key/version, structured_output present/unavailable i review_status su odvojena stanja. Pending nije accepted.",
        "example": "AI moze sazeti da nedostaje evidence, ali ne sme izmisliti coefficient, score, threshold, source ili institucionalni zakljucak.",
        "non_goals": "23D ne uvodi model champion/promotion/eval/fallback governance niti povezuje statisticke rezultate u postojeci synthesis input; to ostaje ISI-25/shared AI scope.",
        "errors_recovery": "Provider/queue/structured-output failure ostaje eksplicitan; ponovite samo po odobrenom retry policy-ju i nikada ne zamenjujte failure izmisljenim odgovorom.",
        "limitations": "AI je pomocni evidence synthesis, nije numericki autoritet niti donosilac odluke. Osetljivi SIMPA podaci ostaju local-only prema aktuelnoj politici.",
        "provenance_review": "source_snapshot_sha256, request/provider/model/policy/prompt metadata i human_review_status moraju biti vidljivi; ljudski review je obavezan decision-support boundary.",
    },
)


def _topic(topic_id: str) -> dict[str, str]:
    return next(topic for topic in SIMPA_HELP_TOPICS if topic["id"] == topic_id)


def render_simpa_help(*, shell: dict[str, Any]) -> None:
    if shell.get("product", {}).get("code") != "SIMPA":
        st.info("SIMPA Help je dostupan samo u aktivnom SIMPA kontekstu.")
        return
    st.markdown('<div class="isi-eyebrow">SIMPA · Help / User Guide</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="isi-shell-title">SIMPA — detaljno uputstvo, metodologija i XAI</h1>', unsafe_allow_html=True)
    st.caption(
        "Izaberite temu za postupak korak po korak, objašnjenje polja, korisničke ekrane, primere i rešavanje problema."
    )
    from src.streamlit_app.help_manual import chapters, render_chapter, render_topic
    extra = chapters("SIMPA")
    selected = st.selectbox(
        "Help tema",
        [topic["id"] for topic in SIMPA_HELP_TOPICS] + list(extra),
        format_func=lambda value: extra[value]["title"] if value in extra else f"{value} · {_topic(value)['title']}",
        key="simpa_illustrated_help_topic",
    )
    if selected in extra:
        render_chapter(selected, product="SIMPA")
        return
    render_topic(_topic(selected))



__all__ = ["HELP_REQUIRED_FIELDS", "SIMPA_HELP_TOPICS", "render_simpa_help"]
