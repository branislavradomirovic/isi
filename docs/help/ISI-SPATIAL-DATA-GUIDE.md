# ISI — Uvoz i validacija prostornih podataka

Status: ISI-29B lokalni API kandidat; grafički GIS radni tok dolazi u 29C. Nije potvrda stvarnih administrativnih granica, licence ili institucionalne metodologije.

## 1. Šta funkcija radi
Registar čuva privatnu verziju GeoJSON geometrije i metapodatke o poreklu, vremenskom važenju i ljudskom pregledu. SIMPA podržava granice lokalnog sistema i lokaciju institucionalnog objekta; ORDO granice prostorne jedinice i lokaciju asset objekta. Zajednička infrastruktura ne spaja domensku logiku.

## 2. Kada je koristiti
Kada postoji konkretan izvor geometrije sa poznatim koordinatnim sistemom, licencom i stabilnim identitetom već registrovanog objekta/jedinice. Ne koristiti izmišljene koordinate ili naziv mesta kao zamenu za potvrđenu lokaciju. Testne figure su sintetičke i ne predstavljaju granice Srbije.

## 3. Ko može koristiti
Svaki poziv zahteva prijavu, aktivno članstvo, pravo na proizvod i odgovarajući radni prostor. `data.upload` registruje; `data.governance.manage` predlaže/povlači; `data.validate` potvrđuje; `data.read` čita. Viewer ne registruje niti potvrđuje. Administrator je ograničen istim tenant/product/workspace pravilima. Dozvola se proverava ponovo za svaki poziv.

## 4. Koraci
1. Registrujte SIMPA local_system/local_actor ili ORDO spatial_unit/asset u odgovarajućem radnom prostoru. ORDO prostorna jedinica mora biti validated sa verzijom granice i izvorom.
2. Pripremite jedan Point za institucionalni objekat ili Polygon/MultiPolygon za granicu; dvodimenzionalne koordinate longitude/latitude u WGS84. Sačuvajte originalni izvor i njegov SHA-256.
3. U API `POST /api/v1/spatial/{SIMPA|ORDO}/geometries` unesite scope, domain_kind/domain_id, novu version, source_uri/source_version, declared_source_sha256, license_identifier, original_crs, axis_order, valid_from/valid_to i geometry.
4. Pregledajte DRAFT metapodatke preko scoped liste. Ne postoji otvorena javna biblioteka geometrije.
5. Pošaljite review sa aktuelnim revision i stanjem PROPOSED. Ovlašćeni reviewer proverava izvor, pravo upotrebe, identitet, lokaciju i vremensko važenje.
6. Za VALIDATED eksplicitno potvrdite `source_license_location_attested=true`. Sistem proverava topologiju, integritet objekta i domensku vezu; to ne zamenjuje stručnu proveru izvora.
7. Čitajte potvrđenu geometriju preko scoped detail uz obavezan `at_date`. Pogrešan datum ili povučen/draft izvor neće dati geometriju za upotrebu.
8. Grešku ispravite novom verzijom; staru RETIRED sačuvajte za istoriju. Nema izmene koordinata iste verzije niti povratka RETIRED u VALIDATED.

## 5. Polja i stanja
DRAFT je registrovan neproveren kandidat, PROPOSED kandidat za ljudski pregled, VALIDATED ljudski potvrđen izvor/identitet/lokacija, RETIRED povučena verzija. `revision` sprečava prepisivanje paralelnog pregleda. `version` je naziv nepromenljive verzije geometrije. `declared_source_sha256` je korisnikova izjava o originalnom izvoru; `geometry_sha256` je sistemski izračunat hash tačno sačuvanog GeoJSON-a. `fingerprint` uključuje scope, izvor, licencu, vremensko važenje i domensku vezu. `HUMAN_ATTESTED` označava ljudsku potvrdu, ne nezavisni mrežni pregled licence.

`valid_from` i `valid_to` su uključive granice važenja; prazno valid_to znači otvoren kraj. `OGC:CRS84` i `EPSG:4326` podržani su samo uz izričit `longitude_latitude`; prikaz je CRS84 sa IDENTITY_WGS84_LON_LAT provenance. Ne pretpostavljajte da datoteka sa EPSG oznakom koristi odgovarajući redosled osa.

## 6. Sintetički primer
Granica sa tačkama (20,44), (21,44), (21,45), (20,45), (20,44) služi samo testu softvera. Nije stvarna opština/destinacija. Point institucionalnog objekta može biti upotrebljen tek nakon potvrde identiteta i izvorne lokacije; naziv ili LLM odgovor nije dovoljan.

## 7. Šta sistem ne radi
Nema automatskog geokodiranja, spoljnih mapa, reprojekcije projektovanog CRS-a, tihog popravljanja geometrije, pojedinačnih građanskih lokacija, prostornog zaključivanja ili matematičkih indeksa/rizika. Nema GIS frontend karte u 29B. Prostorni join i povezivanje sa analizom nisu autoritet ove faze. Prekogranične poligone na antimeridijanu izvor mora eksplicitno podeliti.

## 8. Greške i oporavak
- 403: proverite organizaciju, proizvod, radni prostor i dozvolu; ne pokušavajte tuđi scope.
- 404: identitet nije u dozvoljenom scope-u; ne dokazuje da tuđi zapis postoji.
- 409: verzija već postoji ili revision nije aktuelan; ponovo pročitajte metapodatke, ne prepisujte pregled.
- 400/422: nepoznat CRS, tip, redosled osa, neispravni prstenovi/topologija, opseg, period ili domenska veza; ispravite originalni izvor i kreirajte novu verziju.
- geometry_not_validated/not_valid_at_date: izaberite potvrđenu verziju koja važi za datum podataka.
- Integrity/storage greška: prekinite upotrebu, prijavite administratoru; nema fallback-a na tuđu geometriju. Ako se identitet promenio ili izvor povukao, RETIRED ostaje moguć. Ne brišite privatne objekte ručno.

## 9. Bezbednost, privatnost i ograničenja
Nema automatskog deljenja između SIMPA/ORDO ili organizacija, slanja geometrije geokoderu ili AI provajderu. Izvorni URL mora biti HTTPS bez korisničkih podataka, query tokena ili fragmenta; sistem ga ne posećuje. Ne unosite tajne, privatne kontakte ili podatke o građanima. Sirova geometrija ograničena je na 200000 bajtova/10000 koordinata; nema automatskog uprošćavanja. Planarna provera topologije nije geodetski obračun udaljenosti/površine. Licencu i institucionalnu primenu odgovorna osoba proverava posebno.

## 10. Provenance i ljudski pregled
Sistem čuva scope, izvor/verziju, izjavljeni hash, licencu, originalni/render CRS, tačan transform ugovor, geometrijski hash, identitet domenskog objekta, važenje i fingerprint. Aktor registracije/pregleda i promene stanja auditovani su bez sirovih koordinata/lozinki/tokena. Promena vezanog domenskog identiteta, povlačenje ORDO granice, neispravnost storage hash-a ili datum van važenja blokira upotrebu. Nove verzije ne menjaju stare rezultate. GIS UI, analitičko povezivanje i Word screenshot priručnik proširuju se u kasnijim 29C/29F paketima.
