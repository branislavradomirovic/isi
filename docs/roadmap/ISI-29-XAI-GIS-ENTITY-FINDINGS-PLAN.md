# ISI-29 — XAI, GIS i entiteti/nalazi sa dokazima

Datum: 2026-10-07. Status: **IN_PROGRESS / 29A prihvaćen na main; 29B lokalni kandidat; 29C–F planirani**.
Owner je zatražio proširenje plana i početak razvoja XAI/GIS i ekstrakcije entiteta/nalaza. „SIMA” u zahtevu odnosi se na postojeći SIMPA; nema trećeg proizvoda.
MasterPlan je kanonska nadređena vlast; ADR-0025 ostaje arhitekturna osnova.

## 1. Proverena početna tačka

- Lokalni main, lokalni origin/main i direktno provereni GitHub main: `374dda3db89f6fb87dde7f5b761642440da17bef`; tree `13051743a26f78a50f3a664518c643ff540bd9f9`.
- Početni index/worktree čisti, jedan worktree, prazan stash.
- [ISI required acceptance #96](https://github.com/branislavradomirovic/isi/actions/runs/37515814577): completed/success na tom SHA; svih 12 poslova success. Ova potvrda ne važi automatski za novi kandidat.
- Lokalni zapis `automation/evidence/ISI-28/checkpoint-96/closeout.json` potvrđuje prethodni deployment i ograničene live provere u PREPRODUCTION_TESTING. Nije izvršena nova server provera za ovaj plan. SMTP pending; novi backupi owner-deferred; puna produkcija nije potvrđena.
- Pročitani MasterPlan, AGENTS, task/status ledgers, ADR-0025, ISI-24A GIS ugovor, ISI-28 R3 i release/development ops ugovori; pregledani stvarni modeli, ingestion/governance, AI, XAI, Streamlit, spatial processing i relevantni testovi.

| Zahtev | Stanje | Dokaz / stvarna granica |
| --- | --- | --- |
| Izolacija i numerička/provenance osnova | DONE | Platform data/access/AI/reporting; ADR-0025; postojeće phase 22–25 acceptance |
| SIMPA XAI | PARTIAL | `src/domains/simpa/statistical_xai.py`, `src/streamlit_app/simpa_analytics_workspace.py`: koeficijenti, CI, dijagnostika, poreklo; nema SHAP panela |
| ORDO XAI | PARTIAL | `src/domains/ordo/analytics_xai.py`, `src/streamlit_app/ordo_analytics_workspace.py`: prognoze, intervali/backtests, scenariji; tabelarni prikaz |
| GIS identiteti i agregacije ORDO | PARTIAL | `src/domains/ordo/models.py`, `spatial_processing.py`: verzija granice/CRS, count/sum/mean/min/max po identitetu; bez geometrije i spatial join |
| SIMPA geografska osnova | PARTIAL | `src/domains/simpa/models.py`: geography_code/label; nema odgovarajućeg registra geometrije/kartografskog prikaza |
| Interaktivne GIS karte i povezani filteri | MISSING | Nema implementiranog punog GIS prikaza u pregledanim domen/UI modulima |
| SHAP matrice/lokalna i globalna atribucija | MISSING | Shared AI XAI izričito označava nepodržano; nema odgovarajućeg trajnog ugovora/engine/UI |
| Ekstrakcija prostornih entiteta i atomskih nalaza iz dokumenata | MISSING | CSV/JSON/XLSX materialization i record entity resolution postoje; PDF/DOCX se registruju za kasniju semantičku ekstrakciju (`src/platform/data/ingestion.py`); to nije geografski NER/claim review pipeline |
| Aktuelna governance dokumentacija | DRIFT | Mutable statusi još navode R3 candidate/#95 ili #27A, iako lokalni dokaz/#96 potvrđuju noviju ograničenu verifikaciju |

Ranija VERIFIED Help/XAI oznaka odnosi se na prihvaćeni tadašnji obim. Ne dokazuje kompletan sada traženi XAI/GIS/SHAP proizvod.

## 2. Šta korisnik dobija po proizvodu

| Funkcionalnost | SIMPA | ORDO |
| --- | --- | --- |
| GIS | Agregirani pokazatelji po JLS/prostornoj jedinici, usluge/ustanove gde su podaci dozvoljeni; kvalitet i dostupnost dokaza, poređenje perioda | Destinacije, resursi/objekti, infrastruktura i dokazima povezani indikatori; izbor teritorije i vremenske serije |
| Numerički XAI | Graf koeficijenata i CI, uzorak/missing data, postojeća dijagnostika; SHAP za ugovorom podržani numerički model | Istorijski backtest naspram stvarnih vrednosti, prognoza i intervali, kvalitet/razlozi NOT_ESTIMATED; SHAP samo za stvarno izvršiv i evaluiran odgovarajući model |
| Ekstrakcija | Mesta/JLS, organizacije/ustanove/usluge, indikatori, periodi i agregirani nalazi | Mesta/destinacije, resursi/objekti, organizacije, projekti i indikatori/periodi |
| Provera LLM nalaza | Svaka tvrdnja povezana sa izvorom, periodom, teritorijom i numeričkim rezultatom ako postoji | Isto, sa jasnim odvajanjem zapažanja, prognoze i scenarijske pretpostavke |
| Povezani prikaz | Klik na teritoriju filtrira tabelu, graf i nalaze; klik na nalaz otvara izvor i teritorijalnu vezu | Isti tehnički obrazac, odvojena ORDO semantika/podaci |

SIMPA prikazuje sisteme i agregate. Nema kartiranja korisnika socijalne zaštite, individualnih rizika niti automatskih odluka o pravima. ORDO scenario bez odobrenog response modela ostaje NOT_ESTIMATED.

## 3. Arhitektura i ugovori

Tok: **governed source → versioned extraction/geometry → candidate entities/claims → human review → governed snapshot → deterministic analytics/XAI → GIS prikaz → bounded LLM synthesis → review/report**.

Zajednički sloj poseduje infrastrukturu: storage, job dispatch/RQ, verzionisanje dokaza, autentikaciju, generičke geometry/extraction transport ugovore i renderer. SIMPA/ORDO zadržavaju domenske entitete, metodologije, spatial/statistical adaptere, prompts, privately scoped namespaces i tumačenja. Nema automatskog kopiranja privatnih entiteta između proizvoda/tenanata.

### GIS ugovor

- Stabilan identitet jedinice/objekta + verzija granice, izvor/licenca/hash, vremensko važenje, originalni CRS, geometry artifact i review stanje.
- GeoJSON prikaz u WGS84 sa redosledom longitude/latitude prema [RFC 7946](https://www.rfc-editor.org/info/rfc7946/). Originalni CRS i tačna transformacija ostaju u provenance; unknown CRS se odbija, koordinate se ne pogađaju.
- Poligon/Multipolygon za granice, Point samo za dozvoljene objekte sa potvrđenom lokacijom. Validacija tipa, opsega, topologije, axis order, duplikata, granica na datumu podataka i veličine payload-a. Popravka geometrije je nova verzija, nikad tiha izmena.
- Prvo mapiranje po potvrđenom ključu, uz broj nepovezanih redova. Point-in-polygon i drugi spatial join zahtevaju zaseban verzionisan ugovor sa pravilima za ivice, više pogodaka i unmatched; stari ORDO v1 ostaje identity-only.
- Karte imaju legendu, jedinice, period, provenance, kvalitet i stanja zero/missing/suppressed/not-applicable. Boje ne stvaraju neodobrene risk bands. Različite veličine populacije i promenjene granice ne porede se bez metodološkog pravila.
- Tabularni pristupačan fallback obavezan; nije potrebna mrežna mapa da bi korisnik pročitao rezultate. Bez spoljnog geokodera/tile providera po default-u. Izbor renderer-a/offline basemap-a i eventualnih biblioteka donosi se u 29B posle compatibility/licensing/security provere.
- PostGIS nije automatski uveden; GeoJSON/artifact + scoped PostgreSQL metadata su početna opcija. Ako prostorni upiti/kapacitet zahtevaju PostGIS, prvo ADR, migracija i operativni ugovor.

### XAI/SHAP ugovor

- Koeficijenti i CI prikazuju se na postojećoj family/link skali. Dijagnostika se prikazuje samo ako je sačuvana ili deterministički ponovo izračunata iz tačnog odobrenog inputa u zasebnoj verziji rezultata.
- XAI artifact vezuje result/model/feature/methodology/code verzije, training/background dataset, sample IDs u istom scope-u, target, units/link, explainer/masking/dependence semantiku, seed/tolerancije i fingerprint.
- SHAP početni kandidat: postojeći SIMPA continuous OLS, uz dokaz da se sačuvani tačni feature inputi i parametri mogu reprodukovati. Poisson/logit/fractional podrška se uključuje samo kada je posebno potvrđena output/link semantika i numerička ekvivalencija.
- SHAP isporuka uključuje sample×feature matricu, lokalni waterfall, globalni mean-absolute ranking/summary i tooltip sa baseline, vrednošću feature-a, doprinosom i jedinicom. Ne prikazivati ranking kao dokaz uzroka ili značaja institucionalne politike.
- Provera additivity: baseline + zbir doprinosa = tačan model output na navedenoj skali u deklarisanoj toleranciji. Korelisani features i izbor background-a imaju vidljivo objašnjenje. [SHAP LinearExplainer](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) dokumentuje da background/masking određuju atribuciju; izbor je deo ugovora.
- ORDO naive/seasonal-naive prvo dobijaju odgovarajuće grafike/backtests i objašnjenje upotrebljenih lagova. Nema lažnog SHAP-a za neizvršene regression/tree modele. ORDO SHAP zahteva zaseban odobren execution/result ugovor nad postojećom statistical specification osnovom; ovaj plan ga uključuje kao uslovnu granu, bez automatskog fitting-a/promotion-a ili proširenja model families.
- SHAP numeričkog modela ne potvrđuje verodostojnost LLM teksta. Za LLM se prikazuje claim→source→territory→result veza, pokrivenost citatima i neslaganja, bez generičkog procenta „AI pouzdanosti”.

### Ekstrakcija i geografski nalazi

- Digitalni tekst/tabele prvo; skenirani dokumenti/OCR-VLM u posebno evaluiranoj grani sa istim ugovorom. Registracija PDF-a nije izvršena ekstrakcija.
- Mention: tip i originalni tekst, document/source version/hash, page/span ili table/cell odnosno bbox kada postoji, jezik, ekstrakcioni model/prompt/policy verzija, job/attempt i status.
- Entity link: kandidat iz tenant/product scoped gazetteer/odobrenog boundary registra, alternativa, matching evidence, ambiguity i reviewer. Isto ime na više mesta, istorijsko ime i nerešena lokacija ostaju vidljivi; LLM ne generiše „tačnu” koordinatu.
- Claim: atomska tvrdnja, subjekat/predikat/vrednost/jedinica/period, teritorija ili eksplicitno unresolved, supporting/contradicting citations, tip (observation, model output, assumption, AI inference), limitations i review odluka.
- State: EXTRACTED_UNVERIFIED → REVIEWED_ACCEPTED ili REJECTED; corrected extraction kreira novu verziju. Prihvatanje ekstrakcije nije VALIDATED metodologija, niti dokaz da je tvrdnja istinita.
- Claim retrieval po teritoriji i vremenu koristi potvrđene identitete/filtere; koordinata entity-ja ne znači da svaki claim važi u toj tački. Obuhvat dokumenta, lokacija ustanove i obuhvat nalaza odvojeni su.
- Existing data-governance quarantine/reconciliation, source invalidation/privacy, scoped AI jobs i audit se ponovo koriste. Odbijeni ili povučeni izvori ne mogu nastaviti da podržavaju aktuelne nalaze/report.

## 4. Redosled implementacije i završni kriterijumi

| Paket | Isporuka | Zavisnosti | Prihvatanje |
| --- | --- | --- | --- |
| **29A — Graphical XAI** | SIMPA koeficijenti/CI; ORDO stored forecast/backtest graphics; vidljiva ograničenja; Help | Sadašnji exact-main baseline; bez novih modela/dependencies | Plot podaci odgovaraju stored result, safe escaping, zero/missing, NOT_ESTIMATED bez lažnih tačaka, desktop/mobile, full regression |
| **29B — GIS data contracts** | Governed geometry artifacts, scoped registries/adapters i reproducible spatial bindings za oba proizvoda | 29A; konkretan potvrđen geometry source/license; dependency odluka | Migrations upgrade/downgrade/native PG; CRS/topology/validity/identity/isolation i unknown CRS fail-closed |
| **29C — GIS user workflows** | Interaktivna karta+tabela+period, slojevi/legend/provenance, selection linking i permitted export | 29B | Tačni join/counts, unreachable/missing geometry fallback, map/table parity, mobile/keyboard, bez cross-scope leakage |
| **29D — SHAP/model attribution** | SIMPA podržane atribucije i matrice; ORDO uslovni numerical execution/attribution ugovor ili jasno unavailable za unsupported modele | Tačni model/features/background dostupni; 29A/B; po-family ugovor i evaluation | Additivity, reference equivalence, reproducibility, feature order, temporal leakage, performance/privacy; oba proizvoda bez lažne atribucije |
| **29E — Entity/claim extraction** | Versioned extraction, gazetteer linking, source anchors, review queue i geografski claims | 29B/C; odvojeni SIMPA/ORDO annotated evaluation setovi | Entity/span/geo-link/claim accuracy, ambiguity abstention, numeric/unit/period transcription, citations i adversarial/injection/isolation checks |
| **29F — Evidence, reports and release** | Povezani nalazi/karta/XAI, bounded synthesis, review/report/export, Help i novi Word screenshot manual | 29C/D/E | End-to-end source→claim→location→result→review→report; full gates/native/security/image; exact approved release checkpoint i naknadno ISI-28 deployment |

Redosled je 29A → 29B → 29C → 29D → 29E → 29F. Pre svake runtime celine zaključati exact allowlist, runner i nezavisni analyzer. 29B/E ulazi mogu se pripremati bez menjanja runtime-a. Ne čekati konačnu punu produkciju da bi lokalni razvoj počeo: owner proširenje omogućava 29 nad potvrđenim preproduction baseline-om, dok otvoreni 28 ops gates ostaju otvoreni.

**29A je prihvaćen na main cad6892; 29B geometrijski ugovori su lokalni kandidat. Sledeći runtime paket je 29C — GIS korisnički tokovi.** Ugovor: `automation/specs/ISI-29A-GRAPHICAL-XAI.md`. Owner je zatim odobrio izvršenje 29A–29F. Lokalni 29A runtime kandidat sada postoji; tačan status/gates su u njegovom evidence report-u. 29B–F nisu implementirani.

## 5. Evaluacija, privatnost i release

- Testni reference slučajevi: svi postojeći SIMPA families, legacy/no-CI/nonfinite/missing/zero; ORDO ESTIMATED/NOT_ESTIMATED/backtests/interval gaps; GIS changed boundaries, invalid CRS, edge/multi-match; extraction ambiguous place names, SR Latin/Cyrillic/EN, conflicting units/periods, malicious document instructions.
- Quality pragovi za extraction/retrieval i suppression politika moraju biti zamrznuti pre evaluacije na nezavisnom adjudicated corpus-u. Ne izmišljati institucionalne gold answers ni pragove tokom implementacije. Synthetic fixtures dokazuju software ponašanje, ne realnu domensku tačnost.
- Least-privilege Organization→Membership→Role→Product→Workspace, backend enforcement, privacy-purpose i local-only sensitive SIMPA; review zahteva stvarnog actor-a. Cache ključevi uključuju scope/filter/version; export revalidira prava, source validity i suppression. Sensitive koordinate/claims ne idu u logove/screenshot-e.
- Small-cell/reidentification i diferencijalni export/filter rizici imaju versioned institutional policy; bez nje detaljni osetljivi slojevi fail closed. Nema izmišljenog default suppression praga.
- Size/time/job limits, failed retry/idempotency/cancellation, bounded payload i safe text/rendering; nema arbitrary URL/SSRF fetch iz dokumenta. Scanned/PDF parsing zahteva izolaciju i resource limits u odgovarajućem ugovoru.
- Nakon svakog paketa targeted+regression, nezavisni analyzer i human review. Na završetku native PG/migration, performance, accessibility/responsive, dependency/SBOM/image security i exact-main acceptance. Novi dependencies se prvo opravdavaju i beleže u workstation requirements/MasterPlan; ništa se sada instalira.
- Commit/push samo posle owner odobrenja konkretnog proverenog kandidata; Actions zasebno odobren checkpoint sa usage pre/post. Deployment kroz ISI-28 posle exact-source signed bundle. Krcuga/OralScanXAI/shared Nginx strogo zaštićeni. Ovaj plan ne aktivira SMTP/backupe/purge ili modele na serveru.

## 6. Legacy/drift klasifikacija

| Nalaz | Klasifikacija | Postupak |
| --- | --- | --- |
| Prihvaćeni 23/24/25 Help/XAI checkpoint-i | LEGITIMATE_HISTORY | Sačuvati scope-bound acceptance, nove akcije zasebno MISSING/PARTIAL do dokazivanja |
| ORDO identity-only GIS v1 i stare immutable analytics rows | REQUIRED_COMPATIBILITY | Ne prepisivati geometry/joins u istoriju; novi versioned artifact |
| CSV/JSON/XLSX record entity resolution | REQUIRED_COMPATIBILITY | Ponovo koristiti; ne relabel kao document NER |
| Mutable R3 candidate/#95/27A current status posle #96 | REMOVE_BEFORE_NEXT_SLICE | Ovaj planning kandidat dodaje autoritativan current snapshot i tačan 28 task note; ranije checkpoint paragraphs history |
| Aktivni ops/template još zahtevaju codex-isi suprotno owner 19 Sep odluci | REMOVE_BEFORE_NEXT_SLICE | Usaglasiti te dve instrukcije u istom planning kandidatu; historical approval text ostaje history |
| ORDO overview čita shell.permissions umesto product.permission_codes | REMOVE_IN_NAMED_PHASE(ISI-29C) | Postojeći UI gap; zaključati poseban test/allowlist ako taj workflow postane ulaz u GIS; backend RBAC ostaje authority |
| Staging/precutover deployment assets i older backups | REQUIRED_COMPATIBILITY | Ne izvršavati/brisati; rollback/recovery granice ostaju 28 |
| Stari inventory notes „future 25/24D” | REMOVE_IN_NAMED_PHASE(ISI-29F) | Historical checkpoint je accepted; u 29F ciljno usaglasiti current inventory/help/report ownership |

Relevantna pretraga nije pronašla SHAP implementaciju, pun geometry renderer ili document geo-NER pipeline koji bi novi plan nepotrebno duplirao. Nisu izvršene izmene dependency/runtime/server stanja.

## 7. Inventory i dokaz završetka

MasterPlan target extension rows INV-A22, INV-B29, INV-C45, INV-M22 mapiraju nova korisnička, servisna, persistence i test ownership područja. Postojeći INV-A10/A11/A18/A19/A21, INV-B10/B13/B14/B18/B20/B21/B22, INV-C15/C19/C20/C32/C34–C39 i INV-M07/M08/M15/M16 ostaju as-built authority; njihova konkretna promena ide u paket koji menja ponašanje.
ISI-29 je IN_PROGRESS; 29A je unstaged kandidat i samo njegovi uspešni exact-candidate gates mogu potvrditi IMPLEMENTED. 29B–F ostaju planirani. Nema CI_VERIFIED/SERVER_VERIFIED za novi kandidat. Zaključiti prošireni zahtev tek kada svaki podržani workflow ima stvaran rezultat, graf/kartu, pregled entiteta/nalaza sa izvorom, review, testove i dokumentaciju; unsupported model/dataset states ostaju eksplicitni. Uspešna implementacija ne validira automatski institucionalnu metodologiju.


29A local verification record: IMPLEMENTED / REVIEW_VERIFIED candidate; 23 focused and 1203 regression passes, 43 existing native-lane skips, zero failures/errors. Four responsive widths and keyboard backtest selection verified on synthetic local preview. Exact report/fingerprint: `automation/evidence/ISI-29A/human-review.json`. No CI_VERIFIED or server deployment of 29A. 29B–F remain unimplemented; 29B read-only preparation recorded separately.


## ISI-29A approved main checkpoint and 29B continuation — 2026-10-07

Owner approved exact 29A candidate f220dd3dce9b172c05dc6982167f73b2cd848924b0060d48b1da4143970e492a; committed/pushed main `cad6892fd2d710b8263b936c06bb3d8137cdeddc` and direct remote equality verified with clean worktree. This supersedes mutable 29A unstaged/approval-pending wording; predecessor candidate/CI records remain LEGITIMATE_HISTORY. 29A NOT CI_VERIFIED; latest hosted acceptance #96 remains exact predecessor 374dda3. No CI/server action.

29B scoped geometry/storage/API/domain-adapter candidate is IN_PROGRESS. Contract automation/specs/ISI-29B-GIS-CONTRACTS.md; core_spatial_geometry_versions / migration0035; generic immutable geometry provenance and shared storage, separate SIMPA/ORDO adapters. WGS84 explicit lon/lat only; unknown/projected CRS and invalid topology rejected; no reprojection/provider/geocoder/tiles/PostGIS/indicator or AI changes. One geometry per version, human lifecycle, scoped permissions, immutable fingerprint and content hash. Actual approved boundary dataset absent; synthetic software tests only. Shapely2.1.2 added with existing NumPy preserved; no other lock versions upgraded. Help docs/help/ISI-SPATIAL-DATA-GUIDE.md covers source import/review, with GIS user interface still 29C. Native upgrade/downgrade, regression/dependency/independent review are gates, not yet claimed PASS in this record. 29C–F remain unimplemented. No new staging/commit/push or server mutation authorized by prior29A approval.


29B final local candidate record: initial focused39/native1/full regression passed; final synchronized candidate adds revocation/Help/duplicate checks and must rerun every gate. IMPLEMENTED is confirmed only by matching final acceptance.json + independent-analysis.json + human-review.json under automation/evidence/ISI-29B. Real institutional boundary dataset/licence and projected CRS reprojection remain unavailable; software infrastructure is implemented without importing invented boundaries. 29C–F runtime remains unimplemented.


29B local verification closeout: IMPLEMENTED / REVIEW_VERIFIED unstaged candidate; 42 focused and 1 native PostgreSQL test passed in the pre-final-review cycle (full migration upgrade/downgrade/reupgrade, constraints and stale concurrent write rejection), 1246 regression passes / 43 existing native-lane skips, zero failures/errors. Independent analyzer repeat PASS; runtime dependency audit and fixed musllinux wheel/local import checks PASS. Exact final candidate identity is automation/evidence/ISI-29B/human-review.json, with complete repeated gates on this documentation-synchronized candidate required. This supersedes mutable 29B IN_PROGRESS/verification-pending notes above; previous candidate narratives are LEGITIMATE_HISTORY. No CI/server acceptance or staging/commit/push; institutional geometry dataset/licence and projected CRS remain explicit missing/unsupported states. 29C–F still not implemented.

Final bounded review correction: reject non-string geometry type as a controlled validation failure; require native fixture loopback host before any DB access. Full exact-candidate gates must pass again; final counts/identity in automation/evidence/ISI-29B/human-review.json supersede prior cycle counts. No test gate bypass.
