#!/usr/bin/env python3
"""Prompt-lab runner: evaluate registered prompt variants over the agreement subset.

One results.jsonl per variant (logs/plab_r<round>_<id>/), same record shape as the
main runner so reparse tooling keeps working; fsync'd and resume-keyed per video.
Self-consistency (k>1) stores every sample and the vote.

    python prompt_lab.py --round 1 --variants all --dataset <720p tree> \\
        --subset <72-list> --server_url http://127.0.0.1:8000/v1
"""

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import openai

import pilot_models
from prompt_variants import VARIANTS, build_prompt, parse_binary
from utils import PARSER_VERSION, discover_eval_videos, parse_verdict, read_action_sequence

SYSTEM_PROMPT = "You are a helpful assistant."


def parse_for(variant: dict, raw: str, finish_reason):
    if variant["parser"] == "binary":
        v = parse_binary(raw)
        return {"verdict": v, "reason": "binary", "parser_version": PARSER_VERSION,
                "truncated": finish_reason == "length"}
    return parse_verdict(raw, finish_reason)


def run_variant(vid, variant, items, client, model_id, out_dir, seed, k, dry,
                model_cfg=None, model_arm="verdict", concurrency=1):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.jsonl"
    done = set()
    if path.exists():
        for ln in path.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)["video"])
    f = open(path, "a", encoding="utf-8")

    # A pilot model key replaces the variant's sampling/max_tokens with that
    # model's card-recommended arm (incl. its think switch and, for opt-in
    # thinkers like InternVL, a custom system prompt).
    if model_cfg:
        req_kwargs, req_extra = pilot_models.request_kwargs(model_cfg, model_arm)
        sys_prompt = pilot_models.MODELS[model_cfg]["arms"][model_arm].get(
            "system", SYSTEM_PROMPT)
    else:
        req_kwargs = req_extra = None
        sys_prompt = SYSTEM_PROMPT

    def process(it):
        rel = it["rel_path"]
        action_text = None
        if variant["mode"] != "video_only":
            action_text = read_action_sequence(it["abs_path"])
        precall_records = []
        observations = None
        if variant.get("precall") and not dry:
            # Self-context: ask the model its own probe questions first (greedy),
            # then present its answers back as prior observations. All inputs are
            # deployment-available; nothing external is injected.
            qa = []
            for q in variant["precall"]:
                r = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": [
                            {"type": "video_url",
                             "video_url": {"url": it["abs_path"].resolve().as_uri()}},
                            {"type": "text", "text": q},
                        ]},
                    ],
                    max_tokens=60, temperature=0.0, seed=seed)
                a = r.choices[0].message.content
                precall_records.append({"q": q, "a": a})
                qa.append(f"Q: {q}\nA: {a}")
            observations = "\n".join(qa)
        prompt = build_prompt(variant, action_text)
        if "{observations}" in prompt:
            prompt = prompt.replace("{observations}", observations or "(none)")
        rec = {"video": rel, "variant": vid, "hypothesis": variant["hypothesis"],
               "mode": variant["mode"], "true_label": it["true_label"],
               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
               "sampling": ({**req_kwargs, **(req_extra or {})} if model_cfg
                            else variant["sampling"]),
               "k": k if k > 1 else 1,
               "ts": datetime.now().isoformat(timespec="seconds")}
        if model_cfg:
            rec["model_config"] = model_cfg
        if precall_records:
            rec["precall"] = precall_records
        if dry:
            rec.update(verdict="DryRun", raw_output=None, correct=None, prompt=prompt)
        else:
            t0 = time.time()
            samples = []
            for i in range(max(1, k)):
                if model_cfg:
                    kwargs, extra = dict(req_kwargs), req_extra
                    temp = kwargs.get("temperature", 0.0)
                else:
                    s = dict(variant["sampling"])
                    temp = s.pop("temperature", 0.0)
                    extra = {kk: vv for kk, vv in s.items() if kk not in ("top_p",)}
                    kwargs = {"top_p": s["top_p"]} if "top_p" in s else {}
                    kwargs.update(max_tokens=variant["max_tokens"], temperature=temp)
                r = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": [
                            {"type": "video_url",
                             "video_url": {"url": it["abs_path"].resolve().as_uri()}},
                            {"type": "text", "text": prompt},
                        ]},
                    ],
                    seed=seed + i if temp > 0 else seed,
                    extra_body=extra or None, **kwargs)
                ch = r.choices[0]
                if model_cfg:
                    # Reasoning-parser servers put the trace in reasoning_content;
                    # only the final answer content may produce a verdict.
                    content, reasoning = pilot_models.answer_text(ch)
                else:
                    content, reasoning = ch.message.content, None
                parsed = parse_for(variant, content, ch.finish_reason)
                sample = {"raw_output": ch.message.content,
                          "finish_reason": ch.finish_reason,
                          "verdict": parsed["verdict"],
                          "parse": {kk: vv for kk, vv in parsed.items()
                                    if kk != "verdict"}}
                if reasoning is not None:
                    sample["reasoning_content"] = reasoning
                samples.append(sample)
            votes = Counter(s["verdict"] for s in samples
                            if s["verdict"] in ("Anomaly", "Normal"))
            verdict = votes.most_common(1)[0][0] if votes else "Unknown"
            pred = {"Anomaly": 1, "Normal": 0}.get(verdict)
            rec.update(verdict=verdict, votes=dict(votes),
                       raw_output=samples[0]["raw_output"] if len(samples) == 1 else None,
                       samples=samples if len(samples) > 1 else None,
                       finish_reason=samples[0]["finish_reason"],
                       parse=samples[0]["parse"],
                       correct=None if pred is None else pred == it["true_label"],
                       latency_s=round(time.time() - t0, 3))
            if len(samples) == 1 and samples[0].get("reasoning_content") is not None:
                rec["reasoning_content"] = samples[0]["reasoning_content"]
        return rec

    pending = [it for it in items if it["rel_path"] not in done]
    n = errors = 0
    # Parallel request issuance; this thread stays the sole writer so the
    # fsync-per-record and resume-by-video invariants hold. Failed requests are
    # logged and skipped so completed work persists; re-running resumes them.
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        for fut in as_completed([pool.submit(process, it) for it in pending]):
            try:
                rec = fut.result()
            except Exception as e:
                errors += 1
                print(f"  [{vid}] request failed: {e}", file=sys.stderr, flush=True)
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
            n += 1
            if not dry:
                print(f"  [{vid} {n}] {rec['video'].split('/')[-1]}: {rec['verdict']} "
                      f"({'ok' if rec['correct'] else 'X'})", flush=True)
    f.close()
    if errors:
        sys.exit(f"{vid}: {errors} request(s) failed; re-run to resume")
    recs = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    real = [r for r in recs if r.get("correct") is not None]
    if real:
        print(f"{vid}: {sum(r['correct'] for r in real)}/{len(real)}")
    return n


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--variants", default="all")
    p.add_argument("--dataset", required=True)
    p.add_argument("--subset", type=Path, required=True)
    p.add_argument("--server_url", default=None)
    p.add_argument("--out_root", type=Path,
                   default=Path(__file__).resolve().parents[2] / "logs")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--k", type=int, default=1, help="samples per clip (majority vote)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry_run", action="store_true")
    p.add_argument("--model-config", default=None, choices=list(pilot_models.MODELS),
                   help="pilot model key: its --model-arm replaces variant sampling")
    p.add_argument("--model-arm", default="verdict",
                   help="which arm of the model config to use (verdict, verdict_think)")
    p.add_argument("--out_prefix", default=None,
                   help="output dir prefix (default plab_r<round>)")
    p.add_argument("--concurrency", type=int, default=1,
                   help="parallel in-flight requests (single writer preserved)")
    args = p.parse_args()

    names = list(VARIANTS) if args.variants == "all" else args.variants.split(",")
    for nm in names:
        if nm not in VARIANTS:
            sys.exit(f"unknown variant {nm}")
        if args.model_config and VARIANTS[nm].get("precall"):
            sys.exit(f"{nm}: precall variants are not wired for --model-config "
                     "(precall requests stay Cosmos-tuned)")

    items = discover_eval_videos(args.dataset, strict=False)
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    by_rel = {i["rel_path"]: i for i in items}
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"--subset: {len(missing)} clip(s) missing, e.g. {missing[:3]}")
    items = [by_rel[w] for w in wanted]
    if args.limit:
        items = items[: args.limit]

    client = model_id = None
    if not args.dry_run:
        client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
        model_id = client.models.list().data[0].id

    prefix = args.out_prefix or f"plab_r{args.round}"
    for nm in names:
        out_dir = args.out_root / f"{prefix}_{nm}"
        print(f"=== {nm}: {VARIANTS[nm]['hypothesis']} ===")
        if args.model_config and not args.dry_run:
            pilot_models.write_run_meta(
                out_dir, args.model_config, args.model_arm, args.server_url,
                model_id,
                {"variant": nm, "dataset": args.dataset,
                 "subset": str(args.subset), "seed": args.seed, "k": args.k,
                 "concurrency": args.concurrency, "n_clips": len(items)})
        run_variant(nm, VARIANTS[nm], items, client, model_id, out_dir,
                    args.seed, args.k, args.dry_run,
                    model_cfg=args.model_config, model_arm=args.model_arm,
                    concurrency=args.concurrency)


if __name__ == "__main__":
    main()
