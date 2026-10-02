"""Konfiguration: `.env` (standardværdier) + `data/settings.json` (ændringer
lavet i UI'et, har forrang)."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
FRONTEND_DIR = ROOT_DIR / "frontend"

logger = logging.getLogger("avm70")


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

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
        raise SettingsError("Host/IP må ikke være tom")
    if any(ch.isspace() for ch in host):
        raise SettingsError("Host/IP må ikke indeholde mellemrum")
    try:
        port = int(merged.get("port", 14999))
        poll = float(merged.get("poll_interval", 2.0))
        conn_to = float(merged.get("connect_timeout", 5.0))
        query_to = float(merged.get("query_timeout", 1.5))
    except (TypeError, ValueError):
        raise SettingsError("Port, interval og timeouts skal være tal") from None
    if not 1 <= port <= 65535:
        raise SettingsError("Port skal være mellem 1 og 65535")
    if poll != 0 and not 0.5 <= poll <= 60:
        raise SettingsError("Poll-interval skal være 0 (slået fra) eller mellem 0,5 og 60 sekunder")
    # Under 3 s når Windows ikke at melde en afvist forbindelse (den prøver
    # SYN igen i ~2 s), så "afvist" ville fejlagtigt blive vist som timeout.
    if not 3 <= conn_to <= 60:
        raise SettingsError("Connect-timeout skal være mellem 3 og 60 sekunder")
    if not 0.2 <= query_to <= 10:
        raise SettingsError("Svar-timeout skal være mellem 0,2 og 10 sekunder")
    for flag in ("auto_reconnect", "auto_connect"):
        if not isinstance(merged.get(flag, True), bool):
            raise SettingsError(f"{flag} skal være sand/falsk")
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
            raise ValueError("forventede et JSON-objekt")
        return validate(data, base)
    except (OSError, ValueError) as exc:  # SettingsError er en ValueError
        logger.warning("Ignorerer ugyldig %s (%s) — bruger .env-værdier", SETTINGS_FILE, exc)
        return base


def save_device_settings(settings: DeviceSettings) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


def app_version() -> dict:
    try:
        return json.loads((ROOT_DIR / "version.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": "ukendt", "build": "????"}
