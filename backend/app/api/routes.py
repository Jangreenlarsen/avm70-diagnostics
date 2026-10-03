"""HTTP-endpoints og SSE-strøm. Ingen protokol-logik her — alt går via
`DeviceService`."""

import asyncio
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from app import config
from app.protocol import catalog
from app.services import changelog, report
from app.services.device_service import BusyError, DeviceService, NotConnectedError

router = APIRouter(prefix="/api")

HEARTBEAT_SECONDS = 15
_QUERY_RE = re.compile(r"^[A-Z0-9]+\?$")


def service(request: Request) -> DeviceService:
    return request.app.state.device


class QueryBody(BaseModel):
    command: str


@router.get("/info")
async def info(request: Request) -> dict:
    return {
        "app": config.app_version(),
        "settings": asdict(service(request).settings),
        "defaults": asdict(config.env_defaults()),
        "catalog": [
            {"code": c.code, "label": c.label, "group": c.group, "unit": c.unit}
            for c in catalog.CATALOG.values()
        ],
    }


@router.get("/state")
async def state(request: Request) -> dict:
    return service(request).snapshot()


@router.post("/connect")
async def connect(request: Request) -> dict:
    await service(request).start()
    return service(request).connection


@router.post("/disconnect")
async def disconnect(request: Request) -> dict:
    await service(request).stop()
    return service(request).connection


@router.post("/refresh")
async def refresh(request: Request, group: str | None = None) -> dict:
    if group is not None and group not in catalog.GROUP_TITLES:
        raise HTTPException(400, f"Unknown group: {group!r} — valid: {', '.join(catalog.GROUP_TITLES)}")
    try:
        await service(request).refresh(group)
    except NotConnectedError as exc:
        raise HTTPException(409, str(exc)) from None
    return {"ok": True}


def _parse_settings(body: dict, base: config.DeviceSettings) -> config.DeviceSettings:
    if not isinstance(body, dict):
        raise HTTPException(400, "Expected a JSON object")
    try:
        return config.validate(body, base)
    except config.SettingsError as exc:
        raise HTTPException(400, str(exc)) from None


@router.get("/settings")
async def get_settings(request: Request) -> dict:
    return asdict(service(request).settings)


@router.put("/settings")
async def put_settings(request: Request, body: dict) -> dict:
    dev = service(request)
    new = _parse_settings(body, dev.settings)
    try:
        config.save_device_settings(new)
    except OSError as exc:
        raise HTTPException(500, f"Could not save the settings: {exc}") from None
    await dev.apply_settings(new)
    return asdict(new)


@router.post("/settings/test")
async def test_settings(request: Request, body: dict) -> dict:
    dev = service(request)
    return await dev.test_connection(_parse_settings(body, dev.settings))


@router.post("/settings/reset")
async def reset_settings(request: Request) -> dict:
    """Tilbage til `.env`-standardværdierne (sletter `data/settings.json`)."""
    dev = service(request)
    try:
        config.SETTINGS_FILE.unlink(missing_ok=True)
    except OSError as exc:
        raise HTTPException(500, f"Could not delete {config.SETTINGS_FILE.name}: {exc}") from None
    defaults = config.env_defaults()
    await dev.apply_settings(defaults)
    return asdict(defaults)


@router.post("/query")
async def query(request: Request, body: QueryBody) -> dict:
    command = body.command.strip().upper().rstrip(";")
    if command == "":
        raise HTTPException(400, "Enter a command, e.g. Z1VOL?")
    if not command.endswith("?"):
        raise HTTPException(400, "Only queries (CODE?) are allowed — the app is read-only")
    if not _QUERY_RE.match(command):
        raise HTTPException(400, "Invalid command — only letters and digits followed by ?, e.g. Z1VOL?")
    reason = catalog.blocked_reason(command)
    if reason is not None:
        raise HTTPException(400, f"{command[:-1]} is a {reason} command on the AVM70 and is blocked — "
                                 "the app is read-only and never sends it, not even as a query")
    try:
        return await service(request).raw_query(command[:-1])
    except NotConnectedError as exc:
        raise HTTPException(409, str(exc)) from None


@router.post("/probe")
async def probe(request: Request) -> list[dict]:
    try:
        return await service(request).probe()
    except NotConnectedError as exc:
        raise HTTPException(409, str(exc)) from None
    except BusyError as exc:
        raise HTTPException(409, str(exc)) from None


@router.get("/export")
async def export(request: Request) -> Response:
    """Diagnoserapport som tekstfil (FEATURES.md #12). Er der forbindelse,
    genforespørges alt først, så rapporten er frisk. Uden forbindelse
    eksporteres de senest kendte værdier, og rapporten siger det tydeligt
    — en rapport er stadig nyttig netop når forbindelsen er problemet."""
    dev = service(request)
    refreshed, refresh_error = False, None
    if dev.connected:
        try:
            await dev.refresh()
            refreshed = True
        except Exception as exc:  # noqa: BLE001 — eksporten skal lykkes med de kendte værdier; fejlen står i rapporten
            refresh_error = str(exc) or type(exc).__name__
    now = datetime.now(timezone.utc)
    snapshot = dev.snapshot()
    snapshot["traffic"] = list(dev.traffic)  # hele ringbufferen, ikke kun UI-udsnittet
    text = report.build_report(snapshot, config.app_version(), now, refreshed, refresh_error, dev.last_probe)
    filename = report.report_filename(snapshot, now)
    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/changelog")
async def get_changelog(request: Request) -> dict:
    return service(request).changelog.to_dict()


@router.post("/changelog/reset")
async def reset_changelog(request: Request) -> dict:
    return service(request).new_changelog()


@router.get("/changelog/export")
async def export_changelog(request: Request) -> Response:
    """Ændringsloggen som tekstfil (FEATURES.md #14)."""
    dev = service(request)
    now = datetime.now(timezone.utc)
    known = {code: v for code, v in dev.values.items() if v.status == "ok" or v.raw is not None}
    serial = known["GSN"].raw if "GSN" in known else None
    device = {
        "model": known["IDM"].raw if "IDM" in known else None,
        "serial": serial,
        "address": f"{dev.settings.host}:{dev.settings.port}",
        "owner": dev.settings.owner,
    }
    text = changelog.build_text(dev.changelog.to_dict(), device, config.app_version(), now)
    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{changelog.changelog_filename(serial, now)}"'},
    )


class LogModeStart(BaseModel):
    interval: float | None = None


@router.get("/logmode")
async def get_logmode(request: Request) -> dict:
    dev = service(request)
    return dev.logmode.to_dict(lines=300) if dev.logmode else {"active": False, "lines": []}


@router.post("/logmode/start")
async def start_logmode(request: Request, body: LogModeStart | None = None) -> dict:
    """Log mode (FEATURES.md #15). Intervallet kommer fra ⚙ Setup, medmindre
    et andet gives eksplicit (valideres med samme grænser)."""
    dev = service(request)
    interval = body.interval if body else None
    if interval is not None:
        try:
            config.validate({"log_poll_interval": interval}, dev.settings)
        except config.SettingsError as exc:
            raise HTTPException(400, str(exc)) from None
    return dev.start_logmode(interval)


@router.post("/logmode/stop")
async def stop_logmode(request: Request) -> dict:
    result = service(request).stop_logmode()
    if result is None:
        raise HTTPException(409, "Log mode has not been started")
    return result


@router.get("/logmode/export")
async def export_logmode(request: Request) -> Response:
    """Hele log mode-sessionen (også de linjer der ikke længere er i UI'et)."""
    dev = service(request)
    if dev.logmode is None:
        raise HTTPException(409, "Log mode has not been started")
    gsn = dev.values.get("GSN")
    serial = gsn.raw if gsn is not None and gsn.status == "ok" else ""
    serial = re.sub(r"[^A-Za-z0-9_-]", "", (serial or "").strip()) or "unknown-serial"
    started = datetime.fromisoformat(dev.logmode.to_dict(lines=0)["started_at"]).astimezone()
    filename = f"AVM70_log_{serial}_{started.strftime('%Y%m%d-%H%M%S')}.txt"
    return Response(
        content=dev.logmode.text().encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _sse(event: dict) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"


@router.get("/events")
async def events(request: Request) -> StreamingResponse:
    dev = service(request)
    queue = dev.subscribe()

    async def stream():
        try:
            yield _sse({"type": "reset", "data": dev.snapshot()})
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # wait_for på queue.get() er sikkert (i modsætning til på en
                    # async generator, jf. Movie database BUGS.md #82): en
                    # annulleret get() mister intet element.
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                yield _sse(event)
        finally:
            dev.unsubscribe(queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
