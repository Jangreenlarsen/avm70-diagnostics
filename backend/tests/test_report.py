"""Diagnoserapporten (FEATURES.md #12)."""

from datetime import datetime, timezone

import pytest

from app.services import report
from app.services.device_service import DeviceService
from app.tools.fake_avm import FakeAvm
from tests.test_service_api import api, fake, settings_for, wait_until  # noqa: F401 — fixtures

NOW = datetime(2026, 10, 2, 21, 50, 12, tzinfo=timezone.utc)


def _value(code, label, group, raw, text=None, status="ok"):
    return {"code": code, "label": label, "group": group, "raw": raw,
            "text": text if text is not None else raw, "status": status}


def _snapshot(values, log=None, traffic=None):
    return {
        "connection": {"status": "connected", "host": "10.1.1.7", "port": 14999,
                       "since": "2026-10-02T21:40:00+00:00", "last_error": None},
        "settings": {"host": "10.1.1.7", "port": 14999, "poll_interval": 2.0, "connect_timeout": 5.0,
                     "query_timeout": 1.5, "auto_reconnect": True, "auto_connect": True},
        "values": values, "log": log or [], "traffic": traffic or [],
    }


SNAP = _snapshot([
    _value("IDM", "Model", "system", "AVM 70"),
    _value("GSN", "Serial number", "version", "ALP2000256N070"),
    _value("IDS", "MCU version (main firmware)", "version", "00.80/00.03"),
    _value("RBD", "Network module — release build date", "version", ""),
    _value("EMAC", "Ethernet MAC", "system", "501E2D3E4870", "50:1E:2D:3E:48:70"),
    _value("IS2IN", "Input 2 — name", "inputs", "Blu-Ray"),
    _value("IS10IN", "Input 10 — name", "inputs", "Kodi"),
    _value("Z1ALM", "Listening mode", "audio", "3", "Dolby Surround"),
    _value("Z2VOL", "Volume", "zone2", "-35.0", "-35.0 dB", status="zone_off"),
    _value("Z1BDP", "Never read", "audio", None, None, status="unknown"),
], log=[{"ts": "2026-10-02T21:41:00+00:00", "kind": "change", "text": "Audio format: PCM → DTS", "source": "push"}],
   traffic=[{"ts": "2026-10-02T21:41:00+00:00", "dir": "rx", "line": "Z1AIF5", "origin": "push"},
            {"ts": "2026-10-02T21:41:01+00:00", "dir": "tx", "line": "IDM?", "origin": "refresh"}])


def test_report_has_all_sections_in_order_and_crlf():
    text = report.build_report(SNAP, {"version": "0.5.0", "build": "0005"}, NOW, refreshed=True)
    headings = ["1. DEVICE IDENTIFICATION", "2. FIRMWARE / VERSIONS", "3. NETWORK", "4. SYSTEM & INPUTS",
                "5. DEVICE SETTINGS", "6. FAULT COUNTERS", "7. CURRENT STATUS", "8. COMMAND SUPPORT (PROBE)",
                "9. EVENT LOG", "10. RAW PROTOCOL TRAFFIC", "11. APP SETTINGS", "END OF REPORT"]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")
    assert "ANTHEM AVM 70 - DIAGNOSTIC REPORT" in text
    assert "AVM70 Diagnostics v0.5.0 build 0005" in text
    assert "re-queried from the device immediately before export" in text


def test_report_shows_decoded_and_raw_values_and_empty_and_status():
    text = report.build_report(SNAP, {}, NOW, refreshed=True)
    assert "ALP2000256N070  [GSN]" in text                       # rå == afkodet: kun kode
    assert "Dolby Surround  [Z1ALM = '3']" in text               # afkodet + rå
    assert "50:1E:2D:3E:48:70  [EMAC = '501E2D3E4870']" in text
    assert "(not set)  [RBD = '']" in text                       # tom streng
    assert "(zone is off at last query)" in text                 # fejlstatus efter kendt værdi
    assert "(not read)  [Z1BDP]" in text                         # aldrig læst


def test_report_sorts_inputs_numerically():
    text = report.build_report(SNAP, {}, NOW, refreshed=True)
    assert text.index("Input 2 — name") < text.index("Input 10 — name")


def test_report_without_probe_and_without_connection_says_so():
    snap = {**SNAP, "connection": {**SNAP["connection"], "status": "reconnecting", "last_error": "refused"}}
    text = report.build_report(snap, {}, NOW, refreshed=False)
    assert "No probe has been run" in text
    assert "Not connected - showing the last values" in text
    assert "last error: refused" in text


def test_report_refresh_error_is_reported():
    text = report.build_report(SNAP, {}, NOW, refreshed=False, refresh_error="Connection to AVM70 lost")
    assert "Re-query before export failed (Connection to AVM70 lost)" in text


def test_report_includes_probe_table_and_traffic():
    probe = {"at": "2026-10-02T21:45:00+00:00", "results": [
        {"code": "IDM", "label": "Model", "status": "ok"},
        {"code": "Z2VOL", "label": "Volume", "status": "zone_off"},
    ]}
    text = report.build_report(SNAP, {}, NOW, refreshed=True, probe=probe)
    assert "1 of 2 commands answered" in text
    assert "Z2VOL    zone is off" in text
    assert "RX <- Z1AIF5; [push]" in text
    assert "TX -> IDM?;" in text


@pytest.mark.parametrize("serial,expected", [
    ("ALP2000256N070", "AVM70_ALP2000256N070_"),
    ("", "AVM70_unknown-serial_"),
    ("   ", "AVM70_unknown-serial_"),
    (None, "AVM70_unknown-serial_"),
    ("A/B:C*D", "AVM70_ABCD_"),            # aldrig sti-/ugyldige tegn i filnavnet
])
def test_report_filename(serial, expected):
    snap = _snapshot([_value("GSN", "Serial number", "version", serial)])
    name = report.report_filename(snap, NOW)
    assert name.startswith(expected) and name.endswith(".txt")


async def test_export_endpoint_refreshes_and_returns_text_attachment(api, fake):
    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: dev.changelog.started)  # alt læst, også fejlregistret
    await api.post("/api/probe")

    fake.received.clear()
    r = await api.get("/api/export")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert 'attachment; filename="AVM70_ALP2000256N070_' in r.headers["content-disposition"]
    assert "IDM?" in fake.received                              # frisk aflæsning før eksport
    body = r.text
    assert "re-queried from the device immediately before export" in body
    assert "commands answered" in body                           # probe med i rapporten


async def test_export_works_without_connection(api):
    r = await api.get("/api/export")
    assert r.status_code == 200
    assert "Not connected - showing the last values" in r.text
    assert "AVM70_unknown-serial_" in r.headers["content-disposition"]


def test_probe_table_names_the_zone_so_z1_and_z2_power_differ():
    probe = {"at": "2026-10-02T21:45:00+00:00", "results": [
        {"code": "Z1POW", "label": "Power", "group": "zone1", "status": "ok"},
        {"code": "Z2POW", "label": "Power", "group": "zone2", "status": "ok"},
        {"code": "GSN", "label": "Serial number", "group": "version", "status": "ok"},
    ]}
    snap = {**SNAP, "groups": {"zone1": "Zone 1", "zone2": "Zone 2", "version": "Versions"}}
    text = report.build_report(snap, {}, NOW, refreshed=True, probe=probe)
    assert "Power (Zone 1)" in text and "Power (Zone 2)" in text
    assert "Serial number (Versions)" not in text
