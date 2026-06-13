import os
import asyncio
import base64
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY", "").strip() or None

app = FastAPI(title="Valorant Local Tracker")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

tracker_state = {
    "status": "offline",
    "player_name": "Unknown",
    "puuid": "",
    "game_phase": "OFFLINE",
    "queue_id": "",
    "map_id": "",
    "allies": [],
    "enemies": []
}

stats_cache = {}
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
    Invalidates cached stats when the active game context changes.
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
        clear_stats_cache(reason)
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
                refresh_stats_cache_context()
                await asyncio.sleep(3)
                continue
                
            port = lockfile_info["port"]
            protocol = lockfile_info["protocol"]
            headers = lockfile_info["headers"]
            url = f"{protocol}://127.0.0.1:{port}"
            
            async with httpx.AsyncClient(verify=False, timeout=2.0) as client:
                try:
                    session_resp = await client.get(f"{url}/chat/v1/session", headers=headers)
                    if session_resp.status_code != 200:
                        tracker_state["status"] = "searching_game"
                        tracker_state["game_phase"] = "OFFLINE"
                        tracker_state["allies"] = []
                        tracker_state["enemies"] = []
                        refresh_stats_cache_context()
                        await asyncio.sleep(3)
                        continue
                        
                    session_data = session_resp.json()
                    puuid = session_data.get("puuid")
                    game_name = session_data.get("game_name", "")
                    game_tag = session_data.get("game_tag", "")
                    
                    tracker_state["puuid"] = puuid
                    tracker_state["player_name"] = f"{game_name}#{game_tag}"
                    tracker_state["status"] = "connected"
                except (httpx.ConnectError, httpx.TimeoutException):
                    tracker_state["status"] = "searching_game"
                    tracker_state["game_phase"] = "OFFLINE"
                    tracker_state["allies"] = []
                    tracker_state["enemies"] = []
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
                if tracker_state["game_phase"] in ("PREGAME", "CORE-GAME"):
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
                                        
                                    new_allies.append({
                                        "puuid": player["puuid"],
                                        "name": player["name"],
                                        "agent": player["agent"],
                                        "rank": player["rank"],
                                        "peak_rank": player["peak_rank"],
                                        "kd": player["kd"],
                                        "hs_percent": player["hs_percent"],
                                        "acs": player["acs"],
                                        "badge": badge,
                                        "score": score,
                                        "group_id": p_grp
                                    })
                                tracker_state["allies"] = new_allies
                                tracker_state["enemies"] = []
                    except Exception as e:
                        print("PREGAME EXCEPTION:", str(e))
                        
                elif tracker_state["game_phase"] == "CORE-GAME" and remote_headers:
                    try:
                        core_player_resp = await client.get(f"{glz_url}/core-game/v1/players/{puuid}", headers=remote_headers)
                        if core_player_resp.status_code == 200:
                            match_id = core_player_resp.json().get("MatchID")
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
                                    
                                    if player["team"] == ally_team_id:
                                        new_allies.append(player_info)
                                    else:
                                        new_enemies.append(player_info)
                                        
                                tracker_state["allies"] = new_allies
                                tracker_state["enemies"] = new_enemies
                    except Exception as e:
                        print("CORE-GAME EXCEPTION:", str(e))
                else:
                    tracker_state["allies"] = []
                    tracker_state["enemies"] = []
                    clear_stats_cache("left active match phase")
                    
        except Exception:
            tracker_state["status"] = "offline"
            tracker_state["game_phase"] = "OFFLINE"
            tracker_state["allies"] = []
            tracker_state["enemies"] = []
            refresh_stats_cache_context()
            
        await asyncio.sleep(3)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Fires on startup to initialize the background scanning task.
    """
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

