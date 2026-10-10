# Radni kontekst i ORDO scenariji

Status: lokalni ISI-30A kandidat; nije novo objavljeno izdanje. Prikaz ekrana i
Word dopuna ostaju pending dok browser provera ne bude dostupna.

## Radni kontekst

1. Prijavite se svojim institucionalnim nalogom.
2. U bočnom meniju izaberite organizaciju, SIMPA ili ORDO i radni prostor.
3. Proverite naziv organizacije/proizvoda/prostora iznad sadržaja pre svakog unosa.
4. Otvorite željenu funkciju; prikazuju se samo dozvoljene i podržane stavke.
5. Ako je administrator promenio pristup, izaberite **Osveži pristup**.

Promena konteksta i osvežavanje pristupa odbacuju nezavršene unose. Pre prelaska
sačuvajte rad postojećim dugmetom u obrascu. Odjava čisti lokalno stanje sesije;
backend određuje trajanje i opoziv pristupa. Na telefonu otvorite bočni meni
ugrađenim dugmetom u zaglavlju. Tastaturom koristite Tab/Shift+Tab i Enter/Space.

| Polje/radnja | Značenje |
|---|---|
|Organizacija|Institucija u čijem kontekstu radite; ne spaja podatke drugih institucija|
|Proizvod|SIMPA ili ORDO, prema dodeljenom pristupu|
|Radni prostor|Izdvojeni kontekst rada i podataka unutar proizvoda|
|Osveži pristup|Ponovo učitava serverom odobreni pristup; ne dodeljuje novu ulogu|
|Odjavi se|Opoziva tekuću sesiju kada je usluga dostupna i čisti lokalne unose|

Ako nemate radni prostor ili funkciju, kontaktirajte administratora. Ako je
usluga nedostupna, pokušajte ponovo kada se veza obnovi; ne menjajte organizaciju
da biste zaobišli ograničenje. Primer: sintetički reviewer prelazi sa ORDO
prostora A na B, prethodni tekst obrasca se odbacuje, a operacije koriste B.
Ovaj vodič ne dodeljuje dozvole i ne potvrđuje stanje institucionalnih podataka.

## Scenariji — ORDO

**Šta/kada:** planiranje razvojnih pravaca i pregled osnove u dokazima. Scenario
beleži pretpostavke i mere; nije prognoza, uzročna procena ni automatska preporuka.
SIMPA nema odobrenu scenario funkciju; praćenje sistema ostaje u njenim zasebnim
monitoring/analitičkim tokovima.

**Dozvole:** pregled koristi postojeći `analysis.read`, pisanje/status/pregled
procene postojeći `analysis.run`. Server ponovo proverava organizaciju i prostor.
Te dozvole nisu potvrda stručne kompetencije niti metodološke validacije.

1. Izaberite ORDO radni prostor pa **Scenariji**.
2. Pregledajte ciljeve. Ako imate dozvolu, u **Novi razvojni cilj** unesite kod,
   naziv, opis i fokus, zatim sačuvajte.
3. U **Novi scenario** izaberite cilj, naziv i opis; svaku pretpostavku i meru
   unesite u zaseban red. Sačuvajte scenario.
4. U Podacima pripremite validiran analitički izvor; u Analitici sačuvajte snimak.
   Samo trenutno prihvatljiv snimak može podržati novu procenu.
5. U **Evidence-only procena scenarija** izaberite scenario i snimak, pa kreirajte
   procenu. Nedostatak snimka ostaje vidljiv; sistem ne izmišlja podatke.
6. Pregledajte sačuvanu procenu: poreklo, ograničenja i `NOT_ESTIMATED`.
7. U **Status scenarija** izaberite novi status i lično potvrdite promenu.
8. U **Stručni pregled procene** izaberite procenu i odluku, napišite obrazloženje,
   potvrdite pregled izvora i sačuvajte. Ne potvrđujte bez čitanja dokaza.

|Polje/status|Značenje|
|---|---|
|draft|Uneti nacrt scenarija|
|review_ready|Autor označava spremnost za stručni pregled|
|accepted/rejected|Zabeležen stav o scenariju, ne validacija modela ili efekta|
|reviewed/rejected procena|Sačuvan stručni pregled procene i njegov obrazloženi stav|
|NOT_ESTIMATED|Uticaj nije izračunat; ne znači nula i nije prognoza|
|Snimak/izvor|Verzionisana osnova procene, sa identitetom i otiskom sadržaja|

**Primer:** sintetički cilj „Proveriti osnove plana mobilnosti“ ima scenario sa
jasno označenim pretpostavkama. Stručnjak povezuje raspoloživi snimak i proverava
nedostajuće dokaze; ne upisuje izmišljeni procenat poboljšanja.

**Greške/oporavak:** bez cilja prvo sačuvajte cilj; bez snimka vratite se u
Podatke/Analitiku; bez potvrde ili obrazloženja obrazac ne šalje pregled. Ako je
izvor povučen ili pristup promenjen, ponovo pregledajte važeću osnovu; ne vraćajte
zastareli identitet. Ako veza prekine nakon čuvanja, prvo osvežite listu pre
ponavljanja radnje. Status nije automatski odobrenje objavljivanja izveštaja.

**Privatnost/provenance:** ne unosite tajne ili lične podatke u scenario. Poreklo
snimka, metodologija, rezultat i ljudski pregled ostaju zasebni. Generativni tekst
ne menja numerički autoritet. Granice izvora, institucije i proizvoda se čuvaju.
