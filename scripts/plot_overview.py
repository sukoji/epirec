"""Render the publication-facing overview figure from the frozen EpiRec release."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "epirec_v1.json"
BASELINES = ROOT / "docs" / "baselines.json"
OUT = ROOT / "docs" / "epirec_overview.png"

INK = "#1f2933"
MUTED = "#62717d"
GRID = "#dce3e8"
SHORT = "#edf1f3"
COLORS = {"high": "#d04a3a", "mild": "#d89b1d", "low": "#2878b8"}
PROBE_COLORS = ["#2878b8", "#168a70", "#7d5bb8"]


def main() -> None:
    corpus = json.loads(DATA.read_text(encoding="utf-8"))
    baselines = json.loads(BASELINES.read_text(encoding="utf-8"))
    reference = datetime.fromisoformat(corpus["reference_now"])
    personas = corpus["personas"]
    episodes = [episode for persona in personas for episode in persona["episodes"]]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig = plt.figure(figsize=(14.4, 8.4), facecolor="white")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.38, 1], height_ratios=[1.16, 1], wspace=0.31, hspace=0.42)
    ax_time = fig.add_subplot(grid[0, 0])
    ax_probe = fig.add_subplot(grid[0, 1])
    ax_mix = fig.add_subplot(grid[1, 0])
    ax_baseline = fig.add_subplot(grid[1, 1])

    # Timeline: each dot is one episode, preserving the real frozen timestamps.
    ax_time.axvspan(0, 6, color=SHORT, zorder=0)
    for row, persona in enumerate(personas):
        ages = []
        bands = []
        for episode in persona["episodes"]:
            age = (reference - datetime.fromisoformat(episode["date_time"])).total_seconds() / 86400
            ages.append(age)
            bands.append(episode["intensity_band"])
        for band in ("low", "mild", "high"):
            xs = [age for age, value in zip(ages, bands) if value == band]
            ax_time.scatter(xs, [row] * len(xs), s=42, color=COLORS[band], edgecolors="white", linewidths=.65, zorder=3)
    ax_time.set_xlim(0, 124)
    ax_time.set_ylim(-.7, len(personas) - .3)
    ax_time.invert_yaxis()
    ax_time.set_yticks(range(len(personas)), [persona["persona_id"].upper() for persona in personas])
    ax_time.set_xlabel("Episode age at reference time (days)", color=INK)
    ax_time.set_title("Timeline coverage by authored intensity", loc="left", color=INK, fontweight="bold", pad=10)
    ax_time.grid(axis="x", color=GRID, linewidth=.8)

    # Probe taxonomy: communicates the controlled difficulty ladder without inventing a score.
    ax_probe.set_axis_off()
    ax_probe.set_title("Probe taxonomy: 3 controlled queries per episode", loc="left", color=INK, fontweight="bold", pad=10)
    rows = [
        ("FACTUAL", "Concrete detail", "Lexical overlap allowed"),
        ("EXPLICIT", "Named emotion", "Emotion word or close synonym"),
        ("IMPLICIT", "Indirect reflection", "No emotion word or target content stem"),
    ]
    for index, (tag, title, rule) in enumerate(rows):
        y = .70 - index * .245
        ax_probe.add_patch(Rectangle((.04, y), .92, .20, transform=ax_probe.transAxes,
                                     facecolor="#f7f9fa", edgecolor=GRID, linewidth=.8))
        ax_probe.add_patch(Rectangle((.04, y), .022, .20, transform=ax_probe.transAxes,
                                     facecolor=PROBE_COLORS[index], edgecolor="none"))
        ax_probe.text(.09, y + .135, tag, transform=ax_probe.transAxes, color=PROBE_COLORS[index], fontsize=8, fontweight="bold")
        ax_probe.text(.09, y + .070, title, transform=ax_probe.transAxes, color=INK, fontsize=11, fontweight="bold")
        ax_probe.text(.09, y + .020, rule, transform=ax_probe.transAxes, color=MUTED, fontsize=8.4)
    ax_probe.text(.04, .045, "168 episodes  x  3 query conditions  =  504 single-target probes", transform=ax_probe.transAxes, color=INK, fontsize=9, fontweight="bold")

    # Composition: show intensity and valence as directly labeled stacked bars.
    intensity_order = ["high", "mild", "low"]
    valence_order = ["positive", "negative", "neutral"]
    valence_colors = {"positive": "#168a70", "negative": "#d04a3a", "neutral": "#7f8b95"}
    for y, (label, order, palette, key) in enumerate((
        ("Intensity", intensity_order, COLORS, "intensity_band"),
        ("Valence", valence_order, valence_colors, "valence"),
    )):
        left = 0
        for value in order:
            count = sum(episode[key] == value for episode in episodes)
            ax_mix.barh(y, count, left=left, color=palette[value], height=.48)
            ax_mix.text(left + count / 2, y, f"{value} {count}", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
            left += count
    ax_mix.set_xlim(0, len(episodes))
    ax_mix.set_yticks([0, 1], ["Authored intensity", "Authored valence"])
    ax_mix.invert_yaxis()
    ax_mix.set_xlabel("Episodes", color=INK)
    ax_mix.set_title("Label composition", loc="left", color=INK, fontweight="bold", pad=10)
    ax_mix.grid(axis="x", color=GRID, linewidth=.8)

    # Reference semantic baseline: the figure documents the intended difficulty gradient.
    probe_types = ["factual", "reflective_explicit", "reflective_implicit"]
    labels = ["Factual", "Explicit", "Implicit"]
    values = [baselines["similarity (MiniLM)"][kind]["r3"] for kind in probe_types]
    x = np.arange(len(values))
    ax_baseline.plot(x, values, color="#1f5f97", marker="o", markersize=8, linewidth=2.3)
    for index, value in enumerate(values):
        ax_baseline.text(index, value + .045, f"{value:.3f}", ha="center", color=INK, fontweight="bold")
    ax_baseline.set_xticks(x, labels)
    ax_baseline.set_ylim(0, 1.08)
    ax_baseline.set_yticks([0, .25, .5, .75, 1.0])
    ax_baseline.set_ylabel("Recall@3", color=INK)
    ax_baseline.set_title("Reference difficulty check", loc="left", color=INK, fontweight="bold", pad=10)
    ax_baseline.text(1, .07, "Reference retriever: similarity-only MiniLM", ha="center", color=MUTED, fontsize=8)
    ax_baseline.grid(axis="y", color=GRID, linewidth=.8)

    for axis in (ax_time, ax_mix, ax_baseline):
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#aeb8c0")
        axis.tick_params(colors=INK)

    fig.suptitle("EpiRec v1.0 | Emotional resurfacing and factual lookup", x=.06, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.text(.06, .935, "Frozen synthetic evaluation corpus: 12 personas, 168 episodes, 504 probes", color=MUTED, fontsize=10)
    fig.savefig(OUT, dpi=180, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
