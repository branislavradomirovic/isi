# ORDO — prostorna agregacija validiranog identiteta

## 1. Namena
Deskriptivna agregacija postojećih opservacija istog prostornog identiteta.
Nije GIS join, ponderisanje, forecast, kauzalni efekat ili preporuka.

## 2. Pristup
ORDO → Analitika + AI → ORDO prostorna agregacija validiranog identiteta.
Potrebni analysis.read, data.read i analysis.run u izabranoj organizaciji/workspace-u.
Server proverava analysis.run i aktivno članstvo; skriven ekran nije zamena za server proveru.

## 3. Preduslovi
VALIDATED metodologija sa ORDO-SPATIAL-AGGREGATION-v1 ugovorom; completed governed
ANALYTICAL_SNAPSHOT ili ANALYTICAL_FEATURE_VERSION run; VALIDATED ORDO jedinica.
Metodološko odobrenje je poseban ljudski postupak, nije automatski rezultat forme.

## 4. Učitavanje
Kliknite „Učitaj / osveži ORDO prostorne ulaze“. Učitavaju se aktuelni registri.
Ograničen spisak jedinica ima upozorenje; odsustvo u spisku ne dokazuje nepostojanje.
Osvežavanje poništava prethodni izbor i potvrdu.

## 5. Izbor polja
Izaberite metodologiju (indikator/verzija/pravilo), governed run i jedinicu
(ključ/verzija granica/CRS). Sva tri izbora su u početku prazna.
Pravilo count/sum/mean/min/max dolazi iz odobrene metodologije, ne iz proizvoljnog
izbora pri izvršenju. count broji zapise; ostala pravila isključuju nedostajuće
numeričke vrednosti i beleže njihov broj; nema popunjavanja nulom.

## 6. Pregled i potvrda
Pročitajte tabelu identifikatora/verzije/pravila/identiteta/tipa/granica/CRS.
Potvrdite pregledano izvršenje. Promena izbora menja vezu potvrde. Backend proverava
pregledani ID metodologije pod zaključavanjem; promenjeno odobrenje odbija zahtev.

## 7. Izvršenje
Kliknite „Izvrši ORDO prostornu agregaciju“. Backend ponovo proverava ulazne
fingerprint-e, kvalitet validiranih zapisa i potpuno podudaranje identiteta,
granica i CRS svih zapisa indikatora. Različite jedinice ne spaja automatski.

## 8. Rezultat i GIS
Uspeh prikazuje ID registracije; izbor/potvrda se resetuju. Podaci → GIS:
osvežite validiranu geometriju povezane jedinice i njene rezultate. Postojeći GIS
adapter ponovo proverava metodologiju, ulaz, obračun i fingerprint; zastareo rezultat
je UNAVAILABLE. Registracija ne garantuje dostupnost trenutne brojčane vrednosti.
Datum važenja geometrije nije period opservacije (NOT_ASSIGNED ostaje vidljiv).

## 9. Greške i oporavak
Bez preduslova nema izvršenja. Zastarela metodologija, granice/CRS, kvalitet ili
ulaz odbijaju zahtev bez promene. Posle prekida mreže prvo osvežite GIS pregled:
promena je mogla biti registrovana; ne ponavljajte automatski. Ista veza run/indikator/jedinica/metodologija je jedinstvena: ponovljeno izvršenje
vraća konflikt409, ne predstavlja idempotentan retry.

## 10. Dokazi i ograničenja
ID/verzija metodologije, run/ulazni otisci, jedinica/granice/CRS i trag obračuna
pripadaju postojećem ORDO rezultatu. Ne postoje nove formule ili prostorna inferencija.
Sintetički QA ekrani nisu institucionalni podaci ili ljudsko metodološko odobrenje.
Datirane ilustracije prikazuju postojeći lokalno provereni korisnički tok.
