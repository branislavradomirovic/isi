# ISI Privacy Notice

**Status: DRAFT — NOT APPROVED FOR PUBLICATION**
**Prepared:** 4 October 2026
**Language:** Serbian Latin (controlling draft); English is a working translation.
**Scope:** Public ISI website and the ISI platform, including SIMPA and ORDO, only to the extent confirmed by the final processing map and institutional agreements.

> This is a drafting aid, not legal advice. Bracketed items and the release checklist are blockers. Do not publish until ISI verifies the live processing environment, controller/processor roles, recipients, retention, and contact details and completes legal review.

## Serbian (Latin)

### Obaveštenje o privatnosti i obradi podataka o ličnosti

**Datum stupanja na snagu:** [POTVRDITI DATUM]
**Izdanje:** [POTVRDITI VERZIJU]

#### 1. Ko obrađuje podatke

Rukovalac podacima za **[POTVRDITI konkretne svrhe i sisteme]** je **[POTVRDITI puni registrovani naziv]**, sa sedištem **[POTVRDITI registrovanu adresu]**, kontakt **[POTVRDITI zvanični kontakt za privatnost]** (u ovom obaveštenju: „ISI“ ili „mi“). Opšti javni kontakt prikazan na sajtu je institutzasocijalnuinkluziju@gmail.com; potvrditi da li je to odgovarajući kanal za zahteve u vezi sa podacima.

Za naloge i organizacione radne prostore u SIMPA/ORDO može postojati više uloga: organizacija korisnika može određivati svrhe i sredstva obrade podataka koje unosi, dok ISI može pružati platformu i obrađivati takve podatke po dokumentovanim uputstvima. **Ova podela nije pravno potvrđena za produkciju.** Pre objave utvrditi uloge po svakoj obradi, ugovore sa organizacijama i kontakt za lica čiji se podaci unose u radni prostor.

#### 2. Na koje obrade se ovo odnosi

Ovo obaveštenje razlikuje:

1. **Javni sajt** — pregled javnih stranica, indeksa dokumenata i biblioteke, jezičkih ruta i statičkih resursa.
2. **Nalozi i bezbednost platforme** — pozivni pristup ISI aplikaciji, autentifikacija, oporavak naloga, sesije, bezbednosni događaji i podrška.
3. **Podaci organizacija u SIMPA/ORDO** — podaci koje institucije i ovlašćeni korisnici unose ili generišu u svojim odvojenim radnim prostorima. Obrada može obuhvatati lične podatke i, zavisno od institucionalne namene i zakonitog osnova, posebne kategorije podataka. Za svaku takvu obradu potrebni su posebni ugovorni i informativni dokumenti odgovarajućeg rukovaoca.

Produkcioni opseg javnog sajta, aplikacije, API-ja, hosting logova i podrške mora biti potvrđen pre objave ovog obaveštenja.

#### 3. Podaci, svrhe i pravni osnov

Sledeća tabela je nacrt zasnovan na repository as-built kodu. Ona **ne potvrđuje** šta se trenutno izvršava na serveru. ISI mora povezati svaku svrhu sa tačnim pravnim osnovom iz Zakona o zaštiti podataka o ličnosti i utvrditi da li postoje dodatne svrhe.

| Grupa | Podaci koji su vidljivi u as-built aplikaciji | Svrha | Pravni osnov i rok |
|---|---|---|---|
| Posetioci javnog sajta | Zahtev i tehnički metapodaci mogu nastati na web/proxy nivou; tačan skup nije potvrđen | Dostava stranica, zaštita dostupnosti i otklanjanje grešaka | **[POTVRDITI logove, pravni osnov i stvarni rok čuvanja]** |
| Pozvani korisnički nalozi | E-mail adresa, prikazno ime, verifikacija e-maila, podatak o aktivnom nalogu; lozinka se čuva kao hash | Identifikacija pozvanog korisnika, autentifikacija i dodela pristupa | **[POTVRDITI pravni osnov, ko je rukovalac i rok nakon prestanka naloga]** |
| Sesije i zaštita naloga | Vreme kreiranja/isteka/ukidanja sesije, hash tokena, hash IP adrese i user-agent-a i oznaka uređaja; model čuva polja za IP/user-agent, ali implementacija sesije ih trenutno postavlja na prazno | Održavanje sesije, zaštita naloga, prikaz i opoziv sesija | **[POTVRDITI produkcionu konfiguraciju, pristup i rok čuvanja]** |
| Pozivi, oporavak i autentifikaciona bezbednost | E-mail pozvanog lica, status/vreme poziva, hash i rok jednokratnog tokena; ograničeni bezbednosni identifikatori/događaji | Pozivanje korisnika, potvrda e-maila, reset lozinke, prevencija zloupotrebe i audit | **[POTVRDITI SMTP provajdera, pravni osnov, retenciju i brisanje]** |
| Podaci radnih prostora SIMPA/ORDO | Sadržaj i metapodaci koje ovlašćena organizacija unese; kod podržava klasifikaciju, privacy kategoriju, izvore i izvedene evidencije | Pružanje odobrenih institucionalnih funkcija, upravljanje podacima i sledljivost | **[POTVRDITI uloge rukovaoca/obrađivača, kategorije, svrhe, osnove, upotrebu AI-ja i rokove po ugovoru]** |

Ne unositi u konačno obaveštenje pravni osnov poput saglasnosti, ugovora ili legitimnog interesa dok rukovalac ne dokumentuje da se on zaista primenjuje na konkretnu svrhu. Lozinke, tokeni, tajne i sadržaj akreditiva ne treba opisivati kao podatke dostupne ISI osoblju bez potvrde stvarnog pristupa i tehničkih kontrola.

#### 4. Obaveznost davanja podataka

Pozivni e-mail i podaci neophodni za nalog potrebni su za pristup zatvorenoj platformi; bez njih nalog ne može biti uspostavljen ili korišćen. **[POTVRDITI tačan skup obaveznih polja i pravne posledice.]** Pregled javnih stranica ne zahteva kreiranje naloga prema trenutnom dizajnu, ali web-server obrada zahteva i dalje mora biti proverena.

#### 5. Kolačići i slične tehnologije

Repository pregled nije potvrdio analitičke ili reklamne skripte u javnim ISI šablonima i statičkim JavaScript fajlovima. To samo po sebi ne dokazuje stanje produkcionog servera, proxy sloja, aplikacije ili spoljnog sadržaja. Pre objave proveriti `Set-Cookie` zaglavlja i browser storage na javnim i autentifikovanim rutama, kao i sve ugrađene resurse.

**[POTVRDITI konačan inventar kolačića/lokalne memorije, naziv, izdavaoca, svrhu, trajanje, kategoriju i saglasnost ili drugi osnov.]** Ako postoje samo tehnologije neophodne za traženu funkciju, jasno ih navesti. Ako postoje opciona analitika ili marketing, opisati izbor korisnika i mehanizam prethodne saglasnosti gde je potreban; ne tvrditi „ne koristimo kolačiće“ dok provera nije završena.

#### 6. Primaoci i obrađivači

Pristup mogu imati ovlašćeni radnici i pružaoci usluga samo kada je to potrebno za hosting, održavanje, isporuku autentifikacionih poruka, bezbednost, rezervne kopije ili podršku. Trenutni produkcioni provajderi, lokacije, podobrađivači, ugovori i pristup osoblja **nisu potvrđeni**.

**[POTVRDITI pravna lica/provajdere, njihove uloge i svrhe, lokacije podataka, ugovore o obradi, eventualne podobrađivače i pristupe iz inostranstva.]** Ne navoditi MinIO, PostgreSQL, Redis ili SMTP kao spoljne primaoce samo zato što ih repository podržava; proveriti stvarno hostovanje i administratora svake usluge.

#### 7. Prenos u druge države

**[POTVRDITI da li se podaci ili pristup podacima prenose van Srbije; navesti države i odgovarajuće garancije ako postoje.]** Ne tvrditi da podaci ostaju u Srbiji dok se ne provere lokacija hostinga, rezervne kopije, podrška i svi podobrađivači.

#### 8. Rokovi čuvanja

Podatke čuvamo samo onoliko koliko je potrebno za dokumentovane svrhe ili koliko nalaže zakon. Konkretni rokovi se ne mogu potvrditi iz javno dostupnog repository stanja.

**[POTVRDITI rokove/pravila za: web-server i proxy logove; neaktivne i ugašene naloge; aktivne/opozvane sesije; pozive i jednokratne tokene; bezbednosne događaje i rate-limit zapise; rezervne kopije; podatke i izvedene zapise radnih prostora; e-mail podršku i zahteve lica.]** Navesti okidač za početak roka, automatsko brisanje ili anonimizaciju, izuzetke zbog pravnih zahteva i kako se uklanjaju podaci iz rezervnih kopija.

#### 9. Bezbednost

ISI koristi kontrolu pristupa, izolaciju organizacija i proizvoda, ograničene bezbednosne evidencije i upravljanje sesijama u skladu sa relevantnim funkcijama platforme. Tehnička dokumentacija opisuje izbegavanje sirovih tela zahteva, tajni, tokena, sadržaja upita i identifikatora u telemetriji. Produkcione mere, kontrola privilegovanog pristupa, šifrovanje u prenosu/mirovanju, nadzor, odgovor na incidente, testovi oporavka i trenutne konfiguracije **moraju se potvrditi u ISI-28** pre bilo kakve tvrdnje o njihovom radu.

#### 10. Prava lica

U zavisnosti od konkretnog pravnog osnova i uslova iz zakona, možete zatražiti potvrdu obrade, pristup, kopiju, ispravku, brisanje, ograničenje, prenosivost ili uložiti prigovor; kada je obrada zasnovana na saglasnosti, saglasnost se može povući za buduću obradu. Možete podneti pritužbu Povereniku za informacije od javnog značaja i zaštitu podataka o ličnosti Republike Srbije.

Zahtev pošaljite na **[POTVRDITI zvanični kanal i poštansku adresu]**. ISI može tražiti razumnu proveru identiteta i odgovoriti u zakonskom roku. Ako organizacija korisnika određuje obradu unetih podataka, zahtev u vezi sa tim podacima usmeriti i tom rukovaocu. Konačni tekst treba da objasni kome se zahtev upućuje za svaku kategoriju podataka i kako se proverava identitet bez prikupljanja viška podataka.

#### 11. Lice za zaštitu podataka

**[UTVRDITI da li je ISI po zakonu dužan da odredi lice za zaštitu podataka. Ako jeste, objaviti službene kontakt podatke. Ako nije, ne predstavljati opšti kontakt kao imenovano lice.]**

#### 12. Deca

Javni portal je informativan. Nije potvrđeno da li su određene usluge namenjene maloletnicima ili da li se u radnim prostorima obrađuju podaci dece. **[POTVRDITI ciljnu publiku i pravila za naloge/podatke dece; posebne obrade proceniti zasebno.]**

#### 13. Izmene i kontakt

Važeće izdanje i datum primene biće objavljeni na ovoj stranici. Za pitanja i zahteve u vezi sa privatnošću kontaktirajte **[POTVRDITI zvanični privacy kontakt i adresu rukovaoca]**.

---

## English (working translation)

### Privacy Notice and Personal Data Processing

**Effective date:** [CONFIRM DATE]
**Version:** [CONFIRM VERSION]

#### 1. Who processes personal data

The controller for **[CONFIRM specific purposes and systems]** is **[CONFIRM full registered legal name]**, registered office **[CONFIRM registered address]**, contact **[CONFIRM official privacy contact]** (“ISI” or “we”). The general contact shown on the Website is institutzasocijalnuinkluziju@gmail.com; confirm whether it is an appropriate channel for data-rights requests.

For accounts and organizational workspaces in SIMPA/ORDO, roles may differ: a customer organization may determine the purposes and means for data it enters, while ISI may provide the platform and process that data under documented instructions. **This allocation has not been legally confirmed for production.** Before publication, determine roles for each processing activity, customer agreements, and the contact for people whose data is entered into a workspace.

#### 2. Processing covered

This notice separates: (1) the public website; (2) platform accounts and security, including invitation access, authentication, account recovery, sessions, security events, and support; and (3) organizational data in SIMPA/ORDO workspaces. The latter may include personal data and, depending on the institutional purpose and lawful basis, special categories of personal data. Each such processing activity needs the appropriate controller’s separate contractual and privacy documentation.

The production scope of the website, application, API, hosting logs, and support must be confirmed before publication.

#### 3. Data, purposes, and legal basis

The table below is a draft based on repository as-built code. It **does not confirm** what currently runs on the server. ISI must map each purpose to the precise lawful basis under the Serbian Law on Personal Data Protection and determine whether additional purposes exist.

| Group | Data visible in as-built application | Purpose | Lawful basis and retention |
|---|---|---|---|
| Public-site visitors | Request and technical metadata may arise at web/proxy level; exact set unconfirmed | Deliver pages, protect availability, troubleshoot | **[CONFIRM logs, basis, and actual retention]** |
| Invited user accounts | Email, display name, email verification and active-account state; password stored as a hash | Identify invited users, authenticate, grant access | **[CONFIRM lawful basis, controller, and post-account retention]** |
| Sessions and account security | Session creation/expiry/revocation, token hash, IP and user-agent hashes, device label; model has IP/user-agent fields, but current session implementation sets them empty | Maintain sessions, protect accounts, display and revoke sessions | **[CONFIRM production configuration, access, and retention]** |
| Invitations, recovery, and authentication security | Invitee email, invitation status/time, one-time token hash/expiry; bounded security identifiers/events | Invite users, verify email, reset passwords, prevent abuse, audit | **[CONFIRM SMTP provider, basis, retention, and deletion]** |
| SIMPA/ORDO workspace data | Content and metadata entered or generated by an authorized organization; code supports classification, privacy categories, source lineage, and derived records | Provide authorized institutional functions, govern data, preserve traceability | **[CONFIRM controller/processor roles, categories, purposes, bases, AI use, and contractual retention]** |

Do not state consent, contract, or legitimate interests as the lawful basis until the controller documents that it applies to the specific purpose. Do not describe credentials/tokens as accessible to ISI staff without confirming actual access and controls.

#### 4. Is data required?

An invited email and data required for an account are necessary for restricted-platform access; without them an account cannot be created or used. **[CONFIRM exact required fields and consequences.]** Browsing public pages currently requires no account, but web-server request processing must still be verified.

#### 5. Cookies and similar technologies

Repository review did not confirm analytics or advertising scripts in the public ISI templates and static JavaScript files. This alone does not establish the production server, proxy, application, or embedded-content behavior. Before publication, inspect `Set-Cookie` headers and browser storage on public and authenticated routes, as well as embedded resources.

**[CONFIRM the complete cookie/local-storage inventory, name, provider, purpose, duration, category, and consent or other basis.]** Identify technologies strictly necessary for a requested function. If optional analytics or marketing is used, explain user choice and prior consent where required. Do not claim “we do not use cookies” before completing the inspection.

#### 6. Recipients and processors

Authorized personnel and service providers may need access for hosting, maintenance, authentication email, security, backups, or support. Current production providers, locations, subprocessors, contracts, and staff access are **unconfirmed**.

**[CONFIRM legal entities/providers, roles and purposes, data locations, processing agreements, subprocessors, and foreign access.]** Do not identify PostgreSQL, Redis, MinIO, or SMTP as external recipients merely because the repository supports them; verify actual hosting and administration.

#### 7. International transfers

**[CONFIRM whether data or access is transferred outside Serbia; identify countries and safeguards if applicable.]** Do not claim data remains in Serbia until hosting, backups, support, and subprocessors are checked.

#### 8. Retention

We retain data only as long as needed for documented purposes or as required by law. Specific periods cannot be confirmed from the publicly available repository state.

**[CONFIRM rules/periods for web/proxy logs; inactive and closed accounts; active/revoked sessions; invitations and one-time tokens; security events and rate-limit records; backups; workspace/derived data; support email and rights requests.]** State the retention trigger, deletion/anonymization mechanism, legal-claim exceptions, and how backup copies expire.

#### 9. Security

The platform implements access controls, organization and product isolation, bounded security records, and session management for the relevant features. Technical documentation describes avoiding raw request bodies, secrets, tokens, prompt contents, and identifiers in telemetry. Production controls, privileged access, encryption in transit/at rest, monitoring, incident response, recovery tests, and current configuration **must be verified in ISI-28** before making claims about their operation.

#### 10. Individual rights

Depending on the specific lawful basis and statutory conditions, you may request confirmation, access, a copy, correction, erasure, restriction, portability, or object; where processing is based on consent, you may withdraw it for future processing. You may complain to the Serbian Commissioner for Information of Public Importance and Personal Data Protection.

Send requests to **[CONFIRM official channel and postal address]**. ISI may reasonably verify identity and will respond within the statutory period. If a customer organization determines processing of data entered into its workspace, requests about that data should also be directed to that controller. The final notice must say who handles each data category and how identity is checked without collecting excessive data.

#### 11. Data protection officer

**[DETERMINE whether ISI is legally required to appoint a data protection officer. If so, publish official contact details. If not, do not present a general contact as an appointed officer.]**

#### 12. Children

The public portal is informational. It is unconfirmed whether any service targets minors or whether child data is processed in workspaces. **[CONFIRM audience and account/child-data rules; assess special processing separately.]**

#### 13. Changes and contact

The current version and effective date will appear on this page. For privacy questions and requests, contact **[CONFIRM official privacy contact and controller address]**.
