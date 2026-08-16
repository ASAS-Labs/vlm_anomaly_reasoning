#!/usr/bin/env python3
"""Collate the six subset-eval runs into one report with paired statistics.

Reads logs/subset_{style}_{mode}/results.jsonl for style in {direct, think} and
mode in {no_action_grounding, action_grounding, action_grounding_velocity};
writes logs/subset_eval_report.json and .md.

    python data/cosmos3/collate_subset_results.py
"""

import argparse
import collections
import json
import math
import re
from pathlib import Path

from semantic_agreement import mcnemar

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

STYLES = ("direct", "think")
MODES = ("no_action_grounding", "action_grounding", "action_grounding_velocity")
MODE_SHORT = {"no_action_grounding": "video-only",
              "action_grounding": "action (v+h)",
              "action_grounding_velocity": "velocity-only"}


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


def load_run(d: Path):
    recs = {}
    for ln in (d / "results.jsonl").read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            recs[r["video"]] = r
    return recs


def run_metrics(recs):
    tp = sum(1 for r in recs.values() if r["verdict"] == "Anomaly" and r["true_label"] == 1)
    fp = sum(1 for r in recs.values() if r["verdict"] == "Anomaly" and r["true_label"] == 0)
    tn = sum(1 for r in recs.values() if r["verdict"] == "Normal" and r["true_label"] == 0)
    fn = sum(1 for r in recs.values() if r["verdict"] == "Normal" and r["true_label"] == 1)
    n = len(recs)
    unres = n - (tp + fp + tn + fn)
    acc = (tp + tn) / n if n else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    lats = [r["latency_s"] for r in recs.values() if r.get("latency_s")]
    return {"n": n, "unresolved": unres, "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "accuracy": acc, "acc_ci": wilson(tp + tn, n),
            "precision": prec, "recall": rec, "specificity": spec,
            "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
            "mean_latency_s": sum(lats) / len(lats) if lats else 0.0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--logs", type=Path, default=REPO / "logs")
    p.add_argument("--out-json", type=Path, default=REPO / "logs" / "subset_eval_report.json")
    p.add_argument("--out-md", type=Path, default=REPO / "logs" / "subset_eval_report.md")
    args = p.parse_args()

    runs, metrics = {}, {}
    for style in STYLES:
        for mode in MODES:
            d = args.logs / f"subset_{style}_{mode}"
            if not (d / "results.jsonl").exists():
                print(f"  missing: {d}")
                continue
            key = f"{style}/{mode}"
            runs[key] = load_run(d)
            metrics[key] = run_metrics(runs[key])

    keys = sorted(runs)
    common = set.intersection(*(set(r) for r in runs.values())) if runs else set()
    any_run = next(iter(runs.values()))
    n_anom = sum(1 for r in any_run.values() if r["true_label"] == 1)
    n_norm = len(any_run) - n_anom
    majority = max(n_anom, n_norm) / len(any_run)

    lines = ["# Subset evaluation report",
             "",
             f"72-clip prompt-video-ID agreement subset ({n_anom} anomaly / {n_norm} "
             f"normal), fixed v1_resample trajectories, example-free think prompt.",
             f"Majority-class baseline (always Anomaly): **{majority:.1%}**. "
             f"n={len(common)} paired; Wilson 95% CIs span roughly ±11 points.",
             "",
             "| run | acc | 95% CI | P | R | spec | F1 | lat |",
             "|---|---|---|---|---|---|---|---|"]
    for k in keys:
        m = metrics[k]
        lo, hi = m["acc_ci"]
        lines.append(f"| {k} | {m['accuracy']:.3f} | [{lo:.3f}, {hi:.3f}] | "
                     f"{m['precision']:.3f} | {m['recall']:.3f} | {m['specificity']:.3f} | "
                     f"{m['f1']:.3f} | {m['mean_latency_s']:.2f}s |")

    lines += ["", "## Paired comparisons (McNemar, exact two-sided)", "",
              "| comparison | gains | loses | net | p |", "|---|---|---|---|---|"]
    pairs = []
    for style in STYLES:
        pairs += [(f"{style}/action_grounding", f"{style}/no_action_grounding"),
                  (f"{style}/action_grounding_velocity", f"{style}/no_action_grounding"),
                  (f"{style}/action_grounding_velocity", f"{style}/action_grounding")]
    pairs += [("think/no_action_grounding", "direct/no_action_grounding"),
              ("think/action_grounding", "direct/action_grounding")]
    comparisons = []
    for a, b in pairs:
        if a not in runs or b not in runs:
            continue
        ks = sorted(common)
        a_ok = [bool(runs[a][k]["correct"]) for k in ks]
        b_ok = [bool(runs[b][k]["correct"]) for k in ks]
        lost, gained, pv = mcnemar(b_ok, a_ok)
        comparisons.append({"a": a, "b": b, "gains": gained, "loses": lost, "p": pv})
        lines.append(f"| {a} vs {b} | {gained} | {lost} | {gained - lost:+d} | {pv:.3g} |")

    lines += ["", "## Per-scenario accuracy", ""]
    scen_rows = {}
    header = "| scenario | n | " + " | ".join(k for k in keys) + " |"
    lines += [header, "|" + "---|" * (len(keys) + 2)]
    scens = sorted({scenario(r) for r in common})
    for s in scens:
        clips = [r for r in common if scenario(r) == s]
        row = [s, str(len(clips))]
        accs = {}
        for k in keys:
            ok = sum(1 for c in clips if runs[k][c]["correct"])
            accs[k] = ok / len(clips)
            row.append(f"{ok}/{len(clips)}")
        scen_rows[s] = accs
        lines.append("| " + " | ".join(row) + " |")

    args.out_json.write_text(json.dumps({
        "subset_n": len(common), "anomaly": n_anom, "normal": n_norm,
        "majority_baseline": majority,
        "metrics": metrics, "comparisons": comparisons,
        "per_scenario": scen_rows}, indent=1))
    args.out_md.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {args.out_json}\nwrote {args.out_md}")

    # quick verdict-distribution sanity line
    for k in keys:
        c = collections.Counter(r["verdict"] for r in runs[k].values())
        print(f"  {k}: {dict(c)}")


if __name__ == "__main__":
    main()
