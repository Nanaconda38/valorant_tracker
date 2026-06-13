import sqlite3
from pathlib import Path

class DatabaseManager:
    """
    Manages the SQLite database for local matchmaking tracking.
    """

    def __init__(self, db_path: str = "tracker.db"):
        """
        Initializes the DatabaseManager with the database path.

        @param db_path: Path to the SQLite database file.
        """
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """
        Opens a SQLite connection with row access by column name.

        @return: SQLite connection.
        """
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """
        Initializes the database schema if it does not exist.
        """
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS my_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL UNIQUE,
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
                    kda REAL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_my_matches_date ON my_matches(date)")
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
                INSERT OR IGNORE INTO my_matches (
                    match_id, date, gamemode, map, agent, win_loss, rr_change,
                    acs, kd, hs_percent, kills, deaths, assists, score, kda
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                    float(match_data.get("kda") or 0)
                )
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def get_session_summary(self, since: str) -> dict:
        """
        Calculates wins, losses, and RR delta since a given ISO datetime.

        @param since: ISO datetime string for the session start.
        @return: Session summary dictionary.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN win_loss = 'WIN' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN win_loss = 'LOSS' THEN 1 ELSE 0 END) AS losses,
                    COALESCE(SUM(rr_change), 0) AS rr_delta
                FROM my_matches
                WHERE date >= ?
                """,
                (since,)
            ).fetchone()
        finally:
            conn.close()

        return {
            "wins": int(row["wins"] or 0),
            "losses": int(row["losses"] or 0),
            "rr_delta": int(row["rr_delta"] or 0)
        }
