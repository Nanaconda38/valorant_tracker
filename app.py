import os
import asyncio
import base64
import json
import math
import re
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app_logging import configure_logging, get_logger
from app_paths import cache_dir, ensure_runtime_dirs, logs_dir, resource_path, runtime_path, user_data_dir
from asset_manager import AssetManager
from autostart_manager import startup_status, sync_startup_settings
from database import DatabaseManager
from secrets_manager import HenrikSecretManager, SecretStorageError
from settings_manager import SettingsManager
from tracker_score_model import predict_trs_raw

ensure_runtime_dirs()
configure_logging()
logger = get_logger(__name__)
if os.getenv("VALORANT_TRACKER_SKIP_DOTENV") != "1":
    load_dotenv(resource_path(".env"))

SESSION_STARTED_AT = datetime.now(timezone.utc).isoformat()

app = FastAPI(title="Valorant Local Tracker")

app.mount("/static", StaticFiles(directory=str(resource_path("static"))), name="static")

templates = Jinja2Templates(directory=str(resource_path("templates")))
asset_manager = AssetManager()
db_manager = DatabaseManager()
settings_manager = SettingsManager()
henrik_secret_manager = HenrikSecretManager()
from updater import AppUpdater
app_updater = AppUpdater()

tracker_state = {
    "status": "offline",
    "player_name": "Unknown",
    "puuid": "",
    "game_phase": "OFFLINE",
    "queue_id": "",
    "map_id": "",
    "allies": [],
    "enemies": [],
    "current_match_id": "",
    "core_match_id": "",
    "last_match": None,
    "last_match_status": "",
    "session_summary": {
        "wins": 0,
        "losses": 0,
        "rr_delta": 0
    }
}
persisted_match_ids = set()

stats_cache = {}
player_name_cache = {}
stats_cache_context = {
    "game_phase": tracker_state["game_phase"],
    "queue_id": tracker_state["queue_id"],
    "map_id": tracker_state["map_id"]
}
season_catalog_cache = {
    "loaded": False,
    "acts": {}
}


def get_henrik_api_key() -> str | None:
    """
    Reads the HenrikDev key from local secret storage or dev environment.
    """
    try:
        return henrik_secret_manager.get_key()
    except SecretStorageError as exc:
        logger.error("Henrik secret storage error: %s", exc)
        return None


def normalize_henrik_api_key(api_key: str) -> str:
    """
    Normalizes user-pasted HenrikDev keys without exposing their value.
    """
    cleaned_key = (api_key or "").strip()
    if cleaned_key.lower().startswith("bearer "):
        return cleaned_key[7:].strip()
    return cleaned_key


async def verify_henrik_api_key(api_key: str) -> dict:
    """
    Verifies that a HenrikDev key is accepted by the API.
    """
    cleaned_key = normalize_henrik_api_key(api_key)
    if not cleaned_key:
        return {
            "status": "error",
            "valid": False,
            "reason": "empty_key",
            "message": "HenrikDev API key is empty."
        }

    headers = {"Authorization": cleaned_key}
    probe_puuid = "00000000-0000-0000-0000-000000000000"
    probe_url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/eu/pc/{probe_puuid}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(probe_url, headers=headers)
    except httpx.RequestError:
        return {
            "status": "error",
            "valid": False,
            "reason": "api_unreachable",
            "message": "HenrikDev API did not respond."
        }

    if response.status_code in {401, 403}:
        return {
            "status": "error",
            "valid": False,
            "reason": "invalid_key",
            "message": "HenrikDev API key was rejected."
        }
    if response.status_code == 429:
        return {
            "status": "error",
            "valid": False,
            "reason": "rate_limited",
            "message": "HenrikDev API rate limit reached. Try again later."
        }
    if response.status_code >= 500:
        return {
            "status": "error",
            "valid": False,
            "reason": "api_unavailable",
            "message": "HenrikDev API is temporarily unavailable."
        }

    return {
        "status": "ok",
        "valid": True,
        "reason": "accepted",
        "message": "HenrikDev API key was accepted."
    }


def extract_match_season_id(match_data: dict) -> str:
    """
    Extracts the competitive Act id from Riot match details.
    """
    match_info = match_data.get("matchInfo") or match_data.get("MatchInfo") or {}
    return (
        match_info.get("seasonId")
        or match_info.get("seasonID")
        or match_info.get("SeasonID")
        or ""
    )


def fallback_season_label(season_id: str) -> str:
    """
    Builds a short label when the remote seasons catalog is unavailable.
    """
    return f"ACT {season_id[:8].upper()}" if season_id else "UNKNOWN ACT"


def parse_riot_datetime(value: str) -> datetime | None:
    """
    Parses Riot and app ISO timestamps into timezone-aware datetimes.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def season_id_for_match_date(match_date: str, season_catalog: dict) -> str:
    """
    Infers the Act id from the match date when match details are not cached.
    """
    parsed_match_date = parse_riot_datetime(match_date)
    if not parsed_match_date:
        return ""

    for season_id, season_meta in season_catalog.items():
        start_time = parse_riot_datetime(season_meta.get("start_time", ""))
        end_time = parse_riot_datetime(season_meta.get("end_time", ""))
        if start_time and end_time and start_time <= parsed_match_date < end_time:
            return season_id
    return ""


async def get_valorant_season_catalog() -> dict:
    """
    Loads Valorant Acts and their parent Episodes from the public content catalog.
    """
    if season_catalog_cache["loaded"]:
        return season_catalog_cache["acts"]

    acts = {}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get("https://valorant-api.com/v1/seasons")
            response.raise_for_status()
            seasons = response.json().get("data", [])

        episodes = {item.get("uuid"): item for item in seasons if not item.get("parentUuid")}
        for item in seasons:
            if item.get("type") != "EAresSeasonType::Act":
                continue
            season_id = item.get("uuid", "")
            episode = episodes.get(item.get("parentUuid"), {})
            episode_label = episode.get("displayName") or ""
            label = item.get("title") or " // ".join(
                part for part in [episode_label, item.get("displayName")] if part
            )
            acts[season_id] = {
                "id": season_id,
                "label": label or fallback_season_label(season_id),
                "episode_id": item.get("parentUuid") or "",
                "episode_label": episode_label,
                "start_time": item.get("startTime") or "",
                "end_time": item.get("endTime") or ""
            }
    except Exception as exc:
        logger.warning("Valorant seasons catalog unavailable: %s", exc)

    season_catalog_cache["acts"] = acts
    season_catalog_cache["loaded"] = True
    return acts


def clear_stats_cache(reason: str) -> None:
    """
    Clears cached player stats and logs why the cache was invalidated.

    @param reason: Human-readable reason for the cache clear.
    """
    if stats_cache:
        logger.debug("Stats cache cleared: %s (%s entries)", reason, len(stats_cache))
    stats_cache.clear()


def refresh_stats_cache_context() -> None:
    """
    Tracks the active game context without invalidating career stats cache.
    """
    current_context = {
        "game_phase": tracker_state.get("game_phase", "OFFLINE"),
        "queue_id": tracker_state.get("queue_id", ""),
        "map_id": tracker_state.get("map_id", "")
    }
    
    if current_context != stats_cache_context:
        reason = (
            f"{stats_cache_context['game_phase']}:{stats_cache_context['queue_id']}:{stats_cache_context['map_id']}"
            f" -> {current_context['game_phase']}:{current_context['queue_id']}:{current_context['map_id']}"
        )
        logger.info("Riot context changed: %s", reason)
        stats_cache_context.update(current_context)

AGENT_MAPPING = {
    "e370fa57-4757-3604-3648-499e1f642d3f": "Gekko",
    "dade69b4-4f5a-8528-247b-219e5a1facd6": "Fade",
    "5f8d3a7f-467b-97f3-062c-13acf203c006": "Breach",
    "cc8b64c8-4b25-4ff9-6e7f-37b4da43d235": "Deadlock",
    "b444168c-4e35-8076-db47-ef9bf368f384": "Tejo",
    "f94c3b30-42be-e959-889c-5aa313dba261": "Raze",
    "22697a3d-45bf-8dd7-4fec-84a9e28c69d7": "Chamber",
    "601dbbe7-43ce-be57-2a40-4abd24953621": "KAY/O",
    "6f2a04ca-43e0-be17-7f36-b3908627744d": "Skye",
    "117ed9e3-49f3-6512-3ccf-0cada7e3823b": "Cypher",
    "320b2a48-4d9b-a075-30f1-1f93a9b638fa": "Sova",
    "7c8a4701-4de6-9355-b254-e09bc2a34b72": "Miks",
    "1e58de9c-4950-5125-93e9-a0aee9f98746": "Killjoy",
    "95b78ed7-4637-86d9-7e41-71ba8c293152": "Harbor",
    "efba5359-4016-a1e5-7626-b1ae76895940": "Vyse",
    "707eab51-4836-f488-046a-cda6bf494859": "Viper",
    "eb93336a-449b-9c1b-0a54-a891f7921d69": "Phoenix",
    "92eeef5d-43b5-1d4a-8d03-b3927a09034b": "Veto",
    "41fb69c1-4189-7b37-f117-bcaf1e96f1bf": "Astra",
    "9f0d8ba9-4140-b941-57d3-a7ad57c6b417": "Brimstone",
    "0e38b510-41a8-5780-5e8f-568b2a4f2d6c": "Iso",
    "1dbf2edd-4729-0984-3115-daa5eed44993": "Clove",
    "bb2a4828-46eb-8cd1-e765-15848195d751": "Neon",
    "7f94d92c-4234-0a36-9646-3a87eb8b5c89": "Yoru",
    "df1cb487-4902-002e-5c17-d28e83e78588": "Waylay",
    "569fdd95-4d10-43ab-ca70-79becc718b46": "Sage",
    "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc": "Reyna",
    "8e253930-4c05-31dd-1b6c-968525494517": "Omen",
    "add6443a-41bd-e414-f6ad-e58d267f4e95": "Jett"
}

RANKS = [
    "Unranked",
    "Iron 1", "Iron 2", "Iron 3",
    "Bronze 1", "Bronze 2", "Bronze 3",
    "Silver 1", "Silver 2", "Silver 3",
    "Gold 1", "Gold 2", "Gold 3",
    "Platinum 1", "Platinum 2", "Platinum 3",
    "Diamond 1", "Diamond 2", "Diamond 3",
    "Ascendant 1", "Ascendant 2", "Ascendant 3",
    "Immortal 1", "Immortal 2", "Immortal 3",
    "Radiant"
]

RANK_BY_TIER = {
    0: "Unranked",
    3: "Iron 1", 4: "Iron 2", 5: "Iron 3",
    6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3",
    9: "Silver 1", 10: "Silver 2", 11: "Silver 3",
    12: "Gold 1", 13: "Gold 2", 14: "Gold 3",
    15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3",
    18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3",
    21: "Ascendant 1", 22: "Ascendant 2", 23: "Ascendant 3",
    24: "Immortal 1", 25: "Immortal 2", 26: "Immortal 3",
    27: "Radiant"
}


def get_rank_index(rank_name: str) -> int:
    """
    Finds the index of a rank in the RANKS array.

    @param rank_name: The name of the rank.
    @return: The index integer.
    """
    clean = str(rank_name or "").lower()
    roman_map = {"iii": "3", "ii": "2", "i": "1"}
    for rank_root in ["iron", "bronze", "silver", "gold", "platinum", "diamond", "ascendant", "immortal"]:
        clean = re.sub(
            rf"\b{rank_root}\s+(iii|ii|i)\b",
            lambda match: f"{rank_root} {roman_map[match.group(1)]}",
            clean,
        )

    for i, r in enumerate(RANKS):
        if r.lower() in clean:
            return i
    return 0


def average_rank_name(players: list[dict]) -> str:
    rank_indexes = [
        get_rank_index(str(player.get("rank", "")))
        for player in players
        if get_rank_index(str(player.get("rank", ""))) > 0
    ]
    if not rank_indexes:
        return ""
    return RANKS[max(0, min(len(RANKS) - 1, round(sum(rank_indexes) / len(rank_indexes))))]


def calculate_tracker_score(
    kd: float,
    hs_percent: float,
    acs: int,
    rank: str,
    peak_rank: str,
    adr: float | None = None,
    dda: float | None = None,
    kast: float | None = None,
    kills: int | None = None,
    deaths: int | None = None,
    assists: int | None = None,
    fk: int = 0,
    fd: int = 0,
    mk: int = 0,
    rounds_played: int | None = None,
    won: bool | None = None,
    team_rounds: int | None = None,
    enemy_rounds: int | None = None,
    avg_rank: str | None = None
) -> int:
    """
    Computes a Tracker.gg-like performance score out of 1000.

    @param kd: Kill-death ratio.
    @param hs_percent: Headshot percentage.
    @param acs: Average combat score.
    @param rank: Current rank.
    @param peak_rank: Peak rank.
    @return: The computed score.
    """
    rounds = max(int(_number_or_zero(rounds_played)), 1)
    safe_kills = int(_number_or_zero(kills))
    safe_deaths = int(_number_or_zero(deaths))
    safe_assists = int(_number_or_zero(assists))
    if kills is None and deaths is None:
        safe_deaths = rounds
        safe_kills = round(kd * safe_deaths)
    safe_adr = float(adr if adr is not None else max(0, acs * 0.68))
    safe_dda = float(dda if dda is not None else 0)
    safe_kast = float(kast if kast is not None else 70)
    safe_hs = float(hs_percent or 0) / 100
    safe_kast_rate = safe_kast / 100
    team_total = int(_number_or_zero(team_rounds))
    enemy_total = int(_number_or_zero(enemy_rounds))
    total_rounds = max(team_total + enemy_total, rounds)
    round_diff = ((team_total - enemy_total) / total_rounds) if team_total or enemy_total else 0
    won_value = 1 if won else 0
    player_rank_index = get_rank_index(rank or peak_rank or "")
    avg_rank_index = get_rank_index(avg_rank or "")
    rank_scaled = player_rank_index / 25
    avg_rank_scaled = avg_rank_index / 25
    rank_delta_scaled = (player_rank_index - avg_rank_index) / 25 if avg_rank_index else 0
    plus_minus = safe_kills - safe_deaths
    log_kill_death = math.log1p(max(safe_kills, 0)) - math.log1p(max(safe_deaths, 0))

    stats = {
        "acs": float(acs),
        "adr": float(safe_adr),
        "dda": float(safe_dda),
        "kd": float(kd),
        "plus_minus": float(plus_minus),
        "hs_rate": float(safe_hs),
        "kast_rate": float(safe_kast_rate),
        "fk_per_round": float(fk / rounds),
        "fd_per_round": float(fd / rounds),
        "mk_per_round": float(mk / rounds),
        "assists_per_round": float(safe_assists / rounds),
        "kills_per_round": float(safe_kills / rounds),
        "deaths_per_round": float(safe_deaths / rounds),
        "won": float(won_value),
        "round_diff": float(round_diff),
        "player_rank_idx": float(player_rank_index),
        "avg_rank_idx": float(avg_rank_index),
        "rank_delta": float(player_rank_index - avg_rank_index),
        "log_kill_death": float(log_kill_death),
        "rounds": float(total_rounds),
        "team_rounds": float(team_total),
        "enemy_rounds": float(enemy_total),
    }

    score = predict_trs_raw(stats)
    return max(100, min(1000, round(score)))


def rank_name_from_tier(tier: int | None) -> str:
    """
    Converts Riot competitive tier ids to display rank names.

    @param tier: Riot competitive tier id.
    @return: Rank display name.
    """
    if tier is None:
        return ""
    return RANK_BY_TIER.get(int(_number_or_zero(tier)), "")


def enrich_player_assets(player_info: dict) -> dict:
    """
    Adds local agent and rank asset URLs to a player card payload.

    @param player_info: Player card dictionary.
    @return: The same dictionary enriched with asset URLs.
    """
    agent_assets = asset_manager.agent(player_info.get("agent_id", "")) or asset_manager.agent(player_info.get("agent", ""))
    rank_assets = asset_manager.rank(player_info.get("rank", ""))
    peak_rank_assets = asset_manager.rank(player_info.get("peak_rank", ""))
    player_info["agent_icon_url"] = agent_assets.get("icon", "")
    player_info["agent_full_url"] = agent_assets.get("full", "")
    player_info["rank_icon_url"] = rank_assets.get("small") or rank_assets.get("large", "")
    player_info["peak_rank_icon_url"] = peak_rank_assets.get("small") or peak_rank_assets.get("large", "")
    return player_info


def enrich_match_assets(match_info: dict) -> dict:
    """
    Adds local agent, rank, and map asset URLs to a match payload.

    @param match_info: Match dictionary.
    @return: The same dictionary enriched with asset URLs.
    """
    agent_assets = asset_manager.agent(match_info.get("agent_id", "")) or asset_manager.agent(match_info.get("agent", ""))
    map_assets = asset_manager.map(match_info.get("map_id") or match_info.get("map", ""))
    rank_before_assets = asset_manager.rank(match_info.get("rank_before", ""))
    rank_after_assets = asset_manager.rank(match_info.get("rank_after", ""))
    match_info["agent_icon_url"] = agent_assets.get("icon", "")
    match_info["agent_full_url"] = agent_assets.get("full", "")
    match_info["map_name"] = map_assets.get("name", "")
    match_info["map_banner_url"] = map_assets.get("banner", "")
    match_info["rank_before_icon_url"] = rank_before_assets.get("small") or rank_before_assets.get("large", "")
    match_info["rank_after_icon_url"] = rank_after_assets.get("small") or rank_after_assets.get("large", "")
    return match_info


def get_local_client_version() -> str:
    """
    Parses VALORANT client version from local log files if available.
    Falls back to a default value matching a recently observed version.
    """
    try:
        import os
        log_path = os.path.expandvars(r'%LOCALAPPDATA%\VALORANT\Saved\Logs\ShooterGame.log')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Scan up to the first 300 lines (the version is logged very early at startup)
                for _ in range(300):
                    line = f.readline()
                    if not line:
                        break
                    if "CI server version:" in line:
                        parts = line.split("CI server version:")
                        if len(parts) > 1:
                            val = parts[1].strip()
                            if val:
                                return val
    except Exception:
        pass
    return "release-12.11-shipping-9-4815575"


def get_region_shard(local_region: str) -> tuple:
    """
    Maps LCU region to GLZ region and shard.

    @param local_region: The local region string from LCU.
    @return: A tuple of (glz_region, shard).
    """
    r_lower = local_region.lower()
    if "na" in r_lower or "latam" in r_lower or "br" in r_lower or "pbe" in r_lower:
        return "na", "na"
    elif "ap" in r_lower:
        return "ap", "ap"
    elif "kr" in r_lower:
        return "kr", "kr"
    else:
        return "eu", "eu"


def find_premade_groups(players: list) -> dict:
    """
    Groups players by detecting matching match history entries.

    @param players: The list of players with match history IDs.
    @return: A dictionary mapping PUUID to group ID.
    """
    group_map = {}
    group_counter = 0
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            p1 = players[i]
            p2 = players[j]
            p1_matches = set(p1.get("match_ids", []))
            p2_matches = set(p2.get("match_ids", []))
            shared = p1_matches.intersection(p2_matches)
            if len(shared) >= 3:
                p1_puuid = p1["puuid"]
                p2_puuid = p2["puuid"]
                if p1_puuid in group_map and p2_puuid in group_map:
                    continue
                elif p1_puuid in group_map:
                    group_map[p2_puuid] = group_map[p1_puuid]
                elif p2_puuid in group_map:
                    group_map[p1_puuid] = group_map[p2_puuid]
                else:
                    group_counter += 1
                    group_map[p1_puuid] = group_counter
                    group_map[p2_puuid] = group_counter
    return group_map


def _number_or_zero(value) -> float:
    """
    Converts numeric API values to a number and treats None/invalid values as zero.

    @param value: API value that may be numeric, null, or malformed.
    @return: Numeric value or zero.
    """
    if value is None:
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def iso_from_riot_millis(value) -> str:
    """
    Converts Riot millisecond timestamps to an ISO UTC datetime.

    @param value: Riot timestamp in milliseconds.
    @return: ISO datetime string.
    """
    milliseconds = _number_or_zero(value)
    if milliseconds <= 0:
        return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).isoformat()


def start_tracking_match(match_id: str) -> None:
    """
    Stores the active match id and clears the previous post-match summary.

    @param match_id: Riot match id for the active game.
    """
    if not match_id:
        return
    if tracker_state.get("current_match_id") != match_id:
        tracker_state["current_match_id"] = match_id
        tracker_state["core_match_id"] = ""
        tracker_state["last_match"] = None
        tracker_state["last_match_status"] = ""


def build_post_match_summary(match_data: dict, puuid: str) -> dict | None:
    """
    Builds the local player's completed match summary from Riot PD match details.

    @param match_data: PD match-details response.
    @param puuid: Local player's PUUID.
    @return: Summary dictionary, or None when the payload is incomplete.
    """
    players = match_data.get("players", [])
    player = next((p for p in players if p.get("subject") == puuid or p.get("Subject") == puuid), None)
    if not player:
        return None

    stats = player.get("stats") or player.get("Stats") or {}
    match_info = match_data.get("matchInfo") or match_data.get("MatchInfo") or {}
    teams = match_data.get("teams") or match_data.get("Teams") or []
    team_id = player.get("teamId") or player.get("TeamID") or player.get("teamID")

    team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) == team_id), {})
    enemy_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) != team_id), {})

    rounds_won = int(_number_or_zero(team.get("roundsWon") or team.get("RoundsWon") or team.get("numPoints")))
    enemy_rounds = int(_number_or_zero(enemy_team.get("roundsWon") or enemy_team.get("RoundsWon") or enemy_team.get("numPoints")))
    won = bool(team.get("won") if "won" in team else team.get("Won", rounds_won > enemy_rounds))

    kills = int(_number_or_zero(stats.get("kills") or stats.get("Kills")))
    deaths = int(_number_or_zero(stats.get("deaths") or stats.get("Deaths")))
    assists = int(_number_or_zero(stats.get("assists") or stats.get("Assists")))
    score = int(_number_or_zero(stats.get("score") or stats.get("Score")))
    rounds_played = int(_number_or_zero(stats.get("roundsPlayed") or stats.get("RoundsPlayed") or rounds_won + enemy_rounds))
    acs = round(score / max(rounds_played, 1))

    headshots = 0
    bodyshots = 0
    legshots = 0
    for round_result in match_data.get("roundResults", []) or match_data.get("RoundResults", []) or []:
        for player_stats in round_result.get("playerStats", []) or round_result.get("PlayerStats", []) or []:
            if player_stats.get("subject") != puuid and player_stats.get("Subject") != puuid:
                continue
            for damage in player_stats.get("damage", []) or player_stats.get("Damage", []) or []:
                headshots += int(_number_or_zero(damage.get("headshots") or damage.get("Headshots")))
                bodyshots += int(_number_or_zero(damage.get("bodyshots") or damage.get("Bodyshots")))
                legshots += int(_number_or_zero(damage.get("legshots") or damage.get("Legshots")))
    if headshots + bodyshots + legshots == 0:
        for damage in player.get("roundDamage", []) or player.get("RoundDamage", []) or []:
            headshots += int(_number_or_zero(damage.get("headshots") or damage.get("Headshots")))
            bodyshots += int(_number_or_zero(damage.get("bodyshots") or damage.get("Bodyshots")))
            legshots += int(_number_or_zero(damage.get("legshots") or damage.get("Legshots")))
    total_shots = headshots + bodyshots + legshots
    hs_percent = round((headshots / total_shots) * 100, 1) if total_shots > 0 else 0.0

    agent_id = player.get("characterId") or player.get("CharacterID") or ""
    queue_id = match_info.get("queueID") or match_info.get("queueId") or tracker_state.get("queue_id", "")
    map_id = match_info.get("mapId") or match_info.get("mapID") or tracker_state.get("map_id", "")
    season_id = extract_match_season_id(match_data)

    return {
        "match_id": match_info.get("matchId") or match_info.get("matchID") or tracker_state.get("current_match_id", ""),
        "queue_id": queue_id,
        "map_id": map_id,
        "season_id": season_id,
        "agent_id": agent_id,
        "agent": AGENT_MAPPING.get(agent_id, "Unknown Agent"),
        "won": won,
        "result": "VICTORY" if won else "DEFEAT",
        "scoreline": f"{rounds_won}-{enemy_rounds}" if rounds_won or enemy_rounds else "--",
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kd": round(kills / max(deaths, 1), 2),
        "kda": round((kills + assists) / max(deaths, 1), 2),
        "acs": acs,
        "score": score,
        "hs_percent": hs_percent,
        "rounds_played": rounds_played
    }


def build_cached_match_tracker_context(match_data: dict, puuid: str) -> dict | None:
    """
    Computes the local player's TRS from cached Riot match-details data.

    This intentionally mirrors the scoreboard modal calculation so career rows
    do not drift from the exact per-game score shown in match details.
    """
    players = match_data.get("players", []) or match_data.get("Players", []) or []
    match_info = match_data.get("matchInfo") or match_data.get("MatchInfo") or {}
    teams = match_data.get("teams") or match_data.get("Teams") or []
    round_results = match_data.get("roundResults", []) or match_data.get("RoundResults", []) or []
    player = next((p for p in players if (p.get("subject") or p.get("Subject")) == puuid), None)
    if not player:
        return None

    team_id = player.get("teamId") or player.get("TeamID") or player.get("teamID")
    if not team_id:
        return None

    team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) == team_id), {})
    enemy_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) != team_id), {})
    team_rounds = int(_number_or_zero(team.get("roundsWon") or team.get("RoundsWon") or team.get("numPoints")))
    enemy_rounds = int(_number_or_zero(enemy_team.get("roundsWon") or enemy_team.get("RoundsWon") or enemy_team.get("numPoints")))
    won = bool(team.get("won") if "won" in team else team.get("Won", team_rounds > enemy_rounds))

    stats = player.get("stats") or player.get("Stats") or {}
    kills = int(_number_or_zero(stats.get("kills") or stats.get("Kills")))
    deaths = int(_number_or_zero(stats.get("deaths") or stats.get("Deaths")))
    assists = int(_number_or_zero(stats.get("assists") or stats.get("Assists")))
    raw_score = int(_number_or_zero(stats.get("score") or stats.get("Score")))
    rounds_played = int(_number_or_zero(stats.get("roundsPlayed") or stats.get("RoundsPlayed") or team_rounds + enemy_rounds))
    if rounds_played <= 0:
        return None
    acs = round(raw_score / max(rounds_played, 1))

    headshots = 0
    bodyshots = 0
    legshots = 0
    for round_result in round_results:
        player_stats_list = round_result.get("playerStats") or round_result.get("PlayerStats") or []
        for player_stats in player_stats_list:
            if (player_stats.get("subject") or player_stats.get("Subject")) != puuid:
                continue
            damage_list = player_stats.get("damage") or player_stats.get("Damage") or []
            for damage in damage_list:
                headshots += int(_number_or_zero(damage.get("headshots") or damage.get("Headshots")))
                bodyshots += int(_number_or_zero(damage.get("bodyshots") or damage.get("Bodyshots")))
                legshots += int(_number_or_zero(damage.get("legshots") or damage.get("Legshots")))
    total_shots = headshots + bodyshots + legshots
    hs_percent = round((headshots / max(total_shots, 1)) * 100, 1) if total_shots > 0 else 0.0

    player_puuids = [p.get("subject") or p.get("Subject") or "" for p in players]
    player_teams = {
        (p.get("subject") or p.get("Subject") or ""): (p.get("teamId") or p.get("TeamID") or p.get("teamID") or "")
        for p in players
    }
    round_metric_map = build_round_player_metrics(round_results, player_puuids, player_teams)
    metrics = round_metric_map.get(puuid, {})
    damage_dealt = int(metrics.get("damage_dealt", 0))
    damage_received = int(metrics.get("damage_received", 0))
    adr = round(damage_dealt / max(rounds_played, 1), 1)
    dda = round((damage_dealt - damage_received) / max(rounds_played, 1), 1)
    kast = round((int(metrics.get("kast_rounds", 0)) / max(rounds_played, 1)) * 100, 1)

    rank = rank_name_from_tier(player.get("competitiveTier") or player.get("CompetitiveTier") or 0) or "Unranked"
    team_rank_players = [
        {"rank": rank_name_from_tier(p.get("competitiveTier") or p.get("CompetitiveTier") or 0) or "Unranked"}
        for p in players
        if (p.get("teamId") or p.get("TeamID") or p.get("teamID")) == team_id
    ]
    avg_rank = average_rank_name(team_rank_players) or rank

    tracker_score = calculate_tracker_score(
        kd=round(kills / max(deaths, 1), 2),
        hs_percent=hs_percent,
        acs=acs,
        rank=rank,
        peak_rank=rank,
        adr=adr,
        dda=dda,
        kast=kast,
        kills=kills,
        deaths=deaths,
        assists=assists,
        fk=int(metrics.get("first_kills", 0)),
        fd=int(metrics.get("first_deaths", 0)),
        mk=int(metrics.get("multi_kills", 0)),
        rounds_played=rounds_played,
        won=won,
        team_rounds=team_rounds,
        enemy_rounds=enemy_rounds,
        avg_rank=avg_rank
    )
    total_rounds = team_rounds + enemy_rounds
    return {
        "tracker_score": tracker_score,
        "season_id": extract_match_season_id({"matchInfo": match_info}),
        "kast": kast,
        "dda": dda,
        "adr": adr,
        "team_rounds": team_rounds,
        "enemy_rounds": enemy_rounds,
        "rounds_played": rounds_played,
        "round_win_percent": round((team_rounds / total_rounds) * 100, 1) if total_rounds else None,
    }


def calculate_cached_match_tracker_score(match_data: dict, puuid: str) -> int | None:
    """
    Computes the local player's exact match TRS from cached details.
    """
    context = build_cached_match_tracker_context(match_data, puuid)
    if not context:
        return None
    return context["tracker_score"]


def get_cached_match_tracker_score(match_id: str, puuid: str) -> int | None:
    """
    Returns the exact cached match-detail TRS for a player when available.
    """
    if not match_id or not puuid:
        return None
    raw_json = db_manager.get_match_details_json(match_id)
    if not raw_json:
        return None
    try:
        return calculate_cached_match_tracker_score(json.loads(raw_json), puuid)
    except Exception as exc:
        logger.debug("Career TRS cache miss: match_id=%s error=%s", match_id, exc)
        return None


def get_cached_match_tracker_context(match_id: str, puuid: str) -> dict | None:
    """
    Returns cached profile-score ingredients for a match when available.
    """
    if not match_id or not puuid:
        return None
    raw_json = db_manager.get_match_details_json(match_id)
    if not raw_json:
        return None
    try:
        return build_cached_match_tracker_context(json.loads(raw_json), puuid)
    except Exception as exc:
        logger.debug("Career TRS context miss: match_id=%s error=%s", match_id, exc)
        return None


def get_cached_match_season_id(match_id: str) -> str:
    """
    Returns the cached Act id for a match when available.
    """
    if not match_id:
        return ""
    raw_json = db_manager.get_match_details_json(match_id)
    if not raw_json:
        return ""
    try:
        return extract_match_season_id(json.loads(raw_json))
    except Exception as exc:
        logger.debug("Career season cache miss: match_id=%s error=%s", match_id, exc)
        return ""


def persist_match_season_id(match_id: str, season_id: str, puuid: str = "", overwrite: bool = False) -> None:
    """
    Saves a resolved Act id on the career row when the match already exists.
    """
    if not match_id or not season_id:
        return
    db_manager.update_match_season_id(match_id, season_id, puuid=puuid, overwrite=overwrite)


async def backfill_missing_match_seasons(limit: int = 500) -> int:
    """
    Resolves missing Act ids for saved matches using exact cache first, then match date.
    """
    season_catalog = await get_valorant_season_catalog()
    updated = 0
    for match in db_manager.get_matches_missing_season_id(limit=limit):
        match_id = match.get("match_id", "")
        season_id = get_cached_match_season_id(match_id)
        overwrite = bool(season_id)
        if not season_id:
            season_id = season_id_for_match_date(match.get("date", ""), season_catalog)
        if not season_id:
            continue
        if db_manager.update_match_season_id(
            match_id,
            season_id,
            puuid=match.get("puuid", ""),
            overwrite=overwrite
        ):
            updated += 1
    if updated:
        logger.info("Backfilled season ids for %s saved matches", updated)
    return updated


async def fetch_post_match_summary(client: httpx.AsyncClient, pd_url: str, match_id: str, puuid: str, headers: dict) -> dict | None:
    """
    Fetches completed match details and returns the local player's game stats.

    @param client: HTTP client.
    @param pd_url: Riot PD base URL.
    @param match_id: Match id to fetch.
    @param puuid: Local player's PUUID.
    @param headers: Riot auth headers.
    @return: Summary dictionary, or None while match details are not ready.
    """
    match_resp = await client.get(f"{pd_url}/match-details/v1/matches/{match_id}", headers=headers)
    if match_resp.status_code != 200:
        logger.debug("Post-match details unavailable: status=%s match_id=%s", match_resp.status_code, match_id)
        return None
    try:
        db_manager.save_match_details_json(match_id, match_resp.text)
    except Exception as cache_err:
        logger.warning("Failed to cache raw match details: match_id=%s error=%s", match_id, cache_err)
    return build_post_match_summary(match_resp.json(), puuid)


def extract_rr_change(mmr_data: dict, match_id: str) -> int:
    """
    Extracts the RR delta for a match from Riot MMR payloads.

    @param mmr_data: Riot MMR response payload.
    @param match_id: Completed match id.
    @return: Ranked rating delta, or zero when unavailable.
    """
    candidates = []
    matches = mmr_data.get("Matches", [])
    if isinstance(matches, list):
        candidates.extend(matches)

    latest = mmr_data.get("LatestCompetitiveUpdate")
    if isinstance(latest, dict):
        candidates.append(latest)

    for item in candidates:
        if not isinstance(item, dict):
            continue
        if item.get("MatchID") == match_id or item.get("MatchId") == match_id or item.get("matchId") == match_id:
            return int(_number_or_zero(item.get("RankedRatingEarned")))

    return 0


def extract_mmr_update(mmr_data: dict, match_id: str) -> dict:
    """
    Extracts RR and rank movement for a match from Riot MMR payloads.

    @param mmr_data: Riot MMR response payload.
    @param match_id: Completed match id.
    @return: Match MMR update dictionary.
    """
    candidates = []
    matches = mmr_data.get("Matches", [])
    if isinstance(matches, list):
        candidates.extend(matches)

    latest = mmr_data.get("LatestCompetitiveUpdate")
    if isinstance(latest, dict):
        candidates.append(latest)

    for item in candidates:
        if not isinstance(item, dict):
            continue
        if item.get("MatchID") == match_id or item.get("MatchId") == match_id or item.get("matchId") == match_id:
            tier_before = int(_number_or_zero(item.get("TierBeforeUpdate")))
            tier_after = int(_number_or_zero(item.get("TierAfterUpdate")))
            return {
                "rr_change": int(_number_or_zero(item.get("RankedRatingEarned"))),
                "rank_before": rank_name_from_tier(tier_before),
                "rank_after": rank_name_from_tier(tier_after),
                "rankup": tier_after > tier_before,
                "rr_before": int(_number_or_zero(item.get("RankedRatingBeforeUpdate"))),
                "rr_after": int(_number_or_zero(item.get("RankedRatingAfterUpdate")))
            }

    return {
        "rr_change": 0,
        "rank_before": "",
        "rank_after": "",
        "rankup": False,
        "rr_before": None,
        "rr_after": None
    }


async def fetch_rr_change(
    client: httpx.AsyncClient,
    local_url: str,
    pd_url: str,
    puuid: str,
    match_id: str,
    local_headers: dict,
    remote_headers: dict
) -> int:
    """
    Fetches the RR delta for the completed match.

    @param client: HTTP client.
    @param local_url: Local Riot client base URL.
    @param pd_url: Riot PD base URL.
    @param puuid: Local player's PUUID.
    @param match_id: Completed match id.
    @param local_headers: Local auth headers.
    @param remote_headers: Riot PD auth headers.
    @return: Ranked rating delta, or zero when unavailable/non-ranked.
    """
    local_resp = await client.get(f"{local_url}/mmr/v1/user/{puuid}", headers=local_headers)
    if local_resp.status_code == 200:
        return extract_rr_change(local_resp.json(), match_id)

    updates_resp = await client.get(
        f"{pd_url}/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=10",
        headers=remote_headers
    )
    if updates_resp.status_code == 200:
        return extract_rr_change(updates_resp.json(), match_id)

    player_mmr_resp = await client.get(f"{pd_url}/mmr/v1/players/{puuid}", headers=remote_headers)
    if player_mmr_resp.status_code == 200:
        return extract_rr_change(player_mmr_resp.json(), match_id)

    logger.debug("RR lookup failed: local=%s updates=%s", local_resp.status_code, updates_resp.status_code)
    return 0


async def fetch_mmr_update(
    client: httpx.AsyncClient,
    local_url: str,
    pd_url: str,
    puuid: str,
    match_id: str,
    local_headers: dict,
    remote_headers: dict
) -> dict:
    """
    Fetches RR and rank movement for the completed match.

    @param client: HTTP client.
    @param local_url: Local Riot client base URL.
    @param pd_url: Riot PD base URL.
    @param puuid: Local player's PUUID.
    @param match_id: Completed match id.
    @param local_headers: Local auth headers.
    @param remote_headers: Riot PD auth headers.
    @return: Match MMR update dictionary.
    """
    local_resp = await client.get(f"{local_url}/mmr/v1/user/{puuid}", headers=local_headers)
    if local_resp.status_code == 200:
        return extract_mmr_update(local_resp.json(), match_id)

    updates_resp = await client.get(
        f"{pd_url}/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=10",
        headers=remote_headers
    )
    if updates_resp.status_code == 200:
        return extract_mmr_update(updates_resp.json(), match_id)

    player_mmr_resp = await client.get(f"{pd_url}/mmr/v1/players/{puuid}", headers=remote_headers)
    if player_mmr_resp.status_code == 200:
        return extract_mmr_update(player_mmr_resp.json(), match_id)

    logger.debug("MMR update lookup failed: local=%s updates=%s", local_resp.status_code, updates_resp.status_code)
    return extract_mmr_update({}, match_id)


async def get_riot_remote_context(client: httpx.AsyncClient, local_url: str, local_headers: dict) -> dict | None:
    """
    Builds Riot PD/GLZ authentication context from the local client.

    @param client: HTTP client.
    @param local_url: Local Riot client base URL.
    @param local_headers: Local auth headers.
    @return: Context dictionary or None when auth fails.
    """
    session_resp = await client.get(f"{local_url}/chat/v1/session", headers=local_headers)
    if session_resp.status_code != 200:
        return None

    session_data = session_resp.json()
    puuid = session_data.get("puuid", "")
    if not puuid:
        return None
    token_resp = await client.get(f"{local_url}/entitlements/v1/token", headers=local_headers)
    if token_resp.status_code != 200:
        return None

    token_data = token_resp.json()
    access_token = token_data.get("accessToken")
    entitlements_token = token_data.get("token")
    client_version = get_local_client_version()
    pres_resp = await client.get(f"{local_url}/chat/v4/presences", headers=local_headers)
    if pres_resp.status_code == 200:
        for pres in pres_resp.json().get("presences", []):
            if pres.get("puuid") == puuid and pres.get("private"):
                try:
                    decoded = base64.b64decode(pres["private"]).decode("utf-8")
                    priv_data = json.loads(decoded)
                    p_ver = priv_data.get("partyPresenceData", {}).get("partyClientVersion")
                    if p_ver:
                        client_version = p_ver
                        break
                except Exception:
                    pass

    remote_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": entitlements_token,
        "X-Riot-ClientVersion": client_version,
        "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIndpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogInVua25vd24iDQp9",
        "Accept": "application/json"
    }
    l_region = session_data.get("region", "eu1")
    glz_region, shard = get_region_shard(l_region)
    game_name = session_data.get("game_name", "")
    game_tag = session_data.get("game_tag", "")
    return {
        "session": session_data,
        "puuid": puuid,
        "player_name": f"{game_name}#{game_tag}",
        "remote_headers": remote_headers,
        "pd_url": f"https://pd.{shard}.a.pvp.net",
        "glz_url": f"https://glz-{glz_region}-1.{shard}.a.pvp.net",
        "shard": shard
    }


def format_riot_player_name(game_name: str | None, tag_line: str | None) -> str:
    """
    Formats Riot player name fields into a display name.

    @param game_name: Riot GameName field.
    @param tag_line: Riot TagLine field.
    @return: Display name, or empty string when unavailable.
    """
    clean_name = (game_name or "").strip()
    clean_tag = (tag_line or "").strip()
    if clean_name and clean_tag:
        return f"{clean_name}#{clean_tag}"
    return clean_name


def match_player_display_name(player: dict) -> str:
    """
    Extracts a display name from a match-details player payload.

    @param player: Player payload from PD match-details.
    @return: Display name, or empty string when unavailable.
    """
    return format_riot_player_name(
        player.get("gameName") or player.get("GameName"),
        player.get("tagLine") or player.get("TagLine")
    )


async def fetch_name_service_map(
    client: httpx.AsyncClient,
    pd_url: str,
    remote_headers: dict,
    puuids: list[str]
) -> dict:
    """
    Resolves PUUIDs to Riot display names through PD name-service.

    @param client: HTTP client.
    @param pd_url: Riot PD base URL.
    @param remote_headers: Riot auth headers.
    @param puuids: Player PUUIDs to resolve.
    @return: Mapping of PUUID to display name.
    """
    unique_puuids = list(dict.fromkeys([p for p in puuids if p]))
    if not unique_puuids:
        return {}

    cached_names = {p: player_name_cache[p] for p in unique_puuids if p in player_name_cache}
    unresolved_puuids = [p for p in unique_puuids if p not in cached_names]
    if not unresolved_puuids:
        return cached_names

    names_resp = await client.put(
        f"{pd_url}/name-service/v2/players",
        headers=remote_headers,
        json=unresolved_puuids
    )
    if names_resp.status_code != 200:
        logger.debug("Riot name-service lookup failed: status=%s", names_resp.status_code)
        return cached_names

    names_map = {}
    for name_item in names_resp.json():
        p_id = name_item.get("Subject") or name_item.get("subject")
        display_name = format_riot_player_name(
            name_item.get("GameName") or name_item.get("gameName"),
            name_item.get("TagLine") or name_item.get("tagLine")
        )
        if p_id and display_name:
            names_map[p_id] = display_name
    player_name_cache.update(names_map)
    return {**cached_names, **names_map}


async def resolve_current_riot_player_names(puuids: list[str]) -> dict:
    """
    Resolves player names with the currently running local Riot client.

    @param puuids: Player PUUIDs to resolve.
    @return: Mapping of PUUID to display name.
    """
    if not puuids:
        return {}

    try:
        from lockfile_scanner import LockfileScanner
        scanner = LockfileScanner()
        lockfile_info = scanner.scan()
        if not lockfile_info:
            return {}

        local_url = f"{lockfile_info['protocol']}://127.0.0.1:{lockfile_info['port']}"
        local_headers = lockfile_info["headers"]
        async with httpx.AsyncClient(verify=False, timeout=8.0) as client:
            context = await get_riot_remote_context(client, local_url, local_headers)
            if not context:
                return {}
            return await fetch_name_service_map(
                client,
                context["pd_url"],
                context["remote_headers"],
                puuids
            )
    except Exception:
        logger.exception("Riot name-service lookup failed")
        return {}


def format_duration_from_millis(duration_ms) -> str:
    """
    Formats a millisecond duration as Xm Ys.
    """
    total_seconds = int(_number_or_zero(duration_ms) / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"


def build_round_player_metrics(round_results: list, player_puuids: list[str], player_teams: dict = None) -> dict:
    """
    Builds per-player metrics derived from round results.
    """
    metrics = {
        puuid: {
            "damage_dealt": 0,
            "damage_received": 0,
            "first_kills": 0,
            "first_deaths": 0,
            "multi_kills": 0,
            "kast_rounds": 0,
            "loadout_total": 0,
            "bank_total": 0,
            "spent_total": 0
        }
        for puuid in player_puuids
    }

    for round_result in round_results:
        deaths = set()
        assists_by_player = {puuid: 0 for puuid in player_puuids}
        kills_by_player = {puuid: 0 for puuid in player_puuids}
        first_kill = None
        player_stats_list = round_result.get("playerStats") or round_result.get("PlayerStats") or []

        round_kills = []
        for player_stats in player_stats_list:
            p_id = player_stats.get("subject") or player_stats.get("Subject")
            if not p_id:
                continue

            economy = player_stats.get("economy") or player_stats.get("Economy") or {}
            if p_id in metrics:
                metrics[p_id]["loadout_total"] += int(_number_or_zero(economy.get("loadoutValue")))
                metrics[p_id]["bank_total"] += int(_number_or_zero(economy.get("remaining")))
                metrics[p_id]["spent_total"] += int(_number_or_zero(economy.get("spent")))

            for damage in player_stats.get("damage", []) or player_stats.get("Damage", []) or []:
                damage_amount = int(_number_or_zero(damage.get("damage") or damage.get("Damage")))
                receiver = damage.get("receiver") or damage.get("Receiver")
                if p_id in metrics:
                    metrics[p_id]["damage_dealt"] += damage_amount
                if receiver in metrics:
                    metrics[receiver]["damage_received"] += damage_amount

            for kill in player_stats.get("kills", []) or player_stats.get("Kills", []) or []:
                killer = kill.get("killer") or kill.get("Killer") or p_id
                victim = kill.get("victim") or kill.get("Victim")
                round_time = int(_number_or_zero(kill.get("roundTime") or kill.get("RoundTime")))
                if killer in kills_by_player:
                    kills_by_player[killer] += 1
                if victim:
                    deaths.add(victim)
                for assistant in kill.get("assistants", []) or kill.get("Assistants", []) or []:
                    if assistant in assists_by_player:
                        assists_by_player[assistant] += 1
                if not first_kill or round_time < first_kill["round_time"]:
                    first_kill = {"killer": killer, "victim": victim, "round_time": round_time}
                if killer and victim:
                    round_kills.append({
                        "killer": killer,
                        "victim": victim,
                        "time": round_time
                    })

        if first_kill:
            if first_kill["killer"] in metrics:
                metrics[first_kill["killer"]]["first_kills"] += 1
            if first_kill["victim"] in metrics:
                metrics[first_kill["victim"]]["first_deaths"] += 1

        traded_players = set()
        if player_teams:
            round_kills.sort(key=lambda x: x["time"])
            for idx_k, rk in enumerate(round_kills):
                v = rk["victim"]
                k = rk["killer"]
                t = rk["time"]
                v_team = player_teams.get(v)
                if not v_team:
                    continue
                # Look ahead for a trade within 4 seconds
                for sub_rk in round_kills[idx_k + 1:]:
                    if sub_rk["time"] - t > 4000:
                        break
                    if sub_rk["victim"] == k:
                        sub_killer = sub_rk["killer"]
                        if player_teams.get(sub_killer) == v_team and sub_killer != v:
                            traded_players.add(v)
                            break

        for puuid in player_puuids:
            kill_count = kills_by_player.get(puuid, 0)
            if kill_count >= 2 and puuid in metrics:
                metrics[puuid]["multi_kills"] += 1
            
            is_kast = (
                kill_count > 0 or
                assists_by_player.get(puuid, 0) > 0 or
                puuid not in deaths or
                puuid in traded_players
            )
            if puuid in metrics and is_kast:
                metrics[puuid]["kast_rounds"] += 1

    return metrics


def build_match_tabs_data(round_results: list, players: list, player_lookup: dict, ally_team_id: str) -> dict:
    """
    Builds round, economy and duel payloads for the match details tabs.
    """
    rounds = []
    duels = {}
    ally_ids = [p["puuid"] for p in players if p.get("team_id") == ally_team_id]
    enemy_ids = [p["puuid"] for p in players if p.get("team_id") != ally_team_id]

    for ally_id in ally_ids:
        duels[ally_id] = {
            enemy_id: {"kills": 0, "deaths": 0}
            for enemy_id in enemy_ids
        }

    for round_result in round_results:
        round_num = int(_number_or_zero(round_result.get("roundNum") or round_result.get("RoundNum"))) + 1
        winning_team = round_result.get("winningTeam") or round_result.get("WinningTeam") or ""
        result_code = round_result.get("roundResultCode") or round_result.get("roundResult") or "Round"
        player_stats_list = round_result.get("playerStats") or round_result.get("PlayerStats") or []
        player_economies = round_result.get("playerEconomies") or round_result.get("PlayerEconomies") or []
        kills = []
        deaths = set()
        first_kill = None

        for player_stats in player_stats_list:
            p_id = player_stats.get("subject") or player_stats.get("Subject")
            for kill in player_stats.get("kills", []) or player_stats.get("Kills", []) or []:
                killer = kill.get("killer") or kill.get("Killer") or p_id
                victim = kill.get("victim") or kill.get("Victim")
                round_time = int(_number_or_zero(kill.get("roundTime") or kill.get("RoundTime")))
                if victim:
                    deaths.add(victim)
                kills.append({
                    "killer": killer,
                    "victim": victim,
                    "round_time": round_time
                })
                if killer in ally_ids and victim in enemy_ids:
                    duels[killer][victim]["kills"] += 1
                elif killer in enemy_ids and victim in ally_ids:
                    duels[victim][killer]["deaths"] += 1
                if not first_kill or round_time < first_kill["round_time"]:
                    first_kill = {"killer": killer, "victim": victim, "round_time": round_time}

        ally_loadout = 0
        enemy_loadout = 0
        ally_bank = 0
        enemy_bank = 0
        for economy in player_economies:
            p_id = economy.get("subject") or economy.get("Subject")
            loadout = int(_number_or_zero(economy.get("loadoutValue")))
            bank = int(_number_or_zero(economy.get("remaining")))
            if p_id in ally_ids:
                ally_loadout += loadout
                ally_bank += bank
            elif p_id in enemy_ids:
                enemy_loadout += loadout
                enemy_bank += bank

        rounds.append({
            "round": round_num,
            "winning_team": winning_team,
            "ally_won": winning_team == ally_team_id,
            "result": result_code,
            "ally_kills": sum(1 for p_id in deaths if p_id in enemy_ids),
            "enemy_kills": sum(1 for p_id in deaths if p_id in ally_ids),
            "ally_loadout": ally_loadout,
            "enemy_loadout": enemy_loadout,
            "ally_bank": ally_bank,
            "enemy_bank": enemy_bank,
            "first_kill": first_kill,
            "events": kills[:8]
        })

    return {
        "rounds": rounds,
        "duels": duels,
        "ally_ids": ally_ids,
        "enemy_ids": enemy_ids
    }


def refresh_session_summary() -> None:
    """
    Updates the in-memory session widget state from SQLite.
    """
    puuid = tracker_state.get("puuid", "")
    if not puuid:
        tracker_state["session_summary"] = {"wins": 0, "losses": 0, "rr_delta": 0}
        return
    tracker_state["session_summary"] = db_manager.get_session_summary(SESSION_STARTED_AT, puuid)


def persist_completed_match(summary: dict, puuid: str, player_name: str) -> bool:
    """
    Saves a completed match once and refreshes the session summary.

    @param summary: Completed match summary with RR delta included.
    @return: True when inserted, False when already persisted or invalid.
    """
    match_id = summary.get("match_id")
    persist_key = (puuid, match_id)
    if not puuid or not match_id or persist_key in persisted_match_ids:
        refresh_session_summary()
        return False

    match_data = {
        "puuid": puuid,
        "player_name": player_name,
        "match_id": match_id,
        "date": summary.get("date") or datetime.now(timezone.utc).isoformat(),
        "gamemode": summary.get("queue_id", ""),
        "map": summary.get("map_id", ""),
        "season_id": summary.get("season_id", ""),
        "agent": summary.get("agent", ""),
        "win_loss": "WIN" if summary.get("won") else "LOSS",
        "rr_change": summary.get("rr_change", 0),
        "acs": summary.get("acs", 0),
        "kd": summary.get("kd", 0),
        "hs_percent": summary.get("hs_percent", 0),
        "kills": summary.get("kills", 0),
        "deaths": summary.get("deaths", 0),
        "assists": summary.get("assists", 0),
        "score": summary.get("score", 0),
        "kda": summary.get("kda", 0),
        "rank_before": summary.get("rank_before", ""),
        "rank_after": summary.get("rank_after", ""),
        "rankup": summary.get("rankup", False),
        "rr_before": summary.get("rr_before"),
        "rr_after": summary.get("rr_after")
    }
    inserted = db_manager.save_match(match_data)
    persisted_match_ids.add(persist_key)
    refresh_session_summary()
    if inserted:
        logger.info(
            "Saved match: match_id=%s result=%s rr_change=%s",
            match_id,
            match_data["win_loss"],
            match_data["rr_change"],
        )
    return inserted


async def background_scan_loop() -> None:
    """
    Background loop that polls the lockfile and local LCU API to retrieve game status.
    """
    from lockfile_scanner import LockfileScanner
    scanner = LockfileScanner()
    
    while True:
        try:
            lockfile_info = scanner.scan()
            if not lockfile_info:
                tracker_state["status"] = "offline"
                tracker_state["game_phase"] = "OFFLINE"
                tracker_state["player_name"] = "Unknown"
                tracker_state["puuid"] = ""
                tracker_state["queue_id"] = ""
                tracker_state["map_id"] = ""
                tracker_state["allies"] = []
                tracker_state["enemies"] = []
                refresh_session_summary()
                refresh_stats_cache_context()
                await asyncio.sleep(3)
                continue
                
            port = lockfile_info["port"]
            protocol = lockfile_info["protocol"]
            headers = lockfile_info["headers"]
            url = f"{protocol}://127.0.0.1:{port}"
            
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                try:
                    session_resp = await client.get(f"{url}/chat/v1/session", headers=headers)
                    if session_resp.status_code != 200:
                        tracker_state["status"] = "searching_game"
                        tracker_state["game_phase"] = "OFFLINE"
                        tracker_state["player_name"] = "Unknown"
                        tracker_state["puuid"] = ""
                        tracker_state["allies"] = []
                        tracker_state["enemies"] = []
                        refresh_session_summary()
                        refresh_stats_cache_context()
                        await asyncio.sleep(3)
                        continue
                        
                    session_data = session_resp.json()
                    puuid = session_data.get("puuid")
                    game_name = session_data.get("game_name", "")
                    game_tag = session_data.get("game_tag", "")
                    
                    previous_puuid = tracker_state.get("puuid", "")
                    tracker_state["puuid"] = puuid
                    tracker_state["player_name"] = f"{game_name}#{game_tag}"
                    tracker_state["status"] = "connected"
                    if previous_puuid != puuid:
                        refresh_session_summary()
                except (httpx.ConnectError, httpx.TimeoutException):
                    tracker_state["status"] = "searching_game"
                    tracker_state["game_phase"] = "OFFLINE"
                    tracker_state["player_name"] = "Unknown"
                    tracker_state["puuid"] = ""
                    tracker_state["allies"] = []
                    tracker_state["enemies"] = []
                    refresh_session_summary()
                    refresh_stats_cache_context()
                    await asyncio.sleep(3)
                    continue
                
                try:
                    presence_resp = await client.get(f"{url}/chat/v4/presences", headers=headers)
                    if presence_resp.status_code == 200:
                        presences_data = presence_resp.json()
                        presences_list = presences_data.get("presences", [])
                        my_presence = None
                        
                        for p in presences_list:
                            if p.get("puuid") == puuid:
                                my_presence = p
                                break
                                
                        if my_presence and my_presence.get("private"):
                            private_b64 = my_presence.get("private")
                            decoded_bytes = base64.b64decode(private_b64)
                            decoded_str = decoded_bytes.decode("utf-8")
                            private_data = json.loads(decoded_str)
                            match_presence = private_data.get("matchPresenceData", {})
                            session_state = match_presence.get("sessionLoopState", "MENUS")
                            
                            if session_state == "INGAME":
                                session_state = "CORE-GAME"
                            
                            tracker_state["game_phase"] = session_state
                            tracker_state["queue_id"] = match_presence.get("queueId", private_data.get("queueId", ""))
                            tracker_state["map_id"] = match_presence.get("matchMap", "")
                        else:
                            tracker_state["game_phase"] = "MENUS"
                    else:
                        tracker_state["game_phase"] = "MENUS"
                except Exception:
                    tracker_state["game_phase"] = "MENUS"
                
                refresh_stats_cache_context()
                
                remote_headers = None
                glz_url = ""
                shard = ""
                current_match_id = tracker_state.get("current_match_id", "")
                last_match = tracker_state.get("last_match") or {}
                needs_post_match_fetch = (
                    tracker_state["status"] == "connected"
                    and tracker_state["game_phase"] not in ("PREGAME", "CORE-GAME")
                    and current_match_id
                    and tracker_state.get("core_match_id") == current_match_id
                    and last_match.get("match_id") != current_match_id
                )
                if tracker_state["game_phase"] in ("PREGAME", "CORE-GAME") or needs_post_match_fetch:
                    try:
                        token_resp = await client.get(f"{url}/entitlements/v1/token", headers=headers)
                        if token_resp.status_code == 200:
                            token_data = token_resp.json()
                            access_token = token_data.get("accessToken")
                            entitlements_token = token_data.get("token")
                            
                            client_version = get_local_client_version()
                            pres_resp = await client.get(f"{url}/chat/v4/presences", headers=headers)
                            if pres_resp.status_code == 200:
                                for pres in pres_resp.json().get("presences", []):
                                    if pres.get("puuid") == puuid and pres.get("private"):
                                        try:
                                            decoded = base64.b64decode(pres["private"]).decode("utf-8")
                                            priv_data = json.loads(decoded)
                                            p_ver = priv_data.get("partyPresenceData", {}).get("partyClientVersion")
                                            if p_ver:
                                                client_version = p_ver
                                                break
                                        except Exception:
                                            pass
                            
                            remote_headers = {
                                "Authorization": f"Bearer {access_token}",
                                "X-Riot-Entitlements-JWT": entitlements_token,
                                "X-Riot-ClientVersion": client_version,
                                "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIndpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogInVua25vd24iDQp9",
                                "Accept": "application/json"
                            }
                            
                            l_region = session_data.get("region", "eu1")
                            glz_region, shard = get_region_shard(l_region)
                            glz_url = f"https://glz-{glz_region}-1.{shard}.a.pvp.net"
                    except Exception:
                        logger.exception("Failed to acquire Riot GLZ tokens")
                
                if tracker_state["game_phase"] == "PREGAME" and remote_headers:
                    try:
                        pregame_player_resp = await client.get(f"{glz_url}/pregame/v1/players/{puuid}", headers=remote_headers)
                        if pregame_player_resp.status_code == 200:
                            match_id = pregame_player_resp.json().get("MatchID")
                            start_tracking_match(match_id)
                            pregame_match_resp = await client.get(f"{glz_url}/pregame/v1/matches/{match_id}", headers=remote_headers)
                            if pregame_match_resp.status_code == 200:
                                pregame_match_data = pregame_match_resp.json()
                                alliance_team = pregame_match_data.get("Teams", [])
                                players_list = []
                                if alliance_team:
                                    players_list = alliance_team[0].get("Players", [])
                                    
                                puuids = [p.get("Subject") for p in players_list if p.get("Subject")]
                                pd_url = f"https://pd.{shard}.a.pvp.net"
                                names_resp = await client.put(f"{pd_url}/name-service/v2/players", headers=remote_headers, json=puuids)
                                names_map = {}
                                if names_resp.status_code == 200:
                                    for name_item in names_resp.json():
                                        p_id = name_item.get("Subject")
                                        g_name = name_item.get("GameName", "")
                                        g_tag = name_item.get("TagLine", "")
                                        names_map[p_id] = f"{g_name}#{g_tag}"
                                        
                                from api_client import HenrikDevClient
                                api_client = HenrikDevClient(api_key=get_henrik_api_key())
                                
                                all_players_data = []
                                for p in players_list:
                                    p_puuid = p.get("Subject")
                                    p_agent_id = p.get("CharacterID", "")
                                    p_agent_name = AGENT_MAPPING.get(p_agent_id, "Unknown Agent")
                                    p_name = names_map.get(p_puuid, "Unknown Player")
                                    
                                    cache_key = f"{p_puuid}_{tracker_state['queue_id']}"
                                    if cache_key in stats_cache:
                                        p_stats = stats_cache[cache_key]
                                        if p_stats.get("_deferred"):
                                            p_stats = await api_client.get_player_stats(p_puuid, tracker_state["queue_id"])
                                            stats_cache[cache_key] = p_stats
                                    else:
                                        p_stats = await api_client.get_player_stats(p_puuid, tracker_state["queue_id"])
                                        stats_cache[cache_key] = p_stats
                                        
                                    all_players_data.append({
                                        "puuid": p_puuid,
                                        "name": p_name,
                                        "agent_id": p_agent_id,
                                        "agent": p_agent_name,
                                        "rank": p_stats.get("rank", "Unknown"),
                                        "peak_rank": p_stats.get("peak_rank", "Unknown"),
                                        "kd": p_stats.get("kd", 1.0),
                                        "hs_percent": p_stats.get("hs_percent", 20.0),
                                        "acs": p_stats.get("acs", 200),
                                        "match_ids": p_stats.get("match_ids", []),
                                        "badge": p_stats.get("badge", "")
                                    })
                                    
                                group_map = find_premade_groups(all_players_data)
                                new_allies = []
                                for player in all_players_data:
                                    score = calculate_tracker_score(
                                        player["kd"],
                                        player["hs_percent"],
                                        player["acs"],
                                        player["rank"],
                                        player["peak_rank"]
                                    )
                                    badge = player["badge"]
                                    p_grp = group_map.get(player["puuid"])
                                    if p_grp:
                                        badge = f"Duo" if list(group_map.values()).count(p_grp) == 2 else "Trio"
                                        
                                    player_info = {
                                        "puuid": player["puuid"],
                                        "name": player["name"],
                                        "agent_id": player.get("agent_id", ""),
                                        "agent": player["agent"],
                                        "rank": player["rank"],
                                        "peak_rank": player["peak_rank"],
                                        "kd": player["kd"],
                                        "hs_percent": player["hs_percent"],
                                        "acs": player["acs"],
                                        "badge": badge,
                                        "score": score,
                                        "group_id": p_grp
                                    }
                                    new_allies.append(enrich_player_assets(player_info))
                                tracker_state["allies"] = new_allies
                                tracker_state["enemies"] = []
                    except Exception:
                        logger.exception("Pregame polling failed")
                        
                elif tracker_state["game_phase"] == "CORE-GAME" and remote_headers:
                    try:
                        core_player_resp = await client.get(f"{glz_url}/core-game/v1/players/{puuid}", headers=remote_headers)
                        if core_player_resp.status_code == 200:
                            match_id = core_player_resp.json().get("MatchID")
                            start_tracking_match(match_id)
                            tracker_state["core_match_id"] = match_id
                            core_match_resp = await client.get(f"{glz_url}/core-game/v1/matches/{match_id}", headers=remote_headers)
                            if core_match_resp.status_code == 200:
                                core_match_data = core_match_resp.json()
                                players_list = core_match_data.get("Players", [])
                                
                                ally_team_id = None
                                for p in players_list:
                                    if p.get("Subject") == puuid:
                                        ally_team_id = p.get("TeamID")
                                        break
                                        
                                puuids = [p.get("Subject") for p in players_list if p.get("Subject")]
                                pd_url = f"https://pd.{shard}.a.pvp.net"
                                names_resp = await client.put(f"{pd_url}/name-service/v2/players", headers=remote_headers, json=puuids)
                                names_map = {}
                                if names_resp.status_code == 200:
                                    for name_item in names_resp.json():
                                        p_id = name_item.get("Subject")
                                        g_name = name_item.get("GameName", "")
                                        g_tag = name_item.get("TagLine", "")
                                        names_map[p_id] = f"{g_name}#{g_tag}"
                                        
                                from api_client import HenrikDevClient
                                api_client = HenrikDevClient(api_key=get_henrik_api_key())
                                
                                all_players_data = []
                                for p in players_list:
                                    p_puuid = p.get("Subject")
                                    p_agent_id = p.get("CharacterID", "")
                                    p_agent_name = AGENT_MAPPING.get(p_agent_id, "Unknown Agent")
                                    p_name = names_map.get(p_puuid, "Unknown Player")
                                    p_team = p.get("TeamID")
                                    
                                    cache_key = f"{p_puuid}_{tracker_state['queue_id']}"
                                    if cache_key in stats_cache:
                                        p_stats = stats_cache[cache_key]
                                        if p_stats.get("_deferred"):
                                            p_stats = await api_client.get_player_stats(p_puuid, tracker_state["queue_id"])
                                            stats_cache[cache_key] = p_stats
                                    else:
                                        p_stats = await api_client.get_player_stats(p_puuid, tracker_state["queue_id"])
                                        stats_cache[cache_key] = p_stats
                                        
                                    all_players_data.append({
                                        "puuid": p_puuid,
                                        "name": p_name,
                                        "agent_id": p_agent_id,
                                        "agent": p_agent_name,
                                        "team": p_team,
                                        "rank": p_stats.get("rank", "Unknown"),
                                        "peak_rank": p_stats.get("peak_rank", "Unknown"),
                                        "kd": p_stats.get("kd", 1.0),
                                        "hs_percent": p_stats.get("hs_percent", 20.0),
                                        "acs": p_stats.get("acs", 200),
                                        "match_ids": p_stats.get("match_ids", []),
                                        "badge": p_stats.get("badge", "")
                                    })
                                    
                                group_map = find_premade_groups(all_players_data)
                                new_allies = []
                                new_enemies = []
                                for player in all_players_data:
                                    score = calculate_tracker_score(
                                        player["kd"],
                                        player["hs_percent"],
                                        player["acs"],
                                        player["rank"],
                                        player["peak_rank"]
                                    )
                                    badge = player["badge"]
                                    p_grp = group_map.get(player["puuid"])
                                    if p_grp:
                                        badge = f"Duo" if list(group_map.values()).count(p_grp) == 2 else "Trio"
                                        
                                    player_info = {
                                        "puuid": player["puuid"],
                                        "name": player["name"],
                                        "agent_id": player.get("agent_id", ""),
                                        "agent": player["agent"],
                                        "rank": player["rank"],
                                        "peak_rank": player["peak_rank"],
                                        "kd": player["kd"],
                                        "hs_percent": player["hs_percent"],
                                        "acs": player["acs"],
                                        "badge": badge,
                                        "score": score,
                                        "group_id": p_grp
                                    }
                                    enrich_player_assets(player_info)
                                    
                                    if player["team"] == ally_team_id:
                                        new_allies.append(player_info)
                                    else:
                                        new_enemies.append(player_info)
                                        
                                tracker_state["allies"] = new_allies
                                tracker_state["enemies"] = new_enemies
                    except Exception:
                        logger.exception("Core-game polling failed")
                elif needs_post_match_fetch and remote_headers:
                    try:
                        pd_url = f"https://pd.{shard}.a.pvp.net"
                        summary = await fetch_post_match_summary(
                            client,
                            pd_url,
                            tracker_state["current_match_id"],
                            puuid,
                            remote_headers
                        )
                        tracker_state["allies"] = []
                        tracker_state["enemies"] = []
                        if summary:
                            summary.update(await fetch_mmr_update(
                                client,
                                url,
                                pd_url,
                                puuid,
                                tracker_state["current_match_id"],
                                headers,
                                remote_headers
                            ))
                            # Calculate tracker score for post-match summary
                            peak_rank = tracker_state.get("peak_rank", "")
                            if not peak_rank:
                                peak_rank = summary.get("rank_after", "") or summary.get("rank_before", "")
                            summary["tracker_score"] = calculate_tracker_score(
                                kd=summary.get("kd", 0.0),
                                hs_percent=summary.get("hs_percent", 0.0),
                                acs=summary.get("acs", 0),
                                rank=summary.get("rank_after", "") or summary.get("rank_before", ""),
                                peak_rank=peak_rank,
                                kills=summary.get("kills"),
                                deaths=summary.get("deaths"),
                                assists=summary.get("assists"),
                                rounds_played=summary.get("rounds_played")
                            )
                            enrich_match_assets(summary)
                            tracker_state["last_match"] = summary
                            tracker_state["last_match_status"] = "available"
                            persist_completed_match(summary, puuid, tracker_state.get("player_name", "Unknown"))
                        else:
                            tracker_state["last_match_status"] = "loading"
                    except Exception:
                        tracker_state["last_match_status"] = "loading"
                        logger.exception("Post-match fetch failed")
                else:
                    tracker_state["allies"] = []
                    tracker_state["enemies"] = []
                    
        except Exception:
            logger.exception("Background scan loop iteration failed")
            tracker_state["status"] = "offline"
            tracker_state["game_phase"] = "OFFLINE"
            tracker_state["player_name"] = "Unknown"
            tracker_state["puuid"] = ""
            tracker_state["allies"] = []
            tracker_state["enemies"] = []
            refresh_session_summary()
            refresh_stats_cache_context()
            
        await asyncio.sleep(3)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Fires on startup to initialize the background scanning task.
    """
    settings = settings_manager.load()
    configure_logging(debug=bool(settings.get("app", {}).get("debug")))
    try:
        sync_startup_settings(settings)
    except Exception as exc:
        logger.warning("Unable to sync Windows startup settings on startup: %s", exc)
    db_manager.init_db()
    logger.info("Application startup complete. logs_dir=%s data_dir=%s", logs_dir(), user_data_dir())
    refresh_session_summary()
    asyncio.create_task(backfill_missing_match_seasons())
    asyncio.create_task(background_scan_loop())


@app.get("/")
async def read_root(request: Request):
    """
    Serves the main dashboard page.

    @param request: The incoming HTTP request.
    @return: The rendered HTML template.
    """
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/session-status")
async def get_session_status() -> dict:
    """
    Retrieves the current game connection status.

    @return: A JSON response containing the status payload.
    """
    return tracker_state


@app.get("/api/updater/check")
async def check_update() -> dict:
    """
    Checks GitHub for the latest version.
    """
    return await app_updater.check_latest_release()


@app.post("/api/updater/download")
async def start_download(payload: dict) -> dict:
    """
    Starts download of the updater installer in the background.
    """
    url = payload.get("download_url")
    if not url:
        return {"error": "Missing download_url"}
    
    # Start download task
    app_updater.download_task = asyncio.create_task(app_updater.download_installer(url))
    return {"status": "download_started"}


@app.get("/api/updater/progress")
async def get_progress() -> dict:
    """
    Returns the current download progress percentage.
    """
    return {
        "progress": app_updater.download_progress,
        "completed": app_updater.download_task is not None and app_updater.download_task.done()
    }


@app.post("/api/updater/install")
async def trigger_install() -> dict:
    """
    Launches the installer and shuts down the app.
    """
    loop = asyncio.get_event_loop()
    loop.call_later(0.5, app_updater.run_installer_and_exit)
    return {"status": "closing_for_installation"}


@app.get("/api/settings")
async def get_settings() -> dict:
    """
    Returns non-sensitive local application settings.
    """
    return settings_manager.load()


@app.patch("/api/settings")
async def update_settings(payload: dict) -> dict:
    """
    Applies a partial update to non-sensitive local application settings.
    """
    settings = settings_manager.update(payload)
    if isinstance(payload, dict) and "startup" in payload:
        try:
            settings["startup_status"] = sync_startup_settings(settings)
        except Exception as exc:
            logger.warning("Unable to sync Windows startup settings: %s", exc)
            settings["startup_status"] = {
                "supported": os.name == "nt",
                "error": str(exc),
            }
    return settings


@app.post("/api/settings/first-launch-completed")
async def complete_first_launch() -> dict:
    """
    Marks the first-launch flow as completed.
    """
    return settings_manager.mark_first_launch_completed()


def open_local_folder(path) -> dict:
    """
    Opens a local folder in Windows Explorer.
    """
    target = str(path)
    try:
        if os.name == "nt":
            os.startfile(target)
        else:
            return {
                "status": "error",
                "message": "Opening folders is only supported on Windows in V1."
            }
    except OSError as exc:
        return {
            "status": "error",
            "message": f"Unable to open folder: {exc}"
        }
    return {
        "status": "ok",
        "path": target
    }


@app.post("/api/settings/open-data-folder")
async def open_data_folder() -> dict:
    """
    Opens the local application data folder.
    """
    ensure_runtime_dirs()
    return open_local_folder(user_data_dir())


@app.post("/api/settings/open-logs-folder")
async def open_logs_folder() -> dict:
    """
    Opens the local application logs folder.
    """
    ensure_runtime_dirs()
    return open_local_folder(logs_dir())


@app.post("/api/settings/reload-cache")
async def reload_cache() -> dict:
    """
    Reloads in-memory assets and clears volatile player stats cache.
    """
    asset_manager.reload()
    clear_stats_cache("manual settings reload")
    settings = settings_manager.update({
        "cache": {
            "last_assets_reload_at": datetime.now(timezone.utc).isoformat()
        }
    })
    return {
        "status": "ok",
        "cache_dir": str(cache_dir()),
        "last_assets_reload_at": settings["cache"]["last_assets_reload_at"]
    }


@app.get("/api/config/status")
async def get_config_status() -> dict:
    """
    Returns non-sensitive local configuration status.
    """
    secret_status = henrik_secret_manager.storage_status()
    return {
        "henrik_api": secret_status,
        "settings_path": str(settings_manager.path),
        "startup": startup_status(),
    }


@app.post("/api/config/henrik-key/verify")
async def verify_henrik_key(payload: dict) -> dict:
    """
    Verifies a HenrikDev key without saving it.
    """
    return await verify_henrik_api_key(payload.get("api_key", ""))


@app.post("/api/config/henrik-key")
async def save_henrik_key(payload: dict) -> dict:
    """
    Verifies and securely saves a HenrikDev key.
    """
    api_key = normalize_henrik_api_key(payload.get("api_key", ""))
    verification = await verify_henrik_api_key(api_key)
    if not verification.get("valid"):
        return verification

    try:
        henrik_secret_manager.set_key(api_key)
    except Exception as exc:
        return {
            "status": "error",
            "valid": True,
            "saved": False,
            "reason": "storage_failed",
            "message": f"Unable to save HenrikDev API key: {exc}"
        }

    return {
        "status": "ok",
        "valid": True,
        "saved": True,
        "henrik_api": henrik_secret_manager.storage_status(),
    }


@app.delete("/api/config/henrik-key")
async def delete_henrik_key() -> dict:
    """
    Deletes the locally stored HenrikDev key.
    """
    henrik_secret_manager.delete_key()
    return {
        "status": "ok",
        "deleted": True,
        "henrik_api": henrik_secret_manager.storage_status(),
    }


@app.get("/api/career")
async def get_career() -> dict:
    """
    Retrieves career history and aggregate stats for the current account.

    @return: Career summary for the active PUUID.
    """
    puuid = tracker_state.get("puuid", "")
    career = db_manager.get_career_summary(puuid)
    season_catalog = await get_valorant_season_catalog()
    recent_matches = []
    season_counts = {}
    competitive_tracker_scores = []
    current_rank = ""
    for match in career["recent_matches"]:
        match["map_id"] = match.get("map", "")
        match["won"] = match.get("win_loss") == "WIN"
        match["result"] = "VICTORY" if match["won"] else "DEFEAT"
        match["scoreline"] = ""
        mode = str(match.get("gamemode") or "").strip().lower()
        acs = int(_number_or_zero(match.get("acs")))
        combat_score = int(_number_or_zero(match.get("score")))
        inferred_rounds = round(combat_score / acs) if acs > 0 and combat_score > acs else 0
        cached_context = None
        if mode == "competitive":
            cached_context = get_cached_match_tracker_context(match.get("match_id", ""), puuid)
            if cached_context:
                match["tracker_score"] = cached_context["tracker_score"]
                match["kast"] = cached_context["kast"]
                match["dda"] = cached_context["dda"]
                match["adr"] = cached_context["adr"]
                match["team_rounds"] = cached_context["team_rounds"]
                match["enemy_rounds"] = cached_context["enemy_rounds"]
                match["round_win_percent"] = cached_context["round_win_percent"]
            else:
                rank = match.get("rank_after") or match.get("rank_before") or current_rank or "Unranked"
                match["tracker_score"] = calculate_tracker_score(
                    kd=float(_number_or_zero(match.get("kd"))),
                    hs_percent=float(_number_or_zero(match.get("hs_percent"))),
                    acs=acs,
                    rank=rank,
                    peak_rank=rank,
                    kills=int(_number_or_zero(match.get("kills"))),
                    deaths=int(_number_or_zero(match.get("deaths"))),
                    assists=int(_number_or_zero(match.get("assists"))),
                    rounds_played=inferred_rounds or None,
                    won=match["won"],
                    avg_rank=rank,
                )
            competitive_tracker_scores.append(match["tracker_score"])
        stored_season_id = match.get("season_id") or ""
        season_id = stored_season_id
        if not season_id and cached_context:
            season_id = cached_context.get("season_id", "")
        if not season_id:
            season_id = get_cached_match_season_id(match.get("match_id", ""))
        if not season_id:
            season_id = season_id_for_match_date(match.get("date", ""), season_catalog)
        match["season_id"] = season_id
        if season_id:
            if not stored_season_id:
                persist_match_season_id(match.get("match_id", ""), season_id, puuid=puuid, overwrite=False)
            season_meta = season_catalog.get(season_id, {})
            match["season_label"] = season_meta.get("label") or fallback_season_label(season_id)
            match["episode_id"] = season_meta.get("episode_id", "")
            match["episode_label"] = season_meta.get("episode_label", "")
            season_counts[season_id] = season_counts.get(season_id, 0) + 1
        enrich_match_assets(match)
        if not current_rank and match.get("rank_after") and match.get("rank_after") != "Unranked":
            current_rank = match["rank_after"]
        recent_matches.append(match)

    season_options = []
    for season_id, count in season_counts.items():
        season_meta = season_catalog.get(season_id, {})
        season_options.append({
            "id": season_id,
            "label": season_meta.get("label") or fallback_season_label(season_id),
            "episode_id": season_meta.get("episode_id", ""),
            "episode_label": season_meta.get("episode_label", ""),
            "start_time": season_meta.get("start_time", ""),
            "end_time": season_meta.get("end_time", ""),
            "count": count
        })
    season_options.sort(key=lambda item: item.get("start_time") or "", reverse=True)

    # Calculate peak rank from recent matches
    peak_rank = current_rank or "Unranked"
    peak_idx = get_rank_index(peak_rank)
    for match in recent_matches:
        for key in ["rank_after", "rank_before"]:
            r = match.get(key)
            if r:
                idx = get_rank_index(r)
                if idx > peak_idx:
                    peak_idx = idx
                    peak_rank = r

    career["recent_matches"] = recent_matches
    career["season_options"] = season_options
    career["puuid"] = puuid
    career["player_name"] = tracker_state.get("player_name", "Unknown")
    career["current_rank"] = current_rank or "Unranked"
    rank_assets = asset_manager.rank(current_rank or "Unranked")
    career["current_rank_icon_url"] = rank_assets.get("large") or rank_assets.get("small", "")
    career["peak_rank"] = peak_rank
    peak_assets = asset_manager.rank(peak_rank)
    career["peak_rank_icon_url"] = peak_assets.get("large") or peak_assets.get("small", "")
    career["tracker_score"] = (
        round(sum(competitive_tracker_scores) / len(competitive_tracker_scores))
        if competitive_tracker_scores
        else calculate_tracker_score(
            career["avg_kd"],
            career["avg_hs_percent"],
            career["avg_acs"],
            current_rank or "Unranked",
            current_rank or "Unranked"
        ) if career["matches"] else 0
    )
    return career


@app.post("/api/calculate-score")
async def api_calculate_score(data: dict) -> dict:
    """
    Calcule le Tracker Score (TRS) à la volée pour les paramètres fournis,
    en utilisant le modèle GBR du backend.
    """
    score = calculate_tracker_score(
        kd=float(data.get("kd", 0.0)),
        hs_percent=float(data.get("hs_percent", 0.0)),
        acs=int(data.get("acs", 0)),
        rank=str(data.get("rank", "Unranked")),
        peak_rank=str(data.get("peak_rank", "Unranked")),
        adr=data.get("adr"),
        dda=data.get("dda"),
        kast=data.get("kast"),
        kills=data.get("kills"),
        deaths=data.get("deaths"),
        assists=data.get("assists"),
        fk=int(data.get("fk", 0)),
        fd=int(data.get("fd", 0)),
        mk=int(data.get("mk", 0)),
        rounds_played=data.get("rounds_played"),
        won=data.get("won"),
        team_rounds=data.get("team_rounds"),
        enemy_rounds=data.get("enemy_rounds"),
        avg_rank=data.get("avg_rank")
    )
    return {"status": "ok", "score": score}



@app.get("/api/match-leaderboard/{match_id}")
async def get_match_leaderboard(match_id: str) -> dict:
    """
    Retrieves the complete leaderboard stats for all players in a past match.
    Uses cached raw match JSON or fetches it live from Riot API if client is running.
    """
    # 1. Check local cache
    raw_json = db_manager.get_match_details_json(match_id)
    
    # 2. Fetch live if not cached
    if not raw_json:
        from lockfile_scanner import LockfileScanner
        scanner = LockfileScanner()
        lockfile_info = scanner.scan()
        if not lockfile_info:
            return {
                "status": "error",
                "message": "Match non mis en cache. Veuillez ouvrir VALORANT pour récupérer les détails."
            }
            
        local_url = f"{lockfile_info['protocol']}://127.0.0.1:{lockfile_info['port']}"
        local_headers = lockfile_info["headers"]
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=12.0) as client:
                context = await get_riot_remote_context(client, local_url, local_headers)
                if not context:
                    return {
                        "status": "error",
                        "message": "Impossible de s'authentifier avec le client Riot local."
                    }
                
                pd_url = context["pd_url"]
                remote_headers = context["remote_headers"]
                
                match_resp = await client.get(f"{pd_url}/match-details/v1/matches/{match_id}", headers=remote_headers)
                if match_resp.status_code != 200:
                    return {
                        "status": "error",
                        "message": f"Le serveur Riot a renvoyé une erreur {match_resp.status_code}"
                    }
                    
                raw_json = match_resp.text
                db_manager.save_match_details_json(match_id, raw_json)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération : {str(e)}"
            }
            
    # 3. Parse raw JSON
    try:
        match_data = json.loads(raw_json)
        match_info = match_data.get("matchInfo") or match_data.get("MatchInfo") or {}
        map_id = match_info.get("mapId") or match_info.get("mapID") or ""
        queue_id = match_info.get("queueID") or match_info.get("queueId") or ""
        season_id = extract_match_season_id(match_data)
        season_catalog = await get_valorant_season_catalog()
        season_meta = season_catalog.get(season_id, {}) if season_id else {}
        season_label = (season_meta.get("label") or fallback_season_label(season_id)) if season_id else ""
        teams = match_data.get("teams") or match_data.get("Teams") or []
        players = match_data.get("players") or match_data.get("Players") or []
        round_results = match_data.get("roundResults") or match_data.get("RoundResults") or []
        stored_player_names = {}
        
        # Determine anchor PUUID (local player perspective)
        anchor_puuid = tracker_state.get("puuid", "")
        conn = db_manager._connect()
        try:
            row = conn.execute(
                "SELECT puuid, player_name FROM my_matches WHERE match_id = ? LIMIT 1",
                (match_id,)
            ).fetchone()
            if row:
                if row["puuid"]:
                    stored_player_names[row["puuid"]] = row["player_name"]
                    anchor_puuid = row["puuid"]
        except Exception:
            pass
        finally:
            conn.close()
                
        if not anchor_puuid and players:
            anchor_puuid = players[0].get("subject") or players[0].get("Subject") or ""
        if season_id:
            persist_match_season_id(match_id, season_id, overwrite=True)
            
        local_player = next((p for p in players if (p.get("subject") or p.get("Subject")) == anchor_puuid), None)
        ally_team_id = None
        if local_player:
            ally_team_id = local_player.get("teamId") or local_player.get("TeamID") or local_player.get("teamID")
        if not ally_team_id and players:
            ally_team_id = players[0].get("teamId") or players[0].get("TeamID") or players[0].get("teamID")
            
        # Determine team scores & result
        team_wins = {}
        ally_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) == ally_team_id), {})
        enemy_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) != ally_team_id), {})
        for team in teams:
            team_id = team.get("teamId") or team.get("TeamID")
            if team_id:
                team_wins[team_id] = bool(team.get("won") if "won" in team else team.get("Won", False))
        
        rounds_won = int(_number_or_zero(ally_team.get("roundsWon") or ally_team.get("RoundsWon") or ally_team.get("numPoints")))
        enemy_rounds = int(_number_or_zero(enemy_team.get("roundsWon") or enemy_team.get("RoundsWon") or enemy_team.get("numPoints")))
        won = bool(ally_team.get("won") if "won" in ally_team else ally_team.get("Won", rounds_won > enemy_rounds))
        
        result_text = "VICTORY" if won else "DEFEAT"
        scoreline = f"{rounds_won}-{enemy_rounds}" if rounds_won or enemy_rounds else "--"
        match_duration = format_duration_from_millis(match_info.get("gameLengthMillis") or match_info.get("GameLengthMillis"))
        
        # Calculate shots per player for HS%
        shots_by_player = {}
        for round_result in round_results:
            player_stats_list = round_result.get("playerStats") or round_result.get("PlayerStats") or []
            for player_stats in player_stats_list:
                p_id = player_stats.get("subject") or player_stats.get("Subject")
                if not p_id:
                    continue
                if p_id not in shots_by_player:
                    shots_by_player[p_id] = {"headshots": 0, "bodyshots": 0, "legshots": 0}
                
                damage_list = player_stats.get("damage") or player_stats.get("Damage") or []
                for damage in damage_list:
                    shots_by_player[p_id]["headshots"] += int(_number_or_zero(damage.get("headshots")))
                    shots_by_player[p_id]["bodyshots"] += int(_number_or_zero(damage.get("bodyshots")))
                    shots_by_player[p_id]["legshots"] += int(_number_or_zero(damage.get("legshots")))
                    
        allies_list = []
        enemies_list = []
        player_puuids = [p.get("subject") or p.get("Subject") or "" for p in players]
        player_teams = {
            (p.get("subject") or p.get("Subject") or ""): (p.get("teamId") or p.get("TeamID") or p.get("teamID") or "")
            for p in players
        }
        round_metric_map = build_round_player_metrics(round_results, player_puuids, player_teams)
        needs_name_service = any(not match_player_display_name(p) for p in players)
        name_service_map = await resolve_current_riot_player_names(player_puuids) if needs_name_service else {}
        
        for p in players:
            p_puuid = p.get("subject") or p.get("Subject") or ""
            p_team_id = p.get("teamId") or p.get("TeamID") or p.get("teamID")
            
            p_stats = p.get("stats") or p.get("Stats") or {}
            kills = int(_number_or_zero(p_stats.get("kills") or p_stats.get("Kills")))
            deaths = int(_number_or_zero(p_stats.get("deaths") or p_stats.get("Deaths")))
            assists = int(_number_or_zero(p_stats.get("assists") or p_stats.get("Assists")))
            score = int(_number_or_zero(p_stats.get("score") or p_stats.get("Score")))
            
            rounds_played = int(_number_or_zero(p_stats.get("roundsPlayed") or p_stats.get("RoundsPlayed") or rounds_won + enemy_rounds))
            acs = round(score / max(rounds_played, 1))
            
            p_shots = shots_by_player.get(p_puuid, {"headshots": 0, "bodyshots": 0, "legshots": 0})
            total_shots = p_shots["headshots"] + p_shots["bodyshots"] + p_shots["legshots"]
            hs_percent = round((p_shots["headshots"] / max(total_shots, 1)) * 100, 1) if total_shots > 0 else 0.0
            p_metrics = round_metric_map.get(p_puuid, {})
            damage_dealt = int(p_metrics.get("damage_dealt", 0))
            damage_received = int(p_metrics.get("damage_received", 0))
            adr = round(damage_dealt / max(rounds_played, 1), 1)
            dda = round((damage_dealt - damage_received) / max(rounds_played, 1), 1)
            kast = round((int(p_metrics.get("kast_rounds", 0)) / max(rounds_played, 1)) * 100, 1)
            
            tier = p.get("competitiveTier") or p.get("CompetitiveTier") or 0
            rank = rank_name_from_tier(tier) or "Unranked"
            
            agent_id = p.get("characterId") or p.get("CharacterID") or ""
            agent_name = AGENT_MAPPING.get(agent_id, "Unknown Agent")
            
            full_name = (
                match_player_display_name(p)
                or name_service_map.get(p_puuid)
                or stored_player_names.get(p_puuid)
                or "Unknown Player"
            )
            
            player_info = {
                "puuid": p_puuid,
                "name": full_name,
                "agent_id": agent_id,
                "agent": agent_name,
                "team_id": p_team_id,
                "rank": rank,
                "peak_rank": rank,
                "kd": round(kills / max(deaths, 1), 2),
                "hs_percent": hs_percent,
                "acs": acs,
                "adr": adr,
                "dda": dda,
                "kast": kast,
                "fk": int(p_metrics.get("first_kills", 0)),
                "fd": int(p_metrics.get("first_deaths", 0)),
                "mk": int(p_metrics.get("multi_kills", 0)),
                "damage_dealt": damage_dealt,
                "damage_received": damage_received,
                "avg_loadout": round(int(p_metrics.get("loadout_total", 0)) / max(rounds_played, 1)),
                "avg_bank": round(int(p_metrics.get("bank_total", 0)) / max(rounds_played, 1)),
                "kills": kills,
                "deaths": deaths,
                "assists": assists,
                "score": 0,
                "rounds_played": rounds_played,
                "is_self": p_puuid == anchor_puuid
            }
            
            enrich_player_assets(player_info)
            
            if p_team_id == ally_team_id:
                allies_list.append(player_info)
            else:
                enemies_list.append(player_info)
                
        for team_players in (allies_list, enemies_list):
            team_average_rank = average_rank_name(team_players)
            for player in team_players:
                player_team_rounds = rounds_won if player["team_id"] == ally_team_id else enemy_rounds
                player_enemy_rounds = enemy_rounds if player["team_id"] == ally_team_id else rounds_won
                player_won = team_wins.get(player["team_id"], player["team_id"] == ally_team_id and won)
                player["score"] = calculate_tracker_score(
                    player["kd"],
                    player["hs_percent"],
                    player["acs"],
                    player["rank"],
                    player["rank"],
                    adr=player["adr"],
                    dda=player["dda"],
                    kast=player["kast"],
                    kills=player["kills"],
                    deaths=player["deaths"],
                    assists=player["assists"],
                    fk=player["fk"],
                    fd=player["fd"],
                    mk=player["mk"],
                    rounds_played=player["rounds_played"],
                    won=player_won,
                    team_rounds=player_team_rounds,
                    enemy_rounds=player_enemy_rounds,
                    avg_rank=team_average_rank
                )

        allies_list.sort(key=lambda x: x.get("acs", 0), reverse=True)
        enemies_list.sort(key=lambda x: x.get("acs", 0), reverse=True)
        player_lookup = {player["puuid"]: player for player in allies_list + enemies_list}
        tabs_data = build_match_tabs_data(round_results, allies_list + enemies_list, player_lookup, ally_team_id)
        
        map_assets = asset_manager.map(map_id)
        map_name = map_assets.get("name", "")
        map_banner_url = map_assets.get("banner", "")
        
        return {
            "status": "ok",
            "match_id": match_id,
            "map_id": map_id,
            "map_name": map_name,
            "map_banner_url": map_banner_url,
            "queue_id": queue_id,
            "season_id": season_id,
            "season_label": season_label,
            "episode_id": season_meta.get("episode_id", ""),
            "episode_label": season_meta.get("episode_label", ""),
            "duration": match_duration,
            "scoreline": scoreline,
            "result": result_text,
            "allies": allies_list,
            "enemies": enemies_list,
            "rounds": tabs_data["rounds"],
            "duels": tabs_data["duels"]
        }
    except Exception as parse_err:
        return {
            "status": "error",
            "message": f"Erreur lors de l'analyse des détails : {str(parse_err)}"
        }


@app.post("/api/backfill/competitive")
async def backfill_competitive(limit: int = 20) -> dict:
    """
    Imports recent competitive matches for the current account from Riot PD.

    @param limit: Maximum number of competitive matches to import.
    @return: Import summary.
    """
    from lockfile_scanner import LockfileScanner
    scanner = LockfileScanner()
    lockfile_info = scanner.scan()
    if not lockfile_info:
        return {
            "status": "error",
            "message": "Lockfile not found. Open Valorant before importing."
        }

    limit = max(1, min(int(limit or 20), 50))
    local_url = f"{lockfile_info['protocol']}://127.0.0.1:{lockfile_info['port']}"
    local_headers = lockfile_info["headers"]
    imported = []
    updated = []
    skipped = []
    failed = []

    async with httpx.AsyncClient(verify=False, timeout=12.0) as client:
        context = await get_riot_remote_context(client, local_url, local_headers)
        if not context:
            return {
                "status": "error",
                "message": "Unable to authenticate with Riot local client."
            }

        puuid = context["puuid"]
        player_name = context["player_name"]
        pd_url = context["pd_url"]
        remote_headers = context["remote_headers"]

        previous_puuid = tracker_state.get("puuid", "")
        tracker_state["puuid"] = puuid
        tracker_state["player_name"] = player_name
        tracker_state["status"] = "connected"
        if previous_puuid != puuid:
            refresh_session_summary()

        updates = []
        max_scan = min(100, max(20, limit * 5))
        page_size = 10
        for start_index in range(0, max_scan, page_size):
            end_index = start_index + page_size
            updates_resp = await client.get(
                f"{pd_url}/mmr/v1/players/{puuid}/competitiveupdates?startIndex={start_index}&endIndex={end_index}",
                headers=remote_headers
            )
            if updates_resp.status_code in (400, 404):
                logger.warning(
                    "Riot competitive updates returned %s at startIndex=%s. Stopping pagination.",
                    updates_resp.status_code, start_index
                )
                break
            elif updates_resp.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Riot MMR updates returned {updates_resp.status_code}: {updates_resp.text[:150]}.",
                    "body": updates_resp.text[:300],
                    "start_index": start_index,
                    "end_index": end_index
                }
            page_matches = updates_resp.json().get("Matches", [])
            if not page_matches:
                break
            updates.extend(page_matches)
            if len(page_matches) < page_size:
                break
            competitive_seen = sum(
                1 for update in updates
                if isinstance(update, dict) and update.get("QueueID") == "competitive" and update.get("MatchID")
            )
            if competitive_seen >= limit:
                break

        competitive_updates = [
            update for update in updates
            if isinstance(update, dict) and update.get("QueueID") == "competitive" and update.get("MatchID")
        ][:limit]

        for update in competitive_updates:
            match_id = update["MatchID"]
            existed_before = db_manager.match_exists(puuid, match_id)

            summary = await fetch_post_match_summary(client, pd_url, match_id, puuid, remote_headers)
            if not summary:
                failed.append({"match_id": match_id, "reason": "match_details_unavailable"})
                continue

            summary.update(extract_mmr_update({"Matches": [update]}, match_id))
            summary["date"] = iso_from_riot_millis(update.get("MatchStartTime"))
            # Calculate tracker score for the backfilled match
            peak_rank = tracker_state.get("peak_rank", "")
            if not peak_rank:
                peak_rank = summary.get("rank_after", "") or summary.get("rank_before", "")
            summary["tracker_score"] = calculate_tracker_score(
                kd=summary.get("kd", 0.0),
                hs_percent=summary.get("hs_percent", 0.0),
                acs=summary.get("acs", 0),
                rank=summary.get("rank_after", "") or summary.get("rank_before", ""),
                peak_rank=peak_rank,
                kills=summary.get("kills"),
                deaths=summary.get("deaths"),
                assists=summary.get("assists"),
                rounds_played=summary.get("rounds_played")
            )
            enrich_match_assets(summary)
            inserted = persist_completed_match(summary, puuid, player_name)
            if inserted and existed_before:
                updated.append({
                    "match_id": match_id,
                    "rr_change": summary.get("rr_change", 0),
                    "hs_percent": summary.get("hs_percent", 0)
                })
            elif inserted:
                imported.append({
                    "match_id": match_id,
                    "rr_change": summary.get("rr_change", 0),
                    "rank_before": summary.get("rank_before", ""),
                    "rank_after": summary.get("rank_after", ""),
                    "rankup": summary.get("rankup", False)
                })
            else:
                skipped.append({"match_id": match_id, "reason": "already_saved"})

    refresh_session_summary()
    return {
        "status": "ok",
        "puuid": tracker_state.get("puuid", ""),
        "player_name": tracker_state.get("player_name", "Unknown"),
        "requested_limit": limit,
        "competitive_found": len(competitive_updates),
        "imported": len(imported),
        "updated": len(updated),
        "skipped": len(skipped),
        "failed": len(failed),
        "imported_matches": imported,
        "updated_matches": updated[:10],
        "skipped_matches": skipped[:10],
        "failed_matches": failed[:10],
        "session_summary": tracker_state.get("session_summary", {})
    }


@app.get("/api/debug/lcu")
async def debug_lcu() -> dict:
    """
    Exposes the raw LCU data for debugging.

    @return: A JSON response containing session and presence data.
    """
    from lockfile_scanner import LockfileScanner
    scanner = LockfileScanner()
    lockfile_info = scanner.scan()
    
    if not lockfile_info:
        return {"error": "Lockfile not found"}
        
    port = lockfile_info["port"]
    protocol = lockfile_info["protocol"]
    headers = lockfile_info["headers"]
    url = f"{protocol}://127.0.0.1:{port}"
    
    async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
        try:
            session_resp = await client.get(f"{url}/chat/v1/session", headers=headers)
            session = session_resp.json()
        except Exception as e:
            session = {"error": str(e)}
            
        try:
            presences_resp = await client.get(f"{url}/chat/v4/presences", headers=headers)
            presences = presences_resp.json()
        except Exception as e:
            presences = {"error": str(e)}
            
        res = {
            "session": session,
            "presences": presences
        }
        with runtime_path("lcu_debug_output.json").open("w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
            
        return res
