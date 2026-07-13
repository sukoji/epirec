"""Validate completed human-rating files and report agreement."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample_for_rating.csv"
OUT = HERE / "agreement.json"
BANDS = {"high", "mild", "low"}
VALENCES = {"positive", "negative", "neutral"}
BAND_FIELD = "rated_band(high/mild/low)"
VALENCE_FIELD = "rated_valence(positive/negative/neutral)"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main(args: list[str]) -> int:
    if not args:
        print("provide at least one completed ratings_<name>.csv", file=sys.stderr)
        return 2
    sample_ids = {row["id"] for row in read_rows(SAMPLE)}
    corpus = json.loads((ROOT / "data" / "epirec_v1.json").read_text(encoding="utf-8"))
    authored = {episode["id"]: episode for persona in corpus["personas"] for episode in persona["episodes"]}
    reports = []
    for arg in args:
        path, rows = Path(arg), read_rows(Path(arg))
        if len(rows) != len(sample_ids) or {row.get("id") for row in rows} != sample_ids:
            print(f"{path}: must contain every sampled id exactly once", file=sys.stderr)
            return 1
        if any(row.get(BAND_FIELD) not in BANDS or row.get(VALENCE_FIELD) not in VALENCES for row in rows):
            print(f"{path}: every row requires a valid band and valence", file=sys.stderr)
            return 1
        reports.append({
            "file": path.name,
            "n": len(rows),
            "band_exact_agreement": sum(row[BAND_FIELD] == authored[row["id"]]["intensity_band"] for row in rows) / len(rows),
            "valence_exact_agreement": sum(row[VALENCE_FIELD] == authored[row["id"]]["valence"] for row in rows) / len(rows),
        })
    OUT.write_text(json.dumps({"sample_size": len(sample_ids), "raters": reports}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
