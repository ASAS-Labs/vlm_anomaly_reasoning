#!/usr/bin/env python3
"""Three-way fidelity decomposition: prompt <-> video <-> ID trajectory.

The semantic-agreement metric (prompt <-> ID) conflates two failure sources:
video generation not depicting the prompted action, and the ID pipeline not
reporting what the video depicts. This report separates them using the
optical-flow probe (video_motion.py) as an independent, model-free witness of
what each clip actually shows.

Accountability split:
  prompt <-> video   = generation fidelity  -> regeneration/exclusion list
  video  <-> ID      = ID pipeline accuracy -> the number that must reach 90%+

    python data/cosmos3/fidelity_report.py \
        --flow logs/id_flow_verdicts.json --out logs/id_fidelity_report.json
"""

import argparse
import collections
import json
import re
from pathlib import Path

from id_semantics import STOP_MPH
from video_motion import MIN_PEAK, MOVE_FLOW, STOP_FLOW

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def scenario(rel: str) -> str:
    stem = rel.split("/")[-1].replace(".mp4", "")
    pol = "neg" if "negative" in rel else "pos"
    return f"{pol}_{re.sub(r"_v\d+$", "", stem)}"


def video_end_state(r: dict) -> str:
    if r["peak_flow"] < MIN_PEAK:
        return "unmeasurable"
    if r["tail_flow"] < STOP_FLOW:
        return "stopped"
    if r["tail_flow"] > MOVE_FLOW:
        return "moving"
    return "ambiguous"


def video_matches_prompt(cls: str, r: dict) -> bool | None:
    """Does the pixel evidence realize the prompted end behaviour? None = can't judge."""
    end = video_end_state(r)
    if end in ("ambiguous", "unmeasurable"):
        return None
    if cls == "stop":
        return end == "stopped"
    if cls in ("maintain", "decelerate"):
        # maintain/decelerate prompts here never end in a stop
        return end == "moving"
    if cls in ("accelerate", "start_from_stop"):
        return r["head_flow"] < STOP_FLOW and end == "moving"
    return None


def id_matches_video(cls: str, r: dict) -> bool | None:
    """Does the ID trajectory's end state agree with the pixel evidence?"""
    end = video_end_state(r)
    if end in ("ambiguous", "unmeasurable"):
        return None
    id_stopped = r["id_v_final"] <= STOP_MPH
    if end == "stopped":
        return id_stopped
    return not id_stopped


def main():
    p = argparse.ArgumentParser(description="prompt<->video<->ID decomposition")
    p.add_argument("--flow", type=Path, default=REPO / "logs" / "id_flow_verdicts.json")
    p.add_argument("--out", type=Path, default=REPO / "logs" / "id_fidelity_report.json")
    p.add_argument("--regen-out", type=Path,
                   default=REPO / "logs" / "id_regeneration_list.json")
    args = p.parse_args()

    flow = json.loads(args.flow.read_text())

    rows = []
    for rel, r in sorted(flow.items()):
        rows.append({
            "rel_path": rel, "scenario": scenario(rel), "class": r["cls"],
            "video_end": video_end_state(r),
            "prompt_video": video_matches_prompt(r["cls"], r),
            "video_id": id_matches_video(r["cls"], r),
            "prompt_id": r["agree"],
            "id_v_final": r["id_v_final"], "tail_flow": r["tail_flow"],
            "head_flow": r["head_flow"],
        })

    def rate(vals):
        vals = [v for v in vals if v is not None]
        return (sum(vals), len(vals))

    pv = rate([x["prompt_video"] for x in rows])
    vi = rate([x["video_id"] for x in rows])
    pi = rate([x["prompt_id"] for x in rows])
    amb = sum(1 for x in rows if x["video_end"] in ("ambiguous", "unmeasurable"))

    print(f"n = {len(rows)} clips ({amb} ambiguous pixel verdicts excluded per-measure)\n")
    print(f"  VIDEO <-> ID      {vi[0]:>3}/{vi[1]:<3} = {vi[0]/vi[1]:.1%}   "
          f"<- ID pipeline accuracy (target 90%+)")
    print(f"  PROMPT <-> VIDEO  {pv[0]:>3}/{pv[1]:<3} = {pv[0]/pv[1]:.1%}   "
          f"<- generation fidelity (dataset quality)")
    print(f"  PROMPT <-> ID     {pi[0]:>3}/{pi[1]:<3} = {pi[0]/pi[1]:.1%}   "
          f"<- the conflated metric\n")

    print(f"{'scenario':<16} {'class':<12} {'vid<->ID':>9} {'prm<->vid':>10} {'prm<->ID':>9}")
    by = collections.defaultdict(list)
    for x in rows:
        by[x["scenario"]].append(x)
    for s in sorted(by, key=lambda s: rate([x["prompt_video"] for x in by[s]])[0]
                    / max(1, rate([x["prompt_video"] for x in by[s]])[1])):
        g = by[s]
        a = rate([x["video_id"] for x in g])
        b = rate([x["prompt_video"] for x in g])
        c = rate([x["prompt_id"] for x in g])
        print(f"{s:<16} {g[0]['class']:<12} {a[0]:>4}/{a[1]:<4} {b[0]:>5}/{b[1]:<4} "
              f"{c[0]:>4}/{c[1]:<4}")

    # Clips whose video never realizes the prompt: regenerate or exclude.
    regen = [{"rel_path": x["rel_path"], "scenario": x["scenario"], "class": x["class"],
              "video_end": x["video_end"], "id_v_final": x["id_v_final"],
              "tail_flow": x["tail_flow"]}
             for x in rows if x["prompt_video"] is False]
    args.regen_out.write_text(json.dumps(regen, indent=1))
    args.out.write_text(json.dumps({
        "summary": {"video_id": vi, "prompt_video": pv, "prompt_id": pi,
                    "ambiguous": amb, "n": len(rows)},
        "rows": rows}, indent=1))
    print(f"\nregeneration list ({len(regen)} clips): {args.regen_out}")
    print(f"full report: {args.out}")

    # Disagreements where ID contradicts the pixels: the true ID error cases.
    bad = [x for x in rows if x["video_id"] is False]
    if bad:
        print(f"\nID <-> video disagreements ({len(bad)}) — genuine ID errors to fix:")
        for x in bad:
            print(f"  {x['rel_path'].split('/')[-1]:<22} video={x['video_end']:<8} "
                  f"ID final={x['id_v_final']:>5.1f} mph  tail_flow={x['tail_flow']:.3f}")


if __name__ == "__main__":
    main()
