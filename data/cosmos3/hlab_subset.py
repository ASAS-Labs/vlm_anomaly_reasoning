#!/usr/bin/env python3
"""Draw the H-lab evaluation subset: 40 anomaly + 40 normal from the admitted
agreement subset, stratified across scenarios (largest-remainder allocation),
fixed seed. Also writes a 4-clip gate list covering the longest contexts.

    python hlab_subset.py [--n 40] [--seed 1234]
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from expectation_experiment import scenario_of

REPO = Path(__file__).resolve().parents[2]


def allocate(counts: dict, total: int) -> dict:
    """Largest-remainder (Hamilton) allocation of `total` over pools; ties broken
    alphabetically; no pool gets more than it holds."""
    pool = sum(counts.values())
    quotas = {k: total * v / pool for k, v in counts.items()}
    alloc = {k: min(int(q), counts[k]) for k, q in quotas.items()}
    left = total - sum(alloc.values())
    order = sorted(counts, key=lambda k: (-(quotas[k] - int(quotas[k])), k))
    for k in order:
        if left <= 0:
            break
        if alloc[k] < counts[k]:
            alloc[k] += 1
            left -= 1
    return alloc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--admitted", type=Path,
                   default=REPO / "logs" / "vlm_agreement_subset_admitted.txt")
    p.add_argument("--n", type=int, default=40, help="clips per class")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--out", type=Path, default=REPO / "logs" / "hlab_subset_80.txt")
    p.add_argument("--gate-out", type=Path, default=REPO / "logs" / "hlab_gate_4.txt")
    args = p.parse_args()

    admitted = [ln.strip() for ln in args.admitted.read_text().splitlines() if ln.strip()]
    by = defaultdict(list)
    for rel in admitted:
        by[scenario_of(rel)].append(rel)
    rng = random.Random(args.seed)
    chosen = set()
    for pol in ("neg", "pos"):
        pools = {s: sorted(v) for s, v in by.items() if s.startswith(pol)}
        alloc = allocate({s: len(v) for s, v in pools.items()}, args.n)
        for s in sorted(pools):
            chosen.update(rng.sample(pools[s], alloc[s]))
        print(pol, dict(sorted(alloc.items())))
    subset = [rel for rel in admitted if rel in chosen]   # admitted-list order
    args.out.write_text("\n".join(subset) + "\n")
    n_anom = sum(1 for r in subset if "negative" in r)
    print(f"{len(subset)} clips ({n_anom} anomaly / {len(subset) - n_anom} normal) -> {args.out}")

    gate = []
    for s in ("neg_prompt_0", "neg_prompt_3", "pos_prompt_8", "pos_prompt_0"):
        gate.append(next(r for r in subset if scenario_of(r) == s))
    args.gate_out.write_text("\n".join(gate) + "\n")
    print(f"gate: {[g.split('/')[-1] for g in gate]} -> {args.gate_out}")

    champ = REPO / "logs" / "qlab_r5t_L2" / "results.jsonl"
    if champ.exists():
        recs = {json.loads(ln)["video"]: json.loads(ln) for ln in champ.read_text().splitlines() if ln.strip()}
        ok = sum(1 for r in subset if recs.get(r, {}).get("correct") is True)
        print(f"offline champion (qlab_r5t_L2) on this subset: {ok}/{len(subset)} = {ok/len(subset):.3f}")


if __name__ == "__main__":
    main()
