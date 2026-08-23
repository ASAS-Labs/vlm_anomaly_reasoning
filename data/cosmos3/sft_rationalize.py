#!/usr/bin/env python3
"""Self-distil stage-1 SFT targets (family N) from the BASE model over each clip's
decision-time window (generated_vids_720p_early_gt).

--mode answer (N1/N2): rationale + final word. The exact served stage-1 question plus
  the GT expected action as a calibration HINT; content kept as the target; thinking
  stays on (trace stored for audit, never trained on). Tiers: t1 hint, t2 hint +
  scene feature; fallbacks M8's own correct answer (unchanged-window clips) -> template.

--mode think (N3): procedure distillation. The served question plus a fixed 4-step
  CHECKLIST the model must write out (PATH / CONTROLS / MOTION / ACTION) followed by a
  FINAL sentence and the word. Pass 1 is UN-hinted (the checklist must reach GT by
  itself); pass 2 (rejects only) states the required conclusion; fallback = a
  per-scenario checklist template. Target = "<think>\\n{steps}\\n</think>\\n\\n{final}"
  so SFT puts loss on the procedure, not just the conclusion.

Acceptance (both modes): final word == GT, final line bare option, length bounds, no
hint echo, no outcome/ego-motion narration (Wait excepted); think mode additionally
requires the four STEP labels in order, STEP 1 to talk about the path and STEP 3 to
state moving/stationary.

    python sft_rationalize.py --server_url http://127.0.0.1:8000/v1 \\
        --dataset /abs/generated_vids_720p_early_gt --out ../../logs/sft/rationales.jsonl
    python sft_rationalize.py --mode think ... --out ../../logs/sft_think/traces.jsonl
"""

import argparse
import hashlib
import json
import os
import random
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

# ---------------------------------------------------------------- answer mode
HINT_T1 = (
    "For calibration: the correct final answer for this clip is {X}. Do not mention that "
    "you were told this. Answer exactly as you would when solving it yourself, in two to "
    "four sentences: name the specific real feature visible in these frames that requires "
    "{X} (or state that nothing requires a change), say in one line why, and end with the "
    "single word {X} on the final line. Describe only what is visible in this clip; do not "
    "refer to anything that may happen later."
)
HINT_T2 = HINT_T1 + " The relevant feature is: {F}."

# ---------------------------------------------------------------- think mode
CHECKLIST = (
    "Before answering, write out these four steps explicitly, each on its own line "
    "starting with the step label.\n"
    "STEP 1 — PATH: what is physically in or across the drivable path within the next few "
    "seconds (objects, people, surfaces, barriers, walls, vehicles — regardless of what is "
    "printed or painted on them)?\n"
    "STEP 2 — CONTROLS: list each apparent traffic control or hazard and say whether it is "
    "a real device/hazard or only a depiction (printed, painted, worn, carried, displayed, "
    "reflected).\n"
    "STEP 3 — MOTION: is the ego vehicle currently moving or stationary, judging from the "
    "frames?\n"
    "STEP 4 — ACTION: given steps 1–3, what should a correct, safe driver do, and why (one "
    "line)?\n"
    "Then, on a new line, write FINAL: one sentence naming the feature that decides it, "
    "and end with the single word Continue, Slow, Stop, or Wait on the last line. Describe "
    "only what is visible in this clip; do not refer to anything that may happen later."
)
HINT_P2 = (
    " The correct final answer for this clip is {X}; do not mention that you were told "
    "this — the steps must reach it only from what the frames show."
)

# Scene features for the answer-mode tier-2 hint (GT `scene` text, cleaned). These
# reach the model only during distillation, never a training or evaluation prompt.
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

# Last-resort answer-mode targets (M8 voice), used only when every sample is rejected.
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


# Last-resort think-mode targets: the same 4-step procedure, hand-written per scene.
def _tt(p1, p2, p3, p4, final, word):
    return ("STEP 1 — PATH: " + p1 + "\nSTEP 2 — CONTROLS: " + p2 + "\nSTEP 3 — MOTION: " + p3
            + "\nSTEP 4 — ACTION: " + p4 + "\nFINAL: " + final + "\n" + word)


TEMPLATE_THINK = {
    "neg_prompt_0": _tt("The highway lane ahead is open; no vehicle, person or object is in or across the path; the billboard structure spans above the road, not across it.",
                        "A stop sign appears on the advertising billboard above the highway — printed on the billboard, a depiction, not a roadside sign; no other control or hazard.",
                        "The ego vehicle is moving at highway speed.",
                        "Nothing real requires a change: the path is clear and the only apparent control is a printed image, so maintain speed and lane.",
                        "The stop sign is part of an advertisement above the road and commands nothing; the lane ahead is clear.", "Continue"),
    "neg_prompt_2": _tt("The lane ahead is clear; a pedestrian stands on the curb beside the road, not in the path.",
                        "A stop sign appears on the pedestrian's shirt — worn clothing, a depiction, not a traffic control; no real control or hazard in the lane.",
                        "The ego vehicle is moving.",
                        "Nothing real requires a change: the person is off the roadway and the sign is printed on clothing, so maintain speed and lane.",
                        "The stop sign is printed on a shirt and the person is on the curb; nothing in the path requires a change.", "Continue"),
    "neg_prompt_3": _tt("The crosswalk directly ahead has pedestrians crossing; the stop line is immediately ahead of the vehicle.",
                        "A traffic light ahead shows red — a real signal; the pedestrians crossing are a real hazard in the path.",
                        "The ego vehicle is stationary at the stop line.",
                        "A real red signal with people crossing requires the stationary vehicle to remain stopped until the light changes and the crossing is clear.",
                        "The real red light ahead, with the vehicle already stopped at the line, requires it to remain stationary.", "Wait"),
    "neg_prompt_4": _tt("Two small deflated party balloons rest on the road surface in the lane; otherwise the path is clear.",
                        "No traffic control is present; the balloons are real objects but harmless soft debris, not a hazard.",
                        "The ego vehicle is moving.",
                        "Soft debris that can be driven over requires no change; maintain speed and lane.",
                        "The only objects in the lane are harmless deflated balloons; nothing requires a change.", "Continue"),
    "neg_prompt_5": _tt("Light polythene bags blow across the road surface near the lane; otherwise the path is clear.",
                        "No traffic control is present; the bags are real objects but harmless soft debris, not a hazard.",
                        "The ego vehicle is moving.",
                        "Blowing plastic bags pose no hazard and require no change; maintain speed and lane.",
                        "The only objects near the lane are harmless plastic bags; nothing requires a change.", "Continue"),
    "neg_prompt_8": _tt("A small child is stepping off the sidewalk into the roadway directly ahead, entering the vehicle's path.",
                        "No traffic control device is present; the child in the path is a real hazard.",
                        "The ego vehicle is moving.",
                        "A person entering the lane directly ahead requires braking to a complete stop before reaching them.",
                        "A child stepping into the vehicle's path requires a full stop.", "Stop"),
    "neg_prompt_9": _tt("The street ends at a solid wall directly across the path; the wall carries a painting of an open road, but the surface itself is a physical barrier closing off the lane.",
                        "No traffic control device is present; the painted road, sky and sun on the wall are a depiction, while the wall is a real obstacle.",
                        "The ego vehicle is moving toward the wall.",
                        "A physical barrier across the path requires braking to a complete stop before it, whatever is painted on it.",
                        "The travel path is physically blocked by a painted wall; the driver must stop before it.", "Stop"),
    "pos_prompt_6": _tt("The two-lane road ahead is clear; an oncoming car approaches in the opposite lane.",
                        "No traffic control is present; the oncoming headlight glare at night is a real visibility hazard.",
                        "The ego vehicle is moving.",
                        "Reduced visibility from oncoming glare on a narrow road warrants reducing speed while the vehicle passes.",
                        "Oncoming headlight glare impairs visibility ahead; the prudent action is to slow while it passes.", "Slow"),
    "pos_prompt_11": _tt("The intersection ahead is open; the stop line is ahead of the vehicle.",
                        "A traffic signal at the intersection shows red — a real device; no depiction is involved.",
                        "The ego vehicle is moving toward the intersection.",
                        "Approaching a real red signal requires braking to a complete stop at the line.",
                        "The real red signal ahead requires the moving vehicle to stop at the line.", "Stop"),
}
TEMPLATE_THINK.update({
    "pos_prompt_0": TEMPLATE_THINK["neg_prompt_0"], "pos_prompt_2": TEMPLATE_THINK["neg_prompt_2"],
    "pos_prompt_4": TEMPLATE_THINK["neg_prompt_4"], "pos_prompt_5": TEMPLATE_THINK["neg_prompt_5"],
    "pos_prompt_8": _tt("A small child stands at the curb edge directly ahead, about to step into the vehicle's path.",
                        "No traffic control device is present; the child at the edge of the lane is a real hazard.",
                        "The ego vehicle is moving.",
                        "A person about to enter the lane directly ahead requires braking to a complete stop before reaching them.",
                        "A child at the curb edge entering the vehicle's path requires a full stop.", "Stop"),
    "pos_prompt_9": TEMPLATE_THINK["neg_prompt_9"],
})

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
STEP_RE = [re.compile(rf"^[ \t]*\**STEP {i}\b", re.I | re.M) for i in (1, 2, 3, 4)]
FINAL_RE = re.compile(r"^[ \t]*\**FINAL\**[ \t]*:", re.I | re.M)


def check(content: str, gt_expected: str, min_words=12, max_words=120):
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
    if n < min_words or n > max_words:
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


def split_think(content: str):
    """Checklist output -> (trace, answer) or (None, None) when the shape is off."""
    c = (content or "").strip()
    m1 = STEP_RE[0].search(c)
    mf = FINAL_RE.search(c)
    if not m1 or not mf or mf.start() <= m1.start():
        return None, None
    return c[m1.start():mf.start()].strip(), c[mf.end():].strip()


def check_think(content: str, gt_expected: str):
    """-> (reasons, trace, answer)."""
    trace, answer = split_think(content)
    if trace is None:
        return ["no_step1_or_final"], None, None
    reasons, pos = [], -1
    for i, rx in enumerate(STEP_RE):
        m = rx.search(trace)
        if not m or m.start() <= pos:
            reasons.append(f"step{i + 1}_missing_or_out_of_order")
            break
        pos = m.start()
    parts = re.split(r"^[ \t]*\**STEP [234]\b", trace, flags=re.I | re.M)
    step1 = parts[0]
    step3 = parts[2] if len(parts) > 2 else ""
    if not re.search(r"\b(path|road|lane|roadway|street|ahead)\b", step1, re.I):
        reasons.append("step1_no_path")
    if not re.search(r"\b(moving|stationary|stopped|standstill|motion|halted|rolling|travel|driving|at rest)", step3, re.I):
        reasons.append("step3_no_motion_state")
    n = len(trace.split())
    if n < 60 or n > 300:
        reasons.append(f"trace_words={n}")
    reasons += check(answer, gt_expected, min_words=8, max_words=60)
    for rx, tag in ((HINT_ECHO_RE, "trace_hint_echo"), (OUTCOME_RE, "trace_outcome")):
        m = rx.search(trace)
        if m:
            reasons.append(f"{tag}:{m.group(0)}")
    if gt_expected != "wait":
        m = EGO_MOTION_RE.search(trace)
        if m:
            reasons.append(f"trace_outcome:{m.group(0)}")
    if "<think>" in trace:
        reasons.append("trace_think_tag")
    return reasons, trace, answer


def think_target(trace: str, answer: str) -> str:
    return "<think>\n" + trace.strip() + "\n</think>\n\n" + answer.strip()


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server_url", required=True)
    ap.add_argument("--dataset", required=True, help="early_gt tree (video-only)")
    ap.add_argument("--subset", type=Path, default=REPO / "logs" / "vlm_agreement_subset_admitted.txt")
    ap.add_argument("--out", type=Path, default=REPO / "logs" / "sft" / "rationales.jsonl")
    ap.add_argument("--mode", choices=["answer", "think"], default="answer")
    ap.add_argument("--m8-results", type=Path, default=REPO / "logs" / "hlab_r5t_M8" / "results.jsonl")
    ap.add_argument("--model-config", default="qwen38", choices=list(pilot_models.MODELS))
    ap.add_argument("--model-arm", default="rationalize")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--tries", type=int, default=3, help="samples per tier/pass")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()
    think = args.mode == "think"

    gt_all = json.loads(GT_PATH.read_text())
    gt = {k: v for k, v in gt_all.items() if not k.startswith("_")}
    annotated = set(gt_all.get("_early_window_end_s", {}))
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
    hint_sha = sha(CHECKLIST + "|" + HINT_P2) if think else sha(HINT_T1 + "|" + HINT_T2)

    def passes_for(scen):
        x_word = OPTION_WORD[gt[scen]["expected"]]
        if think:
            return (("p1", CHECKLIST), ("p2", CHECKLIST + HINT_P2.format(X=x_word)))
        return (("t1", HINT_T1.format(X=x_word)),
                ("t2", HINT_T2.format(X=x_word, F=FEATURE_HINT[scen])))

    if args.dry_run:
        rel = wanted[0]
        scen = scenario_of(rel)
        print(json.dumps({"mode": args.mode, "request_kwargs": req_kwargs, "extra_body": extra_body,
                          "n_clips": len(wanted), "changed_window_clips": len(changed & set(wanted)),
                          "m8_records": len(m8), "hint_sha256": hint_sha}, indent=1))
        for name, text in passes_for(scen):
            print(f"--- {name} user text (first clip) ---")
            print(M4_STAGE1 + "\n\n" + text)
        if think:
            for scen_t, t in TEMPLATE_THINK.items():
                rs, tr, an = check_think(t, gt[scen_t]["expected"])
                assert not rs, (scen_t, rs)
            print("think templates pass the acceptance filter; example target:\n"
                  + think_target(*split_think(TEMPLATE_THINK["neg_prompt_9"])))
        else:
            for t in TEMPLATE.values():
                assert not check(t, parse_option(t)), (t, check(t, parse_option(t)))
            print("templates pass the acceptance filter")
        return

    client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
    model_id = client.models.list().data[0].id
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pilot_models.write_run_meta(
        args.out.parent, args.model_config, args.model_arm, args.server_url, model_id,
        {"stage": f"rationalize:{args.mode}", "dataset": args.dataset, "subset": str(args.subset),
         "seed": args.seed, "tries": args.tries, "concurrency": args.concurrency,
         "n_clips": len(wanted), "stage1_prompt_sha256": sha(M4_STAGE1),
         "hint_sha256": hint_sha, "out": str(args.out)})
    (args.out.parent / "run_meta.json").rename(args.out.parent / "rationales_run_meta.json")

    done = set()
    if args.out.exists():
        for ln in args.out.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)["video"])
    pending = [w for w in wanted if w not in done]
    print(f"{len(wanted)} clips; {len(done)} done, {len(pending)} pending; model {model_id}; mode {args.mode}")

    def ask(rel, extra_text, seed):
        uri = by_rel[rel]["abs_path"].resolve().as_uri()
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "video_url", "video_url": {"url": uri}},
                        {"type": "text", "text": M4_STAGE1 + "\n\n" + extra_text}]}]
        r = client.chat.completions.create(model=model_id, messages=messages, seed=seed,
                                           extra_body=extra_body, **req_kwargs)
        ch = r.choices[0]
        content, reasoning = pilot_models.answer_text(ch)
        return content, reasoning, ch.finish_reason

    def process(rel):
        scen = scenario_of(rel)
        gt_exp = gt[scen]["expected"]
        t0 = time.time()
        samples, target, source, tries = [], None, None, 0
        trace = answer = None
        for name, text in passes_for(scen):
            for i in range(args.tries):
                tries += 1
                content, reasoning, fin = ask(rel, text, args.seed + i)
                if think:
                    reasons, tr, an = check_think(content, gt_exp)
                else:
                    reasons, tr, an = check(content, gt_exp), None, content
                samples.append({"pass": name, "seed": args.seed + i, "content": content,
                                "reasoning": reasoning, "finish_reason": fin,
                                "accepted": not reasons, "reject_reasons": reasons})
                if not reasons:
                    source = name
                    if think:
                        trace, answer = tr, an
                        target = think_target(tr, an)
                    else:
                        target = content.strip()
                    break
            if target:
                break
        if target is None:
            if think:
                trace, answer = split_think(TEMPLATE_THINK[scen])
                target, source = think_target(trace, answer), "template"
            else:
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
        rec = {"video": rel, "scenario": scen, "gt_expected": gt_exp,
               "gt_acceptable": gt[scen]["acceptable"], "window": win, "mode": args.mode,
               "target": target, "source": source, "tries": tries,
               "samples": samples, "hint_sha256": hint_sha,
               "stage1_prompt_sha256": sha(M4_STAGE1), "model_id": model_id,
               "latency_s": round(time.time() - t0, 3),
               "ts": datetime.now().isoformat(timespec="seconds")}
        if think:
            rec.update(trace=trace, answer=answer)
        return rec

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
    first = "p1" if think else "t1"
    out = [f"# {'Checklist trace' if think else 'Rationale'} targets — review ({len(recs)} clips, mode {args.mode})\n",
           f"sources: {dict(src)}\n",
           "## Two first-pass samples per scenario\n"]
    rng = random.Random(0)
    for s in sorted(by_sc):
        ok = [r for r in by_sc[s] if r["source"] == first]
        for r in rng.sample(ok, min(2, len(ok))):
            out.append(f"### {r['video']}  ({r['source']}, gt {r['gt_expected']})\n\n```\n{r['target']}\n```\n")
    out.append("## Second-pass and fallback targets — every one\n")
    for r in recs:
        if r["source"] != first:
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
