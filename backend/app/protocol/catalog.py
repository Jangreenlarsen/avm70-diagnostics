"""Kommandokatalog for Anthem AVM 70 (x40-serien).

Værdi-tabellerne følger Anthems officielle x40-protokol
(docs/anthem/MRX-x40-AVM-70-90-IP-RS-232-v5.md, v5 af 5. aug. 2020).
Oprindeligt kom de fra `anthemav` (skrevet til x20), og det gav forkert
afkodning af bl.a. Z1AIC (BUGS.md #4). UI'et viser altid den rå værdi ved
siden af den afkodede tekst, så en afkodning aldrig skjuler hvad enheden
faktisk svarede.
"""

import re
from dataclasses import dataclass, field

SYSTEM = "system"
VERSION = "version"
SETTINGS = "settings"
FAULTS = "faults"
NETWORK = "network"
ZONE1 = "zone1"
AUDIO = "audio"
VIDEO = "video"
ZONE2 = "zone2"
INPUTS = "inputs"

GROUP_TITLES = {
    SYSTEM: "System",
    VERSION: "Versions",
    SETTINGS: "Settings",
    FAULTS: "Fault counters",
    NETWORK: "Network",
    ZONE1: "Zone 1",
    AUDIO: "Audio (zone 1)",
    VIDEO: "Video (zone 1)",
    ZONE2: "Zone 2",
    INPUTS: "Inputs",
}

# Grupper der genforespørges ved hver polling-runde. Systeminfo ændrer sig
# ikke under drift og hentes kun ved forbindelse og manuel opdatering.
RUNTIME_GROUPS = (ZONE1, AUDIO, VIDEO, ZONE2)
# Hentes ved forbindelse og manuel opdatering (ikke polling).
STATIC_GROUPS = (SYSTEM, VERSION, SETTINGS, NETWORK)

ON_OFF = {"0": "Off", "1": "On"}
NO_YES = {"0": "No", "1": "Yes"}
DISABLED_ENABLED = {"0": "Disabled", "1": "Enabled"}
# GCMLOWS/GCMDOWS: "mute ... out when selecting" (AVM 70/90-varianten).
_SOURCES = {"0": "None", **{str(i): f"HDMI {i}" for i in range(1, 8)}, "8": "HDMI ARC",
            "9": "Coax 1", "10": "Coax 2", "11": "Optical 1", "12": "Optical 2", "13": "Optical 3",
            **{str(i): f"Analog {i - 13}" for i in range(14, 18)}, "18": "Phono (MM)"}
_TRIGGER_POWER = {"0": "Off", "1": "Main", "2": "Zone 2", "3": "Main or Zone 2"}


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
    # FEATURES.md #22: pseudo-kode ("@...") fra AVM70's web-API, ikke en
    # protokol-kode — sendes aldrig til AvmClient.
    web: bool = False
    # Værdi der svinger fra måling til måling (Wi-Fi-signal i dBm): vises og
    # rapporteres, men logges ikke som ændring (ændringslog/event-log/log mode).
    volatile: bool = False


_COMMANDS = [
    # --- System ---
    Command("IDM", "Model", SYSTEM),
    Command("GCDN", "Device name", SYSTEM),
    Command("GCFPB", "Front panel brightness", SYSTEM, unit="%"),
    Command("ICN", "Active inputs", SYSTEM),
    # --- Netværk (FEATURES.md #22): protokol ---
    Command("NMST", "Network connection", NETWORK),
    Command("GCIPSTT", "IP status", NETWORK),
    Command("GCIPSTM", "IP mode", NETWORK, {"0": "Automatic (DHCP)", "1": "Manual (static)"}),
    Command("GCIPSTI", "IP address", NETWORK),
    Command("GCIPSTS", "Subnet mask", NETWORK),
    Command("GCIPSTG", "Gateway", NETWORK),
    Command("GCIPSDN", "DNS server", NETWORK),
    Command("EMAC", "Ethernet MAC", NETWORK, is_mac=True),
    Command("WMAC", "Wi-Fi MAC", NETWORK, is_mac=True),
    Command("GCTXS", "IP/RS-232 status broadcast", NETWORK,
            {"0": "Off", "1": "IP only", "2": "IP and RS-232"}, numeric_lookup=True),
    # --- Netværk: web-API (pseudo-koder, se app/protocol/webapi.py) ---
    Command("@NET_STATE", "Network state", NETWORK, web=True),
    Command("@WIFI_STATE", "Wi-Fi state", NETWORK, web=True),
    Command("@WIFI_SSID", "Wi-Fi network (SSID)", NETWORK, web=True),
    Command("@WIFI_BSSID", "Wi-Fi access point (BSSID)", NETWORK, web=True),
    Command("@WIFI_IP", "Wi-Fi IP address", NETWORK, web=True),
    Command("@WIFI_BAND", "Wi-Fi band", NETWORK, web=True),
    Command("@WIFI_CHANNEL", "Wi-Fi channel", NETWORK, web=True),
    Command("@WIFI_SIGNAL", "Wi-Fi signal", NETWORK, unit="dBm", web=True, volatile=True),
    Command("@WIFI_QUALITY", "Wi-Fi signal quality", NETWORK, web=True),
    Command("@WIFI_SECURITY", "Wi-Fi security", NETWORK, web=True),
    Command("@WIFI_CREDENTIALS", "Wi-Fi credentials", NETWORK, web=True),
    Command("@WIRED_CABLE", "Ethernet cable", NETWORK, web=True),
    Command("@WIRED_STATE", "Ethernet state", NETWORK, web=True),
    Command("@WIRED_IP", "Ethernet IP address", NETWORK, web=True),
    Command("@GATEWAYS", "Gateway (web API)", NETWORK, web=True),
    Command("@DNS", "DNS (web API)", NETWORK, web=True),
    Command("@SOFTAP", "Setup hotspot (soft AP)", NETWORK, web=True),
    # --- Versioner ---
    # Koder og betydning fra AVM70's egen web-UI (http://<avm>/js/merged.min.js,
    # COMMAND-tabellen under "// info" og "// network module").
    Command("IDQ", "Combined identification", VERSION),
    Command("GSN", "Serial number", VERSION),
    Command("IDS", "MCU version (main firmware)", VERSION),
    Command("DSPIDS", "DSP version", VERSION),
    Command("LCDIDS", "LCD controller version", VERSION),
    Command("IDB", "Software build date", VERSION),
    Command("IDH", "Hardware version", VERSION),
    Command("IDR", "Region", VERSION),
    Command("NMSVER", "Network module — software", VERSION),
    Command("NMHVER", "Network module — hardware", VERSION),
    Command("RVER", "Network module — release version", VERSION),
    Command("RBD", "Network module — release build date", VERSION),
    Command("NMR", "Network module — region", VERSION),
    # --- Settings (FEATURES.md #20) ---
    # Værditabeller fra den officielle x40-protokol (General Configuration).
    Command("GCSHDMIB", "Standby HDMI bypass", SETTINGS,
            {"0": "Off", "1": "Last used", **{str(i): f"HDMI {i - 1}" for i in range(2, 9)}}, numeric_lookup=True),
    Command("GCCSTBY", "Connected standby", SETTINGS, DISABLED_ENABLED),
    Command("GCNSPO", "No-signal power off", SETTINGS,
            {"0": "5 minutes", "1": "10 minutes", "2": "20 minutes", "3": "1 hour", "4": "2 hours",
             "5": "6 hours", "7": "Never"}, numeric_lookup=True),
    Command("GCCECC", "CEC control", SETTINGS, ON_OFF),
    Command("GCCPFC", "CEC power-off control", SETTINGS, DISABLED_ENABLED),
    Command("GCCTVA", "HDMI audio to TV", SETTINGS, ON_OFF),
    Command("GCHMMO", "Headphone mutes main outputs", SETTINGS, NO_YES),
    Command("GCMLOWS", "Mute line-out when selecting", SETTINGS, _SOURCES, numeric_lookup=True),
    Command("GCMDOWS", "Mute digital-out when selecting", SETTINGS, _SOURCES, numeric_lookup=True),
    Command("GCMMV", "Main max volume", SETTINGS, unit="dB"),
    Command("GCMPOV", "Main power-on volume", SETTINGS, {"0": "Last used"}, unit="dB"),
    Command("GCMPOI", "Main power-on input", SETTINGS, {"0": "Last used"}),
    Command("GCZ2MMV", "Zone 2 max volume", SETTINGS, unit="dB"),
    Command("GCZ2POV", "Zone 2 power-on volume", SETTINGS, {"0": "Last used"}, unit="dB"),
    Command("GCZ2POI", "Zone 2 power-on input", SETTINGS, {"0": "Last used"}),
    # GCAU findes ikke i protokol-dokumentet (v5, 2020); kendt fra web-UI'et.
    Command("GCAU", "Automatic updates", SETTINGS, ON_OFF),
    Command("GCBU", "Beta updates", SETTINGS, NO_YES),
    Command("GCFIR", "Front IR", SETTINGS, ON_OFF),
    Command("GCRIR", "Rear IR", SETTINGS, ON_OFF),
    Command("GCTCP", "TCP port", SETTINGS),
    *[cmd for t in (1, 2, 3) for cmd in (
        Command(f"GCT{t}C", f"Trigger {t} control", SETTINGS, {"0": "Menu", "1": "RS-232/IP"}),
        Command(f"GCT{t}P", f"Trigger {t} power", SETTINGS, _TRIGGER_POWER),
    )],
    # --- Zone 1 ---
    Command("Z1POW", "Power", ZONE1, {"0": "Standby", "1": "On"}),
    Command("Z1VOL", "Volume", ZONE1, unit="dB"),
    Command("Z1PVOL", "Volume (percent)", ZONE1, unit="%"),
    Command("Z1MUT", "Mute", ZONE1, {"0": "Off", "1": "Muted"}),
    Command("Z1INP", "Input number", ZONE1),
    # --- Lyd ---
    Command("Z1AIF", "Audio format", AUDIO,
            {"0": "No input", "1": "Analog", "2": "PCM", "3": "Dolby",
             "4": "DSD", "5": "DTS", "6": "Atmos", "7": "DTS:X"}, numeric_lookup=True),
    Command("Z1AIC", "Input channels", AUDIO,
            {"0": "No input", "1": "Other", "2": "Mono (center only)", "3": "2 channels",
             "4": "5.1 channels", "5": "7.1 channels", "6": "Atmos", "7": "DTS:X"},
            numeric_lookup=True),
    Command("Z1ALM", "Listening mode", AUDIO,
            {"0": "None", "1": "AnthemLogic Cinema", "2": "AnthemLogic Music",
             "3": "Dolby Surround", "4": "DTS Neural:X", "5": "DTS Virtual:X",
             "6": "All Channel Stereo", "7": "Mono", "8": "All Channel Mono"},
            numeric_lookup=True),
    Command("Z1AIN", "Audio format (name)", AUDIO),
    Command("Z1AIR", "Sample rate (name)", AUDIO),
    Command("Z1BRT", "Bitrate", AUDIO, unit="kbps"),
    Command("Z1SRT", "Sample rate", AUDIO, unit="kHz"),
    Command("Z1BDP", "Bit depth", AUDIO, {"0": "No input"}, unit="bit"),
    Command("Z1DYN", "Dynamic range (Dolby)", AUDIO,
            {"0": "Normal", "1": "Reduced", "2": "Late Night"}, numeric_lookup=True),
    Command("Z1DIA", "Dialog normalization", AUDIO, {"n": "Not applicable"}, unit="dB"),
    # --- Video ---
    Command("Z1VIR", "Video resolution", VIDEO,
            {"0": "No input", "1": "Other", "2": "1080p60", "3": "1080p50",
             "4": "1080p24", "5": "1080i60", "6": "1080i50", "7": "720p60",
             "8": "720p50", "9": "576p50", "10": "576i50", "11": "480p60",
             "12": "480i60", "13": "3D", "14": "4K60", "15": "4K50", "16": "4K24"},
            numeric_lookup=True),
    Command("Z1IRH", "Active horizontal resolution", VIDEO, unit="px"),
    Command("Z1IRV", "Active vertical resolution", VIDEO, unit="px"),
    # --- Zone 2 ---
    Command("Z2POW", "Power", ZONE2, {"0": "Standby", "1": "On"}),
    Command("Z2VOL", "Volume", ZONE2, unit="dB"),
    Command("Z2MUT", "Mute", ZONE2, {"0": "Off", "1": "Muted"}),
    Command("Z2INP", "Input number", ZONE2),
]

CATALOG: dict[str, Command] = {c.code: c for c in _COMMANDS}
PROTOCOL_CODES = [c.code for c in _COMMANDS if not c.web]
WEB_CODES = [c.code for c in _COMMANDS if c.web]

_INPUT_RE = re.compile(r"^IS(\d+)(IN|ARC)$")
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
_BARE_MAC_RE = re.compile(r"^[0-9A-Fa-f]{12}$")


# ---------------------------------------------------------------- spærreliste
# FEATURES.md #18. Koder der ifølge Anthems officielle x40-protokol (v5) er
# HANDLINGER. Appen sender aldrig noget til dem — heller ikke "KODE?" — fordi
# vi ikke kan vide om firmwaren behandler en forespørgsel på en ren
# handlingskode som harmløs. (Et forsøg med IDAI? gik godt, men det er ikke
# et bevis for de øvrige.)
_BLOCKED = [
    (r"LDFDS|LOTFS", "factory reset"),
    (r"CPYS", "copy/load settings"),
    (r"BSC", "bulk settings notification"),
    (r"PRG[SRBF]|PRUID", "firmware/flash programming"),
    (r"UPD|CKFUPD|CJFUPD", "firmware update"),
    (r"GCIPV", "network configuration"),
    (r"RWIFIS|RSTWFS|RWPS|NMWPS", "Wi-Fi reset/WPS"),
    (r"RDBL|R[0-9]SET", "reboot/reset"),
    (r"FCR", "fault counter reset"),
    (r"IIAI|IDAI", "add/delete input"),
    (r"CTRL", "exclusive control"),
    (r"Z[12](MSG|SHC|SIM|EMSG|EPRG)", "on-screen message / IR simulation"),
    (r"Z1ARC(MEN|PRC|CRP|CLO)", "room correction measurement / test tone"),
    (r"Z[12](VUP|VDN|PVUP|PVDN|TUP[01]|TDN[01]|LUP|LDN|AUP|ADN)", "volume/tone/level step"),
]
_BLOCKED_RE = [(re.compile(rf"^(?:{pattern})"), reason) for pattern, reason in _BLOCKED]


def blocked_reason(code: str) -> str | None:
    """Hvorfor `code` ikke må sendes, eller None hvis den er tilladt."""
    code = code.strip().upper().rstrip("?;")
    for rx, reason in _BLOCKED_RE:
        if rx.match(code):
            return reason
    return None


# ---------------------------------------------------------------- fejlregister
# FEATURES.md #21. FCC? -> antal tællere (hex); FCN<id>? -> navn; FCQ<id>? ->
# antal fejl. id er 4 hex-cifre fra 0001 — sådan bruger enhedens web-UI og
# Jans firmware det. (Protokol-dokumentet v5 siger 2 hex-cifre fra 0, men det
# svarer ikke til den firmware der kører.) Betydningen er ikke offentligt
# dokumenteret; hardware-navnene herunder er udledt af selve navnene.
HARDWARE_FAULTS = {
    "PRIAAMP": "Analog amplifier",
    "PRIDAMP": "Digital amplifier",
    "PRIPWR": "Power",
    "PRITHERMAL": "Thermal",
    "PRILOSFAN": "Fan (low speed)",
    "PRIHISFAN": "Fan (high speed)",
    "PRIH2LPSU": "Power supply",
    "PRIGBLTHER": "Global thermal",
}
HARDWARE_FAULT_COUNT = len(HARDWARE_FAULTS)  # de første tællere (0001-0008)
FAULT_NAMES: dict[str, str] = {}  # id ("0004") -> navn ("PRITHERMAL"); fyldes af DeviceService
_FAULT_RE = re.compile(r"^FCQ([0-9A-F]{4})$")


def fault_code(index: int) -> str:
    return f"FCQ{index:04X}"


def fault_codes(count: int) -> list[str]:
    return [fault_code(i) for i in range(1, count + 1)]


def fault_label(fault_id: str) -> str:
    name = FAULT_NAMES.get(fault_id)
    if name is None:
        return f"Fault counter {fault_id}"
    if name in HARDWARE_FAULTS:
        return f"{HARDWARE_FAULTS[name]} fault ({name})"
    return f"Command {name} faults"


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
    m = _FAULT_RE.match(code)
    if m:
        return Command(code, fault_label(m.group(1)), FAULTS)
    m = _INPUT_RE.match(code)
    if m:
        n, kind = m.groups()
        if kind == "IN":
            return Command(code, f"Input {n} — name", INPUTS)
        return Command(code, f"Input {n} — room correction", INPUTS, ON_OFF)
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
