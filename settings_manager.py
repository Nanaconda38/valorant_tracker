import json
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app_paths import ensure_runtime_dirs, settings_path


APP_VERSION = "0.1.1"
SETTINGS_SCHEMA_VERSION = 1

DEFAULT_SETTINGS = {
    "schema_version": SETTINGS_SCHEMA_VERSION,
    "app": {
        "version": APP_VERSION,
        "first_launch_completed": False,
        "debug": False,
    },
    "cache": {
        "enabled": True,
        "last_assets_reload_at": None,
    },
    "startup": {
        "launch_on_windows_start": False,
        "launch_when_valorant_starts": False,
    },
    "ui": {
        "theme": "system",
        "compact_mode": False,
    },
}


class SettingsManager:
    """
    Loads and saves non-sensitive local application settings.
    """

    def __init__(self, path: str | Path | None = None):
        """
        Initializes the settings manager.

        @param path: Optional settings file path, useful for tests and tooling.
        """
        self.path = Path(path) if path else settings_path()

    def load(self) -> dict[str, Any]:
        """
        Loads settings from disk, creating a default file when needed.
        """
        ensure_runtime_dirs()
        if not self.path.exists():
            settings = self.defaults()
            self.save(settings)
            return settings

        try:
            raw_settings = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._backup_corrupt_file()
            settings = self.defaults()
            self.save(settings)
            return settings

        settings = self._merge_defaults(raw_settings)
        if settings != raw_settings:
            self.save(settings)
        return settings

    def save(self, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Saves settings atomically and returns the normalized payload.
        """
        ensure_runtime_dirs()
        normalized = self._merge_defaults(settings)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(normalized, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.path)
        return normalized

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        """
        Applies a partial update and saves the result.
        """
        settings = self.load()
        merged = self._deep_merge(settings, patch)
        return self.save(merged)

    def mark_first_launch_completed(self) -> dict[str, Any]:
        """
        Marks onboarding/first-launch flow as completed.
        """
        return self.update({"app": {"first_launch_completed": True}})

    def defaults(self) -> dict[str, Any]:
        """
        Returns a fresh default settings payload.
        """
        return deepcopy(DEFAULT_SETTINGS)

    def _merge_defaults(self, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Keeps known settings keys and fills missing defaults.
        """
        merged = self.defaults()
        if isinstance(settings, dict):
            merged = self._deep_merge(merged, settings)
        merged["schema_version"] = SETTINGS_SCHEMA_VERSION
        merged["app"]["version"] = APP_VERSION
        return merged

    def _deep_merge(self, base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively merges dictionaries while ignoring unknown top-level groups.
        """
        result = deepcopy(base)
        for key, value in (patch or {}).items():
            if key not in DEFAULT_SETTINGS:
                continue
            if isinstance(result.get(key), dict) and isinstance(value, dict):
                result[key] = self._deep_merge_known_group(key, result[key], value)
            elif not isinstance(DEFAULT_SETTINGS.get(key), dict):
                result[key] = value
        return result

    def _deep_merge_known_group(
        self,
        group: str,
        base: dict[str, Any],
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Recursively merges a known settings group and ignores unknown keys.
        """
        result = deepcopy(base)
        default_group = DEFAULT_SETTINGS.get(group, {})
        for key, value in patch.items():
            if key not in default_group:
                continue
            result[key] = value
        return result

    def _backup_corrupt_file(self) -> None:
        """
        Preserves an unreadable settings file before replacing it.
        """
        if not self.path.exists():
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_path = self.path.with_name(f"{self.path.stem}.corrupt-{timestamp}{self.path.suffix}")
        try:
            shutil.copy2(self.path, backup_path)
        except OSError:
            pass
