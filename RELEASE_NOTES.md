# Release Notes

---

## v0.12.0 — 2026-10-03 — Bitdybde

- Lydkortet viser nu **Bit depth** (16/24/32 bit). Den kommer også med i rapport, ændringslog og log mode, så den er nyttig ved fejlsøgning af lyd-dropouts.

## v0.11.0 — 2026-10-03 — Beskyttelse mod farlige kommandoer

- Konsollen og alle andre dele af appen nægter nu at sende AVM70's handlingskommandoer, heller ikke som forespørgsel. Det gælder fx fabriksnulstilling, firmware-opdatering, nulstilling af Wi-Fi og fejltællere, sletning af inputs samt volumen- og testtone-kommandoer. Konsollen forklarer hvorfor.

## v0.10.1 — 2026-10-03 — Rettet visning af lydkanaler

- **Rettet**: "Input channels" viste forkert tekst. Atmos blev vist som "7.1 channels", 7.1 som "6.1 channels", og DTS:X som "Atmos". Appen bruger nu Anthems officielle tabel for AVM 70. Den rå værdi stod hele tiden korrekt ved siden af. Gamle rapporter og logfiler kan derfor have forkert kanaltekst.
- DTS:X genkendes nu som lydformat, og 4K60 vises som "4K60" i stedet for "4K".

## v0.10.0 — 2026-10-03 — Kommando-kolonne i log mode

- Log mode har fået en kolonne med selve kommandoen og dens retning:
  - `POLL Z1AIF?` er det appen spurgte AVM70 om.
  - `PUSH Z1AIF5` er det AVM70 selv sendte.
  - `POLL 48 commands` står ved en hel poll-runde.
- Forklaringen står bagefter som før. Filen har nu kolonneoverskrifter.
- Rettet: INIT-linjen kunne mangle i appens visning af log mode, selvom den stod i filen.

## v0.9.0 — 2026-10-03 — Systemejer

- Rapporten, ændringsloggen og log mode-filen oplyser nu øverst **"System owner: Jan Green Larsen"**. Det samme står i versionsmenuen.
- Ejeren kan ændres i **⚙ Setup → General**.

## v0.8.0 — 2026-10-03 — Log mode

- Ny fane **Log mode**. Når log mode slås til, polles *alle* parametre med et fast interval (standard 5 s):
  - Første gang skrives **INIT** med alle parametre og deres værdier.
  - Derefter kommer én **OK**-linje pr. poll, hvis alt svarede og intet ændrede sig.
  - Har en parameter ændret sig, logges **CHANGE** med fra → til i stedet.
  - Svarer nogle parametre ikke, logges **INCOMPLETE** med hvilke.
  - Ændringer som enheden selv sender imellem to polls logges som **PUSH** med deres præcise tid.
- Loggen skrives løbende til en fil, mens den kører, så intet går tabt hvis appen lukkes. **Save to file** gemmer en kopi.
- Poll-intervallet ændres i **⚙ Setup → Log mode** (2–3600 s) og træder i kraft med det samme.
- "● REC" i fanen viser, at log mode er aktiv. Mens den kører, erstatter den den normale polling.

## v0.7.0 — 2026-10-03 — Ændringslog

- Ny fane **Change log**. Når appen har forbundet og læst alt, gemmes et øjebliksbillede af alle værdier ("Initial values"). Derefter logges kun ændringer, med tid i millisekunder, fra → til og om ændringen kom fra enheden selv (push) eller blev fundet ved polling.
- Tabt og genoprettet forbindelse markeres i loggen, så det er tydeligt når en ændring kan være sket mens forbindelsen var nede.
- **Save to file** gemmer loggen som tekstfil, fx `AVM70_changelog_ALP2000256N070_20261003-003000.txt`. **Start new log** starter forfra med et nyt øjebliksbillede.

## v0.6.0 — 2026-10-03 — Selvstændig Windows-app

- **`AVM70Diagnostics.exe`**: dobbeltklik, og appen åbner i sit eget vindue. Den kræver ingen Python og ingen browser.
- Lukkes vinduet, stopper appen og frigiver AVM70-forbindelsen.
- Der kan kun køre én kopi ad gangen, og en kopi nummer to viser en besked. AVM70 tager kun én klient.
- **⬇ Report** åbner nu en "Save As"-dialog, så du selv vælger hvor rapporten gemmes. Standard er Overførsler.
- Indstillinger og log ligger i `%LOCALAPPDATA%\AVM70 Diagnostics\`.
- Rettet: `run.ps1` kunne ikke køre i Windows PowerShell på grund af danske tegn (BUGS.md #1).

## v0.5.0 — 2026-10-02 — Diagnoserapport til Anthem support

- **⬇ Report** i topbjælken henter en tekstfil, fx `AVM70_ALP2000256N070_20261002-234531.txt`, som kan sendes direkte til Anthem.
- Rapporten er på engelsk og indeholder: identifikation og serienummer, alle firmware-versioner, netværk, inputs, aktuel status for zoner, lyd og video, probe-resultat (hvis kørt), hændelseslog og rå protokol-trafik.
- Har appen forbindelse, spørges enheden igen lige før eksport, så tallene er friske. Uden forbindelse eksporteres de senest kendte værdier, og rapporten skriver det tydeligt.

## v0.4.0 — 2026-10-02 — Engelsk brugerflade

- Hele appen taler nu engelsk: menuer, knapper, labels, værdier, fejlbeskeder og hændelseslog.

## v0.3.0 — 2026-10-02 — Versionsmenu

**Nyt:**
- **ℹ Versioner** i topbjælken viser alle versionsoplysninger fra AVM70:
  - Enhed: samlet identifikation, serienummer, MCU-, DSP- og LCD-controller-version, build-dato, hardware-version og region.
  - Netværksmodul: software, hardware, release-version og netværksforbindelse.
  - Desuden appens egen version.
- **Kopiér alt** lægger det hele på udklipsholderen som tekst, også fra mobilen. **Opdatér** spørger kun enheden om versionerne igen.
- Systemkortet viser nu også enhedsnavn ("AVM70 BIO") og netværksforbindelse (Wi-Fi/kabel).

## v0.2.0 — 2026-10-02 — Første version af AVM70 Diagnostics

Start med `.\run.ps1`. Appen åbner på http://127.0.0.1:8070 og forbinder automatisk til AVM70.

**Nyt:**
- **Systeminfo**: model, software-version og build-dato, hardware-version, region, Ethernet- og Wi-Fi-MAC, IP-status-udsendelse, frontpanel-lysstyrke og alle inputs med navn og rumkorrektion.
- **Runtime-data live**: power, volumen, mute og input for zone 1 og 2, samt lydformat, kanaler, listening mode, samplerate, bitrate, dynamik, dialog-normalisering og video-opløsning. Ændringer fra enheden vises med det samme. Polling fanger det, enheden ikke selv sender.
- **Hændelseslog** med tidsstempel (ms), fra → til og kilde (push/poll), så timing kan aflæses.
- **Rå trafik**: alt der sendes og modtages, med push-beskeder fremhævet.
- **Konsol**: send en vilkårlig forespørgsel, fx `IS4IN?`. Appen er kun læsende, og andet afvises.
- **Probe**: viser hvilke kommandoer AVM70 understøtter. Alle 37 svarer på din enhed.
- **⚙ Opsætning**: host/IP, port, poll-interval, connect-timeout, svar-timeout, auto-reconnect og auto-forbind ved start. Med "Test forbindelse" og "Standardværdier".

**Kendt**: AVM70 tager kun én netværksklient ad gangen. Kører Movie databases AVM70-diagnostik eller Anthem-appen samtidig, kan der ikke forbindes.

## v0.1.0 — 2026-10-02 — Projektinitialisering

Projektstruktur og dokumentation oprettet.

**Næste skridt**: Første version af diagnostik-appen med systeminfo og runtime-data live.
