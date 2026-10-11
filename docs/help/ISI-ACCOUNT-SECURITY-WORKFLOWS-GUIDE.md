# Nalog, pristup i bezbednost sesija

## 1. Šta funkcija radi
Jedan ISI identitet može pristupati SIMPA i ORDO, uz zasebna prava za svaki proizvod.
Ovaj ekran prikazuje vaše sesije, potvrđuje postojeću lozinku za privilegovani rad
i omogućava eksplicitan opoziv drugih sesija. Ne menja lozinku niti dodeljuje prava.

## 2. Ulazi i preduslovi
Prijavljen nalog i važeća sesija. Za pristup proizvodu potrebni su aktivno članstvo
u organizaciji, organizacioni entitlement, aktivan pristup proizvodu, odgovarajuća
uloga/dozvola i workspace. Uloga administratora nije automatski pristup svakom proizvodu.

## 3. Izlazi i potvrde
Pregled uređaja, vremena kreiranja, aktivnosti, isteka i statusa. Uspešan opoziv daje
potvrdu i ponovo učitava pregled. HTTP204 je uspeh bez sadržaja. Greška ne znači uspeh.
Potvrda lozinke važi za trenutnu sesiju; nije drugi faktor niti potvrda institucije.

## 4. Koraci korisnika
Otvorite Bezbednost naloga. Pregledajte sesije i oznaku trenutne sesije.
Za jednu drugu aktivnu sesiju potvrdite „Potvrđujem opoziv ove druge sesije“, zatim
„Opozovi sesiju“. Za grupni opoziv pregledajte obuhvat, eksplicitno potvrdite sve druge
sesije i kliknite „Opozovi sve druge sesije“. Posle potvrde proverite novi status.
Postojeću lozinku unesite lično samo u „Trenutna lozinka“ i „Potvrdi identitet“.
Lozinku, link poziva i reset token nikada ne kopirajte u Help, izveštaj ili poruku podršci.

## 5. Polja i opseg
Opis uređaja je ograničen tekst, ne mrežni identitet. Trenutna i opozvana sesija
nemaju individualni opoziv. Grupni opoziv obuhvata sve vaše druge aktivne sesije
u trenutku izvršenja, uključujući nove otvorene posle pregleda; trenutna ostaje aktivna.
Nova inventura/status/istek/uređaj ili druga trenutna sesija poništava staru potvrdu.

## 6. Pozivanje i pristup obe aplikacije
Administrator najpre proverava članstvo, ulogu, entitlement i pristup SIMPA i ORDO.
Poziv nije aktivan nalog dok ga korisnik ne prihvati. Ne postoji javna samoregistracija.
Novi korisnik lično postavlja lozinku u postojećem obrascu poziva; postojeći identitet
može prihvatiti poziv bez nove lozinke. Posle prijave bira organizaciju, proizvod
pa workspace. Ako proizvod nedostaje, administrator proverava prava; ne pravite drugi
identitet ili administratorski zaobilazni pristup. GoraNova testni nalog mora biti
potvrđen na kontrolisanom server onboarding-u; lokalni primer nije dokaz aktivnog naloga.

## 7. Ograničenja i neizvesnost
SMTP je pending: novi email pozivi, verifikacija i reset nisu dokaz isporuke niti dostupnog
SMTP servisa. Postojeći validni jednokratni linkovi i prijava rade po svojim pravilima.
Produkcioni MFA upis/isporuka ostaju odloženi do stvarnog provajdera. Opoziv sesija
ne uklanja sačuvane domenske podatke niti menja članstvo, metodologiju ili prava.

## 8. Greške i oporavak
Ako pregled nije učitan, ne zaključujte da nema sesija. Osvežite pregled pre ponavljanja.
Posle isteka prijavite se ponovo. Ako postoji nepoznata sesija, opozovite je i obavestite
odgovornu osobu; lozinku menjajte lično kroz odobreni tok. Recovery zahtev ne otkriva
da li email nalog postoji; u pending režimu kontaktirajte administratora.

## 9. Ljudska odgovornost
Vi birate sesiju i potvrđujete posledice. Administrator upravlja pristupom proizvoda
uz najmanje potrebne dozvole. Potvrda lozinke ne zamenjuje odobrenje privilegovane
operacije. Ne delite nalog radi pristupa podacima druge institucije.

## 10. Dokazi i provera
Server ostaje autoritet za own/foreign/current granice, rokove i audit. Lokalni
sintetički testovi i snimci proveravaju GUI, ne stvarni GoraNova nalog ili institucionalno
odobrenje. Datirane ilustracije ovog toka nalaze se u detaljnom Help-u.
Stvarni pristup naloga i stanje server izdanja proveravaju se zasebno.
