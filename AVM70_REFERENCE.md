# AVM70-reference

Noter om Anthem AVM 70's IP-protokol, sådan som den er observeret på Jans enhed (`10.1.1.7:14999`). Anthems officielle dokument hedder "MRXx40/AVM90/AVM70 IP/RS-232 Codes" og ligger i deres manual-arkiv. Det kunne ikke hentes automatisk, så kataloget bygger på `anthemav` 1.4.2 og observationer.

## Protokol

- TCP, port 14999, ASCII. Hver kommando og hvert svar afsluttes med `;`.
- Forespørgsel: `KODE?;`. Svar: `KODEværdi;`.
- Fejlsvar har formen `!<type><kommando>;`:
  - `!I`: ugyldig kommando
  - `!R`: uden for gyldigt område
  - `!E`: kan ikke udføres nu
  - `!Z`: zonen er slukket
- Enheden sender uopfordret ændringer (push), når `GCTXS` er `1` (IP til) eller `2`.
- **Kun én netværksklient ad gangen.**

## Observerede svar (2026-10-02, software 00.80/00.03)

| Kode | Svar | Bemærkning |
|------|------|------------|
| `IDM` | `AVM 70` | |
| `IDS` | `00.80/00.03` | |
| `IDB` | `Sep 1 2023 09H18M47` | |
| `IDH` | `2` | |
| `IDR` | `EU` | |
| `EMAC` / `WMAC` | `501E2D3E4870` | uden skilletegn; appen formaterer med `:` |
| `GCTXS` | `1` | IP-udsendelse til |
| `GCFPB` | `2` | |
| `ICN` | `3` | inputs: `IS1IN` Apple TV, `IS2IN` Blu-Ray, `IS3IN` Nvidia |
| `Z1VOL` | `-30.0` | dB |
| `Z1PVOL` | `25` | % |
| `Z1ALM` | `3` | Dolby Surround (x40-tabellen, uden foranstillet nul) |
| `Z1AIN` | `No Signal` | |
| `Z1AIR` / `Z1BRT` | `lossy input formats` | **tekst**, ikke et tal, når der ikke er signal |
| `Z1VIR` | `15` | 4K50 |
| `Z2VOL` | `-35.0` | svarer selvom zone 2 er i standby (ikke `!Z`) |

Alle 37 katalog-kommandoer svarede `ok` i probe'n.
