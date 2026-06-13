import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


ASSET_ROOT = Path("static/assets/valorant")
MANIFEST_PATH = ASSET_ROOT / "manifest.json"
API_BASE = "https://valorant-api.com/v1"


def slugify(value: str) -> str:
    """
    Converts a display name to a filesystem-safe slug.

    @param value: Display name.
    @return: Slug string.
    """
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def extension_from_url(url: str) -> str:
    """
    Extracts the image extension from a CDN URL.

    @param url: Image URL.
    @return: File extension.
    """
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".png", ".jpg", ".jpeg", ".webp"} else ".png"


def download_image(session: requests.Session, url: str, target: Path) -> str:
    """
    Downloads an image if missing and returns the public static URL.

    @param session: HTTP session.
    @param url: Source image URL.
    @param target: Local target path.
    @return: Browser path under /static.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        response = session.get(url, timeout=30)
        response.raise_for_status()
        target.write_bytes(response.content)
    return "/" + target.as_posix().replace("\\", "/")


def fetch_json(session: requests.Session, endpoint: str) -> list:
    """
    Fetches a Valorant-API endpoint.

    @param session: HTTP session.
    @param endpoint: API endpoint after /v1/.
    @return: Data list.
    """
    response = session.get(f"{API_BASE}/{endpoint}", timeout=30)
    response.raise_for_status()
    return response.json()["data"]


def sync_assets() -> dict:
    """
    Downloads Valorant agents, maps, and rank assets into static assets.

    @return: Generated manifest.
    """
    manifest = {
        "agents": {},
        "agent_aliases": {},
        "maps": {},
        "ranks": {},
        "map_aliases": {}
    }

    with requests.Session() as session:
        agents = fetch_json(session, "agents?isPlayableCharacter=true")
        for agent in agents:
            name = agent["displayName"]
            slug = slugify(name)
            entry = {
                "name": name,
                "uuid": agent["uuid"]
            }
            for key, field in {
                "icon": "displayIcon",
                "full": "fullPortrait",
                "small": "displayIconSmall"
            }.items():
                url = agent.get(field)
                if url:
                    target = ASSET_ROOT / "agents" / f"{slug}-{key}{extension_from_url(url)}"
                    entry[key] = download_image(session, url, target)
            manifest["agents"][name.lower()] = entry
            manifest["agent_aliases"][agent["uuid"].lower()] = name.lower()

        maps = fetch_json(session, "maps")
        for game_map in maps:
            name = game_map["displayName"]
            slug = slugify(name)
            entry = {
                "name": name,
                "uuid": game_map["uuid"],
                "map_url": game_map.get("mapUrl", "")
            }
            for key, field in {
                "banner": "splash",
                "list": "listViewIcon",
                "icon": "displayIcon"
            }.items():
                url = game_map.get(field)
                if url:
                    target = ASSET_ROOT / "maps" / f"{slug}-{key}{extension_from_url(url)}"
                    entry[key] = download_image(session, url, target)
            manifest["maps"][name.lower()] = entry
            if entry["map_url"]:
                manifest["map_aliases"][entry["map_url"].lower()] = name.lower()

        tier_sets = fetch_json(session, "competitivetiers")
        latest_tiers = tier_sets[-1]["tiers"]
        for tier in latest_tiers:
            name = tier["tierName"].title()
            if name.startswith("Unused"):
                continue
            slug = slugify(name)
            entry = {
                "name": name,
                "tier": tier["tier"],
                "color": tier.get("color", "")
            }
            for key, field in {
                "small": "smallIcon",
                "large": "largeIcon"
            }.items():
                url = tier.get(field)
                if url:
                    target = ASSET_ROOT / "ranks" / f"{slug}-{key}{extension_from_url(url)}"
                    entry[key] = download_image(session, url, target)
            manifest["ranks"][name.lower()] = entry

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = sync_assets()
    print(
        f"Synced {len(result['agents'])} agents, "
        f"{len(result['maps'])} maps, {len(result['ranks'])} ranks."
    )
