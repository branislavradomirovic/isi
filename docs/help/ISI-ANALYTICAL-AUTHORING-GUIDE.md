# Analitički skupovi, ugovori, snapshot-i i feature verzije

## Svrha i vreme upotrebe
Ovim tokom autor registruje ponovljiv analitički skup iz kontrolisanih izlaza,
zatim njegovu verziju i feature reference. Koristite ga posle kontrolisanog
učitavanja i governance pregleda izvora, pre SIMPA/ORDO determinističke analize.

## Prava i granice
data.read omogućava postojeći pregled registara/provenijencije. Autorstvo i
promene stanja zahtevaju data.governance.manage u aktivnoj organizaciji, proizvodu
i radnom prostoru. API ponovo proverava prava, vezane izvore i njihove politike.

## Registracija skupa i feature-a
U Podaci otvorite „Registry governance controls“. U „Registracija analitičkog
skupa“ unesite jedinstvenu oznaku, naziv, opis i stvarnu referencu/verziju odobrene
metodologije. Označite potvrdu, pritisnite „Registruj analitički skup“ i osvežite
registre. Feature registar koristi isti postupak u „Registracija feature-a“;
registracija feature-a sama ne računa vrednosti niti izmišlja transformaciju.

## Ugovor polja
1. Izaberite „Skup za ugovor i snapshot“, otvorite „Ugovor polja i aktiviranje“.
2. Dodajte red po polju: jedinstveni ključ, tip, obaveznost i semantičku ulogu.
3. KEY znači ključ identiteta/granularnosti; DIMENSION dimenziju; MEASURE meru;
   ATTRIBUTE dodatni atribut. Uloge ne pretvaraju LLM u numerički autoritet.
4. Izaberite vremenski ugovor: STATIC bez vremenskog ključa; POINT_IN_TIME jedan
   ključ; PERIOD dva ključa, u redosledu početak/kraj. Vremenska polja moraju biti
   obavezna DATE/DATETIME. Navedite ključeve po jedan u redu.
5. Navedite ključeve granularnosti: već deklarisana obavezna KEY polja.
6. Potvrdite ugovor i registrujte nacrt. Backend proverava duplikate, uloge,
   kardinalnost i tipove. PRESERVE_MISSING ne imputira vrednosti.
7. Osvežite, izaberite nacrt, označite potvrdu i „Aktiviraj analitički ugovor“.

## Snapshot iz kontrolisanih izlaza
Otvorite „Snapshot iz kontrolisanih izlaza“. Aktivni ugovor je preduslov. Pritisnite
„Učitaj dostupne kontrolisane izlaze“, pa izaberite tačne izlaze po izvoru/ID/otisku.
Unesite metodološku referencu/verziju i referencu izrade. Potvrdite i kreirajte
snapshot, zatim osvežite. Backend ponovo proverava accepted ocenu, source governance,
aktivni ugovor i neprekinutu lineage. Nedostupan/povučen/reklasifikovan izvor može
blokirati kreiranje iako je stari izlaz još bio prikazan. Raw source verzije nisu
opcija za ovu izradu. Pogledajte lineage, kvalitet, broj zapisa i otisak snapshot-a.

## Životni ciklus snapshot-a
DRAFT→VALIDATED→FROZEN→RETIRED su odvojene ljudske odluke. Izaberite artefakt,
proverite reviziju, stanje i otisak, označite potvrdu i izaberite prikazanu sledeću
promenu. Backend validira kontrolisane ulaze pre VALIDATED/FROZEN. Istorijski
raw-source ili invalidated snapshot-i se ne promovišu ovim tokom. Kod promene
revizije osvežite i ponovo pregledajte; ne pokušavajte da preskočite životni ciklus.

## Feature verzija i njen životni ciklus
Izaberite feature. U „Verzija feature-a iz kontrolisanih snapshot-a“ odaberite samo
prikazane VALIDATED/FROZEN kontrolisane snapshot-e, unesite referencu/verziju,
potvrdite i kreirajte verziju. DRAFT→GOVERNED→FROZEN→RETIRED koristi zasebni odeljak,
reviziju i potvrdu. FROZEN feature zahteva zamrznute ulazne snapshot-e. Više
snapshot-a u feature registru ne garantuje da ih konkretni SIMPA/ORDO model može
koristiti: postojeći deterministički domain loader zahteva jedan eksplicitni ulaz.

## Primer
Sintetički dataset ima unit kao obavezni STRING/KEY, period kao obavezni DATE i
value kao NUMBER/MEASURE. Autor navodi POINT_IN_TIME, period kao vremenski i unit
kao granularity ključ, u skladu sa stvarnom metodologijom. Snapshot iz accepted
kontrolisanog izlaza ostaje DRAFT dok ga ovlašćeni čovek ne pregleda. Primer ne
uvodi formulu, težine ili institucionalno odobrenje.

## Polja, greške i oporavak
Otisak identifikuje sadržaj, revizija kontrolne izmene, verzija nepromenljivi
artefakt. VALIDATED/GOVERNED nisu isto stanje za različite tipove artefakata.
Prazan selektor znači nedostajuće preduslove; nije nulti nalaz. Kod zastarele
revizije ili upstream invalidation osvežite, pregledajte lineage i rešite razlog
u odgovarajućem izvornom toku. Kod prekida servisa prvo osvežite registre jer je
promena mogla već biti registrovana. Kod isteka sesije prijavite se ponovo; kod
zabrane proverite radni prostor/ulogu. Forme ne prikazuju raw sadržaj greške validacije.

## Ograničenja, bezbednost i provenijencija
Nema imputacije, nove formule, numeričke transformacije, automatske preporuke,
validacije institucionalne metodologije ili automatske AI promocije. Reference ne
smeju sadržati tajne. Kvalitet i privatnost nasleđuju kontrolisane izvore; backend
ponovo proverava klasifikaciju, licence/politike, lineage i povlačenje sadržaja.
AI eligibility ostaje odvojen deterministički pregled; ne pokreće model. Human
review i metodološka odgovornost ostaju kod ovlašćenog autora/reviewera. Novi
screenshot-i i završna Word parity su30E; ovaj tekst nije samostalna produkciona
vizuelna acceptance potvrda.
