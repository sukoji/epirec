"""Merge persona files into the released corpus file and print corpus stats.

    python scripts/validate.py   # must pass first
    python scripts/build.py      # writes data/epirec_v1.json + docs/stats.png
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ROOT / "data" / "personas"
OUT = ROOT / "data" / "epirec_v1.json"
NOW = "2025-06-30T12:00:00+00:00"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    personas = [json.loads(f.read_text(encoding="utf-8"))
                for f in sorted(PERSONAS.glob("p*.json"))]

    eps = [e for p in personas for e in p["episodes"]]
    probes = [pr for e in eps for pr in e["probes"]]
    bands = {b: sum(1 for e in eps if e["intensity_band"] == b) for b in ("high", "mild", "low")}
    valences = {v: sum(1 for e in eps if e["valence"] == v) for v in ("positive", "negative", "neutral")}
    types = {t: sum(1 for p in probes if p["type"] == t)
             for t in ("factual", "reflective_explicit", "reflective_implicit")}
    now = datetime.fromisoformat(NOW)
    ages = [(now - datetime.fromisoformat(e["date_time"]).replace(tzinfo=timezone.utc)).days
            for e in eps]

    corpus = {
        "name": "EpiRec",
        "full_name": "Episodic Recall: A Benchmark for Emotional Resurfacing and "
                     "Factual Lookup in Memory-Augmented Agents",
        "version": "1.0",
        "reference_now": NOW,
        "construction": "pre-registered; see GENERATION_SPEC.md",
        "license": "CC BY 4.0",
        "stats": {
            "personas": len(personas),
            "episodes": len(eps),
            "probes": len(probes),
            "intensity_bands": bands,
            "valences": valences,
            "probe_types": types,
            "episode_age_days": {"min": min(ages), "max": max(ages)},
        },
        "personas": personas,
    }
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}")
    for k, v in corpus["stats"].items():
        print(f"  {k}: {v}")

    _stats_figure(eps, bands, types, ages)


def _stats_figure(eps, bands, types, ages) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, blue, aqua, yellow = "#33322e", "#2a78d6", "#1baf7a", "#eda100"
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12.5, 3.6))
    for ax in (a1, a2, a3):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    a1.bar(list(bands), list(bands.values()), color=[blue, aqua, yellow])
    a1.set_title("episodes by intensity band", fontsize=10, color=ink)

    labels = ["factual", "explicit", "implicit"]
    a2.bar(labels, list(types.values()), color=blue)
    a2.set_title("probes by type (3 per episode)", fontsize=10, color=ink)

    a3.hist(ages, bins=17, color=aqua)
    a3.axvspan(0, 6, color="#eeeae2", zorder=0)
    a3.set_title("episode age at reference date (days)\nshaded = short-term window (≤6 d)",
                 fontsize=10, color=ink)

    fig.suptitle("EpiRec v1.0 — 12 personas · 168 episodes · 504 probes", fontsize=12, color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out = Path(__file__).resolve().parents[1] / "docs" / "stats.png"
    fig.savefig(out, bbox_inches="tight", dpi=130)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
