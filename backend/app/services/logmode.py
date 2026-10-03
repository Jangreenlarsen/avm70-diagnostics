"""Log mode (FEATURES.md #15): fast pollingcyklus over ALLE parametre med
en tidslinje der kan læses af et menneske og sendes til Anthem:

    00:40:00.000  INIT        48 parameters
                  Model [IDM] ............... AVM 70
    00:40:05.000  OK          48/48 polled, no changes
    00:40:10.000  CHANGE      Audio format [Z1AIF]: PCM -> Dolby   (raw '2' -> '3')
    00:40:12.345  PUSH        Audio format [Z1AIF]: Dolby -> DTS   (raw '3' -> '5')
    00:40:15.000  INCOMPLETE  47/48 polled - no response: Z1VIR

Ændringer findes ved at sammenligne med LOGGENS EGEN sidste værdi for hver
parameter (ikke appens nuværende tilstand) — ellers ville en ændring som
enheden selv har pushet, og som appen allerede har opdateret, aldrig blive
set af næste poll. En fejlstatus (fx "zone is off") er en del af værdien,
så et statusskift også logges.

`LogSession` er ren logik + filskrivning; DeviceService står for polling.
Linjerne skrives løbende til disk (append + flush), så en lang session ikke
går tabt hvis appen lukkes; i hukommelsen holdes kun de seneste til UI'et.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from app.protocol import catalog
from app.protocol.client import QueryResult
from app.services.report import EOL, _local, _rule

logger = logging.getLogger("avm70")

UI_LINES = 2000
KIND_WIDTH = 12
# FEATURES.md #17: kolonnen med retning + protokol-kommando.
CMD_WIDTH = 22
CMD_MAX = 16  # selve kommandoen; længere push-linjer afkortes
STAMP_WIDTH = 23  # "YYYY-MM-DD HH:MM:SS.mmm"
DETAIL_INDENT = " " * (STAMP_WIDTH + 2 + KIND_WIDTH)
STATUS_TEXT = {
    "invalid": "not supported",
    "out_of_range": "out of range",
    "cannot_execute": "cannot execute now",
    "zone_off": "zone is off",
    "unavailable": "not available",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds")


def _shown(value: tuple[str, str | None], code: str) -> str:
    """En parameters "værdi" er (status, rå). Afkodet tekst til loggen."""
    status, raw = value
    if status != "ok":
        return f"({STATUS_TEXT.get(status, status)})"
    if raw is None or raw.strip() == "":
        return "(not set)"
    return catalog.decode(code, raw)


def _label(code: str) -> str:
    cmd = catalog.lookup(code)
    return cmd.label if cmd else code


def command_cell(direction: str, command: str) -> str:
    """"POLL Z1AIF?" / "PUSH Z1AIF5" — afkortet så kolonnen holder bredden.
    Web-API-værdier (pseudo-kode "@...") vises som "HTTP network:info"."""
    if command.startswith("@"):
        return "HTTP network:info"
    if len(command) > CMD_MAX:
        command = command[: CMD_MAX - 3] + "..."
    return f"{direction} {command}"


def next_due(started: float, interval: float, now: float) -> float:
    """Næste tidspunkt på det faste skema started + n*interval efter `now`
    (driftfrit: en langsom cyklus forskyder ikke de følgende). Springer
    tidspunkter over der allerede er passeret."""
    if interval <= 0:
        return now
    n = int((now - started) // interval) + 1
    return started + n * interval


class LogSession:
    def __init__(self, interval: float, log_dir: Path, device: str = "", owner: str = "") -> None:
        self.interval = interval
        self.started_at = _now()
        self.stopped_at: datetime | None = None
        self.initialized = False
        self.last: dict[str, tuple[str, str | None]] = {}
        self.lines: deque[dict] = deque(maxlen=UI_LINES)
        self.counts = {"cycles": 0, "ok": 0, "changes": 0, "incomplete": 0, "push": 0}
        # Løbenummer pr. linje (BUGS.md #3): lader UI'et vise hver linje præcis
        # én gang, uanset om den kommer via SSE før eller efter et HTTP-svar.
        self._seq = 0
        self.path = log_dir / f"AVM70_log_{self.started_at.astimezone().strftime('%Y%m%d-%H%M%S')}.txt"
        self._file = None
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            self._file = open(self.path, "a", encoding="utf-8", newline="")  # noqa: SIM115 — holdes åben hele sessionen
        except OSError as exc:
            # Loggen virker stadig i UI'et; brugeren får besked i selve loggen.
            logger.error("Log mode: cannot write %s (%s)", self.path, exc)
            self.path = None
        self._write_raw([
            _rule("="),
            " ANTHEM AVM 70 - LOG MODE",
            _rule("="),
            f"Log started .......... {self.started_at.astimezone().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
            f"System owner ......... {owner or '-'}",
            f"Device ............... {device}",
            f"Poll interval ........ {interval:g} s",
            "",
            "INIT = all parameters at the first complete poll; OK = every parameter",
            "answered and nothing changed; CHANGE = changed since the last logged value",
            "(found by polling); PUSH = change sent by the device itself between polls;",
            "NEW = parameter that appeared during the session; INCOMPLETE = some",
            "parameters did not answer in that poll.",
            "COMMAND: POLL = query sent by this app (CODE?), PUSH = message sent by",
            "the device on its own (CODE + value), as on the wire.",
            _rule(),
            f"{'TIME':<{STAMP_WIDTH}}  {'TYPE':<{KIND_WIDTH}}{'COMMAND':<{CMD_WIDTH}}DESCRIPTION",
            _rule(),
        ])
        if self.path is None:
            self._add("ERROR", "Could not create the log file - lines are only kept in the app", _now())

    # ---------------------------------------------------------------- output

    @property
    def active(self) -> bool:
        return self.stopped_at is None

    def _write_raw(self, lines: list[str]) -> None:
        if self._file is None:
            return
        try:
            self._file.write(EOL.join(lines) + EOL)
            self._file.flush()
        except OSError as exc:
            logger.error("Log mode: write failed (%s)", exc)

    def _add(self, kind: str, text: str, ts: datetime, detail: list[str] | None = None, cmd: str = "") -> dict:
        stamp = _local(_iso(ts))
        line = f"{stamp}  {kind:<{KIND_WIDTH}}{cmd:<{CMD_WIDTH}}{text}"
        self._seq += 1
        entry = {"seq": self._seq, "ts": _iso(ts), "kind": kind.lower(), "cmd": cmd, "line": line,
                 "detail": detail or []}
        self.lines.append(entry)
        self._write_raw([line] + [f"{DETAIL_INDENT}{d}" for d in (detail or [])])
        return entry

    def _change_text(self, code: str, old: tuple, new: tuple) -> str:
        text = f"{_label(code)} [{code}]: {_shown(old, code)} -> {_shown(new, code)}"
        old_raw, new_raw = old[1], new[1]
        if old[0] == new[0] == "ok" and (_shown(old, code) != old_raw or _shown(new, code) != new_raw):
            text += f"   (raw {old_raw!r} -> {new_raw!r})"
        return text

    # ---------------------------------------------------------------- hændelser

    def record_cycle(self, results: list[QueryResult], ts: datetime, duration: float) -> list[dict]:
        """Én fuld pollingcyklus. Returnerer de nye linjer (til SSE)."""
        self.counts["cycles"] += 1
        polled = {r.code: (r.status, r.value if r.status == "ok" else None)
                  for r in results if r.status != "timeout"}
        missing = [r.code for r in results if r.status == "timeout"]
        total = len(results)
        out: list[dict] = []

        if not self.initialized:
            detail = [f"{command_cell('POLL', c if c.startswith('@') else c + '?'):<{CMD_WIDTH}}"
                      f"{_label(c)} {'.' * max(3, 38 - len(_label(c)))} {_shown(v, c)}"
                      for c, v in polled.items()]
            out.append(self._add("INIT", f"{len(polled)} parameters", ts, detail, cmd=f"POLL {total} commands"))
            self.last.update(polled)
            self.initialized = True
            if missing:
                out.append(self._add("INCOMPLETE", f"no response at init: {', '.join(missing)}", ts,
                                     cmd=f"POLL {total} commands"))
                self.counts["incomplete"] += 1
            return out

        for code, value in polled.items():
            old = self.last.get(code)
            if old is None:
                out.append(self._add("NEW", f"{_label(code)} [{code}]: {_shown(value, code)}", ts,
                                     cmd=command_cell("POLL", code if code.startswith("@") else code + "?")))
                self.counts["changes"] += 1
            elif old != value:
                out.append(self._add("CHANGE", self._change_text(code, old, value), ts,
                                     cmd=command_cell("POLL", code if code.startswith("@") else code + "?")))
                self.counts["changes"] += 1
            self.last[code] = value

        slow = f" (poll took {duration:.1f} s, longer than the {self.interval:g} s interval)" if duration > self.interval else ""
        if missing:
            self.counts["incomplete"] += 1
            out.append(self._add("INCOMPLETE", f"{total - len(missing)}/{total} polled - no response: {', '.join(missing)}{slow}",
                                 ts, cmd=f"POLL {total} commands"))
        elif not out:
            self.counts["ok"] += 1
            out.append(self._add("OK", f"{total}/{total} polled, no changes{slow}", ts, cmd=f"POLL {total} commands"))
        return out

    def record_push(self, code: str, raw: str, ts: datetime) -> dict | None:
        """Uopfordret ændring fra enheden mellem to cyklusser."""
        if not self.initialized:
            return None
        new = ("ok", raw)
        old = self.last.get(code)
        if old == new:
            return None
        self.last[code] = new
        self.counts["push"] += 1
        cmd = command_cell("PUSH", code + raw)
        if old is None:
            return self._add("PUSH", f"{_label(code)} [{code}]: {_shown(new, code)} (new)", ts, cmd=cmd)
        return self._add("PUSH", self._change_text(code, old, new), ts, cmd=cmd)

    def marker(self, text: str, ts: datetime | None = None) -> dict:
        return self._add("CONNECTION", text, ts or _now())

    def note(self, text: str, ts: datetime | None = None) -> dict:
        return self._add("NOTE", text, ts or _now())

    def set_interval(self, interval: float) -> dict | None:
        if interval == self.interval:
            return None
        old, self.interval = self.interval, interval
        return self.note(f"Poll interval changed from {old:g} s to {interval:g} s")

    def stop(self) -> dict:
        entry = self._add("STOPPED", f"Log mode stopped - {self.counts['cycles']} polls, "
                                     f"{self.counts['ok']} OK, {self.counts['changes']} changes, "
                                     f"{self.counts['push']} push, {self.counts['incomplete']} incomplete", _now())
        self.stopped_at = _now()
        self._write_raw([_rule("="), ""])
        if self._file is not None:
            self._file.close()
            self._file = None
        return entry

    def text(self) -> str:
        """Hele loggen som tekst: fra filen (komplet), ellers fra hukommelsen."""
        if self.path is not None:
            try:
                # read_bytes: read_text() ville oversætte filens CRLF til LF.
                return self.path.read_bytes().decode("utf-8")
            except OSError as exc:
                logger.error("Log mode: cannot read %s (%s)", self.path, exc)
        body = []
        for e in self.lines:
            body.append(e["line"])
            body += [f"{DETAIL_INDENT}{d}" for d in e["detail"]]
        return EOL.join(body) + EOL

    def to_dict(self, lines: int = 500) -> dict:
        return {
            "active": self.active,
            "interval": self.interval,
            "started_at": _iso(self.started_at),
            "stopped_at": _iso(self.stopped_at) if self.stopped_at else None,
            "initialized": self.initialized,
            "file": str(self.path) if self.path else None,
            "counts": dict(self.counts),
            "lines": list(self.lines)[-lines:],
        }
