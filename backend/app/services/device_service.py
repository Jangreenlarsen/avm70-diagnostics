"""Én forbindelse til AVM70, dens tilstand, polling og hændelser.

AVM70 accepterer kun én netværksklient, så hele appen deler denne ene
`DeviceService`. API-laget og SSE-abonnenterne læser tilstanden herfra og
taler aldrig med `AvmClient` direkte.
"""

import asyncio
import logging
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from app.config import DeviceSettings
from app.protocol import catalog
from app.protocol.client import AvmClient, AvmConnectionError, QueryResult
from app.protocol.parser import ERROR_TEXT, Message
from app.services.changelog import ChangeLog

logger = logging.getLogger("avm70")

RING_SIZE = 1000
BACKOFF_START = 2.0
BACKOFF_MAX = 30.0


class NotConnectedError(Exception):
    pass


class BusyError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class ValueState:
    code: str
    label: str
    group: str
    raw: str | None = None
    text: str | None = None
    status: str = "unknown"  # "ok" eller en fejlstatus fra QueryResult
    status_text: str | None = None
    updated_at: str | None = None
    changed_at: str | None = None
    source: str | None = None  # "push" | "poll" | "refresh" | "console" | "probe"


class DeviceService:
    def __init__(self, settings: DeviceSettings) -> None:
        self.settings = settings
        self._client: AvmClient | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._wake = asyncio.Event()
        self._probe_running = False
        self.last_probe: dict | None = None  # {"at": iso, "results": [...]} til rapporten
        self.changelog = ChangeLog()  # FEATURES.md #14
        self.values: dict[str, ValueState] = {}
        self.traffic: deque[dict] = deque(maxlen=RING_SIZE)
        self.log: deque[dict] = deque(maxlen=RING_SIZE)
        self.connection = {
            "status": "disconnected",
            "host": settings.host,
            "port": settings.port,
            "since": _now(),
            "last_error": None,
            "next_retry_s": None,
        }
        self._subscribers: set[asyncio.Queue] = set()
        self._init_values()

    # ------------------------------------------------------------ tilstand

    def _init_values(self) -> None:
        self.values = {
            code: ValueState(code, cmd.label, cmd.group) for code, cmd in catalog.CATALOG.items()
        }

    def snapshot(self) -> dict:
        return {
            "connection": dict(self.connection),
            "settings": asdict(self.settings),
            "groups": catalog.GROUP_TITLES,
            "values": [asdict(v) for v in self.values.values()],
            "log": list(self.log),
            "traffic": list(self.traffic)[-300:],
            "probe_running": self._probe_running,
            "changelog": self.changelog.to_dict(),
        }

    # ------------------------------------------------------------ pub/sub

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=5000)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def _publish(self, event_type: str, data: dict) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait({"type": event_type, "data": data})
            except asyncio.QueueFull:
                # En hængende browserfane må ikke få hukommelsen til at vokse
                # uendeligt; den får et frisk øjebliksbillede når den genforbinder.
                logger.warning("SSE subscriber cannot keep up — disconnecting it")
                self._subscribers.discard(q)

    def _add_log(self, kind: str, text: str, **extra) -> None:
        entry = {"ts": _now(), "kind": kind, "text": text, **extra}
        self.log.append(entry)
        self._publish("log", entry)

    def _on_traffic(self, direction: str, line: str, origin: str) -> None:
        entry = {"ts": _now(), "dir": direction, "line": line, "origin": origin}
        self.traffic.append(entry)
        self._publish("traffic", entry)

    def _set_connection(self, status: str, error: str | None = None, next_retry_s: float | None = None) -> None:
        changed = status != self.connection["status"]
        self.connection.update(
            status=status,
            host=self.settings.host,
            port=self.settings.port,
            last_error=error if error is not None else (None if status == "connected" else self.connection["last_error"]),
            next_retry_s=next_retry_s,
        )
        if changed:
            self.connection["since"] = _now()
        self._publish("connection", dict(self.connection))

    # ------------------------------------------------------------ beskeder

    def _on_message(self, msg: Message, origin: str) -> None:
        if msg.kind != "value" or msg.code is None:
            return
        cmd = catalog.lookup(msg.code)
        if cmd is None:
            return
        state = self.values.get(msg.code)
        if state is None:
            state = ValueState(msg.code, cmd.label, cmd.group)
            self.values[msg.code] = state
        self._apply_value(state, msg.value or "", origin)
        if msg.code == "ICN" and origin == "push":
            # Antallet af inputs ændret uden for en opdatering — hent navnene.
            asyncio.get_running_loop().create_task(self._refresh_inputs("refresh"))

    def _apply_value(self, state: ValueState, raw: str, source: str) -> None:
        ts = _now()
        previous = state.raw
        was_ok = state.status == "ok"
        state.raw = raw
        state.text = catalog.decode(state.code, raw)
        state.status = "ok"
        state.status_text = None
        state.updated_at = ts
        state.source = source
        if previous != raw:
            old_text = catalog.decode(state.code, previous) if previous is not None else None
            state.changed_at = ts
            if previous is not None and was_ok:
                self._add_log(
                    "change",
                    f"{state.label}: {old_text} → {state.text}",
                    code=state.code, group=state.group, old=previous, new=raw, source=source,
                )
        entry = self.changelog.add_value(state.code, state.label, state.group, previous, raw, source, ts)
        if entry is not None:
            self._publish("changelog_entry", entry)
        self._publish("value", asdict(state))

    # ------------------------------------------------------------ ændringslog

    def _changelog_marker(self, text: str) -> None:
        entry = self.changelog.add_marker(text)
        if entry is not None:
            self._publish("changelog_entry", entry)

    def _publish_changelog(self) -> None:
        self._publish("changelog", self.changelog.to_dict())

    def new_changelog(self) -> dict:
        """"Start new log": nyt øjebliksbillede af de nuværende værdier.
        Kendes der ingen værdier endnu, startes loggen ved næste fulde
        aflæsning."""
        known = [asdict(v) for v in self.values.values() if v.status == "ok"]
        if known:
            self.changelog.start(known)
            if not self.connected:
                self._changelog_marker("Log started while disconnected - initial values are the last known values")
        else:
            self.changelog.clear()
        self._add_log("info", "Change log restarted")
        self._publish_changelog()
        return self.changelog.to_dict()

    def _apply_result(self, result: QueryResult, source: str) -> None:
        """Fejlsvar/timeout ændrer status, ikke den sidst kendte værdi —
        så man stadig kan se hvad enheden sagde, før zonen gik i standby."""
        if result.status == "ok":
            return  # selve værdien er allerede sat via _on_message
        state = self.values.get(result.code)
        if state is None:
            cmd = catalog.lookup(result.code)
            if cmd is None:
                return
            state = self.values[result.code] = ValueState(result.code, cmd.label, cmd.group)
        if state.status != result.status:
            state.status = result.status
            state.status_text = ERROR_TEXT.get(result.status, result.status)
            state.updated_at = _now()
            state.source = source
            self._publish("value", asdict(state))

    # ------------------------------------------------------------ forbindelse

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.connected

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._task is not None:
            await self._task
            self._task = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def test_connection(self, settings: DeviceSettings) -> dict:
        """Prøv en kortvarig forbindelse med `settings` (uden at gemme dem):
        åbn, spørg efter model og firmware, luk. AVM70 tager kun én klient,
        så samme adresse som den aktive forbindelse kan ikke testes separat
        — dér er den aktive forbindelse selv beviset."""
        same_target = settings.host == self.settings.host and settings.port == self.settings.port
        if same_target and self.running:
            if self.connected:
                model = self.values["IDM"].text if self.values["IDM"].status == "ok" else None
                return {"ok": True, "message": f"Already connected to {settings.host}:{settings.port}", "model": model}
            return {"ok": False, "message": "The app is already trying to connect to this address — disconnect first to test"}
        client = AvmClient(
            settings.host, settings.port,
            on_message=lambda _m, _o: None, on_traffic=self._on_traffic,
            connect_timeout=settings.connect_timeout,
        )
        try:
            await client.connect()
        except AvmConnectionError as exc:
            return {"ok": False, "message": str(exc)}
        try:
            model = await client.query("IDM", "test", timeout=settings.query_timeout)
            software = await client.query("IDS", "test", timeout=settings.query_timeout)
        except AvmConnectionError as exc:
            return {"ok": False, "message": f"Connection opened but lost again: {exc}"}
        finally:
            await client.close()
        if model.status != "ok":
            return {"ok": False, "message": f"Connected to {settings.host}:{settings.port}, but the device did not answer the model query "
                                            f"({ERROR_TEXT.get(model.status, model.status)}) — is it an Anthem device?"}
        msg = f"Connected — {model.value}"
        if software.status == "ok":
            msg += f", software {software.value}"
        return {"ok": True, "message": msg, "model": model.value}

    async def apply_settings(self, settings: DeviceSettings) -> None:
        reconnect = self.running and (
            settings.host != self.settings.host or settings.port != self.settings.port
        )
        if reconnect:
            await self.stop()
        target_changed = settings.host != self.settings.host or settings.port != self.settings.port
        self.settings = settings
        if target_changed:
            self._init_values()
            self.last_probe = None
            self.changelog.clear()
            self._publish_changelog()
            self._publish("reset", self.snapshot())
        self.connection.update(host=settings.host, port=settings.port)
        self._publish("connection", dict(self.connection))
        self._wake.set()  # nyt poll-interval træder i kraft med det samme
        if reconnect:
            await self.start()

    async def _wait(self, seconds: float, client: AvmClient | None = None) -> None:
        """Vent `seconds`, men vågn straks ved stop, wake eller tabt forbindelse."""
        self._wake.clear()
        waiters = [asyncio.ensure_future(self._stop.wait()), asyncio.ensure_future(self._wake.wait())]
        if client is not None:
            waiters.append(asyncio.ensure_future(client.closed.wait()))
        try:
            await asyncio.wait(waiters, timeout=seconds, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for w in waiters:
                w.cancel()

    async def _run(self) -> None:
        delay = BACKOFF_START
        self._add_log("connection", f"Connecting to {self.settings.host}:{self.settings.port}")
        while not self._stop.is_set():
            self._set_connection("connecting")
            client = AvmClient(
                self.settings.host, self.settings.port,
                on_message=self._on_message, on_traffic=self._on_traffic,
                connect_timeout=self.settings.connect_timeout,
            )
            try:
                await client.connect()
            except AvmConnectionError as exc:
                self._add_log("error", str(exc))
                if not self.settings.auto_reconnect:
                    self._set_connection("disconnected", error=str(exc))
                    break
                self._set_connection("reconnecting", error=str(exc), next_retry_s=delay)
                await self._wait(delay)
                delay = min(delay * 2, BACKOFF_MAX)
                continue

            self._client = client
            delay = BACKOFF_START
            self._set_connection("connected")
            self._add_log("connection", f"Connected to {self.settings.host}:{self.settings.port}")
            self._changelog_marker("Connected - values re-read; changes listed next may have happened while disconnected")
            try:
                await self._refresh_all("refresh")
                while not self._stop.is_set() and client.connected:
                    interval = self.settings.poll_interval
                    await self._wait(interval if interval > 0 else 3600, client)
                    if self._stop.is_set() or not client.connected:
                        break
                    if self.settings.poll_interval > 0:
                        await self._query_many(self._runtime_codes(), "poll")
            except AvmConnectionError:
                pass  # håndteres nedenfor via client.disconnect_reason
            finally:
                self._client = None
                await client.close()

            if not self._stop.is_set():
                reason = client.disconnect_reason or "Connection closed"
                self._add_log("error", reason)
                self._changelog_marker(f"Connection lost: {reason}")
                if not self.settings.auto_reconnect:
                    self._set_connection("disconnected", error=reason)
                    break
                self._set_connection("reconnecting", error=reason, next_retry_s=delay)
                await self._wait(delay)
                delay = min(delay * 2, BACKOFF_MAX)

        if self.connection["status"] != "disconnected":
            self._set_connection("disconnected")
        self._add_log("connection", "Disconnected")
        self._changelog_marker("Disconnected - logging paused")

    # ------------------------------------------------------------ forespørgsler

    def _runtime_codes(self) -> list[str]:
        return [c.code for c in catalog.CATALOG.values() if c.group in catalog.RUNTIME_GROUPS]

    def _group_codes(self, *groups: str) -> list[str]:
        return [c.code for c in catalog.CATALOG.values() if c.group in groups]

    async def _query_many(self, codes: list[str], origin: str) -> list[QueryResult]:
        client = self._client
        if client is None:
            raise AvmConnectionError("Not connected to AVM70")
        results = []
        for code in codes:
            result = await client.query(code, origin, timeout=self.settings.query_timeout)
            self._apply_result(result, origin)
            results.append(result)
        return results

    async def _refresh_inputs(self, origin: str) -> None:
        icn = self.values.get("ICN")
        if icn is None or icn.status != "ok" or not (icn.raw or "").strip().isdigit():
            return
        count = min(int(icn.raw), 30)
        # Fjern inputs der ikke længere findes, så listen ikke viser spøgelser.
        for code in [c for c, v in self.values.items() if v.group == catalog.INPUTS]:
            if code not in catalog.input_commands(count):
                del self.values[code]
        await self._query_many(catalog.input_commands(count), origin)

    async def _refresh_all(self, origin: str) -> None:
        await self._query_many(self._group_codes(*catalog.STATIC_GROUPS), origin)
        await self._refresh_inputs(origin)
        await self._query_many(self._runtime_codes(), origin)
        self._add_log("info", "Full read of system and runtime values completed")
        if not self.changelog.started:
            self.changelog.start([asdict(v) for v in self.values.values()])
            self._add_log("info", f"Change log started with {len(self.changelog.baseline)} initial values")
            self._publish_changelog()

    async def refresh(self, group: str | None = None) -> None:
        """Genforespørg alt, eller kun én gruppe (fx "version" fra versionsmenuen)."""
        if not self.connected:
            raise NotConnectedError("Not connected to AVM70")
        if group is None:
            await self._refresh_all("refresh")
        elif group == catalog.INPUTS:
            await self._query_many(["ICN"], "refresh")
            await self._refresh_inputs("refresh")
        else:
            await self._query_many(self._group_codes(group), "refresh")

    async def raw_query(self, code: str) -> dict:
        client = self._client
        if client is None or not client.connected:
            raise NotConnectedError("Not connected to AVM70")
        result = await client.query(code, "console", timeout=self.settings.query_timeout)
        self._apply_result(result, "console")
        return {**asdict(result), "status_text": ERROR_TEXT.get(result.status), "decoded":
                catalog.decode(result.code, result.value) if result.value is not None else None}

    async def probe(self) -> list[dict]:
        if not self.connected:
            raise NotConnectedError("Not connected to AVM70")
        if self._probe_running:
            raise BusyError("A probe is already running")
        self._probe_running = True
        self._add_log("info", "Probe started")
        try:
            codes = list(catalog.CATALOG) + [c for c, v in self.values.items() if v.group == catalog.INPUTS]
            results = await self._query_many(codes, "probe")
        finally:
            self._probe_running = False
        report = []
        for r in results:
            cmd = catalog.lookup(r.code)
            report.append({
                "code": r.code,
                "label": cmd.label if cmd else r.code,
                "group": cmd.group if cmd else None,
                "status": r.status,
                "status_text": ERROR_TEXT.get(r.status),
                "value": r.value,
                "decoded": catalog.decode(r.code, r.value) if r.value is not None else None,
            })
        self.last_probe = {"at": _now(), "results": report}
        ok = sum(1 for r in results if r.status == "ok")
        self._add_log("info", f"Probe finished: {ok} of {len(results)} commands answered")
        return report
