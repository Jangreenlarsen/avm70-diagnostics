"""Opdeling og klassificering af AVM70's svar.

Enheden sender en strøm af `;`-terminerede beskeder, ofte flere i samme
TCP-pakke og nogle gange delt over to pakker. `StreamSplitter` holder på
en ufærdig rest, indtil resten af beskeden kommer.
"""

import re
from dataclasses import dataclass

from app.protocol.catalog import CATALOG

ERROR_KINDS = {
    "I": "invalid",
    "R": "out_of_range",
    "E": "cannot_execute",
    "Z": "zone_off",
}

ERROR_TEXT = {
    "invalid": "Invalid command",
    "out_of_range": "Out of range",
    "cannot_execute": "Cannot execute now",
    "zone_off": "Zone is off",
    "timeout": "No response",
}

_ZONE_SUFFIXES = sorted(
    {c.code[2:] for c in CATALOG.values() if re.match(r"^Z\d", c.code)},
    key=len,
    reverse=True,
)
_ZONE_RE = re.compile(r"^(Z\d)(" + "|".join(_ZONE_SUFFIXES) + r")(.*)$", re.S)
_INPUT_RE = re.compile(r"^(IS\d+(?:IN|ARC))(.*)$", re.S)
_FAULT_RE = re.compile(r"^(FC[NQ][0-9A-F]{4})(.*)$", re.S)  # FEATURES.md #21
_TOP_CODES = sorted(
    (c for c in CATALOG if not re.match(r"^Z\d", c)), key=len, reverse=True
)


@dataclass(frozen=True)
class Message:
    raw: str
    kind: str  # "value" | "error" | "unknown"
    code: str | None = None
    value: str | None = None
    error: str | None = None  # nøgle i ERROR_KINDS-værdierne


def parse_message(raw: str) -> Message:
    if len(raw) >= 2 and raw[0] == "!" and raw[1] in ERROR_KINDS:
        echoed = raw[2:].rstrip("?")
        return Message(raw, "error", code=echoed or None, error=ERROR_KINDS[raw[1]])
    m = _ZONE_RE.match(raw)
    if m:
        return Message(raw, "value", code=m.group(1) + m.group(2), value=m.group(3))
    m = _INPUT_RE.match(raw)
    if m:
        return Message(raw, "value", code=m.group(1), value=m.group(2))
    m = _FAULT_RE.match(raw)
    if m:
        return Message(raw, "value", code=m.group(1), value=m.group(2))
    for code in _TOP_CODES:
        if raw.startswith(code):
            return Message(raw, "value", code=code, value=raw[len(code):])
    return Message(raw, "unknown")


class StreamSplitter:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, data: bytes) -> list[str]:
        # latin-1 kan ikke fejle på nogen byte — en diagnostik-app må ikke
        # gå ned på et uventet tegn i fx et inputnavn.
        self._buffer += data.decode("latin-1")
        *complete, self._buffer = self._buffer.split(";")
        return [part.strip() for part in complete if part.strip() != ""]
