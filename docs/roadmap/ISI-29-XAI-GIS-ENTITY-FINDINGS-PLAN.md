# ISI-29 — XAI, GIS i entiteti/nalazi sa dokazima

Datum: 2026-10-07. Status: **IN_PROGRESS / 29A–D CI_VERIFIED i preproduction SERVER_VERIFIED na95fec435;29E lokalni kandidat;29F sledeći**.
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

**29A–D su prihvaćeni na95fec435, exact CI/scoped preproduction server potvrđen; 29E lokalni kandidat zahteva konačne tačne dokaze; sledeći paket je29F.** Tačni lokalni/CI/server statusi ostaju u aktuelnim ledger/evidence zapisima; istorijski kandidati ispod ne menjaju ovu aktivnu putanju.

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


## ISI-29B approved main and ISI-29C implementation — 2026-10-07

29B approved exact candidate1c5a531c6ba7e206a1d822e295d70b2e3377257fc06873872d6c07210331f418 committed/pushed main0d59f40aa03ab7115041f1c58052d4610aac3a54; all28 committed file hashes match approval, clean single main worktree/direct remote equality. Final29B43 focused/native1/regression1247 passes,43 predecessor native skips; NOT CI_VERIFIED, no new server verification. Latest hosted acceptance#96 remains predecessor374dda3. This supersedes mutable29B approval-pending notes; earlier candidate gates/history remain LEGITIMATE_HISTORY.

Owner now explicitly approves all planned verified29A-F commits/pushes; repeated per-candidate commit approval is no longer required. Exact deterministic gates, independent readonly analysis and assistant review remain mandatory.29F acceptance/deployment authorization is subject to usage pre/post, exact committed main CI, signed image/bundle and approved ISI-28 server contract. Shared edge non-target protection remains mandatory. SMTP pending/new backups owner-deferred.

29C locked candidate: automation/specs/ISI-29C-GIS-WORKFLOWS.md. Existing Data surface now includes shared GIS catalogue/import/review/date/layer/version/map/table/selected provenance and explicit geometry export. Existing ORDO spatial-unit identity lifecycle exposed; actual ORDO overview permission source fixed, stable resource code input added. Separate domain selectors; no new navigation/schema/formula/provider/model. Geometry date is not observation period. ORDO exact identity-only stored result viewer revalidates source/methodology/boundary/trace/arithmetic; no result-to-geography association exists for SIMPA, displayed unavailable. No institutional boundary source/licence auto-created.

Actual browser WebGL limitation rejected the Pydeck draft renderer (REMOVE_BEFORE_NEXT_SLICE). Final renderer uses existing Streamlit1.63 components.v2 with fixed code/data-only SVG DOM; no new dependencies/lock/install. Bounded25features/50000coordinates/1MB; render-only Mercator with exact source coordinates retained; safe textContent labels, selection/pan/zoom/keyboard controls and table fallback, no tiles/provider keys/user markup. Local focused/full/browser/independent gates required before IMPLEMENTED/REVIEW_VERIFIED closeout; evidence automation/evidence/ISI-29C.29D-F remain unimplemented. DEFERRED_SERVER_VERIFICATION.


## ISI-29C local verification closeout — 2026-10-07

IMPLEMENTED local candidate:37 focused tests and1283 regression tests pass,44 existing native-lane skips, zero failures/errors; lint/policy/mypy/pip/diff gates PASS. Synthetic desktop1280/mobile390 browser checks PASS: map click/Enter/Space, linked selected table/provenance, ORDO result table/chart, zoom/reset, no page overflow or external assets. Exact synchronized candidate requires matching acceptance/browser/independent-analysis/human-review reports under automation/evidence/ISI-29C before approved staging. First unfinished runtime package29D;29E/F planned. Standing owner approval covers verified commit/push. No new CI/server acceptance; DEFERRED_SERVER_VERIFICATION, no full-production claim. Historical pending notes above are LEGITIMATE_HISTORY superseded by this closeout.


## ISI-29C approved main / ISI-29D attribution candidate — 2026-10-08

29C accepted main a77f9f0b4e43038554ee203a0c5ad22cd0b9e981, exact26-file candidate025263734c8ff82ef85c01f01a229e8724ea22ed6b13cfffb312426bacf7f82d; repeated local7gate/independent twice/assistant review PASS.37 focused/1283 regression passes,44 existing native-lane skips; main/origin/direct equality and clean one-worktree checkpoint recorded. No hosted/server verification inherited. Mutable prior29C candidate/current-next text superseded (LEGITIMATE_HISTORY).

29D IN_PROGRESS locked automation/specs/ISI-29D-MODEL-ATTRIBUTION.md: additive0036 simpa_attribution_artifacts, exact interventional continuous OLS explanation from stored coefficients and revalidated complete-case training cohort. No refitting/dependency/provider/model-family change. Domain-owned source/result/contract/background/artifact hashes and immutable metadata; read revalidates source/methodology and stored metric/prediction parity. Scoped analysis.read, explicit analysis.run creation, fingerprint-only audit. Existing SIMPA result expander gains matrix/heatmap/global mean-absolute/local waterfall and ten-item Help docs/help/ISI-SHAP-GUIDE.md. Technical1e-8 tolerance is not institutional threshold.512 selected rows/24features bounded; original training cohort only, correlated features limitations visible. ORDO naive/seasonal SHAP remains unsupported; conditional new model execution not automatically selected. NOT CI_VERIFIED; server deferred to29F. Local/native/full/browser/independent/human exact gates required before phase closeout. Browser access restored on 2026-10-08; synthetic desktop1280/mobile390 visual/keyboard/viewer/unsupported/tamper gates passed, with screenshots under automation/evidence/ISI-29D/. Contradictory legacy non-SHAP caption corrected only in the new attribution panel. Native0036 test participates in the existing hosted native lane without skips. Final local gates/independent review are rerun on the exact updated candidate before authorized commit/push.29E/F unimplemented; current owner explicitly requests checkpoint/deployment of verified current source in preproduction-testing mode, separate from29F whole-plan completion.


## ISI-29E entity/claim extraction candidate — 2026-10-08

29A–29D are CI_VERIFIED / REVIEW_VERIFIED at exact main 95fec43590e9b1d3eb44d55867666581118ec650 (ISI required acceptance run37746165918, all12 completed/success). Recorded signed deployment and scoped server acceptance passed in PREPRODUCTION_TESTING, schema0036; automation/evidence/ISI-29D/release/closeout.json. No fresh server probe in29E. SMTP pending, new backups owner-deferred, institutional/capacity/operational full-production gates remain open.

29E IN_PROGRESS on canonical main; locked automation/specs/ISI-29E-ENTITY-CLAIM-EXTRACTION.md. Additive0037 core_extraction_requests/artifacts/reviews; shared transport/persistence with separate SIMPA/ORDO prompts and scoped gazetteers. Governed aggregate nonpersonal UTF-8 TXT or validated/frozen snapshot cells only; exact Unicode spans/cells and version/hash/record lineage. Local registered AI queue/model/policy; source/actor/prompt/model/request pinned and checked before/after worker execution and at read. Historical code hash remains provenance; pending execution requires current code parity. No parser/OCR/VLM/geocoder/dependency/model install or new numerical authority. Exact-name suggestions remain unresolved until final attested data.validate review; entity registry identity and separately dated polygon claim scope revalidated. Accepted/rejected reviews append once; only accepted findings participate in scoped exact period/geometry retrieval. Invalidated/purged/reclassified input blocks current quotation/retrieval. No raw-content audit, cross-product retrieval, report promotion or fabricated coordinates/truth/causality. Real-domain extraction quality UNCALIBRATED; separate SR Latin/Cyrillic/EN annotated synthetic fixtures are software tests only. Data workspace gains explicit load/create/cancel/source/review/filter controls and ten-item Help.

Local deterministic focused/native/regression/browser/independent gates required on exact candidate before IMPLEMENTED / REVIEW_VERIFIED and standing approved commit/push. 29E is NOT CI_VERIFIED; DEFERRED_SERVER_VERIFICATION. 29F remains first planned package after verified29E: linked reports/Help/Word and whole-plan acceptance/controlled deployment. Historical candidate/CI notes above are LEGITIMATE_HISTORY; this snapshot supersedes current status statements.


### ISI-29E local closeout authority

IMPLEMENTED / REVIEW_VERIFIED applies only to the exact30-file candidate with matching PASS acceptance.json, browser-verification.json, independent-analysis.json and human-review.json under automation/evidence/ISI-29E. Final synchronized candidate must pass all8 gates again before staging; test counts and file hashes are recorded in those reports. Native0037 upgrade/downgrade/reupgrade uses a disposable loopback PostgreSQL schema. Synthetic desktop1280/mobile390 source/identity/territory review, accepted-only period retrieval, ORDO rejection, Help and no page overflow are exercised; no real model quality certification. Earlier51-focused/1375-regression cycle passed and is retained under verified-cycle-51; a final controlled storage-I/O failure case is included in the synchronized candidate.

Standing owner approval covers verified29A-F commit/push. First unfinished package after verified29E is29F (linked evidence/report/Help/Word/final acceptance and controlled deployment). NOT CI_VERIFIED / DEFERRED_SERVER_VERIFICATION for29E; recorded server remains95fec435/schema0036. No new Actions dispatch, server/Nginx/model mutation or SMTP/backups action occurs here. Real adjudicated extraction quality remains UNCALIBRATED; full-production operational gates remain open.

29E final governance review: general AI jobs retain metadata only for extraction; successful raw input/output/structured copies are cleared in the worker transaction. Quotations remain solely in source-revalidated extraction artifacts, preventing general AI/report reads from bypassing source withdrawal (REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate; legacy non-extraction jobs REQUIRED_COMPATIBILITY). Code fingerprint pins service/contracts/models and the selected product extraction/spatial adapter. Empty pending request text and runtime-policy/model parameter drift fail before provider execution. Signed/decimal/date fragments cannot silently become partial numeric value/period tokens; spelling stays verbatim without numerical interpretation or domain formula. Exact final gates required after these bounded corrections.
