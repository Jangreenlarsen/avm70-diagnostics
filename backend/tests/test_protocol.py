"""Parser, katalog-afkodning og klient mod en fake AVM70."""

import asyncio

import pytest

from app.protocol import catalog
from app.protocol.client import AvmClient, AvmConnectionError
from app.protocol.parser import StreamSplitter, parse_message
from app.tools.fake_avm import FakeAvm


# ------------------------------------------------------------------ parser

def test_splitter_handles_messages_split_across_packets():
    s = StreamSplitter()
    assert s.feed(b"Z1VOL-35;Z1A") == ["Z1VOL-35"]
    assert s.feed(b"IF6;;IDMAVM 70;") == ["Z1AIF6", "IDMAVM 70"]


def test_splitter_never_fails_on_odd_bytes():
    assert StreamSplitter().feed(b"IS1IN\xe6bler;") == ["IS1IN\xe6bler"]


@pytest.mark.parametrize("raw,code,value", [
    ("Z1VOL-35.5", "Z1VOL", "-35.5"),
    ("Z1PVOL52", "Z1PVOL", "52"),          # PVOL må ikke forveksles med VOL
    ("Z1AIN Dolby", "Z1AIN", " Dolby"),
    ("Z1AIRx", "Z1AIR", "x"),              # AIR vs AIN
    ("IS12INKodi", "IS12IN", "Kodi"),      # tocifret input
    ("IS3ARC1", "IS3ARC", "1"),
    ("GCTXS1", "GCTXS", "1"),
    ("IDMAVM 70", "IDM", "AVM 70"),
    ("Z2POW0", "Z2POW", "0"),
])
def test_parse_value_messages(raw, code, value):
    msg = parse_message(raw)
    assert (msg.kind, msg.code, msg.value) == ("value", code, value)


@pytest.mark.parametrize("raw,error,code", [
    ("!IFOO?", "invalid", "FOO"),
    ("!RZ1VOL99", "out_of_range", "Z1VOL99"),
    ("!EZ1POW1", "cannot_execute", "Z1POW1"),
    ("!ZZ2VOL?", "zone_off", "Z2VOL"),
])
def test_parse_error_messages(raw, error, code):
    msg = parse_message(raw)
    assert (msg.kind, msg.error, msg.code) == ("error", error, code)


def test_parse_unknown_message_keeps_raw():
    msg = parse_message("XYZ123")
    assert msg.kind == "unknown" and msg.raw == "XYZ123"


# ------------------------------------------------------------------ katalog

@pytest.mark.parametrize("code,raw,text", [
    ("Z1AIF", "6", "Atmos"),
    ("Z1AIF", "06", "Atmos"),              # foranstillede nuller
    ("Z1ALM", "03", "Dolby Surround"),
    ("Z1VOL", "-35.5", "-35.5 dB"),
    ("Z1AIF", "42", "42"),                 # ukendt værdi -> rå værdi
    ("IS2IN", "Plex", "Plex"),
    ("IS2ARC", "1", "On"),
    ("NOPE", "x", "x"),
    ("Z1BRT", "", ""),                     # tom værdi får ikke enhed på
    ("Z1BRT", "   ", "   "),               # heller ikke whitespace
    ("Z1BRT", "lossy input formats", "lossy input formats"),  # rigtig AVM70: tekst, ingen enhed
    ("Z1BRT", "640", "640 kbps"),
    ("EMAC", "501E2D3E4870", "50:1E:2D:3E:48:70"),             # rigtig AVM70: MAC uden kolon
    ("EMAC", "00:1B:7C:12:34:56", "00:1B:7C:12:34:56"),       # allerede formateret
    ("WMAC", "N/A", "N/A"),
])
def test_decode(code, raw, text):
    assert catalog.decode(code, raw) == text


def test_input_commands():
    assert catalog.input_commands(2) == ["IS1IN", "IS1ARC", "IS2IN", "IS2ARC"]
    assert catalog.lookup("IS7IN").group == catalog.INPUTS


# ------------------------------------------------------------------ klient

@pytest.fixture
async def fake():
    f = FakeAvm()
    port = await f.start()
    f.port = port
    yield f
    await f.stop()


def _client(port, messages=None, traffic=None):
    return AvmClient(
        "127.0.0.1", port,
        on_message=lambda m, o: messages.append((m, o)) if messages is not None else None,
        on_traffic=lambda d, l, o: traffic.append((d, l, o)) if traffic is not None else None,
        connect_timeout=5,
    )


async def test_query_returns_value_and_error_statuses(fake):
    traffic = []
    c = _client(fake.port, traffic=traffic)
    await c.connect()
    try:
        r = await c.query("IDM", "refresh")
        assert (r.status, r.value) == ("ok", "AVM 70")
        assert (await c.query("Z2VOL")).status == "zone_off"
        assert (await c.query("FOO")).status == "invalid"
    finally:
        await c.close()
    assert ("tx", "IDM?", "refresh") in traffic
    assert ("rx", "IDMAVM 70", "refresh") in traffic


async def test_query_times_out_without_raising(fake):
    fake.reply_for = lambda cmd: ""  # tavs enhed
    c = _client(fake.port)
    await c.connect()
    try:
        r = await c.query("IDM", timeout=0.2)
        assert r.status == "timeout"
    finally:
        await c.close()


async def test_unsolicited_push_is_marked_as_push(fake):
    messages = []
    c = _client(fake.port, messages=messages)
    await c.connect()
    try:
        await fake.push("Z1AIF", "5")
        for _ in range(50):
            if messages:
                break
            await asyncio.sleep(0.01)
    finally:
        await c.close()
    msg, origin = messages[0]
    assert (msg.code, msg.value, origin) == ("Z1AIF", "5", "push")


async def test_connect_refused_gives_specific_message():
    f = FakeAvm()
    port = await f.start()
    await f.stop()  # porten er nu lukket
    c = _client(port)
    with pytest.raises(AvmConnectionError, match="refused the connection"):
        await c.connect()


async def test_query_rejects_invalid_code(fake):
    c = _client(fake.port)
    await c.connect()
    try:
        with pytest.raises(ValueError):
            await c.query("Z1VOL-50")  # set-kommando, ikke en kode
    finally:
        await c.close()


async def test_lost_connection_fails_pending_query_and_sets_reason(fake):
    fake.reply_for = lambda cmd: ""
    c = _client(fake.port)
    await c.connect()
    task = asyncio.create_task(c.query("IDM", timeout=5))
    await asyncio.sleep(0.05)
    await fake.stop()
    with pytest.raises(AvmConnectionError):
        await task
    assert c.disconnect_reason is not None
    assert not c.connected


# ------------------------------------------------------------------ versioner (FEATURES #10)

@pytest.mark.parametrize("raw,code,value", [
    ("IDQAVM 70 EU 00.80 Sep 1 2023 09H18M47", "IDQ", "AVM 70 EU 00.80 Sep 1 2023 09H18M47"),
    ("GSNALP2000256N070", "GSN", "ALP2000256N070"),
    ("DSPIDS00.00/00.00", "DSPIDS", "00.00/00.00"),
    ("LCDIDS00.32/00.02", "LCDIDS", "00.32/00.02"),
    ("NMSVER2.3.213", "NMSVER", "2.3.213"),
    ("NMSTWi-Fi", "NMST", "Wi-Fi"),          # NMST må ikke forveksles med NMSVER
    ("RBD", "RBD", ""),                      # rigtig AVM70: tomt svar
    ("RVERnot approved", "RVER", "not approved"),
])
def test_parse_version_codes_seen_on_real_avm70(raw, code, value):
    msg = parse_message(raw)
    assert (msg.kind, msg.code, msg.value) == ("value", code, value)


def test_version_group_is_static_not_polled():
    version_codes = {c for c, cmd in catalog.CATALOG.items() if cmd.group == catalog.VERSION}
    assert {"IDQ", "GSN", "IDS", "DSPIDS", "LCDIDS", "NMSVER", "NMHVER", "RVER"} <= version_codes
    assert catalog.VERSION in catalog.STATIC_GROUPS
    assert catalog.VERSION not in catalog.RUNTIME_GROUPS


# ------------------------------------------------------------------ officielle x40-værdier (BUGS.md #4)

@pytest.mark.parametrize("code,raw,text", [
    # docs/anthem/MRX-x40-AVM-70-90-IP-RS-232-v5.md, "System Status"
    ("Z1AIC", "5", "7.1 channels"),   # anthemav (x20) sagde 6.1
    ("Z1AIC", "6", "Atmos"),          # anthemav sagde 7.1
    ("Z1AIC", "7", "DTS:X"),          # anthemav sagde Atmos
    ("Z1AIF", "0", "No input"),
    ("Z1AIF", "7", "DTS:X"),          # manglede
    ("Z1VIR", "14", "4K60"),
    ("Z1VIR", "15", "4K50"),
    ("Z1ALM", "3", "Dolby Surround"),
    ("Z1DIA", "n", "Not applicable"),
    ("Z1DIA", "-4", "-4 dB"),
    ("GCTXS", "1", "IP only"),
    ("GCFPB", "30", "30 %"),
    ("Z1BDP", "24", "24 bit"),       # FEATURES.md #19
    ("Z1BDP", "0", "No input"),
])
def test_decoding_follows_the_official_x40_protocol(code, raw, text):
    assert catalog.decode(code, raw) == text


# ------------------------------------------------------------------ spærreliste (FEATURES.md #18)

@pytest.mark.parametrize("code", [
    "LDFDS", "LOTFS", "CPYS01", "BSC1", "PRGS21", "PRUID0", "UPDOTA", "UPDUSB", "CKFUPD1",
    "GCIPV1A", "GCIPV2I", "RWIFIS", "RSTWFS", "RWPS", "NMWPS", "RDBL", "R1SET", "FCR0001",
    "IIAI", "IDAI3", "CTRL01", "Z1MSG0", "Z1SHC", "Z1SIM", "Z2SIM", "Z1ARCCRP", "Z1ARCMEN",
    "Z1VUP", "Z2VDN", "Z1PVUP", "Z1TUP0", "Z1LDN", "Z1AUP",
])
def test_action_commands_are_blocked(code):
    assert catalog.blocked_reason(code) is not None
    assert catalog.blocked_reason(code.lower() + "?") is not None   # også med ? og små bogstaver


@pytest.mark.parametrize("code", ["FCC", "FCN0001", "FCQ0001", "Z1ARCVAL", "GCIPSTI", "GCIPSTM",
                                  "Z1VOL", "Z1PVOL", "IS1IN", "IS12AIJ", "GCTXS", "GCSHDMIB", "Z1BDP"])
def test_read_codes_are_allowed(code):
    assert catalog.blocked_reason(code) is None


def test_no_catalog_code_is_blocked():
    assert [c for c in catalog.CATALOG if catalog.blocked_reason(c)] == []


async def test_blocked_code_is_never_sent_to_the_device(fake):
    c = _client(fake.port)
    await c.connect()
    try:
        with pytest.raises(ValueError, match="factory reset command on the AVM70 and is blocked"):
            await c.query("LDFDS")
    finally:
        await c.close()
    assert fake.received == []


# ------------------------------------------------------------------ settings-gruppen (FEATURES.md #20)

@pytest.mark.parametrize("code,raw,text", [
    ("GCSHDMIB", "0", "Off"), ("GCSHDMIB", "1", "Last used"), ("GCSHDMIB", "2", "HDMI 1"), ("GCSHDMIB", "8", "HDMI 7"),
    ("GCCSTBY", "1", "Enabled"),
    ("GCNSPO", "3", "1 hour"), ("GCNSPO", "7", "Never"),
    ("GCCECC", "1", "On"), ("GCCPFC", "0", "Disabled"), ("GCCTVA", "0", "Off"),
    ("GCHMMO", "1", "Yes"),
    ("GCMLOWS", "0", "None"), ("GCMLOWS", "8", "HDMI ARC"), ("GCMDOWS", "14", "Analog 1"), ("GCMDOWS", "18", "Phono (MM)"),
    ("GCMMV", "3.5", "3.5 dB"), ("GCMPOV", "0", "Last used"), ("GCMPOV", "-30.0", "-30.0 dB"),
    ("GCBU", "1", "Yes"),
    ("GCT1P", "3", "Main or Zone 2"), ("GCT2C", "1", "RS-232/IP"),
])
def test_settings_decoding_follows_the_official_protocol(code, raw, text):
    assert catalog.decode(code, raw) == text
    assert catalog.CATALOG[code].group == catalog.SETTINGS


def test_settings_are_read_on_connect_not_polled():
    assert catalog.SETTINGS in catalog.STATIC_GROUPS and catalog.SETTINGS not in catalog.RUNTIME_GROUPS
