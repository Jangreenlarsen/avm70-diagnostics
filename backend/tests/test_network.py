"""Netværksmenu: IP-status + AVM70's web-API (FEATURES.md #22)."""

import pytest

from app import config
from app.protocol import catalog, webapi
from app.services.device_service import DeviceService
from app.tools.fake_avm import default_network_info
from tests.test_service_api import fake, settings_for, wait_until  # noqa: F401 — fixtures


# ------------------------------------------------------------------ mapping

def test_map_network_info_from_real_device_answer():
    data = webapi.map_network_info(default_network_info())
    assert data["@WIFI_SSID"] == "VOLDBY17"
    assert data["@WIFI_BAND"] == "2.4 GHz" and data["@WIFI_CHANNEL"] == "6"
    assert data["@WIFI_SIGNAL"] == "-45" and data["@WIFI_QUALITY"] == "Excellent"
    assert data["@WIFI_IP"] == "10.1.1.7"
    assert data["@WIRED_CABLE"] == "Not connected" and data["@WIRED_STATE"] == "down"
    assert data["@WIRED_IP"] == "(none)"
    assert data["@GATEWAYS"] == "10.1.1.1"
    assert data["@DNS"] == "(none reported)"
    assert data["@SOFTAP"] == "up (192.168.255.249)"
    assert data["@WIFI_CREDENTIALS"] == "OK"


@pytest.mark.parametrize("dbm,quality", [(-45, "Excellent"), (-55, "Excellent"), (-56, "Good"),
                                         (-65, "Good"), (-70, "Fair"), (-80, "Poor")])
def test_signal_quality(dbm, quality):
    assert webapi.signal_quality(dbm) == quality


@pytest.mark.parametrize("mhz,band", [(2437, "2.4 GHz"), (5180, "5 GHz"), (5955, "6 GHz"), (900, "900 MHz")])
def test_band(mhz, band):
    assert webapi.band(mhz) == band


def test_missing_fields_are_left_out_not_shown_as_empty():
    data = webapi.map_network_info({"value": {"networkInfo": {"state": "up"}}})
    assert data == {"@NET_STATE": "up"}


def test_unexpected_answer_gives_readable_error():
    with pytest.raises(webapi.WebApiError, match="no networkInfo"):
        webapi.map_network_info({"value": {}})


def test_web_codes_are_never_protocol_codes():
    assert all(c.startswith("@") for c in catalog.WEB_CODES)
    assert not any(c.startswith("@") for c in catalog.PROTOCOL_CODES)
    assert catalog.CATALOG["@WIFI_SIGNAL"].volatile and not catalog.CATALOG["@WIFI_QUALITY"].volatile
    assert catalog.decode("GCIPSTM", "1") == "Manual (static)"


# ------------------------------------------------------------------ service

@pytest.fixture
async def web_fake(fake):
    fake.web_port = await fake.start_web()
    return fake


def _device(fake) -> DeviceService:
    dev = DeviceService(settings_for(fake.port))
    dev.web_port = fake.web_port
    return dev


async def test_web_values_are_read_on_connect_and_part_of_change_log(web_fake):
    dev = _device(web_fake)
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        assert dev.values["@WIFI_SSID"].text == "VOLDBY17"
        assert dev.values["@WIFI_SIGNAL"].text == "-45 dBm"
        assert dev.values["GCIPSTM"].text == "Manual (static)"
        assert {"@WIFI_SSID", "GCIPSDN"} <= {b["code"] for b in dev.changelog.baseline}
        # Ingen web-pseudokode er nogensinde sendt over protokollen.
        assert not any(cmd.startswith("@") for cmd in web_fake.received)
    finally:
        await dev.stop()


async def test_volatile_signal_change_is_not_logged_but_quality_change_is(web_fake):
    dev = _device(web_fake)
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        web_fake.network_info["value"]["networkInfo"]["wireless"]["signalLevel"] = -47   # samme klasse
        await dev.refresh("network")
        assert dev.values["@WIFI_SIGNAL"].raw == "-47"
        assert not any(e.get("code") == "@WIFI_SIGNAL" for e in dev.changelog.entries)
        assert not any(e.get("code") == "@WIFI_SIGNAL" for e in dev.log)
        web_fake.network_info["value"]["networkInfo"]["wireless"]["signalLevel"] = -78   # Poor
        await dev.refresh("network")
        assert any(e.get("code") == "@WIFI_QUALITY" and e["new_raw"] == "Poor" for e in dev.changelog.entries)
    finally:
        await dev.stop()


async def test_unreachable_web_api_marks_values_and_backs_off(web_fake):
    dev = _device(web_fake)
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        web_fake.network_info = None                                     # HTTP 500
        await dev.refresh("network")
        assert dev.values["@WIFI_SSID"].status == "unavailable"
        assert "HTTP 500" in dev.values["@WIFI_SSID"].status_text
        assert dev.values["@WIFI_SSID"].raw == "VOLDBY17"                # sidst kendte værdi bevares
        n = len(web_fake.web_requests)
        data, attempted = await dev._read_web("logpoll")                 # circuit breaker
        assert (data, attempted) == (None, False) and len(web_fake.web_requests) == n
    finally:
        await dev.stop()


async def test_log_mode_logs_wifi_change_with_http_command_cell(web_fake, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    dev = _device(web_fake)
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        dev.start_logmode(interval=0.4)
        await wait_until(lambda: dev.logmode.initialized, timeout=5)
        web_fake.network_info["value"]["networkInfo"]["wireless"]["bssid"] = "4C:77:6D:AD:1E:99"  # roaming
        web_fake.network_info["value"]["networkInfo"]["wireless"]["signalLevel"] = -46            # støj
        await wait_until(lambda: any("BSSID" in e["line"] for e in dev.logmode.lines if e["kind"] == "change"),
                         timeout=5)
        change = [e for e in dev.logmode.lines if e["kind"] == "change" and "BSSID" in e["line"]][0]
        assert change["cmd"] == "HTTP network:info"
        assert not any("@WIFI_SIGNAL" in e["line"] for e in dev.logmode.lines if e["kind"] == "change")
    finally:
        await dev.shutdown()


async def test_report_network_section(web_fake):
    from datetime import datetime, timezone
    from app.services import report
    dev = _device(web_fake)
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        text = report.build_report(dev.snapshot(), {}, datetime.now(timezone.utc), refreshed=True)
        section = text[text.index("3. NETWORK"):text.index("4. SYSTEM & INPUTS")]
        assert "IP mode" in section and "Manual (static)" in section
        assert "DNS server" in section and "192.168.1.1" in section
        assert "[Device web API - network:info]" in section and "VOLDBY17" in section
        assert "Ethernet cable" in section and "Not connected" in section
    finally:
        await dev.stop()
