# ISI — Uvoz i validacija prostornih podataka

Status: ISI-29B prihvaćen na main; ISI-29C lokalni GIS korisnički kandidat, uz zasebne acceptance/release provere. Nije potvrda stvarnih administrativnih granica, licence ili institucionalne metodologije.

## 1. Šta funkcija radi
Registar čuva privatnu verziju GeoJSON geometrije i metapodatke o poreklu, vremenskom važenju i ljudskom pregledu. SIMPA podržava granice lokalnog sistema i lokaciju institucionalnog objekta; ORDO granice prostorne jedinice i lokaciju asset objekta. Zajednička infrastruktura ne spaja domensku logiku.

## 2. Kada je koristiti
Kada postoji konkretan izvor geometrije sa poznatim koordinatnim sistemom, licencom i stabilnim identitetom već registrovanog objekta/jedinice. Ne koristiti izmišljene koordinate ili naziv mesta kao zamenu za potvrđenu lokaciju. Testne figure su sintetičke i ne predstavljaju granice Srbije.

## 3. Ko može koristiti
Svaki poziv zahteva prijavu, aktivno članstvo, pravo na proizvod i odgovarajući radni prostor. `data.upload` registruje; `data.governance.manage` predlaže/povlači; `data.validate` potvrđuje; `data.read` čita; `data.export` eksplicitno izvozi uz ponovno čitanje/validaciju; `analysis.read` otvara povezane rezultate. Viewer ne registruje niti potvrđuje. Administrator je ograničen istim tenant/product/workspace pravilima. Dozvola se proverava ponovo za svaki poziv.

## 4. Koraci
U aplikaciji izaberite organizaciju, SIMPA/ORDO, workspace i **Podaci → GIS — karte, geometrija i ljudski pregled**.
- ORDO: u „Prostorne jedinice” registrujte identitet, izvor/granicu/CRS/hash i datume. Predložite/potvrdite identitet uz obrazloženje. Potvrda identiteta nije potvrda koordinata. SIMPA profil/aktivni institucionalni akter i ORDO resurs zahtevaju stabilnu šifru u svojim overview obrascima.
- Sa `data.upload` otvorite „Uvoz nove verzije geometrije”, izaberite domenski identitet, unesite poreklo/licencu/hash/datume, potvrdite ose i izaberite jednu geometry datoteku. FeatureCollection nije podržani ulaz. Registruj DRAFT ne potvrđuje izvor.
- „Ljudski pregled” prikazuje poreklo/revision. Predložite, zatim ovlašćeni reviewer proverava i potvrđuje VALIDATED ili povlači RETIRED.
- Izaberite datum važenja geometrije, slojeve i najviše25 tačnih verzija. Ograničen katalog100 nije kompletan ako postoje dodatni zapisi. Tačka/poligon ima isti ID u karti, tabeli i izboru. Klik na kartu/red ili tastaturni izbor otvara tačnu verziju/provenance.
- Karte imaju pan/zoom/reset tastere i pomeranje prevlačenjem prazne podloge; Enter/Space bira fokusiranu figuru; legenda plavo=granica, oker=objekat, ljubičasto=izbor. Nema risk bands. Isključite „Prikaži interaktivnu kartu” za tabularni rad; WebGL nije potreban za tabelu/izbor.
- `analysis.read` prikazuje samo revalidirane ORDO identity-only agregacije sa tačnom jedinicom/graničnom verzijom. Prikazuje se najviše10 najnovijih sačuvanih rezultata uz upozorenje ako postoje dodatni. Izaberite jedan rezultat za tabelu/graf i counts. Nema spatial join-a. SIMPA nema odobrenu vezu rezultata sa geometrijom pa numerički sloj ostaje unavailable. **Datum geometrije nije period opservacija**: stari ORDO ugovor nema period nalaza.
- Sa `data.export` kliknite „Pripremi izvoz izabrane geometrije”, zatim preuzmite GeoJSON sa poreklom; backend ponovo proverava scope/state/date/integritet i beleži audit sa akterom, bez koordinata. Izvoz ne daje pravo javne objave ili deljenja.

API koraci za kontrolisane integracije:
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
Nema automatskog geokodiranja, spoljnih mapa, reprojekcije projektovanog CRS-a, tihog popravljanja geometrije, pojedinačnih građanskih lokacija, prostornog zaključivanja ili matematičkih indeksa/rizika. 29B je API osnova; 29C dodaje kartu i tabelu na Podaci → GIS. Prostorni join i povezivanje sa analizom nisu autoritet ove faze. Prekogranične poligone na antimeridijanu izvor mora eksplicitno podeliti.

## 8. Greške i oporavak
- Vektorska karta ne zahteva WebGL. Ako pol na ±90° nije podržan Mercator projekcijom, koristite tabelu/izbor; geometrija se ne menja. Ako izbor prelazi50000 koordinata/1000000 bajtova, smanjite broj verzija; nema tihog uprošćavanja.
- 403: proverite organizaciju, proizvod, radni prostor i dozvolu; ne pokušavajte tuđi scope.
- 404: identitet nije u dozvoljenom scope-u; ne dokazuje da tuđi zapis postoji.
- 409: verzija već postoji ili revision nije aktuelan; ponovo pročitajte metapodatke, ne prepisujte pregled.
- 400/422: nepoznat CRS, tip, redosled osa, neispravni prstenovi/topologija, opseg, period ili domenska veza; ispravite originalni izvor i kreirajte novu verziju.
- geometry_not_validated/not_valid_at_date: izaberite potvrđenu verziju koja važi za datum podataka.
- Integrity/storage greška: prekinite upotrebu, prijavite administratoru; nema fallback-a na tuđu geometriju. Ako se identitet promenio ili izvor povukao, RETIRED ostaje moguć. Ne brišite privatne objekte ručno.

## 9. Bezbednost, privatnost i ograničenja
Karta koristi praznu lokalnu podlogu bez spoljnih tiles/glyphs/sprites; nazivi mesta i ulice nisu automatski dostupni. Nema automatskog deljenja između SIMPA/ORDO ili organizacija, slanja geometrije geokoderu ili AI provajderu. Izvorni URL mora biti HTTPS bez korisničkih podataka, query tokena ili fragmenta; sistem ga ne posećuje. Ne unosite tajne, privatne kontakte ili podatke o građanima. Sirova geometrija ograničena je na 200000 bajtova/10000 koordinata; nema automatskog uprošćavanja. Planarna provera topologije nije geodetski obračun udaljenosti/površine. Licencu i institucionalnu primenu odgovorna osoba proverava posebno.

## 10. Provenance i ljudski pregled
Sistem čuva scope, izvor/verziju, izjavljeni hash, licencu, originalni/render CRS, tačan transform ugovor, geometrijski hash, identitet domenskog objekta, važenje i fingerprint. Aktor registracije/pregleda i promene stanja auditovani su bez sirovih koordinata/lozinki/tokena. Promena vezanog domenskog identiteta, povlačenje ORDO granice, neispravnost storage hash-a ili datum van važenja blokira upotrebu. Nove verzije ne menjaju stare rezultate. 29C povezuje kartu/tabelu/izbor geometrije i revalidirane ORDO identity-only rezultate; Word screenshot dopuna ostaje 29F.
