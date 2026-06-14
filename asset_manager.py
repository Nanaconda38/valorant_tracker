import json
from pathlib import Path

from app_paths import resource_path

MANIFEST_PATH = resource_path("static", "assets", "valorant", "manifest.json")


class AssetManager:
    """
    Resolves local Valorant asset URLs from the generated manifest.
    """

    def __init__(self, manifest_path: Path = MANIFEST_PATH):
        """
        Initializes the asset manager.

        @param manifest_path: Path to the generated asset manifest.
        """
        self.manifest_path = manifest_path
        self.manifest = {
            "agents": {},
            "agent_aliases": {},
            "maps": {},
            "ranks": {},
            "map_aliases": {}
        }
        self.reload()

    def reload(self) -> None:
        """
        Reloads the manifest from disk if it exists.
        """
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def agent(self, name: str) -> dict:
        """
        Returns assets for an agent name.

        @param name: Agent display name.
        @return: Asset dictionary.
        """
        key = (name or "").lower()
        alias = self.manifest.get("agent_aliases", {}).get(key, key)
        return self.manifest.get("agents", {}).get(alias, {})

    def rank(self, name: str) -> dict:
        """
        Returns assets for a rank name.

        @param name: Rank display name.
        @return: Asset dictionary.
        """
        normalized = (name or "Unranked").lower()
        return self.manifest.get("ranks", {}).get(normalized, {})

    def map(self, value: str) -> dict:
        """
        Returns assets for a map path or display name.

        @param value: Riot map path or display name.
        @return: Asset dictionary.
        """
        key = (value or "").lower()
        alias = self.manifest.get("map_aliases", {}).get(key, key)
        return self.manifest.get("maps", {}).get(alias, {})
