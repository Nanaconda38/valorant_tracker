import os
import asyncio
import base64
import json
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from asset_manager import AssetManager
from database import DatabaseManager

load_dotenv()

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY", "").strip() or None
SESSION_STARTED_AT = datetime.now(timezone.utc).isoformat()

app = FastAPI(title="Valorant Local Tracker")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
asset_manager = AssetManager()
db_manager = DatabaseManager()

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


def clear_stats_cache(reason: str) -> None:
    """
    Clears cached player stats and logs why the cache was invalidated.

    @param reason: Human-readable reason for the cache clear.
    """
    if stats_cache:
        print(f"DEBUG CACHE CLEAR: {reason} ({len(stats_cache)} entries)", flush=True)
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
        print(f"DEBUG CONTEXT CHANGE: {reason}", flush=True)
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
    for i, r in enumerate(RANKS):
        if r.lower() in rank_name.lower():
            return i
    return 0


def calculate_tracker_score(kd: float, hs_percent: float, acs: int, rank: str, peak_rank: str) -> int:
    """
    Computes a player performance score out of 1000.

    @param kd: Kill-death ratio.
    @param hs_percent: Headshot percentage.
    @param acs: Average combat score.
    @param rank: Current rank.
    @param peak_rank: Peak rank.
    @return: The computed score.
    """
    acs_pts = min(200, round((acs / 300) * 200))
    kd_pts = min(200, round((kd / 1.5) * 200))
    hs_pts = min(200, round((hs_percent / 35) * 200))
    form_pts = 125
    curr_idx = get_rank_index(rank)
    peak_idx = get_rank_index(peak_rank)
    gap = max(0, peak_idx - curr_idx)
    gap_pts = max(50, 150 - (gap * 15))
    return acs_pts + kd_pts + hs_pts + form_pts + gap_pts


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


def get_region_shard(local_region: str) -> tuple:
    """
    Maps LCU region to GLZ region and shard.

    @param local_region: The local region string from LCU.
    @return: A tuple of (glz_region, shard).
    """
    r_lower = local_region.lower()
    if "na" in r_lower or "latam" in r_lower or "br" in r_lower:
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

    return {
        "match_id": match_info.get("matchId") or match_info.get("matchID") or tracker_state.get("current_match_id", ""),
        "queue_id": queue_id,
        "map_id": map_id,
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
        print(f"DEBUG POST MATCH: {match_resp.status_code} for {match_id}", flush=True)
        return None
    try:
        db_manager.save_match_details_json(match_id, match_resp.text)
    except Exception as cache_err:
        print(f"FAILED TO CACHE RAW MATCH DETAILS: {cache_err}", flush=True)
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

    print(f"DEBUG RR: local={local_resp.status_code} updates={updates_resp.status_code}", flush=True)
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

    print(f"DEBUG MMR UPDATE: local={local_resp.status_code} updates={updates_resp.status_code}", flush=True)
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
    token_resp = await client.get(f"{local_url}/entitlements/v1/token", headers=local_headers)
    if token_resp.status_code != 200:
        return None

    token_data = token_resp.json()
    access_token = token_data.get("accessToken")
    entitlements_token = token_data.get("token")
    client_version = "release-12.11-shipping-9-4815575"
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
        print(f"DEBUG NAME SERVICE: status={names_resp.status_code}", flush=True)
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
    except Exception as e:
        print(f"DEBUG NAME SERVICE EXCEPTION: {str(e)}", flush=True)
        return {}


def format_duration_from_millis(duration_ms) -> str:
    """
    Formats a millisecond duration as Xm Ys.
    """
    total_seconds = int(_number_or_zero(duration_ms) / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"


def build_round_player_metrics(round_results: list, player_puuids: list[str]) -> dict:
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

        if first_kill:
            if first_kill["killer"] in metrics:
                metrics[first_kill["killer"]]["first_kills"] += 1
            if first_kill["victim"] in metrics:
                metrics[first_kill["victim"]]["first_deaths"] += 1

        for puuid in player_puuids:
            kill_count = kills_by_player.get(puuid, 0)
            if kill_count >= 2 and puuid in metrics:
                metrics[puuid]["multi_kills"] += 1
            if puuid in metrics and (kill_count > 0 or assists_by_player.get(puuid, 0) > 0 or puuid not in deaths):
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
        print(f"DEBUG DB: saved match {match_id} ({match_data['win_loss']}, {match_data['rr_change']} RR)", flush=True)
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
                            
                            client_version = "release-12.11-shipping-9-4815575"
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
                    except Exception as token_err:
                        print("FAILED TO ACQUIRE GLZ TOKENS:", str(token_err))
                
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
                                api_client = HenrikDevClient(api_key=HENRIK_API_KEY)
                                
                                all_players_data = []
                                for p in players_list:
                                    p_puuid = p.get("Subject")
                                    p_agent_id = p.get("CharacterID", "")
                                    p_agent_name = AGENT_MAPPING.get(p_agent_id, "Unknown Agent")
                                    p_name = names_map.get(p_puuid, "Unknown Player")
                                    
                                    cache_key = f"{p_puuid}_{tracker_state['queue_id']}"
                                    if cache_key in stats_cache:
                                        p_stats = stats_cache[cache_key]
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
                    except Exception as e:
                        print("PREGAME EXCEPTION:", str(e))
                        
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
                                api_client = HenrikDevClient(api_key=HENRIK_API_KEY)
                                
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
                    except Exception as e:
                        print("CORE-GAME EXCEPTION:", str(e))
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
                            enrich_match_assets(summary)
                            tracker_state["last_match"] = summary
                            tracker_state["last_match_status"] = "available"
                            persist_completed_match(summary, puuid, tracker_state.get("player_name", "Unknown"))
                        else:
                            tracker_state["last_match_status"] = "loading"
                    except Exception as e:
                        tracker_state["last_match_status"] = "loading"
                        print("POST-MATCH EXCEPTION:", str(e))
                else:
                    tracker_state["allies"] = []
                    tracker_state["enemies"] = []
                    
        except Exception:
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
    db_manager.init_db()
    refresh_session_summary()
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


@app.get("/api/career")
async def get_career() -> dict:
    """
    Retrieves career history and aggregate stats for the current account.

    @return: Career summary for the active PUUID.
    """
    puuid = tracker_state.get("puuid", "")
    career = db_manager.get_career_summary(puuid)
    recent_matches = []
    current_rank = ""
    for match in career["recent_matches"]:
        match["map_id"] = match.get("map", "")
        match["won"] = match.get("win_loss") == "WIN"
        match["result"] = "VICTORY" if match["won"] else "DEFEAT"
        match["scoreline"] = ""
        enrich_match_assets(match)
        if not current_rank and match.get("rank_after"):
            current_rank = match["rank_after"]
        recent_matches.append(match)

    career["recent_matches"] = recent_matches
    career["puuid"] = puuid
    career["player_name"] = tracker_state.get("player_name", "Unknown")
    career["current_rank"] = current_rank
    rank_assets = asset_manager.rank(current_rank)
    career["current_rank_icon_url"] = rank_assets.get("large") or rank_assets.get("small", "")
    career["tracker_score"] = calculate_tracker_score(
        career["avg_kd"],
        career["avg_hs_percent"],
        career["avg_acs"],
        current_rank or "Unranked",
        current_rank or "Unranked"
    ) if career["matches"] else 0
    return career


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
            
        local_player = next((p for p in players if (p.get("subject") or p.get("Subject")) == anchor_puuid), None)
        ally_team_id = None
        if local_player:
            ally_team_id = local_player.get("teamId") or local_player.get("TeamID") or local_player.get("teamID")
        if not ally_team_id and players:
            ally_team_id = players[0].get("teamId") or players[0].get("TeamID") or players[0].get("teamID")
            
        # Determine team scores & result
        ally_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) == ally_team_id), {})
        enemy_team = next((t for t in teams if (t.get("teamId") or t.get("TeamID")) != ally_team_id), {})
        
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
        round_metric_map = build_round_player_metrics(round_results, player_puuids)
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
            
            tracker_score = calculate_tracker_score(
                kills / max(deaths, 1),
                hs_percent,
                acs,
                rank,
                rank
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
                "score": tracker_score,
                "is_self": p_puuid == anchor_puuid
            }
            
            enrich_player_assets(player_info)
            
            if p_team_id == ally_team_id:
                allies_list.append(player_info)
            else:
                enemies_list.append(player_info)
                
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
        page_size = 20
        for start_index in range(0, max_scan, page_size):
            end_index = start_index + page_size
            updates_resp = await client.get(
                f"{pd_url}/mmr/v1/players/{puuid}/competitiveupdates?startIndex={start_index}&endIndex={end_index}",
                headers=remote_headers
            )
            if updates_resp.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Riot MMR updates returned {updates_resp.status_code}.",
                    "body": updates_resp.text[:300],
                    "start_index": start_index,
                    "end_index": end_index
                }
            page_matches = updates_resp.json().get("Matches", [])
            if not page_matches:
                break
            updates.extend(page_matches)
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
        with open("lcu_debug_output.json", "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
            
        return res
