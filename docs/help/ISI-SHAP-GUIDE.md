# SIMPA — SHAP matrica i objašnjenje doprinosa

Status: ISI-29D lokalni kandidat; release i server acceptance zasebni. ORDO naive/seasonal-naive nisu SHAP modeli.

## 1. Šta funkcija radi
Za sačuvani continuous OLS rezultat kreira nepromenljiv dokaz: baseline, sample×feature matrica, globalna srednja apsolutna vrednost doprinosa i lokalni waterfall. Tačan interventional linear SHAP doprinos je koeficijent × (input − background srednja vrednost). Sistem koristi postojeće koeficijente; ne trenira drugi model.

## 2. Kada koristiti
Pri stručnom pregledu numeričkog modela, kada su ulazi, metodologija i rezultat validni i dostupni. Ovo su objašnjenja rezultata za originalni trening skup, ne prognoza budućnosti. SHAP nije potvrda tačnosti LLM zaključka.

## 3. Ko može koristiti
Aktivno članstvo, SIMPA entitlement i odgovarajući workspace obavezni su pri svakom pozivu. `analysis.read` čita; `analysis.run` zajedno sa čitanjem eksplicitno kreira. Administratorska rola ne otvara tuđu organizaciju/proizvod. Viewer može čitati dozvoljeni postojeći dokaz, ne kreirati.

## 4. Koraci
Otvorite SIMPA → Analitika → sačuvani statistički rezultat → „SHAP — matrica i doprinosi”. Pročitajte Help. Ovlašćeni analitičar bira „Kreiraj SHAP dokaz iz postojećeg rezultata”. To je zaseban ljudski korak; nema automatskog kreiranja ni model fitting-a. Za čitanje označite „Učitaj sačuvani SHAP dokaz”. Pregledajte background, jedinicu, globalnu tabelu/graf i matricu. Izaberite broj uzorka za waterfall; tabela sadrži input, doprinos, početak/kraj koraka i jedinicu. Sačuvani dokaz se revalidira pri svakom novom čitanju.

## 5. Značenje polja i stanja
Baseline je očekivani output postojećeg modela na tačnom complete-case trening background-u. Output skala je identity, jedinica dolazi iz validirane ciljne metodologije. Pozitivan SHAP pomera rezultat iznad baseline-a, negativan ispod. Globalni mean-absolute ranking opisuje prosečnu veličinu doprinosa, ne značaj politike. Features imaju tačan redosled modela; boje označavaju znak/veličinu, ne rizik; sivo je numerički nulti doprinos. NOT_CREATED nema dokaz; AVAILABLE ima revalidiran dokaz; UNAVAILABLE znači da ugovor/provenance/pristup nisu podobni. Tehnička tolerancija additivity/parity je 1e-8 apsolutno i relativno, ne prag institucionalne odluke. VALIDATED ugovor pri izvršenju i sada je obavezan; PROPOSED/RETIRED ne dobijaju SHAP.

## 6. Sintetički primer
Ako je baseline=10 jedinica, input contribution A=+3 a B=−1, output modela je12. To objašnjava aritmetiku postojećeg modela. Ne tvrdi da promena A uzrokuje poboljšanje institucije. Numerička nula je vrednost; prazni obavezni target/features izostavljaju se istim complete-case pravilom kao pri fit-u.

## 7. Šta sistem ne radi
Nema kauzalnog zaključivanja, generičke AI pouzdanosti, građanskog scoring-a, novih težina/indikatora, promenjenog background-a, prognoze ili automatske preporuke. Nekauzalna (non-causal) interpretacija je obavezna. Poisson/logit/fractional modeli trenutno nisu podržani. ORDO naive/seasonal-naive koriste postojeća objašnjenja lagova/backtesta; nema lažnog SHAP-a za neizvršene modele. LLM tvrdnje zahtevaju zasebno proverljive izvore i ljudski pregled.

## 8. Greške i oporavak
Proverite sesiju, organizaciju, proizvod, workspace i dozvole kod403. Kod UNAVAILABLE proverite lifecycle/izvor/metodologiju; ne pokušavajte prepisivanje dokaza. Promenjeni/povučeni izvor blokira čitanje i ranijeg artefakta. Nefinitne vrednosti, neusklađen fingerprint, drugačiji feature redosled ili numerička nepodudarnost zaustavljaju prikaz. Granica je512 izabranih zapisa i24 features; nema tihog uzorkovanja. Heatmap prikazuje prvih60 redova uz obaveštenje, puna matrica ostaje tabela.

## 9. Bezbednost i ograničenja
Sve se računa lokalno u backend-u, bez spoljnih AI/SHAP servisa. Matrica sadrži samo numeričke agregatne model inputs i lokalni broj uzorka; nema građanskih imena ili source locators. Interventional SHAP zanemaruje korelacije features: rezultat zavisi od izabranog background ugovora i nije conditional attribution. Ovo ne zamenjuje institucionalnu metodologiju, privatnost izvora, procenu modela ili odgovornost stručnog tima. Nema novog unosa budućih perioda; objašnjava se originalni trening cohort.

## 10. Poreklo i ljudski pregled
Dokaz vezuje tačan result/run/contract/methodology, organization/workspace, ulazni i dataset fingerprint, background hash, schema/method/unit/tolerance i artefakt hash. Implementacijski i input-reconstruction hash su zabeleženi; originalni fit code SHA nije bio sačuvan u starim rezultatima (NOT_RECORDED_LEGACY_RESULT). Closed-form metoda nema random seed/sampling. Aktor/vreme/ID kreiranja su vezani fingerprint-om; audit beleži fingerprint, ne matrix/input. Ponovna provera obuhvata trenutni izvor, lifecycle i rezultat. Sačuvani dokaz ne menja stare modele, metodologije ili izveštaje. Ljudski stručni pregled i dalje određuje dozvoljenu institucionalnu upotrebu.
