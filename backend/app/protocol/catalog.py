"""Kommandokatalog for Anthem AVM 70 (x40-serien).

Kommandoerne og deres værdi-tabeller stammer fra `anthemav`-biblioteket
(python-anthemav 1.4.2), der er afprøvet mod x40-enheder. Anthems eget
protokol-dokument ("MRXx40/AVM90/AVM70 IP/RS-232 Codes") kunne ikke hentes
automatisk. Værdi-tabellerne er derfor ikke garanteret 1:1 for AVM70, og
UI'et viser altid den rå værdi ved siden af den afkodede tekst. Probe-
funktionen (`DeviceService.probe`) afgør empirisk hvilke koder enheden
faktisk understøtter.
"""

import re
from dataclasses import dataclass, field

SYSTEM = "system"
ZONE1 = "zone1"
AUDIO = "audio"
VIDEO = "video"
ZONE2 = "zone2"
INPUTS = "inputs"

GROUP_TITLES = {
    SYSTEM: "System",
    ZONE1: "Zone 1",
    AUDIO: "Lyd (zone 1)",
    VIDEO: "Video (zone 1)",
    ZONE2: "Zone 2",
    INPUTS: "Inputs",
}

# Grupper der genforespørges ved hver polling-runde. Systeminfo ændrer sig
# ikke under drift og hentes kun ved forbindelse og manuel opdatering.
RUNTIME_GROUPS = (ZONE1, AUDIO, VIDEO, ZONE2)

ON_OFF = {"0": "Fra", "1": "Til"}


@dataclass(frozen=True)
class Command:
    code: str
    label: str
    group: str
    values: dict[str, str] = field(default_factory=dict)
    unit: str = ""
    # Værdien er et tal med foranstillede nuller ("03"), der skal slås op
    # som heltal — enheden er ikke konsekvent med antallet af cifre.
    numeric_lookup: bool = False
    is_mac: bool = False


_COMMANDS = [
    # --- System ---
    Command("IDM", "Model", SYSTEM),
    Command("IDS", "Software-version", SYSTEM),
    Command("IDB", "Software build-dato", SYSTEM),
    Command("IDH", "Hardware-version", SYSTEM),
    Command("IDR", "Region", SYSTEM),
    Command("EMAC", "Ethernet MAC", SYSTEM, is_mac=True),
    Command("WMAC", "Wi-Fi MAC", SYSTEM, is_mac=True),
    Command("GCTXS", "IP/RS-232 status-udsendelse", SYSTEM,
            {"0": "Fra", "1": "IP til", "2": "IP og RS-232 til"}, numeric_lookup=True),
    Command("GCFPB", "Frontpanel-lysstyrke", SYSTEM),
    Command("ICN", "Antal aktive inputs", SYSTEM),
    # --- Zone 1 ---
    Command("Z1POW", "Power", ZONE1, {"0": "Standby", "1": "Tændt"}),
    Command("Z1VOL", "Volumen", ZONE1, unit="dB"),
    Command("Z1PVOL", "Volumen (procent)", ZONE1, unit="%"),
    Command("Z1MUT", "Mute", ZONE1, {"0": "Fra", "1": "Muted"}),
    Command("Z1INP", "Input-nummer", ZONE1),
    # --- Lyd ---
    Command("Z1AIF", "Lydformat", AUDIO,
            {"0": "Ingen lyd", "1": "Analog", "2": "PCM", "3": "Dolby",
             "4": "DSD", "5": "DTS", "6": "Atmos"}, numeric_lookup=True),
    Command("Z1AIC", "Input-kanaler", AUDIO,
            {"0": "Ingen lyd", "1": "Andet", "2": "Mono (center)", "3": "2 kanaler",
             "4": "5.1 kanaler", "5": "6.1 kanaler", "6": "7.1 kanaler", "7": "Atmos"},
            numeric_lookup=True),
    Command("Z1ALM", "Listening mode", AUDIO,
            {"0": "Ingen", "1": "AnthemLogic Cinema", "2": "AnthemLogic Music",
             "3": "Dolby Surround", "4": "DTS Neural:X", "5": "DTS Virtual:X",
             "6": "All Channel Stereo", "7": "Mono", "8": "All Channel Mono"},
            numeric_lookup=True),
    Command("Z1AIN", "Lydformat (navn)", AUDIO),
    Command("Z1AIR", "Samplerate (navn)", AUDIO),
    Command("Z1BRT", "Bitrate", AUDIO, unit="kbps"),
    Command("Z1SRT", "Samplerate", AUDIO, unit="kHz"),
    Command("Z1DYN", "Dynamikområde (Dolby)", AUDIO,
            {"0": "Normal", "1": "Reduceret", "2": "Late Night"}, numeric_lookup=True),
    Command("Z1DIA", "Dialog-normalisering", AUDIO, unit="dB"),
    # --- Video ---
    Command("Z1VIR", "Video-opløsning", VIDEO,
            {"0": "Ingen video", "1": "Anden", "2": "1080p60", "3": "1080p50",
             "4": "1080p24", "5": "1080i60", "6": "1080i50", "7": "720p60",
             "8": "720p50", "9": "576p50", "10": "576i50", "11": "480p60",
             "12": "480i60", "13": "3D", "14": "4K", "15": "4K50", "16": "4K24"},
            numeric_lookup=True),
    Command("Z1IRH", "Aktiv vandret opløsning", VIDEO, unit="px"),
    Command("Z1IRV", "Aktiv lodret opløsning", VIDEO, unit="px"),
    # --- Zone 2 ---
    Command("Z2POW", "Power", ZONE2, {"0": "Standby", "1": "Tændt"}),
    Command("Z2VOL", "Volumen", ZONE2, unit="dB"),
    Command("Z2MUT", "Mute", ZONE2, {"0": "Fra", "1": "Muted"}),
    Command("Z2INP", "Input-nummer", ZONE2),
]

CATALOG: dict[str, Command] = {c.code: c for c in _COMMANDS}

_INPUT_RE = re.compile(r"^IS(\d+)(IN|ARC)$")
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
_BARE_MAC_RE = re.compile(r"^[0-9A-Fa-f]{12}$")


def input_commands(count: int) -> list[str]:
    """Koderne for navn og rumkorrektion (ARC) på input 1..count."""
    codes = []
    for n in range(1, count + 1):
        codes += [f"IS{n}IN", f"IS{n}ARC"]
    return codes


def lookup(code: str) -> Command | None:
    """Katalog-opslag, inkl. de dynamiske input-koder (IS<n>IN/IS<n>ARC)."""
    if code in CATALOG:
        return CATALOG[code]
    m = _INPUT_RE.match(code)
    if m:
        n, kind = m.groups()
        if kind == "IN":
            return Command(code, f"Input {n} — navn", INPUTS)
        return Command(code, f"Input {n} — rumkorrektion", INPUTS, ON_OFF)
    return None


def decode(code: str, raw: str) -> str:
    """Menneskelæselig tekst for en rå værdi. Ukendte koder/værdier gives
    tilbage uændret (aldrig en tom streng — den rå værdi er bedre end
    ingenting i en diagnostik-app)."""
    cmd = lookup(code)
    if cmd is None:
        return raw
    text = cmd.values.get(raw)
    if text is None and cmd.numeric_lookup and raw.strip().isdigit():
        text = cmd.values.get(str(int(raw)))
    if text is None and cmd.is_mac and _BARE_MAC_RE.match(raw):
        # AVM70 sender MAC uden skilletegn (set på den rigtige enhed: "501E2D3E4870").
        text = ":".join(raw[i:i + 2] for i in range(0, 12, 2)).upper()
    if text is None:
        text = raw
    # Enhed kun på rene tal — Z1BRT svarer fx "lossy input formats" på den
    # rigtige enhed, og "lossy input formats kbps" ville være vrøvl.
    if cmd.unit and text == raw and _NUMBER_RE.match(raw.strip()):
        text = f"{raw} {cmd.unit}"
    return text
