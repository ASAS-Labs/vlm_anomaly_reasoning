#!/usr/bin/env python3
"""Self-distil stage-1 rationale targets for SFT (family N).

For every clip of the agreement subset, ask the BASE model the exact served
stage-1 question over the clip's decision-time window (generated_vids_720p_early_gt)
with the GT expected action given as a HINT, and keep the answer content (named
real feature + one-line why + final word) as the training target. Thinking stays
on (the trace is stored for audit, never trained on). Acceptance filters reject
hint echoes, outcome/ego-motion narration, wrong/missing final word and odd
lengths; rejects fall back to a feature-hinted second tier, then to M8's own
correct answer (unchanged-window clips), then to a per-scenario template.

    python sft_rationalize.py --server_url http://127.0.0.1:8000/v1 \
        --dataset /abs/generated_vids_720p_early_gt --out ../../logs/sft/rationales.jsonl
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import openai

import pilot_models
from expectation_experiment import SYSTEM_PROMPT, parse_option, scenario_of
from h_variants import M4_STAGE1
from utils import discover_eval_videos

REPO = Path(__file__).resolve().parents[2]
GT_PATH = Path(__file__).resolve().parent / "expected_action_gt.json"
OPTION_WORD = {"continue": "Continue", "slow": "Slow", "stop": "Stop", "wait": "Wait"}

HINT_T1 = (
    "For calibration: the correct final answer for this clip is {X}. Do not mention that "
    "you were told this. Answer exactly as you would when solving it yourself, in two to "
    "four sentences: name the specific real feature visible in these frames that requires "
    "{X} (or state that nothing requires a change), say in one line why, and end with the "
    "single word {X} on the final line. Describe only what is visible in this clip; do not "
    "refer to anything that may happen later."
)
HINT_T2 = HINT_T1 + " The relevant feature is: {F}."

# Scene features for the tier-2 hint (GT `scene` text, cleaned). These reach the
# model only during rationalization, never a training or evaluation prompt.
FEATURE_HINT = {
    "neg_prompt_0": "a stop sign that is only part of an advertising billboard above the highway, not a roadside sign",
    "pos_prompt_0": "a stop sign that is only part of an advertising billboard above the highway, not a roadside sign",
    "neg_prompt_2": "a pedestrian standing still on the curb wearing a shirt printed with a stop sign; nothing in the roadway",
    "pos_prompt_2": "a pedestrian standing still on the curb wearing a shirt printed with a stop sign; nothing in the roadway",
    "neg_prompt_3": "a red traffic light at which the ego vehicle is already stationary, with pedestrians crossing",
    "neg_prompt_4": "two small deflated party balloons resting on the road surface — harmless soft debris",
    "pos_prompt_4": "two small deflated party balloons resting on the road surface — harmless soft debris",
    "neg_prompt_5": "light polythene bags blowing near the road surface — harmless soft debris",
    "pos_prompt_5": "light polythene bags blowing near the road surface — harmless soft debris",
    "pos_prompt_6": "oncoming headlight glare at night impairing visibility ahead",
    "neg_prompt_8": "a small child stepping off the sidewalk into the vehicle's path",
    "pos_prompt_8": "a small child at the curb edge about to enter the vehicle's path",
    "neg_prompt_9": "the street ends at a solid wall painted with a photorealistic mural of an open road",
    "pos_prompt_9": "the street ends at a solid wall painted with a photorealistic mural of an open road",
    "pos_prompt_11": "a real traffic signal ahead showing red",
}

# Last-resort targets (M8 voice), used only when every sample is rejected.
TEMPLATE = {
    "neg_prompt_0": "The only apparent traffic control is a stop sign printed on an advertising billboard above the highway; it is an image, not a roadside sign, and commands nothing. The road ahead is clear, so nothing requires a change.\n\nContinue",
    "neg_prompt_2": "The stop sign is printed on a pedestrian's shirt; the person is standing still on the curb and not entering the roadway, so there is no real traffic control or hazard in the lane. Nothing requires a change.\n\nContinue",
    "neg_prompt_3": "The real feature is the traffic light directly ahead showing red while the ego vehicle is already stationary at the line; a red signal requires the vehicle to remain stopped until it changes.\n\nWait",
    "neg_prompt_4": "The only objects in the lane are two small deflated balloons resting on the road surface — harmless soft debris that can be driven over. Nothing requires a change in speed.\n\nContinue",
    "neg_prompt_5": "The only objects near the lane are light polythene bags blowing across the road surface — harmless soft debris that poses no hazard. Nothing requires a change in speed.\n\nContinue",
    "neg_prompt_8": "The real feature is a small child stepping off the sidewalk into the vehicle's path directly ahead; a person entering the lane requires the driver to brake to a complete stop.\n\nStop",
    "neg_prompt_9": "The real feature is a solid wall closing off the street directly ahead; the open road shown on it is only a painted mural, so the travel path is physically blocked and the driver must brake to a stop before it.\n\nStop",
    "pos_prompt_6": "Oncoming headlight glare at night is impairing visibility of the road ahead; while the other vehicle passes, the prudent action is to reduce speed.\n\nSlow",
    "pos_prompt_11": "The real feature is the traffic signal at the intersection ahead showing red; approaching a red light requires the driver to brake to a complete stop at the line.\n\nStop",
}
TEMPLATE.update({"pos_prompt_0": TEMPLATE["neg_prompt_0"], "pos_prompt_2": TEMPLATE["neg_prompt_2"],
                 "pos_prompt_4": TEMPLATE["neg_prompt_4"], "pos_prompt_5": TEMPLATE["neg_prompt_5"],
                 "pos_prompt_8": "The real feature is a small child at the curb edge, about to step into the vehicle's path directly ahead; a person entering the lane requires the driver to brake to a complete stop.\n\nStop",
                 "pos_prompt_9": TEMPLATE["neg_prompt_9"]})

FINAL_LINE_RE = re.compile(r"^\W*(continue|slow|stop|wait)\W*$", re.I)
HINT_ECHO_RE = re.compile(r"\b(told|(was|were) given|given (that )?(the )?(answer|hint)|hint|calibration|"
                          r"known to be|correct (final )?answer|as (instructed|stated)|provided answer)\b", re.I)
# Outcome / ego-motion narration must not leak into a stage-1 target: the target
# describes what the scene requires, not what the vehicle went on to do.
OUTCOME_RE = re.compile(r"\b(later|eventually|at the end of the (clip|video|sequence|footage)|"
                        r"by the end|ends up|goes on to|comes to a (stop|halt|complete stop)|anomal)", re.I)
# Ego-motion narration ("the vehicle is already braking") is outcome leakage for
# every class except Wait, whose defining feature IS that the vehicle is stationary.
EGO_MOTION_RE = re.compile(r"\b(vehicle|car|ego)\S* (is|was|has) (already )?(slow|brak|stopp|decelerat|halt)", re.I)


def check(content: str, gt_expected: str):
    """-> list of reject reasons (empty = accepted)."""
    reasons = []
    c = (content or "").strip()
    if not c:
        return ["empty"]
    if "<think>" in c:
        reasons.append("think_tag")
    lines = [ln.strip() for ln in c.splitlines() if ln.strip()]
    if not FINAL_LINE_RE.match(lines[-1]):
        reasons.append("final_line_not_bare_option")
    if parse_option(c) != gt_expected:
        reasons.append(f"parsed={parse_option(c)}")
    n = len(c.split())
    if n < 12 or n > 120:
        reasons.append(f"words={n}")
    m = HINT_ECHO_RE.search(c)
    if m:
        reasons.append(f"hint_echo:{m.group(0)}")
    m = OUTCOME_RE.search(c)
    if m:
        reasons.append(f"outcome:{m.group(0)}")
    if gt_expected != "wait":
        m = EGO_MOTION_RE.search(c)
        if m:
            reasons.append(f"outcome:{m.group(0)}")
    return reasons


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server_url", required=True)
    ap.add_argument("--dataset", required=True, help="early_gt tree (video-only)")
    ap.add_argument("--subset", type=Path, default=REPO / "logs" / "vlm_agreement_subset_admitted.txt")
    ap.add_argument("--out", type=Path, default=REPO / "logs" / "sft" / "rationales.jsonl")
    ap.add_argument("--m8-results", type=Path, default=REPO / "logs" / "hlab_r5t_M8" / "results.jsonl")
    ap.add_argument("--model-config", default="qwen38", choices=list(pilot_models.MODELS))
    ap.add_argument("--model-arm", default="rationalize")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--tries", type=int, default=3, help="samples per tier")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    gt_all = json.loads(GT_PATH.read_text())
    gt = {k: v for k, v in gt_all.items() if not k.startswith("_")}
    annotated = set(gt_all.get("_early_window_end_s", {}))
    # window changed vs the M8 run of record (T-2.5 tree): annotated clips and the
    # long clips whose rolling window no longer starts at 0
    manifest = Path(args.dataset) / "pilot_tree_manifest.json"
    changed = set(annotated)
    if manifest.exists():
        for c in json.load(open(manifest))["clips"]:
            if c.get("early_start_s", 0) > 0.1:
                changed.add(c["rel_path"])
    m8 = {}
    if args.m8_results.exists():
        for ln in args.m8_results.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                m8[r["video"]] = r

    items = discover_eval_videos(Path(args.dataset), strict=False)
    by_rel = {i["rel_path"]: i for i in items}
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"{len(missing)} subset clip(s) missing from {args.dataset}: {missing[:3]}")
    if args.limit:
        wanted = wanted[:args.limit]
    for w in wanted:
        if scenario_of(w) not in gt:
            sys.exit(f"no GT for {scenario_of(w)}")
    req_kwargs, extra_body = pilot_models.request_kwargs(args.model_config, args.model_arm)
    hint_sha = sha(HINT_T1 + "|" + HINT_T2)

    if args.dry_run:
        rel = wanted[0]
        x = OPTION_WORD[gt[scenario_of(rel)]["expected"]]
        print(json.dumps({"request_kwargs": req_kwargs, "extra_body": extra_body,
                          "n_clips": len(wanted), "changed_window_clips": len(changed & set(wanted)),
                          "m8_records": len(m8), "hint_sha256": hint_sha}, indent=1))
        print("--- tier-1 user text (first clip) ---")
        print(M4_STAGE1 + "\n\n" + HINT_T1.format(X=x))
        print("--- tier-2 suffix ---")
        print(HINT_T2.format(X=x, F=FEATURE_HINT[scenario_of(rel)])[len(HINT_T1.format(X=x)):])
        for t in TEMPLATE.values():
            assert not check(t, parse_option(t)), (t, check(t, parse_option(t)))
        print("templates pass the acceptance filter")
        return

    client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
    model_id = client.models.list().data[0].id
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pilot_models.write_run_meta(
        args.out.parent, args.model_config, args.model_arm, args.server_url, model_id,
        {"stage": "rationalize", "dataset": args.dataset, "subset": str(args.subset),
         "seed": args.seed, "tries": args.tries, "concurrency": args.concurrency,
         "n_clips": len(wanted), "stage1_prompt_sha256": sha(M4_STAGE1),
         "hint_sha256": hint_sha, "out": str(args.out)})
    meta_path = args.out.parent / "run_meta.json"
    meta_path.rename(args.out.parent / "rationales_run_meta.json")

    done = set()
    if args.out.exists():
        for ln in args.out.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)["video"])
    pending = [w for w in wanted if w not in done]
    print(f"{len(wanted)} clips; {len(done)} done, {len(pending)} pending; model {model_id}")

    def ask(rel, hint_text, seed):
        uri = by_rel[rel]["abs_path"].resolve().as_uri()
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "video_url", "video_url": {"url": uri}},
                        {"type": "text", "text": M4_STAGE1 + "\n\n" + hint_text}]}]
        r = client.chat.completions.create(model=model_id, messages=messages, seed=seed,
                                           extra_body=extra_body, **req_kwargs)
        ch = r.choices[0]
        content, reasoning = pilot_models.answer_text(ch)
        return content, reasoning, ch.finish_reason

    def process(rel):
        scen = scenario_of(rel)
        x_word = OPTION_WORD[gt[scen]["expected"]]
        gt_exp = gt[scen]["expected"]
        t0 = time.time()
        samples, target, source, tries = [], None, None, 0
        for tier, hint in (("t1", HINT_T1.format(X=x_word)),
                           ("t2", HINT_T2.format(X=x_word, F=FEATURE_HINT[scen]))):
            for i in range(args.tries):
                tries += 1
                content, reasoning, fin = ask(rel, hint, args.seed + i)
                reasons = check(content, gt_exp)
                samples.append({"tier": tier, "seed": args.seed + i, "content": content,
                                "reasoning": reasoning, "finish_reason": fin,
                                "accepted": not reasons, "reject_reasons": reasons})
                if not reasons:
                    target, source = content.strip(), tier
                    break
            if target:
                break
        if target is None:
            r = m8.get(rel)
            raw = (r or {}).get("expect_raw") or ""
            m8_reasons = [x for x in check(raw, gt_exp) if not x.startswith("words=")]
            if (r and r.get("expect_lenient") and rel not in changed
                    and len(raw.split()) <= 250 and not m8_reasons):
                target, source = raw.strip(), "m8_expect_raw"
            else:
                target, source = TEMPLATE[scen], "template"
        win = None
        if manifest.exists():
            win = next(({"start_s": c["early_start_s"], "end_s": c["early_end_s"]}
                        for c in json.load(open(manifest))["clips"] if c["rel_path"] == rel), None)
        return {"video": rel, "scenario": scen, "gt_expected": gt_exp,
                "gt_acceptable": gt[scen]["acceptable"], "window": win,
                "target": target, "source": source, "tries": tries,
                "samples": samples, "hint_sha256": hint_sha,
                "stage1_prompt_sha256": sha(M4_STAGE1), "model_id": model_id,
                "latency_s": round(time.time() - t0, 3),
                "ts": datetime.now().isoformat(timespec="seconds")}

    with open(args.out, "a") as fh, ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = {pool.submit(process, rel): rel for rel in pending}
        n = 0
        for fut in as_completed(futs):
            rel = futs[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - log and continue, resume later
                print(f"  FAILED {rel}: {exc}", flush=True)
                continue
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            n += 1
            print(f"  [{n}/{len(pending)}] {rel.split('/')[-1]}: {rec['source']} "
                  f"(tries {rec['tries']})", flush=True)

    # ---- review file ----
    recs = [json.loads(ln) for ln in args.out.read_text().splitlines() if ln.strip()]
    src = Counter(r["source"] for r in recs)
    by_sc = defaultdict(list)
    for r in recs:
        by_sc[r["scenario"]].append(r)
    out = [f"# Rationale targets — review ({len(recs)} clips)\n",
           f"sources: {dict(src)}\n",
           "## Two accepted samples per scenario\n"]
    import random
    rng = random.Random(0)
    for s in sorted(by_sc):
        ok = [r for r in by_sc[s] if r["source"] in ("t1", "t2")]
        for r in rng.sample(ok, min(2, len(ok))):
            out.append(f"### {r['video']}  ({r['source']}, gt {r['gt_expected']})\n\n```\n{r['target']}\n```\n")
    out.append("## Fallbacks (m8_expect_raw / template) — every one\n")
    for r in recs:
        if r["source"] in ("m8_expect_raw", "template"):
            rej = "; ".join(",".join(s["reject_reasons"]) for s in r["samples"])
            out.append(f"### {r['video']}  ({r['source']}, gt {r['gt_expected']}; rejects: {rej})\n\n```\n{r['target']}\n```\n")
    out.append("## Reject-reason histogram (all samples)\n")
    hist = Counter(reason.split(":")[0] for r in recs for s in r["samples"] for reason in s["reject_reasons"])
    out.append("\n".join(f"- {k}: {v}" for k, v in hist.most_common()) + "\n")
    review = args.out.parent / "rationales_review.md"
    review.write_text("\n".join(out))
    print(f"sources: {dict(src)}; review -> {review}")


if __name__ == "__main__":
    main()
