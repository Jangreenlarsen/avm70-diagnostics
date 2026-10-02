"""Ændringsloggen (FEATURES.md #14)."""

from collections import deque
from datetime import datetime, timezone

from app.services import changelog
from app.services.changelog import ChangeLog
from app.services.device_service import DeviceService
from tests.test_service_api import api, fake, settings_for, wait_until  # noqa: F401 — fixtures

NOW = datetime(2026, 10, 3, 0, 20, 0, tzinfo=timezone.utc)
TS = "2026-10-03T00:21:00.000+00:00"


def _v(code, raw, status="ok", group="audio", label=None):
    return {"code": code, "label": label or code, "group": group, "raw": raw, "text": raw, "status": status}


# ------------------------------------------------------------------ ChangeLog

def test_nothing_is_logged_before_start():
    log = ChangeLog()
    assert log.add_value("Z1AIF", "Audio format", "audio", "2", "3", "push", TS) is None
    assert log.add_marker("x") is None
    assert log.to_dict()["entries"] == []


def test_baseline_only_contains_values_that_were_read_ok():
    log = ChangeLog()
    log.start([_v("Z1AIF", "2"), _v("Z2VOL", "-35", status="zone_off"), _v("Z1BDP", None, status="unknown")])
    assert [b["code"] for b in log.baseline] == ["Z1AIF"]


def test_only_real_changes_are_logged():
    log = ChangeLog()
    log.start([_v("Z1AIF", "2")])
    assert log.add_value("Z1AIF", "Audio format", "audio", "2", "2", "poll", TS) is None  # samme værdi
    e = log.add_value("Z1AIF", "Audio format", "audio", "2", "3", "push", TS)
    assert (e["kind"], e["old_text"], e["new_text"], e["source"]) == ("change", "PCM", "Dolby", "push")


def test_value_unknown_at_start_is_logged_as_first_value():
    log = ChangeLog()
    log.start([_v("Z1AIF", "2")])
    assert log.add_value("Z1AIF", "Audio format", "audio", None, "2", "refresh", TS) is None  # i baseline
    e = log.add_value("IS4IN", "Input 4 - name", "inputs", None, "Kodi", "refresh", TS)
    assert e["kind"] == "first" and e["new_raw"] == "Kodi"


def test_change_after_error_status_is_still_logged():
    """Event-loggen springer den over (was_ok) — ændringsloggen må ikke."""
    log = ChangeLog()
    log.start([_v("Z2VOL", "-35.0", group="zone2")])
    assert log.add_value("Z2VOL", "Volume", "zone2", "-35.0", "-30.0", "poll", TS) is not None


def test_entries_are_capped_and_dropped_count_is_kept():
    log = ChangeLog()
    log.start([])
    log.entries = deque(maxlen=3)
    for i in range(5):
        log.add_marker(f"m{i}")
    assert [e["text"] for e in log.entries] == ["m2", "m3", "m4"]
    assert log.dropped == 2


# ------------------------------------------------------------------ tekst

CHANGE = {"ts": TS, "kind": "change", "code": "Z1AIF", "label": "Audio format", "source": "push",
          "old_raw": "2", "old_text": "PCM", "new_raw": "3", "new_text": "Dolby"}


def test_entry_line_change_shows_raw_only_when_decoded_differs():
    assert changelog.entry_line(CHANGE).endswith("push    Audio format [Z1AIF]: PCM -> Dolby   (raw '2' -> '3')")
    same = {**CHANGE, "code": "IS1IN", "label": "Input 1 name", "old_raw": "A", "old_text": "A",
            "new_raw": "B", "new_text": "B"}
    assert changelog.entry_line(same).endswith("Input 1 name [IS1IN]: A -> B")


def test_entry_line_empty_first_and_marker():
    same = {**CHANGE, "old_raw": "A", "old_text": "A", "new_raw": "", "new_text": ""}
    assert "A -> (not set)" in changelog.entry_line(same)
    first = {**CHANGE, "kind": "first", "old_raw": None, "old_text": None, "new_raw": "B", "new_text": "B"}
    assert changelog.entry_line(first).endswith("first value B")
    marker = {"ts": TS, "kind": "connection", "text": "Connection lost: x"}
    assert "---- Connection lost: x ----" in changelog.entry_line(marker)


def test_build_text_has_header_baseline_by_group_and_changes():
    log = ChangeLog()
    log.start([_v("IDM", "AVM 70", group="system", label="Model"), _v("Z1AIF", "2", label="Audio format")])
    log.add_value("Z1AIF", "Audio format", "audio", "2", "3", "push", TS)
    text = changelog.build_text(log.to_dict(), {"model": "AVM 70", "serial": "ALP1", "address": "10.1.1.7:14999"},
                                {"version": "0.7.0", "build": "0007"}, NOW)
    assert "ANTHEM AVM 70 - CHANGE LOG" in text and "serial ALP1" in text
    assert text.index("INITIAL VALUES") < text.index("[System]") < text.index("[Audio (zone 1)]") < text.index("CHANGES")
    assert "Audio format [Z1AIF]: PCM -> Dolby" in text
    assert "\n" not in text.replace("\r\n", "")


def test_build_text_when_not_started():
    text = changelog.build_text(ChangeLog().to_dict(), {"address": "x"}, {}, NOW)
    assert "not started" in text and "(no changes since the log started)" in text


def test_changelog_filename():
    assert changelog.changelog_filename("ALP2000256N070", NOW).startswith("AVM70_changelog_ALP2000256N070_")
    assert changelog.changelog_filename(" ", NOW).startswith("AVM70_changelog_unknown-serial_")
    assert changelog.changelog_filename(None, NOW).startswith("AVM70_changelog_unknown-serial_")


# ------------------------------------------------------------------ service + API

async def test_log_starts_after_full_read_and_records_push_change_and_reconnect(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        codes = {b["code"] for b in dev.changelog.baseline}
        assert {"IDM", "GSN", "Z1AIF", "IS2IN"} <= codes
        assert "Z2VOL" not in codes          # zone_off -> ikke en kendt værdi
        assert not dev.changelog.entries     # ingen ændringer endnu

        await fake.push("Z1AIF", "5")
        await wait_until(lambda: any(e.get("code") == "Z1AIF" for e in dev.changelog.entries))
        e = [e for e in dev.changelog.entries if e.get("code") == "Z1AIF"][0]
        assert (e["old_text"], e["new_text"], e["source"]) == ("Atmos", "DTS", "push")

        for w in list(fake.writers):
            w.close()
        await wait_until(lambda: any("Connection lost" in (x.get("text") or "") for x in dev.changelog.entries))
        await wait_until(lambda: any((x.get("text") or "").startswith("Connected") for x in dev.changelog.entries),
                         timeout=6)
    finally:
        await dev.stop()
    assert dev.changelog.entries[-1]["text"] == "Disconnected - logging paused"


async def test_api_new_log_and_export(api, fake):
    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: dev.changelog.started)
    await fake.push("Z1AIF", "2")
    await wait_until(lambda: len(dev.changelog.entries) == 1)

    r = await api.get("/api/changelog/export")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    assert 'filename="AVM70_changelog_ALP2000256N070_' in r.headers["content-disposition"]
    assert "Audio format [Z1AIF]: Atmos -> PCM" in r.text

    body = (await api.post("/api/changelog/reset")).json()
    assert body["started_at"] and body["entries"] == []
    assert any(b["code"] == "Z1AIF" and b["raw"] == "2" for b in body["baseline"])  # ny baseline = nuværende


async def test_changelog_is_cleared_when_device_address_changes(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        old_start = dev.changelog.started_at
        await dev.apply_settings(settings_for(fake.port, host="localhost"))
        assert not dev.changelog.started          # anden enhed -> ingen gammel baseline
        await wait_until(lambda: dev.changelog.started)
        assert dev.changelog.started_at != old_start
    finally:
        await dev.stop()


async def test_new_log_without_known_values_starts_at_next_full_read():
    dev = DeviceService(settings_for(1))
    result = dev.new_changelog()
    assert result["started_at"] is None and result["baseline"] == []
