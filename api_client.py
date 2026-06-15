import os
import time
from collections import OrderedDict
from dataclasses import dataclass

import httpx
import hashlib

from app_logging import get_logger


logger = get_logger(__name__)


def _env_int(name: str, default: int) -> int:
    """
    Reads a positive integer from the environment.
    """
    try:
        return max(1, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


HENRIK_REQUESTS_PER_MINUTE = _env_int("HENRIK_REQUESTS_PER_MINUTE", 30)
HENRIK_WINDOW_SECONDS = 60.0
_henrik_response_cache = {}
_henrik_pending_requests = OrderedDict()
_henrik_window_started_at = time.monotonic()
_henrik_window_count = 0


class DeferredHenrikData(Exception):
    """
    Raised when HenrikDev data is not cached yet and the current minute budget is exhausted.
    """


@dataclass
class HenrikResponse:
    """
    A cached or live HenrikDev response.
    """

    status_code: int
    data: dict
    from_cache: bool = False


def _cache_key(url: str) -> str:
    """
    Uses the full HenrikDev URL as the in-memory cache key.
    """
    return url


def _reset_henrik_window_if_needed(now: float | None = None) -> None:
    """
    Starts a new per-minute request window when needed.
    """
    global _henrik_window_started_at, _henrik_window_count
    current = now or time.monotonic()
    if current - _henrik_window_started_at >= HENRIK_WINDOW_SECONDS:
        logger.info(
            "HenrikDev request window reset: used=%s queued=%s limit=%s",
            _henrik_window_count,
            len(_henrik_pending_requests),
            HENRIK_REQUESTS_PER_MINUTE,
        )
        _henrik_window_started_at = current
        _henrik_window_count = 0


def _henrik_budget_available() -> bool:
    """
    Returns whether another HenrikDev request can be sent in the current minute.
    """
    _reset_henrik_window_if_needed()
    return _henrik_window_count < HENRIK_REQUESTS_PER_MINUTE


def _consume_henrik_budget() -> bool:
    """
    Consumes one HenrikDev request slot when available.
    """
    global _henrik_window_count
    if not _henrik_budget_available():
        return False
    _henrik_window_count += 1
    return True


def _queue_henrik_request(url: str) -> None:
    """
    Queues a HenrikDev URL to retry when the next minute budget opens.
    """
    key = _cache_key(url)
    if key not in _henrik_response_cache:
        _henrik_pending_requests[key] = url


def get_henrik_rate_state() -> dict:
    """
    Returns the current HenrikDev request budget and cache state.
    """
    _reset_henrik_window_if_needed()
    seconds_elapsed = time.monotonic() - _henrik_window_started_at
    return {
        "limit_per_minute": HENRIK_REQUESTS_PER_MINUTE,
        "used_this_minute": _henrik_window_count,
        "queued": len(_henrik_pending_requests),
        "cached": len(_henrik_response_cache),
        "seconds_until_reset": max(0, round(HENRIK_WINDOW_SECONDS - seconds_elapsed)),
    }


async def _fetch_henrik_json(client: httpx.AsyncClient, url: str, headers: dict) -> HenrikResponse:
    """
    Fetches HenrikDev JSON with a shared per-minute budget and response cache.
    """
    global _henrik_window_count
    key = _cache_key(url)
    cached = _henrik_response_cache.get(key)
    if cached:
        return HenrikResponse(cached["status_code"], cached["data"], from_cache=True)

    if not _consume_henrik_budget():
        _queue_henrik_request(url)
        raise DeferredHenrikData(url)

    response = await client.get(url, headers=headers)
    logger.debug(
        "HenrikDev request: status=%s count=%s/%s url=%s",
        response.status_code,
        _henrik_window_count,
        HENRIK_REQUESTS_PER_MINUTE,
        url,
    )

    if response.status_code == 429:
        _henrik_window_count = HENRIK_REQUESTS_PER_MINUTE
        _queue_henrik_request(url)
        logger.warning(
            "HenrikDev rate limit reached: queued=%s limit=%s",
            len(_henrik_pending_requests),
            HENRIK_REQUESTS_PER_MINUTE,
        )
        raise DeferredHenrikData(url)

    try:
        data = response.json()
    except ValueError:
        data = {}

    _henrik_pending_requests.pop(key, None)
    if response.status_code == 200:
        _henrik_response_cache[key] = {
            "status_code": response.status_code,
            "data": data,
            "saved_at": time.time(),
        }

    return HenrikResponse(response.status_code, data)


async def _drain_henrik_pending(client: httpx.AsyncClient, headers: dict) -> None:
    """
    Tries queued HenrikDev requests at the beginning of each new budget window.
    """
    _reset_henrik_window_if_needed()
    drained = 0
    while _henrik_pending_requests and _henrik_budget_available():
        _, url = _henrik_pending_requests.popitem(last=False)
        try:
            await _fetch_henrik_json(client, url, headers)
            drained += 1
        except DeferredHenrikData:
            break
        except Exception:
            logger.debug("Failed to drain queued HenrikDev request: %s", url, exc_info=True)
    if drained:
        logger.info(
            "HenrikDev queued requests drained: drained=%s remaining=%s count=%s/%s",
            drained,
            len(_henrik_pending_requests),
            _henrik_window_count,
            HENRIK_REQUESTS_PER_MINUTE,
        )

RANKS_LIST = [
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

HENRIK_MODE_BY_QUEUE = {
    "competitive": "competitive",
    "unrated": "unrated",
    "swiftplay": "swiftplay",
    "spikerush": "spikerush",
    "deathmatch": "deathmatch",
    "ggteam": "escalation",
    "onefa": "replication",
    "snowball": "snowballfight",
    "newmap": "newmap",
    "hurm": "teamdeathmatch",
}


def _puuid_hash_int(puuid: str) -> int:
    """
    Creates a deterministic integer from a PUUID for seeding mock stats.

    @param puuid: The player's unique identifier.
    @return: A positive integer derived from the PUUID hash.
    """
    return int(hashlib.md5(puuid.encode()).hexdigest(), 16)


def _henrik_mode_from_queue(queue: str) -> str:
    """
    Converts Riot queue IDs to HenrikDev match history mode values.

    @param queue: Riot queue ID from local client state.
    @return: HenrikDev mode value, or an empty string when unsupported.
    """
    if not queue:
        return ""
    return HENRIK_MODE_BY_QUEUE.get(queue.lower(), "")


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


def _normalize_rank_name(rank: str, default: str = "Unknown") -> str:
    """
    Normalizes rank labels returned by HenrikDev.

    @param rank: Raw rank name.
    @param default: Value to use when rank is missing.
    @return: Display-safe rank name.
    """
    if not rank:
        return default
    if rank.lower() == "unrated":
        return "Unranked"
    return rank


def _extract_rank_info(mmr_data: dict) -> tuple:
    """
    Extracts current and peak ranks from HenrikDev MMR response formats.

    @param mmr_data: The response "data" object.
    @return: Tuple of current rank and peak rank.
    """
    current_rank = "Unknown"
    peak_rank = "Unknown"

    current = mmr_data.get("current", {})
    if isinstance(current, dict):
        tier = current.get("tier", {})
        if isinstance(tier, dict):
            current_rank = _normalize_rank_name(tier.get("name"), current_rank)

    peak = mmr_data.get("peak", {})
    if isinstance(peak, dict):
        tier = peak.get("tier", {})
        if isinstance(tier, dict):
            peak_rank = _normalize_rank_name(tier.get("name"), peak_rank)

    # HenrikDev v1 has a flatter shape. Keep this for fallback compatibility.
    current_rank = _normalize_rank_name(mmr_data.get("currenttierpatched"), current_rank)
    highest_tier = mmr_data.get("highest_tier", {})
    if isinstance(highest_tier, dict):
        peak_rank = _normalize_rank_name(highest_tier.get("patched_tier"), peak_rank)

    if peak_rank == "Unknown" and current_rank != "Unknown":
        peak_rank = current_rank

    return current_rank, peak_rank


class HenrikDevClient:
    """
    Client for interacting with the HenrikDev Valorant API.
    """

    def __init__(self, api_key: str = None):
        """
        Initializes the HenrikDevClient with an optional API key.

        @param api_key: The HenrikDev API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.henrikdev.xyz"

    def _generate_mock_stats(self, puuid: str) -> dict:
        """
        Generates deterministic but unique mock stats for a player based on their PUUID.

        @param puuid: The player's unique identifier.
        @return: A dictionary containing varied mock stats.
        """
        h = _puuid_hash_int(puuid)

        # KD between 0.60 and 1.80
        kd = round(0.60 + (h % 120) / 100.0, 2)
        # HS% between 12.0 and 35.0
        hs_percent = round(12.0 + ((h >> 8) % 230) / 10.0, 1)
        # ACS between 120 and 310
        acs = 120 + ((h >> 16) % 191)
        # Generate unique mock match IDs based on PUUID segments
        puuid_short = puuid.replace("-", "")[:8]
        mock_match_ids = [f"m_{puuid_short}_{i}" for i in range(3)]

        badge = ""
        if kd > 1.5:
            badge = "On Fire"
        elif kd < 0.8:
            badge = "Struggling"

        return {
            "rank": "Unknown",
            "peak_rank": "Unknown",
            "kd": kd,
            "hs_percent": hs_percent,
            "acs": acs,
            "badge": badge,
            "match_ids": mock_match_ids
        }

    async def get_player_stats(self, puuid: str, queue: str) -> dict:
        """
        Fetches the player stats from HenrikDev API for a specific queue.

        @param puuid: The player's unique identifier.
        @param queue: The game mode / queue type.
        @return: A dictionary containing the player stats.
        """
        if not self.api_key:
            stats = self._generate_mock_stats(puuid)
            stats["_source"] = "mock_no_api_key"
            stats["_cacheable"] = True
            return stats

        headers = {"Authorization": self.api_key}
        region = "eu"
        critical_statuses = {401, 403}
        henrik_mode = _henrik_mode_from_queue(queue)
        rank = "Unknown"
        peak_rank = "Unknown"
        deferred = False
        
        async with httpx.AsyncClient(timeout=6.0) as client:
            try:
                await _drain_henrik_pending(client, headers)

                mmr_url = f"{self.base_url}/valorant/v3/by-puuid/mmr/{region}/pc/{puuid}"
                try:
                    mmr_resp = await _fetch_henrik_json(client, mmr_url, headers)
                except DeferredHenrikData:
                    deferred = True
                    mmr_resp = None
                
                mmr_ok = bool(mmr_resp and mmr_resp.status_code == 200)
                if mmr_ok:
                    mmr_data = mmr_resp.data.get("data", {})
                    rank, peak_rank = _extract_rank_info(mmr_data)
                elif mmr_resp and mmr_resp.status_code in critical_statuses:
                    logger.warning("Using fallback stats after HenrikDev MMR status=%s puuid=%s", mmr_resp.status_code, puuid)
                    fallback_stats = self._generate_mock_stats(puuid)
                    fallback_stats["_source"] = f"fallback_mmr_status_{mmr_resp.status_code}"
                    fallback_stats["_cacheable"] = mmr_resp.status_code == 403
                    return fallback_stats
                
                matches_url = f"{self.base_url}/valorant/v3/by-puuid/matches/{region}/{puuid}"
                if henrik_mode:
                    matches_url = f"{matches_url}?mode={henrik_mode}"
                try:
                    matches_resp = await _fetch_henrik_json(client, matches_url, headers)
                except DeferredHenrikData:
                    deferred = True
                    matches_resp = None

                if matches_resp and matches_resp.status_code in critical_statuses:
                    logger.warning(
                        "Using fallback stats after HenrikDev matches status=%s puuid=%s",
                        matches_resp.status_code,
                        puuid,
                    )
                    fallback_stats = self._generate_mock_stats(puuid)
                    fallback_stats["rank"] = rank
                    fallback_stats["peak_rank"] = peak_rank
                    fallback_stats["_source"] = f"fallback_matches_status_{matches_resp.status_code}"
                    fallback_stats["_cacheable"] = matches_resp.status_code == 403
                    return fallback_stats
                
                matches_ok = bool(matches_resp and matches_resp.status_code == 200)
                if not mmr_ok and not matches_ok:
                    logger.warning(
                        "Using temporary fallback stats because HenrikDev data is not ready: puuid=%s deferred=%s",
                        puuid,
                        deferred,
                    )
                    fallback_stats = self._generate_mock_stats(puuid)
                    fallback_stats["_source"] = "fallback_deferred" if deferred else "fallback_unusable"
                    fallback_stats["_cacheable"] = not deferred
                    fallback_stats["_deferred"] = deferred
                    return fallback_stats
                
                kills = 0
                deaths = 0
                total_score = 0
                total_rounds = 0
                headshots = 0
                bodyshots = 0
                legshots = 0
                match_count = 0
                match_ids = []
                
                if matches_ok:
                    matches_data = matches_resp.data.get("data", [])
                    for match in matches_data:
                        if not isinstance(match, dict):
                            continue

                        metadata = match.get("metadata") or {}
                        if metadata.get("matchid"):
                            match_ids.append(metadata.get("matchid"))
                            
                        players_data = match.get("players") or {}
                        players = players_data.get("all_players") or []
                        player_stats = None
                        for p in players:
                            if isinstance(p, dict) and p.get("puuid") == puuid:
                                player_stats = p
                                break
                        
                        if player_stats:
                            match_count += 1
                            stats = player_stats.get("stats") or {}
                            kills += _number_or_zero(stats.get("kills"))
                            deaths += _number_or_zero(stats.get("deaths"))
                            total_score += _number_or_zero(stats.get("score"))
                            
                            teams = match.get("teams") or {}
                            red_rounds = _number_or_zero(teams.get("red", {}).get("rounds_won")) if teams.get("red") else 0
                            blue_rounds = _number_or_zero(teams.get("blue", {}).get("rounds_won")) if teams.get("blue") else 0
                            total_rounds += (red_rounds + blue_rounds)
                            
                            headshots += _number_or_zero(stats.get("headshots"))
                            bodyshots += _number_or_zero(stats.get("bodyshots"))
                            legshots += _number_or_zero(stats.get("legshots"))

                if not mmr_ok and match_count == 0:
                    logger.warning("Using fallback stats because HenrikDev returned no usable data: puuid=%s", puuid)
                    fallback_stats = self._generate_mock_stats(puuid)
                    fallback_stats["_source"] = "fallback_no_usable_data"
                    fallback_stats["_cacheable"] = not deferred
                    fallback_stats["_deferred"] = deferred
                    return fallback_stats
                
                kd = round(kills / max(deaths, 1), 2) if match_count > 0 else 1.0
                acs = round(total_score / total_rounds) if total_rounds > 0 else 200
                
                total_shots = headshots + bodyshots + legshots
                hs_percent = round((headshots / max(total_shots, 1)) * 100, 1) if total_shots > 0 else 20.0
                
                return {
                    "rank": rank,
                    "peak_rank": peak_rank,
                    "kd": kd,
                    "hs_percent": hs_percent,
                    "acs": acs,
                    "badge": "",
                    "match_ids": match_ids,
                    "_source": "cache" if ((mmr_resp and mmr_resp.from_cache) or (matches_resp and matches_resp.from_cache)) else "api",
                    "_cacheable": not deferred,
                    "_deferred": deferred,
                }
                
            except Exception:
                logger.exception("HenrikDev client request failed")
                fallback_stats = self._generate_mock_stats(puuid)
                fallback_stats["rank"] = rank
                fallback_stats["peak_rank"] = peak_rank
                fallback_stats["_source"] = "fallback_exception"
                fallback_stats["_cacheable"] = False
                fallback_stats["_deferred"] = True
                return fallback_stats
