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
