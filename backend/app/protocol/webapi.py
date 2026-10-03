"""AVM70's web-API (port 80) — kun læsning (FEATURES.md #22).

Enhedens egen web-UI henter netværksdetaljer fra
`GET /api/getData?path=network:info&roles=@all`. Det er en anden kanal end
TCP-protokollen på 14999 og påvirker ikke den eneste protokolforbindelse.
Resultatet oversættes til pseudo-koder ("@WIFI_SSID" …), så de kan vises,
rapporteres og logges på samme måde som protokol-værdier.

urllib (i en tråd) frem for et HTTP-bibliotek: ingen ekstra afhængighed i
den pakkede exe.
"""

import asyncio
import json
import urllib.error
import urllib.request

NETWORK_INFO_PATH = "/api/getData?path=network:info&roles=@all"
SOURCE = "HTTP network:info"


class WebApiError(Exception):
    """Web-API'et kunne ikke læses. Beskeden kan vises direkte."""


def signal_quality(dbm: int) -> str:
    """Grov klasse til log mode (dBm svinger fra måling til måling)."""
    if dbm >= -55:
        return "Excellent"
    if dbm >= -65:
        return "Good"
    if dbm >= -75:
        return "Fair"
    return "Poor"


def band(frequency_mhz: int) -> str:
    if 2400 <= frequency_mhz < 2500:
        return "2.4 GHz"
    if 4900 <= frequency_mhz < 5900:
        return "5 GHz"
    if 5925 <= frequency_mhz < 7125:
        return "6 GHz"
    return f"{frequency_mhz} MHz"


def _ips(section: dict) -> str:
    ips = [a.get("ip") for a in section.get("addresses") or [] if a.get("ip")]
    return ", ".join(ips) if ips else "(none)"


def map_network_info(payload: dict) -> dict[str, str]:
    """`network:info`-svaret -> {pseudo-kode: tekst}. Felter der mangler i
    svaret udelades (så de ikke fejlagtigt vises som tomme værdier)."""
    try:
        info = payload["value"]["networkInfo"]
    except (KeyError, TypeError):
        raise WebApiError("Unexpected answer from the AVM70 web API (no networkInfo)") from None
    out: dict[str, str] = {}
    if "state" in info:
        out["@NET_STATE"] = str(info["state"])
    wl = info.get("wireless")
    if isinstance(wl, dict):
        out["@WIFI_STATE"] = str(wl.get("state", ""))
        out["@WIFI_SSID"] = str(wl.get("ssid", ""))
        out["@WIFI_BSSID"] = str(wl.get("bssid", ""))
        out["@WIFI_IP"] = _ips(wl)
        if wl.get("channel") is not None:
            out["@WIFI_CHANNEL"] = str(wl["channel"])
        if isinstance(wl.get("frequency"), (int, float)):
            out["@WIFI_BAND"] = band(int(wl["frequency"]))
        if isinstance(wl.get("signalLevel"), (int, float)):
            out["@WIFI_SIGNAL"] = str(int(wl["signalLevel"]))
            out["@WIFI_QUALITY"] = signal_quality(int(wl["signalLevel"]))
        if wl.get("encryption") is not None:
            out["@WIFI_SECURITY"] = str(wl["encryption"])
        if wl.get("credentialsSuspect") is not None:
            out["@WIFI_CREDENTIALS"] = "Suspect" if wl["credentialsSuspect"] else "OK"
    wd = info.get("wired")
    if isinstance(wd, dict):
        if wd.get("cableConnected") is not None:
            out["@WIRED_CABLE"] = "Connected" if wd["cableConnected"] else "Not connected"
        out["@WIRED_STATE"] = str(wd.get("state", ""))
        out["@WIRED_IP"] = _ips(wd)
    if "gateways" in info:
        gws = [g.get("ip") for g in info.get("gateways") or [] if g.get("ip")]
        out["@GATEWAYS"] = ", ".join(gws) if gws else "(none)"
    if "dns" in info:
        dns = [d if isinstance(d, str) else d.get("ip") for d in info.get("dns") or []]
        dns = [d for d in dns if d]
        out["@DNS"] = ", ".join(dns) if dns else "(none reported)"
    sa = info.get("softAp")
    if isinstance(sa, dict):
        ips = [a.get("ip") for ap in sa.get("aps") or [] for a in ap.get("addresses") or [] if a.get("ip")]
        state = str(sa.get("state", ""))
        out["@SOFTAP"] = f"{state} ({', '.join(ips)})" if ips and state == "up" else state
    return out


def _get_json(url: str, timeout: float) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise WebApiError(f"AVM70 web API answered HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise WebApiError(f"AVM70 web API not reachable ({reason})") from None
    except ValueError:
        raise WebApiError("AVM70 web API returned invalid JSON") from None


async def fetch_network_info(host: str, port: int = 80, timeout: float = 4.0) -> dict[str, str]:
    url = f"http://{host}:{port}{NETWORK_INFO_PATH}"
    payload = await asyncio.to_thread(_get_json, url, timeout)
    return map_network_info(payload)
