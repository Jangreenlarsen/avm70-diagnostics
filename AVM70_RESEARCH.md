# AVM70 — research: kendte problemer og udokumenterede kommandoer

Undersøgt 2026-10-03 på Jans opfordring: *"lave en undersøgelse af hvad andre på internettet har haft af problemer som vi kan understøtte og eventuelt udokumenterede kommandoer"*.

Kilder er brugerfora, Anthems FAQ og manual, integrations-biblioteker samt **AVM70's egen web-UI og firmware**, læst direkte fra Jans enhed (software 00.80/00.03). Kildelisten står nederst.

---

## 1. Sammenfatning

1. **Firmwaren har et fejlregister** (`FCC`/`FCN`/`FCQ`), som ikke er dokumenteret nogen steder offentligt. De første 8 poster er hardwarefejl: forstærker, strøm, termisk, ventilator lav/høj hastighed, strømforsyning og global temperatur. Alle står på **0** på Jans enhed. Resten er en fejltæller pr. kommando. Det er det mest værdifulde diagnostiske fund.
2. **Fejlregisteret er også firmwarens komplette kommandoliste**: 164 kommandoer. Vi bruger 42 i dag. Web-UI'et bruger ca. 226 varianter (med zone- og input-nummer). Flere kommandoer findes kun i firmwaren, fx `UPDOTA`, `RSTWFS`, `RWPS`, `R1SET`–`R3SET`, `Z1SIM` og `Z1ARCPRC`.
3. **Mange kendte brugerproblemer kan diagnosticeres med koder vi endnu ikke læser**: IP-status (Wi-Fi/IP/gateway/DNS), standby-, CEC- og HDMI-bypass-indstillinger, triggere, bitdybde, ARC-gyldighed samt balance og tone.
4. **Sikkerhed**: tabellen indeholder handlingskoder som `LDFDS` (*load factory default settings*), `CPYS`, `LOTFS`, `FCR` (nulstil fejltæller), `GCIPV_A` (anvend ny IP-opsætning) og `IIAI`/`IDAI` (tilføj/slet input). Appens konsol tillader i dag enhver `KODE?`. Vi ved ikke om en *forespørgsel* på en handlingskode er harmløs for alle koder. Anbefaling: en spærreliste (se afsnit 5, punkt 1).
5. **Anthems officielle kodedokument** (`MRX-x40-AVM-70-90-IP-RS-232-v5.xls`, maj 2022) findes, men anthemav.com afviser automatisk download (404). Web-UI'et i enheden er en bedre kilde, fordi det følger den firmware der faktisk kører.

---

## 2. Kendte problemer fra andre brugere, og hvad appen kan måle

| Problem (rapporteret af brugere) | Relevante koder | Kan appen hjælpe? |
|---|---|---|
| **Lyd-dropouts**, især Xbox 4K/120. Anthem anbefaler "Standby HDMI Bypass" på den port. Andre sænker til 60 Hz | `GCSHDMIB` (standby HDMI bypass), `Z1AIF`/`Z1AIC`/`Z1SRT`/`Z1BRT`/`Z1BDP`, `Z1VIR`/`Z1IRH`/`Z1IRV` | **Ja.** Log mode viser hvornår lydformat og samplerate skifter eller falder ud i forhold til video-opløsningen. Det kan sendes til Anthem som bevis. Mangler: `Z1BDP` (bitdybde) og `GCSHDMIB` |
| **HDMI-blanking**: billedet går sort et par sekunder, og lyden kommer flere sekunder efter | `Z1VIR`, `Z1IRH`/`Z1IRV`, `Z1AIF`, `Z1AIN` | **Ja.** Timingen mellem video- og lydskift kan ses i log mode (ms-tidsstempler og push). Kortere poll-interval er en fordel her |
| **Atmos spiller kun som 7.1**, medmindre Dolby Surround er valgt | `Z1ALM`, `Z1AIF`, `Z1AIC`, `Z1AIN` | **Delvis.** Appen viser hvad enheden selv melder om format og kanaler pr. listening mode |
| **Enheden får ingen IP / mister netværket** (169.254.x.x, "Connecting", skal have strømmen fjernet). Jans enhed forsvandt fra netværket 2026-10-02 ca. 23:46 | `GCIPSTT`/`GCIPSTM`/`GCIPSTI`/`GCIPSTS`/`GCIPSTG`/`GCIPSDN`, `NMST`, `GCCSTBY`, web-API `network:info` (Wi-Fi-signal) | **Ja.** IP-status og Wi-Fi-signal i log mode og rapport viser om tab skyldes Wi-Fi, DHCP eller standby. Appens forbindelseslog viser allerede hvornår den forsvandt |
| **To MAC/IP-adresser** (enhed + Play-Fi) giver ustabil forbindelse ved forkert DHCP-reservation | `EMAC`, `WMAC`, `GCIPSTI` | **Ja.** Allerede delvist med MAC'erne. IP-status tilføjer den aktive IP |
| **Reagerer ikke på IP i standby** (manualen: lavstrøms-standby lytter ikke) | `GCCSTBY` (connected standby), `GCSHDMIB` | **Ja.** Indstillingerne kan vises, og forbindelsestab ved standby kan logges |
| **Tænder/slukker uventet** (CEC, "no signal power off") | `GCCECC`, `GCCPFC`, `GCCTVA`, `GCNSPO`, triggere `GCT1C`–`GCT3P` | **Ja.** Indstillingerne kan vises, og `Z1POW`-skift logges med tid |
| **Ventilatorstøj / varme** (rettet i en firmware ifølge brugere) | Fejlregister: `PRITHERMAL`, `PRILOSFAN`, `PRIHISFAN`, `PRIGBLTHER` | **Ja.** Tællerne viser om enheden har registreret termiske eller ventilator-fejl |
| **Glemmer subwoofer-opsætning** | `SSSP_*` (profil), `SSAM*` | Muligt, men ikke prioriteret (hører til opsætning, ikke drift) |
| **Andre apps kan ikke forbinde** (Anthem-app, ARC-2 rumkalibrering), mens en integration holder forbindelsen | Kun én TCP-klient | **Vigtigt for os.** Appen blokerer selv ARC/Anthem-appen mens den kører. Det bør stå i UI'et |

---

## 3. Udokumenterede koder læst fra Jans enhed (kun læsning)

Alle koder herunder forespørges også af enhedens eget web-UI, så de er sikre at læse.

**IP-status**
| Kode | Betydning (web-UI) | Værdi |
|---|---|---|
| `GCIPSTT` | IP-status | `Wi-Fi` |
| `GCIPSTM` | IP-mode | `1` |
| `GCIPSTI` | IP-adresse | `10.1.1.7` |
| `GCIPSTS` | Subnet | `255.255.255.0` |
| `GCIPSTG` | Gateway | `10.1.1.1` |
| `GCIPSDN` | DNS | `192.168.1.1` ⚠ (se nedenfor) |
| `GCTCP` | TCP-port | `14999` |

⚠ **DNS-serveren er `192.168.1.1`, som ligger uden for enhedens eget subnet (10.1.1.0/24).** Er den adresse ikke nåbar fra 10.1.1.0/24, kan det påvirke firmware-tjek, streaming og tidssynkronisering. Det bør Jan verificere i routeren eller DHCP-opsætningen.

**Drift og standby**
| Kode | Betydning | Værdi |
|---|---|---|
| `GCSHDMIB` | Standby HDMI bypass | `0` (fra) |
| `GCCSTBY` | Connected standby | `1` (til) |
| `GCNSPO` | No signal power off | `3` |
| `GCCECC` / `GCCPFC` / `GCCTVA` | CEC-styring / CEC power off / HDMI-lyd til TV | `1` / `1` / `0` |
| `GCAU` / `GCBU` | Automatiske opdateringer / beta-opdateringer | `0` / **`1`** (beta til) |
| `GCMMV` / `GCMPOV` / `GCMPOI` | Max volumen / volumen ved tænd / input ved tænd | `3.5` / `-30.0` / `0` |
| `GCT1C`–`GCT3P` | 12 V trigger 1–3, styring/power | T1 `0`/`1`, T2 `0`/`1`, T3 `0`/`0` |
| `GCFIR` / `GCRIR` | IR front / bag | `1` / `0` |
| `Z1BDP` | Lyd-bitdybde | `0` |
| `Z1ARCVAL` / `Z1ARCUPL` / `Z1ARCNAM` | ARC gyldig / uploaddato / navn | `1` / tom / tom |
| `Z1BAL` / `Z1TON0` / `Z1TON1` | Balance / bas / diskant | `-0.5` / `2.5` / `-2.0` |
| `IS1VID`, `IS1AIJ`, `IS1LS`, `IS1IT`, … | Input 1: video-input, lyd-input, lip sync, input-trim, … | `1`, `1`, `0`, `0.0`, … |

**Bemærk:** "Beta updates" står **til** på Jans enhed. Det kan forklare adfærd der afviger fra andre brugeres, og det er værd at nævne over for Anthem support.

---

## 4. Fejlregisteret (`FCC` / `FCN` / `FCQ`)

Fundet i web-UI'ets admin-side (`handle_fault_commands`):
- `FCC?` giver antal tællere (hex), på Jans enhed `00A4` = 164.
- `FCN<id>?` (id som 4 hex-cifre, fx `FCN0001?`) giver navnet.
- `FCQ<id>?` giver tællerværdien.
- `FCR<id>` **nulstiller** en tæller. Det er en handling, så appen må aldrig sende den.

**Hardwaretællere** (post 0001–0008) står alle på 0:
`PRIAAMP` (analog forstærker), `PRIDAMP` (digital forstærker), `PRIPWR` (strøm), `PRITHERMAL` (termisk), `PRILOSFAN` (ventilator lav hastighed), `PRIHISFAN` (ventilator høj hastighed), `PRIH2LPSU` (strømforsyning), `PRIGBLTHER` (global termisk). Betydningen er udledt af navnene. Anthem har ikke dokumenteret den.

**Kommandotællere** (post 0009–00A4) har én tæller pr. protokol-kommando. Ikke-nul på Jans enhed: `Z1VIR` 2, `Z1IRH` 2, `Z1IRV` 2, `Z1AIC` 3, `Z1AIF` 3, `Z1SRT` 3, `IS` 6, `GCDSZ` 2, `GCIPST` 8, `GCIPSDN` 5, `GCT` 2, `Z1ALM` 4.
Hvad de tæller, er udokumenteret. **Observation**: `GCT` steg fra 1 til 2 mellem to af mine læsninger af `GCT1C`–`GCT3P`, så tællerne ser ud til at registrere protokol-fejl eller -afvisninger. Også appens egne forespørgsler kan altså tælle dem op. Tællere der stiger *uden* at appen har sendt den kommando, er derfor det interessante.

Den fulde liste over alle 164 kommandoer står i bilaget nederst.

---

## 5. Forslag til næste skridt (prioriteret)

1. **Spærreliste i konsollen (sikkerhed).** Backend afviser forespørgsler på kendte handlingskoder: `LDFDS`, `CPYS`, `LOTFS`, `BSC`, `FCR`, `GCIPV*`, `IIAI`, `IDAI`, `CTRL*`, `Z1MSG`, `Z1SHC`, `UPDOTA`, `RSTWFS`, `RWPS`, `RDBL`, `R?SET`, `PRG*`. Det er billigt og forhindrer et uheld med en factory reset.
2. **Fejlregister i appen.** Hardwaretællerne vises i System, og alle 164 kommer med i rapporten. Ændringer i tællerne logges i log mode. Det er det mest værdifulde nye diagnostiske signal.
3. **Netværksmenu.** IP-status (`GCIPST*`) samt Wi-Fi-signal, kanal og BSSID fra web-API'et `network:info`. Log mode logger IP- og signalskift, så et netværkstab kan forklares.
4. **Drift- og standby-indstillinger** (`GCSHDMIB`, `GCCSTBY`, `GCNSPO`, CEC, triggere, `GCAU`/`GCBU`) i en "Settings"-gruppe, så de kommer med i rapporten. Det er relevant for support ved tænd-, sluk- og dropout-problemer.
5. **`Z1BDP` (bitdybde)** i lydgruppen. Det er en enkelt kode og nyttig ved dropout-sager.
6. **UI-note om at appen optager forbindelsen**: "While connected, the Anthem app and ARC room correction cannot connect".

---

## Kilder

- [Official Anthem AVM 70/90 Owners Thread (AVS Forum)](https://www.avsforum.com/threads/official-anthem-avm-70-90-owners-thread.3181385/page-407) (Xbox-dropouts, Standby HDMI Bypass), [side 432](https://www.avsforum.com/threads/official-anthem-avm-70-90-owners-thread.3181385/page-432), [side 147](https://www.avsforum.com/threads/official-anthem-avm-70-90-owners-thread.3181385/page-147), [side 11](https://www.avsforum.com/threads/official-anthem-avm-70-90-owners-thread.3181385/page-11)
- [Owners Thread for MRX 540, 740 & 1140 (AVS Forum)](https://www.avsforum.com/threads/owners-thread-for-mrx-540-740-1140-receivers.3180183/page-278) (power-on-bug, netværk, to MAC/IP), [side 168](https://www.avsforum.com/threads/owners-thread-for-mrx-540-740-1140-receivers.3180183/page-168), [side 16](https://www.avsforum.com/threads/owners-thread-for-mrx-540-740-1140-receivers.3180183/page-16) (ventilator)
- [LAN Connectivity with Anthem 1140 (AVS Forum)](https://www.avsforum.com/threads/lan-connectvity-with-anthem-1140.3224580/)
- [Owners' Thread – Anthem AVM70 & 90 (AVForums)](https://www.avforums.com/threads/anthem-avm70-90-discussion-help-experiences.2321588/page-52), [side 73](https://www.avforums.com/threads/anthem-avm70-90-discussion-help-experiences.2321588/page-73)
- [AVM70 (8K) not outputting video from HDMI out 2 (Audioholics)](https://forums.audioholics.com/forums/threads/avm70-8k-not-outputting-video-from-hdmi-out-2-or-hdmi-zone2-out.127760/), [AVM-70 8K and Apple TV start-up issue](https://forums.audioholics.com/forums/threads/anthem-avm-70-8k-and-apple-tv-start-up-issue.126143/)
- [Anthem FAQ: CEC controls](https://faq.anthemav.com/support/solutions/articles/43000720547-what-are-the-cec-controls-and-how-do-they-work-), [firmware MRXx40/AVM 70/90](https://faq.anthemav.com/support/solutions/articles/43000720545-can-i-upgrade-the-firmware-on-the-mrxx40-avm-70-90-how-do-i-confirm-the-latest-version-is-installed)
- [Anthem MRX/AVM operating manual](https://manuals.anthemav.com/media/manuals/mrx-avm_en.pdf)
- [home-assistant-libs/anthem-rs232 README](https://github.com/home-assistant-libs/anthem-rs232/blob/main/README.md) (Gen 4: `GC*`, `NM*`, `SS*`, opdelte `Z1ARC*`)
- [anthemav på PyPI](https://pypi.org/project/anthemav) (én klient ad gangen, blokerer Anthem-app og ARC-2)
- [Chowmain: Anthem MRX x40 driver til Control4](https://chowmain.software/drivers/control4-anthem-mrx-x40)
- AVM70's eget web-UI, `http://10.1.1.7/js/merged.min.js` (`const COMMAND`, `handle_fault_commands`, `send_query_commands`), læst 2026-10-03

---

## Bilag: firmwarens kommandoliste og fejltællere (Jans enhed, 2026-10-03)

| Id | Kommando | Tæller |
|---|---|---|
| 0001 | `PRIAAMP` | 0 |
| 0002 | `PRIDAMP` | 0 |
| 0003 | `PRIPWR` | 0 |
| 0004 | `PRITHERMAL` | 0 |
| 0005 | `PRILOSFAN` | 0 |
| 0006 | `PRIHISFAN` | 0 |
| 0007 | `PRIH2LPSU` | 0 |
| 0008 | `PRIGBLTHER` | 0 |
| 0009 | `PRGB` | 0 |
| 000A | `PRGR` | 0 |
| 000B | `PRGF` | 0 |
| 000C | `PRGS` | 0 |
| 000D | `IDM` | 0 |
| 000E | `IDS` | 0 |
| 000F | `DSPIDS` | 0 |
| 0010 | `LCDIDS` | 0 |
| 0011 | `GSN` | 0 |
| 0012 | `IDQ` | 0 |
| 0013 | `IDB` | 0 |
| 0014 | `IDH` | 0 |
| 0015 | `IDR` | 0 |
| 0016 | `NMSVER` | 0 |
| 0017 | `NMHVER` | 0 |
| 0018 | `RVER` | 0 |
| 0019 | `RBD` | 0 |
| 001A | `NMR` | 0 |
| 001B | `WMAC` | 0 |
| 001C | `EMAC` | 0 |
| 001D | `NMST` | 0 |
| 001E | `Z1VIR` | 2 |
| 001F | `Z1IRH` | 2 |
| 0020 | `Z1IRV` | 2 |
| 0021 | `Z1AIC` | 3 |
| 0022 | `Z1AIF` | 3 |
| 0023 | `Z1BRT` | 0 |
| 0024 | `Z1SRT` | 3 |
| 0025 | `Z1BDP` | 0 |
| 0026 | `Z1AIN` | 0 |
| 0027 | `Z1AIR` | 0 |
| 0028 | `Z1DIA` | 0 |
| 0029 | `NMSN` | 0 |
| 002A | `NMTI` | 0 |
| 002B | `NMAR` | 0 |
| 002C | `NMAL` | 0 |
| 002D | `NMTE` | 0 |
| 002E | `SSAMF` | 0 |
| 002F | `SSAMS` | 0 |
| 0030 | `SSAMB` | 0 |
| 0031 | `SSAMH1` | 0 |
| 0032 | `SSAMH2` | 0 |
| 0033 | `SS3DH` | 0 |
| 0034 | `SSSP` | 0 |
| 0035 | `BMSP` | 0 |
| 0036 | `LPSP` | 0 |
| 0037 | `LCSP` | 0 |
| 0038 | `ICN` | 0 |
| 0039 | `IIAI` | 0 |
| 003A | `IDAI` | 0 |
| 003B | `IS` | 6 |
| 003C | `GCL` | 0 |
| 003D | `GCAU` | 0 |
| 003E | `GCBU` | 0 |
| 003F | `GCDU` | 0 |
| 0040 | `GCFPB` | 0 |
| 0041 | `GCWUB` | 0 |
| 0042 | `GCOSID` | 0 |
| 0043 | `GCOSIZ` | 0 |
| 0044 | `GCFPDI` | 0 |
| 0045 | `GCMVS` | 0 |
| 0046 | `GCMMV` | 0 |
| 0047 | `GCZ2MMV` | 0 |
| 0048 | `GCMPOV` | 0 |
| 0049 | `GCZ2POV` | 0 |
| 004A | `GCMPOI` | 0 |
| 004B | `GCZ2POI` | 0 |
| 004C | `GCHMMO` | 0 |
| 004D | `GCDSZ` | 2 |
| 004E | `GCFCSI` | 0 |
| 004F | `GCNSPO` | 0 |
| 0050 | `GCSHDMIB` | 0 |
| 0051 | `GCCSTBY` | 0 |
| 0052 | `GCCECC` | 0 |
| 0053 | `GCCPFC` | 0 |
| 0054 | `GCCTVA` | 0 |
| 0055 | `GCMLOWS` | 0 |
| 0056 | `GCMDOWS` | 0 |
| 0057 | `GCML` | 0 |
| 0058 | `GCDN` | 0 |
| 0059 | `GCTCP` | 0 |
| 005A | `GCRIR` | 0 |
| 005B | `GCFIR` | 0 |
| 005C | `GCTXS` | 0 |
| 005D | `GCIPV` | 0 |
| 005E | `GCIPST` | 8 |
| 005F | `GCIPSDN` | 5 |
| 0060 | `GCT` | 2 |
| 0061 | `Z1POW` | 0 |
| 0062 | `Z1INP` | 0 |
| 0063 | `Z1VOL` | 0 |
| 0064 | `Z1VUP` | 0 |
| 0065 | `Z1VDN` | 0 |
| 0066 | `Z1PVOL` | 0 |
| 0067 | `Z1PVUP` | 0 |
| 0068 | `Z1PVDN` | 0 |
| 0069 | `Z1MUT` | 0 |
| 006A | `Z2POW` | 0 |
| 006B | `Z2INP` | 0 |
| 006C | `Z2VOL` | 0 |
| 006D | `Z2VUP` | 0 |
| 006E | `Z2VDN` | 0 |
| 006F | `Z2PVOL` | 0 |
| 0070 | `Z2PVUP` | 0 |
| 0071 | `Z2PVDN` | 0 |
| 0072 | `Z2MUT` | 0 |
| 0073 | `Z1TON0` | 0 |
| 0074 | `Z1TON1` | 0 |
| 0075 | `Z1TUP0` | 0 |
| 0076 | `Z1TUP1` | 0 |
| 0077 | `Z1TDN0` | 0 |
| 0078 | `Z1TDN1` | 0 |
| 0079 | `Z1BAL` | 0 |
| 007A | `Z1BLT` | 0 |
| 007B | `Z1BRT` | 0 |
| 007C | `Z1LEV` | 0 |
| 007D | `Z1LUP` | 0 |
| 007E | `Z1LDN` | 0 |
| 007F | `Z1ARCVAL` | 0 |
| 0080 | `Z1ARCUPL` | 0 |
| 0081 | `Z1ARCNAM` | 0 |
| 0082 | `Z1ARCMEN` | 0 |
| 0083 | `Z1ARCPRC` | 0 |
| 0084 | `Z1ARCCRP` | 0 |
| 0085 | `Z1ARCCLO` | 0 |
| 0086 | `Z1DYN` | 0 |
| 0087 | `Z1MSG` | 0 |
| 0088 | `Z1SHC` | 0 |
| 0089 | `Z1SMD` | 0 |
| 008A | `Z1SIM` | 0 |
| 008B | `Z2SIM` | 0 |
| 008C | `R1SET` | 0 |
| 008D | `R2SET` | 0 |
| 008E | `R3SET` | 0 |
| 008F | `CTRL` | 0 |
| 0090 | `CPYS` | 0 |
| 0091 | `Z1EMSG` | 0 |
| 0092 | `Z1EPRG` | 0 |
| 0093 | `Z1SPR` | 0 |
| 0094 | `Z1PRO` | 0 |
| 0095 | `Z1PRM` | 0 |
| 0096 | `Z1PRS` | 0 |
| 0097 | `Z1ALM` | 4 |
| 0098 | `Z1AUP` | 0 |
| 0099 | `Z1ADN` | 0 |
| 009A | `SPDSZ` | 0 |
| 009B | `RDBL` | 0 |
| 009C | `UPDOTA` | 0 |
| 009D | `LDFDS` | 0 |
| 009E | `LOTFS` | 0 |
| 009F | `FCC` | 0 |
| 00A0 | `FCQ` | 0 |
| 00A1 | `FCR` | 0 |
| 00A2 | `FCN` | 0 |
| 00A3 | `RWPS` | 0 |
| 00A4 | `RSTWFS` | 0 |
