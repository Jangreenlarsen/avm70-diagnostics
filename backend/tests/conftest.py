"""Fælles test-opsætning."""

import pytest

from app.services.device_service import DeviceService


@pytest.fixture(autouse=True)
def no_real_web_api(monkeypatch):
    """AVM70's web-API (port 80) er slået fra i testene som standard, så ingen
    test forsøger at nå en rigtig enhed eller venter på timeouts. Web-testene
    (test_network.py) peger `web_port` mod fake'ns web-server."""
    monkeypatch.setattr(DeviceService, "DEFAULT_WEB_PORT", None)
