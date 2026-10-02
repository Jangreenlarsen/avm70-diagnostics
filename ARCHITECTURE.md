# Arkitektur: AVM70 Diagnostics

## Principper

1. **Ingen lag må springe et lag over.** Frontend kalder kun API'et, API'et kalder kun service-laget, og kun protokol-laget taler TCP med AVM70.
2. **Kun én forbindelse til AVM70.** Enheden accepterer kun én netværksklient. `DeviceService` ejer den ene `AvmClient`, og intet andet sted i koden må åbne en socket mod enheden.
3. **Kun læsende.** Protokol-laget har en `query()`. API'ets rå-konsol afviser alt der ikke er en ren forespørgsel (`KODE?`). Afvisningen sker i backend, ikke kun i UI'et.
4. **Alle lag eksponerer kun et veldefineret interface.** Interne implementeringsdetaljer er skjulte.

---

## Lag-oversigt

```
┌──────────────────────────────┐
│  Frontend (browser)           │  frontend/  — HTML/CSS/JS, intet build-trin
└──────────────┬───────────────┘
               │ HTTP REST + Server-Sent Events (/api/events)
┌──────────────▼───────────────┐
│  API-lag                      │  app/api/routes.py
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  Service-lag                  │  app/services/device_service.py
│  (forbindelse, tilstand,      │  — reconnect, polling, hændelser,
│   polling, hændelser, probe)  │    trafiklog, probe
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│  Protokol-lag                 │  app/protocol/{catalog,parser,client}.py
└──────────────┬───────────────┘
               │ TCP 14999, ASCII, ';'-termineret
        ┌──────▼──────┐
        │   AVM 70     │   (eller app/tools/fake_avm.py under udvikling/test)
        └─────────────┘
```

---

## Lag-beskrivelse

### Lag 1 — Frontend
- **Ansvar**: Viser systeminfo, runtime-data, hændelseslog, rå trafik, rå-forespørgsel og probe-resultat. Opdateres live via SSE.
- **Filer**: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
- **Regler**: Må kun kalde `/api/*`. Viser altid backends specifikke fejlbesked (`detail`).

### Lag 2 — API
- **Ansvar**: HTTP-endpoints og SSE-strøm. Validerer input og oversætter service-fejl til HTTP-statuskoder.
- **Filer**: `app/api/routes.py`, `app/main.py` (app-opsætning og statiske filer)
- **Regler**: Ingen protokol-logik. Må ikke tale med `AvmClient` direkte.

| Metode | Sti | Formål |
|--------|-----|--------|
| GET  | `/api/info` | App-version, aktuelle og standard-indstillinger, kommandokatalog |
| GET  | `/api/state` | Fuldt øjebliksbillede: forbindelse, alle kendte værdier, seneste hændelser og trafik |
| POST | `/api/connect` | Start forbindelsen (med auto-reconnect) |
| POST | `/api/disconnect` | Stop forbindelsen |
| POST | `/api/refresh` | Genforespørg alle system- og runtime-kommandoer |
| GET  | `/api/settings` | Aktuelle kommunikationsparametre |
| PUT  | `/api/settings` | Gem parametre fra opsætningsmenuen (host, port, poll-interval, connect-/svar-timeout, auto-reconnect, auto-connect). Valideres i backend og gemmes i `data/settings.json`. Ændret host/port giver genforbindelse |
| POST | `/api/settings/test` | Test parametre uden at gemme: kortvarig forbindelse + `IDM?`/`IDS?`. Er adressen den aktive forbindelse, bruges den i stedet (kun én klient) |
| POST | `/api/settings/reset` | Tilbage til `.env`-standardværdierne |
| POST | `/api/query` | Rå forespørgsel (`{"command": "Z1VOL?"}`). Kun `?`-forespørgsler accepteres, og andet giver `400` |
| POST | `/api/probe` | Spørg alle katalog-kommandoer og rapportér hvilke AVM70 understøtter |
| GET  | `/api/events` | SSE: `state`, `value`, `connection`, `traffic`, `log`-events og heartbeat |

### Lag 3 — Service
- **Ansvar**: Én `DeviceService`-instans. Ejer forbindelsen og reconnect-løkken (backoff 2→30 s), holder værdi-tilstanden (værdi, tekst, tidspunkt for seneste svar og seneste ændring), poller runtime-kommandoer med fast interval og publicerer hændelser til SSE-abonnenter. Fører også ringbuffere for trafik og hændelseslog.
- **Filer**: `app/services/device_service.py`, `app/config.py`
- **Regler**: Må ikke åbne sockets selv. Går kun via `AvmClient`.

### Lag 4 — Protokol
- **Ansvar**: `catalog.py` er kommandokataloget (kode, beskrivelse, gruppe, værdi-opslag) og afkodning. `parser.py` splitter strømmen på `;` og klassificerer svar (værdi, fejlsvar, ukendt). `client.py` er asyncio-TCP-klienten: connect med timeout, læse-løkke, `query()` der matcher svar til forespørgsel, og callbacks for hver rå linje ind/ud og for forbindelsestab.
- **Filer**: `app/protocol/catalog.py`, `app/protocol/parser.py`, `app/protocol/client.py`
- **Regler**: Ingen viden om HTTP/SSE eller app-tilstand.

### Værktøj — Fake AVM70
- `app/tools/fake_avm.py` er en lille TCP-server, der svarer som en AVM70 og skifter lydformat med jævne mellemrum. Den bruges af testsuiten og til visuel verifikation uden den rigtige enhed (`python -m app.tools.fake_avm`).

---

## Projektstruktur

```
.
├── CLAUDE.md
├── version.json               # eneste versionskilde
├── ARCHITECTURE.md
├── FEATURES.md
├── BUGS.md
├── CHANGELOG.md
├── RELEASE_NOTES.md
├── README.md
├── AVM70_REFERENCE.md         # protokol-noter + observerede svar fra den rigtige enhed
├── run.ps1                    # opret venv + start app
├── .claude/
│   └── settings.local.json
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py            # FastAPI-app, serverer frontend/
│   │   ├── config.py          # .env + data/settings.json
│   │   ├── api/routes.py
│   │   ├── services/device_service.py
│   │   ├── protocol/          # catalog.py, parser.py, client.py
│   │   └── tools/fake_avm.py
│   └── tests/
└── frontend/                  # index.html, app.js, styles.css
```
