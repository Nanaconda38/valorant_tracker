import csv
import sys
from pathlib import Path

PROJECT_DIR = Path(r"c:\Users\naelc\PycharmProjects\valorant_tracker")
sys.path.insert(0, str(PROJECT_DIR))

from app import calculate_tracker_score

CSV_PATH = PROJECT_DIR / "data" / "tracker_score_samples.csv"

print("Checking predictions for fracture_14_12...")
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["sample_id"] == "fracture_14_12":
            left, right = [int(x) for x in r["scoreline"].split("-")]
            won = r["team_result"] == "WIN"
            pred = calculate_tracker_score(
                kd=float(r["kd"]),
                hs_percent=float(r["hs_percent"]),
                acs=int(r["acs"]),
                rank=r["player_rank"],
                peak_rank=r["player_rank"],
                adr=float(r["adr"]),
                dda=float(r["dda"]),
                kast=float(r["kast_percent"]),
                kills=int(r["k"]),
                deaths=int(r["d"]),
                assists=int(r["a"]),
                fk=int(r["fk"]),
                fd=int(r["fd"]),
                mk=int(r["mk"]),
                rounds_played=left + right,
                won=won,
                team_rounds=left if r["team"] == "A" else right,
                enemy_rounds=right if r["team"] == "A" else left,
                avg_rank=r["avg_rank"]
            )
            print(f"Player: {r['player_rank']:12s} | Team: {r['team']} | Actual: {r['trs']:3s} | Pred: {pred:<3d} | Diff: {pred - int(r['trs']):+d}")
