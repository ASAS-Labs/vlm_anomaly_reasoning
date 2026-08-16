#!/usr/bin/env python3
"""Measure perception directly: factual probe questions with no anomaly framing.

The verdict experiments show near-chance discrimination; this separates
"cannot see" from "cannot judge". Each clip gets two probes with objective
ground truth:

  action  end-state of the ego vehicle (Stopped / Moving / Started), GT from the
          frozen expectation class — valid because the subset is prompt-video-ID
          agreed, so the class is what the video actually depicts;
  scene   the scenario's discriminating percept (is the stop sign real or on a
          shirt/billboard? what is on the road? signal colour?), GT authored from
          the scenario definitions.

No mention of anomalies, safety, or intervention anywhere in the prompts, so the
probe measures perception unconfounded by the judgment task.

    python perception_probe.py --dataset .../id_variants/v1_resample \\
        --subset .../vlm_agreement_subset_admitted.txt --server_url ... \\
        --out_dir logs/probe_4fps
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

from utils import discover_eval_videos

SYSTEM_PROMPT = "You are a helpful assistant."

ACTION_PROBE = {
    "question": ("Watch the ego vehicle's motion in this driving clip. By the END of "
                 "the clip, which best describes the ego vehicle? Answer with exactly "
                 "one word:\n"
                 "Stopped — it has come to a stop and is stationary at the end\n"
                 "Moving — it is still moving forward at the end\n"
                 "Started — it was stationary and has just started moving"),
    "options": ["stopped", "moving", "started"],
}
ACTION_GT = {"stop": "stopped", "maintain": "moving", "accelerate": "started",
             "start_from_stop": "started", "decelerate": "moving"}

BALLOON_Q = {
    "question": ("Look at the road surface ahead of the ego vehicle in this clip. "
                 "What is lying on the road? Answer with exactly one word: "
                 "Balloons, Bags, Rocks, or Nothing."),
    "options": ["balloons", "bags", "rocks", "nothing"],
}
SIGNAL_Q = {
    "question": ("What colour is the traffic signal facing the ego vehicle in this "
                 "clip? Answer with exactly one word: Red, Green, or Amber."),
    "options": ["red", "green", "amber"],
}
PEDESTRIAN_Q = {
    "question": ("Does a pedestrian step off the sidewalk into the road in the ego "
                 "vehicle's path during this clip? Answer with exactly one word: "
                 "Yes or No."),
    "options": ["yes", "no"],
}
WALL_Q = {
    "question": ("Look at where this street leads. Does the road ahead continue as "
                 "a real, drivable open road, or does the street end at a solid wall "
                 "painted to look like a road? Answer with exactly one word: "
                 "Continues or Wall."),
    "options": ["continues", "wall"],
}

# scenario -> (probe dict, ground-truth option). GT authored from the human prompt
# lines in video_gen_prompts/final_semantic_scenarios/*/prompt.txt.
SCENE_PROBES = {
    "neg_prompt_2": ({
        "question": ("A stop sign is visible somewhere in this scene. Is it a real "
                     "roadside traffic sign, or is it printed on a pedestrian's "
                     "shirt? Answer with exactly one word: Real or Shirt."),
        "options": ["real", "shirt"]}, "shirt"),
    "neg_prompt_3": (SIGNAL_Q, "red"),
    "neg_prompt_4": (BALLOON_Q, "balloons"),
    "neg_prompt_5": (BALLOON_Q, "bags"),
    "neg_prompt_8": (PEDESTRIAN_Q, "yes"),
    "neg_prompt_9": (WALL_Q, "wall"),
    "pos_prompt_0": ({
        "question": ("A stop sign is visible somewhere in this scene. Is it a real "
                     "roadside traffic sign, or is it part of a billboard "
                     "advertisement? Answer with exactly one word: Real or "
                     "Billboard."),
        "options": ["real", "billboard"]}, "billboard"),
    "pos_prompt_4": (BALLOON_Q, "balloons"),
    "pos_prompt_5": (BALLOON_Q, "bags"),
    "pos_prompt_6": ({
        "question": ("Is there an oncoming vehicle with bright headlights facing the "
                     "ego vehicle at any point in this clip? Answer with exactly one "
                     "word: Yes or No."),
        "options": ["yes", "no"]}, "yes"),
    "pos_prompt_8": (PEDESTRIAN_Q, "yes"),
    "pos_prompt_11": (SIGNAL_Q, "red"),
}


def scenario_of(rel: str) -> str:
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def parse_answer(raw: str, options: list[str]) -> str:
    """Last-mentioned option wins (same convention as the verdict parser)."""
    if not raw:
        return "unknown"
    text = raw.lower()
    best, pos = "unknown", -1
    for opt in options:
        i = text.rfind(opt)
        if i > pos:
            best, pos = opt, i
    return best


def ask(client, model_id, video_path: Path, question: str, seed: int):
    r = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "video_url",
                 "video_url": {"url": video_path.resolve().as_uri()}},
                {"type": "text", "text": question},
            ]},
        ],
        max_tokens=30, temperature=0.0, seed=seed,
    )
    return r.choices[0].message.content


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True)
    p.add_argument("--subset", type=Path, required=True)
    p.add_argument("--server_url", default=None)
    p.add_argument("--out_dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry_run", action="store_true")
    args = p.parse_args()

    items = discover_eval_videos(args.dataset, strict=False)
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    by_rel = {i["rel_path"]: i for i in items}
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"--subset: {len(missing)} clip(s) missing, e.g. {missing[:3]}")
    items = [by_rel[w] for w in wanted]
    if args.limit:
        items = items[: args.limit]

    expectations = json.loads(
        (Path(__file__).parent / "id_expectations.json").read_text())

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = open(args.out_dir / "results.jsonl", "a", encoding="utf-8")
    done = set()
    if (args.out_dir / "results.jsonl").exists():
        for ln in (args.out_dir / "results.jsonl").read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                done.add((r["video"], r["probe"]))

    client = model_id = None
    if not args.dry_run:
        client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
        model_id = client.models.list().data[0].id

    n_req = 0
    for it in items:
        rel = it["rel_path"]
        scen = scenario_of(rel)
        cls = expectations[rel]["class"]
        probes = [("action", ACTION_PROBE, ACTION_GT[cls])]
        if scen in SCENE_PROBES:
            spec, gt = SCENE_PROBES[scen]
            probes.append(("scene", spec, gt))
        for pid, spec, gt in probes:
            if (rel, pid) in done:
                continue
            rec = {"video": rel, "scenario": scen, "probe": pid, "class": cls,
                   "question": spec["question"], "options": spec["options"],
                   "gt": gt, "ts": datetime.now().isoformat(timespec="seconds")}
            if args.dry_run:
                rec.update(raw=None, answer="DryRun", correct=None)
            else:
                t0 = time.time()
                raw = ask(client, model_id, it["abs_path"], spec["question"], args.seed)
                ans = parse_answer(raw, spec["options"])
                rec.update(raw=raw, answer=ans, correct=ans == gt,
                           latency_s=round(time.time() - t0, 3))
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            n_req += 1
            if not args.dry_run:
                print(f"[{n_req}] {rel.split('/')[-1]} {pid}: {rec['answer']} "
                      f"(gt={gt}) {'OK' if rec['correct'] else 'X'}", flush=True)
    out.close()

    # summary over everything on disk
    recs = [json.loads(ln) for ln in
            (args.out_dir / "results.jsonl").read_text().splitlines() if ln.strip()]
    real = [r for r in recs if r.get("correct") is not None]
    if real:
        summary = {}
        for pid in ("action", "scene"):
            sub = [r for r in real if r["probe"] == pid]
            by_scen = {}
            for r in sub:
                a = by_scen.setdefault(r["scenario"], [0, 0])
                a[1] += 1
                a[0] += int(r["correct"])
            summary[pid] = {
                "n": len(sub), "correct": sum(r["correct"] for r in sub),
                "accuracy": sum(r["correct"] for r in sub) / len(sub) if sub else None,
                "by_scenario": {k: {"correct": v[0], "n": v[1]}
                                for k, v in sorted(by_scen.items())}}
        (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=1))
        for pid, s in summary.items():
            print(f"{pid}: {s['correct']}/{s['n']} = {s['accuracy']:.1%}")
    print(f"done: {n_req} new request(s); results in {args.out_dir}")


if __name__ == "__main__":
    main()
