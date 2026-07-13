"""Build or verify the immutable EpiRec v1.0 release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ROOT / "data" / "personas"
OUT = ROOT / "data" / "epirec_v1.json"
MANIFEST = ROOT / "data" / "SHA256SUMS"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_release_text(path: Path, text: str, encoding: str) -> None:
    with path.open("w", encoding=encoding, newline="\n") as handle:
        handle.write(text)


def main(check: bool = False) -> int:
    from validate import build_payload, main as validate
    if validate(check_release=False):
        print("refusing to build an invalid corpus", file=sys.stderr)
        return 1
    personas = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(PERSONAS.glob("p*.json"))]
    rendered = json.dumps(build_payload(personas), indent=2, ensure_ascii=False) + "\n"
    if check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != rendered:
            print("release corpus is stale; run python scripts/build.py", file=sys.stderr)
            return 1
        expected = f"{digest(OUT)}  {OUT.name}\n"
        if not MANIFEST.exists() or MANIFEST.read_text(encoding="ascii") != expected:
            print("release SHA-256 manifest is stale; run python scripts/build.py", file=sys.stderr)
            return 1
        print("release corpus and SHA-256 manifest are current")
        return 0
    write_release_text(OUT, rendered, "utf-8")
    write_release_text(MANIFEST, f"{digest(OUT)}  {OUT.name}\n", "ascii")
    print(f"wrote {OUT}")
    print(f"wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated release files are stale")
    raise SystemExit(main(parser.parse_args().check))
