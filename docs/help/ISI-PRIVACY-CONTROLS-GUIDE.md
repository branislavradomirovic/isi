# Čuvanje, hold, anonimizacija i dozvoljeni izvoz

1. **Svrha:** primena odobrenih politika čuvanja, zabrana brisanja, evidencija i
   pregled anonimizacije i kontrolisani izvoz verzije. Sistem ne određuje pravni rok.
2. **Pristup:** Podaci → izabrani izvor → Čuvanje, anonimizacija i izvoz izvora.
   Proverite organizaciju, SIMPA/ORDO i workspace. `data.read` za retention pregled,
   `data.governance.manage` za politike/hold/dokaze, `data.export` za izvoz.
3. **Politika:** unesite oznaku, verziju, naziv, odobrene rokove i referencu. Prazan
   rok znači neodređen. Bez automatskog brisanja, ljudski pregled i arhiva imaju
   bezbedne početne vrednosti; potvrdite stvarno odobrenu politiku. „Registruj politiku
   čuvanja“ ne dodeljuje je izvoru; dodela je u governance profilu.
4. **Retencija:** izaberite tačnu verziju i učitajte stanje. Proverite početak/rok,
   hold, purge status, reviziju i tombstone. Osvežavanje uklanja prethodne potvrde.
5. **Hold:** uz referencu i potvrdu „Postavi hold“ blokira purge. „Ukloni hold“ zahteva
   potvrdu i važeću reviziju. Zahtev za operativni pregled purge-a samo menja evidenciju.
   Odobravanje/izvršavanje fizičkog brisanja su zasebni operator API postupci sa
   postojećim step-up i retention proverama. Ovaj ekran ne briše sadržaj; automatska
   arhiva nije implementirana i nove kopije su odložene u preproduction radu.
6. **Predlog anonimizacije:** izlaz najpre proizvedite odobrenom metodom u drugom
   izvoru istog scope-a. Učitajte izlazne verzije, izaberite izlaz, unesite metodu/verziju/
   parametre/dokaz i ciljnu klasifikaciju/privatnost. Potvrdite i registrujte predlog.
   Platforma beleži evidence; ne izvršava anonimizaciju i ne certifikuje metodu.
7. **Pregled:** učitajte evidenciju (50 zapisa po strani), izaberite PROPOSED predlog,
   proverite ulaz/izlaz/metodu/reference/target kategorije. Izaberite VERIFIED ili
   REJECTED, navedite referencu i potvrdu. Backend zaključava zapis i dozvoljava samo
   jednu konačnu odluku. VERIFIED ID može biti dokaz za governance promenu kada svi
   backend uslovi i izvor izlaza odgovaraju.
8. **Izvoz:** navedite svrhu, potvrdite izabranu verziju i pripremite dozvoljeni izvoz.
   Samo uspešan backend odgovor sa manifestom daje dugme za preuzimanje. Privatnost,
   politika, hold i purge mogu blokirati. Osetljivi izvoz traži governance dozvolu i
   stvarni MFA assurance; potvrda lozinke ga ne zamenjuje. MFA provajder još nije potvrđen.
9. **Greške i oporavak:** posle prekida veze ili „Registrovano“ osvežite evidenciju.
   Stara revizija/već pregledan dokaz/povučeni sadržaj zahtevaju novi pregled. Ne
   unosite kredencijale ili privatne tekstove u reference. Nema zaobilaženja zabrana.
10. **Evidencija i granice:** audit beleži ID/status/reference bez raw payload-a;
    eksport ima manifest, purge ima tombstone/invalidation. Ovo nije pravni savet,
    institucionalna validacija ili odobrenje AI analize. Popunjene sintetičke slike i
    Word parity30E; završni acceptance/deployment30F. SMTP ostaje pending.
