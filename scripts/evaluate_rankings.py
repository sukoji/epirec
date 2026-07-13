"""Evaluate an external system's ranked episode outputs on frozen EpiRec v1.0.

Input is JSONL with one object per probe:
{"persona_id": "p01", "probe_id": "p01e01-f", "ranked_episode_ids": ["p01e01", ...]}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "epirec_v1.json"
DEFAULT_OUTPUT = ROOT / "results" / "evaluation.json"
BOOTSTRAP_SAMPLES = 2000
SEED = 20260713


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * p)]


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    metrics = {"recall@1": [row["rank"] == 1 for row in rows],
               "recall@3": [row["rank"] <= 3 for row in rows],
               "mrr": [1 / row["rank"] for row in rows]}
    rng = random.Random(SEED)
    report = {"n": len(rows)}
    for name, values in metrics.items():
        values = [float(value) for value in values]
        report[name] = round(statistics.mean(values), 4)
        draws = [statistics.mean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAP_SAMPLES)]
        report[f"{name}_ci95"] = [round(percentile(draws, .025), 4), round(percentile(draws, .975), 4)]
    return report


def main(rankings_path: Path, output: Path) -> int:
    corpus = json.loads(DATA.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(corpus["reference_now"])
    probes, allowed = {}, {}
    for persona in corpus["personas"]:
        pid = persona["persona_id"]
        allowed[pid] = {episode["id"] for episode in persona["episodes"]}
        for episode in persona["episodes"]:
            age = (now - datetime.fromisoformat(episode["date_time"])).total_seconds() / 86400
            age_bucket = "short" if age <= 6 else "long" if age > 30 else "medium"
            for probe in episode["probes"]:
                probes[(pid, probe["id"])] = {
                    "target": episode["id"], "probe_type": probe["type"],
                    "intensity_band": episode["intensity_band"], "age_bucket": age_bucket,
                }
    seen, rows = set(), []
    for line_number, line in enumerate(rankings_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        key = (record.get("persona_id"), record.get("probe_id"))
        ranked = record.get("ranked_episode_ids")
        if key not in probes or key in seen or not isinstance(ranked, list):
            raise ValueError(f"invalid or duplicate record at line {line_number}")
        if (
            len(ranked) != len(allowed[key[0]])
            or len(ranked) != len(set(ranked))
            or set(ranked) != allowed[key[0]]
        ):
            raise ValueError(f"invalid ranking at line {line_number}")
        seen.add(key)
        row = dict(probes[key])
        row["rank"] = ranked.index(row["target"]) + 1
        rows.append(row)
    if seen != set(probes):
        raise ValueError(f"expected {len(probes)} rankings, received {len(seen)}")

    def grouped(*keys: str) -> dict:
        groups: dict[str, list[dict]] = {}
        for row in rows:
            label = " | ".join(row[key] for key in keys)
            groups.setdefault(label, []).append(row)
        return {label: summarize(value) for label, value in sorted(groups.items())}

    output.parent.mkdir(exist_ok=True)
    report = {
        "benchmark": "EpiRec v1.0",
        "data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "bootstrap": {"samples": BOOTSTRAP_SAMPLES, "seed": SEED, "unit": "probe"},
        "overall": summarize(rows),
        "by_probe_type": grouped("probe_type"),
        "by_probe_type_and_intensity": grouped("probe_type", "intensity_band"),
        "by_probe_type_and_age": grouped("probe_type", "age_bucket"),
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    raise SystemExit(main(args.rankings, args.output))
