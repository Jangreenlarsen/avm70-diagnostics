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

## Versionskoder (fra AVM70's egen web-UI)

Enhedens web-brugerflade (`http://10.1.1.7/`) definerer sine protokolkoder i `js/merged.min.js` (`const COMMAND = …`, med kommentarer). Det er den mest autoritative kilde vi har. Versionsafsnittet og svarene på Jans enhed:

| Kode | Web-UI-kommentar | Svar (2026-10-02) |
|------|------------------|-------------------|
| `IDQ` | model and firmware version | `AVM 70 EU 00.80 Sep 1 2023 09H18M47` |
| `GSN` | serial number | `ALP2000256N070` |
| `IDS` | mcu version | `00.80/00.03` |
| `DSPIDS` | dsp version | `00.00/00.00` |
| `LCDIDS` | lcdc version | `00.32/00.02` |
| `IDB` | software build date | `Sep 1 2023 09H18M47` |
| `IDH` | hardware version | `2` |
| `IDR` | region | `EU` |
| `NMSVER` | module version | `2.3.213` |
| `NMHVER` | module hardware version | `1` |
| `RVER` | release version | `not approved` |
| `RBD` | release build date | *(tom)* |
| `NMR` | module region | *(tom)* |
| `NMST` | network status | `Wi-Fi` |
| `GCDN` | device name | `AVM70 BIO` |

## Advarsel: gæt ikke koder i blinde

`IDAI` betyder *delete input* og `IIAI` *add input* (web-UI'ets `COMMAND`-tabel). En brute-force-probe af `ID??`-koder sendte `IDAI?`. Den gjorde ingenting (enheden svarede `IDAI1`, og alle inputs var urørte bagefter), men handlings-koder kan se ud som forespørgsler. Slå altid koden op i `COMMAND`-tabellen før den prøves.

## Web-UI'ets JSON-API (port 80, læsende)

- `GET /api/getData?path=network:info&roles=@all`: Wi-Fi (SSID, kanal, signalstyrke i dBm, BSSID), kablet forbindelse, IP-adresser og gateway.
- `GET /api/getData?path=firmwareupdate:updateStatus&roles=@all`: status for firmware-opdatering (`idle`, download-fremskridt).
- **Ikke brugt**: `setData?path=firmwareupdate:checkForUpdate&role=activate` (opdateringstjek). Det er en handling, ikke en læsning.
