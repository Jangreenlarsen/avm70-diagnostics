"""Konfiguration: `.env` (standardværdier) + `data/settings.json` (ændringer
lavet i UI'et, har forrang)."""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Pakket som .exe (PyInstaller, FEATURES.md #13): frontend og version.json
# ligger i den udpakkede bundle (sys._MEIPASS), som er skrivebeskyttet og
# slettes når appen lukker — indstillinger og log skal derfor ligge i
# brugerens %LOCALAPPDATA%. En evt. .env læses ved siden af exe'en.
FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    FRONTEND_DIR = RESOURCE_DIR / "frontend"
    VERSION_FILE = RESOURCE_DIR / "version.json"
    ENV_FILE = Path(sys.executable).parent / ".env"
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "AVM70 Diagnostics"
else:
    BACKEND_DIR = Path(__file__).resolve().parent.parent
    ROOT_DIR = BACKEND_DIR.parent
    FRONTEND_DIR = ROOT_DIR / "frontend"
    VERSION_FILE = ROOT_DIR / "version.json"
    ENV_FILE = BACKEND_DIR / ".env"
    DATA_DIR = BACKEND_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOG_FILE = DATA_DIR / "avm70-diagnostics.log"

logger = logging.getLogger("avm70")


# FEATURES.md #16: systemets ejer står i rapporter og logfiler.
DEFAULT_OWNER = "Jan Green Larsen"
OWNER_MAX = 100


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    avm_host: str = "10.1.1.7"
    avm_port: int = 14999
    avm_web_port: int = 80  # AVM70's web-API (FEATURES.md #22)
    poll_interval: float = 2.0
    connect_timeout: float = 5.0
    query_timeout: float = 1.5
    auto_reconnect: bool = True
    auto_connect: bool = True
    log_poll_interval: float = 5.0
    owner: str = DEFAULT_OWNER
    app_port: int = 8070
    log_level: str = "INFO"


env = EnvSettings()


class SettingsError(ValueError):
    """Ugyldig indstilling. Beskeden vises direkte for brugeren."""


@dataclass(frozen=True)
class DeviceSettings:
    """Kommunikationsparametre for AVM70 — redigeres i UI'ets opsætningsmenu."""

    host: str
    port: int = 14999
    poll_interval: float = 2.0
    connect_timeout: float = 5.0
    query_timeout: float = 1.5
    auto_reconnect: bool = True
    auto_connect: bool = True
    log_poll_interval: float = 5.0  # log mode (FEATURES.md #15)
    owner: str = DEFAULT_OWNER      # FEATURES.md #16


FIELDS = tuple(DeviceSettings.__dataclass_fields__)


def validate(data: dict, base: DeviceSettings | None = None) -> DeviceSettings:
    """Validerer et (evt. delvist) sæt indstillinger oven på `base`.
    Rejser `SettingsError` med en besked der kan vises direkte."""
    merged = {**(asdict(base) if base else {}), **{k: v for k, v in data.items() if k in FIELDS}}
    host = merged.get("host")
    host = host.strip() if isinstance(host, str) else ""
    if host == "":
        raise SettingsError("Host/IP must not be empty")
    if any(ch.isspace() for ch in host):
        raise SettingsError("Host/IP must not contain spaces")
    try:
        port = int(merged.get("port", 14999))
        poll = float(merged.get("poll_interval", 2.0))
        conn_to = float(merged.get("connect_timeout", 5.0))
        query_to = float(merged.get("query_timeout", 1.5))
        log_poll = float(merged.get("log_poll_interval", 5.0))
    except (TypeError, ValueError):
        raise SettingsError("Port, interval and timeouts must be numbers") from None
    if not 1 <= port <= 65535:
        raise SettingsError("Port must be between 1 and 65535")
    if poll != 0 and not 0.5 <= poll <= 60:
        raise SettingsError("Poll interval must be 0 (disabled) or between 0.5 and 60 seconds")
    # Under 3 s når Windows ikke at melde en afvist forbindelse (den prøver
    # SYN igen i ~2 s), så "afvist" ville fejlagtigt blive vist som timeout.
    if not 3 <= conn_to <= 60:
        raise SettingsError("Connect timeout must be between 3 and 60 seconds")
    if not 0.2 <= query_to <= 10:
        raise SettingsError("Response timeout must be between 0.2 and 10 seconds")
    # En fuld log-cyklus over ~48 parametre tager ca. 2 s på den rigtige enhed.
    if not 2 <= log_poll <= 3600:
        raise SettingsError("Log poll interval must be between 2 and 3600 seconds")
    owner = merged.get("owner", DEFAULT_OWNER)
    owner = " ".join(owner.split()) if isinstance(owner, str) else ""
    if owner == "":
        raise SettingsError("System owner must not be empty")
    if len(owner) > OWNER_MAX:
        raise SettingsError(f"System owner must be at most {OWNER_MAX} characters")
    for flag in ("auto_reconnect", "auto_connect"):
        if not isinstance(merged.get(flag, True), bool):
            raise SettingsError(f"{flag} must be true/false")
    return DeviceSettings(
        host=host, port=port, poll_interval=poll, connect_timeout=conn_to, query_timeout=query_to,
        auto_reconnect=merged.get("auto_reconnect", True), auto_connect=merged.get("auto_connect", True),
        log_poll_interval=log_poll, owner=owner,
    )


def env_defaults() -> DeviceSettings:
    return DeviceSettings(
        host=env.avm_host, port=env.avm_port, poll_interval=env.poll_interval,
        connect_timeout=env.connect_timeout, query_timeout=env.query_timeout,
        auto_reconnect=env.auto_reconnect, auto_connect=env.auto_connect,
        log_poll_interval=env.log_poll_interval, owner=env.owner,
    )


def load_device_settings() -> DeviceSettings:
    base = env_defaults()
    if not SETTINGS_FILE.exists():
        return base
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
        return validate(data, base)
    except (OSError, ValueError) as exc:  # SettingsError er en ValueError
        logger.warning("Ignoring invalid %s (%s) — using .env values", SETTINGS_FILE, exc)
        return base


def save_device_settings(settings: DeviceSettings) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


def app_version() -> dict:
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": "ukendt", "build": "????"}
