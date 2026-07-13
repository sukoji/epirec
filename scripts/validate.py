"""Validator for the EpiRec corpus — mechanically enforces GENERATION_SPEC.md.

Run after authoring / before freezing:

    python scripts/validate.py

Checks (violations are listed, exit 1 on any):
- schema completeness and unique ids
- per-persona episode count 14–18, session count 10–14, ~120-day span,
  every session strictly before the corpus anchor NOW (2025-06-30 12:00 UTC)
- band mix per spec (aggregate): ~45% low / ~40% high / ~15% mild (±10 pp)
- both emotional and neutral episodes present in short-term (≤6 d) and
  long-term (>30 d) age ranges, in aggregate
- exactly 3 probes per episode, one per type
- reflective_implicit probes: no content-word stem overlap with the episode
  text and no word from the independent emotion vocabulary below
- episode text 15–60 words, 1–3 sentences

The emotion vocabulary used for the implicit-probe check is authored here,
independently of persode/analyzer.py's lexicon (see spec: the analyzer's
behaviour on these probes is a measured result, not a construction input).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "personas"
NOW = datetime(2025, 6, 30, 12, 0, 0, tzinfo=timezone.utc)

BANDS = {"high", "mild", "low"}
VALENCES = {"positive", "negative", "neutral"}
PROBE_TYPES = {"factual", "reflective_explicit", "reflective_implicit"}

# Independent generic emotion vocabulary (NRC-style, hand-picked; NOT the
# analyzer lexicon). Implicit probes must avoid these words and their stems.
EMOTION_VOCAB = {
    "happy", "happiness", "joy", "joyful", "glad", "delight", "delighted",
    "excited", "excitement", "thrilled", "proud", "pride", "grateful",
    "gratitude", "love", "loved", "loving", "content", "contentment",
    "sad", "sadness", "unhappy", "sorrow", "sorrowful", "grief", "grieving",
    "heartbroken", "miserable", "depressed", "cry", "crying", "cried", "tears",
    "angry", "anger", "furious", "mad", "rage", "annoyed", "irritated",
    "frustrated", "frustrating", "frustration", "resentful", "upset",
    "afraid", "fear", "fearful", "scared", "terrified", "anxious", "anxiety",
    "nervous", "worried", "worry", "dread", "stressed", "stress", "panic",
    "ashamed", "shame", "embarrassed", "guilt", "guilty", "regret",
    "regretful", "lonely", "loneliness", "miss", "missed", "missing",
    "surprised", "surprise", "shocked", "astonished", "amazed",
    "disgust", "disgusted", "hate", "hated", "jealous", "envy", "envious",
    "hopeful", "hope", "hopeless", "despair", "relief", "relieved", "calm",
    "peaceful", "serene", "hurt", "hurting", "devastated", "overjoyed",
    "emotional", "emotion", "feelings", "feeling", "felt", "mourn", "mourning",
}

_STOP = set("""a an the this that these those i you he she it we they me my your his her its our their
of to in on at by for with and or but if then so as is am are was were be been being do did does done
have has had having i'm i've i'd it's don't didn't can't won't not no yes very really just about into
over under after before during when while where what who how why which there here out up down again still
sometimes some any all both each few more most other than too can will would should could may might must
day days week weeks month months year years time times back once twice around
from same whole until till like first second third next last behind above below toward towards through
because since longer anything everything someone something nothing different finally left took take taken
kept keep made make went come came gone goes get got one two three four five six seven eight nine ten
eleven twelve forty""".split())


def _stems(text: str, min_len: int = 4) -> set:
    toks = [t for t in re.findall(r"[a-z']+", text.lower()) if t not in _STOP and len(t) >= min_len]
    return {t[:6] for t in toks}


def _words(text: str) -> list:
    return re.findall(r"[a-z']+", text.lower())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    files = sorted(DATA_DIR.glob("p*.json"))
    if not files:
        print(f"no persona files in {DATA_DIR}")
        return 1

    all_ep_ids, all_probe_ids = set(), set()
    band_counts = {"high": 0, "mild": 0, "low": 0}
    age_cover = {("short", True): 0, ("short", False): 0, ("long", True): 0, ("long", False): 0}
    n_eps = 0

    for f in files:
        p = json.loads(f.read_text(encoding="utf-8"))
        pid = p.get("persona_id", f.stem)
        eps = p.get("episodes", [])
        if not (14 <= len(eps) <= 18):
            problems.append(f"{pid}: {len(eps)} episodes (spec: 14–18)")
        dts = []
        sessions = set()
        for e in eps:
            eid = e.get("id")
            if eid in all_ep_ids:
                problems.append(f"{pid}: duplicate episode id {eid}")
            all_ep_ids.add(eid)
            for key in ("id", "session", "date_time", "text", "emotion", "intensity_band", "valence", "probes"):
                if key not in e:
                    problems.append(f"{pid}/{eid}: missing field {key}")
            if e.get("intensity_band") not in BANDS:
                problems.append(f"{pid}/{eid}: bad band {e.get('intensity_band')}")
            if e.get("valence") not in VALENCES:
                problems.append(f"{pid}/{eid}: bad valence {e.get('valence')}")
            band_counts[e["intensity_band"]] = band_counts.get(e["intensity_band"], 0) + 1
            n_eps += 1
            sessions.add(e.get("session"))

            dt = datetime.fromisoformat(e["date_time"]).replace(tzinfo=timezone.utc)
            dts.append(dt)
            if dt >= NOW:
                problems.append(f"{pid}/{eid}: date {dt} not before NOW")
            age = (NOW - dt).days
            emo = e["intensity_band"] == "high"
            if age <= 6:
                age_cover[("short", emo)] += 1
            elif age > 30:
                age_cover[("long", emo)] += 1

            words = _words(e["text"])
            if not (15 <= len(words) <= 60):
                problems.append(f"{pid}/{eid}: {len(words)} words (spec: 15–60)")
            n_sent = len([s for s in re.split(r"[.!?]+", e["text"]) if s.strip()])
            if not (1 <= n_sent <= 3):
                problems.append(f"{pid}/{eid}: {n_sent} sentences (spec: 1–3)")

            probes = e.get("probes", [])
            types = [pr.get("type") for pr in probes]
            if sorted(types) != sorted(PROBE_TYPES):
                problems.append(f"{pid}/{eid}: probe types {types} (need one of each)")
            for pr in probes:
                prid = pr.get("id")
                if prid in all_probe_ids:
                    problems.append(f"{pid}/{eid}: duplicate probe id {prid}")
                all_probe_ids.add(prid)
                if pr["type"] == "reflective_implicit":
                    q = pr["query"]
                    overlap = _stems(q) & _stems(e["text"])
                    if overlap:
                        problems.append(f"{pid}/{eid}: implicit probe shares stems {sorted(overlap)}")
                    hits = [w for w in _words(q) if w in EMOTION_VOCAB]
                    if hits:
                        problems.append(f"{pid}/{eid}: implicit probe uses emotion words {hits}")

        if dts:
            span = (max(dts) - min(dts)).days
            if not (90 <= span <= 150):
                problems.append(f"{pid}: session span {span} d (spec: ~120, accept 90–150)")
        if not (10 <= len(sessions) <= 14):
            problems.append(f"{pid}: {len(sessions)} sessions (spec: 10–14)")

    if n_eps:
        for band, lo, hi in (("low", 0.35, 0.55), ("high", 0.30, 0.50), ("mild", 0.05, 0.25)):
            frac = band_counts[band] / n_eps
            if not (lo <= frac <= hi):
                problems.append(f"aggregate band {band}: {frac:.2f} outside [{lo}, {hi}]")
    for key, n in age_cover.items():
        if n == 0:
            problems.append(f"aggregate age coverage empty: {key} (range, emotional)")

    print(f"personas: {len(files)}  episodes: {n_eps}  probes: {len(all_probe_ids)}")
    print(f"bands: {band_counts}  age coverage (range, is_high): {age_cover}")
    if problems:
        print(f"\n{len(problems)} VIOLATIONS:")
        for p in problems:
            print(" -", p)
        return 1
    print("\nOK — corpus satisfies GENERATION_SPEC.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
