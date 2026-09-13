#!/usr/bin/env python3
"""Taxonomy-extension prompt tooling: gate | check | expectations.

  gate          all 100 extension rows decided -> VALID ids -> extension/manifest.json (k -> id)
  check         lint positive/negative prompt.txt (line count, blanks, style, motion class)
  expectations  freeze per-clip expectation classes from the sparse final sentences

Run from the repo root: uv run python data/cosmos3/extension_prompts.py <cmd> [--force]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from id_semantics import classify_expected  # noqa: E402
from prompt_resolve import last_sentence  # noqa: E402

TAXONOMY = REPO / "data" / "taxonomy_validation" / "taxonomy.json"
DB = REPO / "data" / "taxonomy_validation" / "decisions.sqlite"
POLARITIES = ("positive_scenarios", "negative_scenarios")
ROW_FIELDS = ("category", "object", "nominal_context", "ood_context", "normal_action",
              "anomalous_action", "example", "tag")


def load_manifest(ext: Path) -> dict:
    return json.loads((ext / "manifest.json").read_text())


def cmd_gate(args) -> int:
    rows = [r for r in json.loads(TAXONOMY.read_text())["rows"] if r["section"] == "extension"]
    ids = sorted(r["id"] for r in rows)
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    decided = dict(con.execute("SELECT row_id, value FROM decisions WHERE kind='validity'"))
    missing = [i for i in ids if i not in decided]
    if missing:
        print(f"gate NOT satisfied: {len(decided)}/{len(ids)} decided; undecided ids: {missing}")
        return 1
    valid = [i for i in ids if decided[i] == "VALID"]
    by_id = {r["id"]: r for r in rows}
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "n": len(valid),
        "clips": [{"k": k, "taxonomy_id": i, **{f: by_id[i][f] for f in ROW_FIELDS}}
                  for k, i in enumerate(valid)],
    }
    out = args.ext_dir / "manifest.json"
    if out.exists() and not args.force:
        old = [c["taxonomy_id"] for c in load_manifest(args.ext_dir)["clips"]]
        if old != valid:
            print(f"manifest exists with a different id list ({len(old)} ids); "
                  f"refusing to renumber without --force")
            return 1
        print("manifest unchanged")
        return 0
    args.ext_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    invalid = [i for i in ids if decided[i] == "INVALID"]
    print(f"gate satisfied: {len(valid)} VALID rows -> k 0..{len(valid) - 1}; "
          f"{len(invalid)} INVALID dropped: {invalid}")
    print("VALID ids:", valid)
    return 0


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def line_class(line: str) -> tuple[str | None, bool]:
    e = classify_expected(last_sentence(line))
    return e["speed"], bool(e["steer"])


def cmd_check(args) -> int:
    n = load_manifest(args.ext_dir)["n"]
    files = {p: args.ext_dir / p / "prompt.txt" for p in POLARITIES}
    problems: list[str] = []
    lines = {}
    for pol, path in files.items():
        if not path.exists():
            problems.append(f"{pol}: prompt.txt missing")
            continue
        raw = read_lines(path)
        if raw and raw[-1] == "":
            raw = raw[:-1]  # one trailing newline is fine
        if len(raw) != n:
            problems.append(f"{pol}: {len(raw)} lines, expected {n}")
        for k, ln in enumerate(raw):
            if not ln.strip():
                problems.append(f"{pol} k={k}: blank line")
                continue
            if not ln.startswith("The ego view of"):
                problems.append(f"{pol} k={k}: does not start with 'The ego view of'")
            if not ln.rstrip().endswith(")"):
                problems.append(f"{pol} k={k}: missing trailing timing parenthetical")
            if not 250 <= len(ln) <= 900:
                problems.append(f"{pol} k={k}: length {len(ln)} outside 250..900")
            if any(u in ln.lower() for u in (" mph", " km/h", " kph")):
                problems.append(f"{pol} k={k}: numeric speed unit")
            if "‘" in ln or "’" in ln or "“" in ln or "”" in ln:
                problems.append(f"{pol} k={k}: curly quotes (use ASCII)")
            spd, steer = line_class(ln)
            if spd is None and not steer:
                problems.append(f"{pol} k={k}: final sentence has no recognisable motion class: "
                                f"{last_sentence(ln)!r}")
        lines[pol] = raw
    if all(p in lines for p in POLARITIES):
        print(f"{'k':>3} {'id':>4} {'positive':>22} {'negative':>22} {'len+':>5} {'len-':>5}")
        clips = load_manifest(args.ext_dir)["clips"]
        for k in range(min(len(lines[POLARITIES[0]]), len(lines[POLARITIES[1]]))):
            lp, ln_ = lines[POLARITIES[0]][k], lines[POLARITIES[1]][k]
            cp, cn = line_class(lp), line_class(ln_)
            if cp == cn:
                problems.append(f"k={k}: positive and negative share the class {cp}")
            tid = clips[k]["taxonomy_id"] if k < len(clips) else "?"
            fmt = lambda c: f"{c[0]}{'+steer' if c[1] else ''}"  # noqa: E731
            print(f"{k:>3} {tid:>4} {fmt(cp):>22} {fmt(cn):>22} {len(lp):>5} {len(ln_):>5}")
    for p in problems:
        print("PROBLEM:", p)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_expectations(args) -> int:
    out = args.ext_dir / "expectations.json"
    if out.exists() and not args.force:
        print(f"{out} exists; refusing to overwrite without --force (expectations are frozen)")
        return 1
    clips = load_manifest(args.ext_dir)["clips"]
    exp = {}
    for pol in POLARITIES:
        raw = read_lines(args.ext_dir / pol / "prompt.txt")
        raw = raw[:-1] if raw and raw[-1] == "" else raw
        for k, ln in enumerate(raw):
            sent = last_sentence(ln)
            e = classify_expected(sent)
            exp[f"{pol}/prompt_{k}.mp4"] = {
                "class": e["speed"], "steer": bool(e["steer"]), "sentence": sent,
                "taxonomy_id": clips[k]["taxonomy_id"], "polarity": pol.split("_")[0], "k": k,
                "label": 1 if pol.startswith("negative") else 0,
            }
    bad = [r for r, e in exp.items() if e["class"] is None and not e["steer"]]
    if bad:
        print("unclassified:", bad)
        return 1
    out.write_text(json.dumps(exp, indent=1, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"wrote {out}: {len(exp)} clips;", dict(Counter(e["class"] for e in exp.values())))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["gate", "check", "expectations"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--ext-dir", type=Path, default=HERE / "video_gen_prompts" / "extension")
    ap.add_argument("--db", type=Path, default=DB)
    args = ap.parse_args()
    return {"gate": cmd_gate, "check": cmd_check, "expectations": cmd_expectations}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
