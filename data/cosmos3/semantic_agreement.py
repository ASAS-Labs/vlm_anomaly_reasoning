#!/usr/bin/env python3
"""Score trajectory variants against what their prompts say the vehicle did.

This is the primary evidence for whether an ID fix worked, and it needs no VLM: it
asks directly whether a clip whose prompt says "comes to a complete stop" produces a
trajectory that actually reaches zero.

Expectations are frozen to a committed JSON file first, so the language classifier
cannot drift between variants and every variant is judged against identical labels.

    python data/cosmos3/semantic_agreement.py --freeze-expectations
    python data/cosmos3/semantic_agreement.py --variants-root data/datasets/id_variants
"""

import argparse
import json
import math
from pathlib import Path

from id_semantics import STOP_MPH, check_match, classify_expected, evaluate_sequence
from prompt_resolve import prompt_sentence_for
from utils import discover_eval_videos

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_SRC = REPO / "data" / "datasets" / "generated_vids"
DEFAULT_PROMPTS = HERE / "video_gen_prompts"
EXPECTATIONS = HERE / "id_expectations.json"


def freeze(src, prompts_root, out):
    """Classify every eval clip's prompt once and commit the result."""
    exp = {}
    unclassified = []
    for it in discover_eval_videos(src):
        sentence = prompt_sentence_for(Path(it["rel_path"]), prompts_root)
        if sentence is None:
            unclassified.append(it["rel_path"])
            continue
        e = classify_expected(sentence)
        if e["speed"] is None and not e["steer"]:
            unclassified.append(it["rel_path"])
        exp[it["rel_path"]] = {"class": e["speed"], "steer": e["steer"],
                               "sentence": sentence}
    out.write_text(json.dumps(exp, indent=2, sort_keys=True))
    counts = {}
    for v in exp.values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    print(f"froze {len(exp)} expectations -> {out}")
    print(f"  classes: {counts}")
    print(f"  steer flagged: {sum(1 for v in exp.values() if v['steer'])}")
    if unclassified:
        print(f"  WARNING {len(unclassified)} unclassified, e.g. {unclassified[:3]}")


def mcnemar(a_ok, b_ok):
    """Exact two-sided McNemar on paired boolean vectors."""
    b = sum(1 for x, y in zip(a_ok, b_ok) if x and not y)
    c = sum(1 for x, y in zip(a_ok, b_ok) if y and not x)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n) * 2
    return b, c, min(1.0, p)


def score(tree: Path, expectations: dict) -> dict:
    """Per-clip agreement plus diagnostics for one variant tree."""
    per_clip, stats_all = {}, []
    for it in discover_eval_videos(tree, strict=False):
        rel = it["rel_path"]
        exp = expectations.get(rel)
        if exp is None or exp["class"] is None:
            continue
        seq = json.loads(
            it["abs_path"].with_name(it["abs_path"].stem + ".txt").read_text())
        st = evaluate_sequence(seq)
        ok, reasons = check_match({"speed": exp["class"], "steer": exp["steer"]}, st)
        per_clip[rel] = {"class": exp["class"], "agree": ok, "reasons": reasons, **st}
        stats_all.append(per_clip[rel])
    return per_clip


def summarize(name, per_clip):
    n = len(per_clip)
    if not n:
        return {}
    agree = sum(1 for r in per_clip.values() if r["agree"])
    by_class = {}
    for r in per_clip.values():
        c = by_class.setdefault(r["class"], [0, 0])
        c[1] += 1
        c[0] += int(r["agree"])
    stops = [r for r in per_clip.values() if r["class"] == "stop"]
    maint = [r for r in per_clip.values() if r["class"] == "maintain"]

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else float("nan")

    t_stop = [r["t_first_below_stop"] for r in stops if r["t_first_below_stop"] is not None]
    return {
        "variant": name, "n": n, "agree": agree, "rate": agree / n,
        "by_class": {k: {"agree": v[0], "n": v[1], "rate": v[0] / v[1]}
                     for k, v in sorted(by_class.items())},
        "stop_median_end_v": med([r["v_final"] for r in stops]),
        "stop_p_reaches_zero": (sum(1 for r in stops if r["v_final"] <= STOP_MPH)
                                / len(stops)) if stops else float("nan"),
        "stop_median_t_first_stop": med(t_stop) if t_stop else None,
        "stop_n": len(stops),
        "maintain_median_cruise": med([r["start_v"] for r in maint]),
        "pct_v_max_over_100": sum(1 for r in per_clip.values() if r["v_max"] > 100) / n,
        "pct_edge_outlier": sum(1 for r in per_clip.values() if r["edge_outlier"]) / n,
        "median_mean_abs_dv": med([r["mean_abs_dv"] for r in per_clip.values()]),
    }


def main():
    p = argparse.ArgumentParser(description="Semantic agreement of ID trajectories")
    p.add_argument("--freeze-expectations", action="store_true")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--prompts-root", type=Path, default=DEFAULT_PROMPTS)
    p.add_argument("--expectations", type=Path, default=EXPECTATIONS)
    p.add_argument("--variants-root", type=Path,
                   default=REPO / "data" / "datasets" / "id_variants")
    p.add_argument("--baseline", default="v0_baseline")
    p.add_argument("--out", type=Path, default=REPO / "logs" / "id_semantic_agreement.json")
    args = p.parse_args()

    if args.freeze_expectations:
        freeze(args.src, args.prompts_root, args.expectations)
        return

    expectations = json.loads(args.expectations.read_text())
    trees = sorted(d for d in args.variants_root.iterdir() if d.is_dir())
    if not trees:
        raise SystemExit(f"no variant trees under {args.variants_root}")

    scored = {t.name: score(t, expectations) for t in trees}
    # Compare only over clips every variant covers, so the numbers are paired.
    common = set.intersection(*(set(v) for v in scored.values() if v)) if scored else set()
    print(f"{len(trees)} variants, {len(common)} clips common to all\n")

    rows = []
    for name in sorted(scored):
        pc = {k: v for k, v in scored[name].items() if k in common}
        rows.append(summarize(name, pc))

    hdr = (f"{'variant':<14} {'agree':>12} {'stop end_v':>11} {'P(stop=0)':>10} "
           f"{'t_stop':>7} {'cruise':>7} {'edge%':>6} {'|dv|':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if not r:
            continue
        t = r["stop_median_t_first_stop"]
        print(f"{r['variant']:<14} {r['agree']:>4}/{r['n']:<4} {r['rate']:>5.1%} "
              f"{r['stop_median_end_v']:>11.1f} {r['stop_p_reaches_zero']:>10.1%} "
              f"{(f'{t:.2f}' if t is not None else '  -- '):>7} "
              f"{r['maintain_median_cruise']:>7.1f} {r['pct_edge_outlier']:>5.1%} "
              f"{r['median_mean_abs_dv']:>6.2f}")

    base = scored.get(args.baseline)
    if base:
        print(f"\npaired vs {args.baseline} (McNemar, exact two-sided):")
        keys = sorted(common)
        b_ok = [base[k]["agree"] for k in keys]
        for name in sorted(scored):
            if name == args.baseline:
                continue
            v_ok = [scored[name][k]["agree"] for k in keys]
            lost, gained, pv = mcnemar(b_ok, v_ok)
            print(f"  {name:<14} gains {gained:>3}, loses {lost:>3}  "
                  f"(net {gained - lost:+d})  p={pv:.4g}")

    print("\nper-class agreement:")
    for r in rows:
        if r:
            cls = "  ".join(f"{k}:{v['agree']}/{v['n']}" for k, v in r["by_class"].items())
            print(f"  {r['variant']:<14} {cls}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {"summary": rows, "per_clip": scored}, indent=2, default=str))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
