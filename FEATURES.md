# Features

Format: `[status] vX.X.X — beskrivelse`
Status: `planned` | `in-progress` | `done`

---

| # | Feature | Status | Version |
|---|---------|--------|---------|
| 1 | **Systeminfo**: model, software-version, build-dato, hardware-version, region, Ethernet/Wi-Fi MAC, IP-styrings-/TX-status, frontpanel-lysstyrke, antal inputs og inputnavne | planned | — |
| 2 | **Runtime-data live**: zone 1/2 power, volumen, mute og input samt lydformat, kanaler, listening mode, bitrate, samplerate, video-opløsning, DRC og dialnorm. Pushes via SSE og polles som fallback | planned | — |
| 3 | **Hændelseslog**: tidsstemplet log over hver værdi-ændring (fra → til) og hvert forbindelsesskift | planned | — |
| 4 | **Rå trafik**: alle linjer sendt/modtaget med tidsstempel | planned | — |
| 5 | **Rå forespørgsel**: send en vilkårlig `KODE?` og se svaret. Kun forespørgsler; afvises i backend ellers | planned | — |
| 6 | **Probe**: spørg alle katalog-kommandoer og vis hvilke AVM70 understøtter (OK/ugyldig/zone slukket/timeout) | planned | — |
| 7 | **Forbindelsesstyring**: connect/disconnect, auto-reconnect med backoff, host/port/poll-interval kan ændres i UI'et | planned | — |
| 8 | **Fake AVM70** til test og udvikling uden den rigtige enhed | planned | — |
