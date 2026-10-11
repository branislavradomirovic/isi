# ISI — AI dokazi i ljudski pregled

## 1. Namena
AI je pomoćni sloj za pregled dokaza. Numerički sistemi ostaju autoritet; LLM
tekst ne predstavlja automatski institucionalni zaključak.

## 2. Kontekst
Izaberite organizaciju, SIMPA ili ORDO, radni prostor i AI. Istorija job-ova i
 evaluacije pripadaju tačnom kontekstu. Modelski/prompt registar može biti zajednički
ili proizvodni; to ne daje pristup tuđim privatnim rezultatima.

## 3. Istorija i rezultat
Pregledajte status, model/provider, prompt verziju, politiku, pokušaje i ljudski
review status. Izaberite job za sveži rezultat i trag. Struktura se prikazuje kao
polja/vrednosti; nula, false i nedostajuća vrednost ostaju različiti. Ograničenje
broja/dubine polja se prikazuje, nije potvrda kompletnosti dokaza.

## 4. Objašnjenja
Pregled job-a pokazuje pokušaje, fallback i zahteve ljudskog pregleda. Evaluacija
pokazuje metrike sa otiscima, registry/prompt/policy/benchmark identitet, izvor,
ljudski pregled, drift/circuit i ograničenja. Nedostupni SHAP, importance, kalibracija,
pouzdanost, verovatnoća ili neizvesnost ne dobijaju izmišljene brojeve.

## 5. Učitavanje evaluacije
analysis.read omogućava „Učitaj / osveži AI evaluacione dokaze“. Izaberite konkretan
run; nema podrazumevanog cilja. Rezultati, istorija pregleda i objašnjenje učitavaju
se sveže. Prazan registar nije potvrda kvaliteta modela.

## 6. Odluka pregleda
report.publish i aktivno članstvo omogućavaju pending, a za terminalni completed/
failed run i approved, changes_requested ili rejected. Odaberite odluku, obrazloženje
i referencu dokaza. Za konačnu odluku obrazloženje/referenca moraju biti popunjeni.
Ne unosite tajne, lozinke ili neodobrene lične podatke u napomene/referencu.

## 7. Potvrda i trag
Potvrdite upravo pregledane dokaze i kliknite „Sačuvaj ljudski AI pregled“.
Promena polja/dokaza/konteksta poništava potvrdu. Server pod zaključavanjem proverava
pregledani status/otisak rezultata, ulogu i scope pre upisa postojećeg auditabilnog
pregleda. Konačni pregled istog recenzenta je neizmenjiv. Uspeh zahteva novo učitavanje.

## 8. Infrastrukturna dijagnostika
analysis.run UI omogućava postojeći lokalni Ollama foundation test. Eksplicitno
izaberite lokalni registrovani model, sensitivity i potvrdu. Unos je fiksni sintetički
infrastrukturni primer; ne sadrži institucionalne podatke. SIMPA sensitive ostaje
local_only i zahteva ljudski pregled. Registrovan queued zahtev nije gotov rezultat.

## 9. Greške i oporavak
Promenjeni dokaz zahteva osvežavanje i novi pregled. Bez ovlašćenja/terminalnog stanja/
reference nema konačnog upisa. Ne prepisujte neizmenjivi pregled. Posle prekida mreže
prvo pregledajte istoriju jer je upis mogao uspeti. Nema automatskog retry-ja i nema
sirove poruke servera sa privatnim request poljima.

## 10. Granice i dokazi
Pregled ne promoviše model, ne menja provider, ne bira champion i ne objavljuje izveštaj.
Registracija/benchmark/threshold/promotion/circuit i evaluaciono izvršavanje ostaju
operaterski upravljani kroz postojeće ugovore. Sintetički QA nije institucionalno
odobrenje ni produkciona kalibracija. Datirane ilustracije prikazuju lokalno proverene tokove;
stvarno stanje server izdanja proverava se zasebno.
