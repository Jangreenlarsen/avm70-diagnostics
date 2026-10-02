# Changelog

Nyeste øverst. Format: `## [version build NNNN] — YYYY-MM-DD — beskrivelse`

---

## [0.7.0 build 0007] — 2026-10-03 — Ændringslog med initialværdier, gemmes som tekst

FEATURES.md #14 og BUGS.md #2.

**Filer tilføjet:**
- `backend/app/services/changelog.py`: `ChangeLog` med baseline (kun værdier læst ok), ændringer (`change`), værdier der ikke var kendt ved start (`first`) og forbindelsesmarkører. Maks. 20.000 poster, ældste droppes og tælles. `build_text()` laver en engelsk tekstfil i UTF-8 med CRLF: hoved, initialværdier pr. gruppe og ændringer med afkodet og rå værdi
- `backend/tests/test_changelog.py`: 15 tests (før start, baseline-filtrering, kun reelle ændringer, første værdi, ændring efter fejlstatus, loft, tekstlinjer, filnavn, start efter fuld aflæsning, push-ændring, reconnect-markører, API reset/export, nulstilling ved adresseskift)

**Filer ændret:**
- `backend/app/services/device_service.py`: loggen startes efter første fulde aflæsning. Hver ny værdi går gennem `changelog.add_value()`, også efter en fejlstatus (event-loggen springer den over). Markører ved forbindelse, tabt forbindelse og afbrydelse. `new_changelog()`. Loggen nulstilles ved skift af host/port. Nye SSE-events `changelog` og `changelog_entry`
- `backend/app/api/routes.py`: `GET /api/changelog`, `POST /api/changelog/reset`, `GET /api/changelog/export`
- `backend/app/desktop.py`: `save(kind)` med whitelist (`report`, `changelog`), så JS ikke kan bede om vilkårlige URL'er. `_attach`/`_EXPORTS` er private, så pywebview ikke eksponerer dem til JS
- `frontend/index.html`, `app.js`, `styles.css`: "Change log"-fane (første fane) med status, sammenklappelige initialværdier, ændringer live, "Save to file" og "Start new log". Fælles `saveExport()` til rapport og log
- `backend/tests/test_desktop.py`: ugyldig escape-sekvens rettet (BUGS.md #2)
- `backend/tests/test_scripts.py`: alle `.py` kompileres med `SyntaxWarning` som fejl

## [0.6.0 build 0006] — 2026-10-03 — Selvstændig Windows-app (AVM70Diagnostics.exe)

FEATURES.md #13 og BUGS.md #1. Appen kan nu køres som én exe-fil med eget vindue, uden Python-installation.

**Filer tilføjet:**
- `backend/app/desktop.py`: launcher. Starter uvicorn i en baggrundstråd på `127.0.0.1` og en ledig port, og viser UI'et i et pywebview/WebView2-vindue. Én instans håndhæves via Windows-mutex. Logger til fil i `%LOCALAPPDATA%\AVM70 Diagnostics\`. `sys.stdout`/`stderr` erstattes når de er `None` (windowed exe). Fejl vises i en message box. Serveren stoppes pænt når vinduet lukkes. `DesktopApi.save_report()` gemmer rapporten via "Save As"-dialog. Test-hook `AVM70_DEBUG_PORT` åbner WebView2's CDP-port på localhost
- `packaging/launcher.py`, `packaging/build_exe.py` (PyInstaller onefile/windowed, Windows-versionsinfo fra `version.json`), `packaging/requirements-build.txt`, `packaging/make_icon.py`, `packaging/avm70.ico`
- `build.ps1`: build-venv med Python 3.12, giver `dist\AVM70Diagnostics.exe`
- `backend/tests/test_desktop.py` (9 tests: enkelt-instans, port, std-streams, Save-as inkl. annullering og fejl), `backend/tests/test_scripts.py` (`.ps1` skal være ASCII)

**Filer ændret:**
- `backend/app/config.py`: pakket tilstand (`FROZEN`). Ressourcer læses fra bundlen, data fra `%LOCALAPPDATA%`, `.env` ved siden af exe'en. `VERSION_FILE`/`LOG_FILE`
- `frontend/app.js`: "⬇ Report" bruger `window.pywebview.api.save_report()` i app-vinduet. WebView2 dropper blob-downloads stille, hvilket blev fundet ved runtime-test af exe'en
- `run.ps1`, `build.ps1`: ren ASCII og engelsk output (BUGS.md #1)
- `.gitignore`: `.venv-build/`, `build/`, `dist/`
- `ARCHITECTURE.md` (nyt lag 0: launcher), `CLAUDE.md`, `README.md`, `BUGS.md`, `FEATURES.md`

**Verificeret i den faktiske runtime (selve exe'en):**
- Vinduet åbner på ca. 5 s og forbinder til AVM70.
- "Save As" gemmer rapporten.
- Kopi nummer to afvises.
- Når vinduet lukkes, stopper alle processer, og AVM70-forbindelsen frigives.

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
