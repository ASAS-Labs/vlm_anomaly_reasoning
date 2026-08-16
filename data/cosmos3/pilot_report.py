#!/usr/bin/env python3
"""Collate the open-VLM pilot results into one table vs the Cosmos bars.

Reads logs/pilot_<key>_{expect_early,expect_full}/results.jsonl and
logs/pilot_<key>_verdict_P0/results.jsonl (plus run_meta.json when present).

    python pilot_report.py            # prints markdown
    python pilot_report.py --out ../../logs/pilot_report.md
"""

import argparse
import json
from pathlib import Path

from pilot_models import MODELS

# Reference rows (EXPERIMENT_ARMS.md families H/I; same subset & input standard).
COSMOS_BARS = [
    ("Cosmos3-Nano (bar)", "18/72", "38/72", "22/72", "40/72", "0.736", "—"),
    ("Cosmos3-Super", "8/72", "26/72", "12/72", "27/72", "—", "—"),
]


def read_jsonl(path: Path):
    if not path.exists():
        return None
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def expect_cell(recs):
    if not recs:
        return "—", "—", {}
    n = len(recs)
    strict = sum(1 for r in recs if r.get("expect_strict"))
    lenient = sum(1 for r in recs if r.get("expect_lenient"))
    stats = {"unknown": sum(1 for r in recs if r.get("expect") == "unknown"),
             "truncated": sum(1 for r in recs if r.get("finish_reason") == "length"),
             "mean_latency": sum(r.get("latency_s", 0) for r in recs) / n}
    return f"{strict}/{n}", f"{lenient}/{n}", stats


def verdict_cell(recs):
    if not recs:
        return "—", {}
    real = [r for r in recs if r.get("correct") is not None]
    stats = {"unknown": sum(1 for r in recs if r.get("verdict") == "Unknown"),
             "truncated": sum(1 for r in recs if r.get("finish_reason") == "length"),
             "mean_latency": sum(r.get("latency_s", 0) for r in recs) / max(1, len(recs))}
    if not real:
        return "—", stats
    acc = sum(r["correct"] for r in real) / len(real)
    anom = [r for r in real if r["true_label"] == 1]
    norm = [r for r in real if r["true_label"] == 0]
    if anom and norm:
        rec_ = sum(r["correct"] for r in anom) / len(anom)
        spec = sum(r["correct"] for r in norm) / len(norm)
        stats["recall_spec"] = f"{rec_:.2f}/{spec:.2f}"
    return f"{acc:.3f}", stats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--logs", type=Path,
                   default=Path(__file__).resolve().parents[2] / "logs")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    rows, notes = [], []
    for key, m in MODELS.items():
        ee = read_jsonl(args.logs / f"pilot_{key}_expect_early" / "results.jsonl")
        ef = read_jsonl(args.logs / f"pilot_{key}_expect_full" / "results.jsonl")
        vd = read_jsonl(args.logs / f"pilot_{key}_verdict_P0" / "results.jsonl")
        if not any((ee, ef, vd)):
            continue
        ee_s, ee_l, ee_x = expect_cell(ee)
        ef_s, ef_l, ef_x = expect_cell(ef)
        vd_a, vd_x = verdict_cell(vd)
        rows.append((m["hf_id"].split("/")[-1], ee_s, ee_l, ef_s, ef_l, vd_a,
                     vd_x.get("recall_spec", "—")))
        for arm, x in (("expect_early", ee_x), ("expect_full", ef_x),
                       ("verdict", vd_x)):
            if x and (x["unknown"] or x["truncated"]):
                notes.append(f"- {key} {arm}: {x['unknown']} unknown, "
                             f"{x['truncated']} truncated, "
                             f"mean latency {x['mean_latency']:.1f}s")

    lines = ["# Open-VLM pilot report", "",
             "72-clip agreement subset, 720p↑ @ 8 fps. Primary discriminator: "
             "expect_early strict (Cosmos-Nano bar 18/72).", "",
             "| model | early strict | early lenient | full strict | "
             "full lenient | verdict acc | rec/spec |",
             "|---|---|---|---|---|---|---|"]
    for r in COSMOS_BARS + rows:
        lines.append("| " + " | ".join(r) + " |")
    if notes:
        lines += ["", "## Parse/latency notes", ""] + notes
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
