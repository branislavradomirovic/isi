# Oporavak kontrolisane obrade

1. **Svrha:** dopuna određenog prozora (backfill), ponovna obrada originalnog
   sadržaja (replay) i pregled odbijenih operativnih stavki (dead-letter).
2. **Pristup:** Podaci → izvor → Operativni oporavak obrade. Proverite organizaciju,
   proizvod SIMPA/ORDO i workspace. `data.read` za pregled; `data.upload` za backfill/
   replay; `data.governance.manage` za requeue i zatvaranje dead-letter stavke.
3. **Preduslovi:** usaglašeni ugovori i operativna politika koja dozvoljava operaciju;
   dostupan originalni sadržaj za replay; nema aktivne konfliktne obrade. Backend
   ponovo proverava svaki uslov. Istorijska obrada bez politike nije replay kandidat.
4. **Pregled:** kliknite „Učitaj / osveži operativni pregled“. Sam pregled ne pokreće
   posao. Osvežavanje uklanja prethodno označene potvrde; proverite izbor ponovo.
5. **Backfill:** izaberite CSV/JSON/XLSX do16MB, unesite eksplicitni idempotency ključ,
   početni/krajnji neproziran kursor i opciono vreme opažanja. Vreme mora imati UTC
   pomak, npr. `2026-10-10T12:00:00+02:00`; prazno znači nepoznato, ne trenutni čas.
   Potvrdite prozor/datoteku/ugovore, zatim „Pokreni backfill“. Forward kursor ostaje.
6. **Replay:** izaberite završenu obradu, unesite ključ novog replay zahteva, potvrdite
   izbor i kliknite „Pokreni replay“. Ponovno slanje istog zahteva koristi isti ključ;
   novi sadržaj ili druga operacija sa istim ključem nisu dozvoljeni.
7. **Dead-letter:** pregledajte razlog i povezanu obradu. OPEN stavka može u kontrolisani
   replay preko novog ključa i potvrde. Zatvaranje zahteva RESOLVED/DISCARDED i obrazloženje.
   DISCARDED je sačuvana odluka, ne brisanje sadržaja. Odluka ne prihvata odbijeni izlaz.
8. **Rezultati i greške:** poruka „Registrovano“ potvrđuje zahtev, ne uspešnu završenu
   obradu. Osvežite izvor/obradu i pregledajte ocenu i kontrolisani izlaz. Posle prekida
   veze prvo osvežite; zahtev možda postoji. Politika, povučeni sadržaj ili aktivan posao
   mogu blokirati operaciju. Ne menjajte ključ radi zaobilaženja konflikta.
9. **Ograničenja:** nema automatske metodološke ili institucionalne validacije, imputacije,
   popravke karantina ili AI odobrenja. Samo postojeći pinovani ugovori i sadržaj.
10. **Evidencija:** sačuvani ID obrade/stavke, otisci, vezane politike i audit ostaju
    dostupni ovlašćenim korisnicima. Datirane sintetičke ilustracije prikazuju ovaj tok u Help-u;
    stanje stvarnog izdanja i izvora proverava se zasebno. Ne unosite tajne ili lične podatke u obrazloženje.
