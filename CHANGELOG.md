# Changelog

Nyeste øverst. Format: `## [version build NNNN] — YYYY-MM-DD — beskrivelse`

---

## [0.16.0 build 0017] — 2026-10-03 — Ryddeligt, kompakt UI

FEATURES.md #23. Kun frontend.

**Filer ændret:**
- `frontend/index.html`: fire sider (Overview, Device, Logs, Tools) med sidevalg i topbjælken. Topbjælken har kun status, én Connect/Disconnect-knap, ⬇ Report, ⚙ og kontakten "Codes". Versions- og Network-dialogerne er fjernet; de er nu kort på Device-siden
- `frontend/app.js`:
  - Overview-felter (`renderTiles`): hovedzone med input-navn, volumen og mute, lyd ("No input signal" markeres rødt når zonen er tændt), listening mode, video, zone 2 og sundhed (hardwarefejl, Wi-Fi, log mode).
  - Kort pr. side via `PAGE_GROUPS`. Versioner med Copy all/Refresh, netværk og indstillinger i sektioner, inputs som én række pr. input med et "selected"-mærke, og fejlregister med sektioner.
  - Felterne gentegnes én gang pr. bølge af værdier. Siden huskes i `#`, og "Codes" huskes i localStorage med try/catch.
- `frontend/styles.css`: sidevalg, statusfelter med farvekant (ok/warn/bad/off), kort-hoveder med handlinger, sektionstitler, kompakte rækker, kolonne-layout på Device-siden (ingen huller), protokolkoder skjult som standard og nedtonet "Zone is off"

## [0.15.0 build 0016] — 2026-10-03 — Netværksmenu (IP-status + web-API)

FEATURES.md #22.

**Filer tilføjet:**
- `backend/app/protocol/webapi.py`: henter `GET /api/getData?path=network:info` fra AVM70's web-UI (urllib i tråd, ingen ny afhængighed i exe'en) og oversætter til pseudo-koder: Wi-Fi (tilstand, SSID, BSSID, IP, bånd, kanal, signal, kvalitet, sikkerhed, credentials), Ethernet (kabel, tilstand, IP), gateway, DNS og soft-AP. Felter der mangler, udelades. Læsbare fejl (`WebApiError`)
- `backend/tests/test_network.py` (18 tests), `backend/tests/conftest.py` (web-API slået fra som standard i tests)

**Filer ændret:**
- `backend/app/protocol/catalog.py`: ny gruppe `network`. `GCIPSTT/M/I/S/G` og `GCIPSDN` (IP mode 0/1 = Automatic (DHCP)/Manual (static)). `NMST`, MAC'er og `GCTXS` er flyttet fra System. Web-pseudokoder med flag `web` og `volatile` (Wi-Fi-signal i dBm). `PROTOCOL_CODES`/`WEB_CODES`
- `backend/app/services/device_service.py`: `_read_web()` ved forbindelse, ved opdatering (alt eller `network`) og i hver log mode-runde. Circuit breaker: efter en fejl prøves højst én gang pr. minut, så log mode ikke bremses. Web-værdier får status `unavailable` med årsag, og den sidst kendte værdi bevares. Volatile værdier logges ikke som ændringer (event-log og ændringslog). Protokol-, polling- og probe-lister udelader web-koder. `AVM_WEB_PORT` i `.env`
- `backend/app/services/logmode.py`: web-værdier har kommando-cellen `HTTP network:info`. Status `unavailable`
- `backend/app/services/report.py`: netværkssektionen viser kontrolprotokol og web-API hver for sig
- `backend/app/tools/fake_avm.py`: fake web-API (`--web-port`), svar som på Jans enhed
- `frontend/index.html`, `app.js`: "🌐 Network"-dialog (kontrolprotokol, Wi-Fi og Ethernet/øvrigt) med "Refresh" og en note om at appen optager den eneste protokolforbindelse
- Tests der ventede på "Full read", venter nu på at alt er læst (`changelog.started`). Fejlregistret (0.14.0) gjorde dem sporadisk ustabile

## [0.14.0 build 0015] — 2026-10-03 — Fejlregister

FEATURES.md #21.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: `FAULTS`-gruppe og dynamiske koder `FCQ<4 hex>`. Etiketter efter navnet fra `FCN`: hardwaretællere som fx "Thermal fault (PRITHERMAL)", øvrige som "Command Z1AIF faults". `HARDWARE_FAULTS`, `fault_codes()`, `FAULT_NAMES`
- `backend/app/protocol/parser.py`: `FCQ`/`FCN`-svar
- `backend/app/services/device_service.py`: `_read_faults()` ved forbindelse (navne + tællere). Fejl i registret vælter aldrig forbindelsen. `refresh_faults()`. Log mode læser hardwaretællerne hver runde og alle hver 12. runde. Ændringsloggen starter først når også fejlregistret er læst (ellers ville tællerne stå som "first value"). Nyt SSE-event `faults`
- `backend/app/api/routes.py`: `GET /api/faults`, `POST /api/faults/refresh`. Rapport-eksporten genlæser tællerne
- `backend/app/services/report.py`: ny sektion "6. Fault counters" (hardware + ikke-nul kommandotællere). Efterfølgende sektioner er omnummereret (7–11)
- `backend/app/tools/fake_avm.py`: 10 fejltællere (8 hardware + `Z1AIF`=3, `IS`=6)
- `frontend/app.js`, `styles.css`: kortet "Fault counters" med tidspunkt og "Re-read"
- `backend/tests/test_faults.py`: 10 tests (parser, etiketter, spærret `FCR`, læsning ved forbindelse før ændringsloggen, manglende register, log mode-udvalg, stigende hardwaretæller logges, API og rapport)

## [0.13.0 build 0014] — 2026-10-03 — Drift- og standby-indstillinger

FEATURES.md #20.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: ny statisk gruppe `settings` med 26 koder og værditabeller fra den officielle protokol: `GCSHDMIB`, `GCCSTBY`, `GCNSPO`, `GCCECC`, `GCCPFC`, `GCCTVA`, `GCHMMO`, `GCMLOWS`, `GCMDOWS`, `GCMMV`, `GCMPOV`, `GCMPOI`, `GCZ2MMV`, `GCZ2POV`, `GCZ2POI`, `GCAU` (kun kendt fra web-UI), `GCBU`, `GCFIR`, `GCRIR`, `GCTCP` og `GCT1C`–`GCT3P`
- `backend/app/services/report.py`: ny sektion "5. Device settings". Efterfølgende sektioner er omnummereret (6–10)
- `backend/app/services/changelog.py`: settings indgår i initialværdierne
- `backend/app/tools/fake_avm.py`: settings-værdier som på Jans enhed
- `frontend/app.js`: "Settings"-kort på forsiden
- Tests: 22 nye (afkodning efter den officielle tabel og statisk gruppe). Log mode-testen tæller nu parametre ud fra kataloget

**Bemærk**: log mode poller nu 75 parametre pr. runde (ca. 3 s på den rigtige enhed). Standard-intervallet på 5 s holder, men intervaller under ca. 3 s vil give noten "poll took longer than the interval".

## [0.12.0 build 0013] — 2026-10-03 — Lyd-bitdybde

FEATURES.md #19.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: `Z1BDP` "Bit depth" i lydgruppen (enhed "bit", 0 = No input)
- `backend/app/tools/fake_avm.py`: `Z1BDP` = 24
- `backend/tests/`: afkodningstests. Log mode tæller nu 49 parametre

## [0.11.0 build 0012] — 2026-10-03 — Spærreliste for handlingskoder

FEATURES.md #18.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: `blocked_reason()` med en spærreliste bygget fra Anthems officielle x40-protokol ("Set only"-kommandoer og handlinger): fabriksnulstilling, kopiér/indlæs indstillinger, firmware-programmering/-opdatering, netværk og Wi-Fi, fejltæller-nulstilling, input tilføj/slet, eksklusiv kontrol, beskeder og IR-simulering, ARC-måling og testtoner, volumen-/tone-/niveau-trin
- `backend/app/protocol/client.py`: `query()` nægter spærrede koder (forsvar i dybden, så det også gælder probe og fremtidige veje)
- `backend/app/api/routes.py`: `/api/query` giver en `400` med forklaring
- `frontend/index.html`: hjælpeteksten i konsollen nævner spærringen
- Tests: 50 nye (alle spærrede koder også med `?` og små bogstaver, tilladte læse-koder, ingen katalog-kode spærret, spærret kode når aldrig fake-enheden, API-besked)

## [0.10.1 build 0011] — 2026-10-03 — Rettet afkodning efter Anthems officielle x40-protokol

BUGS.md #4.

**Filer ændret:**
- `backend/app/protocol/catalog.py`: værditabellerne følger Anthems officielle x40-protokol (v5).
  - `Z1AIC`: 5 = 7.1, 6 = Atmos, 7 = DTS:X. Før var de forskudt efter x20-tabellen.
  - `Z1AIF`: 7 = DTS:X. `Z1VIR`: 14 = 4K60. `GCTXS`: "IP only" / "IP and RS-232". `GCFPB` vises i %. `Z1DIA`: `n` = Not applicable. "No input" i stedet for "No audio"/"No video".
- `backend/app/tools/fake_avm.py`: Atmos = `Z1AIC 6`, DTS-HD MA 7.1 = `Z1AIC 5`
- `backend/tests/test_protocol.py`: 12 regressionstests mod det officielle dokument

## [0.10.0 build 0010] — 2026-10-03 — Kommando-kolonne i log mode

FEATURES.md #17 og BUGS.md #3.

**Filer ændret:**
- `backend/app/services/logmode.py`: ny kolonne efter type med retning og protokol-kommando (`POLL Z1AIF?`, `PUSH Z1AIF5`, `POLL 48 commands`). `command_cell()` afkorter kommandoer over 16 tegn med "...". INIT-detaljelinjerne har samme kolonne pr. parameter. Filhovedet har fået forklaring af COMMAND og en kolonneoverskrift (TIME / TYPE / COMMAND / DESCRIPTION). Hver linje har nu et løbenummer `seq` og feltet `cmd`
- `frontend/app.js`: indrykning af detaljelinjer følger den nye kolonne. `mergeLogmode()` og `seq`-tjek i `addLogmodeLine()` sikrer at hver linje vises præcis én gang, og at et ældre HTTP-svar aldrig overskriver nyere SSE-linjer (BUGS.md #3: INIT manglede i UI'et)
- `backend/tests/test_logmode.py`: 5 nye tests (kolonnens indhold pr. type, forklaringen starter altid i samme kolonne, afkortning, kolonneoverskrift, løbenumre)

## [0.9.0 build 0009] — 2026-10-03 — Systemejer i rapporter og logfiler

FEATURES.md #16.

**Filer ændret:**
- `backend/app/config.py`: indstillingen `owner` (standard "Jan Green Larsen", `OWNER` i `.env`). Valideres: må ikke være tom i nogen form (tom, kun whitespace, ikke-tekst), whitespace samles, og maks. 100 tegn
- `backend/app/services/report.py`: "System owner" i rapporthovedet. Afsnittet "App settings" viser også `log_poll_interval` og `owner`
- `backend/app/services/changelog.py`, `backend/app/api/routes.py`: "System owner" i ændringslog-filens hoved
- `backend/app/services/logmode.py`, `backend/app/services/device_service.py`: "System owner" i log mode-filens hoved
- `backend/.env.example`: `LOG_POLL_INTERVAL` og `OWNER`
- `frontend/index.html`, `app.js`, `styles.css`: nyt "General"-afsnit i ⚙ Setup med "System owner". Ejeren vises i versionsmenuen og i "Copy all". "Defaults" opdaterer nu også appens kendte indstillinger
- `backend/tests/test_owner.py`: 12 tests (standard, alle former for "tom", trimning, maks. længde, rapport, ændringslog, log mode-fil, Setup → eksport)

## [0.8.0 build 0008] — 2026-10-03 — Log mode med fast pollingcyklus

FEATURES.md #15.

**Filer tilføjet:**
- `backend/app/services/logmode.py`: `LogSession`. Første cyklus er `INIT` med alle parametre. Derefter pr. cyklus `OK` eller `CHANGE`/`NEW` (sammenlignet med loggens egen sidste værdi, hvor fejlstatus indgår som værdi) eller `INCOMPLETE`. Desuden `PUSH` imellem cyklusser, `CONNECTION`, `NOTE` og `STOPPED`. Linjerne skrives løbende til fil (append + flush, CRLF), og de seneste 2000 holdes i hukommelsen. Kan filen ikke oprettes, fortsætter loggen i hukommelsen med en `ERROR`-linje. `next_due()` giver et driftfrit skema
- `backend/tests/test_logmode.py`: 17 tests (skema, INIT, OK, CHANGE, statusskift, INCOMPLETE, NEW, PUSH uden dobbelt-logning, langsom cyklus, intervalskift, stop og fuld tekst med CRLF, uskrivbar mappe, service-integration med push og ændring uden push, normal polling på pause, fil ved shutdown, API-validering og export)

**Filer ændret:**
- `backend/app/services/device_service.py`: log-cyklus i forbindelsesløkken erstatter den normale polling mens log mode er aktiv. Poller katalog og kendte inputs og henter inputnavne, hvis `ICN` ændrer sig. Push går til `record_push`. Markører ved forbindelse, tabt forbindelse og afbrydelse. Intervalskift fra Setup træder i kraft med det samme. Ved adresseskift stoppes loggen. `shutdown()` lukker loggen pænt, når appen lukker
- `backend/app/config.py`: `log_poll_interval` (standard 5 s, 2–3600 s). `DeviceSettings` konstrueres nu med keyword-argumenter
- `backend/app/api/routes.py`: `/api/logmode`, `/start`, `/stop`, `/export`
- `backend/app/desktop.py`: `logmode` tilføjet til de tilladte eksporter ("Save As")
- `backend/app/main.py`: lifespan kalder `shutdown()`
- `frontend/index.html`, `app.js`, `styles.css`: "Log mode"-fane med Enable/Disable, status og tællere, sti til logfilen, "● REC" i fanen, live tidslinje (farvet pr. type, "Follow newest"), "Save to file", "⚙ Log poll setup". Nyt "Log mode"-afsnit i Setup-dialogen

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
