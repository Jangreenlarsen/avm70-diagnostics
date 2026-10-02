# Projekt: AVM70 Diagnostics

Dette er Claudes system-prompt for dette projekt. Den læses altid først og følges uden undtagelser.

---

## Projektbeskrivelse

Selvstændig diagnostik-app til Anthem AVM 70-lydprocessoren (Voldby BIO, `10.1.1.7:14999`). Jan bruger den til at se al system-relevant info (model, firmware, MAC, inputs, IP-styringsstatus) og runtime-data (power, volumen, input, lydformat, kanaler, listening mode, video-opløsning) live, inkl. rå protokol-trafik og en tidsstemplet hændelseslog. Grundlag for at forstå enhedens faktiske opførsel/timing.

Appen kører lokalt på Jans Windows-PC: én Python-proces der både taler med AVM70 og serverer browser-UI'et på `http://127.0.0.1:8070`.

**Vigtige forhold ved AVM70** (lært i Movie database, BUGS.md #82/#93 dér):
- AVM70 accepterer kun **én** netværksklient ad gangen. Kører anden software mod den (fx Movie databases diagnostik eller Anthem-appen), afvises/afbrydes vi.
- Protokollen er ren ASCII over TCP: kommandoer og svar afsluttes med `;`. Forespørgsler er `KODE?;`, og svar er `KODEværdi;`. Fejlsvar er `!I` (ugyldig), `!R` (uden for område), `!E` (kan ikke udføres) og `!Z` (zone slukket).
- Appen er indtil videre **kun læsende**: backend afviser alt andet end forespørgsler (`?`).
- **App-sprog er engelsk (UFRAVIGELIG, FEATURES.md #11)**: al tekst brugeren ser er på engelsk. Det gælder UI, fejlbeskeder fra backend, katalog-labels, værdi-afkodning, hændelseslog og eksport. Projektdokumentation (CLAUDE.md, CHANGELOG, RELEASE_NOTES osv.) og kodekommentarer skrives fortsat på dansk.

**Reference-stack**:
- **Backend**: Python 3.12+ / FastAPI / uvicorn, egen asyncio-protokolklient (ikke `anthemav`)
- **Frontend**: statisk HTML/CSS/vanilla JS (intet build-trin), live-opdatering via Server-Sent Events
- **Deployment**: lokalt på Jans PC via `run.ps1` (opretter venv og starter serveren)

---

## Faste regler

1. **Versionering (UFRAVIGELIG)**: Projektet versioneres via [version.json](version.json). Denne fil er den **eneste** kilde til versionsnumre — alle andre steder (backend, frontend, changelog) læser herfra.
   - Normalt format: `{ "version": "MAJOR.MINOR.PATCH", "build": "NNNN" }`
   - **build**: incrementeres med **1** ved HVERT commit med kodeændringer (0001 → 0002 → ...).
   - **PATCH**: incrementeres ved bug fixes (afsluttede). Build nulstilles IKKE.
   - **MINOR**: incrementeres ved nye features. PATCH sættes til 0.
   - **MAJOR**: incrementeres ved breaking changes (fx skema-ændringer der kræver migration) eller store milepæle. MINOR og PATCH sættes til 0.
   - **Debugging-format (4 decimaler)**: Under aktiv fejlsøgning bruges `MAJOR.MINOR.PATCH.D` hvor D starter på 1 og incrementeres for hvert debug-commit: `v0.1.0.1`, `v0.1.0.2`, osv. Commit-beskeder præfikses `vX.X.X.D-bNNNN: debug: beskrivelse`.
   - **Afslutning af debugging**: Når Jan bekræfter *"nu virker det som det skal"*, incrementeres PATCH og D nulstilles: `v0.1.0.3` → `v0.1.1.0`. Commit markeres som `fix:` og afslutter debug-serien.
   - **Kun-dokumentations-commits** (RELEASE_NOTES.md, CHANGELOG.md, BUGS.md, FEATURES.md uden kodeændringer): bump IKKE version — lav commit uden versionsbump.
   - **RELEASE_NOTES.md skal opdateres ved ETHVERT commit der ændrer kode** — features, bugfixes og debug-afslutninger. Dokumentations-commits er undtaget. Glem aldrig dette.
   - Changelog-entries tagges med versionsnummer: `## [0.1.0 build 0001] — YYYY-MM-DD — beskrivelse`.
   - Claude **skal** opdatere `version.json` og vise den nye version i commit-beskeden.

2. **Ny funktionalitet (features)** skal ALTID registreres i [FEATURES.md](FEATURES.md) *før* implementering påbegyndes. Opdatér status når den er færdig.

3. **Bugs** skal ALTID registreres i [BUGS.md](BUGS.md) så snart de opdages. Opdatér med løsning når de er fikset.

4. **Alle kodeændringer** skal logges i [CHANGELOG.md](CHANGELOG.md) med version, dato, berørte filer og kort beskrivelse. Nyeste øverst.

5. **Lag-arkitekturen** beskrevet i [ARCHITECTURE.md](ARCHITECTURE.md) skal respekteres til enhver tid. Intet lag må springe et lag over eller kaldes "baglæns".

6. **Hemmeligheder og eksterne nøgler (UFRAVIGELIG)**: API-nøgler, adgangskoder og andre hemmeligheder må ALDRIG committes, logges i klartekst eller sendes tilbage til en klient. Opbevar dem i git-ignorerede `.env`-filer (eller en tilsvarende secret-store). Ethvert endpoint der eksponerer nøgle-*status* til en frontend må kun returnere om en nøgle er sat og hvorfra — aldrig selve værdien; sætning af en ny værdi er en skriv-kun handling. *I dag har projektet ingen hemmeligheder. AVM70-adressen er en LAN-adresse og ikke en hemmelighed. Reglen gælder, hvis der senere kommer nøgler til.*

7. **Read/write rettigheder**: Claude har forhåndsgodkendelse (via [.claude/settings.local.json](.claude/settings.local.json)) til at læse, skrive og redigere filer i projektmappen. Samme forhåndsgodkendelse dækker **alle kommandoer der er relevante for at køre og teste projektet** — uden at spørge først (fx `pytest`, `npm test`/`npm run lint`/`npm run build`, samt at starte/stoppe dev-servere lokalt til visuel verifikation). Kun ægte destruktive handlinger (force-push, `git reset --hard`, sletning af andet end egne midlertidige testdata) kræver stadig eksplicit accept, jf. `deny`-listen.

8. **Versionskontrol**: Projektet er et git-repo. Efter enhver logisk afsluttet ændring skal Claude lave en git commit med en beskrivende commit-besked. Aldrig bulk-commits af urelaterede ændringer.

9. **GitHub branch-strategi (UFRAVIGELIG)**:
   - `dev` — aktiv udviklingsbranch. **Al ny kode commites hertil.** Claude arbejder altid på `dev`.
   - `main` — stabil release-branch. Kun opdateret via PR/merge fra `dev` når en release er klar. Produktion følger `main`.
   - Claude skal pushe til `origin dev` efter hvert commit — aldrig direkte til `main`.
   - Merge `dev` → `main` gøres manuelt af Jan når en release er godkendt.

10. **Push og merge efter commit (UFRAVIGELIG)**: Efter ethvert commit skal Claude automatisk:
    - Pushe til `origin dev` — **uden at spørge først**
    - Spørge Jan: *"Vil du også merge til `main` og pushe?"*
    - Hvis ja: merge `dev` → `main` med `--no-ff` og pushe `origin main`
    - Hvis nej: forblive på `dev` og informere om at `main` ikke er opdateret
    - Svarer Jan blot *"main"*, betyder det ja til hele kæden (push `dev` → merge → push `main`), ikke kun det ene led.

11. **Runtime-logging**: Kritiske handlinger og fejl skal logges med struktureret kontekst via projektets logging-mekanisme. Log-niveau konfigureres via miljøvariabel (`LOG_LEVEL`, i `.env`). Python `logging` til konsol; forbindelsesskift og protokolfejl logges altid.

12. **Kodekvalitets-foranalyse (UFRAVIGELIG)**: Dette er en fast metode Claude *altid* anvender — både løbende mens der skrives ny kode, og som selvtjek før en feature/fix meldes færdig. Punkterne er generaliserede lektioner fra reelle fejl i tidligere projekter:
    - **Null/fejl-propagering**: ethvert kald der kan returnere `None`/`null` eller kaste en fejl, skal have sit resultat tjekket *før* det bruges. Antag aldrig succes.
    - **Fejlbeskeder til brugeren**: frontend skal *altid* vise den specifikke fejlbesked fra backend, aldrig kun en generisk besked når en specifik findes. Enhver `catch`-blok skal enten vise fejlen eller have en eksplicit, begrundet kommentar om hvorfor den bevidst undertrykkes.
    - **Adgangskontrol-lockout**: permission-/rolle-systemer skal altid beskyttes mod at ende i en tilstand uden nogen med adgang til at rette det igen (fx sidste admin fjernet). Håndhæv den slags regler i **backend**, ikke kun som en UI-bekvemmelighed der er triviel at omgå.
    - **Eksterne API'er og "tomhed"**: brug `is not None` — aldrig ren truthiness — for tal-/valgfri-felter der lovligt kan være `0`/tomme. Håndtér altid et catch-all for uventede fejlstatusser fra eksterne API'er (ikke kun de statuskoder man tilfældigvis har tænkt på).
    - **"Tomhed"-repræsentationer generelt**: når en bug rettes for én repræsentation af "tom" (fx `null`), tjek samtidig alle andre ækvivalente (tom streng, whitespace-only) for samme klasse fejl — ret hele klassen, ikke kun den rapporterede instans.
    - **Sikkerhedskonfiguration**: usikre default-værdier (hemmeligheder, nøgler, adgangskoder) skal advare eller nægte at starte hvis de stadig er i brug ved opstart — aldrig glide stille igennem til en kørende instans.
    - **Samtidige delvise opdateringer ("last write wins")**: en funktion der opdaterer et dokument må aldrig læse hele dokumentet, ændre ét felt i hukommelsen og skrive det hele tilbage ("read-modify-write") hvis flere sådanne kald kan ske i hurtig rækkefølge. Brug i stedet punkt-sti-`$set` (kun de faktisk ændrede felter), så to samtidige kald der rører *forskellige* felter ikke overskriver hinanden.
    - **Bulk-operationer mod eksterne API'er**: fejl der rammer *hele batchen* (manglende/ugyldig nøgle, rate-limit) skal håndteres adskilt fra fejl der kun rammer ét element. Tjek forudsætninger *før* løkken, og stop batchen straks ved et rate-limit i stedet for at hamre en allerede-blokeret API.
    - **Test i den faktiske runtime-kontekst, ikke kun logikken**: skal koden køre under en bestemt sandkasse/isolation (systemd-service, container, begrænset bruger), er det ikke nok at teste logikken i et privilegeret shell — verificér i den kontekst koden rent faktisk kører i produktion, *før* funktionen meldes færdig.
    - **Rammeværkets fejl har en anden form end vores egne**: når et lag oversætter fejl til noget brugeren kan læse, dækker det typisk kun de fejl vi selv kaster. Rammeværket kaster sine egne, i sit eget format (fx en valideringsfejl som en *liste* af objekter frem for en streng). Tjek eksplicit *begge* former.
    - **Regler der kun gælder én gren**: når en regel indføres for ét tilfælde (kun ved oprettelse, kun for den ene ressource), så gennemgå de øvrige grene *med det samme* — opdatering, den anden ressource, import-vejen. En regel der kun holder halvvejs opdages typisk først som en fejlmelding fra Jan.
    - Ved større funktioner (auth, permissions, betalinger, data-integritet) skal Claude proaktivt overveje disse punkter under implementering, ikke først vente på at Jan beder om en fejl-gennemgang.

13. **Visuel verifikation af layout-ændringer (UFRAVIGELIG)**: en ændring af *placering* — absolut positionering, flex/grid-containere, hjørne-grupper, z-index, ombrydning — skal ses i browseren/på skærmen før den meldes færdig. `build` og `lint` kan ikke fange den slags: markup og styling er hver for sig gyldige, og det er kun kombinationen der er forkert. Browseren *er* runtime-konteksten for layout. Sig eksplicit i afrapporteringen om ændringen er *set* eller kun *bygget*. Verificér mod den indbyggede fake-AVM70 (`python -m app.tools.fake_avm`), hvis den rigtige enhed ikke er tilgængelig.

14. **Tests**: Ny logik der kan gå galt uden at nogen opdager det — fejlbesked-oversættelse, formatering, fallback, tilstands-skift — skal have en test. Rene visuelle ændringer skal ikke; til dem gælder regel 13. Kør **alle** relevante testsuiter før noget meldes færdigt: `backend\.venv\Scripts\python.exe -m pytest` (fra `backend/`).

---

## Workflow for enhver opgave

1. Tilføj entry i `FEATURES.md` (feature) eller `BUGS.md` (bug).
2. Implementer ændringen i det korrekte lag jf. `ARCHITECTURE.md`.
3. Opdater `version.json`: bump build (altid), bump version (hvis feature/bugfix/breaking).
4. Tilføj entry i `CHANGELOG.md` med `[version build NNNN]` prefix.
5. Opdater `RELEASE_NOTES.md` hvis kode er ændret.
6. Kør testsuiter/verifikation før noget meldes færdigt. Rører ændringen layout, gælder desuden regel 13.
7. `git add` + `git commit` med besked der inkluderer version: `v0.1.0-b0001: beskrivelse`.
8. `git push origin dev` til GitHub.
9. Spørg Jan: *"Vil du også merge til `main`?"* — merge og push `origin main` hvis ja.

---

## Projektstruktur

Se [ARCHITECTURE.md](ARCHITECTURE.md#projektstruktur).
