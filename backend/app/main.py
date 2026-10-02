"""AVM70 Diagnostics — FastAPI-app der serverer både API og frontend.

Start: `python -m uvicorn app.main:app --port 8070` (fra backend/), eller
`run.ps1` i projektroden.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.api.routes import router
from app.services.device_service import DeviceService

logging.basicConfig(
    level=config.env.log_level.upper(),
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("avm70")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = config.load_device_settings()
    device = DeviceService(settings)
    app.state.device = device
    version = config.app_version()
    logger.info("AVM70 Diagnostics v%s build %s — AVM70 at %s:%s",
                version.get("version"), version.get("build"), settings.host, settings.port)
    if settings.auto_connect:
        await device.start()
    try:
        yield
    finally:
        await device.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="AVM70 Diagnostics", lifespan=lifespan)
    app.include_router(router)
    if config.FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
