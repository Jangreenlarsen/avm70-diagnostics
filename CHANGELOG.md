# Changelog

Nyeste øverst. Format: `## [version build NNNN] — YYYY-MM-DD — beskrivelse`

---

## [0.3.0 build 0003] — 2026-10-02 — Versionsmenu med alle versionsoplysninger fra AVM70

FEATURES.md #10. Kodelisten kommer fra AVM70's egen web-UI (`http://10.1.1.7/js/merged.min.js`, `COMMAND`-tabellen) og er verificeret mod den rigtige enhed.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: ny gruppe `version` (IDQ, GSN, IDS, DSPIDS, LCDIDS, IDB, IDH, IDR, NMSVER, NMHVER, RVER, RBD, NMR). IDS/IDB/IDH/IDR er flyttet hertil fra System. System har fået GCDN (enhedsnavn) og NMST (netværksforbindelse). Ny `STATIC_GROUPS`
- `backend/app/services/device_service.py`: `refresh(group)`, så én gruppe kan genforespørges for sig
- `backend/app/api/routes.py`: `POST /api/refresh?group=…` med validering af gruppenavn
- `backend/app/tools/fake_avm.py`: svarer på de nye koder med værdier fra den rigtige enhed
- `backend/tests/`: 11 nye tests (parsing af versionskoder, inkl. NMST vs. NMSVER og tomt RBD-svar; gruppe-opdatering spørger kun versionskoderne; ukendt gruppe → 400)
- `frontend/index.html`, `app.js`, `styles.css`: "ℹ Versioner"-knap og -dialog med sektionerne app, enhed og netværksmodul, "Opdatér" og "Kopiér alt". Kopiering falder tilbage til `execCommand`, når siden ikke kører i en secure context (fx fra mobilen via `http://10.1.1.50:8070`). Versionsgruppen vises ikke som kort på forsiden
- `AVM70_REFERENCE.md`: versionskoder, web-UI'ets JSON-API og en advarsel om handlings-koder

## [0.2.0 build 0002] — 2026-10-02 — Diagnostik-app: systeminfo, runtime-data live og opsætningsmenu

Første funktionelle version (FEATURES.md #1–#9). Testet mod den rigtige AVM70 på `10.1.1.7:14999`, hvor alle 37 katalog-kommandoer svarer.

**Filer tilføjet:**
- `backend/app/protocol/catalog.py`: kommandokatalog (system, inputs, zone 1, lyd, video, zone 2) med afkodning. MAC uden skilletegn formateres, og enhed sættes kun på numeriske værdier
- `backend/app/protocol/parser.py`: `;`-opdeling på tværs af TCP-pakker og klassificering af værdi- og fejlsvar (`!I`/`!R`/`!E`/`!Z`)
- `backend/app/protocol/client.py`: egen asyncio-TCP-klient (kun `query`), svar matches til forespørgsel, timeout som resultat, specifikke forbindelsesfejl
- `backend/app/services/device_service.py`: én forbindelse med reconnect-backoff, polling, tilstand, hændelseslog, trafiklog, SSE-publicering, probe og test-forbindelse
- `backend/app/api/routes.py`: REST + SSE. `/api/query` afviser alt andet end `KODE?` i backend
- `backend/app/config.py`: `.env` + `data/settings.json` med backend-validering af alle kommunikationsparametre
- `backend/app/main.py`: FastAPI-app, der også serverer frontenden
- `backend/app/tools/fake_avm.py`: fake AVM70 til tests og udvikling
- `backend/tests/`: 55 tests (parser, afkodning, klient, service, reconnect, API, validering)
- `frontend/index.html`, `app.js`, `styles.css`: dashboard, hændelseslog, rå trafik, konsol og probe samt opsætningsdialog
- `run.ps1`: opretter venv og starter appen
- `AVM70_REFERENCE.md`: protokol-noter og observerede svar

**Filer ændret:** `version.json`, `FEATURES.md`, `ARCHITECTURE.md`, `RELEASE_NOTES.md`

## [0.1.0 build 0001] — 2026-10-02 — Projektinitialisering

**Filer tilføjet:**
- `CLAUDE.md` — projektdefinition og systemregler (udfyldt til AVM70 Diagnostics)
- `version.json` — versionskilde (0.1.0 build 0001)
- `ARCHITECTURE.md` — lagdelt arkitekturbeskrivelse (frontend → API → service → protokol)
- `FEATURES.md` — feature-backlog
- `BUGS.md` — bug-register
- `CHANGELOG.md` — denne fil
- `RELEASE_NOTES.md` — release-noter
- `README.md` — projektbeskrivelse og opstart
- `.claude/settings.local.json` — tilpasset pytest/uvicorn
