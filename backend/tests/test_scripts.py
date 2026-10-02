"""BUGS.md #1: Windows PowerShell 5.1 læser .ps1 uden BOM som ANSI, så
ét enkelt ikke-ASCII-tegn (ø, —) kan få hele scriptet til ikke at parse."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = sorted(ROOT.glob("*.ps1")) + sorted((ROOT / "packaging").glob("*.ps1"))


def test_there_are_scripts_to_check():
    assert {p.name for p in SCRIPTS} >= {"run.ps1", "build.ps1"}


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_powershell_scripts_are_ascii(script):
    data = script.read_bytes()
    bad = [(i, b) for i, b in enumerate(data) if b > 127]
    assert not bad, f"{script.name} contains non-ASCII bytes at {bad[:5]}"
