"""Emit within-persona lexical near-neighbor candidates for blinded human review."""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "epirec_v1.json"
OUT = ROOT / "docs" / "ambiguity_candidates.json"
STOP = {"a", "an", "the", "and", "or", "to", "of", "in", "on", "at", "for", "with", "i", "my", "was", "were", "is", "it", "that", "this", "had", "have", "but", "so", "after", "before", "from"}


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower())) - STOP


def main() -> None:
    corpus = json.loads(DATA.read_text(encoding="utf-8"))
    candidates = []
    for persona in corpus["personas"]:
        for left, right in combinations(persona["episodes"], 2):
            left_terms, right_terms = terms(left["text"]), terms(right["text"])
            similarity = len(left_terms & right_terms) / len(left_terms | right_terms)
            if similarity >= .10:
                candidates.append({"persona_id": persona["persona_id"], "episode_a": left["id"],
                                   "episode_b": right["id"], "jaccard": round(similarity, 4),
                                   "shared_terms": sorted(left_terms & right_terms)})
    candidates.sort(key=lambda item: (-item["jaccard"], item["persona_id"]))
    OUT.write_text(json.dumps({"method": "token Jaccard within persona; human review required", "candidates": candidates}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(candidates)} candidates)")


if __name__ == "__main__":
    main()
