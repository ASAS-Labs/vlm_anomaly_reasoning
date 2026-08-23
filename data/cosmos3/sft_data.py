#!/usr/bin/env python3
"""Build the stage-1 SFT dataset (family N): leave-scene-group-out folds over the
235-clip agreement subset, ms-swift train.jsonl per fold, held-out lists, manifest.

Each training example = the EXACT served stage-1 request (system prompt + M4_STAGE1
over the clip's 2.5 s decision-time window from generated_vids_720p_early_gt) with
the target from sft_rationalize.py:
  --target-format answer : rationale + final word (no think block; ms-swift adds the
                           empty one; loss_scale ignore_empty_think)
  --target-format think  : "<think>\\n{4-step checklist}\\n</think>\\n\\n{final}" (loss on
                           the trace; loss_scale default); manifest carries the
                           stage-1 think budget derived from the training targets.
GT never enters a prompt.

    python sft_data.py --rationales ../../logs/sft/rationales.jsonl \
        --video-root /abs/data/datasets/generated_vids_720p_early_gt --out ../../logs/sft
    python sft_data.py --target-format think --rationales ../../logs/sft_think/traces.jsonl \
        --folds-from ../../logs/sft/folds.json --out ../../logs/sft_think [--tokenizer /path/to/base]
    python sft_data.py --self-test
    python sft_data.py --dry-run --targets-from-m8 --video-root ... --out <scratch>
"""

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from expectation_experiment import SYSTEM_PROMPT, parse_option, scenario_of
from h_variants import M4_STAGE1

REPO = Path(__file__).resolve().parents[2]
ADMITTED = REPO / "logs" / "vlm_agreement_subset_admitted.txt"
GT_PATH = Path(__file__).resolve().parent / "expected_action_gt.json"
M8_RESULTS = REPO / "logs" / "hlab_r5t_M8" / "results.jsonl"
M8_RUN_META = REPO / "logs" / "hlab_r5t_M8" / "run_meta.json"

# Leave-scene-group-out: group = scenario number; both polarities of a pair
# travel together. Concept families are split across folds (plan §1).
FOLDS_LOGO5 = {"f1": [9, 6], "f2": [5, 3], "f3": [0, 11], "f4": [4], "f5": [2, 8]}
USER_TEXT = "<video>" + M4_STAGE1
THINK_RE = re.compile(r"<think>\n(.*?)\n</think>\n\n", re.S)


def group_of(rel: str) -> int:
    return int(scenario_of(rel).split("_")[-1])


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_gt():
    gt = json.loads(GT_PATH.read_text())
    return {k: v for k, v in gt.items() if not k.startswith("_")}


def assign(clips, scheme, seed):
    """-> {fold: {"held_out": [...], "train": [...], "groups": [...]}} ; admitted order."""
    folds = {}
    if scheme == "logo5":
        for f, groups in FOLDS_LOGO5.items():
            held = [c for c in clips if group_of(c) in groups]
            folds[f] = {"groups": groups, "held_out": held}
    elif scheme == "within5":
        by = defaultdict(list)
        for c in clips:
            by[scenario_of(c)].append(c)
        rng = random.Random(seed)
        held = defaultdict(list)
        for s in sorted(by):
            pool = sorted(by[s])
            rng.shuffle(pool)
            for i, c in enumerate(pool):
                held[f"f{i % 5 + 1}"].append(c)
        for f in ("f1", "f2", "f3", "f4", "f5"):
            folds[f] = {"groups": "within-scenario round-robin",
                        "held_out": [c for c in clips if c in set(held[f])]}
    else:
        raise ValueError(scheme)
    for f, d in folds.items():
        ho = set(d["held_out"])
        d["train"] = [c for c in clips if c not in ho]
    return folds


def check_folds(folds, clips, scheme):
    all_held = [c for d in folds.values() for c in d["held_out"]]
    assert sorted(all_held) == sorted(clips), "every clip held out exactly once"
    assert len(set(all_held)) == len(clips)
    for f, d in folds.items():
        assert not (set(d["held_out"]) & set(d["train"])), f"{f}: train/held-out overlap"
        assert len(d["held_out"]) + len(d["train"]) == len(clips)
        if scheme == "logo5":
            assert not ({group_of(c) for c in d["held_out"]}
                        & {group_of(c) for c in d["train"]}), f"{f}: scene group leaks"


def example(rel, target, video_root: Path):
    return {"messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": USER_TEXT},
                         {"role": "assistant", "content": target}],
            "videos": [str((video_root / rel).resolve())]}


def token_counter(tokenizer_path):
    """Exact token counts with the base tokenizer when available, else words*1.4."""
    if tokenizer_path:
        try:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(tokenizer_path)
            return (lambda s: len(tok(s)["input_ids"])), "tokenizer"
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] tokenizer unavailable ({exc}); using words*1.4")
    return (lambda s: int(math.ceil(len(s.split()) * 1.4))), "words*1.4"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rationales", type=Path, default=REPO / "logs" / "sft" / "rationales.jsonl")
    ap.add_argument("--video-root", type=Path,
                    default=REPO / "data" / "datasets" / "generated_vids_720p_early_gt")
    ap.add_argument("--out", type=Path, default=REPO / "logs" / "sft")
    ap.add_argument("--scheme", choices=["logo5", "within5"], default="logo5")
    ap.add_argument("--folds-from", type=Path, default=None,
                    help="reuse the fold assignment of an existing folds.json (asserted identical clips)")
    ap.add_argument("--target-format", choices=["answer", "think"], default="answer")
    ap.add_argument("--tokenizer", default=None, help="base model path for exact think-budget tokens")
    ap.add_argument("--budget-margin", type=int, default=512)
    ap.add_argument("--shuffle-seed", type=int, default=1234)
    ap.add_argument("--smoke", type=int, default=10, help="rows in smoke/train.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--targets-from-m8", action="store_true",
                    help="stand-in targets = M8's own expect_raw (dry runs only)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    think = args.target_format == "think"

    clips = [ln.strip() for ln in ADMITTED.read_text().splitlines() if ln.strip()]
    gt = load_gt()

    if args.self_test:
        for scheme in ("logo5", "within5"):
            folds = assign(clips, scheme, 1234)
            check_folds(folds, clips, scheme)
            print(f"{scheme}: {{f: (held, train)}} =",
                  {f: (len(d['held_out']), len(d['train'])) for f, d in folds.items()})
        f = assign(clips, "logo5", 1234)["f1"]["held_out"]
        assert {scenario_of(c) for c in f} == {"neg_prompt_9", "pos_prompt_9", "pos_prompt_6"}
        assert sha(USER_TEXT[len("<video>"):]) == sha(M4_STAGE1)
        t = "<think>\nSTEP 1 — PATH: x\nSTEP 2 — CONTROLS: y\nSTEP 3 — MOTION: z\nSTEP 4 — ACTION: w\n</think>\n\nFinal.\nStop"
        assert THINK_RE.search(t) and parse_option(t) == "stop"
        print("self-test ok")
        return

    # ---- targets ----
    targets, sources = {}, {}
    if args.targets_from_m8:
        assert args.dry_run, "--targets-from-m8 is for --dry-run only"
        for ln in M8_RESULTS.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                raw = (r["expect_raw"] or "").strip()
                if think:   # synthetic think shape from the stand-in text
                    raw = ("<think>\nSTEP 1 — PATH: (stand-in)\nSTEP 2 — CONTROLS: (stand-in)\n"
                           "STEP 3 — MOTION: (stand-in)\nSTEP 4 — ACTION: (stand-in)\n</think>\n\n" + raw)
                targets[r["video"]] = raw
                sources[r["video"]] = "m8_expect_raw(dry)"
    else:
        if not args.rationales.exists():
            sys.exit(f"missing {args.rationales} (run sft_rationalize.py first)")
        for ln in args.rationales.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                targets[r["video"]] = r["target"]
                sources[r["video"]] = r["source"]
    missing = [c for c in clips if c not in targets]
    if missing:
        sys.exit(f"{len(missing)} clip(s) without a target, e.g. {missing[:3]}")

    # ---- guards on targets and paths ----
    bad = []
    for c in clips:
        t = targets[c]
        if parse_option(t) not in gt[scenario_of(c)]["acceptable"]:
            bad.append((c, parse_option(t)))
        if think:
            m = THINK_RE.search(t)
            if not (t.startswith("<think>\n") and m and t.count("<think>") == 1
                    and all(f"STEP {i}" in m.group(1) for i in (1, 2, 3, 4))):
                bad.append((c, "think-shape"))
        elif "<think>" in t:
            bad.append((c, "think-tag-in-answer-target"))
        if not (args.video_root / c).exists():
            sys.exit(f"video missing: {args.video_root / c}")
    if bad and not args.dry_run:
        sys.exit(f"{len(bad)} target(s) fail the guards: {bad[:3]}")
    elif bad:
        print(f"[dry-run] {len(bad)} stand-in target(s) fail the guards (expected for M8 errors)")

    if args.folds_from:
        src = json.loads(args.folds_from.read_text())
        folds = {f: {"groups": d["groups"], "held_out": d["held_out"], "train": d["train"]}
                 for f, d in src["folds"].items()}
        scheme = src["scheme"]
        assert sorted(c for d in folds.values() for c in d["held_out"]) == sorted(clips), \
            "--folds-from covers a different clip set"
    else:
        folds, scheme = assign(clips, args.scheme, args.shuffle_seed), args.scheme
    check_folds(folds, clips, scheme)

    # ---- write ----
    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.shuffle_seed)
    fold_summary = {}
    for f, d in folds.items():
        fd = args.out / f
        fd.mkdir(exist_ok=True)
        rows = [example(c, targets[c], args.video_root) for c in d["train"]]
        rng.shuffle(rows)
        with open(fd / "train.jsonl", "w") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        (fd / "held_out.txt").write_text("\n".join(d["held_out"]) + "\n")
        for ln in (fd / "train.jsonl").read_text().splitlines():
            row = json.loads(ln)
            assert row["messages"][0]["content"] == SYSTEM_PROMPT
            assert row["messages"][1]["content"] == USER_TEXT
            if think:
                assert row["messages"][2]["content"].startswith("<think>\n")
            else:
                assert "<think>" not in row["messages"][2]["content"]
        fold_summary[f] = {
            "groups": d["groups"], "n_train": len(d["train"]), "n_held_out": len(d["held_out"]),
            "held_out_labels": dict(Counter("anomaly" if "negative" in c else "normal" for c in d["held_out"])),
            "held_out_gt": dict(Counter(gt[scenario_of(c)]["expected"] for c in d["held_out"])),
            "train_gt": dict(Counter(gt[scenario_of(c)]["expected"] for c in d["train"])),
            "target_sources_train": dict(Counter(sources[c] for c in d["train"])),
        }
    smoke_dir = args.out / "smoke"
    smoke_dir.mkdir(exist_ok=True)
    smoke_rows = [example(c, targets[c], args.video_root) for c in folds["f1"]["train"][:args.smoke]]
    (smoke_dir / "train.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in smoke_rows))
    (args.out / "folds.json").write_text(json.dumps(
        {"scheme": scheme, "shuffle_seed": args.shuffle_seed, "folds_from": str(args.folds_from) if args.folds_from else None,
         "folds": {f: {"groups": d["groups"], "held_out": d["held_out"], "train": d["train"]}
                   for f, d in folds.items()}}, indent=1))

    m8_sha = None
    if M8_RUN_META.exists():
        m8_sha = json.load(open(M8_RUN_META)).get("stage1_prompt_sha256")
        assert m8_sha == sha(M4_STAGE1), "M4_STAGE1 changed since the M8 run of record"
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip()
    except OSError:
        git = None
    words = [len(targets[c].split()) for c in clips]
    count, how = token_counter(args.tokenizer)
    toks = sorted(count(targets[c]) for c in clips)
    p99 = toks[min(len(toks) - 1, int(math.ceil(0.99 * len(toks))) - 1)]
    think_budget = int(math.ceil((p99 + args.budget_margin) / 256.0) * 256) if think else None
    manifest = {"scheme": scheme, "target_format": args.target_format, "n_clips": len(clips),
                "n_scenarios": len({scenario_of(c) for c in clips}),
                "system_prompt_sha256": sha(SYSTEM_PROMPT), "stage1_prompt_sha256": sha(M4_STAGE1),
                "stage1_prompt_sha256_matches_m8_run": m8_sha == sha(M4_STAGE1),
                "user_text_sha256": sha(USER_TEXT), "video_root": str(args.video_root.resolve()),
                "rationales": None if args.targets_from_m8 else str(args.rationales),
                "target_sources": dict(Counter(sources.values())),
                "target_words": {"min": min(words), "median": sorted(words)[len(words) // 2], "max": max(words)},
                "target_tokens": {"method": how, "min": toks[0], "median": toks[len(toks) // 2], "p99": p99, "max": toks[-1]},
                "think_budget": think_budget, "budget_margin": args.budget_margin,
                "folds": fold_summary, "smoke_rows": len(smoke_rows), "shuffle_seed": args.shuffle_seed,
                "dry_run": args.dry_run, "git_commit": git}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for f, s in fold_summary.items():
        print(f"{f}: held_out {s['n_held_out']} {s['held_out_labels']} gt {s['held_out_gt']} | train {s['n_train']}")
    print(f"targets: {manifest['target_sources']} words {manifest['target_words']} tokens {manifest['target_tokens']} think_budget {think_budget}")
    print(f"wrote {args.out}/{{folds.json,manifest.json,f*/train.jsonl,f*/held_out.txt,smoke/train.jsonl}}")


if __name__ == "__main__":
    main()
