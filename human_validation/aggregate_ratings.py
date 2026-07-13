"""Validate blinded ratings, report agreement, and export consensus disputes.

Usage: python human_validation/aggregate_ratings.py ratings_rater1.csv ratings_rater2.csv
"""

from __future__ import annotations

import csv
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample_for_rating.csv"
OUT = HERE / "agreement.json"
DISPUTES = HERE / "disputes.csv"
BANDS = {"high", "mild", "low"}
VALENCES = {"positive", "negative", "neutral"}
BAND_FIELD = "rated_band(high/mild/low)"
VALENCE_FIELD = "rated_valence(positive/negative/neutral)"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def cohen_kappa(left: list[str], right: list[str]) -> float:
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    expected = sum(left.count(value) / len(left) * right.count(value) / len(right) for value in set(left + right))
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def consensus(values: list[str]) -> tuple[str, bool]:
    counts = Counter(values)
    value, count = counts.most_common(1)[0]
    return value, count > len(values) / 2


def main(args: list[str]) -> int:
    if len(args) < 2:
        print("provide ratings from at least two independent raters", file=sys.stderr)
        return 2
    sample_ids = {row["id"] for row in read_rows(SAMPLE)}
    corpus = json.loads((ROOT / "data" / "epirec_v1.json").read_text(encoding="utf-8"))
    authored = {episode["id"]: episode for persona in corpus["personas"] for episode in persona["episodes"]}
    raters: dict[str, dict[str, dict[str, str]]] = {}
    for arg in args:
        path, rows = Path(arg), read_rows(Path(arg))
        if len(rows) != len(sample_ids) or {row.get("id") for row in rows} != sample_ids:
            print(f"{path}: must contain every sampled id exactly once", file=sys.stderr)
            return 1
        if any(row.get(BAND_FIELD) not in BANDS or row.get(VALENCE_FIELD) not in VALENCES for row in rows):
            print(f"{path}: every row requires a valid band and valence", file=sys.stderr)
            return 1
        raters[path.name] = {row["id"]: row for row in rows}

    names = sorted(raters)
    pairwise = []
    for left, right in itertools.combinations(names, 2):
        pairwise.append({
            "raters": [left, right],
            "band_cohen_kappa": round(cohen_kappa([raters[left][id][BAND_FIELD] for id in sorted(sample_ids)], [raters[right][id][BAND_FIELD] for id in sorted(sample_ids)]), 4),
            "valence_cohen_kappa": round(cohen_kappa([raters[left][id][VALENCE_FIELD] for id in sorted(sample_ids)], [raters[right][id][VALENCE_FIELD] for id in sorted(sample_ids)]), 4),
        })
    disputes = []
    for episode_id in sorted(sample_ids):
        band, band_majority = consensus([raters[name][episode_id][BAND_FIELD] for name in names])
        valence, valence_majority = consensus([raters[name][episode_id][VALENCE_FIELD] for name in names])
        if not band_majority or not valence_majority or band != authored[episode_id]["intensity_band"] or valence != authored[episode_id]["valence"]:
            disputes.append({"id": episode_id, "authored_band": authored[episode_id]["intensity_band"], "consensus_band": band, "authored_valence": authored[episode_id]["valence"], "consensus_valence": valence, "band_majority": band_majority, "valence_majority": valence_majority})
    OUT.write_text(json.dumps({"sample_size": len(sample_ids), "raters": names, "pairwise_cohen_kappa": pairwise, "dispute_count": len(disputes)}, indent=2) + "\n", encoding="utf-8")
    with DISPUTES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "authored_band", "consensus_band", "authored_valence", "consensus_valence", "band_majority", "valence_majority"])
        writer.writeheader()
        writer.writerows(disputes)
    print(f"wrote {OUT} and {DISPUTES} ({len(disputes)} disputes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
