"""HTTP-endpoints og SSE-strøm. Ingen protokol-logik her — alt går via
`DeviceService`."""

import asyncio
import json
import re
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import config
from app.protocol import catalog
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
async def refresh(request: Request) -> dict:
    try:
        await service(request).refresh()
    except NotConnectedError as exc:
        raise HTTPException(409, str(exc)) from None
    return {"ok": True}


def _parse_settings(body: dict, base: config.DeviceSettings) -> config.DeviceSettings:
    if not isinstance(body, dict):
        raise HTTPException(400, "Forventede et JSON-objekt")
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
        raise HTTPException(500, f"Kunne ikke gemme indstillingerne: {exc}") from None
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
        raise HTTPException(500, f"Kunne ikke slette {config.SETTINGS_FILE.name}: {exc}") from None
    defaults = config.env_defaults()
    await dev.apply_settings(defaults)
    return asdict(defaults)


@router.post("/query")
async def query(request: Request, body: QueryBody) -> dict:
    command = body.command.strip().upper().rstrip(";")
    if command == "":
        raise HTTPException(400, "Skriv en kommando, fx Z1VOL?")
    if not command.endswith("?"):
        raise HTTPException(400, "Kun forespørgsler (KODE?) er tilladt — appen er kun læsende")
    if not _QUERY_RE.match(command):
        raise HTTPException(400, "Ugyldig kommando — kun bogstaver og tal efterfulgt af ?, fx Z1VOL?")
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
