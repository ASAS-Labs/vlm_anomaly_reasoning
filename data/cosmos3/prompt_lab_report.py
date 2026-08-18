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
    p.add_argument("--prefix", default=None,
                   help="results-dir prefix (default plab_r<round>)")
    args = p.parse_args()

    prefix = args.prefix or f"plab_r{args.round}"
    runs = {}
    for d in sorted(args.logs.glob(f"{prefix}_*")):
        vid = d.name[len(prefix) + 1:]
        recs = {}
        for ln in (d / "results.jsonl").read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                recs[r["video"]] = r
        runs[vid] = recs
    if args.baseline not in runs:
        raise SystemExit(f"baseline {args.baseline} not found in round {args.round}")
    counts = {vid: len(recs) for vid, recs in runs.items()}
    if len(set(counts.values())) > 1 or 0 in counts.values():
        # A stale/partial dir would silently shrink the paired intersection
        # for every arm; fail loudly instead.
        raise SystemExit(f"record-count mismatch across {prefix}_* dirs: {counts}")
    base = runs[args.baseline]
    common = set.intersection(*(set(r) for r in runs.values()))
    scens = sorted({scenario(v) for v in common})

    lines = [f"# Prompt lab — round {args.round} ({prefix})", "",
             f"n={len(common)} paired clips; baseline={args.baseline} "
             f"acc={sum(1 for v in common if base[v]['correct'] is True)/len(common):.3f}",
             "",
             "| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | "
             "breadth | anomaly-verdicts | trunc | hypothesis |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    summary = {}
    order = sorted(runs, key=lambda k: -sum(1 for v in common if runs[k][v]["correct"]))
    for vid in order:
        recs = runs[vid]
        k = sum(1 for v in common if recs[v]["correct"] is True)
        lo, hi = wilson(k, len(common))
        ks = sorted(common)
        b_ok = [base[v]["correct"] is True for v in ks]
        v_ok = [recs[v]["correct"] is True for v in ks]
        lost, gained, pv = mcnemar(b_ok, v_ok)
        # breadth: scenarios strictly improved vs baseline
        breadth = 0
        for s in scens:
            clips = [v for v in common if scenario(v) == s]
            if sum(recs[v]["correct"] is True for v in clips) > sum(base[v]["correct"] is True for v in clips):
                breadth += 1
        n_anom = sum(1 for v in common if recs[v]["verdict"] == "Anomaly")
        # strict-all recall/specificity/balanced accuracy (Unknown counts wrong)
        anom = [v for v in common if recs[v]["true_label"] == 1]
        norm = [v for v in common if recs[v]["true_label"] == 0]
        rec_ = sum(recs[v]["correct"] is True for v in anom) / max(1, len(anom))
        spec = sum(recs[v]["correct"] is True for v in norm) / max(1, len(norm))
        balacc = (rec_ + spec) / 2
        trunc = sum(1 for v in common
                    if recs[v].get("finish_reason") == "length")
        hyp = next(iter(recs.values()))["hypothesis"]
        summary[vid] = {"acc": k / len(common), "ci": [lo, hi], "gained": gained,
                        "lost": lost, "p": pv, "breadth": breadth,
                        "anomaly_verdicts": n_anom, "balacc": balacc,
                        "recall": rec_, "specificity": spec, "truncated": trunc}
        lines.append(f"| {vid} | {k/len(common):.3f} | [{lo:.3f},{hi:.3f}] | "
                     f"{balacc:.3f} | {rec_:.2f}/{spec:.2f} | "
                     f"{gained - lost:+d} ({pv:.3f}) | {breadth}/{len(scens)} | "
                     f"{n_anom}/{len(common)} | {trunc} | {hyp} |")

    lines += ["", "## Per-scenario accuracy", "",
              "| scenario | n | " + " | ".join(order) + " |",
              "|" + "---|" * (len(order) + 2)]
    for s in scens:
        clips = [v for v in common if scenario(v) == s]
        row = [s, str(len(clips))]
        for vid in order:
            row.append(f"{sum(runs[vid][v]['correct'] is True for v in clips)}/{len(clips)}")
        lines.append("| " + " | ".join(row) + " |")

    # error autopsy pointers: clips the top non-baseline variant fixed/broke
    top = next((v for v in order if v != args.baseline), None)
    if top is None:
        top = args.baseline
    fixed = [v for v in sorted(common)
             if runs[top][v]["correct"] is True and base[v]["correct"] is not True]
    broke = [v for v in sorted(common)
             if runs[top][v]["correct"] is not True and base[v]["correct"] is True]
    lines += ["", f"## {top} vs {args.baseline}: flips",
              "", f"fixed ({len(fixed)}): " + ", ".join(x.split("/")[-1] for x in fixed),
              f"broke ({len(broke)}): " + ", ".join(x.split("/")[-1] for x in broke)]

    stem = f"prompt_lab_{prefix}" if args.prefix else f"prompt_lab_round{args.round}"
    out_md = args.logs / f"{stem}.md"
    out_json = args.logs / f"{stem}.json"
    out_md.write_text("\n".join(lines) + "\n")
    out_json.write_text(json.dumps(
        {"round": args.round, "n": len(common), "summary": summary}, indent=1))
    print("\n".join(lines))
    print(f"\nwrote {out_md}")

    verd = collections.Counter(runs[top][v]["verdict"] for v in common)
    print(f"{top} verdict distribution: {dict(verd)}")


if __name__ == "__main__":
    main()
