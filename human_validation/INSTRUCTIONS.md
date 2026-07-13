# Human label validation — rater instructions

Goal: independently check the authored `intensity_band` and `valence` labels on a
stratified sample of 60 episodes. Do NOT look at the persona files while rating.

1. Open `sample_for_rating.csv` (generate with `python human_validation/make_sample.py`).
2. For each episode text, fill in:
   - `rated_band`: how emotionally intense is this moment for the writer?
     - `high` — a moment that would clearly stay with them (strong joy, grief, fear, anger, relief…)
     - `mild` — noticeable feeling, but everyday-sized
     - `low` — routine; little or no emotional charge
   - `rated_valence`: `positive`, `negative`, or `neutral` overall for the writer.
3. Rate from the text alone; do not consult the stored labels.
4. Save the file as `ratings_<yourname>.csv` in this folder.

Reporting (done by the maintainer script, not the rater): exact-match agreement and
off-by-one-band agreement are published in DATASHEET.md; episodes where the human
band contradicts the authored band are flagged `label_disputed: true` in the next
corpus version and excluded from label-dependent metrics.
