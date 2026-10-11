# ORDO — statističke specifikacije i ljudski pregled

## 1. Namena
ORDO-STATISTICAL-MODEL-CONTRACT-v1 je verzionisani metodološki ugovor.
Fitting NOT_IMPLEMENTED; numerical_results NOT_PRESENT. Nema koeficijenata,
SHAP-a ili performansi samo zato što je specifikacija VALIDATED.

## 2. Pristup
ORDO → Analitika + AI → ORDO statističke specifikacije i ljudski pregled.
analysis.read za pregled; indicator.manage i aktivno članstvo za promene.
Organizacija/workspace ostaju granice registra. Globalna ciljna metodologija
ima zasebno odobrenje, ali statistička specifikacija pripada ovom workspace-u.

## 3. Učitavanje i stranice
Izaberite stranicu (100 specifikacija po stranici), zatim „Učitaj / osveži
ORDO statistički registar“. Promena stranice zahteva novo učitavanje i pregled.
Upozorenje za naredne stavke znači da postoji sledeća stranica, ne novi rezultat.
Osvežavanje resetuje prethodne potvrde.

## 4. Cilj i ulaz
Za novi DRAFT izaberite trenutno VALIDATED ciljnu metodologiju, completed
ANALYTICAL_SNAPSHOT ili ANALYTICAL_FEATURE_VERSION run, semantiku cilja i strukturu.
Nema automatski potvrđenih izbora. Server proverava pregledani ID metodologije
pod zaključavanjem i sam vezuje verziju/hash metodologije i governed input.

## 5. Polja definicije
Unesite analysis_key, svrhu, dozvoljenu modelsku i response porodicu.
continuous: linear/robust + gaussian; count: poisson/negative-binomial;
proportion_rate: fractional/beta. Panel: fixed_effects/mixed_effects/hierarchical.
Ovo su postojeće specifikacije, ne tvrdnja da je fitting tih porodica dostupan.
Unesite početak/kraj/as-of (start ≤ end ≤ as-of), pretpostavke, potrebnu
DIJAGNOSTIKU i ograničenja — jedan zapis po redu. Polja su u početku prazna.

## 6. Feature tabela
Dodajte najmanje jednu jedinstvenu feature definiciju: feature_key, role
(predictor/control/offset/exposure), source_field, version_identity,
transformation (none/log1p/standardize/categorical) i missing_rule
(complete_case/exclude/missing_indicator). Pregledajte izvore/verzije.
Definicije su metapodaci; ne tvrde da je feature transformisan ili model fitovan.
Ne unosite lozinke, tokene ili neodobrene lične podatke u polja/referencu.

## 7. Kreiranje i pregled
Potvrdite autorizovani DRAFT i pregledanu ciljnu metodologiju/ulaz, pa kliknite
„Registruj ORDO statistički DRAFT“. Posle uspeha ponovo učitajte registar i
izaberite specifikaciju. Pregled prikazuje definiciju, features, pretpostavke,
dijagnostiku, ograničenja, otiske, status/verziju i ljudski trag.

## 8. Ljudski lifecycle
DRAFT → PROPOSED: izričita potvrda. PROPOSED → VALIDATED: obrazloženje i referenca
dokaza pregleda. Odobrenje povlači prethodnu validiranu verziju istog analysis_key
u istom workspace-u. VALIDATED → RETIRED: razlog i potvrda; istorija ostaje.
Backend proverava pregledani status/hash pod zaključavanjem, a pri predlaganju i
odobrenju ponovo proverava metodologiju/ulaz/otiske. Promenjeni dokaz blokira prelaz.

## 9. Greške i oporavak
Bez uloga ili preduslova nema promena. Neispravna semantika/familija, duplirani
features, datumi ili zastareo pregled odbijaju zahtev. Konflikt verzije zahteva
osvežavanje, ne automatski retry. Posle prekida mreže prvo proverite registar:
promena je mogla biti sačuvana. Uspeh resetuje prethodne potvrde.

## 10. Tumačenje i dokaz
VALIDATED odobrava specifikaciju, ne koeficijente, predikciju ili institucionalni
zaključak. non_causal=true i automatic_policy_recommendation=false su zaključani.
Podaci pregleda su istorijski metapodaci, ne potvrda aktuelnog numeričkog rezultata.
Sintetički QA ekrani nisu stvarno metodološko odobrenje. Datirane ilustracije prikazuju specifikaciju
i njenu kontrolu, bez tvrdnje da je izvršeno fitovanje modela.
