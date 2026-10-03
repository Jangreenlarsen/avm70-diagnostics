"""Fejlregister (FEATURES.md #21)."""

import pytest

from app import config
from app.protocol import catalog
from app.protocol.parser import parse_message
from app.services.device_service import DeviceService
from tests.test_service_api import api, fake, settings_for, wait_until  # noqa: F401 — fixtures


@pytest.fixture(autouse=True)
def clean_fault_names():
    catalog.FAULT_NAMES.clear()
    yield
    catalog.FAULT_NAMES.clear()


def test_parser_handles_fault_replies():
    m = parse_message("FCQ00043")
    assert (m.kind, m.code, m.value) == ("value", "FCQ0004", "3")
    m = parse_message("FCN0004PRITHERMAL")
    assert (m.code, m.value) == ("FCN0004", "PRITHERMAL")


def test_fault_labels():
    assert catalog.lookup("FCQ0004").label == "Fault counter 0004"   # navn endnu ikke læst
    catalog.FAULT_NAMES.update({"0004": "PRITHERMAL", "0022": "Z1AIF"})
    assert catalog.lookup("FCQ0004").label == "Thermal fault (PRITHERMAL)"
    assert catalog.lookup("FCQ0022").label == "Command Z1AIF faults"
    assert catalog.lookup("FCQ0004").group == catalog.FAULTS
    assert catalog.lookup("FCN0004") is None                          # navne gemmes ikke som værdier


def test_fault_codes_and_reset_is_blocked():
    assert catalog.fault_codes(3) == ["FCQ0001", "FCQ0002", "FCQ0003"]
    assert catalog.fault_code(164) == "FCQ00A4"
    assert catalog.blocked_reason("FCR0001") is not None
    assert catalog.blocked_reason("FCQ0001") is None and catalog.blocked_reason("FCN0001") is None


async def test_faults_are_read_on_connect_before_change_log_starts(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        assert dev.faults["count"] == 10 and dev.faults["read_at"] and dev.faults["error"] is None
        assert dev.values["FCQ0004"].label == "Thermal fault (PRITHERMAL)"
        assert dev.values["FCQ0009"].raw == "3" and dev.values["FCQ0009"].label == "Command Z1AIF faults"
        # Tællerne er med i ændringsloggens initialværdier - ikke som "first value"-poster.
        assert any(b["code"] == "FCQ0001" for b in dev.changelog.baseline)
        assert not any(e.get("code", "").startswith("FCQ") for e in dev.changelog.entries)
    finally:
        await dev.stop()


async def test_missing_fault_register_gives_readable_error(fake):
    del fake.values["FCC"]
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        assert dev.faults["count"] is None
        assert "did not report its fault counters" in dev.faults["error"]
    finally:
        await dev.stop()


def test_log_mode_reads_hardware_counters_every_cycle_and_all_every_12th():
    dev = DeviceService(settings_for(1))
    assert dev._fault_codes_for_cycle(0) == []                    # ikke læst endnu
    dev.faults["count"] = 164
    assert len(dev._fault_codes_for_cycle(0)) == 164              # INIT: alle
    assert dev._fault_codes_for_cycle(1) == catalog.fault_codes(8)
    assert len(dev._fault_codes_for_cycle(12)) == 164


async def test_log_mode_logs_a_rising_hardware_counter(fake, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        dev.start_logmode(interval=0.3)
        await wait_until(lambda: dev.logmode.initialized, timeout=5)
        fake.values["FCQ0004"] = "1"                               # termisk fejl registreret
        await wait_until(lambda: any(e["kind"] == "change" and "PRITHERMAL" in e["line"] for e in dev.logmode.lines),
                         timeout=5)
        line = [e for e in dev.logmode.lines if "PRITHERMAL" in e["line"]][0]["line"]
        assert "Thermal fault (PRITHERMAL) [FCQ0004]: 0 -> 1" in line
    finally:
        await dev.shutdown()


async def test_api_faults_and_report_section(api, fake):
    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: dev.changelog.started)
    body = (await api.get("/api/faults")).json()
    assert body["count"] == 10 and len(body["counters"]) == 10
    r = await api.post("/api/faults/refresh")
    assert r.status_code == 200 and r.json()["read_at"]

    text = (await api.get("/api/export")).text
    section = text[text.index("6. FAULT COUNTERS"):text.index("7. CURRENT STATUS")]
    assert "Thermal fault (PRITHERMAL)" in section
    assert "[Command fault counters - 2 of 2 not zero]" in section
    assert "Command Z1AIF faults" in section and "Command IS faults" in section


async def test_api_faults_refresh_requires_connection(api):
    r = await api.post("/api/faults/refresh")
    assert r.status_code == 409 and r.json()["detail"] == "Not connected to AVM70"
