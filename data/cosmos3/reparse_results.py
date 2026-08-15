#!/usr/bin/env python3
"""Re-derive verdicts from stored raw model output, without re-running inference.

Every result record keeps `raw_output` verbatim, so a parser bug is fixable offline.
This re-runs the current parse_verdict over a results.jsonl, reports what changed,
recomputes metrics, and writes metrics_reparsed.json beside the input.

    python data/cosmos3/reparse_results.py logs/*/results.jsonl
    python data/cosmos3/reparse_results.py logs/smoke_*/results.jsonl --check

--check applies the pre-flight gates for a smoke run and exits non-zero on failure.
"""

import argparse
import collections
import json
from pathlib import Path

from utils import PARSER_VERSION, Metrics, parse_verdict

# Verdicts the model is expected to produce cleanly. Anything else means either the
# token budget is too small or the model is not answering in the requested format.
GOOD_REASONS = {"verdict_after_think", "bare_word"}


def load(path: Path) -> list[dict]:
    recs = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  warning: skipping malformed line in {path.name}")
    # Last record per video wins, matching the runner's resume semantics.
    by_video = {r["video"]: r for r in recs if "video" in r}
    return list(by_video.values())


def reparse(recs: list[dict]) -> tuple[Metrics, list[dict], collections.Counter]:
    metrics = Metrics()
    changes = []
    reasons = collections.Counter()
    for r in recs:
        old = r.get("verdict", "Error")
        if old == "Error":
            metrics.add("Error", r["true_label"], None, r.get("on_skip_list", False), None)
            reasons["<error>"] += 1
            continue
        new = parse_verdict(r.get("raw_output"), r.get("finish_reason"))
        reasons[new["reason"]] += 1
        metrics.add(new["verdict"], r["true_label"], r.get("latency_s"),
                    r.get("on_skip_list", False), new["reason"])
        if new["verdict"] != old:
            changes.append({"video": r["video"], "old": old, "new": new["verdict"],
                            "reason": new["reason"],
                            "finish_reason": r.get("finish_reason")})
    return metrics, changes, reasons


def check_gates(recs: list[dict], reasons: collections.Counter) -> list[str]:
    failures = []
    finishes = collections.Counter(r.get("finish_reason") for r in recs)
    n_length = finishes.get("length", 0)
    if n_length:
        failures.append(
            f"{n_length}/{len(recs)} outputs hit the token limit (finish_reason=length). "
            f"Raise --max_tokens and re-run; truncated outputs cannot be trusted."
        )
    bad = {k: v for k, v in reasons.items() if k not in GOOD_REASONS and k != "<error>"}
    if bad:
        failures.append(f"unexpected parse reasons: {bad}. Read the raw outputs before "
                        f"proceeding; do NOT loosen the parser to make this pass.")
    n_err = sum(1 for r in recs if r.get("verdict") == "Error")
    if n_err:
        failures.append(f"{n_err} error record(s) present")
    if any("upsampled_prompts" in r["video"] for r in recs):
        failures.append("records reference upsampled_prompts/, which must be excluded")
    return failures


def main():
    p = argparse.ArgumentParser(description="Re-parse stored model outputs")
    p.add_argument("paths", nargs="+", type=Path, help="results.jsonl file(s)")
    p.add_argument("--check", action="store_true", help="apply smoke-run gates")
    p.add_argument("--histogram", action="store_true", help="print reason/finish histograms")
    args = p.parse_args()

    any_failed = False
    for path in args.paths:
        recs = load(path)
        if not recs:
            print(f"{path}: no records")
            continue
        metrics, changes, reasons = reparse(recs)
        m = metrics.compute()

        print(f"\n{'=' * 64}\n{path}  ({len(recs)} records)")
        stamped = {r.get("parse", {}).get("parser_version")
                   for r in recs if isinstance(r.get("parse"), dict)}
        print(f"  parser: run used {stamped or {'n/a'}}, now v{PARSER_VERSION}")

        if changes:
            print(f"\n  {len(changes)} VERDICT CHANGE(S):")
            for c in collections.Counter(
                    (c["old"], c["new"]) for c in changes).most_common():
                print(f"    {c[0][0]:>7} -> {c[0][1]:<7}  {c[1]}")
            for c in changes[:10]:
                print(f"    {c['video'].split('/')[-1]}: {c['old']} -> {c['new']} "
                      f"({c['reason']}, finish={c['finish_reason']})")
            if len(changes) > 10:
                print(f"    ... and {len(changes) - 10} more")
        else:
            print("  no verdict changes (parser is deterministic vs the run)")

        if args.histogram:
            print("\n  parse reasons:")
            for k, v in reasons.most_common():
                print(f"    {k:<24} {v}")
            print("  finish reasons:")
            for k, v in collections.Counter(
                    r.get("finish_reason") for r in recs).most_common():
                print(f"    {str(k):<24} {v}")

        c = m["resolved"]
        print(f"\n  resolved n={c['n']} coverage={m['coverage']:.3f}  "
              f"acc={c['accuracy']:.4f} P={c['precision']:.4f} R={c['recall']:.4f} "
              f"F1={c['f1']:.4f}")
        print(f"  all n={m['strict_all']['n']} acc={m['strict_all']['accuracy']:.4f} "
              f"(bounds {m['accuracy_bounds'][0]:.4f}-{m['accuracy_bounds'][1]:.4f})")

        out = path.parent / "metrics_reparsed.json"
        out.write_text(json.dumps(
            {"parser_version": PARSER_VERSION, "n_changes": len(changes),
             "changes": changes, "metrics": m}, indent=2))
        print(f"  wrote {out}")

        if args.check:
            failures = check_gates(recs, reasons)
            if failures:
                any_failed = True
                print("\n  GATE FAILURES:")
                for f in failures:
                    print(f"    - {f}")
            else:
                print("\n  all gates passed")

    raise SystemExit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
