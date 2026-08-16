#!/usr/bin/env python3
"""Two-stage expected-vs-actual monitor, with no oracle inputs.

Stage 1 (expectation): from the scene alone, what SHOULD a correct driver do?
Runs on the EARLY window (first 2.5 s) so the expectation cannot be anchored on
the clip's outcome — the dataset places the label-defining action in the final
>=2 s, so the early window is common to both polarities of a scenario pair.
An `expect_full` arm on the whole clip measures that anchoring contamination.

Stage 2 (monitor): a second turn supplies the ACTUAL recorded trajectory (text
only) and asks whether it matches the stage-1 expectation. Everything used is
available at deployment time: camera video and the CAN/ID action trace.

Ground truth for stage 1 lives in expected_action_gt.json, authored from the
scenario definitions (framework field 4) and validated against each scene's
positive-polarity twin class; it never enters any prompt.

    python expectation_experiment.py --stage expect_early --dataset <early tree> ...
    python expectation_experiment.py --stage monitor --dataset <early tree> \\
        --full-dataset <v1 tree with .txt> ...
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import openai

from utils import discover_eval_videos, parse_verdict, read_action_sequence

SYSTEM_PROMPT = "You are a helpful assistant."

EXPECT_OPTIONS = ["continue", "slow", "stop", "wait"]
EXPECT_QUESTION = (
    "You are evaluating the driving scene in this clip from the ego vehicle's "
    "point of view. Based only on what the scene requires, what SHOULD a correct, "
    "safe driver do over the next few seconds? Answer with exactly one word:\n"
    "Continue — maintain current speed and lane\n"
    "Slow — reduce speed but keep moving\n"
    "Stop — brake to a complete stop\n"
    "Wait — the vehicle is already stationary and should remain stopped"
)

MONITOR_FOLLOWUP = (
    "Here is the ego vehicle's ACTUAL recorded action over the full clip, as "
    "[[velocity_in_mph, heading_in_degrees], ...] sampled at 5 Hz:\n{seq}\n\n"
    "First state in one short sentence what the vehicle actually did. Then state "
    "whether the actual behaviour matches what a correct driver should do in this "
    "scene. Reply on the final line with exactly one of:\n"
    "Classification: Anomaly — the actual behaviour does not match the correct "
    "response and would require intervention\n"
    "Classification: Normal — the actual behaviour matches the correct response"
)


def scenario_of(rel: str) -> str:
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def parse_option(raw: str) -> str:
    if not raw:
        return "unknown"
    text = raw.lower()
    best, pos = "unknown", -1
    for opt in EXPECT_OPTIONS:
        i = text.rfind(opt)
        if i > pos:
            best, pos = opt, i
    return best


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=["expect_early", "expect_full", "monitor"],
                   required=True)
    p.add_argument("--dataset", required=True,
                   help="tree whose mp4s are shown to the model (early or full)")
    p.add_argument("--full-dataset", default=None,
                   help="monitor stage: tree holding the full-clip .txt trajectories")
    p.add_argument("--subset", type=Path, required=True)
    p.add_argument("--server_url", required=True)
    p.add_argument("--out_dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    gt = json.loads((Path(__file__).parent / "expected_action_gt.json").read_text())
    gt.pop("_doc", None)

    items = discover_eval_videos(args.dataset, strict=False)
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    by_rel = {i["rel_path"]: i for i in items}
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"--subset: {len(missing)} clip(s) missing, e.g. {missing[:3]}")
    items = [by_rel[w] for w in wanted]
    if args.limit:
        items = items[: args.limit]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "results.jsonl"
    done = set()
    if out_path.exists():
        for ln in out_path.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)["video"])
    out = open(out_path, "a", encoding="utf-8")

    client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
    model_id = client.models.list().data[0].id

    n = 0
    for it in items:
        rel = it["rel_path"]
        if rel in done:
            continue
        scen = scenario_of(rel)
        g = gt[scen]
        uri = it["abs_path"].resolve().as_uri()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "video_url", "video_url": {"url": uri}},
                {"type": "text", "text": EXPECT_QUESTION},
            ]},
        ]
        t0 = time.time()
        r1 = client.chat.completions.create(model=model_id, messages=messages,
                                            max_tokens=30, temperature=0.0,
                                            seed=args.seed)
        a1_raw = r1.choices[0].message.content
        expect = parse_option(a1_raw)
        rec = {"video": rel, "scenario": scen, "stage": args.stage,
               "true_label": it["true_label"],
               "gt_expected": g["expected"], "gt_acceptable": g["acceptable"],
               "expect_raw": a1_raw, "expect": expect,
               "expect_strict": expect == g["expected"],
               "expect_lenient": expect in g["acceptable"],
               "ts": datetime.now().isoformat(timespec="seconds")}

        if args.stage == "monitor":
            full_tree = Path(args.full_dataset)
            seq_text = read_action_sequence(full_tree / rel)
            messages += [
                {"role": "assistant", "content": a1_raw},
                {"role": "user", "content": MONITOR_FOLLOWUP.format(seq=seq_text)},
            ]
            r2 = client.chat.completions.create(model=model_id, messages=messages,
                                                max_tokens=200, temperature=0.0,
                                                seed=args.seed)
            raw2 = r2.choices[0].message.content
            parsed = parse_verdict(raw2, r2.choices[0].finish_reason)
            pred = {"Anomaly": 1, "Normal": 0}.get(parsed["verdict"])
            rec.update(monitor_raw=raw2, verdict=parsed["verdict"],
                       parse_reason=parsed["reason"],
                       correct=None if pred is None else pred == it["true_label"],
                       action_sequence=seq_text)

        rec["latency_s"] = round(time.time() - t0, 3)
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        out.flush()
        os.fsync(out.fileno())
        n += 1
        tail = rec.get("verdict", rec["expect"])
        print(f"[{n}] {rel.split('/')[-1]}: expect={expect} "
              f"(gt={g['expected']}) -> {tail}", flush=True)
    out.close()

    recs = [json.loads(ln) for ln in out_path.read_text().splitlines() if ln.strip()]
    strict = sum(r["expect_strict"] for r in recs)
    lenient = sum(r["expect_lenient"] for r in recs)
    print(f"stage1 strict {strict}/{len(recs)}  lenient {lenient}/{len(recs)}")
    if args.stage == "monitor":
        ok = [r for r in recs if r.get("correct") is not None]
        print(f"monitor verdict accuracy "
              f"{sum(r['correct'] for r in ok)}/{len(ok)}")


if __name__ == "__main__":
    main()
