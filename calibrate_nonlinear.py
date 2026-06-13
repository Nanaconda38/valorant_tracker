import csv
import math
import os
import sys
from pathlib import Path

# Setup paths
PROJECT_DIR = Path(__file__).parent
CSV_PATH = PROJECT_DIR / "data" / "tracker_score_samples.csv"

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
    "Radiant",
]

def number(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def rank_index(rank_name: str) -> int:
    clean = (rank_name or "").lower()
    for index, rank in enumerate(RANKS):
        if rank.lower() in clean:
            return index
    return 0

def parse_scoreline(scoreline: str) -> tuple[int, int]:
    left, right = scoreline.split("-", 1)
    return int(left), int(right)

def feature_row(row: dict) -> list[float]:
    left, right = parse_scoreline(row["scoreline"])
    team_rounds = left if row["team"] == "A" else right
    enemy_rounds = right if row["team"] == "A" else left
    rounds = max(left + right, 1)
    won = 1.0 if row["team_result"] == "WIN" else 0.0
    round_diff = (team_rounds - enemy_rounds) / rounds
    
    kills = number(row["k"])
    deaths = number(row["d"])
    assists = number(row["a"])
    fk = number(row["fk"])
    fd = number(row["fd"])
    mk = number(row["mk"])
    acs = number(row["acs"])
    adr = number(row["adr"])
    dda = number(row["dda"])
    kd = number(row["kd"])
    hs = number(row["hs_percent"]) / 100.0
    kast = number(row["kast_percent"]) / 100.0
    
    kills_per_round = kills / rounds
    deaths_per_round = deaths / rounds
    assists_per_round = assists / rounds
    fk_per_round = fk / rounds
    fd_per_round = fd / rounds
    mk_per_round = mk / rounds
    
    player_rank_idx = rank_index(row["player_rank"])
    avg_rank_idx = rank_index(row.get("avg_rank", ""))
    rank_delta = player_rank_idx - avg_rank_idx
    rank_delta_scaled = rank_delta / 25.0
    positive_rank_delta = max(0.0, rank_delta_scaled)
    negative_rank_delta = min(0.0, rank_delta_scaled)
    plus_minus = kills - deaths
    log_kill_death = math.log1p(max(kills, 0)) - math.log1p(max(deaths, 0))

    return [
        acs,
        adr,
        dda,
        kd,
        plus_minus,
        hs,
        kast,
        fk_per_round,
        fd_per_round,
        mk_per_round,
        assists_per_round,
        kills_per_round,
        deaths_per_round,
        won,
        round_diff,
        player_rank_idx,
        avg_rank_idx,
        rank_delta,
        log_kill_death
    ]

FEATURE_NAMES = [
    "acs",
    "adr",
    "dda",
    "kd",
    "plus_minus",
    "hs_rate",
    "kast_rate",
    "fk_per_round",
    "fd_per_round",
    "mk_per_round",
    "assists_per_round",
    "kills_per_round",
    "deaths_per_round",
    "won",
    "round_diff",
    "player_rank_idx",
    "avg_rank_idx",
    "rank_delta",
    "log_kill_death"
]

def load_data():
    with open(CSV_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        samples = list(reader)
    
    x = [feature_row(row) for row in samples]
    y = [number(row["trs"]) for row in samples]
    return x, y, samples

def export_tree_to_python(tree, feature_names):
    left = tree.tree_.children_left
    right = tree.tree_.children_right
    threshold = tree.tree_.threshold
    features = tree.tree_.feature
    value = tree.tree_.value

    def recurse(node, depth):
        indent = "    " * depth
        if left[node] == -1: # Leaf node
            val = value[node][0][0]
            return f"{indent}return {val:.6f}\n"
        else:
            name = feature_names[features[node]]
            thresh = threshold[node]
            left_str = recurse(left[node], depth + 1)
            right_str = recurse(right[node], depth + 1)
            return (
                f"{indent}if {name} <= {thresh:.6f}:\n"
                f"{left_str}"
                f"{indent}else:\n"
                f"{right_str}"
            )
            
    return recurse(0, 2)

def export_gbr_to_python(gbr, feature_names):
    init_val = gbr.init_.constant_[0][0]
    lr = gbr.learning_rate
    
    code = []
    code.append("def predict_trs_raw(stats: dict) -> float:\n")
    for name in feature_names:
        code.append(f"    {name} = stats.get('{name}', 0.0)\n")
        
    code.append(f"    score = {init_val:.6f}\n\n")
    
    for idx, estimator in enumerate(gbr.estimators_[:, 0]):
        tree_code = export_tree_to_python(estimator, feature_names)
        code.append(f"    def tree_{idx}():\n")
        code.append(tree_code)
        code.append(f"    score += {lr:.6f} * tree_{idx}()\n\n")
        
    code.append("    return score\n")
    return "".join(code)

def main():
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.model_selection import KFold
    from sklearn.metrics import mean_absolute_error
    import numpy as np
        
    x, y, samples = load_data()
    X = np.array(x)
    Y = np.array(y)
    
    print(f"Loaded {len(X)} samples with {len(FEATURE_NAMES)} features.")
    
    # 5-fold CV
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    best_mae = 999.0
    best_config = None
    best_model = None
    
    # Grid search over GBR hyperparameters
    for n_est in [20, 30, 50, 100]:
        for depth in [3, 4, 5, 6]:
            for lr in [0.05, 0.1, 0.2]:
                model = GradientBoostingRegressor(n_estimators=n_est, max_depth=depth, learning_rate=lr, random_state=42)
                
                maes = []
                for train_idx, test_idx in kf.split(X):
                    X_train, X_test = X[train_idx], X[test_idx]
                    Y_train, Y_test = Y[train_idx], Y[test_idx]
                    
                    model.fit(X_train, Y_train)
                    pred = np.clip(np.round(model.predict(X_test)), 100, 999)
                    maes.append(mean_absolute_error(Y_test, pred))
                    
                mean_mae = np.mean(maes)
                if mean_mae < best_mae:
                    best_mae = mean_mae
                    best_config = (n_est, depth, lr)
                    best_model = model
                    
    print(f"Best GBR Config: n_estimators={best_config[0]}, max_depth={best_config[1]}, learning_rate={best_config[2]} | CV MAE: {best_mae:.2f}")
    
    # Also search Random Forest
    rf_best_mae = 999.0
    rf_best_config = None
    for n_est in [20, 50, 100]:
        for depth in [5, 7, 9, 12]:
            model = RandomForestRegressor(n_estimators=n_est, max_depth=depth, random_state=42)
            maes = []
            for train_idx, test_idx in kf.split(X):
                X_train, X_test = X[train_idx], X[test_idx]
                Y_train, Y_test = Y[train_idx], Y[test_idx]
                
                model.fit(X_train, Y_train)
                pred = np.clip(np.round(model.predict(X_test)), 100, 999)
                maes.append(mean_absolute_error(Y_test, pred))
            mean_mae = np.mean(maes)
            if mean_mae < rf_best_mae:
                rf_best_mae = mean_mae
                rf_best_config = (n_est, depth)
                
    print(f"Best RF Config: n_estimators={rf_best_config[0]}, max_depth={rf_best_config[1]} | CV MAE: {rf_best_mae:.2f}")
    
    # Train final best model (GBR) on 100% of data
    print(f"\nTraining final model with best GBR configuration: n_estimators={best_config[0]}, max_depth={best_config[1]}, learning_rate={best_config[2]}")
    model = GradientBoostingRegressor(n_estimators=best_config[0], max_depth=best_config[1], learning_rate=best_config[2], random_state=42)
    model.fit(X, Y)
    
    train_pred = np.clip(np.round(model.predict(X)), 100, 999)
    train_mae = mean_absolute_error(Y, train_pred)
    train_rmse = np.sqrt(np.mean((Y - train_pred)**2))
    print(f"Final Model Train MAE: {train_mae:.2f} | Train RMSE: {train_rmse:.2f}")
    
    # Sort samples by absolute error to find worst errors
    errors = np.abs(Y - train_pred)
    worst_indices = np.argsort(errors)[::-1][:10]
    print("\nWorst errors on final model:")
    for idx in worst_indices:
        r = samples[idx]
        print(f"  {r['sample_id']:40s} | Actual TRS: {int(Y[idx]):<3d} | Pred: {int(train_pred[idx]):<3d} | Err: {int(Y[idx] - train_pred[idx]):+d}")
        
    # Export model to code
    py_code = export_gbr_to_python(model, FEATURE_NAMES)
    output_code_path = PROJECT_DIR / "data" / "predict_trs_generated.py"
    with open(output_code_path, "w", encoding="utf-8") as f:
        f.write(py_code)
    print(f"\nSaved pure Python GBR formula code to {output_code_path}")

if __name__ == "__main__":
    main()
