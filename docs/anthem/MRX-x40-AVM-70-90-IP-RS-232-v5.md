# Anthem MRX x40 / AVM 70 / AVM 90 — IP/RS-232 protocol (v5)

Konverteret fra Anthems officielle regneark `MRX-x40-AVM-70-90-IP-RS-232-v5.xls` (dateret Aug 5 2020, sidst gemt 2020-08-26).
Hentet 2026-10-03 fra Wayback Machines kopi af `https://www.anthemav.com/downloads/MRX-x40-AVM-70-90-IP-RS-232-v5.xls` (arkiveret 2023-01-29), da anthemav.com ikke længere udleverer filen. Original ligger ved siden af denne fil.
SHA-256: `130c03a30da3028bcb08099a7e95a513e97735d242ee8ba04eca6bf70a5ff0e2`. Indholdet er © Anthem — kun til reference i dette private projekt.


## Ark: Serial Commands

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Anthem MRX 1140-740-540 AVR and AVM 90-70 AVP serial commands |  | Aug 5 2020 |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Command | Description | Related Query Command | Report |
| ; | (semicolon) Command separator/terminator - note that semicolon is the only valid line feed. | there will be a semicolon at the end of report |  |


### Host MCU

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| IDQ? | Query model and firmware version | returns IDQ followed by model, software version, region, software build date e.g. "IDQMRX 1140 US 0.2.3Aug 05 2020" |  |
| IDM? | Query model | returns IDM followed by model e.g. "IDMMRX 1140" |  |
| IDS? | Query software version | returns IDS followed by software version e.g. "IDS0.2.3" |  |
| DSPIDS | Query DSP software version |  |  |
| LCDIDS | Query LCDC software version |  |  |
| GSN | Query serial number |  |  |
| IDR? | Query region | returns IDR followed by region e.g. "IDRUS" or "IDREU" or "IDRCN" |  |
| IDB? | Query software build date | returns IDB followed by software build date e.g. "IDBAug 13 2020" |  |
| IDH? | Query hardware version | returns IDH followed by hardware version e.g. "IDH1" |  |


### Networking Module (NM)

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| NMSVER | Module software version | ex: NMVER0.1.2945 |  |
| NMHVER | Module hardware version | ex: NMHVER1 |  |
| RVER | Release version | ex: RVER0.2.2945 |  |
| RBD | Release build date |  |  |
| NMR | Module region |  |  |
| WMAC | Wi-Fi MAC address | ex: 01.23.45.67.89.AB |  |
| EMAC | Ethernet MAC address | ex: 01.23.45.67.89.AB |  |
| NMST | Network status | ex: 192.168.1.54 or 'Up' or 'Down' or 'Connecting'. Up to 32 characters |  |


### Upper case letters represent command, lower case represent variables which must be entered.


### System Status

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1VIR? | Query video input resolution: 0=no input, 1=other, 2=1080p60, 3=1080p50, 4=1080p24, 5=1080i60, 6=1080i50, 7=720p60, 8=720p50, 9=576p50, 10=576i50, 11=480p60, 12=480i60, 13=3D, 14=4k60, 15=4k50, 16=4k24 | returns Z1VIRxx | yes |
| Z1IRH? | Query active horizontal video resolution (in pixels) | return Z1IRHxxxx | yes |
| Z1IRV? | Query active vertical video resolution (in pixels/lines) | return Z1IRVxxxx | yes |
| Z1AIC? | Query audio input channels: 0=no input, 1=other, 2=mono (center channel only), 3=2-channel, 4=5.1-channel, 5==7.1-channel, 6=Atmos, 7=DTS-X | returns Z1AICx | yes |
| Z1AIF? | Query audio input format: 0=no input, 1=Analog, 2=PCM, 3=Dolby, 4= DSD, 5=DTS, 6=Atmos, 7=DTS-X. | Returns Z1AIFxx | yes |
| Z1BRT? | Query audio input bit rate (kbps). For Analog/PCM inputs this is equal to the sample rate multiplied by the bit depth and the number of channels | returns Z1BRTxxxx, 0=analog | yes |
| Z1SRT? | Query audio input sampling rate (kHz) | returns Z1SRTxxx, 0=analog direct | yes |
| Z1BDP? | Query audio bit depth | returns Z1BDPxxx, 16-bit, 24-bit, 32-bit | yes |
| Z1AIN? | Query the current audio input name (maximum of 16 characters returned) | Returns Z1AINx. Ex: Current audio input format is DTS Master Audio. 'Z1AIN?' Returns 'Z1AINDTS Master Audio' | yes |
| Z1AIR? | Query the current audio input rate name (maximum of 16 characters returned). | Returns Z1AIRx. For lossy input formats, returns the bit rate (ex 'Z1AIR384 kbps'). For lossless audio, analog audio, or PCM audio inputs it returns the sample rate combined with bit depth (ex: Z1AIR48/16). | yes |


### Speaker Setup - Amp Matrixing

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| SSAMF | Front: MRX740 only: y=0 Front, y=1 Zone 2, y=2 Height 1, y=3 Height 2 MRX1140 only: y=0 Front, y=1 Zone 2, y=2 Front Wide, y=3 Height 3 | SSAMF? returns SSAMFy | yes |
| SSAMS | Surround: MRX740 only: y=0 Surround, y=1 Zone 2, y=2 Height 2 MRX1140 only: y=0 Surround, y=1 Zone 2, y=2 Height 3 | SSAMS? returns SSAMSy | yes |
| SSAMB | Back: MRX740 only: y=0 Back, y=1 Zone 2, y=2 Zone 2 On Demand, y=3 Height 1, y=4 Front (Bi-Amp) MRX1140 only: y=0 Back, y=1 Zone 2, y=2 Zone 2 On Demand, y=3 Front Wide, y=4 Front (Bi-Amp) | SSAMB? returns SSAMBy | yes |
| SSAMH1 | Height 1: MRX1140 only: y=0 Height 1, y=1 Zone 2, y=2 Front (Bi-Amp) | SSAMH1? returns SSAMH1y | yes |
| SSAMH2 | Height 2: MRX1140 only: y=0 Height 2, y=1 Zone 2, y=2 Front Wide, y=3 Front (Bi-Amp) | SSAMH2? returns SSAMH2y | yes |


### Speaker Setup - 3D Sound

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| SS3DHLy | Height (MRX 540 only) y=0 Height (Atmos), y=1 Back (No Atmos) | SS3DHL? returns SS3DHLy |  |
| SS3DH1y | Height 1 y=0 Front In-Ceiling, y=1 Front Dolby, y=2 Front On-Wall, y=3 Middle In-Ceiling, y=4 Middle Dolby, y=5 Back In-Celing, y=6 Back Dolby, y=7 Back On-Wall, y=8 Off | SS3DH1? returns SS3DH1y |  |
| SS3DH2y | Height 2 (MRX 740/1140, AVM 70/90) y=0 Middle In-Ceiling, y=1 Middle Dolby, y=2 Back In-Celing, y=3 Back Dolby, y=4 Back On-Wall, y=5 Off | SS3DH2? returns SS3DH2y |  |
| SS3DH3y | Height 3 (MRX 1140, AVM 70/90) y=0 Back In-Celing, y=1 Back Dolby, y=2 Back On-Wall, y=3 Off | SS3DH3? returns SS3DH3y |  |


### Profile Setup - Speaker Setup

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | p is the profile number: 1 - 4 |  |  |
| SSSPp0yyy | Speaker Profile name of the specified profile number. yyy=16 characters. | SSSPp0? returns SSSPp0yyy | yes |
| SSSPp1y | Subwoofer MRX 540/740: y=0 Off, y=1 On MRX 1140, AVM 70: y=0 None, y=1 to 2 AVM 90: y=0 None, y=1 to 4 | SSSPp1y? returns SSSPp1y | yes |
| SSSPp5y | Front (read only) y=1 On | SSSPp5y? returns SSSPp5y | yes |
| SSSPp6y | Front Wide MRX 1140, AVM 70/90 only) y=0 Off, y=1 On | SSSPp6y? returns SSSPp6y | yes |
| SSSPp7y | Center  y=0 Off, y=1 On | SSSPp7y? returns SSSPp7y | yes |
| SSSPp8y | Surround  y=0 Off, y=1 On | SSSPp8y? returns SSSPp8y | yes |
| SSSPp9y | Back y=0 Off, y=1 On | SSSPp9y? returns SSSPp9y | yes |
| SSSPpAy | Height 1 y=0 Off, y=1 On | SSSPpAy? returns SSSPpAy | yes |
| SSSPpBy | Height 2 (MRX 740/1140, AVM 70/90) y=0 Off, y=1 On | SSSPpBy? returns SSSPpBy | yes |
| SSSPpCy | Height 3 (MRX 1140, AVM 70/90) y=0 Off, y=1 On | SSSPpCy? returns SSSPpCy | yes |


### Profile Setup - Bass Management

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | p is the profile number: 1 - 4 |  |  |
| BMSPp0y | LFE Low Pass Filter y=40 to 120 (Hz) step 10, y=130 Bypass | BMSPp0? returns BMSPp0y | yes |
| BMSPp10y | Subwoofer 1 Phase Frequency y=40 to 120 (Hz) | BMSPp10? returns BMSPp10y | yes |
| BMSPp11y | Subwoofer 1 Phase y=0 to 180 (degrees)  step 1 | BMSPp11? returns BMSPp11y | yes |
| BMSPp12y | Subwoofer 1 Polarity y=0 Normal, y=1 Inverted | BMSPp12? returns BMSPp12y | yes |
| BMSPp20y | Subwoofer 2 Phase Frequency (MRX 1140, AVM 70/90 only) y=40 to 120 (Hz) | BMSPp20? returns BMSPp20y | yes |
| BMSPp21y | Subwoofer 2 Phase (MRX 1140, AVM 70/90 only) y=0 to 180 (degrees)  step 1 | BMSPp21? returns BMSPp21y | yes |
| BMSPp22y | Subwoofer 2 Polarity (MRX 1140, AVM 70/90 only) y=0 Normal, y=1 Inverted | BMSPp22? returns BMSPp22y | yes |
| BMSPp30y | Subwoofer 3 Phase Frequency (AVM 90 only) y=40 to 120 (Hz) | BMSPp30? returns BMSPp30y | yes |
| BMSPp31y | Subwoofer 3 Phase (AVM 90 only) y=0 to 180 (degrees)  step 1 | BMSPp31? returns BMSPp31y | yes |
| BMSPp32y | Subwoofer 3 Polarity (AVM 90 only) y=0 Normal, y=1 Inverted | BMSPp32? returns BMSPp32y | yes |
| BMSPp40y | Subwoofer 4 Phase Frequency (AVM 90 only) y=40 to 120 (Hz) | BMSPp40? returns BMSPp40y | yes |
| BMSPp41y | Subwoofer 4 Phase (AVM 90 only) y=0 to 180 (degrees)  step 1 | BMSPp41? returns BMSPp41y | yes |
| BMSPp42y | Subwoofer 4 Polarity (AVM 90 only) y=0 Normal, y=1 Inverted | BMSPp42? returns BMSPp42y | yes |
| BMSPp5y | Front Crossover y=30 Off, 40 to 250 (Hz) step 10 | BMSPp5? returns BMSPp5y | yes |
| BMSPp6y | Front Wide Crossover (MRX 1140, AVM 70/90 only) y=30 Off, 40 to 250 (Hz) step 10 | BMSPp6? returns BMSPp6y | yes |
| BMSPp7y | Center Crossover y=30 Off, 40 to 250 (Hz) step 10 | BMSPp7? returns BMSPp7y | yes |
| BMSPp8y | Surround Crossover y=30 Off, 40 to 250 (Hz) step 10 | BMSPp8? returns BMSPp8y | yes |
| BMSPp9y | Back Crossover y=30 Off, 40 to 250 (Hz) step 10 | BMSPp9? returns BMSPp9y | yes |
| BMSPpAy | Height 1 Crossover y=30 Off, 40 to 250 (Hz) step 10 | BMSPpA? returns BMSPpAy | yes |
| BMSPpBy | Height 2 Crossover (MRX 740/1140, AVM 70/90 only) y=30 Off, 40 to 250 (Hz) step 10 | BMSPpB? returns BMSPpBy | yes |
| BMSPpCy | Height 3 Crossover (MRX 1140, AVM 70/90 only) y=30 Off, 40 to 250 (Hz) step 10 | BMSPpC? returns BMSPpCy | yes |
| BMSPpDy | Super Sub Fronts y=0 No, y=1 Yes | BMSPpD? returns BMSPpDy | yes |


### Profile Setup - Listener Position

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | p is the profile number: 1 - 4 |  |  |
| LPSPp1y | Subwoofer (1) Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp1? returns LPSPp1y | yes |
| LPSPp2y | Subwoofer 2 Distance (MRX 1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp2? returns LPSPp2y | yes |
| LPSPp3y | Subwoofer 3 Distance (AVM 90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp3? returns LPSPp3y | yes |
| LPSPp4y | Subwoofer 4 Distance (AVM 90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp4? returns LPSPp4y | yes |
| LPSPp5y | Front Left Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp5? returns LPSPp5y | yes |
| LPSPp6y | Front Right Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp6? returns LPSPp6y | yes |
| LPSPp7y | Front Wide Left Distance (MRX 1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | yLPSPp7? returns LPSPp7 | yes |
| LPSPp8y | Front Wide Right Distance (MRX 1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | yLPSPp8? returns LPSPp8 | yes |
| LPSPp9y | Center Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPp9? returns LPSPp9y | yes |
| LPSPpAy | Surround Left Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpA? returns LPSPpAy | yes |
| LPSPpBy | Surround Right Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpB? returns LPSPpBy | yes |
| LPSPpCy | Back Left Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpC? returns LPSPpCy | yes |
| LPSPpDy | Back Right Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpD? returns LPSPpDy | yes |
| LPSPpEy | Height 1 Left Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpE? returns LPSPpEy | yes |
| LPSPpFy | Height 1 Right Distance y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpF? returns LPSPpFy | yes |
| LPSPpGy | Height 2 Left Distance (MRX 740/1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpG? returns LPSPpGy | yes |
| LPSPpHy | Height 2 Right Distance (MRX 740/1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpH? returns LPSPpHy | yes |
| LPSPpIy | Height 3 Left Distance (MRX 1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpI? returns LPSPpIy | yes |
| LPSPpJy | Height 3 Right Distance (MRX 1140, AVM 70/90 only) y=0 to 180 Feet: 0'0" to 30'0", step 2"; Metric: 0 to 900 cm, step 5 cm | LPSPpJ? returns LPSPpJt | yes |


### Profile Setup - Level Calibration

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | p is the profile number: 1 - 4 |  |  |
| LCSPp0y | Calibration Level y=-15 dB to +15 dB, step 0.5 dB | LCSPp0? returns LCSPp0y | yes |
| LCSPp1y | Subwoofer (1) y=-15 dB to +15 dB, step 0.5 dB | LCSPp1? returns LCSPp1y | yes |
| LCSPp2y | Subwoofer 2 (MRX 1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPp2? returns LCSPp2y | yes |
| LCSPp3y | Subwoofer 3 (AVM 90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPp3? returns LCSPp3y | yes |
| LCSPp4y | Subwoofer 4 (AVM 90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPp4? returns LCSPp4y | yes |
| LCSPp5y | Front Left y=-15 dB to +15 dB, step 0.5 dB | LCSPp5? returns LCSPp5y | yes |
| LCSPp6y | Front Right y=-15 dB to +15 dB, step 0.5 dB | LCSPp6? returns LCSPp6y | yes |
| LCSPp7y | Front Wide Left (MRX 1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPp7? returns LCSPp7y | yes |
| LCSPp8y | Front Wide Right (MRX 1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPp8? returns LCSPp8y | yes |
| LCSPp9y | Center y=-15 dB to +15 dB, step 0.5 dB | LCSPp9? returns LCSPp9y | yes |
| LCSPpAy | Surround Left y=-15 dB to +15 dB, step 0.5 dB | LCSPpA? returns LCSPpAy | yes |
| LCSPpBy | Surround Right y=-15 dB to +15 dB, step 0.5 dB | LCSPpB? returns LCSPpBy | yes |
| LCSPpCy | Back Left y=-15 dB to +15 dB, step 0.5 dB | LCSPpC? returns LCSPpCy | yes |
| LCSPpDy | Back Right y=-15 dB to +15 dB, step 0.5 dB | LCSPpD? returns LCSPpDy | yes |
| LCSPpEy | Height 1 Left y=-15 dB to +15 dB, step 0.5 dB | LCSPpE? returns LCSPpEy | yes |
| LCSPpFy | Height 1 Right y=-15 dB to +15 dB, step 0.5 dB | LCSPpF? returns LCSPpFy | yes |
| LCSPpGy | Height 2 Left (MRX 740/1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPpG? returns LCSPpGy | yes |
| LCSPpHy | Height 2 Right (MRX 740/1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPpH? returns LCSPpHy | yes |
| LCSPpIy | Height 3 Left (MRX 1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPpI? returns LCSPpIy | yes |
| LCSPpJy | Height 3 Right (MRX 1140, AVM 70/90 only) y=-15 dB to +15 dB, step 0.5 dB | LCSPpJ? returns LCSPpJy | yes |
| LCSPpKy | Test Noise y=0 Off, y=1 On. Only one profile can have Test Noise active at a time. | LCSPpK? returns LCSPpKy | yes |


### Input Setup

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | i is the input number: 1 to ZZ, the number of configured inputs (max 30) |  |  |
| ICN? | Query number of active input configurations. The system supports 30 input configurations. | returns ICNyy e.g. "ICN9" for a system with 9 active inputs | yes |
| IIAIi | Insert input number. Shift all higher numbered inputs down. Default values are assigned. |  |  |
| IDAIi | Delete input number. Shift all higher numbered inputs up. |  |  |
| ISiINyyyy | The name of the input yyyy is 16 characters | returns 'ISiINyyyy' where 'yyyy'= Input name as set in the setup menu. Maximum length of the long input name is 16 ASCII characters. | yes |
| ISiVIDx | Video Input Jack x=0 None, x=1 to 7 HDMI 1 to 7 | ISiVID? returns IsiVIDx | yes |
| ISiAIJx | Audio Input Jack x=0 None, x=1 HDMI MRX 540/740/1140 only: x=2 HDMI eARC, x=3 Digital Coaxial 1, x=4 Digital Coaxial 2, x=5 Digital Optical 1, x=6 Digital Optical 2, x=7 Digital Optical 3, x=8 Analog 1, x=9 Analog 2, x=10 Analog 3, x=11 Analog 4, x=12 Analog 5, x=13 Streaming, x=14 Bluetooth AVM 70/90 only: x=2 HDMI Audio Return Channel, x=3 Digital Coaxial 1, x=4 Digital Coaxial 2, x=5 Digital Optical 1, x=6 Digital Optical 2, x=7 Digital Optical 3, x=8 Analog 1, x=9 Analog 2, x=10 Analog 3, x=11 Analog 4, x=12 Phono (MM), x=13 Streaming, x=14 Bluetooth | ISiAIJ? returns IsiAIJx | yes |
| ISiCAx | Convert Analog MRX 540/740/1140 x=0 No, x=1 32/96 kHz AVM 70/90 x=0 No, x=1 48/96/192 kHz | ISiCA? returns IsiCAx |  |
| ISiSPp | Set Speaker Profile to # p for profile 1 (p=1), profile 2 (p=2), profile 3 (p=3) and profile 4 (p=4) for the Input # i (i=1-ZZ where ZZ is the number of active input configurations). | ISiSP? returns ISiSPp | yes |
| ISiARCx | Anthem Room Correction x=0 Off, x=1 On. ARC must have been performed. | ISiARC? returns IsiARCx | yes |
| ISiRFx | Rumble Filter (AVM 70/90 only) x=0 Off, x=1 On | ISiRF? returns IsiRFx | yes |
| ISiDVx | Set Dolby Audio Post-Processing off (x=0), Movie (x=1), Music (x=2) or Night (x=3) for the input i. | ISiDV? returns ISiDVx | yes |
| ISiPMx | Mode Pre-set for Mono Source x=0 Mono, x=1 Last Used, x=2 All Channel Mono | ISiPM? returns IsiPMx | yes |
| ISiPSx | Mode Pre-set for Stereo Source x=0 None, x=1 Last Used, x=2 AnthemLogic-Cinema, x=3 AnthemLogic-Music, x=4 Dolby Surround, x=5 DTS Neural:X, x=6 DTS Virtual:X, x=7 All Channel Stereo, x=8 Mono, x=9All Channel Mono | ISiPS? returns IsiPSx | yes |
| ISiPCx | Mode Pre-set for Multi-Channel Source x=0 None, x=1 Last Used, x=2 Dolby Surround, x=3 DTS Neural:X, x=4 DTS Virtual:X, x=5 All Channel Stereo, x=6 Mono, x=7 All Channel Mono | ISiPC? returns IsiPCx | yes |
| ISiLSxxx | Set Lip Sync to xxx (0-150) ms for the Input # i (i=1-ZZ where ZZ is the number of active input configurations).  Step must be in increments of 5ms or error will result. | ISiLS? returns ISiLSxxx | yes |
| ISiITx | Input Trim x= -12 dB to +12 dB, step 0.5 dB | ISiIT? returns IsiITx | yes |


### General Configuration - Preferences

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| GCLx | Language x=0 English, x=1 Chinese, x=2 German, x=3 Spanish, x=4 French, x=5 Italian | GCL? returns GCLx | yes |
| GCTZccc | Time Zone ccc= -12.00 to 14.00 | GCTZ? returns GCTZccc | yes |
| GCBUx | Beta Updates x=0 No, x=1 Yes | GCBU? returns GCBUx | yes |
| GCDUx | Distance Units x=0 Feet, x=1 Metres | GCDU? returns GCDUx | yes |
| GCFPBx | Front panel brightness: x=0 to 100 (%), default 30% | GCFPB? returns GCFPBx (x=0-100) | yes |
| GCCWUBx | Wake-Up Brightness: x=<Front Panel brightness> to 100 (%) | GCCWUB? returns GCCWUBx | yes |
| GCOSIDx | On-Screen Display Info x=0 Off, x=1 16:9, x=2 2.4:1 | GCOSID? returns GCOSIDx | yes |
| GCFPDIx | Front Panel Display Info x=0 All, x=1 Volume only | GCFPDI? returns GCFPDIx | yes |
| GCMVSx | Master Volume Scale x=0 per cent (%), x=1 dB | GCMVS? returns GCMVSx | yes |
| GCMLx | Mute Level x= -50 to -5 (dB), 5 dB steps | GCML? returns GCMLx | yes |
| GCMMVx | Main Maximum Volume x= -40 to +10 (dB), 0.5 dB steps | GCMMV? returns GCMMVx | yes |
| GCZ2MMVx | Zone 2 Maximum Volume (MRX 740/1140, AVM 70/90 only) x= -40 to +10 (dB), 0.5 dB steps | GCZ2MMV? returns GCZ2MMVx | yes |
| GCMPOVx | Main Power-On Volume x=0 Last Used, x=1 -90 (dB) to <Main Maximum Volume>, 0.5 dB steps | GCMPOV? returns GCMPOVx | yes |
| GCZ2POVx | Zone 2 Power-On Volume (MRX 740/1140, AVM 70/90 only) x=0 Last Used, x=1 -90 (dB) to <Zone 2 Maximum Volume>, 0.5 dB steps | GCZ2POV? returns GCZ2POVx | yes |
| GCMPOIx | Main Power-On Input x=0 Last Used, <Input List> | GCMPOI? returns GCMPOIx | yes |
| GCZ2POIx | Zone 2 Power-On Input (MRX 740/1140, AVM 70/90 only) x=0 Last Used, <Input List> | GCZ2POI? returns GCZ2POIx | yes |
| GCHMMOx | Headphone Mutes Main Outputs x=0 No, x=1 Yes | GCHMMO? returns GCHMMOx | yes |
| GCDSZx | Default Streaming Zone (MRX 740/1140, AVM 70/90 only) x=0 Main, x=1 Zone 2 | GCDSZ? returns GCDSZx | yes |
| GCFCSIx | Favor Current Streaming Input (MRX 740/1140, AVM 70/90 only) x=0 No, x=1 Yes | GCFCSI? returns GCFCSIx | yes |
| GCNSPOx | No Signal Power Off x=0 5 minutes, x=1 10 minutes, x=2 20 minutes, x=3 1 hour, x=4 2 hours, x=5 6 hours, x=7 Never | GCNSPO? returns GCNSPOx | yes |
| GCSHDMIBx | Standyby HDMI Bypass x=0 Off, x=1 Last Used, x=2 to 8 HDMI 1 to 7 | GCSHHDMI? returns GCSHDMIBx | yes |
| GCCSTBYx | Set Connected Standby to Disabled (x=0) or Enabled (x=1). This must be enabled for the power-on command to operate via IP. With serial control, the power-on command need not be sent twice (once for wake-up) when this setting is enabled. | GCCSTBY? returns GCCSTBYx | yes |
| GCCECCx | CEC Control x=0 Off, x=1 On | GCCECC? returns GCCECCx | yes |
| GCCPFCx | CEC Power-Off Control x=0 Disabled, x=1 Enabled CEC must be On to operate | GCCPFC? returns GCCPFCx | yes |
| GCCTVAx | HDMI Audio to TV x=0 Off, x=1 On CEC must be Off to operate | GCCTVA? returns GCCTVAx | yes |
| GCMLOWSx | Mute Line-Out When Selecting x=0 None, x=1 to 7 HDMI 1 to 7, x=8 HDMI Audio Return Channel, x=9 to 10 Digital Coaxial 1 to 2, x=11 to 13 Digital Optical 1 to 3, x=14 to 17 Analog 1 to 4 MRX 540/740/1140 only: x=18 Analog 5 AVM 70/90 only: x=18 Phono (MM) | GCMLOW? returns GCMLOWSx | yes |
| GCMDOWSx | Mute DIGITAL-Out When Selecting x=0 None, x=1 to 7 HDMI 1 to 7, x=8 HDMI Audio Return Channel, x=9 to 10 Digital Coaxial 1 to 2, x=11 to 13 Digital Optical 1 to 3, x=14 to 17 Analog 1 to 4 MRX 540/740/1140 only: x=18 Analog 5 AVM 70/90 only: x=18 Phono (MM) | GCMDOW? returns GCMDOWSx | yes |


### General Configuration - Triggers

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | t is the trigger number: 1 to 3 |  |  |
| GCTDx | Trigger Delay x=0 None, x=1 250 ms | GCTD? returns GCTDx | yes |
| GCTtCx | Trigger control. x=0 menu control, x=1 RS-232/IP | GCTtC? Returns GCTtCx | yes |
| GCTtPx | Power MRX 540 only: x=0 Off, x=1 Main MRX 740/1140, AVM 70/90 only: x=0 Off, x=1 Main, x=2 Zone 2, x=3 Main or Zone 2 | GCTtP? returns GCTtPx | yes |
| GCTtIix | Input i=1 to ZZ (maximum 30) MRX 540 only: x=0 Off, x=1 Main MRX 740/1140, AVM 70/90 only: x=0 Off, x=1 Main, x=2 Zone 2, x=3 Main or Zone 2 | GCTtIi? returns GCTtIix | yes |


### General Configuration - Remote Control

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| GCDNccc | Device Name. 16 characters 0-9, A-Z, a-z, ' ', '-', '.', '/' | GCDN? Returns GCDNccc | yes |
| GCTCPxxxx | TCP Port x=1025 to 49150 | GCTCP? Returns GCTCPxxxx | yes |
| GCRIRx | Rear IR. X=0 Off, x=1 On | GCRIR? Returns GCRIRx | yes |
| GCFIRx | Front IR. X=0 Off, x=1 On | GCFIR? Returns GCFIRx | yes |
| GCTXSx | Tx Status x=0 Off, x=1 IP only, x=2 IP and RS-232 | GCTXS? Returns GCTXSx | yes |


### General Configuration - IP Settings

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | i=1 Ethernet, i=2 Wi-Fi |  |  |
| GCIPViA | Apply Change. Uses these preconfigured settings. | Set only |  |
| GCIPViMx | Mode. X=0 Auto (DHCP), x=1 Manual | GCIPViM? returns GCIPViMx | yes |
| GCIPViIccc | IP Address. ccc=32-bit IPV4, up to 15 characters | GCIPViI? returns GCIPViIccc | yes |
| GCIPViSccc | Subnet mask. ccc=32-bit IPV4, up to 15 characters | GCIPViS? returns GCIPViSccc | yes |
| GCIPViGccc | Gateway. ccc=32-bit IPV4, up to 15 characters | GCIPViG? returns GCIPVGiccc | yes |
| GCIPViDccc | DNS. ccc=32-bit IPV4, up to 15 characters | GCIPViD? returns GCIPVDiccc | yes |


### General Configuration - IP Status

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | Returns the settings for the active channel only |  |  |
| GCIPSTT? | Status. NM will populate with data like "Ethernet", "Wi-Fi", "Connecting", "Disconnected", etc. | GCIPSTT? returns GCIPSTccc |  |
| GCIPSTM? | Mode. X=0 Auto (DHCP), x=1 Manual | GCIPSTM? returns GCIPSTMx |  |
| GCIPSTI? | IP Address. ccc=32-bit IPV4, up to 15 characters | GCIPSTI? returns GCIPSTIccc |  |
| GCIPSTS? | Subnet. ccc=32-bit IPV4, up to 15 characters | GCIPSTS? returns GCIPSTSccc |  |
| GCIPSTG? | Gateway. ccc=32-bit IPV4, up to 15 characters | GCIPSTG? returns GCIPSTGccc |  |
| GCIPSDN? | DNS. ccc=32-bit IPV4, up to 15 characters | GCIPSTD? returns GCIPSTDccc |  |


### Main Zone and Zone 2 (common)

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | z=1 Main Zone, z=2 Zone 2 |  |  |
| ZzPOWy | Power.z=zone: 1 (main), 2 (where applicable).  y: 0=off, 1=on. | ZzPOW? returns ZxPOWy | yes |
| ZzINPy | Current Input. Select: yy=1-ZZ. Where ZZ is the number of active input configurations for the specified zone. Eg: 'Z1INP9' would select the 9th input in the main zone. | ZzINP? returns ZxINPy  e.g. "Z1INP10". | yes |
| ZzVOLsyy | Volume setting: s=sign: +/-, yy=value.  Example: Z1VOL-35 represents main zone volume set to -35 dB.  Entry is rounded to nearest valid value. | ZzVOL? returns ZzVOLsyy | yes |
| ZzVDN | Volume Down. A step is 0.5 dB. | currently returns ZzPVOLyy |  |
| ZzVUP | Volume Up. A step is 0.5 dB. | currently returns ZzPVOLyy |  |
| ZzPVOLyy | Volume Percent setting:  yy=per cent value (0 to 100%, step of 1%). | ZzPVOL? returns ZzPVOLyy | yes |
| ZzPVDN | Volume Percent Down. A step is 1% (may be 0.5, 1, 2, 3 or 4 dB). | currently returns ZzPVOLyy |  |
| ZzPVUP | Volume Percent Up. A step is 1% (may be 0.5, 1, 2, 3 or 4 dB). | currently returns ZzPVOLyy |  |
| ZzMUTy | Mute: 0=unmute, 1=mute, t=toggle | ZzMUT? returns ZzMUTy (y=0-1) | yes |
|  | Terse volume mapping table: [0% = -90 db] step 4 dB [4% = -74 dB] step 3 dB [11% = -53 dB] step 2 dB [20% = -35 dB] step 1 dB [30 % = -25 dB] step 0.5 dB [100% = +10 dB]. Converted dB round up to the next per cent. i.e. -89.5 to -86 dB round to 1%. |  |  |


### Main Zone only

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1ALMy | Audio Listening Mode: 0=None, 1=AnthemLogic-Cinema, 2=AnthemLogic-Music, 3=Dolby Surround, 4=DTS neural:X, 5=DTS Virtual:X, 5=Stereo, 6=All Channel Stereo, 7=Mono*, 8=All-Channel Mono*.  *Applicable to 2-channel source only. | Z1ALM? returns Z1ALMy | yes |
| Z1ADN | Audio Listening Mode: next lower numbered selection. |  |  |
| Z1AUP | Audio Listening Mode: next higher numbered selection. |  |  |
| Z1TONyszz | Tone setting: y=0 bass, 1 treble.  s=sign: +/-, zz=value.  Example: Z1TON0-01 represents a bass cut by 1 dB. Range is -10 dB to +10 dB with 0.5 dB steps. | Z1TONy? returns Z1TONyszz | yes |
| Z1TUPy | Tone Up. y=0 bass, 1 treble. Step is 0.5 dB. |  |  |
| Z1TDNy | Tone Down. y=0 bass, 1 treble. Step is 0.5 dB. |  |  |
| Z1BALsyyy | Balance setting: yyy=-5 to 5 with 0.5 dB steps. Examples: Z1BAL5 represents balance completely to the right; Z1BAL-5 represents balance completely to the left; Z1BAL0 is balance in the middle; Z1BAL-1.5 represents balance partly to the left. Entry is rounded to nearest valid value. | Z1BAL? returns Z1BALyyy | yes |
| Z1BLT | Shift the balance of all channels 0.5 dB to left. |  |  |
| Z1BRT | Shift the balance of all channels 0.5 dB to right. |  |  |
| Z1DSCSy | Dolby Surround Centre Spread. Y=0 off, Y=1 on | Z1DSCS? Return Z1DSCSy | yes |
| Z1LEVyszz | Level setting: y=Channels: 1=subwoofers, 5=fronts, 6=front wides, 7=center, 8=surrounds, 9=backs, A=Heights1, B=Heights2, C=Heights3, D=LFE. s=sign: +/-, zz=value. Front Wide, Height2 and Height3 are for MRX 740/1140, AVM 70/90 only. Example: Z1LEV1+01 represents fronts boosted by 1 dB.  Entry is rounded to nearest valid value. Subs, fronts, front wides, center, surrounds, backs and all heights have range -10 dB to +10 dB. LFE has range -10 dB to 0 dB. | Z1LEVy? returns Z1LEVyszz | yes |
| Z1LUPy | Level pp: y=channels: 1=subwoofers, 5=fronts, 6=front wides, 7=center, 8=surrounds, 9=backs, A=Heights1, B=Heights2, C=Heights3, D=LFE. Step is 0.5 dB. |  |  |
| Z1LDNy | Level Down: y=channels:1=subs, 5=fronts, 6=front wides, 7=center, 8=surrounds, 9=backs, A=Heights1, B=Heights2, C=Heights3, D=LFE. Step is 0.5 dB. |  |  |


### ARC Metadata

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1ARCVAL? | ARC Valid. X=0 Not valid, x=1 Valid. Can only be set externally to 0 which causes system to erase the ARC coefficients block stored in external flash. | Returns Z1ARCVALx |  |
| Z1ARCUPL? | ARC Date. 16 characters. 0-9, A-Z, a-z, ' ', '-', '.', '/' | Returns Z1ARCUPLccc |  |
| Z1ARCNAM? | ARC Name. 16 characters. 0-9, A-Z, a-z, ' ', '-', '.', '/' | Returns Z1ARCNAMccc |  |


### System Control - Audio

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1DYNy | Dolby Digital Dynamic Range (Dolby Digital 5.1 source): y=0 Normal, y=1 Reduced, y=2 Late Night. | Z1DYN? returns Z1DYNy (y=0-2) | yes |
| Z1DIA? | Query Dolby Digital dialog normalization | returns Z1DIAx where x is dB of normalization, n=not applicable | yes |


### System Control - Basic Control

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1MSGxyyyy | Display custom on-screen status message for duration of display timeout: x=row 0-3, yyyy=message (up to 32 characters). | Set only. |  |
| Z1SHCy | Show/Hide custom message. y=0 hide, y=1 show. | Z1SHC? Returns Z1SHCy | yes |
| Z1SMDx | Setup menu display: x=0 Close, x=1 Open, x=t Toggle | Z1SMD? returns Z1SMDx (x=0-1) | yes |
| ZzSIMyyyy | Simulate IR command for zone (z=1, z=2). yyyy=IR command as listed at the bottom of this document. | Set only. |  |


### Trigger Control

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| RxSETy | Trigger set: x=1 Trigger 1, x=2 Trigger 2, x=3 Trigger 3.  y=0 Off, y=1 On. Only available if trigger control has been set to RS-232/IP for the specified trigger | RxSET? returns RxSETy | yes |


### Control - Advanced Control

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| CTRLxy | Exclusive Control. x = domain (0=arc, 1=scratchpad, 2=firmware) y = action (0=released, 1=taken) ex: CTRL01 will take exclusive control over ARC (enter arc mode) | CTRLx? Return CTRLxy |  |
| CPYSxy | Copy Settings from x to y. x = Current, User, Installer, Scratchpad y = Current, User, Installer, Scratchpad ex: CPYS03 -> copy settings from current to scratchpad copying to/from scratchpad requires scratchpad exclusive control | Set only. |  |
| CPYS01 | Save User Settings. MCU will save the current settings as user settings backup. | Set only. |  |
| CPYS02 | Save Installer Settings. MCU will save the installer settings as user settings backup. | Set only. |  |
| CPYS10 | Load User Settings. MCU will reload current settings from the user settings backup. Issue ‘Bulk Settings Changed’ (BSC1) to all open connections. | Set only. |  |
| CPYS20 | Load Installer Settings. MCU will reload current settings from the installer settings backup. Issue ‘Bulk Settings Changed’ (BSC1) to all open connections. | Set only. |  |
| SPDSZ | Scratchpad Size. Query the size of the scratchpad (size in bytes of an entire binary copy of the current system settings). | SPDSZ? -> MCU returns SPDSZ<size32> where <size32> is 32 bit max size of the system settings when stored in the scratchpad. |  |
| CJFUPDx | Check for NM Update. Sent from the MCU to the NM to request that it check for updates from USB (x=0) or Network (x=1). | Set only. |  |
| UPDUSB | Check for Update via USB. MCU should first check if the USB stick has a host fw update. If yes, prompt the user to install that. Otherwise, host MCU should issue Check for NM Update from USB (CKFUPD0) to NM. | Set only. |  |
| UPDOTA | Check for Update via Network. MCU should issue Check for NM Update from Network (CKFUPD1) to the NM. | Set only. |  |
| NMWPS | WPS Pushbutton. Sent from the MCU to the NM to trigger WPS bush button. | Set only. |  |
| RWIFIS | Reset NM Wireless Settings. Sent from the MCU to the NM to request that it clear the wireless settings. Should be sent whenever ‘reset network settings’ or ‘load factory defaults | Set only. |  |
| LDFDS | Load Factory Defaults. Load the factory default settings. Afterwards, the host MCU should send RWIFIS to NM and issue ‘Bulk Settings Changed’ (BSC1) to all open connections. | Set only. |  |
| LOTFS | Reset On-the-Fly Settings. Load the factory default On-The-Fly settings. Afterwards, the Host MCU should issue ‘Bulk Settings Changed’ (BSC1) to all open connections. | Set only. |  |
| Z1EMSGrt | Exclusive Control Message. 2 rows of up to 32 characters r=0 Title, r=1 Message. t= 1 to 32 character long string: ‘ ’, ‘-‘, ‘.’, ‘/’, 0-9, A-Z, a-z |  |  |
| Z1EPRGx | Exclusive Control Progress. x=0 to 100 % progress, x=101 hide progress bar. |  |  |
| Z1SPRx | Show Prompt. x=0 Close x=1 show prompt with 1 option x=2 show prompt with 2 options x=3 show prompt with 3 options |  |  |
| Z1PROxt | Prompt Options. t is up to 16 characters for option x. x=0 Option 1 x=1 Option 2 x=2 Option 3 t=1 to 16 character long string: ‘ ’, ‘-‘, ‘.’, ‘/’, 0-9, A-Z, a-z |  |  |
| Z1PRMmsg | Prompt Message. msg is up to 32 characters for message. 1 to 32 character long string: ‘ ’, ‘-‘, ‘.’, ‘/’, 0-9, A-Z, a-z. |  |  |
| Z1PRSx | Current Prompt Selection. The current prompt selection. x=0 No selection x=1 Option 1 x=2 Option 2 x=3 Option 3 |  |  |


### System Control - Flash Access

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| PRGSxy | Program Start. x = mode (0=arc, 1 scratchpad, 2=firmware-MCU, 3=firmware-dsp, 4=firmware-fp, 5=firmware-osd) y = action (0=not ok to program, 1=ok to program) | PRGSx? returns PRGSxy |  |
| PRGRxyz | Program Resume. x = mode (0=arc, 1=scratchpad, 2=firmware-MCU, 3=firmware-dsp, 4=firmware-fp, 5=firmware-osd) y = <offset32><checksum32> -> result of resume request on success where       offset32 -> 32 bit value as hex of current write progress       checksum32 -> 32 bit crc of current write progress Whether or not the programming will resume where it left off or restart is up to the client. It could compare the checksum and offset to the data it wants to program and if they match it could resume with programming blocks, otherwise it could restart with a program start command. | PRGRx? returns PRGRxyz |  |
| PRGBxy | Program Block.  x = mode (0=arc, 1=scratchpad, 2=firmware-MCU, 3=firmware-dsp, 4=firmware-fp, 5=firmware-osd) y = <offset32><countbytes16><byte1>...<byteN>       offset32 -> 32 bit value as hex (8 chars)       countbytes16 -> 16 bit value as hex (4 chars)       byte1...byteN -> 8 bit value as hex (2 chars) |  |  |
| PRGFxy | Program Finish. x = mode (arc, scratchpad, firmware-MCU, firmware-dsp, firmware-fp, firmware-osd) y = <numberofbytes32><applicationchecksum32> When firmware programming is finished successfully the Host MCU automatically resets into the bootloader in order to update itself. When ARC coefficients programming is finished successfully the Host MCU automatically re-processes the ARC coefficients and, if valid, download them to the DSP and set ARC Coefficients => ARC Valid = valid |  |  |
| RDBLxy? | Read Block. x = mode (0=arc, 1=scratchpad, 2=firmware-MCU, 3=firmware-dsp, 4=firmware-fp, 5=firmware-osd) y = <offset32><countbytes16>       offset32 -> 32 bit value as hex (8 chars)       countbytes16 -> 16 bit value as hex (4 chars) | Host MCU responds from RDBLxyz where z = <byte1> ... <byteN>, byte1...byteN -> 8-bit value as hex (2 chars) |  |


### System Control - ARC Mode

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Z1ARCMENx | Measure with ARC EQ Applied. x=0 Disabled, x=1 Profile 1, x=2 Profile 2, x=3 Profile 3, x=4 Profile 4. |  |  |
| Z1ARCPRCx | Measure with Speaker Processing Applied. x=0 Disabled, x=1 Profile 1, x=2 Profile 2, x=3 Profile 3, x=4 Profile 4. Speaker processing means apply the crossovers, phase, level adjustments etc... |  |  |
| Z1ARCCRP | Test Tone Control. bitmask selecting weather or not the specified audio channel should play the test tone. See the Channel Bit Masks table for valid values For example: Z1ARCCRP00000011 will play the arc chirp on subwoofer 1 and the front left speaker simultaneously Note that values returned from queries of this value should return the current chirp state register from the DSP |  |  |
| Z1ARCCLOx | Chirp Level Offset. Applied to the ARC chirp vs. reference level x= -50 to +10 dB, 0.5 dB step. |  |  |


### System Control - Stream Service

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| NMSNstr | Service Name. str is hex encoded UTF8 with maximum length 64 bytes. Care should be taken to render the UTF8 characters. |  |  |
| NMTIstr | Title. str is hex encoded UTF8 with maximum length 64 bytes. Care should be taken to render the UTF8 characters. |  |  |
| NMARstr | Artist. str is hex encoded UTF8 with maximum length 64 bytes. Care should be taken to render the UTF8 characters. |  |  |
| NMALstr | Album. str is hex encoded UTF8 with maximum length 64 bytes. Care should be taken to render the UTF8 characters. |  |  |
| NMTEx | State. x=0 Stopped, x=1 transitioning, x=2 paused, x=3 playing. | NMTE? Returns NMTEx |  |
| NMPC | Pause Command. Causes plackback to pause. Sent from Host MCU to Networking module. |  |  |
| NMSC | Stop Command. Causes playback to stop. Sent from Host MCU to Networking module. |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| commant | Other Commands |  |  |
| FCCcount | Query Fault Counter Count. Query the number of fault counters on the system. Returns FCC<count> where <count> is 8-bit hex encoded ascii. | FCC? returns FCCcount |  |
| FCQx | Query Fault Counter. Queries the number of faults that have occurred for fault counter with index <#> (starts at 0). <#> sent as 8-bit hex encoded ascii. Specifics of fault counter <#> are implementation specified (ANAM should provide documentation on the meaning of each fault counter) | FCQx? returns FCQxn |  |
| FCRx | Reset Fault Counter. Reset (set to 0) the specified fault counter x. | Set only. |  |
| FCNxs | Query Fault Counter Name. Get the implementation specified name (s) of the fault counter x. | FCNx? returns FCNxs. s is 32 characters. |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| PRUID1sn | Serial Number as a text string. | PRUID1? Returns PRUID1sn |  |
| PRUID0key | Commit. key=7F36FD81-7A63-43EF-8246-270496C147F9. Sending this command commits the current factory settings to a dedicated region in flash. |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| BSC1 | Bulk Settings Changed. Sent by host MCU whenever bulk operations are performed on the Menu Settings / On-the-fly Adjustments / etc. Normally those operations would result in significant system notifications, however, the MCU can instead send BSC1 to all active connections to indicate that all cached settings should be invalidated. For example: load user settings could change hundreds of settings at once, sending notifications for each one would be wasteful. Instead, the host MCU should send BSC1. |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Sample Command Strings |  |  |  |
| To send a power-on command, send "Z1POW1;" using the semi-colon ";" command separator/terminator. |  |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Notes: |  |  |  |
| 1. Successful serial commands return ';' after the action is completed. |  |  |  |
| 2. When a recognized command cannot be executed "!E<OriginalCommand>" is returned. Ex: trigger control is set to Menu, and "R1SET1;" is sent on the serial port, then the system would return "!ER1SET1<LF>". Ex2: no tuner preset assigned for preset #03 and "T1PSL03<LF>" is sent then the system would return "!ET1PSL03<LF>" |  |  |  |
| 3. Out-of-range parameters return the message "!R<OriginalCommand>". Ex: 'Z1VOL+50;' would result in a response: '!RZ1VOL+50;' |  |  |  |
| 4. Invalid commands return the message "!I<OriginalCommand>". Ex 'HELLO;' would result in a response '!IHELLO;' |  |  |  |
| 5. Receiving a command for a zone when the zone is off (but the system is not in standby), returns the message "!Z<OriginalMessage>". |  |  |  |
| 6. Ony a few commands are valid when the system is in standby 'IDM?', 'ZxPOWy', 'ZxPOW?'. All other commands are considered 'Invalid'. |  |  |  |
| 7. Maximum command length is 256 bytes including the terminator. Maximum response length is 258 bytes. |  |  |  |
| 8. Average command processing latency must be less than 30 ms. |  |  |  |
| 9. Individual commands have a maximum processing latency of 100 ms. |  |  |  |
| 10. Systems that communicate over RS232 should wait for at least 1 s for a response before retransmision |  |  |  |
| 11. When Standby IP Control is disabled in setup menu (this saves energy), the unit can still be powered on serially but power-on command must be sent twice - wait for semicolon response before sending power-on command the second time (around 1s). To avoid having to send power-on command twice, enable Standby IP Control via SIPx command. |  |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| RS-232 Pin Configuration: |  |  |  |
| 2 - Tx |  |  |  |
| 3 - Rx |  |  |  |
| 5 - Ground |  |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| RS-232 Cable: |  |  |  |
| Straight-wired DB9 is used for PC connection. |  |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Factory Default Communication Settings: |  |  |  |
| Baud rate - 115200 |  |  |  |
| Data bits - 8 |  |  |  |
| Parity - None |  |  |  |
| Stop Bit - 1 |  |  |  |
| Flow Control - None |  |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
| Simulated IR Command values for ZxSIMyyyy (use 0 to fill in blanks Ex: Key 1 = 0001) |  |  |  |
| yyyy | Main Zone IR Key | Zone 2 IR Key |  |
| 0 | Key 0 |  |  |
| 1 | Key 1 |  |  |
| 2 | Key 2 |  |  |
| 3 | Key 3 |  |  |
| 4 | Key 4 |  |  |
| 5 | Key 5 |  |  |
| 6 | Key 6 |  |  |
| 7 | Key 7 |  |  |
| 8 | Key 8 |  |  |
| 9 | Key 9 |  |  |
| 10 | Power On | Power On |  |
| 11 | Power Off | Power Off |  |
| 12 | Setup |  |  |
| 13 | Input | Input |  |
| 14 | Mode |  |  |
| 15 | Dim |  |  |
| 16 | Level |  |  |
| 17 | Info |  |  |
| 18 | Up |  |  |
| 19 | Down |  |  |
| 20 | Left |  |  |
| 21 | Right |  |  |
| 22 | Select |  |  |
| 23 | Page Up | Next Pre-set |  |
| 24 | Page Down | Previous Pre-set |  |
| 25 | Volume Up | Volume Up |  |
| 26 | Volume Down | Volume Down |  |
| 27 | Mute Toggle | Mute Toggle |  |
| 28 | Last |  |  |
| 29 | Tone |  |  |
| 30 | Bass |  |  |
| 31 | Treble |  |  |
| 32 | Lip Sync |  |  |
| 33 | Balance |  |  |
| 34 | Dynamics |  |  |
| 35 | Clear |  |  |
| 36 | Preset |  |  |

| c1 | c2 | c3 | c4 |
|---|---|---|---|
|  | Channel | Bitmask |  |
|  | Subwoofer 1 | 00000001 |  |
|  | Subwoofer 2 | 00000002 |  |
|  | Subwoofer 3 | 00000004 |  |
|  | Subwoofer 4 | 00000008 |  |
|  | Front Left | 00000010 |  |
|  | Front Right | 00000020 |  |
|  | Front Wide Left | 00000040 |  |
|  | Front Wide Right | 00000080 |  |
|  | Center | 00000100 |  |
|  | Surround Left | 00000200 |  |
|  | Surround Right | 00000400 |  |
|  | Back Left | 00000800 |  |
|  | Back Right | 00001000 |  |
|  | Height 1 Left | 00002000 |  |
|  | Height 1 Right | 00004000 |  |
|  | Height 2 Left | 00008000 |  |
|  | Height 2 Right | 00010000 |  |
|  | Height 3 Left | 00020000 |  |
|  | Height 3 Right | 00040000 |  |

## Ark: IP Control

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Anthem MRX x10 series, MRX x20 series, and AVM 60 IP protocol |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| To communicate with the system via the network: |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1. Unit must first be powered on.  If 'IP control in standby' is enabled in the setup menu, it will enable IP control as soon as possible after AC power is connected. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2. The IP address of the unit must be known, either through the device discovery process described below, or through a static IP (setup menu setting). |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3. A TCP/IP connection to the unit must be established on the defined port (setup menu setting). |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 4. The system will treat the data coming across the TCP/IP link as if it were coming accoss the RS-232 port (all RS232 serial commands can be sent over the TCP/IP socket). |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 5. If the system has exceeded the maximum number of simultaneous connections it will forcibly close the oldest connection. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Device Discovery: |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DDP (Device Discovery Packet) version 1: |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| offset | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|  | 80 'P' | 65 'A' | 82 'R' | 67 'C' | 0 | 0 | announce | 1 | version |  |  |  | tcp_ip_port |  |  |  |
|  | device_name[0-15] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | model_name[0-15] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | serial_number[0-15] |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | Description |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | announce |  | If this bit is set then any Anthem product that receives the packet will broadcast its own copy of this packet with the appropriate parameters set. |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | version |  | current packet version |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | tcp_ip_port |  | the port that the system will listen on for incoming TCP connections |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | device_name |  | device name as defined by the user in the setup menu |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | model_name |  | model name - this string should be the same as what is returned when the device receives a IDM? query (Ex: 'MRX 710' or 'MRX 510' etc) |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | serial_number |  | MAC address |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | Notes: |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | All values are sent in network order |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | The DD packet is broadcast on the local subnet each time a device establishes a network connection. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | The DD packet is broadcast on the local subnet each time the system will be shutting down and losing the network connection. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | -> in this case the off byte will be set to 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | Every time the system receives a valid DD packet with 'announce' set to 1 it will respond by broadcasting another DD packet on the local subnet. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | Unused bits/bytes are filled with 0's. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | device_name, model_name and serial_number are not necessarily null terminated C-Style strings. |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | -> code using these strings should not assume that the last byte is a null |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Microsoft VC++ structure definition |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | #pragma pack(push,1) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | struct device_descriptor_t |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | unique_header[0x4]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | reserved1_rw0; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | reserved2_rw0; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | announce; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | powering_off; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int32 | version; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int32 | tcp_ip_port; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | device_name[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | model_name[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | __int8 | serial_number[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | void hton() { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | version = htonl(version); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | tcp_ip_port = htonl(tcp_ip_port); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | } |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | void ntoh() { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | version = ntohl(version); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | tcp_ip_port = ntohl(tcp_ip_port); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | } |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | }; |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | #pragma pack(pop) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GCC structure definition |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | struct device_descriptor_t |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | unique_header[0x4]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | reserved1_rw0; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | reserved2_rw0; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | announce; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | powering_off; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int32_t | version; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int32_t | tcp_ip_port; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | device_name[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | model_name[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | int8_t | serial_number[0x10]; |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | void hton() { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | version = htonl(version); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | tcp_ip_port = htonl(tcp_ip_port); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | } |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | c9 | c10 | c11 | c12 | c13 | c14 | c15 | c16 | c17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  | void ntoh() { |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | version = ntohl(version); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  | tcp_ip_port = ntohl(tcp_ip_port); |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  | } |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | } __attribute__ ((__packed__)); |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
