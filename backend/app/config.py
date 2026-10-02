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


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    avm_host: str = "10.1.1.7"
    avm_port: int = 14999
    poll_interval: float = 2.0
    connect_timeout: float = 5.0
    query_timeout: float = 1.5
    auto_reconnect: bool = True
    auto_connect: bool = True
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
    for flag in ("auto_reconnect", "auto_connect"):
        if not isinstance(merged.get(flag, True), bool):
            raise SettingsError(f"{flag} must be true/false")
    return DeviceSettings(
        host, port, poll, conn_to, query_to,
        merged.get("auto_reconnect", True), merged.get("auto_connect", True),
    )


def env_defaults() -> DeviceSettings:
    return DeviceSettings(
        env.avm_host, env.avm_port, env.poll_interval, env.connect_timeout,
        env.query_timeout, env.auto_reconnect, env.auto_connect,
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
