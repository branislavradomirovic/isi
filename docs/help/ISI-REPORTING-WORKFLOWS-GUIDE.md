# Izveštaji i ljudski pregled

## 1. Svrha
Izveštaj čuva konkretnu verziju sadržaja sa izvorima i otiscima. SIMPA monitoring,
ORDO snapshot/scenario i povezani nalazi ostaju odvojeni po proizvodu i prostoru.

## 2. Kada se koristi
Posle pripreme podobnog sačuvanog analitičkog izvora ili prihvaćene ekstrakcije.
Prazan registar ne stvara izmišljene rezultate. Neuspešno učitavanje nije prazan registar.

## 3. Dozvole
Čitanje/izvoz zahteva report.read; kreiranje/nova verzija/slanje analysis.run;
review/publication organization.manage. Povezani izvori dodatno zahtevaju prava
za podatke, geometriju i izabrani numerički dokaz. Platformski status ne zaobilazi scope.

## 4. Postupak
Otvorite Izveštaji u tačnoj organizaciji, SIMPA ili ORDO i radnom prostoru.
Izaberite Izvor bez podrazumevanog izbora, unesite naslov i pregledajte identitet.
Za ekstrakciju unesite stvarni claim ID iz Podataka, opcioni UUID rezultata,
obrazloženje veze i izričitu potvrdu. Pregledaj povezani dokaz ponovo proverava izvor.
Potvrdite tačan naslov/izvor i Kreiraj draft izveštaj. U Registry otvorite verziju,
pročitajte sadržaj/poreklo, potvrdite pa Pošalji na review. Ovlašćeni recenzent bira
approved ili rejected, unosi Review napomena i potvrđuje odluku. Odobrenu verziju
zasebno potvrdite i Publikuj verziju. Za novu verziju izaberite kompatibilan Izvor
za novu verziju; ne pretpostavljajte da je prva stavka najnovija. Prethodna ostaje sačuvana.

## 5. Polja i statusi
draft je nacrt; in_review čeka pregled; approved je odobreno ali još neobjavljeno;
rejected je odbijeno; published je objavljeno unutar platforme; superseded je
istorijska zamenjena verzija. content SHA-256 i provenance SHA-256 označavaju
pregledani dokaz. Promena izbora, napomene, izvora/statusa poništava prethodnu potvrdu.

## 6. Primer
Sintetički zbirni nalaz za 2025. povežite sa eksplicitno izabranim sačuvanim
rezultatom. Napišite razlike perioda, jedinice i teritorije. Primer i korisničko
odobrenje nisu potvrda stvarne institucionalne istine. Datirane ilustracije prikazuju odvojene korake ovog toka.

## 7. Granice tumačenja
Prihvatanje ekstrakcije, review izveštaja i objavljivanje su različite odluke.
Objavljivanje nije javna objava, email isporuka, validacija metodologije ili nova AI analiza.
UNCALIBRATED ekstrakcija i nepodržan SHAP ostaju takvi i u izveštaju.

## 8. Greške i oporavak
Ako se pregledana verzija promeni, čuvanje se odbija sa409. Osvežite, pročitajte
aktuelan sadržaj/status/otiske, pa ponovo odlučite. Ne ponavljajte automatski
zahtev nakon mrežne greške; prvo proverite da li je operacija već sačuvana.
Povučen izvor, promenjena granica/pregled ili ukinuta prava blokiraju povezani pregled/izvoz.

## 9. Preuzimanje i privatnost
Za approved/published/superseded izaberite HTML, Markdown ili JSON i Pripremi download
artefakt. Svaki prikaz/preuzimanje ponovo proverava podobnost; nema trajnog keša
citata. Proverite Export SHA-256. Ranije preuzete kopije nije moguće udaljeno opozvati.
Delite ih samo uz ovlašćenje institucije. Izvoz PDF/DOCX izveštaja nije ponuđen ovom radnjom.

## 10. Poreklo i odgovornost
Proverite izvor/verziju, product/workspace, otiske, pregled, datum geometrije i
numerički rezultat kada postoji. Review trag čuva odluku i napomenu. Ne predstavljajte
tehnički status ili modelsku povezanost kao uzrok, preporuku ili kalibrisanu pouzdanost LLM-a.
