"""Validate EpiRec source personas and the committed release artifact."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ROOT / "data" / "personas"
RELEASE = ROOT / "data" / "epirec_v1.json"
MANIFEST = ROOT / "data" / "SHA256SUMS"
CROISSANT = ROOT / "data" / "croissant.json"
NOW = datetime(2025, 6, 30, 12, tzinfo=timezone.utc)
BANDS = {"high", "mild", "low"}
VALENCES = {"positive", "negative", "neutral"}
TYPES = {"factual", "reflective_explicit", "reflective_implicit"}
EMOTION_WORDS = set("happy happiness joy joyful glad delight delighted excited excitement thrilled proud pride grateful gratitude love loved loving content contentment sad sadness unhappy sorrow sorrowful grief grieving heartbroken miserable depressed cry crying cried tears angry anger furious mad rage annoyed irritated frustrated frustrating frustration resentful upset afraid fear fearful scared terrified anxious anxiety nervous worried worry dread stressed stress panic ashamed shame embarrassed guilt guilty regret regretful lonely loneliness miss missed missing surprised surprise shocked astonished amazed disgust disgusted hate hated jealous envy envious hopeful hope hopeless despair relief relieved calm peaceful serene hurt hurting devastated overjoyed emotional emotion feelings feeling felt mourn mourning".split())
STOP = set("a an the this that these those i you he she it we they me my your his her its our their of to in on at by for with and or but if then so as is am are was were be been being do did does done have has had having im ive id its dont didnt cant wont not no yes very really just about into over under after before during when while where what who how why which there here out up down again still sometimes some any all both each few more most other than too can will would should could may might must day days week weeks month months year years time times back once twice around from same whole until till like first second third next last behind above below toward towards through because since longer anything everything someone something nothing different finally left took take taken kept keep made make went come came gone goes get got one two three four five six seven eight nine ten eleven twelve forty".split())


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def content_stems(text: str) -> set[str]:
    return {word[:6] for word in tokens(text) if word not in STOP and len(word) >= 4}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_datetime(value: object, label: str, issues: list[str]) -> datetime | None:
    if not isinstance(value, str):
        issues.append(f"{label}: date_time must be an ISO-8601 string with a UTC offset")
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        issues.append(f"{label}: invalid date_time {value!r}")
        return None
    if dt.tzinfo is None:
        issues.append(f"{label}: date_time must include a UTC offset")
        return None
    return dt.astimezone(timezone.utc)


def build_payload(personas: list[dict]) -> dict:
    episodes = [episode for persona in personas for episode in persona["episodes"]]
    probes = [probe for episode in episodes for probe in episode["probes"]]
    ages = [(NOW - datetime.fromisoformat(episode["date_time"]).astimezone(timezone.utc)).days for episode in episodes]
    return {
        "name": "EpiRec",
        "full_name": "Episodic Recall: A Benchmark for Emotional Resurfacing and Factual Lookup in Memory-Augmented Agents",
        "version": "1.0", "reference_now": NOW.isoformat(),
        "construction": "fixed construction protocol; see GENERATION_SPEC.md", "license": "CC BY 4.0",
        "stats": {
            "personas": len(personas), "episodes": len(episodes), "probes": len(probes),
            "intensity_bands": {band: sum(e["intensity_band"] == band for e in episodes) for band in ("high", "mild", "low")},
            "valences": {value: sum(e["valence"] == value for e in episodes) for value in ("positive", "negative", "neutral")},
            "probe_types": {kind: sum(p["type"] == kind for p in probes) for kind in ("factual", "reflective_explicit", "reflective_implicit")},
            "episode_age_days": {"min": min(ages), "max": max(ages)},
        }, "personas": personas,
    }


def main(check_release: bool = True) -> int:
    files, issues = sorted(PERSONAS.glob("p*.json")), []
    personas, episode_ids, probe_ids, texts, queries = [], set(), set(), {}, {}
    bands = {band: 0 for band in BANDS}
    coverage = {(span, high): 0 for span in ("short", "long") for high in (True, False)}
    for path in files:
        try:
            persona = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"{path.name}: invalid JSON ({exc.msg})")
            continue
        personas.append(persona)
        pid, episodes = persona.get("persona_id"), persona.get("episodes")
        if pid != path.stem: issues.append(f"{path.name}: persona_id must equal {path.stem!r}")
        if not isinstance(episodes, list) or not 14 <= len(episodes) <= 18:
            issues.append(f"{pid}: requires 14-18 episodes"); continue
        dates, sessions = [], set()
        for episode in episodes:
            eid, label = episode.get("id"), f"{pid}/{episode.get('id')}"
            required = {"id", "session", "date_time", "text", "emotion", "intensity_band", "valence", "probes"}
            if missing := required - set(episode): issues.append(f"{label}: missing fields {sorted(missing)}"); continue
            if eid in episode_ids: issues.append(f"{label}: duplicate episode id")
            episode_ids.add(eid)
            if not isinstance(episode["text"], str) or not episode["text"].strip(): issues.append(f"{label}: text must be non-empty")
            text_key = " ".join(tokens(episode["text"]))
            if text_key in texts: issues.append(f"{label}: duplicate episode text of {texts[text_key]}")
            texts[text_key] = label
            if episode["intensity_band"] not in BANDS or episode["valence"] not in VALENCES: issues.append(f"{label}: invalid intensity_band or valence")
            else: bands[episode["intensity_band"]] += 1
            dt = read_datetime(episode["date_time"], label, issues)
            if dt:
                dates.append(dt)
                if dt >= NOW: issues.append(f"{label}: date_time must precede reference_now")
                age = (NOW - dt).days
                if age <= 6: coverage[("short", episode["intensity_band"] == "high")] += 1
                elif age > 30: coverage[("long", episode["intensity_band"] == "high")] += 1
            sessions.add(episode["session"])
            count = len(tokens(episode["text"]))
            if not 15 <= count <= 60: issues.append(f"{label}: episode must contain 15-60 words")
            if not 1 <= len([x for x in re.split(r"[.!?]+", episode["text"]) if x.strip()]) <= 3: issues.append(f"{label}: episode must contain 1-3 sentences")
            probes = episode["probes"]
            if not isinstance(probes, list) or len(probes) != 3 or {probe.get("type") for probe in probes} != TYPES:
                issues.append(f"{label}: requires exactly one probe of each type"); continue
            for probe in probes:
                prid, query, probe_label = probe.get("id"), probe.get("query"), f"{label}/{probe.get('id')}"
                if prid in probe_ids: issues.append(f"{probe_label}: duplicate probe id")
                probe_ids.add(prid)
                if not isinstance(query, str) or not query.strip(): issues.append(f"{probe_label}: query must be non-empty"); continue
                query_key = " ".join(tokens(query))
                if query_key in queries: issues.append(f"{probe_label}: duplicate probe query of {queries[query_key]}")
                queries[query_key] = probe_label
                if probe["type"] == "reflective_implicit":
                    if overlap := content_stems(query) & content_stems(episode["text"]): issues.append(f"{probe_label}: implicit probe shares stems {sorted(overlap)}")
                    if hits := [word for word in tokens(query) if word in EMOTION_WORDS]: issues.append(f"{probe_label}: implicit probe uses emotion words {hits}")
        if dates and not 90 <= (max(dates) - min(dates)).days <= 150: issues.append(f"{pid}: session span must be 90-150 days")
        if not 10 <= len(sessions) <= 14: issues.append(f"{pid}: requires 10-14 sessions")
    total = sum(bands.values())
    for band, low, high in (("low", .35, .55), ("high", .30, .50), ("mild", .05, .25)):
        if total and not low <= bands[band] / total <= high: issues.append(f"aggregate {band} mix outside [{low}, {high}]")
    for key, count in coverage.items():
        if not count: issues.append(f"aggregate age coverage empty: {key}")
    if check_release and not issues:
        expected = build_payload(personas)
        if not RELEASE.exists() or json.loads(RELEASE.read_text(encoding="utf-8")) != expected: issues.append("release corpus differs from source personas; run scripts/build.py")
        expected_manifest = f"{digest(RELEASE)}  {RELEASE.name}\n" if RELEASE.exists() else ""
        if not MANIFEST.exists() or MANIFEST.read_text(encoding="ascii") != expected_manifest: issues.append("release SHA-256 manifest is missing or stale; run scripts/build.py")
        if not CROISSANT.exists():
            issues.append("missing data/croissant.json metadata")
        else:
            try:
                metadata = json.loads(CROISSANT.read_text(encoding="utf-8"))
                distribution = metadata.get("distribution", [{}])[0]
                if metadata.get("dct:conformsTo") != "http://mlcommons.org/croissant/1.1":
                    issues.append("Croissant metadata must declare version 1.1")
                if distribution.get("sha256") != digest(RELEASE):
                    issues.append("Croissant metadata SHA-256 is stale")
            except (json.JSONDecodeError, IndexError, TypeError):
                issues.append("data/croissant.json is invalid JSON-LD")
    print(f"personas: {len(personas)} episodes: {len(episode_ids)} probes: {len(probe_ids)}")
    print(f"bands: {bands}; age coverage: {coverage}")
    if issues:
        print(f"\n{len(issues)} violations:"); print("\n".join(f" - {issue}" for issue in issues)); return 1
    print("\nOK - corpus and release artifact satisfy the fixed protocol"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
