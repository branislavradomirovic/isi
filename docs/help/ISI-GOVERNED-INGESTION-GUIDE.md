# Kontrolisano učitavanje — korisnički vodič

## Svrha i upotreba
Ovaj tok priprema postojeći izvor za ponovljiv kontrolisani ingestion iz datoteke.
Koristite ga kada želite eksplicitnu šemu, identitet zapisa, karantin i operativnu
ocenu pre izrade analitičkog skupa. Profil inbound/batch ne preuzima podatke sa URL-a.

## Uloge
data.read: pregled verzija ugovora u aktivnoj organizaciji/proizvodu/radnom prostoru.
data.governance.manage: registracija i ljudski potvrđeno aktiviranje četiri ugovora.
data.upload: kontrolisano učitavanje kroz aktivni lanac. Backend proverava sve veze.

## Koraci
1. U Podaci izaberite izvor i otvorite „Priprema ugovora i kontrolisano učitavanje“.
2. U „1. Konektor“ registrujte inbound/batch nacrt, osvežite, izaberite nacrt i
   potvrdite aktiviranje. Ovo ne čuva kredencijale i ne pokreće mrežni konektor.
3. U „2. Mapiranje kolona“ popunite po jedan red za svaku izvornu kolonu: ime,
   tip, obaveznost, nullable i MAP/IGNORE. Kod MAP navedite jedinstven ciljni ključ;
   kod IGNORE ostavite ključ prazan. Redosled redova je ordinal šeme.
4. Odaberite TABULAR ili RECORD prema stvarnoj datoteci. CSV/XLSX zahtevaju TABULAR;
   JSON podržava odgovarajući postojeći oblik. Izaberite REJECT/IGNORE za nepoznata
   polja. Nedostajuće tokene navedite po jedan u redu, uključujući prazan token samo
   ako je stvarno deo odobrenog ugovora. Sistem ne imputira vrednosti.
5. Registrujte nacrt mapiranja, osvežite i aktivirajte ga. Prikazan je vezani konektor.
6. U „3. Identitet i politika zapisa“ izaberite ključeve identiteta među MAP poljima,
   registrujte i aktivirajte politiku. Konflikti/nedostajući identitet idu u karantin;
   identični duplikati povezuju postojeći zapis.
7. U „4. Operativna politika“ unesite stvarno odobrene pragove starosti u sekundama,
   udele karantina 0–1, obavezne šifre provera i retry/dead-letter pravila. Sistem
   nema institucionalne podrazumevane pragove. Odbijanje mora biti >= upozorenja.
8. Potvrdite registraciju politike, osvežite i aktivirajte njen nacrt.
9. Proverite tabelu aktivnog lanca. Sva četiri identiteta moraju pripadati istom
   izvoru i biti vezana za prethodnu aktivnu verziju.
10. U „5. Učitavanje kroz aktivne ugovore“ izaberite CSV/JSON/XLSX, navedite jedinstven
    idempotency ključ, eventualni kursor, potvrdu i „Pokreni kontrolisanu obradu“.
11. Osvežite obradu i pregledajte inspekciju, ocenu i kontrolisani izlaz.

## Polja i stanja
DRAFT je nacrt, ACTIVE odobrena aktivna verzija, RETIRED istorijska verzija.
Aktiviranje nove verzije može učiniti prethodna nizvodna vezivanja nevažećim;
ponovo usaglasite ceo lanac. Otisak ugovora identifikuje tačan sadržaj verzije.
required označava obavezno polje, nullable dozvolu prazne vrednosti. MAP povezuje
izvornu kolonu sa ključem, IGNORE izričito odbacuje polje. PRESERVE_MISSING znači
čuvanje semantike nedostajuće vrednosti. Kursor je neprozirna oznaka serije, nije
procena vremena. Politika dozvole backfill/replay ne izvršava sama te operacije.

## Primer
Za sintetičku tabelu unit/period/value autor mapira unit na ključ jedinice i period
na datum, u skladu sa odobrenom šemom, zatim bira stvarni identitet. Pragove ocene
preuzima iz odobrene politike, ne iz ovog primera. Isti zahtev posle prekida šalje
sa istim ključem i istim sadržajem; različit sadržaj uz isti ključ se odbija.

## Greške i oporavak
Bez aktivne vezane verzije sledeći korak prikazuje preduslov. Nevalidna polja se
odbijaju pre API slanja; backend dodatno proverava semantiku/duplikate/veze/prava.
Posle prekida prvo osvežite verzije/status: commit može prethoditi dispatch-u.
Ne kreirajte slepo drugi ugovor niti menjajte idempotency ključ istog zahteva.
Kod isteka sesije prijavite se ponovo, kod zabrane proverite ulogu/radni prostor.

## Ograničenja, provenijencija i ljudski pregled
Nema URL/secret/JSON konzole, imputacije, automatske institucionalne validacije,
novog modela ili zaključka o korisnicima. Autor potvrđuje šemu i operativnu politiku;
ne unosite tajne u nazive, šifre i reference. Aktivni ugovori i otisci, verzija
izvora, run i ocena čine provenijenciju. Analitički ugovori i njihova validacija
su zaseban korak. Datirane ilustracije opisuju ovaj tok u detaljnom Help-u.
