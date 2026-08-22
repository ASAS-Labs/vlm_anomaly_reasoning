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
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import openai

import pilot_models
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
    """The answer is the option word that LEADS a line, taking the last such line
    (prompts ask for the answer on the final line; a gloss like "... no need to
    stop" or a trailing parenthetical must not override it). Fallback: rightmost
    option word anywhere."""
    if not raw:
        return "unknown"
    for ln in reversed([ln.strip() for ln in raw.splitlines() if ln.strip()]):
        m = re.match(r"\W*([a-z]+)", ln.lower())
        if m and m.group(1) in EXPECT_OPTIONS:
            return m.group(1)
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
    p.add_argument("--model-config", default=None, choices=list(pilot_models.MODELS),
                   help="pilot model key: use its arm sampling + parsing")
    p.add_argument("--model-arm", default="expect",
                   help="pilot model arm for BOTH stages (H-lab: verdict_think16k)")
    p.add_argument("--hvariant", default=None,
                   help="H-lab registry id (h_variants.py): stage-1/stage-2 texts, "
                        "window and action rendering; default = legacy H3 texts")
    p.add_argument("--max_tokens", type=int, default=None,
                   help="override the resolved max_tokens")
    p.add_argument("--concurrency", type=int, default=1,
                   help="parallel in-flight requests (single writer preserved)")
    p.add_argument("--dry_run", action="store_true",
                   help="print resolved request config and exit (no server needed)")
    args = p.parse_args()

    # H-lab variant: texts/window/rendering from the registry; legacy texts otherwise.
    if args.hvariant:
        import h_variants
        hv = h_variants.H_VARIANTS[args.hvariant]
        stage1_text, stage2_tmpl = hv["stage1"], hv["stage2"]
        render = hv["action_render"]
        stage2_for = lambda seq: h_variants.stage2_prompt(hv, seq)  # noqa: E731
        hyp = hv["hypothesis"]
    else:
        hv = None
        stage1_text, stage2_tmpl, render = EXPECT_QUESTION, MONITOR_FOLLOWUP, "raw"
        stage2_for = lambda seq: MONITOR_FOLLOWUP.format(seq=seq)  # noqa: E731
        hyp = ("H3 two-stage monitor (legacy texts)" if args.stage == "monitor"
               else "stage-1 expectation (legacy text)")
    variant_id = args.hvariant or ("H3" if args.stage == "monitor" else args.stage)

    # Stage-1 request settings: Cosmos default unchanged; a pilot model key
    # swaps in that model's card-recommended arm (both stages under --hvariant).
    if args.model_config:
        req_kwargs, extra_body = pilot_models.request_kwargs(args.model_config,
                                                             args.model_arm)
    else:
        req_kwargs, extra_body = {"max_tokens": 30, "temperature": 0.0}, None
    if args.max_tokens:
        req_kwargs["max_tokens"] = args.max_tokens
    max_model_len = (pilot_models.MODELS[args.model_config]["max_model_len"]
                     if args.model_config else None)

    gt = json.loads((Path(__file__).parent / "expected_action_gt.json").read_text())
    gt.pop("_doc", None)

    if args.dry_run:
        info = {"model_config": args.model_config, "model_arm": args.model_arm,
                "stage": args.stage, "variant": variant_id, "hypothesis": hyp,
                "stage1_window": hv["stage1_window"] if hv else "(dataset)",
                "action_render": render, "request_kwargs": req_kwargs,
                "extra_body": extra_body, "seed": args.seed,
                "stage1_prompt_sha256": hashlib.sha256(stage1_text.encode()).hexdigest(),
                "stage2_prompt_sha256": hashlib.sha256(stage2_tmpl.encode()).hexdigest(),
                "stage1_prompt": stage1_text}
        if args.full_dataset and args.subset.exists():
            first = next((ln.strip() for ln in args.subset.read_text().splitlines()
                          if ln.strip()), None)
            if first:
                seq = read_action_sequence(Path(args.full_dataset) / first)
                info["stage2_prompt_rendered_for"] = first
                info["stage2_prompt"] = stage2_for(seq)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return

    items = discover_eval_videos(args.dataset, strict=False)
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    by_rel = {i["rel_path"]: i for i in items}
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"--subset: {len(missing)} clip(s) missing, e.g. {missing[:3]}")
    items = [by_rel[w] for w in wanted]
    if args.limit:
        items = items[: args.limit]
    no_gt = sorted({scenario_of(i["rel_path"]) for i in items} - set(gt))
    if no_gt:
        sys.exit(f"expected_action_gt.json lacks scenarios {no_gt}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "results.jsonl"
    s1_sha = hashlib.sha256(stage1_text.encode()).hexdigest()
    s2_sha = hashlib.sha256(stage2_tmpl.encode()).hexdigest()
    done = set()
    if out_path.exists():
        for ln in out_path.read_text().splitlines():
            if ln.strip():
                r0 = json.loads(ln)
                done.add(r0["video"])
                if r0.get("stage1_prompt_sha256", s1_sha) != s1_sha or \
                        r0.get("stage2_prompt_sha256", s2_sha) != s2_sha:
                    sys.exit(f"{out_path} holds records from different prompt texts; "
                             "use a fresh --out_dir")
    out = open(out_path, "a", encoding="utf-8")

    client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
    model_id = client.models.list().data[0].id

    if args.model_config:
        pilot_models.write_run_meta(
            args.out_dir, args.model_config, args.model_arm, args.server_url, model_id,
            {"stage": args.stage, "variant": variant_id, "hypothesis": hyp,
             "dataset": args.dataset, "full_dataset": args.full_dataset,
             "stage1_window": hv["stage1_window"] if hv else None,
             "action_render": render,
             "subset": str(args.subset), "seed": args.seed,
             "concurrency": args.concurrency, "n_clips": len(items),
             "prompt_sha256": s1_sha, "stage1_prompt_sha256": s1_sha,
             "stage2_prompt_sha256": s2_sha})

    def process(it):
        rel = it["rel_path"]
        scen = scenario_of(rel)
        g = gt[scen]
        uri = it["abs_path"].resolve().as_uri()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "video_url", "video_url": {"url": uri}},
                {"type": "text", "text": stage1_text},
            ]},
        ]
        t0 = time.time()
        k1 = (hv or {}).get("stage1_k", 1)
        s1_samples = []
        for i in range(max(1, k1)):
            r1 = client.chat.completions.create(model=model_id, messages=messages,
                                                seed=args.seed + i, extra_body=extra_body,
                                                **req_kwargs)
            ch = r1.choices[0]
            c_i, rs_i = pilot_models.answer_text(ch)
            s1_samples.append({"content": c_i, "reasoning": rs_i, "expect": parse_option(c_i),
                               "finish_reason": ch.finish_reason, "raw": ch.message.content})
        if k1 > 1:
            # majority vote over parsed options; the assistant turn carries the
            # content of the first sample that voted with the majority
            from collections import Counter
            votes = Counter(x["expect"] for x in s1_samples if x["expect"] != "unknown")
            expect = votes.most_common(1)[0][0] if votes else "unknown"
            pick = next((x for x in s1_samples if x["expect"] == expect), s1_samples[0])
            content, reasoning = pick["content"], pick["reasoning"]
            ch_finish, ch_raw = pick["finish_reason"], pick["raw"]
        else:
            content, reasoning = s1_samples[0]["content"], s1_samples[0]["reasoning"]
            expect = s1_samples[0]["expect"]
            ch_finish, ch_raw = s1_samples[0]["finish_reason"], s1_samples[0]["raw"]
        rec = {"video": rel, "scenario": scen, "stage": args.stage,
               "variant": variant_id, "hypothesis": hyp,
               "true_label": it["true_label"],
               "gt_expected": g["expected"], "gt_acceptable": g["acceptable"],
               "expect_raw": ch_raw, "expect": expect,
               "expect_strict": expect == g["expected"],
               "expect_lenient": expect in g["acceptable"],
               "finish_reason": ch_finish,
               "stage1_prompt_sha256": s1_sha,
               "ts": datetime.now().isoformat(timespec="seconds")}
        if args.model_config:
            rec.update(model_config=args.model_config, model_arm=args.model_arm,
                       stage1_window=hv["stage1_window"] if hv else None)
        if reasoning is not None:
            rec["reasoning_content"] = reasoning
        if k1 > 1:
            rec["stage1_k"] = k1
            rec["stage1_votes"] = [x["expect"] for x in s1_samples]

        if args.stage == "monitor" and not content.strip():
            # stage 1 produced no answer (e.g. unterminated think): there is no
            # expectation to compare against; record an Unknown verdict.
            rec["expect_finish_reason"] = rec.pop("finish_reason")
            rec.update(monitor_raw=None, verdict="Unknown", parse_reason="stage1_empty",
                       finish_reason=None, correct=None, action_sequence=None,
                       action_render=render, stage2_prompt_sha256=s2_sha)
        elif args.stage == "monitor":
            full_tree = Path(args.full_dataset)
            seq_text = read_action_sequence(full_tree / rel)
            prompt2 = stage2_for(seq_text)
            messages += [
                {"role": "assistant", "content": content},
                {"role": "user", "content": prompt2},
            ]
            if args.model_config:
                # Same arm as stage 1; clamp the budget to the context window
                # (stage-1 prompt incl. video tokens + answer + follow-up).
                kw2 = dict(req_kwargs)
                used = ((r1.usage.prompt_tokens if r1.usage else 0)
                        + len(content) // 3 + len(prompt2) // 3 + 256)
                room = max_model_len - used
                if room < 1024:
                    raise RuntimeError(f"{rel}: stage-2 context room {room} < 1024")
                kw2["max_tokens"] = min(kw2["max_tokens"], room)
                r2 = client.chat.completions.create(model=model_id, messages=messages,
                                                    seed=args.seed,
                                                    extra_body=extra_body, **kw2)
                ch2 = r2.choices[0]
                content2, reasoning2 = pilot_models.answer_text(ch2)
                rec["stage2_max_tokens"] = kw2["max_tokens"]
                if reasoning2 is not None:
                    rec["monitor_reasoning_content"] = reasoning2
            else:
                r2 = client.chat.completions.create(model=model_id, messages=messages,
                                                    max_tokens=200, temperature=0.0,
                                                    seed=args.seed)
                ch2 = r2.choices[0]
                content2 = ch2.message.content
            parsed = parse_verdict(content2, ch2.finish_reason)
            pred = {"Anomaly": 1, "Normal": 0}.get(parsed["verdict"])
            # monitor records report the stage-2 finish_reason at top level
            rec["expect_finish_reason"] = rec.pop("finish_reason")
            rec.update(monitor_raw=ch2.message.content, verdict=parsed["verdict"],
                       parse_reason=parsed["reason"], finish_reason=ch2.finish_reason,
                       correct=None if pred is None else pred == it["true_label"],
                       action_sequence=seq_text, action_render=render,
                       stage2_prompt_sha256=s2_sha)
            if render != "raw":
                rec["action_rendered"] = h_variants.render_action(render, seq_text)

        rec["latency_s"] = round(time.time() - t0, 3)
        return rec

    pending = [it for it in items if it["rel_path"] not in done]
    n = errors = 0
    # Requests may run in parallel; the main thread stays the sole writer so the
    # fsync-per-record and resume-by-video invariants are unchanged. A failed
    # request is logged and skipped so completed work still persists; re-running
    # resumes the missing clips.
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = [pool.submit(process, it) for it in pending]
        for fut in as_completed(futures):
            try:
                rec = fut.result()
            except Exception as e:
                errors += 1
                print(f"request failed: {e}", file=sys.stderr, flush=True)
                continue
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
            n += 1
            tail = rec.get("verdict", rec["expect"])
            print(f"[{n}] {rec['video'].split('/')[-1]}: expect={rec['expect']} "
                  f"(gt={rec['gt_expected']}) -> {tail}", flush=True)
    out.close()
    if errors:
        sys.exit(f"{errors} request(s) failed; re-run to resume the missing clips")

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
