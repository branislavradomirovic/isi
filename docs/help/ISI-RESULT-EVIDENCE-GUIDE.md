# ISI — čitanje rezultata i porekla dokaza

## 1. Namena
Naslovljene tabele objašnjavaju sačuvani rezultat, ulaz, metodologiju i ograničenja.
Ne računaju novi rezultat niti potvrđuju istinitost izvornog nalaza.

## 2. Kontekst
SIMPA/ORDO, organizacija i radni prostor ostaju granice. Analitika, GIS, ekstrakcija
i izveštaji koriste postojeća zasebna ovlašćenja i serversku revalidaciju izvora.

## 3. Polja i vrednosti
Svaki red navodi putanju polja i tekstualnu vrednost. 0 je nula; False je negativna
logička vrednost; „Nije navedeno“ je nedostajuće. Prazna struktura ne znači nultu
metričku vrednost. Dugi dokazi imaju izričito ograničenje prikaza, ne prećutnu kompletnost.

## 4. SIMPA rezultat
Pregledajte identitet modela/cilja, koeficijente i postojeći grafikon, fit/error,
dijagnostiku, kalibraciju, otiske i production_eligible. Ne tumačite koeficijent
kao kauzalni efekat. Tabele su prikaz postojeće validirane numeričke osnove.

## 5. SHAP
Posebno učitajte sačuvani podržani SIMPA OLS SHAP dokaz. Globalni doprinos, matrica,
heatmap i lokalni waterfall ostaju dostupni uz proveru ugovora. Nova tabela prikazuje
schema/method/fingerprint/background/provenance. SHAP opisuje doprinos modelu, ne
istinitost LLM tvrdnje, kauzalnost ili generičku pouzdanost.

## 6. ORDO forecast
ESTIMATED prikazuje sačuvane tačke/intervale, backtest grafikon i tabelu. Proverite
coverage, rolling-origin plan, dostupnost metrika, dijagnostiku i poreklo.
NOT_ESTIMATED ne dobija izmišljene tačke, nule, intervale ili metrike.
ORDO naive/seasonal-naive nema podržan SHAP. Interval nije generička verovatnoća.

## 7. Scenario
Scenario readiness nije prognoza efekta. NOT_ESTIMATED impact ostaje nenumerički.
Pregledajte razloge, pretpostavke, poreklo i nepodržana objašnjenja; nema automatskog
pretvaranja scenarija u prognozu ili preporuku.

## 8. GIS i ekstrakcija
GIS metapodaci prikazuju identitet/verziju/izvor; tačan GeoJSON je samo u opcionalnom
tehničkom expander-u. Karte i rezultati imaju postojeću revalidaciju. Ekstrakcija
prikazuje entitete, citate/start/end lokatore, potvrđeni ili nerešeni obuhvat,
verzije i ljudski pregled. UNCALIBRATED ostaje ograničenje kvaliteta modela.

## 9. Povezani izveštaj i greške
Citirani nalaz, izvor, pregled i numerički dokaz imaju odvojene tabele/grafikone.
Veza ne potvrđuje slaganje perioda/teritorije niti istinitost. Ako dokaz nije dostupan,
proverite sesiju, prava i aktuelnu verziju. Osvežite pre ponavljanja; nema automatskog
retry-ja, sirovih exception poruka ili zamenskog rezultata.

## 10. Dokaz i ograničenja
Otisci daju identitet/verziju dokaza, ne institucionalnu validaciju. Izvorni tekst
prikazuje se kao tekst, ne izvršivi HTML. Sve postojeće domenske granice i grafički
ugovori ostaju. Sintetički QA nije produkcioni zaključak. Datirane ilustracije
prikazuju postojeći rezultat, ne novo institucionalno odobrenje.
