# Bugs

Format: `[status] vX.X.X — beskrivelse`
Status: `open` | `investigating` | `fixed`

---

| # | Bug | Status | Løsning | Version |
|---|-----|--------|---------|---------|
| 1 | **`run.ps1` kan ikke køre i Windows PowerShell 5.1**. Scriptet indeholdt ikke-ASCII-tegn (`ø`, `å`, `—`) og var gemt som UTF-8 uden BOM. PowerShell 5.1 læser sådanne filer som ANSI (Windows-1252), så `—` blev til `â€”` og parseren fejlede med *"The string is missing the terminator"*. Fundet da `build.ps1` (samme mønster) fejlede ved første build (FEATURES #13). Har været til stede siden v0.2.0, fordi appen indtil nu kun var startet via uvicorn direkte og aldrig via selve scriptet. | fixed | Begge `.ps1`-scripts er nu ren ASCII med engelsk output (også jf. sprogreglen). Ny test `test_powershell_scripts_are_ascii` fanger ikke-ASCII i alle `.ps1`-filer. Scriptene er verificeret ved at køre dem i `powershell.exe` 5.1. | 0.6.0 |
| 2 | **Sporadisk pytest-advarsel** ("1 warning") i nogle kørsler af testsuiten. | fixed | Rodårsag: `tests/test_desktop.py` indeholdt en ugyldig escape-sekvens. Filen var skrevet via en Bash-heredoc, hvor værktøjet halverede backslashes, så mutex-navnet `"Local\\AVM…"` (dobbelt backslash) endte som `"Local\AVM…"` (enkelt), og `\A` er ingen gyldig escape. Python giver kun `SyntaxWarning` når filen kompileres på ny, og bagefter bruges `.pyc`-cachen, derfor var advarslen sporadisk. Rettet, og hele kodebasen er scannet (ingen andre forekomster). Ny test `test_python_sources_have_no_invalid_escape_sequences` kompilerer alle `.py` med advarsler som fejl. | 0.7.0 |
| 3 | **Log mode: INIT (og evt. andre tidlige linjer) manglede i UI'et**, men stod korrekt i filen. Kapløb: når log mode slås til, kan INIT-linjen nå frem via SSE *før* HTTP-svaret på "Enable". Frontenden erstattede så visningen med svaret, som var et ældre øjebliksbillede uden INIT. Fundet ved visuel verifikation af FEATURES #17. Har eksisteret siden v0.8.0. | fixed | Hver log-linje får et løbenummer (`seq`) pr. session. Frontenden tilføjer kun linjer med højere `seq` end den sidst viste og erstatter aldrig en nyere visning med et ældre svar (`mergeLogmode`). Test af løbenumre i backend, og UI'et verificeret visuelt. | 0.10.0 |
