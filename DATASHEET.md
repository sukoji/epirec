# Datasheet for EpiRec v1.0

Following *Datasheets for Datasets* (Gebru et al., 2021).

## Motivation

**Why was the dataset created?** Memory-augmented conversational agents (journaling
assistants in particular) claim both factual lookup and *emotional resurfacing* —
retrieving an emotionally significant episode from a reflective, lexically-indirect
prompt. Public long-term-memory benchmarks (LoCoMo, LongMemEval, MSC) test factual
recall only and carry no emotional-salience labels, so the resurfacing claim could
previously only be tested on tiny author-made scenarios. EpiRec provides a labeled,
mechanically-validated corpus for exactly that claim.

**Who created it and who funded it?** Authored by Claude (Anthropic) in a session
supervised by Seokho Jin, who also maintains the Persode reference implementation —
an evaluated system. This conflict is disclosed prominently; see "Integrity" in the
README for mitigations. No external funding.

## Composition

- 12 fictional personas (ages 16–35), each with 14 first-person journal episodes
  (168 total) across 10–14 dated sessions spanning ~90–150 days.
- Each episode: `text` (15–60 words), `date_time`, `emotion` (free-form),
  `intensity_band` (high ≥ 0.7 / mild 0.4–0.6 / low ≤ 0.3, authored),
  `valence` (positive / negative / neutral, authored).
- Each episode has exactly 3 probes (504 total): `factual`,
  `reflective_explicit`, `reflective_implicit`. Single-target: each probe's answer
  is its own episode; probes are unambiguous within a persona by construction.
- Band mix: 72 high / 37 mild / 59 low. Valence: 82 positive / 38 negative /
  48 neutral. Both emotional and neutral episodes populate the short-term (≤ 6 days
  before the reference date) and long-term (> 30 days) age ranges.
- No splits: the corpus is evaluation-only (no training set).

## Collection / generation process

Fully synthetic; no human subjects, no scraped data, no real-person information.
Generation followed a **pre-registered specification** (GENERATION_SPEC.md) frozen
before authoring: independence rules (no consulting any evaluated system's lexicon;
no conditioning on any retrieval method's behaviour; symmetric probing of emotional
and neutral episodes), band/timeline quotas, and probe-construction rules.
`scripts/validate.py` mechanically enforces the rules — notably that
`reflective_implicit` probes share no content-word stems with their episode and use
no word from an independent emotion vocabulary. v1.0 has zero violations.

## Labeling

`intensity_band` and `valence` are assigned at authoring time as design targets
("gold by construction"), not derived from any model. Validation: a stratified
60-episode sample is independently rated by a human
(`human_validation/`); agreement will be reported in this datasheet, and episodes
whose human rating contradicts the authored band are flagged `label_disputed`
(and excluded from label-dependent metrics), never silently edited. Status:
**pending** as of v1.0 release.

## Recommended uses

- Evaluating retrieval / memory-selection components of episodic-memory agents,
  especially claims about emotional salience, time decay, and reflective recall.
- Studying the gap between explicit and implicit emotional phrasing in retrieval.

## Non-recommended uses

- Training data (tiny; evaluation-only).
- Any claim about *real human* emotional memory or journaling behaviour — the
  corpus is synthetic fiction; ecological validity requires user studies.
- Clinical or mental-health applications of any kind.

## Distribution & maintenance

GitHub: https://github.com/sukoji/epirec. Data CC BY 4.0, scripts MIT.
Versioned releases only; errors produce a v1.x changelog entry. Maintainer:
Seokho Jin (sukoji). Known limitations of v1.0: English-only; single-target
probes; authored (not naturally occurring) text; LLM authorship may carry the
generator's stylistic and cultural biases; size at the small end of accepted
retrieval benchmarks (~500 probes).
