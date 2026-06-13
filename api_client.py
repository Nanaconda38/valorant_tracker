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


def _puuid_hash_int(puuid: str) -> int:
    """
    Creates a deterministic integer from a PUUID for seeding mock stats.

    @param puuid: The player's unique identifier.
    @return: A positive integer derived from the PUUID hash.
    """
    return int(hashlib.md5(puuid.encode()).hexdigest(), 16)


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
        # Rank index from the list
        rank_idx = (h >> 24) % len(RANKS_LIST)
        rank = RANKS_LIST[rank_idx]
        # Peak rank is same or up to 3 tiers higher
        peak_offset = (h >> 32) % 4
        peak_idx = min(rank_idx + peak_offset, len(RANKS_LIST) - 1)
        peak_rank = RANKS_LIST[peak_idx]

        # Generate unique mock match IDs based on PUUID segments
        puuid_short = puuid.replace("-", "")[:8]
        mock_match_ids = [f"m_{puuid_short}_{i}" for i in range(3)]

        badge = ""
        if kd > 1.5:
            badge = "On Fire"
        elif kd < 0.8:
            badge = "Struggling"

        return {
            "rank": rank,
            "peak_rank": peak_rank,
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
        
        async with httpx.AsyncClient(timeout=6.0) as client:
            try:
                mmr_url = f"{self.base_url}/valorant/v1/by-puuid/mmr/{region}/{puuid}"
                mmr_resp = await client.get(mmr_url, headers=headers)
                print(f"DEBUG MMR: {mmr_resp.status_code} for {puuid}", flush=True)
                if mmr_resp.status_code != 200:
                    print(f"DEBUG MMR ERROR: {mmr_resp.text[:200]}", flush=True)
                if mmr_resp.status_code in critical_statuses:
                    print(f"DEBUG FALLBACK: critical MMR status {mmr_resp.status_code} for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
                mmr_ok = mmr_resp.status_code == 200
                rank = "Unranked"
                peak_rank = "Unknown"
                
                if mmr_ok:
                    mmr_data = mmr_resp.json().get("data", {})
                    current_data = mmr_data.get("current_data", {})
                    rank = current_data.get("currenttierpatched", "Unranked")
                    
                    highest_tier = mmr_data.get("highest_tier", {})
                    peak_rank = highest_tier.get("patched_tier", "Unknown")
                
                matches_url = f"{self.base_url}/valorant/v3/by-puuid/matches/{region}/{puuid}?mode={queue}"
                matches_resp = await client.get(matches_url, headers=headers)
                print(f"DEBUG MATCHES: {matches_resp.status_code} for {puuid} with mode {queue}", flush=True)
                if matches_resp.status_code != 200:
                    print(f"DEBUG MATCHES ERROR: {matches_resp.text[:200]}", flush=True)
                if matches_resp.status_code in critical_statuses:
                    print(f"DEBUG FALLBACK: critical matches status {matches_resp.status_code} for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
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
                        metadata = match.get("metadata", {})
                        if metadata.get("matchid"):
                            match_ids.append(metadata.get("matchid"))
                            
                        players = match.get("players", {}).get("all_players", [])
                        player_stats = None
                        for p in players:
                            if p.get("puuid") == puuid:
                                player_stats = p
                                break
                        
                        if player_stats:
                            match_count += 1
                            stats = player_stats.get("stats", {})
                            kills += stats.get("kills", 0)
                            deaths += stats.get("deaths", 0)
                            total_score += stats.get("score", 0)
                            
                            teams = match.get("teams", {})
                            red_rounds = teams.get("red", {}).get("rounds_won", 0) if teams.get("red") else 0
                            blue_rounds = teams.get("blue", {}).get("rounds_won", 0) if teams.get("blue") else 0
                            total_rounds += (red_rounds + blue_rounds)
                            
                            headshots += stats.get("headshots", 0)
                            bodyshots += stats.get("bodyshots", 0)
                            legshots += stats.get("legshots", 0)

                if not mmr_ok and match_count == 0:
                    print(f"DEBUG FALLBACK: no usable Henrik data for {puuid}", flush=True)
                    return self._generate_mock_stats(puuid)
                
                kd = round(kills / max(deaths, 1), 2) if match_count > 0 else 1.0
                acs = round(total_score / max(total_rounds, 1)) if match_count > 0 else 200
                
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
                print(f"DEBUG CLIENT EXCEPTION: {e}", flush=True)
                return self._generate_mock_stats(puuid)
