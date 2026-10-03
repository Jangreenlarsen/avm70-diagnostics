"""Ændringslog (FEATURES.md #14): et øjebliksbillede af alle værdier
("initial values") efter første fulde aflæsning, og derefter KUN
værdi-ændringer — plus markering af tabt/genoprettet forbindelse, så en
ændring der skete mens forbindelsen var nede, ikke fejltolkes som sket i
det øjeblik den blev opdaget.

`ChangeLog` holder data; `build_text()` er en ren funktion der laver den
tekstfil brugeren gemmer (engelsk, UTF-8, CRLF — samme stil som rapporten).
"""

import re
from collections import deque
from datetime import datetime, timezone

from app.protocol import catalog
from app.services.report import EOL, _field, _local, _rule, _value_text

MAX_ENTRIES = 20000
GROUP_ORDER = ["system", "version", "inputs", "zone1", "audio", "video", "zone2"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ChangeLog:
    def __init__(self) -> None:
        self.started_at: str | None = None
        self.baseline: list[dict] = []
        self._baseline_codes: set[str] = set()
        self.entries: deque[dict] = deque(maxlen=MAX_ENTRIES)
        self.dropped = 0

    @property
    def started(self) -> bool:
        return self.started_at is not None

    def clear(self) -> None:
        """Ingen log (fx ved skift til en anden enhed). Starter igen ved
        næste fulde aflæsning."""
        self.started_at = None
        self.baseline = []
        self._baseline_codes = set()
        self.entries.clear()
        self.dropped = 0

    def start(self, values: list[dict]) -> None:
        """Ny log med `values` (kun værdier med status ok) som initialværdier."""
        self.clear()
        self.started_at = _now()
        self.baseline = [
            {k: v.get(k) for k in ("code", "label", "group", "raw", "text", "status")}
            for v in values if v.get("status") == "ok" and v.get("raw") is not None
        ]
        self._baseline_codes = {v["code"] for v in self.baseline}

    def _append(self, entry: dict) -> dict:
        if len(self.entries) == self.entries.maxlen:
            self.dropped += 1
        self.entries.append(entry)
        return entry

    def add_value(self, code: str, label: str, group: str, old_raw: str | None,
                  new_raw: str, source: str, ts: str) -> dict | None:
        """Registrér en ny værdi. Returnerer posten, eller None hvis det
        ikke er en ændring (eller loggen ikke er startet)."""
        if not self.started:
            return None
        if old_raw is None:
            if code in self._baseline_codes:
                return None
            # Værdi der ikke var kendt ved start (fx et nyt input) — det er
            # også "noget der har ændret sig siden init".
            kind, old_text = "first", None
        elif old_raw == new_raw:
            return None
        else:
            kind, old_text = "change", catalog.decode(code, old_raw)
        return self._append({
            "ts": ts, "kind": kind, "code": code, "label": label, "group": group,
            "old_raw": old_raw, "old_text": old_text,
            "new_raw": new_raw, "new_text": catalog.decode(code, new_raw),
            "source": source,
        })

    def add_marker(self, text: str, ts: str | None = None) -> dict | None:
        if not self.started:
            return None
        return self._append({"ts": ts or _now(), "kind": "connection", "text": text})

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "baseline": list(self.baseline),
            "entries": list(self.entries),
            "dropped": self.dropped,
        }


# ---------------------------------------------------------------- tekstfil

def _shown(text: str | None, raw: str | None) -> str:
    if raw is None:
        return "(none)"
    if raw.strip() == "":
        return "(not set)"
    return text if text is not None else raw


def entry_line(e: dict) -> str:
    ts = _local(e["ts"])
    if e["kind"] == "connection":
        return f"{ts}  ---- {e['text']} ----"
    head = f"{ts}  {e['source']:<8}{e['label']} [{e['code']}]: "
    new = _shown(e.get("new_text"), e.get("new_raw"))
    if e["kind"] == "first":
        line = head + f"first value {new}"
        return line + (f"   (raw {e['new_raw']!r})" if new != e["new_raw"] else "")
    old = _shown(e.get("old_text"), e.get("old_raw"))
    line = head + f"{old} -> {new}"
    if old != e["old_raw"] or new != e["new_raw"]:
        line += f"   (raw {e['old_raw']!r} -> {e['new_raw']!r})"
    return line


def changelog_filename(serial: str | None, now: datetime) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]", "", (serial or "").strip()) or "unknown-serial"
    return f"AVM70_changelog_{clean}_{now.astimezone().strftime('%Y%m%d-%H%M%S')}.txt"


def build_text(log: dict, device: dict, app_version: dict, now: datetime) -> str:
    """`device`: {"model", "serial", "address", "owner"}. `now` skal være tidszone-bevidst."""
    entries = log["entries"]
    changes = sum(1 for e in entries if e["kind"] != "connection")
    out = [
        _rule("="),
        f" ANTHEM {(device.get('model') or 'AVM 70').upper()} - CHANGE LOG",
        _rule("="),
        _field("System owner", device.get("owner") or "-"),
        _field("Device", f"{device.get('model') or '?'}, serial {device.get('serial') or '?'}, {device.get('address')}"),
        _field("Log started", _local(log["started_at"]) if log["started_at"] else "not started"),
        _field("Saved", f"{now.astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}"),
        _field("Changes logged", str(changes)
               + (f" (oldest {log['dropped']} dropped - log limit {MAX_ENTRIES})" if log.get("dropped") else "")),
        _field("Generated by", f"AVM70 Diagnostics v{app_version.get('version', '?')} build {app_version.get('build', '?')}"),
        "",
        "Contains the values read when the log started, followed only by",
        "changes. Source: push = sent by the device itself, poll = found by",
        "periodic polling, refresh = found when the app re-read the values.",
    ]

    out += ["", f"INITIAL VALUES ({_local(log['started_at'])})" if log["started_at"] else "INITIAL VALUES", _rule()]
    if not log["baseline"]:
        out.append("(none - the log starts after the first complete read of the device)")
    by_group: dict[str, list[dict]] = {}
    for v in log["baseline"]:
        by_group.setdefault(v["group"], []).append(v)
    for group in GROUP_ORDER + [g for g in by_group if g not in GROUP_ORDER]:
        if group not in by_group:
            continue
        out.append(f"[{catalog.GROUP_TITLES.get(group, group)}]")
        out += [_field(v["label"], _value_text(v)) for v in by_group[group]]
        out.append("")
    if out[-1] == "":
        out.pop()

    out += ["", "CHANGES (oldest first)", _rule()]
    out += [entry_line(e) for e in entries] or ["(no changes since the log started)"]
    out += ["", _rule("="), " END OF CHANGE LOG", _rule("="), ""]
    return EOL.join(out)
