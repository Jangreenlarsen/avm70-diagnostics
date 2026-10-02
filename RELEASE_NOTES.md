# Release Notes

---

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
