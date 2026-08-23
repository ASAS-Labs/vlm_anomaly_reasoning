#!/usr/bin/env python3
"""Family-N report: CV-concatenated SFT stage-1 inside M8 vs the in-session
zero-shot M8gt anchor on the same 235 clips.

    python sft_report.py --prefix sft_r1 --anchor sft_r1_anchor
"""

import argparse
import collections
import json
import re
from pathlib import Path

from prompt_lab_report import wilson
from semantic_agreement import mcnemar

REPO = Path(__file__).resolve().parents[2]


def load(p: Path):
    return {json.loads(ln)["video"]: json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()}


def scenario_of(rel):
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def conf(recs, keys):
    tp = sum(1 for k in keys if recs[k]["true_label"] == 1 and recs[k]["verdict"] == "Anomaly")
    fn = sum(1 for k in keys if recs[k]["true_label"] == 1 and recs[k]["verdict"] != "Anomaly")
    tn = sum(1 for k in keys if recs[k]["true_label"] == 0 and recs[k]["verdict"] == "Normal")
    fp = sum(1 for k in keys if recs[k]["true_label"] == 0 and recs[k]["verdict"] != "Normal")
    rec = tp / (tp + fn) if tp + fn else 0.0
    spec = tn / (tn + fp) if tn + fp else 0.0
    return dict(tp=tp, fn=fn, tn=tn, fp=fp, recall=rec, spec=spec, balacc=(rec + spec) / 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prefix", required=True, help="e.g. sft_r1 -> logs/sft_r1_f*/")
    ap.add_argument("--anchor", required=True, help="anchor dir name under logs/, e.g. sft_r1_anchor")
    ap.add_argument("--logs", type=Path, default=REPO / "logs")
    ap.add_argument("--folds", type=Path, default=REPO / "logs" / "sft" / "folds.json")
    ap.add_argument("--reference", default="hlab_r5t_M8", help="unpaired zero-shot reference dir (T-2.5 tree)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    folds = json.loads(args.folds.read_text())["folds"]
    anchor = load(args.logs / args.anchor / "results.jsonl")
    sft, per_fold = {}, {}
    for f in sorted(folds):
        d = args.logs / f"{args.prefix}_{f}"
        recs = load(d / "results.jsonl")
        held = set(folds[f]["held_out"])
        assert set(recs) == held, f"{f}: results {len(recs)} != held_out {len(held)} (missing {len(held - set(recs))}, extra {len(set(recs) - held)})"
        sft.update(recs)
        meta = {}
        if (d / "fold_meta.json").exists():
            meta = json.loads((d / "fold_meta.json").read_text())
        per_fold[f] = {"n": len(recs), "acc": sum(1 for r in recs.values() if r["correct"] is True) / len(recs),
                       "s1_len": sum(1 for r in recs.values() if r["expect_lenient"]),
                       "unknown": sum(1 for r in recs.values() if r["verdict"] == "Unknown"),
                       "anchor_acc": sum(1 for k in recs if anchor[k]["correct"] is True) / len(recs),
                       **{k: meta.get(k) for k in ("train_n", "steps", "final_loss", "sec_per_sample", "train_wall_min", "usd")}}
    keys = sorted(sft)
    assert set(keys) == set(anchor), f"SFT union {len(keys)} != anchor {len(anchor)}"
    n = len(keys)
    a_ok = [anchor[k]["correct"] is True for k in keys]
    s_ok = [sft[k]["correct"] is True for k in keys]
    lost, gained, p = mcnemar(a_ok, s_ok)
    ca, cs = conf(anchor, keys), conf(sft, keys)
    acc_a, acc_s = sum(a_ok) / n, sum(s_ok) / n
    lo_s, hi_s = wilson(sum(s_ok), n)
    lo_a, hi_a = wilson(sum(a_ok), n)
    s1a = sum(1 for k in keys if anchor[k]["expect_lenient"])
    s1s = sum(1 for k in keys if sft[k]["expect_lenient"])
    s1a_st = sum(1 for k in keys if anchor[k]["expect_strict"])
    s1s_st = sum(1 for k in keys if sft[k]["expect_strict"])
    dist_a = dict(collections.Counter(anchor[k]["expect"] for k in keys))
    dist_s = dict(collections.Counter(sft[k]["expect"] for k in keys))
    unk_s = sum(1 for k in keys if sft[k]["verdict"] == "Unknown")
    trunc_s = sum(1 for k in keys if sft[k].get("finish_reason") == "length")
    s1_trunc = sum(1 for k in keys if sft[k].get("expect_finish_reason") == "length")
    tr_lens = sorted(len(sft[k].get("reasoning_content") or "") for k in keys)
    med_trace = tr_lens[len(tr_lens) // 2] if tr_lens else 0
    anc_trace = sorted(len(anchor[k].get("reasoning_content") or "") for k in keys)[n // 2]
    verdict = "PASS" if (p < 0.05 and cs["balacc"] > ca["balacc"]) else "FAIL"

    out = [f"# Family N — SFT stage 1 inside M8 ({args.prefix}) vs zero-shot anchor ({args.anchor})\n",
           f"n = {n} clips (CV-concatenated: each clip scored by the fold model that never saw its scene); "
           f"anchor = in-session zero-shot M8gt, same early_gt tree, same stage 2.\n",
           "| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient | stage-1 answers | Unknown / s2-trunc / s1-trunc | median s1 trace chars |",
           "|---|---|---|---|---|---|---|---|---|",
           f"| **SFT (M8 + {sft[keys[0]].get('stage1_arm', 'expect_sft')})** | **{acc_s:.3f}** ({sum(s_ok)}/{n}) | [{lo_s:.3f}, {hi_s:.3f}] | **{cs['balacc']:.3f}** | {cs['recall']:.2f} / {cs['spec']:.2f} | {s1s_st} / {s1s} | {dist_s} | {unk_s} / {trunc_s} / {s1_trunc} | {med_trace} |",
           f"| anchor (M8gt zero-shot) | {acc_a:.3f} ({sum(a_ok)}/{n}) | [{lo_a:.3f}, {hi_a:.3f}] | {ca['balacc']:.3f} | {ca['recall']:.2f} / {ca['spec']:.2f} | {s1a_st} / {s1a} | {dist_a} | — | {anc_trace} |",
           "",
           f"Paired McNemar SFT vs anchor: +{gained} gained / −{lost} lost (net {gained - lost:+d}), p = {p:.4f}.",
           f"**Pre-registered verdict: {verdict}** (PASS iff p < 0.05 AND balacc_SFT > balacc_anchor; declare only when a second training seed also passes).\n"]
    ref = args.logs / args.reference / "results.jsonl"
    if ref.exists():
        rr = load(ref)
        rk = [k for k in keys if k in rr]
        out.append(f"Unpaired reference {args.reference} (T−2.5 tree, different window on 25 clips): "
                   f"{sum(1 for k in rk if rr[k]['correct'] is True)}/{len(rk)} = "
                   f"{sum(1 for k in rk if rr[k]['correct'] is True) / max(1, len(rk)):.3f}.\n")
    out.append("## Per scenario\n")
    out.append("| scenario | n | anchor acc | SFT acc | net | anchor s1-lenient | SFT s1-lenient | SFT answers |")
    out.append("|---|---|---|---|---|---|---|---|")
    by = collections.defaultdict(list)
    for k in keys:
        by[scenario_of(k)].append(k)
    for s in sorted(by, key=lambda x: (x[:3] != "neg", x)):
        ks = by[s]
        aa = sum(1 for k in ks if anchor[k]["correct"] is True)
        ss = sum(1 for k in ks if sft[k]["correct"] is True)
        out.append(f"| {s} | {len(ks)} | {aa}/{len(ks)} | {ss}/{len(ks)} | {ss - aa:+d} | "
                   f"{sum(1 for k in ks if anchor[k]['expect_lenient'])} | {sum(1 for k in ks if sft[k]['expect_lenient'])} | "
                   f"{dict(collections.Counter(sft[k]['expect'] for k in ks))} |")
    out.append("\n## Per fold\n")
    out.append("| fold | held-out n | anchor acc | SFT acc | SFT s1-lenient | Unknown | train n | steps | final loss | s/sample | train min | $ |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for f, m in per_fold.items():
        out.append(f"| {f} | {m['n']} | {m['anchor_acc']:.3f} | {m['acc']:.3f} | {m['s1_len']}/{m['n']} | {m['unknown']} | "
                   f"{m['train_n']} | {m['steps']} | {m['final_loss']} | {m['sec_per_sample']} | {m['train_wall_min']} | {m['usd']} |")
    flips_gain = [k for k in keys if s_ok[keys.index(k)] and not a_ok[keys.index(k)]]
    flips_lost = [k for k in keys if a_ok[keys.index(k)] and not s_ok[keys.index(k)]]
    out.append("\n## Flips vs anchor\n")
    out.append(f"gained ({len(flips_gain)}): " + ", ".join(k.split('/')[-1] for k in flips_gain))
    out.append(f"\nlost ({len(flips_lost)}): " + ", ".join(k.split('/')[-1] for k in flips_lost) + "\n")
    dst = args.out or (REPO / "logs" / "sft" / f"report_{args.prefix}.md")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out))
    print("\n".join(out[:9]))
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
