#!/usr/bin/env python3
"""H-lab diagnostics per round: stage-1 answer distributions (strict/lenient vs
the diagnostic GT), twin divergence (anchoring), verdict accuracy conditional on
stage-1 correctness, per-stage truncation, and flips vs the anchor by scenario.

    python hlab_report.py --prefix hlab_r1t [--anchor L2]
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def scenario(rel):
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def load(p):
    return {json.loads(ln)["video"]: json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--logs", type=Path, default=REPO / "logs")
    ap.add_argument("--anchor", default="L2")
    a = ap.parse_args()
    runs = {}
    for d in sorted(a.logs.glob(f"{a.prefix}_*")):
        if (d / "results.jsonl").exists():
            runs[d.name[len(a.prefix) + 1:]] = load(d / "results.jsonl")
    anchor = runs.get(a.anchor)
    lines = [f"# H-lab diagnostics — {a.prefix}", ""]
    lines += ["| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | "
              "twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | "
              "s1 trunc | s2 trunc | Unknown verdicts |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for vid, recs in runs.items():
        if "expect" not in next(iter(recs.values())):
            continue  # the anchor (single-call) has no stage 1
        vids = sorted(recs)
        n = len(vids)
        dist = Counter(recs[v]["expect"] for v in vids)
        strict = sum(1 for v in vids if recs[v].get("expect_strict"))
        lenient = sum(1 for v in vids if recs[v].get("expect_lenient"))
        # twin divergence: |P(expect in {stop,slow} | neg_k) - P(. | pos_k)| averaged
        # over scenario pairs present on both sides
        by = defaultdict(lambda: {"neg": [], "pos": []})
        for v in vids:
            s = scenario(v)
            k = s.split("_", 1)[1]
            by[k][s[:3]].append(recs[v]["expect"] in ("stop", "slow"))
        divs = [abs(sum(d["neg"]) / len(d["neg"]) - sum(d["pos"]) / len(d["pos"]))
                for d in by.values() if d["neg"] and d["pos"]]
        div = sum(divs) / len(divs) if divs else float("nan")
        ok = [v for v in vids if recs[v].get("expect_lenient")]
        bad = [v for v in vids if not recs[v].get("expect_lenient")]
        acc = sum(1 for v in vids if recs[v].get("correct") is True) / n
        acc_ok = (sum(1 for v in ok if recs[v].get("correct") is True) / len(ok)) if ok else float("nan")
        acc_bad = (sum(1 for v in bad if recs[v].get("correct") is True) / len(bad)) if bad else float("nan")
        t1 = sum(1 for v in vids if recs[v].get("expect_finish_reason") == "length")
        t2 = sum(1 for v in vids if recs[v].get("finish_reason") == "length")
        unk = sum(1 for v in vids if recs[v].get("verdict") == "Unknown")
        lines.append(f"| {vid} | {n} | {dist.get('continue',0)}/{dist.get('slow',0)}/"
                     f"{dist.get('stop',0)}/{dist.get('wait',0)}/{dist.get('unknown',0)} | "
                     f"{strict}/{n} | {lenient}/{n} | {div:.2f} | {acc:.3f} | "
                     f"{acc_ok:.2f} | {len(ok)} | {acc_bad:.2f} | {len(bad)} | {t1} | {t2} | {unk} |")
    if anchor:
        lines += ["", f"## Flips vs {a.anchor} by scenario (fixed/broke)", ""]
        for vid, recs in runs.items():
            if vid == a.anchor:
                continue
            common = sorted(set(recs) & set(anchor))
            fb = defaultdict(lambda: [0, 0])
            for v in common:
                s = scenario(v)
                c, ca = recs[v].get("correct") is True, anchor[v].get("correct") is True
                if c and not ca:
                    fb[s][0] += 1
                elif ca and not c:
                    fb[s][1] += 1
            net = sum(x[0] - x[1] for x in fb.values())
            parts = ", ".join(f"{s} +{f}/-{b}" for s, (f, b) in sorted(fb.items()) if f or b)
            lines.append(f"- {vid}: net {net:+d} — {parts or 'no flips'}")
    text = "\n".join(lines) + "\n"
    out = a.logs / f"{a.prefix}_diag.md"
    out.write_text(text)
    print(text)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
