#!/usr/bin/env python3
"""Automated realism pass over the extension's upsampled prompt JSONs.

Applies the release's proven prompt repairs by expectation class (stop ->
feasible_timing: 2 s smooth brake + locked-off hold; maintain -> explicit
no-braking constraint; accelerate/start_from_stop -> explicit pull-away),
plus a log-only lint. Idempotent: prompts already stamped `_regen_fix` are
reported as already_fixed. Writes extension/realism_changes.json.

  uv run python data/cosmos3/extension_realism_pass.py [--dry-run] [--targets logs/extension/roundN_targets.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from regen_fix import BRAKE_RE, _parse_range, _t, accelerate_reinforce, feasible_timing, maintain_reinforce  # noqa: E402

EXT = HERE / "video_gen_prompts" / "extension"
STATIONARY_RE = re.compile(r"stationary|standstill|remains stopped|comes to a (complete|full) stop|fully stopped", re.I)
NEGATED_BRAKE_RE = re.compile(r"\b(without|neither|no|never|not|nor)\s+(\w+\s+){0,2}?(slow\w*|brak\w*|decelerat\w*)"
                              r"(\s+(or|nor)\s+\w+)?", re.I)
EGO_BRAKE_RE = re.compile(r"\b(brakes|braking|brake hard|decelerat\w*|slows? down|slowing down|"
                          r"comes? to a (complete |full )?stop)\b", re.I)
MIN_HOLD = 1.5  # feasible_timing leaves >= 1.5 s of stationary hold (release recipe)


def lint(cls: str, p: dict) -> list[str]:
    out = []
    if p.get("duration") != "5s":
        out.append(f"duration {p.get('duration')!r} != '5s'")
    if p.get("fps") != 24:
        out.append(f"fps {p.get('fps')!r} != 24")
    for key, tkey in (("actions", "time"), ("segments", "time_range")):
        beats = p.get(key) or []
        if not beats:
            out.append(f"no {key}")
            continue
        try:
            a, b = _parse_range(beats[-1][tkey])
            if b - a < MIN_HOLD - 1e-6:
                out.append(f"last {key[:-1]} spans {b - a:.1f} s (< {MIN_HOLD} s)")
            if abs(b - 5.0) > 1e-6:
                out.append(f"last {key[:-1]} ends at {b} s, not 5 s")
        except Exception:  # noqa: BLE001
            out.append(f"unparseable {key} time {beats[-1].get(tkey)!r}")
    texts = [a["description"] for a in p.get("actions", [])] + [s["description"] for s in p.get("segments", [])]
    if cls in ("maintain",) and any(EGO_BRAKE_RE.search(NEGATED_BRAKE_RE.sub("", t)) for t in texts):
        out.append("maintain-class prompt describes braking/slowing")
    if cls == "stop":
        final = (p.get("actions") or [{}])[-1].get("description", "") + " " + (p.get("segments") or [{}])[-1].get("description", "")
        if not STATIONARY_RE.search(final):
            out.append("stop-class final beat does not say the vehicle is stationary")
    return out


STOP_PHRASE_RE = re.compile(r"comes? to a (complete |full )?stop|completes? a (smooth |full |complete )?stop|"
                            r"standstill|fully stopped|remains stationary", re.I)


def split_last_beat(p: dict) -> dict | None:
    """Brake and hold merged into the final beat -> two beats (brake, stationary hold).

    Applied per list (actions / segments) to whichever one ends in a brake-or-stop beat;
    the brake half is prefixed so feasible_timing recognises it (it rewrites that text anyway).
    """
    q = json.loads(json.dumps(p))
    touched = False
    for beats, tkey in ((q.get("actions") or [], "time"), (q.get("segments") or [], "time_range")):
        if not beats:
            continue
        last = beats[-1]["description"]
        if not (BRAKE_RE.search(last) or STOP_PHRASE_RE.search(last)):
            continue
        a, b = _parse_range(beats[-1][tkey])
        if b - a < 1.0 - 1e-6:
            continue
        mid = (a + b) / 2
        hold = json.loads(json.dumps(beats[-1]))
        beats[-1][tkey] = f"{_t(a)}-{_t(mid)}"
        beats[-1]["description"] = "The vehicle brakes: " + last
        hold[tkey] = f"{_t(mid)}-{_t(b)}"
        hold["description"] = "The vehicle is fully stopped and remains stationary."
        if "key_changes" in hold:
            hold["key_changes"] = "No motion; the vehicle is fully stopped"
        if "camera" in hold:
            hold["camera"] = "Static"
        if "segment_index" in hold:
            hold["segment_index"] = beats[-1]["segment_index"] + 1
        beats.append(hold)
        touched = True
    return q if touched else None


def stationary_throughout(p: dict) -> bool:
    """A stop-class prompt whose vehicle never moves (no brake beat; static camera or stationary final beat)."""
    acts = p.get("actions") or []
    if not acts or any(BRAKE_RE.search(a["description"]) for a in acts):
        return False
    cam = str((p.get("cinematography") or {}).get("camera_motion", "")).lower()
    return cam.startswith("static") or bool(STATIONARY_RE.search(acts[-1]["description"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--targets", type=Path, default=None, help="restrict to rel_paths listed in a targets json")
    ap.add_argument("--ext-dir", type=Path, default=EXT)
    args = ap.parse_args()
    exp = json.loads((args.ext_dir / "expectations.json").read_text())
    rels = [t["rel_path"] for t in json.loads(args.targets.read_text())] if args.targets else list(exp)
    log_path = args.ext_dir / "realism_changes.json"
    changes = json.loads(log_path.read_text()) if log_path.exists() else []
    ts = datetime.now().isoformat(timespec="seconds")
    for rel in rels:
        cls, jpath = exp[rel]["class"], args.ext_dir / rel.replace(".mp4", ".json")
        if not jpath.exists():
            changes.append({"rel_path": rel, "class": cls, "action": "missing_json", "ts": ts})
            continue
        before = json.loads(jpath.read_text())
        entry = {"rel_path": rel, "class": cls, "ts": ts, "lint": lint(cls, before)}
        after = None
        if before.get("_regen_fix"):
            entry["action"] = "already_fixed"
        elif cls == "stop":
            after = feasible_timing(before)
            split = None
            if after is None:
                split = split_last_beat(before)
                after = feasible_timing(split) if split is not None else None
            if after is None and stationary_throughout(before):
                entry["action"] = "stationary_throughout"
            elif after is None:
                entry["action"] = "manual"
                entry["reason"] = "brake/hold beat structure not recognised; split the last beat by hand"
            else:
                after["_regen_fix"] = {"feasible_timing": True, "ts": ts,
                                       "old_times": [a["time"] for a in before["actions"]],
                                       "new_times": [a["time"] for a in after["actions"]]}
                if split is not None:
                    after["_regen_fix"]["split_last_beat"] = True
                entry.update(action="rewritten" if split is None else "split+rewritten",
                             old_times=after["_regen_fix"]["old_times"],
                             new_times=after["_regen_fix"]["new_times"])
        elif cls in ("maintain", "decelerate"):
            after = maintain_reinforce(before)
            after["_regen_fix"] = {"maintain_reinforce": True, "ts": ts}
            entry["action"] = "reinforced"
        elif cls in ("accelerate", "start_from_stop"):
            after = accelerate_reinforce(before)
            after["_regen_fix"] = {"accelerate_reinforce": True, "ts": ts}
            entry["action"] = "reinforced"
        else:
            entry["action"] = "unchanged"
        if after is not None:
            entry["lint_after"] = lint(cls, after)
            if not args.dry_run:
                jpath.write_text(json.dumps(after, indent=2, ensure_ascii=False) + "\n")
        changes.append(entry)
    if not args.dry_run:
        log_path.write_text(json.dumps(changes, indent=1, ensure_ascii=False) + "\n")
    this = changes[-len(rels):]
    print(dict(Counter(c["action"] for c in this)), "" if args.dry_run else f"-> {log_path}")
    for c in this:
        if c["action"] == "manual":
            print("MANUAL:", c["rel_path"], "-", c["reason"])
        for w in c.get("lint_after", c.get("lint", [])):
            print("LINT:", c["rel_path"], "-", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
