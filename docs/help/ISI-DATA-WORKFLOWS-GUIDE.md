# Podaci — verzije, kvalitet i kontrolisana obrada

## Svrha i vreme upotrebe
Koristite ovaj pregled posle učitavanja izvora i kada proveravate koja je tačno
verzija obrađena. Osnovna inspekcija i kontrolisani ingestion su različiti koraci.
Uspešno učitavanje datoteke nije automatski kontrolisani analitički izlaz.

## Pristup
`data.read` omogućava pregled unutar aktivne organizacije, proizvoda i radnog
prostora. `data.upload` omogućava novu verziju i potvrđeno ponavljanje neuspele
obrade. Backend ponovo proverava prava; vidljivo dugme nije dodatna dozvola.

## Koraci
1. Izaberite organizaciju, SIMPA ili ORDO i radni prostor u bočnom panelu.
2. Otvorite Podaci, pa u odeljku „Verzije, kvalitet i obrada izvora“ izaberite izvor.
3. Izaberite verziju. Uporedite naziv datoteke, broj verzije, status i SHA-256.
4. Pročitajte provere kvaliteta: oznaku provere, status, poruku i metriku.
5. Za dopunu otvorite „Nova verzija postojećeg izvora“, izaberite datoteku,
   potvrdite naziv izvora i pritisnite „Dodaj novu verziju“.
6. Osvežite pregled i proverite da li je verzija zaista registrovana.
7. Izaberite kontrolisanu obradu. „Status inspekcije“ prikazuje posao i napredak.
8. „Prikaži ocenu obrade“ prikazuje svežinu, kvalitet i odluku operativne politike.
9. „Prikaži kontrolisani izlaz“ prikazuje identitet, broj zapisa i otisak izlaza.
10. Samo za FAILED obradu označite potvrdu i izaberite „Ponovi neuspelu obradu“.
    Sistem neposredno pre slanja ponovo proverava status. Osvežite posle slanja.

## Polja i statusi
Verzija je nepromenljiva registrovana datoteka. SHA-256 identifikuje sadržaj;
otisak strukture identifikuje detektovanu šemu. Redovi i kolone mogu biti nepoznati
pre obrade ili kod netabelarnog formata. Prazna kvalitetska tabela ne znači PASS.
QUEUED znači čekanje, RUNNING obradu, SUCCEEDED završen posao, FAILED grešku.
Ocena ima odvojenu odluku ACCEPTED, ACCEPTED_WITH_WARNING, REJECTED ili
DEAD_LETTERED, uz status kvaliteta i svežine. Nepostojanje ocene nije prihvatanje.
Kontrolisani izlaz navodi ocenu, aktuelne/duplikat/karantinske/zamenjene zapise.

## Primer
Sintetički izvor „Opštinski agregati“ dobije v2 nakon korekcije naziva kolone.
Pregledajte kvalitet v2 i njen otisak. Ako kontrolisana obrada odbije mapiranje,
ispravite odobreni ugovor u odgovarajućem toku; ponavljanje samo po sebi ne menja
mapiranje i ne garantuje prolaz.

## Greške i oporavak
Kod istekle sesije prijavite se ponovo. Kod zabrane pristupa proverite aktivni
radni prostor i ulogu. Nedostupna ocena/izlaz može značiti nedovršenu ili odbijenu
obradu. Kod prekida servisa prvo osvežite istoriju/status: zahtev je mogao biti
sačuvan pre prekida dispatch-a. Nemojte slepo ponovo učitati istu datoteku.
Ako se FAILED promeni u QUEUED/RUNNING/SUCCEEDED, ponavljanje se ne šalje.

## Ograničenja, bezbednost i ljudski pregled
Pregled ne izvozi raw zapise, ne zaobilazi privatnost, ne validira metodologiju,
ne pokreće model i ne daje institucionalni zaključak. Provera kvaliteta nije
pravna potvrda niti dokaz reprezentativnosti. Koristite samo odobrene podatke.
AI i analitika zahtevaju zasebno kontrolisan analitički ugovor i validaciju.
Identitet izvora/verzije/obrade/ocene i otisci ostaju proverljiva provenijencija.
Nove ilustracije i Word pokrivenost ovog toka pripadaju30E; ovaj tekst sam nije
potpuno završena vizuelna acceptance evidencija.
