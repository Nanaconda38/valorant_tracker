import httpx
import hashlib

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
            return self._generate_mock_stats(puuid)
            
        headers = {"Authorization": self.api_key}
        region = "eu"
        critical_statuses = {401, 403, 429}
        henrik_mode = _henrik_mode_from_queue(queue)
        rank = "Unknown"
        peak_rank = "Unknown"
        
        async with httpx.AsyncClient(timeout=6.0) as client:
            try:
                mmr_url = f"{self.base_url}/valorant/v3/by-puuid/mmr/{region}/pc/{puuid}"
                mmr_resp = await client.get(mmr_url, headers=headers)
                print(f"DEBUG MMR: {mmr_resp.status_code} for {puuid}", flush=True)
                if mmr_resp.status_code != 200:
                    print(f"DEBUG MMR ERROR: {mmr_resp.text[:200]}", flush=True)
                if mmr_resp.status_code in critical_statuses:
                    print(f"DEBUG FALLBACK: critical MMR status {mmr_resp.status_code} for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
                mmr_ok = mmr_resp.status_code == 200
                if mmr_ok:
                    mmr_data = mmr_resp.json().get("data", {})
                    rank, peak_rank = _extract_rank_info(mmr_data)
                
                matches_url = f"{self.base_url}/valorant/v3/by-puuid/matches/{region}/{puuid}"
                if henrik_mode:
                    matches_url = f"{matches_url}?mode={henrik_mode}"
                matches_resp = await client.get(matches_url, headers=headers)
                print(f"DEBUG MATCHES: {matches_resp.status_code} for {puuid} with mode {henrik_mode or 'all'}", flush=True)
                if matches_resp.status_code != 200:
                    print(f"DEBUG MATCHES ERROR: {matches_resp.text[:200]}", flush=True)
                if matches_resp.status_code in critical_statuses:
                    print(f"DEBUG FALLBACK: critical matches status {matches_resp.status_code} for {puuid}", flush=True)
                    fallback_stats = self._generate_mock_stats(puuid)
                    fallback_stats["rank"] = rank
                    fallback_stats["peak_rank"] = peak_rank
                    return fallback_stats
                
                matches_ok = matches_resp.status_code == 200
                if not mmr_ok and not matches_ok:
                    print(f"DEBUG FALLBACK: MMR and matches failed for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
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
                    matches_data = matches_resp.json().get("data", [])
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
                    print(f"DEBUG FALLBACK: no usable Henrik data for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
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
                    "match_ids": match_ids
                }
                
            except Exception as e:
                print(f"DEBUG CLIENT EXCEPTION: {e!r}", flush=True)
                fallback_stats = self._generate_mock_stats(puuid)
                fallback_stats["rank"] = rank
                fallback_stats["peak_rank"] = peak_rank
                return fallback_stats
