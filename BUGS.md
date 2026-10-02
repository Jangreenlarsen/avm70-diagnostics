# Bugs

Format: `[status] vX.X.X — beskrivelse`
Status: `open` | `investigating` | `fixed`

---

| # | Bug | Status | Løsning | Version |
|---|-----|--------|---------|---------|
| 1 | **`run.ps1` kan ikke køre i Windows PowerShell 5.1**. Scriptet indeholdt ikke-ASCII-tegn (`ø`, `å`, `—`) og var gemt som UTF-8 uden BOM. PowerShell 5.1 læser sådanne filer som ANSI (Windows-1252), så `—` blev til `â€”` og parseren fejlede med *"The string is missing the terminator"*. Fundet da `build.ps1` (samme mønster) fejlede ved første build (FEATURES #13). Har været til stede siden v0.2.0, fordi appen indtil nu kun var startet via uvicorn direkte og aldrig via selve scriptet. | fixed | Begge `.ps1`-scripts er nu ren ASCII med engelsk output (også jf. sprogreglen). Ny test `test_powershell_scripts_are_ascii` fanger ikke-ASCII i alle `.ps1`-filer. Scriptene er verificeret ved at køre dem i `powershell.exe` 5.1. | 0.6.0 |
