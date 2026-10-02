# Changelog

Nyeste øverst. Format: `## [version build NNNN] — YYYY-MM-DD — beskrivelse`

---

## [0.5.0 build 0005] — 2026-10-02 — Diagnoserapport som tekstfil til Anthem support

FEATURES.md #12. "⬇ Report" henter en struktureret engelsk tekstfil med alt appen har hentet fra AVM70. Den er beregnet til at sende til fabrikanten.

**Filer tilføjet:**
- `backend/app/services/report.py`: `build_report()` og `report_filename()`. Rapporten har 9 faste sektioner (identifikation, firmware, netværk, system og inputs, aktuel status, probe, hændelseslog, rå trafik, indstillinger). Hver værdi vises afkodet med kode og rå værdi. Tomme værdier vises som "(not set)", og værdier der aldrig er læst som "(not read)". Teksten er UTF-8 med CRLF. Serienummeret i filnavnet renses for ugyldige tegn
- `backend/tests/test_report.py`: 14 tests (sektionsrækkefølge, rå/afkodet/tom/fejlstatus, numerisk input-sortering, uden forbindelse, fejlet genforespørgsel, probe-tabel med zone, filnavn, endpoint med og uden forbindelse)

**Filer ændret:**
- `backend/app/api/routes.py`: `GET /api/export`
- `backend/app/services/device_service.py`: gemmer seneste probe (`last_probe`), som nulstilles når host/port skiftes
- `frontend/index.html`, `frontend/app.js`: "⬇ Report"-knap (fetch + blob, så backend-fejl vises som toast; virker også på mobil). `action()` slår nu altid knappen til igen. Før forblev knapper, der ikke styres af `renderConnection()`, deaktiverede (fanget under udviklingen, ikke udgivet)
- `ARCHITECTURE.md`, `FEATURES.md`

## [0.4.0 build 0004] — 2026-10-02 — Engelsk brugerflade

FEATURES.md #11. Al tekst brugeren ser er nu på engelsk. Dokumentation og kodekommentarer er fortsat på dansk.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: gruppetitler, labels og værdi-tabeller (fx `On`/`Off`, `No audio`, `7.1 channels`)
- `backend/app/protocol/parser.py`: fejltekster (`Invalid command`, `Zone is off`, …)
- `backend/app/protocol/client.py`, `backend/app/config.py`, `backend/app/services/device_service.py`, `backend/app/api/routes.py`, `backend/app/main.py`, `backend/app/tools/fake_avm.py`: forbindelses- og valideringsfejl, logtekster, test-forbindelse og probe-beskeder
- `frontend/index.html`, `frontend/app.js`: alle tekster, `lang="en"` og tidsformat `en-GB` (24 timer)
- `backend/tests/`: forventede beskeder opdateret, plus en ny test af connect-timeout på 2 s (under minimum)
- `CLAUDE.md`: ny fast regel om engelsk app-sprog

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
