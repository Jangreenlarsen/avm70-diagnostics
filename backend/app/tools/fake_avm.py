"""Fake AVM70 — en lille TCP-server der svarer som en Anthem AVM 70.

Bruges af testsuiten og til at udvikle/verificere UI'et uden den rigtige
enhed:

    python -m app.tools.fake_avm [--port 14999] [--cycle 8]

Med `--cycle N` skifter den lydformat hvert N. sekund og pusher ændringen
uopfordret, ligesom den rigtige enhed gør.
"""

import argparse
import asyncio
import json
import logging

logger = logging.getLogger("fake_avm")

DEFAULT_VALUES = {
    "IDM": "AVM 70",
    "IDS": "1.6.15",
    "IDB": "Mar 12 2025 10:21:44",
    "IDH": "1.0",
    "IDR": "Europe",
    "IDQ": "AVM 70 EU 00.80 Sep 1 2023 09H18M47",
    "GSN": "ALP2000256N070",
    "GCDN": "AVM70 BIO",
    "DSPIDS": "00.00/00.00",
    "LCDIDS": "00.32/00.02",
    "NMSVER": "2.3.213",
    "NMHVER": "1",
    "RVER": "not approved",
    "RBD": "",
    "NMR": "",
    "NMST": "Wi-Fi",
    "EMAC": "00:1B:7C:12:34:56",
    "WMAC": "00:1B:7C:12:34:57",
    "GCTXS": "1",
    "GCFPB": "2",
    "ICN": "3",
    "IS1IN": "Apple TV",
    "IS1ARC": "1",
    "IS2IN": "Plex",
    "IS2ARC": "1",
    "IS3IN": "Blu-ray",
    "IS3ARC": "0",
    "Z1POW": "1",
    "Z1VOL": "-35.5",
    "Z1PVOL": "52",
    "Z1MUT": "0",
    "Z1INP": "2",
    "Z1AIF": "6",
    "Z1AIC": "6",
    "Z1ALM": "0",
    "Z1AIN": "Dolby TrueHD Atmos",
    "Z1AIR": "48 kHz",
    "Z1BRT": "0",
    "Z1SRT": "48",
    "Z1BDP": "24",
    "Z1DYN": "0",
    "Z1DIA": "-31",
    "Z1VIR": "16",
    "Z1IRH": "3840",
    "Z1IRV": "2160",
    "Z2POW": "0",
    # IP-status (FEATURES.md #22) - som på Jans enhed
    "GCIPSTT": "Wi-Fi", "GCIPSTM": "1", "GCIPSTI": "10.1.1.7", "GCIPSTS": "255.255.255.0",
    "GCIPSTG": "10.1.1.1", "GCIPSDN": "192.168.1.1",
    # Settings (FEATURES.md #20) - som på Jans enhed 2026-10-03
    "GCSHDMIB": "0", "GCCSTBY": "1", "GCNSPO": "3", "GCCECC": "1", "GCCPFC": "1", "GCCTVA": "0",
    "GCHMMO": "1", "GCMLOWS": "0", "GCMDOWS": "0", "GCMMV": "3.5", "GCMPOV": "-30.0", "GCMPOI": "0",
    "GCZ2MMV": "10.0", "GCZ2POV": "-35.0", "GCZ2POI": "0", "GCAU": "0", "GCBU": "1", "GCFIR": "1",
    "GCRIR": "0", "GCTCP": "14999", "GCT1C": "0", "GCT1P": "1", "GCT2C": "0", "GCT2P": "1",
    "GCT3C": "0", "GCT3P": "0",
}
ZONE2_OFF = {"Z2VOL", "Z2MUT", "Z2INP"}

# Fejlregister (FEATURES.md #21): 8 hardwaretællere + 2 kommandotællere.
_FAULT_NAMES = ["PRIAAMP", "PRIDAMP", "PRIPWR", "PRITHERMAL", "PRILOSFAN", "PRIHISFAN", "PRIH2LPSU",
                "PRIGBLTHER", "Z1AIF", "IS"]
_FAULT_COUNTS = [0, 0, 0, 0, 0, 0, 0, 0, 3, 6]
DEFAULT_VALUES_FAULTS = {"FCC": f"{len(_FAULT_NAMES):04X}"}
for _i, (_n, _c) in enumerate(zip(_FAULT_NAMES, _FAULT_COUNTS), start=1):
    DEFAULT_VALUES_FAULTS[f"FCN{_i:04X}"] = _n
    DEFAULT_VALUES_FAULTS[f"FCQ{_i:04X}"] = str(_c)

AUDIO_CYCLE = [
    {"Z1AIF": "6", "Z1AIC": "6", "Z1AIN": "Dolby TrueHD Atmos", "Z1SRT": "48"},
    {"Z1AIF": "5", "Z1AIC": "5", "Z1AIN": "DTS-HD MA 7.1", "Z1SRT": "48"},
    {"Z1AIF": "2", "Z1AIC": "3", "Z1AIN": "PCM 2.0", "Z1SRT": "44.1"},
]


def default_network_info() -> dict:
    """Web-API-svar (network:info) som på Jans enhed 2026-10-03 (FEATURES.md #22)."""
    return {
        "path": "network:info",
        "type": "value",
        "value": {"networkInfo": {
            "state": "up",
            "wireless": {"name": "wlan0", "state": "up", "ssid": "VOLDBY17", "bssid": "4C:77:6D:AD:1E:40",
                         "mac": "50:1E:2D:3E:48:71", "channel": 6, "frequency": 2437, "signalLevel": -45,
                         "encryption": "wpa_psk", "credentialsSuspect": False, "connectingStatus": "idle",
                         "addresses": [{"protocol": "ipv4", "prefix": 24, "ip": "10.1.1.7"}]},
            "wired": {"name": "eth0", "state": "down", "cableConnected": False, "mac": "50:1E:2D:3E:48:70"},
            "gateways": [{"protocol": "ipv4", "ip": "10.1.1.1"}],
            "dns": [],
            "softAp": {"name": "softap", "state": "up",
                       "aps": [{"name": "uap0", "addresses": [{"ip": "192.168.255.249"}]}]},
        }},
    }


class FakeAvm:
    def __init__(self, values: dict | None = None, single_client: bool = True) -> None:
        self.values = dict({**DEFAULT_VALUES, **DEFAULT_VALUES_FAULTS} if values is None else values)
        self.single_client = single_client
        self.writers: set[asyncio.StreamWriter] = set()
        self.received: list[str] = []
        self.server: asyncio.base_events.Server | None = None
        # Web-API (FEATURES.md #22). network_info=None -> svarer HTTP 500.
        self.network_info: dict | None = default_network_info()
        self.web_server: asyncio.base_events.Server | None = None
        self.web_requests: list[str] = []

    async def start(self, host: str = "127.0.0.1", port: int = 0) -> int:
        self.server = await asyncio.start_server(self._handle, host, port)
        return self.server.sockets[0].getsockname()[1]

    async def start_web(self, host: str = "127.0.0.1", port: int = 0) -> int:
        self.web_server = await asyncio.start_server(self._handle_web, host, port)
        return self.web_server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        for w in list(self.writers):
            w.close()
        for srv in (self.server, self.web_server):
            if srv is not None:
                srv.close()
                await srv.wait_closed()

    async def _handle_web(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request_line = (await reader.readline()).decode("latin-1").strip()
            while (await reader.readline()) not in (b"\r\n", b"\n", b""):
                pass
            path = request_line.split(" ")[1] if " " in request_line else ""
            self.web_requests.append(path)
            if path.startswith("/api/getData?path=network:info") and self.network_info is not None:
                status, body = "200 OK", json.dumps(self.network_info).encode()
            elif path.startswith("/api/getData?path=network:info"):
                status, body = "500 Internal Server Error", b"{}"
            else:
                status, body = "404 Not Found", b"{}"
            writer.write(f"HTTP/1.1 {status}\r\nContent-Type: application/json\r\n"
                         f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
            await writer.drain()
        finally:
            writer.close()

    def reply_for(self, cmd: str) -> str:
        if not cmd.endswith("?"):
            return f"!E{cmd}"  # fake'n er også kun læsende
        code = cmd[:-1]
        if code in ZONE2_OFF and self.values.get("Z2POW") == "0":
            return f"!Z{cmd}"
        if code in self.values:
            return f"{code}{self.values[code]}"
        return f"!I{cmd}"

    async def push(self, code: str, value: str) -> None:
        self.values[code] = value
        for w in list(self.writers):
            w.write(f"{code}{value};".encode("latin-1"))
            await w.drain()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if self.single_client and self.writers:
            writer.close()  # AVM70 tager kun én klient
            return
        self.writers.add(writer)
        buffer = ""
        try:
            while data := await reader.read(1024):
                buffer += data.decode("latin-1")
                *cmds, buffer = buffer.split(";")
                for cmd in cmds:
                    if cmd.strip():
                        self.received.append(cmd.strip())
                        writer.write(f"{self.reply_for(cmd.strip())};".encode("latin-1"))
                await writer.drain()
        except ConnectionError:
            pass
        finally:
            self.writers.discard(writer)
            writer.close()


async def _main(port: int, cycle: float, web_port: int | None = None) -> None:
    fake = FakeAvm()
    actual = await fake.start("127.0.0.1", port)
    logger.info("Fake AVM70 listening on 127.0.0.1:%s (Ctrl+C to stop)", actual)
    if web_port is not None:
        logger.info("Fake web API on 127.0.0.1:%s", await fake.start_web("127.0.0.1", web_port))
    i = 0
    while True:
        await asyncio.sleep(cycle if cycle > 0 else 3600)
        if cycle > 0:
            i = (i + 1) % len(AUDIO_CYCLE)
            for code, value in AUDIO_CYCLE[i].items():
                await fake.push(code, value)
            logger.info("Pushed audio format: %s", AUDIO_CYCLE[i]["Z1AIN"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=14999)
    parser.add_argument("--cycle", type=float, default=8.0)
    parser.add_argument("--web-port", type=int, default=None, help="also serve the web API (network:info)")
    args = parser.parse_args()
    logging.basicConfig(level="INFO", format="%(asctime)s %(message)s")
    try:
        asyncio.run(_main(args.port, args.cycle, args.web_port))
    except KeyboardInterrupt:
        pass
