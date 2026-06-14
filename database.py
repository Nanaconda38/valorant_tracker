import sqlite3
from pathlib import Path

from app_logging import get_logger
from app_paths import database_path


logger = get_logger(__name__)

class DatabaseManager:
    """
    Manages the SQLite database for local matchmaking tracking.
    """

    def __init__(self, db_path: str | Path | None = None):
        """
        Initializes the DatabaseManager with the database path.

        @param db_path: Path to the SQLite database file.
        """
        self.db_path = str(db_path or database_path())

    def _connect(self) -> sqlite3.Connection:
        """
        Opens a SQLite connection with row access by column name.

        @return: SQLite connection.
        """
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _select_or_default(self, existing_columns: set, column: str, default_sql: str) -> str:
        """
        Returns a selectable column or a SQL default expression for migrations.

        @param existing_columns: Existing source table columns.
        @param column: Desired column name.
        @param default_sql: SQL expression used when the column is missing.
        @return: SQL select expression.
        """
        return column if column in existing_columns else f"{default_sql} AS {column}"

    def init_db(self) -> None:
        """
        Initializes the database schema if it does not exist.
        """
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS my_matches_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    puuid TEXT NOT NULL,
                    player_name TEXT,
                    match_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    gamemode TEXT,
                    map TEXT,
                    agent TEXT,
                    win_loss TEXT,
                    rr_change INTEGER DEFAULT 0,
                    acs INTEGER,
                    kd REAL,
                    hs_percent REAL,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    score INTEGER,
                    kda REAL,
                    rank_before TEXT,
                    rank_after TEXT,
                    rankup INTEGER DEFAULT 0,
                    rr_before INTEGER,
                    rr_after INTEGER,
                    season_id TEXT,
                    UNIQUE(puuid, match_id)
                )
                """
            )
            existing_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(my_matches)").fetchall()
            }
            if existing_columns:
                player_name_sql = self._select_or_default(existing_columns, "player_name", "NULL")
                rank_before_sql = self._select_or_default(existing_columns, "rank_before", "NULL")
                rank_after_sql = self._select_or_default(existing_columns, "rank_after", "NULL")
                rankup_sql = self._select_or_default(existing_columns, "rankup", "0")
                rr_before_sql = self._select_or_default(existing_columns, "rr_before", "NULL")
                rr_after_sql = self._select_or_default(existing_columns, "rr_after", "NULL")
                season_id_sql = self._select_or_default(existing_columns, "season_id", "NULL")
                conn.execute(
                    f"""
                    INSERT OR IGNORE INTO my_matches_v2 (
                        puuid, player_name, match_id, date, gamemode, map, agent,
                        win_loss, rr_change, acs, kd, hs_percent, kills, deaths,
                        assists, score, kda, rank_before, rank_after, rankup,
                        rr_before, rr_after, season_id
                    )
                    SELECT
                        COALESCE(NULLIF(puuid, ''), 'legacy') AS puuid,
                        {player_name_sql},
                        match_id,
                        date,
                        gamemode,
                        map,
                        agent,
                        win_loss,
                        rr_change,
                        acs,
                        kd,
                        hs_percent,
                        kills,
                        deaths,
                        assists,
                        score,
                        kda,
                        {rank_before_sql},
                        {rank_after_sql},
                        {rankup_sql},
                        {rr_before_sql},
                        {rr_after_sql},
                        {season_id_sql}
                    FROM my_matches
                    """
                    if "puuid" in existing_columns
                    else
                    f"""
                    INSERT OR IGNORE INTO my_matches_v2 (
                        puuid, player_name, match_id, date, gamemode, map, agent,
                        win_loss, rr_change, acs, kd, hs_percent, kills, deaths,
                        assists, score, kda, rank_before, rank_after, rankup,
                        rr_before, rr_after, season_id
                    )
                    SELECT
                        'legacy' AS puuid,
                        NULL AS player_name,
                        match_id,
                        date,
                        gamemode,
                        map,
                        agent,
                        win_loss,
                        rr_change,
                        acs,
                        kd,
                        hs_percent,
                        kills,
                        deaths,
                        assists,
                        score,
                        kda,
                        {rank_before_sql},
                        {rank_after_sql},
                        {rankup_sql},
                        {rr_before_sql},
                        {rr_after_sql},
                        {season_id_sql}
                    FROM my_matches
                    """
                )
                conn.execute("DROP TABLE my_matches")
                conn.execute("ALTER TABLE my_matches_v2 RENAME TO my_matches")
            else:
                conn.execute("ALTER TABLE my_matches_v2 RENAME TO my_matches")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS my_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    puuid TEXT NOT NULL,
                    player_name TEXT,
                    match_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    gamemode TEXT,
                    map TEXT,
                    agent TEXT,
                    win_loss TEXT,
                    rr_change INTEGER DEFAULT 0,
                    acs INTEGER,
                    kd REAL,
                    hs_percent REAL,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    score INTEGER,
                    kda REAL,
                    rank_before TEXT,
                    rank_after TEXT,
                    rankup INTEGER DEFAULT 0,
                    rr_before INTEGER,
                    rr_after INTEGER,
                    season_id TEXT,
                    UNIQUE(puuid, match_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_my_matches_date ON my_matches(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_my_matches_puuid_date ON my_matches(puuid, date)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS match_details_cache (
                    match_id TEXT PRIMARY KEY,
                    raw_json TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def save_match(self, match_data: dict) -> bool:
        """
        Saves a match history entry into the database.

        @param match_data: Dictionary containing match details to persist.
        @return: True if the match was inserted, False if it already existed.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO my_matches (
                    puuid, player_name, match_id, date, gamemode, map, agent,
                    win_loss, rr_change, acs, kd, hs_percent, kills, deaths,
                    assists, score, kda, rank_before, rank_after, rankup,
                    rr_before, rr_after, season_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(puuid, match_id) DO UPDATE SET
                    player_name = excluded.player_name,
                    date = excluded.date,
                    gamemode = excluded.gamemode,
                    map = excluded.map,
                    agent = excluded.agent,
                    win_loss = excluded.win_loss,
                    rr_change = excluded.rr_change,
                    acs = excluded.acs,
                    kd = excluded.kd,
                    hs_percent = excluded.hs_percent,
                    kills = excluded.kills,
                    deaths = excluded.deaths,
                    assists = excluded.assists,
                    score = excluded.score,
                    kda = excluded.kda,
                    rank_before = excluded.rank_before,
                    rank_after = excluded.rank_after,
                    rankup = excluded.rankup,
                    rr_before = excluded.rr_before,
                    rr_after = excluded.rr_after,
                    season_id = COALESCE(excluded.season_id, my_matches.season_id)
                """,
                (
                    match_data.get("puuid"),
                    match_data.get("player_name"),
                    match_data.get("match_id"),
                    match_data.get("date"),
                    match_data.get("gamemode"),
                    match_data.get("map"),
                    match_data.get("agent"),
                    match_data.get("win_loss"),
                    int(match_data.get("rr_change") or 0),
                    int(match_data.get("acs") or 0),
                    float(match_data.get("kd") or 0),
                    float(match_data.get("hs_percent") or 0),
                    int(match_data.get("kills") or 0),
                    int(match_data.get("deaths") or 0),
                    int(match_data.get("assists") or 0),
                    int(match_data.get("score") or 0),
                    float(match_data.get("kda") or 0),
                    match_data.get("rank_before"),
                    match_data.get("rank_after"),
                    1 if match_data.get("rankup") else 0,
                    match_data.get("rr_before"),
                    match_data.get("rr_after"),
                    match_data.get("season_id")
                )
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def get_session_summary(self, since: str, puuid: str = "") -> dict:
        """
        Calculates wins, losses, and RR delta since a given ISO datetime.

        @param since: ISO datetime string for the session start.
        @param puuid: Optional account PUUID to filter the session.
        @return: Session summary dictionary.
        """
        conn = self._connect()
        try:
            where_clause = "date >= ?"
            params = [since]
            if puuid:
                where_clause += " AND puuid = ?"
                params.append(puuid)

            row = conn.execute(
                f"""
                SELECT
                    SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN win_loss = 'LOSS' THEN 1 ELSE 0 END) AS losses,
                    COALESCE(SUM(rr_change), 0) AS rr_delta
                FROM my_matches
                WHERE {where_clause}
                """,
                params
            ).fetchone()
        finally:
            conn.close()

        return {
            "wins": int(row["wins"] or 0),
            "losses": int(row["losses"] or 0),
            "rr_delta": int(row["rr_delta"] or 0)
        }

    def match_exists(self, puuid: str, match_id: str) -> bool:
        """
        Checks whether a match is already saved for a specific account.

        @param puuid: Account PUUID.
        @param match_id: Riot match id.
        @return: True when the row already exists.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM my_matches WHERE puuid = ? AND match_id = ? LIMIT 1",
                (puuid, match_id)
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    def get_career_summary(self, puuid: str, limit: int = 20) -> dict:
        """
        Returns aggregate and recent match history for a player account.

        @param puuid: Account PUUID.
        @param limit: Number of recent matches to include.
        @return: Career summary dictionary.
        """
        if not puuid:
            return {
                "matches": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "rr_delta": 0,
                "avg_acs": 0,
                "avg_kd": 0,
                "avg_hs_percent": 0,
                "recent_matches": []
            }

        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS matches,
                    SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN win_loss = 'LOSS' THEN 1 ELSE 0 END) AS losses,
                    COALESCE(SUM(rr_change), 0) AS rr_delta,
                    COALESCE(AVG(acs), 0) AS avg_acs,
                    COALESCE(AVG(kd), 0) AS avg_kd,
                    COALESCE(AVG(hs_percent), 0) AS avg_hs_percent
                FROM my_matches
                WHERE puuid = ?
                """,
                (puuid,)
            ).fetchone()
            recent_rows = conn.execute(
                """
                SELECT
                    match_id, date, gamemode, map, agent, win_loss, rr_change,
                    acs, kd, hs_percent, kills, deaths, assists, score, kda,
                    rank_before, rank_after, rankup, rr_before, rr_after, season_id
                FROM my_matches
                WHERE puuid = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (puuid, limit)
            ).fetchall()
        finally:
            conn.close()

        matches = int(row["matches"] or 0)
        wins = int(row["wins"] or 0)
        losses = int(row["losses"] or 0)
        return {
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "win_rate": round((wins / matches) * 100, 1) if matches else 0,
            "rr_delta": int(row["rr_delta"] or 0),
            "avg_acs": round(row["avg_acs"] or 0),
            "avg_kd": round(row["avg_kd"] or 0, 2),
            "avg_hs_percent": round(row["avg_hs_percent"] or 0, 1),
            "recent_matches": [dict(match) for match in recent_rows]
        }

    def save_match_details_json(self, match_id: str, raw_json: str) -> None:
        """
        Caches raw match details JSON.
        """
        import datetime
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO match_details_cache (match_id, raw_json, saved_at)
                VALUES (?, ?, ?)
                """,
                (match_id, raw_json, datetime.datetime.now(datetime.timezone.utc).isoformat())
            )
            conn.commit()
        except Exception:
            logger.exception("Failed to cache match details")
        finally:
            conn.close()

    def get_match_details_json(self, match_id: str) -> str | None:
        """
        Retrieves cached raw match details JSON.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT raw_json FROM match_details_cache WHERE match_id = ? LIMIT 1",
                (match_id,)
            ).fetchone()
            return row["raw_json"] if row else None
        except Exception:
            logger.exception("Failed to read cached match details")
            return None
        finally:
            conn.close()

    def get_matches_missing_season_id(self, limit: int = 500) -> list[dict]:
        """
        Returns saved matches that still need an Act id.
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT puuid, match_id, date, gamemode
                FROM my_matches
                WHERE season_id IS NULL OR season_id = ''
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception:
            logger.exception("Failed to list matches missing season id")
            return []
        finally:
            conn.close()

    def update_match_season_id(self, match_id: str, season_id: str, puuid: str = "", overwrite: bool = False) -> bool:
        """
        Stores the Valorant Act id for an existing match row.
        """
        if not match_id or not season_id:
            return False

        conn = self._connect()
        try:
            params = [season_id, match_id]
            where_clause = "match_id = ?"
            if puuid:
                where_clause += " AND puuid = ?"
                params.append(puuid)

            season_assignment = "season_id = ?"
            if not overwrite:
                where_clause += " AND (season_id IS NULL OR season_id = '')"

            cursor = conn.execute(
                f"""
                UPDATE my_matches
                SET {season_assignment}
                WHERE {where_clause}
                """,
                params
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            logger.exception("Failed to update match season id")
            return False
        finally:
            conn.close()
