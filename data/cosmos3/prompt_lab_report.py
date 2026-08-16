#!/usr/bin/env python3
"""Per-round prompt-lab analysis: accuracy, paired stats vs P0, breadth, bias shift.

    python prompt_lab_report.py --round 1
"""

import argparse
import collections
import json
import math
import re
from pathlib import Path

from semantic_agreement import mcnemar

REPO = Path(__file__).resolve().parents[2]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - m, c + m)


def scenario(rel):
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--logs", type=Path, default=REPO / "logs")
    p.add_argument("--baseline", default="P0")
    args = p.parse_args()

    runs = {}
    for d in sorted(args.logs.glob(f"plab_r{args.round}_*")):
        vid = d.name.split("_", 2)[2]
        recs = {}
        for ln in (d / "results.jsonl").read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                recs[r["video"]] = r
        runs[vid] = recs
    if args.baseline not in runs:
        raise SystemExit(f"baseline {args.baseline} not found in round {args.round}")
    base = runs[args.baseline]
    common = set.intersection(*(set(r) for r in runs.values()))
    scens = sorted({scenario(v) for v in common})

    lines = [f"# Prompt lab — round {args.round}", "",
             f"n={len(common)} paired clips; baseline={args.baseline} "
             f"acc={sum(1 for v in common if base[v]['correct'])/len(common):.3f}",
             "",
             "| variant | acc | 95% CI | vs P0 net (p) | breadth | anomaly-verdicts | hypothesis |",
             "|---|---|---|---|---|---|---|"]
    summary = {}
    order = sorted(runs, key=lambda k: -sum(1 for v in common if runs[k][v]["correct"]))
    for vid in order:
        recs = runs[vid]
        k = sum(1 for v in common if recs[v]["correct"])
        lo, hi = wilson(k, len(common))
        ks = sorted(common)
        b_ok = [bool(base[v]["correct"]) for v in ks]
        v_ok = [bool(recs[v]["correct"]) for v in ks]
        lost, gained, pv = mcnemar(b_ok, v_ok)
        # breadth: scenarios strictly improved vs baseline
        breadth = 0
        for s in scens:
            clips = [v for v in common if scenario(v) == s]
            if sum(recs[v]["correct"] for v in clips) > sum(base[v]["correct"] for v in clips):
                breadth += 1
        n_anom = sum(1 for v in common if recs[v]["verdict"] == "Anomaly")
        hyp = next(iter(recs.values()))["hypothesis"]
        summary[vid] = {"acc": k / len(common), "ci": [lo, hi], "gained": gained,
                        "lost": lost, "p": pv, "breadth": breadth,
                        "anomaly_verdicts": n_anom}
        lines.append(f"| {vid} | {k/len(common):.3f} | [{lo:.3f},{hi:.3f}] | "
                     f"{gained - lost:+d} ({pv:.3f}) | {breadth}/{len(scens)} | "
                     f"{n_anom}/{len(common)} | {hyp} |")

    lines += ["", "## Per-scenario accuracy", "",
              "| scenario | n | " + " | ".join(order) + " |",
              "|" + "---|" * (len(order) + 2)]
    for s in scens:
        clips = [v for v in common if scenario(v) == s]
        row = [s, str(len(clips))]
        for vid in order:
            row.append(f"{sum(runs[vid][v]['correct'] for v in clips)}/{len(clips)}")
        lines.append("| " + " | ".join(row) + " |")

    # error autopsy pointers: clips the top non-baseline variant fixed/broke
    top = next(v for v in order if v != args.baseline)
    fixed = [v for v in sorted(common)
             if runs[top][v]["correct"] and not base[v]["correct"]]
    broke = [v for v in sorted(common)
             if not runs[top][v]["correct"] and base[v]["correct"]]
    lines += ["", f"## {top} vs {args.baseline}: flips",
              "", f"fixed ({len(fixed)}): " + ", ".join(x.split("/")[-1] for x in fixed),
              f"broke ({len(broke)}): " + ", ".join(x.split("/")[-1] for x in broke)]

    out_md = args.logs / f"prompt_lab_round{args.round}.md"
    out_json = args.logs / f"prompt_lab_round{args.round}.json"
    out_md.write_text("\n".join(lines) + "\n")
    out_json.write_text(json.dumps(
        {"round": args.round, "n": len(common), "summary": summary}, indent=1))
    print("\n".join(lines))
    print(f"\nwrote {out_md}")

    verd = collections.Counter(runs[top][v]["verdict"] for v in common)
    print(f"{top} verdict distribution: {dict(verd)}")


if __name__ == "__main__":
    main()
