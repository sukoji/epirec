<div align="center">

# EpiRec

**Episodic Recall: A Benchmark for Emotional Resurfacing and Factual Lookup in Memory-Augmented Agents**

[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-2a78d6.svg)](LICENSE)
[![Code: MIT](https://img.shields.io/badge/code-MIT-52514e.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0-1baf7a.svg)](data/epirec_v1.json)

</div>

Memory-augmented agents claim two different retrieval abilities that existing long-term-memory benchmarks ([LoCoMo](https://github.com/snap-research/locomo), LongMemEval) only test one of: **factual lookup** ("what did I order at the ramen place?") and **emotional resurfacing** — recalling an emotionally significant episode from a reflective, lexically-indirect prompt ("that evening by the water still comes back to me"). No public dataset carries emotional-salience labels. EpiRec fills that gap.

**12 personas · 168 first-person journal episodes · 504 probes**, fully synthetic, with authored intensity-band and valence labels, real session timestamps spanning ~120 days, and — the part that makes it hard — every episode probed three ways:

| Probe type | Construction rule | Example |
|---|---|---|
| `factual` | direct question about a concrete detail; may reuse content words | *"How much did Mochi weigh at the vet?"* |
| `reflective_explicit` | first-person reflection **naming the emotion** | *"I still feel overjoyed remembering the day my cat arrived."* |
| `reflective_implicit` | first-person reflection with **no emotion words and no content words reused** (mechanically enforced) | *"That evening a tiny creature chose to stay near me, and it keeps coming back to my mind."* |

<p align="center"><img src="docs/stats.png" width="92%" alt="EpiRec v1.0 corpus statistics"></p>

## Results (v1.0 baselines)

recall@3 per probe type, single-target, per-persona stores (14 episodes each). Reference baselines from [`scripts/baseline_retrieval.py`](scripts/baseline_retrieval.py); memory-model rows measured with [Persode](https://github.com/sukoji/persode) (`experiments/exp6_epirec.py`).

| Strategy (MiniLM embeddings) | factual | reflective explicit | **reflective implicit** | overall |
|---|---:|---:|---:|---:|
| recency-only | 0.21 | 0.21 | 0.21 | 0.21 |
| similarity-only (pure RAG) | 1.00 | 0.88 | **0.66** | 0.84 |
| salience-only (no similarity) | 0.21 | 0.21 | 0.21 | 0.21 |
| salience fusion, always-on (α = 0.5) | 0.99 | 0.82 | 0.60 | 0.80 |
| emotion-gated fusion | 1.00 | 0.87 | **0.66** | 0.84 |

What the benchmark shows so far:

- **The difficulty gradient works as designed**: factual (1.00) → explicit (0.88) → implicit (0.66) for every method and both embedders. The `reflective_implicit` stratum has real headroom — it is the open problem this benchmark poses.
- **A negative result the authors' own small-scale tests had missed**: always-on emotional-salience fusion loses to pure similarity on *every* stratum here — including the high-intensity emotional episodes it was designed for (0.60 vs 0.63 implicit-high) — because its emotional-intensity estimates come from a keyword analyzer that is too noisy at this scale. Emotion-gating restores parity but does not yet add gains. A salience prior earns its keep only with a better E estimator (e.g., an LLM analyzer) — untested, and exactly the kind of claim EpiRec exists to check.

## Using the data

```python
import json
corpus = json.load(open("data/epirec_v1.json", encoding="utf-8"))
for persona in corpus["personas"]:
    for ep in persona["episodes"]:          # id, text, date_time, emotion,
        for probe in ep["probes"]:          #   intensity_band, valence
            ...                             # probe: id, type, query; target = ep["id"]
```

Evaluation protocol (fixed in [GENERATION_SPEC.md](GENERATION_SPEC.md)): per persona, all episodes form one store; rank the store per probe; report recall@3 (primary), recall@1, MRR — overall, per probe type, and reflective probes stratified by intensity band. `reference_now` is the corpus anchor date for any time-aware model.

## Construction & integrity

- **Pre-registered**: [GENERATION_SPEC.md](GENERATION_SPEC.md) (persona shape, band mix, timeline coverage, probe rules, label protocol, eval protocol) was frozen before generation, and the corpus was frozen before any retrieval method ran on it.
- **Mechanically validated**: [`scripts/validate.py`](scripts/validate.py) enforces every spec rule — including that `reflective_implicit` probes share no content-word stems with their episode and use no word from an independent emotion vocabulary. v1.0 passes with zero violations.
- **Provenance, disclosed**: episodes and probes were authored by Claude (Anthropic) in a supervised session, by the same team that maintains one of the evaluated systems. Mitigations: the frozen spec, the mechanical validator, publication of every rule, and the fact that v1.0's headline finding is *negative* for that system's own mechanism.
- **Label validation**: authored band/valence labels are gold *by construction*; an independent human rating of a stratified 60-episode sample ships in [`human_validation/`](human_validation/) — status: **pending** (agreement will be reported here when complete; disputed episodes get flagged, never silently edited).
- **Ethics**: fully fictional personas, everyday emotional range, no crisis/medical/abuse content, no real persons or user data.

## Reproduce

```bash
python scripts/validate.py            # spec conformance (must pass)
python scripts/build.py               # regenerate data/epirec_v1.json + docs/stats.png
python scripts/baseline_retrieval.py  # reference baselines (numpy only; MiniLM optional)
```

## Versioning

The corpus is frozen per version. Errors are fixed by releasing v1.x with a changelog — never by silent in-place edits. Planned: v1.1 scale-up (~24 personas / ~1,000 probes), EpiRec-ko (Korean parallel corpus).

## License

Data: [CC BY 4.0](LICENSE). Scripts: MIT.

## Citation

```bibtex
@misc{epirec2026,
  title  = {EpiRec: Episodic Recall — A Benchmark for Emotional Resurfacing and
            Factual Lookup in Memory-Augmented Agents},
  author = {Jin, Seokho},
  year   = {2026},
  url    = {https://github.com/sukoji/epirec},
  note   = {Version 1.0. Synthetic corpus generated with Claude (Anthropic),
            pre-registered construction, mechanically validated}
}
```
