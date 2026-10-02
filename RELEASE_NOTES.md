# Release Notes

---

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
