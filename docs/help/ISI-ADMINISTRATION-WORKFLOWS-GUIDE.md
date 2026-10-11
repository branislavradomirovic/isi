# ISI — administracija i sesije članova

## 1. Namena
Upravljanje postojećim članstvom, pristupom proizvodu, rolama, pozivima i radnim
prostorima. Administrator organizacije nije platformski superadministrator.

## 2. Kontekst i ovlašćenja
Izaberite organizaciju i SIMPA ili ORDO → Administracija. members.read/man­age,
workspace.manage, organization.manage i audit.read su odvojena ovlašćenja.
Pravo organizacije na proizvod (entitlement) ostaje read-only.

## 3. Pregled članova
Tabela prikazuje ime, email, status, pristup tekućem proizvodu i scope role.
Izaberite konkretnog člana; nema unapred odabranog cilja. Pregled se dobija sa
servera pri svakom prikazu. Potvrda se poništava kad se pregled ili kontekst promeni.

## 4. Status članstva i pristup
Status active/suspended utiče na celu organizaciju i oba proizvoda. Product access
utiče samo na izabrani proizvod. Odaberite željeno stanje, pregledajte cilj,
potvrdite promenu i sačuvajte. Server štiti poslednjeg administratora.

## 5. Role
Odaberite rolu i scope product/organization; organizacioni scope zahteva šire
ovlašćenje i važi za celu organizaciju. Dodela i svako uklanjanje imaju zasebnu
potvrdu. Bez product access-a product rola ne daje pristup. Role ne menjaju entitlement.

## 6. Sesije člana
Organization-wide members.manage može eksplicitno učitati bezbedne metapodatke
sesija. Nema tokena, cookie-ja, IP adresa ni sirovih browser podataka. Odaberite
aktivnu sesiju, potvrdite njen ID i opozovite je. Osvežavanje poništava odabir i
potvrdu. Server ponovo proverava cilj, ovlašćenja i postojeći MFA/assurance zahtev.
Sopstvene sesije koristite u ličnom nalogu. Globalne sesije člana više organizacija
nisu podržane ovde. Blokirana dodatna autentifikacija se ne zaobilazi.

## 7. Pozivi
Unesite email, eksplicitnu početnu product rolu i potvrdu. Organization_admin
nije ponuđen kao početna rola poziva. SMTP je pending do konfiguracije; razvojni
poziv nije potvrda email isporuke niti aktivnog naloga. Tajni token se ne prikazuje
u administrativnom pregledu. Pending poziv se može zasebno potvrđeno opozvati.
Lozinku lično postavlja vlasnik naloga kroz odobreni jednokratni onboarding.

## 8. Radni prostor i organizacija
Unesite naziv i jedinstven slug, pa potvrdite kreiranje. Arhiviranje/reactiviranje
zahteva zasebnu potvrdu cilja. Promena naziva organizacije zahteva organization-wide
ovlašćenje i utiče na oba proizvoda. Slug/status organizacije nisu izmenjivi ovde.

## 9. Greške i oporavak
Neuspeh ostaje vidljiv; ne prikazuje se uspeh i nema automatskog retry-ja.
Posle prekida mreže prvo proverite aktuelan pregled: promena je možda sačuvana.
Dupli slug, neaktivno pravo organizacije, poslednji admin i dodatna autentifikacija
imaju jasnu poruku. Greške ne prikazuju sirovi response niti unesene tajne.

## 10. Dokaz i ograničenja
Uspeh prikazuje potvrdu i resetuje prethodne odluke. Audit pokazuje postojeći
append-only administrativni trag prema ovlašćenjima. Sve promene ostaju
serverski autorizovane. Sintetički QA nije dokaz produkcione administrativne promene.
Popunjene ilustracije i Word parity ostaju30E; SMTP, realni MFA i institucionalna
operativna spremnost ne proglašavaju se završenim na osnovu ovog GUI koraka.
