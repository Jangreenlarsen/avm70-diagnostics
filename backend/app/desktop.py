"""Windows-app-launcher (FEATURES.md #13): serveren kører i en baggrundstråd
på 127.0.0.1 og en ledig port, og UI'et vises i et eget vindue (pywebview /
Edge WebView2). Når vinduet lukkes, lukkes serveren pænt, så AVM70-
forbindelsen frigives (enheden tager kun én klient).

Køres pakket som AVM70Diagnostics.exe (se packaging/), eller i udvikling:
`python -m app.desktop` fra backend/.

Kun tilgængelig fra PC'en selv (Jans valg) — der lyttes aldrig på andet end
127.0.0.1.
"""

import ctypes
import logging
import logging.handlers
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

from app import config

APP_NAME = "AVM70 Diagnostics"
MUTEX_NAME = "Local\\AVM70Diagnostics.SingleInstance"
ERROR_ALREADY_EXISTS = 183
SERVER_START_TIMEOUT = 20.0

logger = logging.getLogger("avm70")


def _fix_std_streams() -> None:
    """En --windowed PyInstaller-exe har sys.stdout/stderr = None, og både
    logging og uvicorn kalder .write()/.isatty() på dem og crasher."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115 — lever hele processens levetid
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def _setup_logging() -> None:
    """Uden konsol er logfilen det eneste sted fejl kan ses."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.handlers.RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
    ]
    if not config.FROZEN:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=config.env.log_level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def message_box(text: str, error: bool = True) -> None:
    flags = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
    try:
        ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, flags)
    except (AttributeError, OSError):
        print(text, file=sys.stderr)  # ikke Windows — bedste alternativ


def acquire_single_instance(name: str = MUTEX_NAME):
    """Navngiven Windows-mutex. Returnerer et handle (skal holdes i live),
    eller None hvis en anden instans allerede kører."""
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, name)
    if not handle:
        raise OSError(f"CreateMutexW failed (error {kernel32.GetLastError()})")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        return None
    return handle


def release_single_instance(handle) -> None:
    if handle:
        ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(handle))


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class DesktopApi:
    """Eksponeres til frontenden som `window.pywebview.api` (FEATURES.md #13).

    WebView2 under pywebview dropper blob-downloads stille (fundet ved
    runtime-test af exe'en: frontenden meldte "downloaded", men filen
    fandtes ingen steder). I app-vinduet gemmes rapporten derfor via en
    rigtig Windows "Gem som"-dialog. Rapporten hentes stadig gennem API'et
    (GET /api/export) — launcheren springer ikke service-laget over."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        # Privat: pywebview eksponerer offentlige attributter til JS, og et
        # Window-objekt der kan nå sig selv giver rekursion i den proces.
        self._window = None

    def attach(self, window) -> None:
        self._window = window

    def save_report(self) -> dict:
        try:
            with urllib.request.urlopen(self._base_url + "api/export", timeout=60) as res:
                data = res.read()
                header = Message()
                header["content-disposition"] = res.headers.get("Content-Disposition", "")
                filename = header.get_filename() or "AVM70_report.txt"
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Report export failed (HTTP {exc.code})") from None
        except OSError as exc:
            raise RuntimeError(f"Report export failed: {exc}") from None

        import webview

        downloads = Path(os.environ.get("USERPROFILE") or Path.home()) / "Downloads"
        chosen = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            directory=str(downloads if downloads.is_dir() else Path.home()),
            save_filename=filename,
            file_types=("Text files (*.txt)", "All files (*.*)"),
        )
        if not chosen:
            return {"saved": False}
        path = Path(chosen if isinstance(chosen, str) else chosen[0])
        try:
            path.write_bytes(data)
        except OSError as exc:
            raise RuntimeError(f"Could not save {path.name}: {exc.strerror or exc}") from None
        logger.info("Report saved to %s", path)
        return {"saved": True, "path": str(path), "name": path.name}


def _start_server(port: int):
    import uvicorn

    from app.main import app

    # log_config=None: brug vores egen logging (fil) frem for uvicorns, der
    # forventer en konsol. h11/asyncio: undgår valgfrie C-udvidelser, som
    # PyInstaller ellers skal have at vide eksplicit.
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, log_config=None,
        loop="asyncio", http="h11", ws="none", lifespan="on",
    ))
    thread = threading.Thread(target=server.run, name="uvicorn", daemon=True)
    thread.start()
    deadline = time.monotonic() + SERVER_START_TIMEOUT
    while not server.started:
        if not thread.is_alive():
            raise RuntimeError("The internal server stopped during start-up")
        if time.monotonic() > deadline:
            raise RuntimeError(f"The internal server did not start within {SERVER_START_TIMEOUT:g} s")
        time.sleep(0.05)
    return server, thread


def _stop_server(server, thread) -> None:
    server.should_exit = True
    thread.join(timeout=10)
    if thread.is_alive():
        logger.warning("Internal server did not stop within 10 s")


def main() -> int:
    _fix_std_streams()
    _setup_logging()
    version = config.app_version()
    logger.info("%s v%s build %s starting (frozen=%s)", APP_NAME, version.get("version"), version.get("build"), config.FROZEN)

    mutex = acquire_single_instance()
    if mutex is None:
        logger.info("Another instance is already running — exiting")
        message_box(
            f"{APP_NAME} is already running.\n\n"
            "The AVM70 accepts only one network client at a time, so only one "
            "copy of the app can be open.",
            error=False,
        )
        return 1

    try:
        try:
            server, thread = _start_server(free_port())
        except Exception as exc:  # noqa: BLE001 — alt skal ende i en synlig besked; der er ingen konsol
            logger.exception("Server start failed")
            message_box(f"{APP_NAME} could not start: {exc}\n\nLog file:\n{config.LOG_FILE}")
            return 1

        url = f"http://127.0.0.1:{server.config.port}/"
        logger.info("Internal server running at %s", url)
        try:
            import webview

            webview.settings["ALLOW_DOWNLOADS"] = True  # "⬇ Report" skal kunne gemme filen
            webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
            # Test-hook: med AVM70_DEBUG_PORT sat åbner WebView2 en CDP-port
            # på localhost, så vinduet kan styres af en automatiseret test
            # (Playwright connect_over_cdp). Slået fra som standard.
            debug_port = os.environ.get("AVM70_DEBUG_PORT", "").strip()
            if debug_port.isdigit():
                webview.settings["REMOTE_DEBUGGING_PORT"] = int(debug_port)
                logger.warning("WebView2 remote debugging enabled on port %s (AVM70_DEBUG_PORT)", debug_port)
            api = DesktopApi(url)
            api.attach(webview.create_window(
                f"{APP_NAME} v{version.get('version', '?')}",
                url, width=1400, height=950, min_size=(480, 600), js_api=api,
            ))
            webview.start(gui="edgechromium")
        except Exception as exc:  # noqa: BLE001 — typisk manglende WebView2-runtime
            logger.exception("Window failed")
            message_box(
                f"{APP_NAME} could not open its window: {exc}\n\n"
                "The app needs the Microsoft Edge WebView2 Runtime "
                "(included in Windows 11).\n\n"
                f"Log file:\n{config.LOG_FILE}"
            )
            return 1
        finally:
            logger.info("Window closed — stopping")
            _stop_server(server, thread)
        return 0
    finally:
        release_single_instance(mutex)


if __name__ == "__main__":
    sys.exit(main())
