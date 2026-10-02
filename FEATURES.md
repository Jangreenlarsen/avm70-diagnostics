# Features

Format: `[status] vX.X.X — beskrivelse`
Status: `planned` | `in-progress` | `done`

---

| # | Feature | Status | Version |
|---|---------|--------|---------|
| 1 | **Systeminfo**: model, software-version, build-dato, hardware-version, region, Ethernet/Wi-Fi MAC, IP-styrings-/TX-status, frontpanel-lysstyrke, antal inputs og inputnavne | done | 0.2.0 |
| 2 | **Runtime-data live**: zone 1/2 power, volumen, mute og input samt lydformat, kanaler, listening mode, bitrate, samplerate, video-opløsning, DRC og dialnorm. Pushes via SSE og polles som fallback | done | 0.2.0 |
| 3 | **Hændelseslog**: tidsstemplet log over hver værdi-ændring (fra → til) og hvert forbindelsesskift | done | 0.2.0 |
| 4 | **Rå trafik**: alle linjer sendt/modtaget med tidsstempel | done | 0.2.0 |
| 5 | **Rå forespørgsel**: send en vilkårlig `KODE?` og se svaret. Kun forespørgsler; afvises i backend ellers | done | 0.2.0 |
| 6 | **Probe**: spørg alle katalog-kommandoer og vis hvilke AVM70 understøtter (OK/ugyldig/zone slukket/timeout) | done | 0.2.0 |
| 7 | **Forbindelsesstyring**: connect/disconnect, auto-reconnect med backoff, host/port/poll-interval kan ændres i UI'et | done | 0.2.0 |
| 8 | **Fake AVM70** til test og udvikling uden den rigtige enhed | done | 0.2.0 |
| 9 | **Opsætningsmenu for AVM70-kommunikation** (Jan: *"i app skal vi have en setup menu for avm70 hvor vi sætter kom paramenter op"*): host/IP, port, poll-interval, connect-timeout, svar-timeout, auto-reconnect og auto-forbind ved opstart. Gemmes i `backend/data/settings.json`. Inkl. "Test forbindelse" der prøver uden at gemme | done | 0.2.0 |
| 10 | **Versionsmenu** (Jan: *"lave en menu med alle version info vi kan hente"*): "ℹ Versioner"-dialog med alle versions- og identitetsfelter AVM70 udleverer over IP-protokollen. Kodelisten kommer fra enhedens egen web-UI (`/js/merged.min.js`, `COMMAND`-tabellen): IDQ, GSN, GCDN, IDS (MCU), DSPIDS, LCDIDS, IDB, IDH, IDR, NMSVER, NMHVER, RVER, RBD, NMR, NMST. Dertil appens egen version, en "Opdatér"-knap (genforespørger kun versionskoderne) og "Kopiér alt" som tekst | done | 0.3.0 |
| 11 | **Engelsk brugerflade** (Jan: *"vi skal have app til kun at tale på eng."*): al tekst brugeren ser er på engelsk. Det gælder frontend, backend-fejlbeskeder, labels og værdi-afkodning i kataloget, hændelseslog og forbindelsesfejl. Projektdokumentation og kodekommentarer forbliver på dansk | done | 0.4.0 |
| 12 | **Download af alle data** (Jan: *"en mulighed for at dload alle data info du henter fra AVM70"*): én fil med alt appen har hentet. Indhold: app-version, tidspunkt, indstillinger, forbindelse, alle værdier (rå + afkodet + status + tidsstempler), seneste probe, hændelseslog og rå trafik. JSON (komplet) og CSV (værdier) | planned | — |
