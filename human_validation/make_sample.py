"""Draw the stratified 60-episode sample for independent human label rating.

Deterministic (seeded by episode ids, no RNG state): sorts episodes within each
(band, valence) stratum by the MD5 of their id and takes a proportional share.

    python human_validation/make_sample.py   # writes sample_for_rating.csv
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N = 60


def main() -> None:
    corpus = json.loads((ROOT / "data" / "epirec_v1.json").read_text(encoding="utf-8"))
    eps = [e for p in corpus["personas"] for e in p["episodes"]]

    strata: dict[tuple, list] = {}
    for e in eps:
        strata.setdefault((e["intensity_band"], e["valence"]), []).append(e)

    sample = []
    for key in sorted(strata):
        pool = sorted(strata[key], key=lambda e: hashlib.md5(e["id"].encode()).hexdigest())
        share = max(1, round(N * len(pool) / len(eps)))
        sample.extend(pool[:share])
    sample = sorted(sample, key=lambda e: hashlib.md5(e["id"].encode()).hexdigest())[:N]

    out = Path(__file__).resolve().parent / "sample_for_rating.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "rated_band(high/mild/low)", "rated_valence(positive/negative/neutral)"])
        for e in sample:
            w.writerow([e["id"], e["text"], "", ""])
    print(f"wrote {out} ({len(sample)} episodes)")


if __name__ == "__main__":
    main()
