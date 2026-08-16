#!/usr/bin/env python3
"""Build the prompt-video-ID agreement subset for the next VLM stage.

A clip is admitted only when every available witness is consistent with the
scenario it claims to depict:

  1. ID      the fixed (v1_resample) trajectory matches the frozen prompt
             expectation (id_semantics.check_match);
  2. video   the optical-flow probe does not contradict the prompt
             (contradiction excludes; ambiguous/unmeasurable does not, since the
             ID pipeline agrees with the probe at 98% where both can speak);
  3. human   the clip is not on the review skip lists — the union of the two
             variants filter CSVs and the Invalid rows of
             inverse_dynamics_filter.csv.

Clips without a fixed-ID trajectory yet are reported as `pending_id`, not
excluded — rerun after the remaining ID pass to finalize.

    python data/cosmos3/build_agreement_subset.py \
        --raw outputs/id_raw.jsonl --flow logs/id_flow_verdicts_all315.json
"""

import argparse
import csv
import json
from pathlib import Path

from fidelity_report import video_matches_prompt
from id_semantics import check_match, evaluate_sequence
from id_trajectory import derive_variant
from utils import discover_eval_videos

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VALIDATION = HERE / "data_validation"


def human_reject_sets() -> tuple[set[str], set[str], set[str]]:
    """(neg_names, pos_names, invalid_rel_paths) rejected by human review.

    The variants filter lists are bare filenames scoped to their own polarity —
    126 basenames collide across the neg/pos trees, so applying either list
    globally would over-reject the other polarity (the review GUI scopes them
    the same way). inverse_dynamics_filter.csv rows carry full relative paths.
    """
    def load(f):
        q = VALIDATION / f
        return ({ln.strip() for ln in q.read_text().splitlines() if ln.strip()}
                if q.is_file() else set())
    neg = load("negative_scenarios_variants_filter.csv")
    pos = load("positive_scenarios_variants_filter.csv")
    invalid: set[str] = set()
    idf = VALIDATION / "inverse_dynamics_filter.csv"
    if idf.is_file():
        with open(idf) as fh:
            for row in csv.DictReader(fh):
                if row.get("Valid/Invalid", "").strip() == "Invalid":
                    invalid.add(row[list(row)[0]].strip())
    return neg, pos, invalid


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path,
                   default=REPO / "data" / "datasets" / "generated_vids")
    p.add_argument("--raw", type=Path, default=REPO / "outputs" / "id_raw.jsonl")
    p.add_argument("--flow", type=Path,
                   default=REPO / "logs" / "id_flow_verdicts_all315.json")
    p.add_argument("--expectations", type=Path, default=HERE / "id_expectations.json")
    p.add_argument("--out", type=Path,
                   default=REPO / "logs" / "vlm_agreement_subset.json")
    args = p.parse_args()

    expectations = json.loads(args.expectations.read_text())
    flow = json.loads(args.flow.read_text()) if args.flow.exists() else {}
    raw = {}
    if args.raw.exists():
        for ln in args.raw.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                raw[r["rel_path"]] = r
    neg_rej, pos_rej, invalid_rel = human_reject_sets()

    rows, counts = [], {"admitted": 0, "pending_id": 0, "excluded": 0}
    for it in discover_eval_videos(args.src):
        rel = it["rel_path"]
        exp = expectations.get(rel)
        fv = flow.get(rel)
        reasons = []

        name = it["abs_path"].name
        polarity_rejects = neg_rej if "negative_scenario" in rel else pos_rej
        if name in polarity_rejects or rel in invalid_rel:
            reasons.append("human_rejected")
        if exp is None or exp["class"] is None:
            reasons.append("no_expectation")
        if fv is not None and exp and exp["class"] is not None:
            pv = video_matches_prompt(exp["class"], {**fv, "cls": exp["class"]})
            if pv is False:
                reasons.append("video_contradicts_prompt")

        id_status = "missing"
        if rel in raw and exp and exp["class"] is not None:
            r = raw[rel]
            seq5, _ = derive_variant(r["poses"], r["input_fps"],
                                     r["n_valid_steps"] + 1, "v1_resample")
            ok, why = check_match({"speed": exp["class"], "steer": exp["steer"]},
                                  evaluate_sequence(seq5))
            id_status = "agrees" if ok else "disagrees"
            if not ok:
                reasons.append(f"id_disagrees: {'; '.join(why)}")

        if reasons:
            status = "excluded"
        elif id_status == "missing":
            status = "pending_id"
        else:
            status = "admitted"
        counts[status] += 1
        rows.append({"rel_path": rel, "true_label": it["true_label"],
                     "class": exp["class"] if exp else None, "status": status,
                     "id_status": id_status,
                     "video_end": (fv or {}).get("end_state"),
                     "reasons": reasons})

    admitted = [r for r in rows if r["status"] == "admitted"]
    n_anom = sum(1 for r in admitted if r["true_label"] == 1)
    args.out.write_text(json.dumps({
        "criteria": "prompt-video-ID agreement + human review union",
        "counts": counts,
        "admitted_anomaly": n_anom,
        "admitted_normal": len(admitted) - n_anom,
        "clips": rows}, indent=1))

    print(f"total {len(rows)}: admitted {counts['admitted']} "
          f"({n_anom} anomaly / {len(admitted) - n_anom} normal), "
          f"pending_id {counts['pending_id']}, excluded {counts['excluded']}")
    from collections import Counter
    why = Counter(r["reasons"][0].split(":")[0] for r in rows if r["reasons"])
    print("exclusion reasons (first per clip):", dict(why))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
