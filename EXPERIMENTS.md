# EpiRec Experiment Protocol

EpiRec v1.0 is a small diagnostic benchmark. A publishable claim requires a
system comparison under the fixed protocol below; do not infer system quality
from the reference lexical baselines alone.

## Required evaluation

1. Build a separate memory store for each persona using its 14 episodes only.
2. For every one of the 504 probes, return a permutation of all 14 episode IDs
   for that persona. Do not add oracle filtering, query-specific prompt
   examples, or external memories.
3. Run the official evaluator:

```bash
python scripts/evaluate_rankings.py \
  --rankings path/to/system_rankings.jsonl \
  --output results/system_name.json
```

Each JSONL line must be:

```json
{"persona_id":"p01","probe_id":"p01e01-f","ranked_episode_ids":["p01e01","p01e04"]}
```

The example is abbreviated; each ranking must contain every one of that
persona's 14 episode IDs exactly once. The evaluator rejects partial rankings,
duplicates, unknown IDs, and missing probes.

## Report card

Report recall@3 as the primary metric, alongside recall@1 and MRR with the
evaluator's deterministic probe-level bootstrap 95% confidence intervals.
Include the evaluator-produced groups: probe type, probe type x intensity band,
and probe type x age bucket. Publish the exact ranking JSONL, result JSON,
commit hash, model and embedding revision, prompts, decoding configuration,
hardware, wall-clock time, and API cost where applicable.

Do not present a single aggregate score as evidence for emotional retrieval.
The factual, explicit-reflection, and implicit-reflection columns answer
different questions.

## Minimum comparison set

The following local baselines are feasible and should be reported before any
claim about emotion-aware memory:

| ID | System | Fixed control |
|---|---|---|
| R1 | Recency | rank only by episode timestamp |
| R2 | Dense retrieval | one frozen encoder, cosine ranking |
| R3 | Time-decay retrieval | R2 plus fixed temporal decay |
| R4 | Salience fusion | R2 plus authored/estimated salience signal |
| R5 | Emotion-gated fusion | R4 only when a frozen query emotion score crosses a pre-registered threshold |

R3, R4, and R5 must use the same encoder, corpus, candidate set, top-k, and
time reference as R2. State all weights and thresholds before running the
final test. Pair every claimed component with its removal ablation.

## Related systems: feasibility

| System | Status for EpiRec | Conditions for a valid comparison |
|---|---|---|
| Persode | Directly feasible | Export its ranking for all probes; evaluate R1-R5 under the same encoder and time reference. |
| [LUFY](https://github.com/ryuichi-sumida/LUFY) | Feasible adapter study | Its released implementation uses an OpenAI API workflow. Pin the API model, prompt, temperature, retrieval depth, and cost; label the result as an adaptation, not a reproduction. |
| [Letta](https://github.com/letta-ai/letta) / MemGPT | Feasible system integration | Fix memory ingestion order, agent model, context limit, tools, and retrieval-only controls. Report cost and latency. |
| [LongMem](https://github.com/Victorwz/LongMem) | Not an immediate baseline | It is training-oriented; an apples-to-apples result needs a training budget and a documented adaptation. |
| [LongMemEval](https://github.com/xiaowu0162/longmemeval) | External-validity companion | Use it after EpiRec for factual long-memory coverage; it is not a direct EpiRec baseline. |

## Release status

v1.0 ships reference retrieval baselines only. It does not yet ship a claimed
winner among memory architectures. Add a versioned `results/` directory only
after the full matrix, configurations, and ranking artifacts above are present.
Human label-audit agreement is also pending; intensity and valence strata should
be described as authored design labels until that audit is released.
