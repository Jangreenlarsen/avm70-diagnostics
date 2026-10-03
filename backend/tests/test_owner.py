"""Systemejer i rapporter og logfiler (FEATURES.md #16)."""

from datetime import datetime, timezone

import pytest

from app import config
from app.config import DeviceSettings, SettingsError, validate
from app.services import changelog, report
from app.services.logmode import LogSession
from tests.test_report import SNAP
from tests.test_service_api import api, fake, wait_until  # noqa: F401 — fixtures

NOW = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_default_owner_is_jan_green_larsen():
    assert DeviceSettings("10.1.1.7").owner == "Jan Green Larsen"
    assert config.env_defaults().owner == "Jan Green Larsen"


@pytest.mark.parametrize("owner", ["", "   ", "\t\n", None, 42])
def test_owner_must_not_be_empty_in_any_form(owner):
    with pytest.raises(SettingsError, match="System owner must not be empty"):
        validate({"owner": owner}, DeviceSettings("10.1.1.7"))


def test_owner_is_trimmed_and_inner_whitespace_collapsed():
    assert validate({"owner": "  Jan   Green\tLarsen "}, DeviceSettings("10.1.1.7")).owner == "Jan Green Larsen"


def test_owner_max_length():
    with pytest.raises(SettingsError, match="at most 100"):
        validate({"owner": "x" * 101}, DeviceSettings("10.1.1.7"))


def test_report_header_shows_owner():
    snap = {**SNAP, "settings": {**SNAP["settings"], "owner": "Jan Green Larsen"}}
    text = report.build_report(snap, {}, NOW, refreshed=True)
    header = text[: text.index("1. DEVICE IDENTIFICATION")]
    assert "System owner" in header and "Jan Green Larsen" in header


def test_changelog_header_shows_owner():
    text = changelog.build_text(changelog.ChangeLog().to_dict(), {"address": "x", "owner": "Jan Green Larsen"}, {}, NOW)
    assert "System owner ..." in text and "Jan Green Larsen" in text.split("INITIAL VALUES")[0]


def test_logmode_file_header_shows_owner(tmp_path):
    s = LogSession(5, tmp_path, device="d", owner="Jan Green Larsen")
    assert "System owner ......... Jan Green Larsen" in s.path.read_bytes().decode("utf-8")


async def test_owner_set_in_setup_reaches_report_and_changelog_export(api, fake):
    r = await api.put("/api/settings", json={"owner": "Jan Green Larsen (Voldby BIO)"})
    assert r.status_code == 200 and r.json()["owner"] == "Jan Green Larsen (Voldby BIO)"
    assert "Jan Green Larsen (Voldby BIO)" in (await api.get("/api/export")).text
    assert "Jan Green Larsen (Voldby BIO)" in (await api.get("/api/changelog/export")).text
    r = await api.put("/api/settings", json={"owner": "  "})
    assert r.status_code == 400 and r.json()["detail"] == "System owner must not be empty"
