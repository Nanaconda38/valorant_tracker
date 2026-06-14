import os
import subprocess
import sys
from typing import Any

from app_paths import project_root


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_RUN_VALUE = "ValorantTracker"
WATCHER_RUN_VALUE = "ValorantTrackerValorantWatcher"


def is_windows() -> bool:
    """
    Returns True when Windows Run registry entries are supported.
    """
    return os.name == "nt"


def quote_command(parts: list[str]) -> str:
    """
    Builds a Windows-safe command line for HKCU Run.
    """
    return subprocess.list2cmdline([str(part) for part in parts])


def launcher_parts(extra_args: list[str] | None = None) -> list[str]:
    """
    Returns the command parts used to start this app in packaged or dev mode.
    """
    args = extra_args or []
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    return [sys.executable, str(project_root() / "desktop_main.py"), *args]


def launcher_command(extra_args: list[str] | None = None) -> str:
    """
    Returns the command string used for a Windows Run entry.
    """
    return quote_command(launcher_parts(extra_args))


def watcher_command() -> str:
    """
    Returns the Windows Run command for the Valorant watcher.
    """
    return launcher_command(["--watch-valorant"])


def app_command() -> str:
    """
    Returns the Windows Run command for launching the app at login.
    """
    return launcher_command([])


def _open_run_key(access: int):
    """
    Opens the HKCU Run key.
    """
    import winreg

    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, access)


def set_run_entry(name: str, command: str) -> None:
    """
    Creates or updates a HKCU Run entry.
    """
    if not is_windows():
        raise RuntimeError("Windows startup entries are only supported on Windows.")

    import winreg

    with _open_run_key(winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)


def delete_run_entry(name: str) -> None:
    """
    Deletes a HKCU Run entry if it exists.
    """
    if not is_windows():
        raise RuntimeError("Windows startup entries are only supported on Windows.")

    import winreg

    try:
        with _open_run_key(winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except FileNotFoundError:
        pass


def get_run_entry(name: str) -> str:
    """
    Reads a HKCU Run entry.
    """
    if not is_windows():
        return ""

    import winreg

    try:
        with _open_run_key(winreg.KEY_QUERY_VALUE) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except FileNotFoundError:
        return ""


def sync_startup_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Applies startup settings to HKCU Run and returns non-sensitive status.
    """
    startup = settings.get("startup", {}) if isinstance(settings, dict) else {}
    launch_on_windows_start = bool(startup.get("launch_on_windows_start"))
    launch_when_valorant_starts = bool(startup.get("launch_when_valorant_starts"))

    status = {
        "supported": is_windows(),
        "launch_on_windows_start": launch_on_windows_start,
        "launch_when_valorant_starts": launch_when_valorant_starts,
        "app_entry": "",
        "watcher_entry": "",
    }

    if not is_windows():
        return status

    if launch_on_windows_start:
        set_run_entry(APP_RUN_VALUE, app_command())
    else:
        delete_run_entry(APP_RUN_VALUE)

    if launch_when_valorant_starts:
        set_run_entry(WATCHER_RUN_VALUE, watcher_command())
    else:
        delete_run_entry(WATCHER_RUN_VALUE)

    status["app_entry"] = get_run_entry(APP_RUN_VALUE)
    status["watcher_entry"] = get_run_entry(WATCHER_RUN_VALUE)
    return status


def startup_status() -> dict[str, Any]:
    """
    Returns the current HKCU Run status for this app.
    """
    return {
        "supported": is_windows(),
        "app_entry": get_run_entry(APP_RUN_VALUE),
        "watcher_entry": get_run_entry(WATCHER_RUN_VALUE),
        "expected_app_entry": app_command(),
        "expected_watcher_entry": watcher_command(),
    }
