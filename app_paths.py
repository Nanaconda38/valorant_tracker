import os
import sys
from pathlib import Path


APP_NAME = "ValorantTracker"


def is_frozen() -> bool:
    """
    Returns True when the app is running from a PyInstaller bundle.
    """
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """
    Returns the source project root in development mode.
    """
    return Path(__file__).resolve().parent


def bundled_root() -> Path:
    """
    Returns the root containing bundled read-only resources.
    """
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return project_root()


def resource_path(*parts: str) -> Path:
    """
    Resolves a read-only application resource path.
    """
    return bundled_root().joinpath(*parts)


def user_data_dir() -> Path:
    """
    Resolves the per-user runtime data directory.
    """
    override = os.getenv("VALORANT_TRACKER_DATA_DIR")
    if override:
        return Path(override).expanduser()

    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME

    return Path.home() / ".valorant_tracker"


def logs_dir() -> Path:
    """
    Resolves the application logs directory.
    """
    return user_data_dir() / "logs"


def cache_dir() -> Path:
    """
    Resolves the application cache directory.
    """
    return user_data_dir() / "cache"


def settings_path() -> Path:
    """
    Resolves the local settings file path.
    """
    return user_data_dir() / "settings.json"


def database_path() -> Path:
    """
    Resolves the local SQLite database path.
    """
    return user_data_dir() / "tracker.db"


def runtime_path(*parts: str) -> Path:
    """
    Resolves a writable path inside the per-user runtime data directory.
    """
    return user_data_dir().joinpath(*parts)


def ensure_runtime_dirs() -> None:
    """
    Creates the standard per-user runtime directories.
    """
    user_data_dir().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    cache_dir().mkdir(parents=True, exist_ok=True)
