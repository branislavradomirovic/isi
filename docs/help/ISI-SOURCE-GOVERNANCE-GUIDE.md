# Governance izvora i pregled karantina

1. **Svrha:** evidentirati stvarnu klasifikaciju, privatnost, svrhu, vlasništvo,
   ograničenja AI/izvoza i ljudske odluke o konfliktima zapisa.
2. **Pristup:** Podaci → izabrani izvor → Governance izvora i karantin. Proverite
   organizaciju, SIMPA/ORDO i workspace. Profil zahteva `data.read`; izmene i svaki
   pregled karantina zahtevaju `data.governance.manage`.
3. **Preduslovi:** vlasnik i odobrena svrha obrade; dokumentovana klasifikacija i
   odobrena pravila. Ne birajte vrednost radi zaobilaženja blokirane analize.
4. **Profil:** „Učitaj / osveži governance profil“ prikazuje trenutnu reviziju i
   pravila. „Izmena governance profila“ popunjava postojeće vrednosti. Menjaju se
   samo promenjena polja; revizija sprečava prepisivanje tuđe izmene.
5. **Polja:** klasifikacija/privatnost/stanje i AI/izvoz su postojeći katalozi.
   Svrha, vlasnik i obrazloženje su autorske reference. Steward je ID aktivnog
   članstva iste organizacije; politika čuvanja bira se iz aktivnih scoped politika.
   Prazno opciono članstvo/politika eksplicitno uklanja vezu kada je prethodno postojala.
6. **Potvrda i dokaz:** pregledajte sve promene, označite potvrdu i „Sačuvaj governance
   profil“. Smanjenje osetljivosti zahteva ID VERIFIED anonimizacije sa odgovarajućim
   ulazom/izlazom; slobodan tekst nije dokaz. Backend može odbiti promenu.
7. **Karantin:** učitajte listu, izaberite zapis, zatim „Učitaj zapis i aktuelni prihvaćeni
   zapis“. Uporedite identitet, oba sadržaja, lokator i razlog konflikta. Odluka nije
   dostupna pre učitavanja detalja. Ovi podaci se ne iznose u javni Help ili audit tekst.
8. **Odluka:** REJECT_INCOMING odbija dolazni zapis; ACCEPT_INCOMING je dopušten samo
   za podržan konflikt, ne za popravku nedostajućeg identiteta. Unesite referencu
   pregleda, opciono obrazloženje, potvrdu i „Registruj odluku o zapisu“. ID pregledanog
   prihvaćenog zapisa se pin-uje; promena između pregleda i odluke blokira upis.
9. **Oporavak:** „Registrovano“ znači sačuvan zahtev/odluku. Osvežite profil/listu nakon
   uspeha ili prekida veze. Osvežavanje uklanja stare potvrde. Stara revizija, povučeni
   zapis, nevažeći dokaz ili promenjen prihvaćeni zapis zahtevaju novi pregled.
10. **Granice i evidencija:** odluka o zapisu nije metodološka/institucionalna validacija
    i ne prihvata automatski odbijenu operativnu ocenu. Važe postojeći audit/lineage i
    ograničenja AI/izvoza. Čuvanje, anonimizacija i izvoz opisani su u zasebnom poglavlju.
    Datirani sintetički primeri ne potvrđuju institucionalnu validaciju. Ne unosite kredencijale u reference ili obrazloženja.
