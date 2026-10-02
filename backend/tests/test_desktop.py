"""Windows-launcherens hjælpefunktioner (FEATURES.md #13)."""

import socket
import sys
import uuid

import pytest

from app import desktop

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows-mutex")


@windows_only
def test_second_instance_is_refused_until_first_is_released():
    """AVM70 tager kun én klient — to kopier af appen må ikke køre samtidig."""
    name = f"Local\AVM70Diagnostics.Test.{uuid.uuid4()}"
    first = desktop.acquire_single_instance(name)
    assert first is not None
    try:
        assert desktop.acquire_single_instance(name) is None
    finally:
        desktop.release_single_instance(first)
    again = desktop.acquire_single_instance(name)
    assert again is not None
    desktop.release_single_instance(again)


def test_free_port_is_bindable_on_localhost_only():
    port = desktop.free_port()
    assert 1024 <= port <= 65535
    with socket.socket() as s:
        s.bind(("127.0.0.1", port))


def test_fix_std_streams_replaces_missing_streams(monkeypatch):
    """En --windowed exe har sys.stdout/stderr = None; logging/uvicorn crasher på det."""
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    desktop._fix_std_streams()
    assert sys.stdout is not None and sys.stderr is not None
    sys.stdout.write("x")
    sys.stdout.close()
    sys.stderr.close()


# ------------------------------------------------------------------ "Save as" i app-vinduet

class _FakeResponse:
    def __init__(self, data: bytes, disposition: str):
        self._data = data
        self.headers = {"Content-Disposition": disposition}

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeWindow:
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def create_file_dialog(self, kind, **kw):
        self.calls.append((kind, kw))
        return self.answer


@pytest.fixture
def fake_webview(monkeypatch):
    """pywebview findes kun i build-miljøet — testen bruger en stub."""
    import types
    stub = types.SimpleNamespace(FileDialog=types.SimpleNamespace(SAVE=30))
    monkeypatch.setitem(sys.modules, "webview", stub)


def _api(monkeypatch, answer, data=b"REPORT", disposition='attachment; filename="AVM70_X_1.txt"'):
    monkeypatch.setattr(desktop.urllib.request, "urlopen", lambda url, timeout: _FakeResponse(data, disposition))
    api = desktop.DesktopApi("http://127.0.0.1:1/")
    window = _FakeWindow(answer)
    api.attach(window)
    return api, window


def test_save_report_writes_file_and_suggests_server_filename(monkeypatch, tmp_path, fake_webview):
    target = tmp_path / "chosen.txt"
    api, window = _api(monkeypatch, str(target))
    result = api.save_report()
    assert result == {"saved": True, "path": str(target), "name": "chosen.txt"}
    assert target.read_bytes() == b"REPORT"
    assert window.calls[0][1]["save_filename"] == "AVM70_X_1.txt"


def test_save_report_cancelled_is_not_an_error(monkeypatch, fake_webview):
    api, _ = _api(monkeypatch, None)
    assert api.save_report() == {"saved": False}


def test_save_report_accepts_tuple_answer(monkeypatch, tmp_path, fake_webview):
    target = tmp_path / "t.txt"
    api, _ = _api(monkeypatch, (str(target),))
    assert api.save_report()["saved"] is True and target.exists()


def test_save_report_export_failure_gives_readable_error(monkeypatch, fake_webview):
    def boom(url, timeout):
        raise desktop.urllib.error.URLError("connection refused")
    monkeypatch.setattr(desktop.urllib.request, "urlopen", boom)
    api = desktop.DesktopApi("http://127.0.0.1:1/")
    api.attach(_FakeWindow("x"))
    with pytest.raises(RuntimeError, match="Report export failed"):
        api.save_report()


def test_save_report_write_failure_gives_readable_error(monkeypatch, tmp_path, fake_webview):
    api, _ = _api(monkeypatch, str(tmp_path / "missing-dir" / "r.txt"))
    with pytest.raises(RuntimeError, match="Could not save r.txt"):
        api.save_report()
