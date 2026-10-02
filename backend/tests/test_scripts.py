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


PY_SOURCES = sorted((ROOT / "backend" / "app").rglob("*.py")) + sorted((ROOT / "backend" / "tests").rglob("*.py")) \
    + sorted((ROOT / "packaging").glob("*.py"))


@pytest.mark.parametrize("source", PY_SOURCES, ids=lambda p: str(p.relative_to(ROOT)))
def test_python_sources_have_no_invalid_escape_sequences(source):
    """BUGS.md #2: en ugyldig escape-sekvens (fx en Windows-sti med enkelt
    backslash i en almindelig streng) giver kun en SyntaxWarning når filen
    kompileres på ny (ikke fra .pyc-cachen) — derfor dukkede advarslen op
    sporadisk. Kompilér eksplicit med advarsler som fejl."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
