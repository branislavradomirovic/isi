# ISI — entiteti i nalazi sa izvorima (29E)

## 1. Svrha
SIMPA i ORDO imaju odvojene domenske instrukcije i registre. Ekstrakcija izvlači originalne citate, entitete i atomske nalaze. Model ne računa nove domenske indikatore niti potvrđuje institucionalne zaključke.

## 2. Kada koristiti
Za zbirne nepersonalne izvore sa dozvolom za lokalnu AI analizu. Podržani su digitalni UTF-8 TXT dokumenti i već validirani/zamrznuti governed snapshot-i tabela. PDF/DOCX/OCR/VLM nisu podržani ovom fazom. Realna kvalitetna domenska evaluacija ostaje UNCALIBRATED; sintetičke SR Latinica/Ćirilica/EN evaluacije proveravaju softverski ugovor.

## 3. Prava i kontekst
`data.read`: lista, izvori, nalazi. `ai.run`: novi zahtev i otkazivanje pending posla. `data.validate`: konačan ljudski pregled. Organizacija → članstvo → uloga → proizvod → workspace se proveravaju na backend-u. Koristite aktivni SIMPA ili ORDO kontekst; izvor drugog proizvoda ili organizacije nije dozvoljen.

## 4. Postupak
U Podacima otvorite „Entiteti i nalazi“. Eksplicitno učitajte listu. Uredite governance izvora pre kreiranja zahteva: aktivan izvor, uspešan ingest, dostupna verzija, klasifikacija, aggregate nonpersonal, svrha, vlasnik i lokalna AI dozvola. Izaberite document/snapshot, tačan UUID verzije/snapshot-a, jezik i registrovani lokalni model. Pokrenite novu ekstrakciju. Osvežite listu i otvorite izabrani zahtev. Pregledajte sve citate i polja. Izaberite konačno prihvatanje ili odbijanje, napišite razlog i potvrdite pregled. Za ispravku napravite novi zahtev; konačni artefakt i pregled su nepromenljivi.

## 5. Polja i statusi
`queued/running/failed` su statusi AI posla. `EXTRACTED_UNVERIFIED` čeka pregled; `REVIEWED_ACCEPTED` znači da je čovek pregledao ekstrakciju; `REJECTED` je isključuje iz prihvaćenih nalaza; `CANCELLED` označava zahtev otkazan pre izvršenja. Nalaz ima statement, subject, predicate, value, unit, period, vrstu (observation/model_output/assumption/AI_inference), podržavajuće/protivrečne citate i ograničenja. `null` označava nedostajuće, nula je citirana nula. SR/EN original ostaje neizmenjen; nema automatskog prevoda.

## 6. Primer i GIS povezivanje
Sintetičko: „Grad A ima 12 usluga u 2025.“ Broj, jedinica i period moraju ostati originalni. Imena se predlažu samo tačnim poređenjem; AMBIGUOUS/CANDIDATE nisu rešeni identiteti. U pregledu posebno izaberite domenski identitet i napišite dokaz; možete ostaviti UNRESOLVED. Teritoriju svakog nalaza posebno vežite za validiranu polygon/multipolygon verziju sa datumom i dokazom obuhvata. Lokacija ustanove (Point) nije automatski teritorija njenog nalaza. Filteri koriste tačan period citata i UUID pregledane granice; ne rade prostorni join ni nagađanje koordinata.

## 7. Granice tumačenja
Prihvatanje ekstrakcije ne potvrđuje istinu, domensku metodologiju, uzročnost ili zakonsku podobnost. SHAP objašnjava postojeći podržani numerički model i ne proverava LLM tvrdnje. Nema personalnog profilisanja, citizen scoring-a, geokodera ni automatske institucionalne preporuke. Izvorni span koristi Unicode offset [start,end); tabela koristi normalizovanu ćeliju, record fingerprint i source locator. Dokument nema izmišljene page/bbox podatke.

## 8. Greške i oporavak
Ulaz je ograničen na 200 KB raw TXT, 12.000 znakova, 200 ćelija, 20.000 znakova ukupnog AI request envelope-a, najviše 100 entiteta i 100 nalaza; preveliki ulazi se odbijaju bez tihog skraćivanja. Netačan citat, nezaključen ugovor, promena politike/modela/prompta ili izvora blokiraju rezultat. Posao se proverava pre i posle modela. Pending zahtev može da se otkaže; postojeći request key ne šalje ponovo posao. Failed/odbijen rezultat zahteva eksplicitno novi zahtev. Bez modela kreiranje je onemogućeno. Ako izvor postane nedostupan, otvaranje i aktuelno pronalaženje njegovih nalaza su blokirani.

## 9. Privatnost i bezbednost
Samo lokalni AI, registrovana konfiguracija i postojeći worker. Nema slanja spoljnim providerima, unosa novih modela, preuzimanja proizvoljnih URL-ova ili menjanja servera. Izvorne instrukcije su nepoverljivi podaci. Citati ostaju u organizaciji/proizvodu/workspace-u; audit beleži otiske, ne sirovi sadržaj. Promene governance-a, purge ili povlačenje izvora ponovo se proveravaju pri čitanju.

## 10. Poreklo, ljudski pregled i rezultati
Proverite source/version/hash, span/cell, jezik, model, prompt, policy, code hash, posao/pokušaj, actor/time i fingerprint. Svako polje dokumenta je u citiranoj tvrdnji; polja tabele mogu biti u različitim ćelijama istog reda uz zasebne tačne podržavajuće citate. Ne smeju spajati redove. Pronalaženje odbija zbir veći od 100 nalaza ili 2 MB; suzite filtere umesto tihog skraćivanja. Pregledani identiteti i granice se ponovo proveravaju pri čitanju. Samo REVIEWED_ACCEPTED ulazi u listu prihvaćenih nalaza. Reports/export/Word dopuna i konačni release pripadaju 29F; postojeći institucionalni izveštaji ne dobijaju automatski neproverene nalaze.

29E final governance review: general AI jobs retain metadata only for extraction; successful raw input/output/structured copies are cleared in the worker transaction. Quotations remain solely in source-revalidated extraction artifacts, preventing general AI/report reads from bypassing source withdrawal (REMOVE_BEFORE_NEXT_SLICE, resolved in this candidate; legacy non-extraction jobs REQUIRED_COMPATIBILITY). Code fingerprint pins service/contracts/models and the selected product extraction/spatial adapter. Empty pending request text and runtime-policy/model parameter drift fail before provider execution. Signed/decimal/date fragments cannot silently become partial numeric value/period tokens; spelling stays verbatim without numerical interpretation or domain formula. Exact final gates required after these bounded corrections.
