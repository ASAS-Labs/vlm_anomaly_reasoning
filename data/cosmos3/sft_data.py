#!/usr/bin/env python3
"""Build the stage-1 SFT dataset (family N): leave-scene-group-out folds over the
235-clip agreement subset, ms-swift train.jsonl per fold, held-out lists, manifest.

Each training example = the EXACT served stage-1 request (system prompt + M4_STAGE1
over the clip's 2.5 s decision-time window from generated_vids_720p_early_gt) with
the rationale+final-word target from sft_rationalize.py. No think block in the data
(ms-swift --add_non_thinking_prefix adds the empty one). GT never enters a prompt.

    python sft_data.py --rationales ../../logs/sft/rationales.jsonl \
        --video-root /abs/data/datasets/generated_vids_720p_early_gt --out ../../logs/sft
    python sft_data.py --self-test
    python sft_data.py --dry-run --targets-from-m8 --video-root ... --out <scratch>
"""

import argparse
import hashlib
import json
import random
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
        # per-scenario round-robin: every scene appears in train (learnability diagnostic)
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
            # scene pairs co-located: no group appears in both sides
            assert not ({group_of(c) for c in d["held_out"]}
                        & {group_of(c) for c in d["train"]}), f"{f}: scene group leaks"


def example(rel, target, video_root: Path):
    return {"messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": USER_TEXT},
                         {"role": "assistant", "content": target}],
            "videos": [str((video_root / rel).resolve())]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rationales", type=Path, default=REPO / "logs" / "sft" / "rationales.jsonl")
    ap.add_argument("--video-root", type=Path,
                    default=REPO / "data" / "datasets" / "generated_vids_720p_early_gt")
    ap.add_argument("--out", type=Path, default=REPO / "logs" / "sft")
    ap.add_argument("--scheme", choices=["logo5", "within5"], default="logo5")
    ap.add_argument("--shuffle-seed", type=int, default=1234,
                    help="train.jsonl row order (and within5 assignment)")
    ap.add_argument("--smoke", type=int, default=10, help="rows in smoke/train.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="do not require rationales/APPROVED; allow --targets-from-m8")
    ap.add_argument("--targets-from-m8", action="store_true",
                    help="stand-in targets = M8's own expect_raw (dry runs only)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    clips = [ln.strip() for ln in ADMITTED.read_text().splitlines() if ln.strip()]
    gt = load_gt()

    if args.self_test:
        for scheme in ("logo5", "within5"):
            folds = assign(clips, scheme, 1234)
            check_folds(folds, clips, scheme)
            sizes = {f: (len(d["held_out"]), len(d["train"])) for f, d in folds.items()}
            print(f"{scheme}: {sizes}")
        f = assign(clips, "logo5", 1234)["f1"]["held_out"]
        assert {scenario_of(c) for c in f} == {"neg_prompt_9", "pos_prompt_9", "pos_prompt_6"}
        assert sha(USER_TEXT[len("<video>"):]) == sha(M4_STAGE1)
        print("self-test ok")
        return

    # ---- targets ----
    targets, sources = {}, {}
    if args.targets_from_m8:
        assert args.dry_run, "--targets-from-m8 is for --dry-run only"
        for ln in M8_RESULTS.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                targets[r["video"]] = (r["expect_raw"] or "").strip()
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
        opt = parse_option(t)
        if opt not in gt[scenario_of(c)]["acceptable"]:
            bad.append((c, opt))
        if not (args.video_root / c).exists():
            sys.exit(f"video missing: {args.video_root / c}")
    if bad and not args.dry_run:
        sys.exit(f"{len(bad)} target(s) do not parse into the acceptable set: {bad[:3]}")
    elif bad:
        print(f"[dry-run] {len(bad)} stand-in target(s) outside the acceptable set (expected for M8 errors)")

    folds = assign(clips, args.scheme, args.shuffle_seed)
    check_folds(folds, clips, args.scheme)

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
        # re-read and assert the user turn is byte-identical to the served prompt
        for ln in (fd / "train.jsonl").read_text().splitlines():
            row = json.loads(ln)
            assert row["messages"][0]["content"] == SYSTEM_PROMPT
            assert row["messages"][1]["content"] == USER_TEXT
            assert "<think>" not in row["messages"][2]["content"]
        fold_summary[f] = {
            "groups": d["groups"], "n_train": len(d["train"]), "n_held_out": len(d["held_out"]),
            "held_out_labels": dict(Counter("anomaly" if "negative" in c else "normal"
                                            for c in d["held_out"])),
            "held_out_gt": dict(Counter(gt[scenario_of(c)]["expected"] for c in d["held_out"])),
            "train_gt": dict(Counter(gt[scenario_of(c)]["expected"] for c in d["train"])),
            "target_sources_train": dict(Counter(sources[c] for c in d["train"])),
        }
    smoke_dir = args.out / "smoke"
    smoke_dir.mkdir(exist_ok=True)
    smoke_rows = [example(c, targets[c], args.video_root) for c in folds["f1"]["train"][:args.smoke]]
    (smoke_dir / "train.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                                   for r in smoke_rows))
    (args.out / "folds.json").write_text(json.dumps(
        {"scheme": args.scheme, "shuffle_seed": args.shuffle_seed,
         "folds": {f: {"groups": d["groups"], "held_out": d["held_out"], "train": d["train"]}
                   for f, d in folds.items()}}, indent=1))

    m8_sha = None
    if M8_RUN_META.exists():
        m8_sha = json.load(open(M8_RUN_META)).get("stage1_prompt_sha256")
        assert m8_sha == sha(M4_STAGE1), "M4_STAGE1 changed since the M8 run of record"
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             cwd=REPO).stdout.strip()
    except OSError:
        git = None
    words = [len(targets[c].split()) for c in clips]
    manifest = {"scheme": args.scheme, "n_clips": len(clips), "n_scenarios": len({scenario_of(c) for c in clips}),
                "system_prompt_sha256": sha(SYSTEM_PROMPT), "stage1_prompt_sha256": sha(M4_STAGE1),
                "stage1_prompt_sha256_matches_m8_run": m8_sha == sha(M4_STAGE1),
                "user_text_sha256": sha(USER_TEXT), "video_root": str(args.video_root.resolve()),
                "rationales": None if args.targets_from_m8 else str(args.rationales),
                "target_sources": dict(Counter(sources.values())),
                "target_words": {"min": min(words), "median": sorted(words)[len(words) // 2], "max": max(words)},
                "folds": fold_summary, "smoke_rows": len(smoke_rows), "shuffle_seed": args.shuffle_seed,
                "dry_run": args.dry_run, "git_commit": git}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for f, s in fold_summary.items():
        print(f"{f}: held_out {s['n_held_out']} {s['held_out_labels']} gt {s['held_out_gt']} | train {s['n_train']}")
    print(f"targets: {manifest['target_sources']} words {manifest['target_words']}")
    print(f"wrote {args.out}/{{folds.json,manifest.json,f*/train.jsonl,f*/held_out.txt,smoke/train.jsonl}}")


if __name__ == "__main__":
    main()
