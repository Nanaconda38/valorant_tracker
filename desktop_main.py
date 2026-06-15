import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass

import requests
import uvicorn

from app_logging import configure_logging, get_logger
from app_paths import project_root
from autostart_manager import launcher_parts


APP_TITLE = "Valorant Local Tracker"
DEFAULT_WIDTH = 1360
DEFAULT_HEIGHT = 860
MIN_WIDTH = 1120
MIN_HEIGHT = 720
STARTUP_TIMEOUT_SECONDS = 20
VALORANT_PROCESS_NAMES = [
    "VALORANT-Win64-Shipping.exe",
    "VALORANT.exe",
]

logger = get_logger(__name__)


def find_free_port(host: str = "127.0.0.1") -> int:
    """
    Returns an available local TCP port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_backend(url: str, timeout_seconds: int = STARTUP_TIMEOUT_SECONDS) -> None:
    """
    Waits until the local FastAPI backend accepts HTTP requests.
    """
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{url}/api/settings", timeout=1.0)
            if response.status_code < 500:
                return
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Backend did not start in time: {last_error}")


@dataclass
class BackendServer:
    """
    Owns the background uvicorn server lifecycle.
    """

    host: str
    port: int
    reload: bool = False

    def __post_init__(self) -> None:
        if self.reload:
            app_target = "app:app"
        else:
            from app import app as app_target

        self.server = uvicorn.Server(
            uvicorn.Config(
                app_target,
                host=self.host,
                port=self.port,
                reload=self.reload,
                log_config=None,
                access_log=False,
            )
        )
        self.thread = threading.Thread(target=self.server.run, name="valorant-tracker-backend", daemon=True)

    @property
    def url(self) -> str:
        """
        Returns the local backend URL.
        """
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        """
        Starts uvicorn and waits for readiness.
        """
        logger.info("Starting local backend: %s", self.url)
        self.thread.start()
        wait_for_backend(self.url)
        logger.info("Local backend ready: %s", self.url)

    def stop(self) -> None:
        """
        Requests a graceful uvicorn shutdown.
        """
        logger.info("Stopping local backend")
        self.server.should_exit = True
        if self.thread.is_alive():
            self.thread.join(timeout=5)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parses desktop launcher arguments.
    """
    parser = argparse.ArgumentParser(description="Run Valorant Tracker as a desktop app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Backend port. 0 chooses a free port.")
    parser.add_argument("--dev", action="store_true", help="Keep dev .env loading and open the app in a browser.")
    parser.add_argument("--no-window", action="store_true", help="Start only the local backend.")
    parser.add_argument("--watch-valorant", action="store_true", help="Wait for Valorant, launch the app, then exit.")
    parser.add_argument("--watch-poll-interval", type=float, default=5.0)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    return parser.parse_args(argv)


def configure_desktop_environment(dev_mode: bool) -> None:
    """
    Applies environment defaults for desktop mode.
    """
    if not dev_mode:
        os.environ.setdefault("VALORANT_TRACKER_SKIP_DOTENV", "1")
    configure_logging(debug=dev_mode)

    if sys.platform == "win32":
        import ctypes
        try:
            myappid = "naelc.valoranttracker.desktop.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass


class WindowApi:
    """
    Exposes desktop window control functions to the frontend.
    """

    def __init__(self) -> None:
        self._window = None

    def toggle_fullscreen(self) -> None:
        """
        Toggles fullscreen mode for the pywebview window.
        """
        if self._window:
            self._window.toggle_fullscreen()


def open_desktop_window(url: str, width: int, height: int, backend: BackendServer) -> None:
    """
    Opens the pywebview desktop window and blocks until it closes.
    """
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "pywebview is not installed. Run "
            "`./venv/Scripts/python.exe -m pip install -r requirements.txt`."
        ) from exc

    api = WindowApi()

    window = webview.create_window(
        APP_TITLE,
        url,
        width=max(width, MIN_WIDTH),
        height=max(height, MIN_HEIGHT),
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        confirm_close=False,
        js_api=api,
    )
    api._window = window

    def on_closed() -> None:
        backend.stop()

    window.events.closed += on_closed
    logger.info("Opening desktop window")
    webview.start(debug=False)


def is_process_running(process_name: str) -> bool:
    """
    Returns True when a Windows process is running.
    """
    if os.name != "nt":
        return False

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creationflags,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        logger.debug("Unable to query process list for %s", process_name, exc_info=True)
        return False
    return process_name.lower() in result.stdout.lower()


def valorant_is_running() -> bool:
    """
    Returns True when Valorant appears to be running.
    """
    return any(is_process_running(name) for name in VALORANT_PROCESS_NAMES)


def launch_app_detached() -> None:
    """
    Launches the desktop app and returns immediately.
    """
    command = launcher_parts([])
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    subprocess.Popen(
        command,
        cwd=str(project_root()),
        close_fds=True,
        creationflags=creationflags,
    )


def watch_valorant_and_launch(poll_interval: float) -> int:
    """
    Waits for Valorant to start, launches the app, and exits.
    """
    logger.info("Valorant watcher started")
    print("Valorant Tracker watcher running. Waiting for VALORANT...")
    while True:
        if valorant_is_running():
            logger.info("Valorant detected. Launching app.")
            print("VALORANT detected. Launching Valorant Tracker...")
            launch_app_detached()
            return 0
        time.sleep(max(1.0, poll_interval))


def main(argv: list[str] | None = None) -> int:
    """
    Runs the local backend and opens the desktop shell.
    """
    args = parse_args(argv or sys.argv[1:])
    configure_desktop_environment(args.dev)
    if args.watch_valorant:
        return watch_valorant_and_launch(args.watch_poll_interval)

    port = args.port or find_free_port(args.host)
    backend = BackendServer(args.host, port)
    try:
        backend.start()
        if args.no_window:
            print(f"Valorant Tracker backend running at {backend.url}")
            print("Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        if args.dev:
            print(f"Valorant Tracker dev URL: {backend.url}")
            print("Opening the system browser. Press Ctrl+C here to stop the backend.")
            webbrowser.open(backend.url)
            while True:
                time.sleep(1)
        print(f"Valorant Tracker backend running at {backend.url}")
        print("Opening desktop window...")
        open_desktop_window(backend.url, args.width, args.height, backend)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logger.exception("Desktop launcher failed")
        print(f"Desktop launcher failed: {exc}", file=sys.stderr)
        return 1
    finally:
        backend.stop()


if __name__ == "__main__":
    raise SystemExit(main())
