"""Asyncio-TCP-klient til AVM70 — kun læsende (`query`).

Hvorfor ikke `anthemav`: Movie database (BUGS.md #82 dér) viste at
bibliotekets `Connection.create(auto_reconnect=False)` aldrig selv åbner
forbindelsen, og at dets uendelige retry-løkke ikke har nogen timeout. En
diagnostik-app skal desuden kunne se og sende rå linjer og spørge efter
koder biblioteket ikke kender. Derfor denne lille, egen klient.
"""

import asyncio
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

from app.protocol.catalog import blocked_reason
from app.protocol.parser import Message, StreamSplitter, parse_message

logger = logging.getLogger("avm70")

_CODE_RE = re.compile(r"^[A-Z0-9]+$")


class AvmConnectionError(Exception):
    """Forbindelsen kunne ikke åbnes eller er tabt. Beskeden er skrevet til
    at kunne vises direkte for brugeren."""


@dataclass(frozen=True)
class QueryResult:
    code: str
    status: str  # "ok" | "invalid" | "out_of_range" | "cannot_execute" | "zone_off" | "timeout"
    value: str | None = None
    raw: str | None = None


@dataclass
class _Pending:
    code: str
    origin: str
    future: asyncio.Future


TrafficCallback = Callable[[str, str, str], None]  # (direction, line, origin)
MessageCallback = Callable[[Message, str], None]  # (message, origin)
DisconnectCallback = Callable[[str], None]


class AvmClient:
    def __init__(
        self,
        host: str,
        port: int,
        on_message: MessageCallback,
        on_traffic: TrafficCallback,
        connect_timeout: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self._on_message = on_message
        self._on_traffic = on_traffic
        self._connect_timeout = connect_timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_task: asyncio.Task | None = None
        self._pending: list[_Pending] = []
        self._write_lock = asyncio.Lock()
        self._closing = False
        self.closed = asyncio.Event()
        self.disconnect_reason: str | None = None

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self.closed.is_set()

    async def connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self._connect_timeout,
            )
        except asyncio.TimeoutError:
            raise AvmConnectionError(
                f"No connection to {self.host}:{self.port} within "
                f"{self._connect_timeout:g} s (device is off, wrong IP address, "
                f"or a firewall is blocking)"
            ) from None
        except ConnectionRefusedError:
            raise AvmConnectionError(
                f"{self.host}:{self.port} refused the connection (IP Control disabled, "
                f"wrong port, or another client is already connected)"
            ) from None
        except OSError as exc:
            raise AvmConnectionError(f"Could not connect to {self.host}:{self.port}: {exc}") from None
        self._read_task = asyncio.create_task(self._read_loop())

    async def close(self) -> None:
        self._closing = True
        if self._read_task is not None:
            self._read_task.cancel()
            try:
                await self._read_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001 — oprydning; fejlen er allerede håndteret i _read_loop
                pass
        self._mark_closed("Connection closed")

    async def query(self, code: str, origin: str = "console", timeout: float = 1.5) -> QueryResult:
        """Send `<code>?;` og vent på svaret.

        Rejser `AvmConnectionError` hvis forbindelsen er (eller bliver) tabt —
        timeout er et almindeligt resultat (`status="timeout"`), ikke en fejl,
        fordi en slukket zone eller ukendt kode lovligt kan give tavshed."""
        code = code.strip().upper()
        if not _CODE_RE.match(code):
            raise ValueError(f"Invalid code: {code!r}")
        reason = blocked_reason(code)
        if reason is not None:
            # Forsvar i dybden (FEATURES.md #18): gælder konsol, probe og alt andet.
            raise ValueError(f"{code} is a {reason} command on the AVM70 and is blocked - the app is read-only")
        if not self.connected:
            raise AvmConnectionError("Not connected to AVM70")
        future = asyncio.get_running_loop().create_future()
        pending = _Pending(code, origin, future)
        self._pending.append(pending)
        try:
            await self._send(f"{code}?", origin)
            return await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
        except asyncio.TimeoutError:
            return QueryResult(code, "timeout")
        finally:
            if pending in self._pending:
                self._pending.remove(pending)

    async def _send(self, line: str, origin: str) -> None:
        async with self._write_lock:
            if not self.connected:
                raise AvmConnectionError("Not connected to AVM70")
            self._on_traffic("tx", line, origin)
            try:
                self._writer.write(f"{line};".encode("latin-1"))
                await self._writer.drain()
            except OSError as exc:
                self._mark_closed(f"Write error: {exc}")
                raise AvmConnectionError(f"Connection to AVM70 lost ({exc})") from None

    async def _read_loop(self) -> None:
        splitter = StreamSplitter()
        reason = "AVM70 closed the connection"
        try:
            while True:
                data = await self._reader.read(4096)
                if not data:
                    break
                for raw in splitter.feed(data):
                    self._dispatch(raw)
        except asyncio.CancelledError:
            raise
        except OSError as exc:
            reason = f"Connection to AVM70 lost ({exc})"
        finally:
            self._mark_closed(reason)

    def _dispatch(self, raw: str) -> None:
        msg = parse_message(raw)
        origin = self._resolve_pending(msg)
        self._on_traffic("rx", raw, origin)
        try:
            self._on_message(msg, origin)
        except Exception:  # noqa: BLE001 — en fejl i tilstandshåndteringen må ikke dræbe læse-løkken
            logger.exception("Error while handling message %r", raw)

    def _resolve_pending(self, msg: Message) -> str:
        """Find den ventende forespørgsel beskeden svarer på. Returnerer
        dens oprindelse, eller "push" hvis beskeden ikke var bestilt."""
        for p in self._pending:
            if p.future.done():
                continue
            if msg.kind == "error":
                if msg.code == p.code:
                    p.future.set_result(QueryResult(p.code, msg.error, raw=msg.raw))
                    return p.origin
            elif msg.raw.startswith(p.code):
                p.future.set_result(QueryResult(p.code, "ok", msg.raw[len(p.code):], msg.raw))
                return p.origin
        return "push"

    def _mark_closed(self, reason: str) -> None:
        if self.closed.is_set():
            return
        self.disconnect_reason = reason
        self.closed.set()
        if self._writer is not None:
            try:
                self._writer.close()
            except Exception:  # noqa: BLE001 — socket allerede død; intet at gøre
                pass
        for p in self._pending:
            if not p.future.done():
                p.future.set_exception(AvmConnectionError(reason))
        if not self._closing:
            logger.warning("AVM70 connection lost: %s", reason)
