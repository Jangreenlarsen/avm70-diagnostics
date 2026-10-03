"""Log mode (FEATURES.md #15)."""

from datetime import datetime, timedelta, timezone

import pytest

from app import config
from app.protocol.client import QueryResult
from app.services.device_service import DeviceService
from app.services.logmode import LogSession, next_due
from tests.test_service_api import api, fake, settings_for, wait_until  # noqa: F401 — fixtures

T0 = datetime(2026, 10, 3, 1, 0, 0, tzinfo=timezone.utc)


def _r(code, value=None, status="ok"):
    return QueryResult(code, status, value)


BASE = [_r("IDM", "AVM 70"), _r("Z1AIF", "2"), _r("Z2VOL", status="zone_off")]


def _session(tmp_path, interval=5.0):
    return LogSession(interval, tmp_path / "logs", device="AVM 70, serial X, 10.1.1.7:14999")


def _kinds(entries):
    return [e["kind"] for e in entries]


# ------------------------------------------------------------------ skema

@pytest.mark.parametrize("now,expected", [
    (100.0, 105.0),   # lige efter start -> næste slot
    (107.3, 110.0),   # midt i et interval
    (121.0, 125.0),   # passerede slots springes over (ingen "indhentning")
])
def test_next_due_is_drift_free(now, expected):
    assert next_due(100.0, 5.0, now) == expected


# ------------------------------------------------------------------ cyklusser

def test_first_cycle_is_init_with_all_parameters(tmp_path):
    s = _session(tmp_path)
    out = s.record_cycle(BASE, T0, 1.0)
    assert _kinds(out) == ["init"]
    assert "3 parameters" in out[0]["line"]
    detail = "\n".join(out[0]["detail"])
    assert "AVM 70" in detail and "PCM" in detail and "(zone is off)" in detail
    text = s.path.read_text(encoding="utf-8")
    assert "LOG MODE" in text and "Poll interval ........ 5 s" in text and "INIT" in text


def test_unchanged_cycle_logs_only_ok(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle(BASE, T0 + timedelta(seconds=5), 1.0)
    assert _kinds(out) == ["ok"]
    assert out[0]["line"].endswith("OK          POLL 3 commands       3/3 polled, no changes")


def test_changed_value_is_logged_instead_of_ok(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", "3"), _r("Z2VOL", status="zone_off")], T0, 1.0)
    assert _kinds(out) == ["change"]
    assert "Audio format [Z1AIF]: PCM -> Dolby   (raw '2' -> '3')" in out[0]["line"]


def test_status_change_is_a_change(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", "2"), _r("Z2VOL", "-35.0")], T0, 1.0)
    assert "Volume [Z2VOL]: (zone is off) -> -35.0 dB" in out[0]["line"]


def test_missing_answer_gives_incomplete_and_keeps_last_value(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", status="timeout"), _r("Z2VOL", status="zone_off")], T0, 1.0)
    assert _kinds(out) == ["incomplete"]
    assert "2/3 polled - no response: Z1AIF" in out[0]["line"]
    assert s.last["Z1AIF"] == ("ok", "2")
    assert _kinds(s.record_cycle(BASE, T0, 1.0)) == ["ok"]  # svarer igen med samme værdi -> OK


def test_new_parameter_is_logged(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle(BASE + [_r("IS4IN", "Kodi")], T0, 1.0)
    assert _kinds(out) == ["new"] and "Input 4 — name [IS4IN]: Kodi" in out[0]["line"]


def test_push_is_logged_once_and_next_poll_is_ok(tmp_path):
    s = _session(tmp_path)
    assert s.record_push("Z1AIF", "3", T0) is None          # før INIT: intet
    s.record_cycle(BASE, T0, 1.0)
    e = s.record_push("Z1AIF", "3", T0 + timedelta(seconds=2))
    assert e["kind"] == "push" and "PCM -> Dolby" in e["line"]
    assert s.record_push("Z1AIF", "3", T0) is None          # samme værdi igen
    out = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", "3"), _r("Z2VOL", status="zone_off")], T0, 1.0)
    assert _kinds(out) == ["ok"]                            # ingen dobbelt-logning


def test_slow_cycle_is_noted(tmp_path):
    s = _session(tmp_path, interval=2)
    s.record_cycle(BASE, T0, 1.0)
    out = s.record_cycle(BASE, T0, 2.6)
    assert "poll took 2.6 s, longer than the 2 s interval" in out[0]["line"]


def test_interval_change_stop_and_full_text(tmp_path):
    s = _session(tmp_path)
    s.record_cycle(BASE, T0, 1.0)
    assert "changed from 5 s to 10 s" in s.set_interval(10)["line"]
    assert s.set_interval(10) is None
    stop = s.stop()
    assert stop["kind"] == "stopped" and "1 polls" in stop["line"] and not s.active
    text = s.text()
    assert text.index("INIT") < text.index("changed from 5 s") < text.index("STOPPED")
    assert "\n" not in text.replace("\r\n", "")


def test_unwritable_log_dir_still_works_in_memory(tmp_path):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")
    s = LogSession(5, blocker / "logs", device="d")
    assert s.path is None
    assert s.lines[0]["kind"] == "error"
    s.record_cycle(BASE, T0, 1.0)
    assert "INIT" in s.text()


# ------------------------------------------------------------------ service

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return tmp_path


async def test_service_log_mode_init_ok_push_and_poll_change(fake, data_dir):
    dev = DeviceService(settings_for(fake.port, poll_interval=0.5))
    await dev.start()
    try:
        await wait_until(lambda: dev.changelog.started)
        dev.start_logmode(interval=0.4)
        await wait_until(lambda: any(e["kind"] == "ok" for e in dev.logmode.lines), timeout=5)
        kinds = [e["kind"] for e in dev.logmode.lines]
        assert kinds[0] == "init"
        from app.protocol import catalog
        # katalog + 6 input-koder + fake'ns 10 fejltællere (alle læses ved INIT)
        assert f"{len(catalog.PROTOCOL_CODES) + 6 + 10} parameters" in dev.logmode.lines[0]["line"]

        await fake.push("Z1AIF", "5")
        await wait_until(lambda: any(e["kind"] == "push" for e in dev.logmode.lines))

        fake.values["Z1VOL"] = "-20.0"                                     # ændring uden push
        await wait_until(lambda: any(e["kind"] == "change" and "Z1VOL" in e["line"] for e in dev.logmode.lines),
                         timeout=5)

        # Normal polling er sat på pause mens log mode kører.
        assert not any(t["origin"] == "poll" for t in list(dev.traffic)[-100:])
    finally:
        await dev.shutdown()
    assert dev.logmode.lines[-1]["kind"] == "stopped"
    files = list((data_dir / "logs").glob("AVM70_log_*.txt"))
    assert len(files) == 1 and "STOPPED" in files[0].read_text(encoding="utf-8")


async def test_service_interval_change_is_noted(fake, data_dir):
    dev = DeviceService(settings_for(fake.port))
    await dev.start()
    try:
        await wait_until(lambda: dev.connected)
        dev.start_logmode(interval=3)
        await dev.apply_settings(settings_for(fake.port, log_poll_interval=7))
        assert any("changed from 3 s to 7 s" in e["line"] for e in dev.logmode.lines)
    finally:
        await dev.shutdown()


async def test_api_log_mode_validation_stop_and_export(api, fake, data_dir):
    r = await api.post("/api/logmode/stop")
    assert r.status_code == 409 and r.json()["detail"] == "Log mode has not been started"
    r = await api.post("/api/logmode/start", json={"interval": 1})
    assert r.status_code == 400 and "between 2 and 3600" in r.json()["detail"]

    await api.post("/api/connect")
    dev = api.app.state.device
    await wait_until(lambda: dev.connected)
    r = await api.post("/api/logmode/start")
    assert r.status_code == 200 and r.json()["active"] and r.json()["interval"] == 5.0
    await wait_until(lambda: dev.logmode.initialized, timeout=5)

    r = await api.get("/api/logmode/export")
    assert r.status_code == 200
    assert 'filename="AVM70_log_ALP2000256N070_' in r.headers["content-disposition"]
    assert "INIT" in r.text

    r = await api.post("/api/logmode/stop")
    assert r.json()["active"] is False


# ------------------------------------------------------------------ kommando-kolonne (FEATURES.md #17)

TEXT_COL = 23 + 2 + 12 + 22  # tid + mellemrum + type + kommando


def test_command_column_shows_direction_and_protocol_command(tmp_path):
    s = _session(tmp_path)
    init = s.record_cycle(BASE, T0, 1.0)[0]
    assert init["cmd"] == "POLL 3 commands"
    assert init["detail"][0].startswith("POLL IDM?")
    change = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", "3"), _r("Z2VOL", status="zone_off")], T0, 1.0)[0]
    assert change["cmd"] == "POLL Z1AIF?"
    push = s.record_push("Z1AIF", "5", T0)
    assert push["cmd"] == "PUSH Z1AIF5"
    ok = s.record_cycle([_r("IDM", "AVM 70"), _r("Z1AIF", "5"), _r("Z2VOL", status="zone_off")], T0, 1.0)[0]
    assert ok["cmd"] == "POLL 3 commands"
    marker = s.marker("Connection lost: x")
    assert marker["cmd"] == ""


def test_description_always_starts_in_the_same_column(tmp_path):
    s = _session(tmp_path)
    lines = [s.record_cycle(BASE, T0, 1.0)[0], s.record_push("Z1AIN", "Dolby TrueHD Atmos", T0),
             s.record_cycle(BASE, T0, 1.0)[0], s.marker("Connection lost: x")]
    for e in lines:
        assert e["line"][TEXT_COL - 1] == " " and e["line"][TEXT_COL] != " ", e["line"]


def test_long_push_command_is_truncated():
    from app.services.logmode import command_cell
    cell = command_cell("PUSH", "Z1AINDolby TrueHD Atmos")
    assert cell == "PUSH Z1AINDolby Tr..."
    assert len(cell) < 22  # mindst ét mellemrum før forklaringen


def test_file_has_column_header(tmp_path):
    s = _session(tmp_path)
    text = s.path.read_bytes().decode("utf-8")
    assert "TIME                     TYPE        COMMAND               DESCRIPTION" in text
    assert "POLL = query sent by this app" in text


def test_every_line_has_an_increasing_sequence_number(tmp_path):
    """BUGS.md #3: UI'et bruger seq til at vise hver linje præcis én gang."""
    s = _session(tmp_path)
    entries = s.record_cycle(BASE, T0, 1.0) + [s.marker("x"), s.record_push("Z1AIF", "3", T0)] \
        + s.record_cycle(BASE, T0, 1.0) + [s.stop()]
    seqs = [e["seq"] for e in entries]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    assert [e["seq"] for e in s.to_dict()["lines"]] == [e["seq"] for e in s.lines]
