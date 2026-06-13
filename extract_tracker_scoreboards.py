import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR


SCREEN_DIR = Path("data/scoreboard_screens")
OUTPUT_PATH = Path("data/tracker_score_samples_extracted.csv")

CSV_FIELDS = [
    "sample_id", "map", "scoreline", "team", "team_result", "avg_rank", "player_rank",
    "trs", "acs", "k", "d", "a", "plus_minus", "kd", "dda", "adr",
    "hs_percent", "kast_percent", "fk", "fd", "mk", "source_image"
]

RANK_NAMES = [
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

CROP_BOX = (570, 520, 1985, 1435)
SCALE = 2

COLUMNS = {
    "trs": (760, 920),
    "acs": (950, 1090),
    "k": (1125, 1235),
    "d": (1255, 1370),
    "a": (1385, 1495),
    "plus_minus": (1510, 1630),
    "kd": (1640, 1765),
    "dda": (1780, 1910),
    "adr": (1935, 2115),
    "hs_percent": (2120, 2260),
    "kast_percent": (2275, 2435),
    "fk": (2440, 2555),
    "fd": (2565, 2680),
    "mk": (2690, 2820),
}


def center(box):
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    return (sum(xs) / 4, sum(ys) / 4)


def normalize_int(text: str):
    clean = re.sub(r"[^0-9+\-]", "", text or "")
    if not clean or clean in {"+", "-"}:
        return None
    try:
        return int(clean)
    except ValueError:
        return None


def normalize_float(text: str):
    clean = (text or "").replace(",", ".")
    clean = re.sub(r"[^0-9+\-.]", "", clean)
    if not clean or clean in {"+", "-", "."}:
        return None
    try:
        return float(clean)
    except ValueError:
        return None


def normalize_percent(text: str):
    return normalize_float((text or "").replace("%", ""))


def normalize_rank(text: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9 ]", " ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip().lower()
    roman_map = {"iii": "3", "ii": "2", "i": "1"}
    for rank_root in ["iron", "bronze", "silver", "gold", "platinum", "diamond", "ascendant", "immortal"]:
        clean = re.sub(
            rf"\b{rank_root}\s+(iii|ii|i)\b",
            lambda match: f"{rank_root} {roman_map[match.group(1)]}",
            clean,
        )
    clean = clean.replace("ascendant", "ascendant ")
    clean = re.sub(r"\s+", " ", clean)
    for rank in sorted(RANK_NAMES, key=len, reverse=True):
        compact = rank.lower()
        if compact in clean or compact.replace(" ", "") in clean.replace(" ", ""):
            return rank
    return ""


def cell_text(items, y, key, max_distance=34):
    x0, x1 = COLUMNS[key]
    candidates = []
    for item in items:
        if x0 <= item["cx"] <= x1 and abs(item["cy"] - y) <= max_distance:
            candidates.append(item)
    if not candidates:
        return ""
    candidates.sort(key=lambda item: (abs(item["cy"] - y), item["cx"]))
    return " ".join(item["text"] for item in candidates[:2])


def crop_cell(crop, row_y, key, x_padding=12, y_padding=36):
    x0, x1 = COLUMNS[key]
    left = max(0, int(x0 - x_padding))
    top = max(0, int(row_y - y_padding))
    right = min(crop.width, int(x1 + x_padding))
    bottom = min(crop.height, int(row_y + y_padding))
    return crop.crop((left, top, right, bottom))


def digit_mask(image):
    gray = image.convert("L")
    return np.array(gray) > 150


def digit_components(mask):
    cols = np.where(mask.any(axis=0))[0]
    if len(cols) == 0:
        return []

    groups = []
    start = int(cols[0])
    previous = int(cols[0])
    for col in cols[1:]:
        col = int(col)
        if col - previous > 1:
            groups.append((start, previous))
            start = col
        previous = col
    groups.append((start, previous))

    components = []
    for x0, x1 in groups:
        submask = mask[:, x0:x1 + 1]
        ys, xs = np.where(submask)
        if len(xs) == 0:
            continue
        y0 = int(ys.min())
        y1 = int(ys.max())
        if (x1 - x0 + 1) * (y1 - y0 + 1) < 6:
            continue
        components.append(mask[y0:y1 + 1, x0:x1 + 1])
    return components


def normalize_digit_component(component):
    image = Image.fromarray((component * 255).astype("uint8"))
    canvas = Image.new("L", (48, 64), 0)
    image.thumbnail((42, 58), Image.Resampling.NEAREST)
    canvas.paste(image, ((48 - image.width) // 2, (64 - image.height) // 2))
    return np.array(canvas) > 128


def digit_score(a, b):
    intersection = np.logical_and(a, b).sum()
    union = max(np.logical_or(a, b).sum(), 1)
    return np.mean(a != b) - 0.25 * (intersection / union)


def digit_features(component):
    height, width = component.shape
    center = component[height // 3:2 * height // 3, width // 3:2 * width // 3].mean()
    midrow = component[max(0, height // 2 - 1):min(height, height // 2 + 2), :].mean()
    midcol = component[:, max(0, width // 2 - 1):min(width, width // 2 + 2)].mean()
    inverse = ~component
    padded = np.pad(inverse, 1, constant_values=True)
    seen = np.zeros(padded.shape, dtype=bool)
    holes = 0

    for start_y in range(padded.shape[0]):
        for start_x in range(padded.shape[1]):
            if not padded[start_y, start_x] or seen[start_y, start_x]:
                continue
            stack = [(start_y, start_x)]
            seen[start_y, start_x] = True
            touches_edge = False
            while stack:
                y, x = stack.pop()
                if y in {0, padded.shape[0] - 1} or x in {0, padded.shape[1] - 1}:
                    touches_edge = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny = y + dy
                    nx = x + dx
                    if (
                        0 <= ny < padded.shape[0]
                        and 0 <= nx < padded.shape[1]
                        and padded[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if not touches_edge:
                holes += 1

    return {
        "aspect": width / max(height, 1),
        "center": center,
        "midrow": midrow,
        "midcol": midcol,
        "holes": holes,
        "fill": component.mean(),
    }


def geometric_digit(component):
    features = digit_features(component)
    if features["aspect"] < 0.52:
        return "1"
    if features["holes"] >= 2:
        return "8"
    if features["holes"] == 1:
        if features["center"] < 0.12:
            return "0"
        if features["aspect"] > 0.70 and features["midcol"] > 0.50 and features["fill"] < 0.56:
            return "4"
        if features["midrow"] > 0.74:
            return "9"
    return ""


def build_digit_templates(crop, items):
    templates = {str(index): [] for index in range(10)}
    for item in items:
        text = item["text"].strip()
        if not re.fullmatch(r"\d{1,3}", text):
            continue

        xs = [point[0] for point in item["box"]]
        ys = [point[1] for point in item["box"]]
        image = crop.crop((
            max(0, int(min(xs) - 3)),
            max(0, int(min(ys) - 3)),
            min(crop.width, int(max(xs) + 3)),
            min(crop.height, int(max(ys) + 3)),
        ))
        components = digit_components(digit_mask(image))
        if len(components) != len(text):
            continue

        for char, component in zip(text, components):
            templates[char].append(normalize_digit_component(component))
    return templates


def recognize_digit_cell(crop, row_y, key, templates):
    if not templates or not any(templates.values()):
        return None

    cell = crop_cell(crop, row_y, key, 20, 44)
    components = digit_components(digit_mask(cell))
    if not components or len(components) > 2:
        return None

    digits = []
    for component in components:
        geometric = geometric_digit(component)
        if geometric:
            digits.append(geometric)
            continue

        normalized = normalize_digit_component(component)
        matches = []
        for digit, digit_templates in templates.items():
            for template in digit_templates:
                matches.append((digit_score(normalized, template), digit))
        if not matches:
            return None
        score, digit = min(matches, key=lambda item: item[0])
        if score > 0.08:
            return None
        digits.append(digit)

    try:
        return int("".join(digits))
    except ValueError:
        return None


def cell_ocr_text(crop, ocr, row_y, key):
    cell = crop_cell(crop, row_y, key)
    cell = cell.resize((cell.width * 4, cell.height * 4), Image.Resampling.LANCZOS)
    result, _ = ocr(np.array(cell))
    if not result:
        return ""
    entries = []
    for box, text, conf in result:
        cx, cy = center(box)
        entries.append({"text": text, "conf": float(conf), "cx": cx, "cy": cy})
    entries.sort(key=lambda item: (item["cy"], item["cx"]))
    return " ".join(item["text"] for item in entries if item["conf"] >= 0.25)


def parse_column_value(items, crop, ocr, row_y, key, templates):
    text = cell_text(items, row_y, key)
    if key in {"kd", "adr"}:
        value = normalize_float(text)
    elif key in {"hs_percent", "kast_percent"}:
        value = normalize_percent(text)
    else:
        value = normalize_int(text)
    if value is not None:
        return value

    if key in {"trs", "acs", "k", "d", "a", "fk", "fd", "mk"}:
        value = recognize_digit_cell(crop, row_y, key, templates)
        if value is not None:
            return value

    text = cell_ocr_text(crop, ocr, row_y, key)
    if key in {"kd", "adr"}:
        return normalize_float(text)
    if key in {"hs_percent", "kast_percent"}:
        return normalize_percent(text)
    return normalize_int(text)


def parse_header(items):
    top_text = " ".join(item["text"] for item in items if item["cy"] < 180)
    map_name = ""
    for candidate in [
        "Abyss", "Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox",
        "Lotus", "Pearl", "Split", "Sunset"
    ]:
        if candidate.lower() in top_text.lower():
            map_name = candidate
            break

    scoreline = ""
    score_area_candidates = []
    fallback_candidates = []
    for item in items:
        if item["cy"] > 190:
            continue
        if "/" in item["text"]:
            continue
        for match in re.finditer(r"(\d{1,2})\s*[:\-]\s*(\d{1,2})", item["text"]):
            left = int(match.group(1))
            right = int(match.group(2))
            if left + right <= 50:
                candidate = (item["cy"], item["cx"], left, right)
                if 300 <= item["cx"] <= 600 and 80 <= item["cy"] <= 145:
                    score_area_candidates.append(candidate)
                else:
                    fallback_candidates.append(candidate)
    candidates = score_area_candidates or fallback_candidates
    if candidates:
        _, _, left, right = sorted(candidates)[0]
        scoreline = f"{left}-{right}"

    return map_name, scoreline


def parse_team_headers(items):
    headers = []
    for item in items:
        text = item["text"].lower()
        compact = re.sub(r"[^a-z0-9]", "", text)
        if "team" in compact and "avg" in compact and item["cy"] > 430:
            team = "A" if "teama" in compact else "B" if "teamb" in compact else ""
            nearby_rank_text = " ".join(
                other["text"]
                for other in items
                if 250 <= other["cx"] <= 520 and abs(other["cy"] - item["cy"]) <= 24
            )
            rank = normalize_rank(f"{item['text']} {nearby_rank_text}")
            headers.append({"team": team, "rank": rank, "y": item["cy"]})
    headers.sort(key=lambda item: item["y"])
    return headers


def is_valid_final_scoreline(score_a, score_b):
    return max(score_a, score_b) >= 13 and abs(score_a - score_b) >= 2


def row_team(row_y, team_headers):
    active = None
    for header in team_headers:
        if row_y > header["y"]:
            active = header
    return active or {"team": "", "rank": "", "y": 0}


def parse_image(path: Path, ocr: RapidOCR):
    image = Image.open(path).convert("RGB")
    crop = image.crop(CROP_BOX)
    crop = crop.resize((crop.width * SCALE, crop.height * SCALE), Image.Resampling.LANCZOS)
    result, _ = ocr(np.array(crop))
    if not result:
        return [], "no_ocr"

    items = []
    for box, text, conf in result:
        cx, cy = center(box)
        items.append({"box": box, "text": text, "conf": float(conf), "cx": cx, "cy": cy})
    digit_templates = build_digit_templates(crop, items)

    all_text = " ".join(item["text"] for item in items)
    if "Scoreboard" not in all_text or "TRS" not in all_text or "ACS" not in all_text:
        return [], "not_scoreboard"

    map_name, scoreline = parse_header(items)
    if not scoreline:
        return [], "missing_scoreline"

    score_a, score_b = [int(part) for part in scoreline.split("-")]
    if not is_valid_final_scoreline(score_a, score_b):
        return [], "invalid_scoreline"
    team_headers = parse_team_headers(items)
    if len(team_headers) < 2:
        return [], "missing_team_headers"

    trs_items = []
    for item in items:
        if COLUMNS["trs"][0] <= item["cx"] <= COLUMNS["trs"][1] and 520 <= item["cy"] <= 1780:
            value = normalize_int(item["text"])
            if value is not None and 50 <= value <= 999:
                trs_items.append(item)

    rows = []
    used_y = []
    for item in sorted(trs_items, key=lambda entry: entry["cy"]):
        if any(abs(item["cy"] - y) < 45 for y in used_y):
            continue
        used_y.append(item["cy"])
        rows.append(item["cy"])

    parsed_rows = []
    for row_y in rows:
        team_info = row_team(row_y, team_headers)
        team = team_info["team"]
        if team not in {"A", "B"}:
            continue

        player_texts = [
            item for item in items
            if 120 <= item["cx"] <= 470 and abs(item["cy"] - row_y) <= 34
        ]
        player_texts.sort(key=lambda item: item["cx"])
        rank_texts = [
            item for item in items
            if 120 <= item["cx"] <= 430 and 20 <= item["cy"] - row_y <= 60
        ]
        rank = normalize_rank(" ".join(item["text"] for item in rank_texts))

        values = {}
        for key in COLUMNS:
            values[key] = parse_column_value(items, crop, ocr, row_y, key, digit_templates)

        if values.get("plus_minus") is None and values.get("k") is not None and values.get("d") is not None:
            values["plus_minus"] = values["k"] - values["d"]
        if values.get("k") is None and values.get("d") is not None and values.get("plus_minus") is not None:
            values["k"] = values["d"] + values["plus_minus"]
        if values.get("d") is None and values.get("k") is not None and values.get("plus_minus") is not None:
            values["d"] = values["k"] - values["plus_minus"]

        required = ["trs", "acs", "k", "d", "a", "plus_minus", "kd", "dda", "adr", "hs_percent", "kast_percent", "fk", "fd", "mk"]
        if any(values.get(key) is None for key in required):
            continue

        team_score = score_a if team == "A" else score_b
        other_score = score_b if team == "A" else score_a
        parsed_rows.append({
            "sample_id": f"{path.stem}_{map_name}_{scoreline}",
            "map": map_name,
            "scoreline": scoreline,
            "team": team,
            "team_result": "WIN" if team_score > other_score else "LOSS",
            "avg_rank": team_info["rank"],
            "player_rank": rank or team_info["rank"],
            "trs": values["trs"],
            "acs": values["acs"],
            "k": values["k"],
            "d": values["d"],
            "a": values["a"],
            "plus_minus": values["plus_minus"],
            "kd": values["kd"],
            "dda": values["dda"],
            "adr": values["adr"],
            "hs_percent": values["hs_percent"],
            "kast_percent": values["kast_percent"],
            "fk": values["fk"],
            "fd": values["fd"],
            "mk": values["mk"],
            "source_image": path.name,
        })

    if len(parsed_rows) < 8:
        return parsed_rows, "too_few_rows"
    return parsed_rows[:10], "ok"


def row_identity(row):
    return (
        row["map"], row["scoreline"], row["team"], row["trs"], row["acs"],
        row["k"], row["d"], row["a"], row["plus_minus"], row["kd"], row["dda"],
        row["adr"], row["hs_percent"], row["kast_percent"], row["fk"], row["fd"], row["mk"]
    )


def match_signature(rows):
    return tuple(sorted(row_identity(row) for row in rows))


def main():
    ocr = RapidOCR()
    files = sorted(SCREEN_DIR.glob("scoreboard_*.bmp"))
    extracted = []
    statuses = Counter()
    seen_matches = {}

    for path in files:
        rows, status = parse_image(path, ocr)
        statuses[status] += 1
        if status != "ok":
            print(f"skip {path.name}: {status} rows={len(rows)}")
            continue

        signature = match_signature(rows)
        if signature in seen_matches:
            print(f"dupe {path.name}: same as {seen_matches[signature]}")
            continue

        seen_matches[signature] = path.name
        extracted.extend(rows)
        print(f"ok   {path.name}: rows={len(rows)} {rows[0]['map']} {rows[0]['scoreline']}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(extracted)

    print("statuses", dict(statuses))
    print("matches", len(seen_matches), "rows", len(extracted), "output", OUTPUT_PATH)


if __name__ == "__main__":
    main()
