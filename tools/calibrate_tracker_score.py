import csv
import math
import re
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold


DATASET_PATH = Path("data/tracker_score_samples.csv")
MODEL_PATH = Path("data/predict_trs_generated.py")

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

FEATURE_NAMES = [
    "acs",
    "adr",
    "dda",
    "positive_dda",
    "negative_dda",
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
    "log_kill_death",
    "rounds",
    "team_rounds",
    "enemy_rounds",
    "acs_kast",
    "adr_kast",
    "kd_kast",
    "acs_kd",
    "dda_kast",
    "plus_minus_per_round",
    "fk_fd_per_round",
    "adjusted_round_impact",
]

MODEL_PARAMS = {
    "n_estimators": 400,
    "learning_rate": 0.1,
    "max_depth": 4,
    "min_samples_leaf": 2,
    "subsample": 0.9,
    "random_state": 42,
}


def number(value: str | int | float | None) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rank_index(rank_name: str) -> int:
    clean = (rank_name or "").lower()
    roman_map = {"iii": "3", "ii": "2", "i": "1"}
    for rank_root in ["iron", "bronze", "silver", "gold", "platinum", "diamond", "ascendant", "immortal"]:
        clean = re.sub(
            rf"\b{rank_root}\s+(iii|ii|i)\b",
            lambda match: f"{rank_root} {roman_map[match.group(1)]}",
            clean,
        )
    for index, rank in enumerate(RANKS):
        if rank.lower() in clean:
            return index
    return 0


def parse_scoreline(scoreline: str) -> tuple[int, int]:
    left, right = scoreline.split("-", 1)
    return int(left), int(right)


def stats_from_row(row: dict) -> dict:
    score_a, score_b = parse_scoreline(row["scoreline"])
    team_rounds = score_a if row["team"] == "A" else score_b
    enemy_rounds = score_b if row["team"] == "A" else score_a
    rounds = max(score_a + score_b, 1)
    kills = number(row["k"])
    deaths = number(row["d"])
    player_rank_idx = rank_index(row["player_rank"])
    avg_rank_idx = rank_index(row.get("avg_rank", ""))

    return {
        "acs": number(row["acs"]),
        "adr": number(row["adr"]),
        "dda": number(row["dda"]),
        "kd": number(row["kd"]),
        "plus_minus": number(row["plus_minus"]),
        "hs_rate": number(row["hs_percent"]) / 100,
        "kast_rate": number(row["kast_percent"]) / 100,
        "fk_per_round": number(row["fk"]) / rounds,
        "fd_per_round": number(row["fd"]) / rounds,
        "mk_per_round": number(row["mk"]) / rounds,
        "assists_per_round": number(row["a"]) / rounds,
        "kills_per_round": kills / rounds,
        "deaths_per_round": deaths / rounds,
        "won": 1.0 if row["team_result"] == "WIN" else 0.0,
        "round_diff": (team_rounds - enemy_rounds) / rounds,
        "player_rank_idx": player_rank_idx,
        "avg_rank_idx": avg_rank_idx,
        "rank_delta": player_rank_idx - avg_rank_idx,
        "log_kill_death": math.log1p(max(kills, 0)) - math.log1p(max(deaths, 0)),
        "rounds": rounds,
        "team_rounds": team_rounds,
        "enemy_rounds": enemy_rounds,
    }


def feature_vector(stats: dict) -> list[float]:
    acs = number(stats.get("acs"))
    adr = number(stats.get("adr"))
    dda = number(stats.get("dda"))
    kd = number(stats.get("kd"))
    plus_minus = number(stats.get("plus_minus"))
    hs_rate = number(stats.get("hs_rate"))
    kast_rate = number(stats.get("kast_rate"))
    fk_per_round = number(stats.get("fk_per_round"))
    fd_per_round = number(stats.get("fd_per_round"))
    mk_per_round = number(stats.get("mk_per_round"))
    assists_per_round = number(stats.get("assists_per_round"))
    kills_per_round = number(stats.get("kills_per_round"))
    deaths_per_round = number(stats.get("deaths_per_round"))
    won = number(stats.get("won"))
    round_diff = number(stats.get("round_diff"))
    player_rank_idx = number(stats.get("player_rank_idx"))
    avg_rank_idx = number(stats.get("avg_rank_idx"))
    rank_delta = number(stats.get("rank_delta"))
    log_kill_death = number(stats.get("log_kill_death"))
    rounds = max(number(stats.get("rounds")), 1)
    team_rounds = number(stats.get("team_rounds"))
    enemy_rounds = number(stats.get("enemy_rounds"))

    return [
        acs,
        adr,
        dda,
        max(0.0, dda),
        min(0.0, dda),
        kd,
        plus_minus,
        hs_rate,
        kast_rate,
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
        log_kill_death,
        rounds,
        team_rounds,
        enemy_rounds,
        acs * kast_rate,
        adr * kast_rate,
        kd * kast_rate,
        acs * kd,
        dda * kast_rate,
        plus_minus / rounds,
        fk_per_round - fd_per_round,
        kills_per_round + 0.7 * assists_per_round - deaths_per_round,
    ]


def load_samples() -> list[dict]:
    with DATASET_PATH.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def clamp_score(values) -> np.ndarray:
    return np.clip(np.rint(values), 100, 1000)


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    errors = clamp_score(y_pred) - y_true
    abs_errors = np.abs(errors)
    return {
        "mae": float(np.mean(abs_errors)),
        "rmse": float(np.sqrt(np.mean(errors * errors))),
        "p95": float(np.percentile(abs_errors, 95)),
        "max": float(np.max(abs_errors)),
    }


def make_model(random_state: int = 42) -> GradientBoostingRegressor:
    return GradientBoostingRegressor(**{**MODEL_PARAMS, "random_state": random_state})


def cross_validate(x: np.ndarray, y: np.ndarray) -> dict:
    predictions = np.zeros_like(y)
    kfold = KFold(n_splits=5, shuffle=True, random_state=123)
    for train_index, test_index in kfold.split(x):
        model = make_model(random_state=123)
        model.fit(x[train_index], y[train_index])
        predictions[test_index] = model.predict(x[test_index])
    return evaluate(y, predictions)


def tree_to_tuple(tree, node_id: int = 0):
    left = int(tree.children_left[node_id])
    right = int(tree.children_right[node_id])
    if left == -1:
        return ("leaf", float(tree.value[node_id][0][0]))
    return (
        "node",
        int(tree.feature[node_id]),
        float(tree.threshold[node_id]),
        tree_to_tuple(tree, left),
        tree_to_tuple(tree, right),
    )


def format_tree(node, indent: str = "    ") -> str:
    kind = node[0]
    if kind == "leaf":
        return f"('leaf', {node[1]:.12f})"
    _, feature, threshold, left, right = node
    return (
        "('node', "
        f"{feature}, {threshold:.12f},\n"
        f"{indent}{format_tree(left, indent + '    ')},\n"
        f"{indent}{format_tree(right, indent + '    ')})"
    )


def generate_predictor(model: GradientBoostingRegressor, metrics: dict, cv_metrics: dict) -> None:
    init_value = float(model.init_.constant_[0][0])
    trees = [tree_to_tuple(estimator[0].tree_) for estimator in model.estimators_]
    tree_text = ",\n".join(f"    {format_tree(tree)}" for tree in trees)
    feature_names = ",\n".join(f"    {name!r}" for name in FEATURE_NAMES)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(
        f'''# Auto-generated by calibrate_tracker_score.py. Do not edit by hand.
import math


FEATURE_NAMES = [
{feature_names}
]

INIT_VALUE = {init_value:.12f}
LEARNING_RATE = {model.learning_rate:.12f}
TRAIN_METRICS = {metrics!r}
CV_METRICS = {cv_metrics!r}

TREES = [
{tree_text}
]


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _features(stats: dict) -> list[float]:
    acs = _number(stats.get('acs'))
    adr = _number(stats.get('adr'))
    dda = _number(stats.get('dda'))
    kd = _number(stats.get('kd'))
    plus_minus = _number(stats.get('plus_minus'))
    hs_rate = _number(stats.get('hs_rate'))
    kast_rate = _number(stats.get('kast_rate'))
    fk_per_round = _number(stats.get('fk_per_round'))
    fd_per_round = _number(stats.get('fd_per_round'))
    mk_per_round = _number(stats.get('mk_per_round'))
    assists_per_round = _number(stats.get('assists_per_round'))
    kills_per_round = _number(stats.get('kills_per_round'))
    deaths_per_round = _number(stats.get('deaths_per_round'))
    won = _number(stats.get('won'))
    round_diff = _number(stats.get('round_diff'))
    player_rank_idx = _number(stats.get('player_rank_idx'))
    avg_rank_idx = _number(stats.get('avg_rank_idx'))
    rank_delta = _number(stats.get('rank_delta'))
    log_kill_death = _number(stats.get('log_kill_death'))
    rounds = max(_number(stats.get('rounds')), 1.0)
    team_rounds = _number(stats.get('team_rounds'))
    enemy_rounds = _number(stats.get('enemy_rounds'))

    return [
        acs,
        adr,
        dda,
        max(0.0, dda),
        min(0.0, dda),
        kd,
        plus_minus,
        hs_rate,
        kast_rate,
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
        log_kill_death,
        rounds,
        team_rounds,
        enemy_rounds,
        acs * kast_rate,
        adr * kast_rate,
        kd * kast_rate,
        acs * kd,
        dda * kast_rate,
        plus_minus / rounds,
        fk_per_round - fd_per_round,
        kills_per_round + 0.7 * assists_per_round - deaths_per_round,
    ]


def _predict_tree(node, features: list[float]) -> float:
    while node[0] == 'node':
        _, feature_index, threshold, left, right = node
        node = left if features[feature_index] <= threshold else right
    return node[1]


def predict_trs_raw(stats: dict) -> float:
    features = _features(stats)
    score = INIT_VALUE
    for tree in TREES:
        score += LEARNING_RATE * _predict_tree(tree, features)
    return score
''',
        encoding="utf-8",
    )


def main() -> None:
    samples = load_samples()
    x = np.array([feature_vector(stats_from_row(row)) for row in samples], dtype=float)
    y = np.array([number(row["trs"]) for row in samples], dtype=float)

    model = make_model()
    model.fit(x, y)

    train_predictions = model.predict(x)
    train_metrics = evaluate(y, train_predictions)
    cv_metrics = cross_validate(x, y)
    generate_predictor(model, train_metrics, cv_metrics)

    errors = clamp_score(train_predictions) - y
    print(f"samples={len(samples)}")
    print(
        "train "
        f"mae={train_metrics['mae']:.2f} rmse={train_metrics['rmse']:.2f} "
        f"p95={train_metrics['p95']:.2f} max={train_metrics['max']:.2f}"
    )
    print(
        "cv    "
        f"mae={cv_metrics['mae']:.2f} rmse={cv_metrics['rmse']:.2f} "
        f"p95={cv_metrics['p95']:.2f} max={cv_metrics['max']:.2f}"
    )
    print(f"generated={MODEL_PATH}")

    print("\nworst training errors:")
    for index in np.argsort(np.abs(errors))[::-1][:12]:
        row = samples[int(index)]
        print(
            f"  {row['source_image']:<38s} {row['team']} {row['player_rank']:<11s} "
            f"TRS={int(y[index]):>4} pred={int(clamp_score([train_predictions[index]])[0]):>4} "
            f"err={int(errors[index]):>4}"
        )


if __name__ == "__main__":
    main()
