"""Reference baselines for EpiRec — self-contained, no framework required.

Per persona, all episodes form one memory store; each probe queries that store.
Strategies here are the memory-model-free reference points:

- recency-only: rank episodes newest-first (query-independent)
- similarity (hashing): deterministic hashed bag-of-words cosine
- similarity (MiniLM): sentence-transformers all-MiniLM-L6-v2, if installed

Metrics (fixed in GENERATION_SPEC.md): recall@3 (primary), recall@1, MRR —
overall and per probe type. Each probe has exactly one target episode.
Memory-model baselines (salience fusion, gating, decay) live with the systems
being evaluated, e.g. github.com/sukoji/persode.

    python scripts/baseline_retrieval.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "epirec_v1.json"
TYPES = ("factual", "reflective_explicit", "reflective_implicit")


def hash_embed(text: str, dim: int = 256) -> np.ndarray:
    vec = np.zeros(dim)
    for tok in re.findall(r"[a-z0-9']+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0 if (h >> 8) % 2 == 0 else -1.0
    n = np.linalg.norm(vec)
    return vec / n if n else vec


def evaluate(embed) -> dict:
    corpus = json.loads(DATA.read_text(encoding="utf-8"))
    per_type = {t: {"r3": [], "r1": [], "mrr": []} for t in TYPES}

    for persona in corpus["personas"]:
        eps = persona["episodes"]
        ids = [e["id"] for e in eps]
        if embed is None:  # recency
            order = sorted(range(len(eps)), reverse=True,
                           key=lambda i: datetime.fromisoformat(eps[i]["date_time"]))
            rankings = {None: [ids[i] for i in order]}
        else:
            M = np.stack([embed(e["text"]) for e in eps])
        for e in eps:
            for pr in e["probes"]:
                if embed is None:
                    ranked = rankings[None]
                else:
                    sims = M @ embed(pr["query"])
                    ranked = [ids[i] for i in np.argsort(-sims)]
                rank = ranked.index(e["id"]) + 1
                m = per_type[pr["type"]]
                m["r3"].append(float(rank <= 3))
                m["r1"].append(float(rank == 1))
                m["mrr"].append(1.0 / rank)

    out = {}
    for t, m in per_type.items():
        out[t] = {k: round(float(np.mean(v)), 3) for k, v in m.items()}
    allv = {k: round(float(np.mean([x for t in TYPES for x in per_type[t][k]])), 3)
            for k in ("r3", "r1", "mrr")}
    out["overall"] = allv
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    runs = {
        "recency-only": evaluate(None),
        "similarity (hashing)": evaluate(hash_embed),
    }
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        cache: dict[str, np.ndarray] = {}

        def st_embed(text: str) -> np.ndarray:
            v = cache.get(text)
            if v is None:
                v = model.encode([text], normalize_embeddings=True)[0]
                cache[text] = v
            return v

        runs["similarity (MiniLM)"] = evaluate(st_embed)
    except ImportError:
        print("sentence-transformers not installed — MiniLM baseline skipped")

    for name, res in runs.items():
        print(f"\n### {name}")
        for t in (*TYPES, "overall"):
            r = res[t]
            print(f"  {t:21s} recall@3={r['r3']:.3f}  recall@1={r['r1']:.3f}  MRR={r['mrr']:.3f}")

    (ROOT / "docs" / "baselines.json").write_text(json.dumps(runs, indent=2))
    print(f"\nwrote {ROOT / 'docs' / 'baselines.json'}")


if __name__ == "__main__":
    main()
