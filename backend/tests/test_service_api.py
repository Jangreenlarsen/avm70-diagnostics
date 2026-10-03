"""DeviceService (tilstand, hændelser, reconnect) og API'et."""

import asyncio

import httpx
import pytest

from app import config
from app.config import DeviceSettings, SettingsError, validate
from app.main import create_app
from app.services.device_service import DeviceService
from app.tools.fake_avm import FakeAvm


async def wait_until(predicate, timeout=3.0):
    for _ in range(int(timeout / 0.02)):
        if predicate():
            return
        await asyncio.sleep(0.02)
    raise AssertionError("Betingelsen blev aldrig opfyldt")


def settings_for(port, **kw) -> DeviceSettings:
    base = dict(host="127.0.0.1", port=port, poll_interval=0, connect_timeout=5,
                query_timeout=0.3, auto_reconnect=True, auto_connect=False)
    return DeviceSettings(**{**base, **kw})


@pytest.fixture
async def fake():
    f = FakeAvm()
    f.port = await f.start()
    yield f
    await f.stop()


# ------------------------------------------------------------------ indstillinger

def test_validate_rejects_all_empty_host_forms():
    for host in ["", "   ", None, "\t"]:
        with pytest.raises(SettingsError, match="empty"):
            validate({"host": host})


@pytest.mark.parametrize("data,msg", [
    ({"port": 0}, "Port must be"),
    ({"port": "abc"}, "numbers"),
    ({"poll_interval": 0.1}, "Poll interval"),
    ({"connect_timeout": 0}, "Connect timeout"),
    ({"connect_timeout": 2}, "Connect timeout"),
    ({"query_timeout": 20}, "Response timeout"),
    ({"auto_reconnect": "ja"}, "true/false"),
    ({"host": "10.1.1 .7"}, "spaces"),
])
def test_validate_rejects_bad_values(data, msg):
    with pytest.raises(SettingsError, match=msg):
        validate(data, DeviceSettings("10.1.1.7"))


def test_validate_allows_poll_zero_and_merges_onto_base():
    s = validate({"poll_interval": 0, "host": " 10.1.1.8 "}, DeviceSettings("10.1.1.7", port=1234))
    assert (s.host, s.port, s.poll_interval) == ("10.1.1.8", 1234, 0)


# ------------------------------------------------------------------ service

async def test_service_reads_system_inputs_and_runtime_and_logs_changes(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: any("Full read" in e["text"] for e in dev.log))
        assert dev.values["IDM"].text == "AVM 70"
        assert dev.values["Z1AIF"].text == "Atmos"
        assert dev.values["IS2IN"].raw == "Plex"
        assert dev.values["Z2VOL"].status == "zone_off"
        assert dev.connection["status"] == "connected"

        await fake.push("Z1AIF", "5")
        await wait_until(lambda: dev.values["Z1AIF"].raw == "5")
        change = [e for e in dev.log if e["kind"] == "change"][-1]
        assert change["text"] == "Audio format: Atmos → DTS"
        assert change["source"] == "push"
    finally:
        await dev.stop()
    assert dev.connection["status"] == "disconnected"


async def test_service_reconnects_after_connection_loss(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.connected)
        for w in list(fake.writers):
            w.close()
        await wait_until(lambda: dev.connection["status"] == "reconnecting")
        assert dev.connection["last_error"]
        await wait_until(lambda: dev.connected, timeout=5)
    finally:
        await dev.stop()


async def test_service_without_auto_reconnect_stops_with_error():
    f = FakeAvm()
    port = await f.start()
    await f.stop()
    dev = DeviceService(settings_for(port, auto_reconnect=False))
    await dev.start()
    await wait_until(lambda: not dev.running)
    assert dev.connection["status"] == "disconnected"
    assert "refused" in dev.connection["last_error"]


async def test_test_connection_reports_model_and_specific_failure(fake):
    dev = DeviceService(settings_for(fake.port))
    ok = await dev.test_connection(settings_for(fake.port))
    assert ok["ok"] and ok["model"] == "AVM 70"

    f2 = FakeAvm()
    port2 = await f2.start()
    await f2.stop()
    bad = await dev.test_connection(settings_for(port2))
    assert not bad["ok"] and "refused" in bad["message"]


async def test_test_connection_on_active_target_does_not_open_second_client(fake):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.values["IDM"].status == "ok")
        result = await dev.test_connection(settings_for(fake.port))
        assert result["ok"] and "Already connected" in result["message"]
    finally:
        await dev.stop()


# ------------------------------------------------------------------ API

@pytest.fixture
async def api(fake, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "load_device_settings", lambda: settings_for(fake.port))
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            client.app = app
            yield client


async def test_api_query_only_allows_read_queries(api):
    for cmd in ["Z1VOL-50", "Z1POW1", "Z1VOL?;Z1POW1", ""]:
        r = await api.post("/api/query", json={"command": cmd})
        assert r.status_code == 400, cmd
        assert r.json()["detail"]


async def test_api_query_requires_connection(api):
    r = await api.post("/api/query", json={"command": "IDM?"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Not connected to AVM70"


async def test_api_connect_query_probe_and_settings(api, fake, tmp_path):
    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: dev.values["IDM"].status == "ok")

    r = await api.post("/api/query", json={"command": "z1aif?"})
    assert r.status_code == 200
    assert r.json()["decoded"] == "Atmos"

    r = await api.post("/api/probe")
    statuses = {row["code"]: row["status"] for row in r.json()}
    assert statuses["IDM"] == "ok" and statuses["Z2VOL"] == "zone_off"

    r = await api.put("/api/settings", json={"port": 99999})
    assert r.status_code == 400 and "Port must be" in r.json()["detail"]

    r = await api.put("/api/settings", json={"poll_interval": 5})
    assert r.status_code == 200 and r.json()["poll_interval"] == 5
    assert (tmp_path / "settings.json").exists()

    r = await api.post("/api/settings/test", json={"port": fake.port})
    assert r.json()["ok"] is True

    await api.post("/api/disconnect")
    assert dev.connection["status"] == "disconnected"


# ------------------------------------------------------------------ versioner (FEATURES #10)

async def test_versions_read_on_connect_and_group_refresh_only_queries_that_group(api, fake):
    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: any("Full read" in e["text"] for e in dev.log))
    assert dev.values["GSN"].raw == "ALP2000256N070"
    assert dev.values["NMSVER"].text == "2.3.213"
    assert dev.values["RBD"].status == "ok" and dev.values["RBD"].raw == ""

    fake.received.clear()
    r = await api.post("/api/refresh", params={"group": "version"})
    assert r.status_code == 200
    queried = {cmd[:-1] for cmd in fake.received}
    version_codes = {c for c, v in dev.values.items() if v.group == "version"}
    assert queried == version_codes


async def test_refresh_rejects_unknown_group(api):
    r = await api.post("/api/refresh", params={"group": "nope"})
    assert r.status_code == 400
    assert "Unknown group" in r.json()["detail"]


async def test_api_query_blocks_action_commands_with_explanation(api):
    for cmd, word in [("LDFDS?", "factory reset"), ("fcr0001?", "fault counter reset"), ("Z1VUP?", "volume")]:
        r = await api.post("/api/query", json={"command": cmd})
        assert r.status_code == 400, cmd
        assert word in r.json()["detail"] and "not even as a query" in r.json()["detail"]
