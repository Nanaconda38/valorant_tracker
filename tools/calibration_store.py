import argparse
import csv
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path("tracker.db")
DEFAULT_CSV_PATH = Path("data/tracker_score_samples.csv")
DEFAULT_TABLE_NAME = "tracker_score_samples"

CSV_FIELDS = [
    "sample_id",
    "map",
    "scoreline",
    "team",
    "team_result",
    "avg_rank",
    "player_rank",
    "trs",
    "acs",
    "k",
    "d",
    "a",
    "plus_minus",
    "kd",
    "dda",
    "adr",
    "hs_percent",
    "kast_percent",
    "fk",
    "fd",
    "mk",
    "source_image",
]


IDENTITY_FIELDS = [
    "map",
    "scoreline",
    "team",
    "team_result",
    "avg_rank",
    "player_rank",
    "trs",
    "acs",
    "k",
    "d",
    "a",
    "plus_minus",
    "kd",
    "dda",
    "adr",
    "hs_percent",
    "kast_percent",
    "fk",
    "fd",
    "mk",
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def validate_table_name(table_name: str) -> str:
    if not table_name.replace("_", "").isalnum() or table_name[0].isdigit():
        raise ValueError(f"Unsafe table name: {table_name}")
    return table_name


def ensure_schema(conn: sqlite3.Connection, table_name: str = DEFAULT_TABLE_NAME) -> None:
    table_name = validate_table_name(table_name)
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identity_hash TEXT NOT NULL UNIQUE,
            batch_id TEXT NOT NULL,
            sample_id TEXT,
            map TEXT,
            scoreline TEXT,
            team TEXT,
            team_result TEXT,
            avg_rank TEXT,
            player_rank TEXT,
            trs INTEGER,
            acs INTEGER,
            k INTEGER,
            d INTEGER,
            a INTEGER,
            plus_minus INTEGER,
            kd REAL,
            dda REAL,
            adr REAL,
            hs_percent REAL,
            kast_percent REAL,
            fk INTEGER,
            fd INTEGER,
            mk INTEGER,
            source_image TEXT,
            imported_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_tracker_score_samples_batch
        ON {table_name}(batch_id)
        """
    )
    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_tracker_score_samples_sample
        ON {table_name}(sample_id)
        """
    )
    conn.commit()


def clean_row(row: dict) -> dict:
    cleaned = {field: str(row.get(field, "") or "").strip() for field in CSV_FIELDS}
    return cleaned


def identity_hash(row: dict) -> str:
    payload = "\x1f".join(str(row.get(field, "")).strip() for field in IDENTITY_FIELDS)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def import_csv(csv_path: Path, db_path: Path, batch_id: str, table_name: str = DEFAULT_TABLE_NAME) -> tuple[int, int]:
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    imported_at = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0

    with connect(db_path) as conn:
        table_name = validate_table_name(table_name)
        ensure_schema(conn, table_name)
        for raw_row in rows:
            row = clean_row(raw_row)
            cursor = conn.execute(
                f"""
                INSERT OR IGNORE INTO {table_name} (
                    identity_hash, batch_id, sample_id, map, scoreline, team,
                    team_result, avg_rank, player_rank, trs, acs, k, d, a,
                    plus_minus, kd, dda, adr, hs_percent, kast_percent,
                    fk, fd, mk, source_image, imported_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity_hash(row),
                    batch_id,
                    row["sample_id"],
                    row["map"],
                    row["scoreline"],
                    row["team"],
                    row["team_result"],
                    row["avg_rank"],
                    row["player_rank"],
                    to_int(row["trs"]),
                    to_int(row["acs"]),
                    to_int(row["k"]),
                    to_int(row["d"]),
                    to_int(row["a"]),
                    to_int(row["plus_minus"]),
                    to_float(row["kd"]),
                    to_float(row["dda"]),
                    to_float(row["adr"]),
                    to_float(row["hs_percent"]),
                    to_float(row["kast_percent"]),
                    to_int(row["fk"]),
                    to_int(row["fd"]),
                    to_int(row["mk"]),
                    row["source_image"],
                    imported_at,
                ),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1
        conn.commit()

    return inserted, skipped


def export_csv(db_path: Path, csv_path: Path, table_name: str = DEFAULT_TABLE_NAME) -> int:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        table_name = validate_table_name(table_name)
        ensure_schema(conn, table_name)
        rows = conn.execute(
            f"""
            SELECT
                sample_id, map, scoreline, team, team_result, avg_rank, player_rank,
                trs, acs, k, d, a, plus_minus, kd, dda, adr,
                hs_percent, kast_percent, fk, fd, mk, source_image
            FROM {table_name}
            ORDER BY id
            """
        ).fetchall()

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(dict(row) for row in rows)
    return len(rows)


def count_by_batch(db_path: Path, table_name: str = DEFAULT_TABLE_NAME) -> list[sqlite3.Row]:
    with connect(db_path) as conn:
        table_name = validate_table_name(table_name)
        ensure_schema(conn, table_name)
        return conn.execute(
            f"""
            SELECT batch_id, COUNT(*) AS samples
            FROM {table_name}
            GROUP BY batch_id
            ORDER BY MIN(id)
            """
        ).fetchall()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import/export Tracker Score calibration samples.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    import_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    import_parser.add_argument("--batch-id", required=True)
    import_parser.add_argument("--table", default=DEFAULT_TABLE_NAME)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    export_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    export_parser.add_argument("--table", default=DEFAULT_TABLE_NAME)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    summary_parser.add_argument("--table", default=DEFAULT_TABLE_NAME)

    args = parser.parse_args()
    if args.command == "import":
        inserted, skipped = import_csv(args.csv, args.db, args.batch_id, args.table)
        print(f"imported={inserted} skipped={skipped} db={args.db} table={args.table}")
    elif args.command == "export":
        exported = export_csv(args.db, args.csv, args.table)
        print(f"exported={exported} csv={args.csv}")
    elif args.command == "summary":
        for row in count_by_batch(args.db, args.table):
            print(f"{row['batch_id']}: {row['samples']}")


if __name__ == "__main__":
    main()
