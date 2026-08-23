#!/usr/bin/env python3
"""Build the two input trees the pilot arms consume, for the agreement subset.

1. hires: 832x480 -> 1248x720 lanczos upscale (the F2 input standard; the
   original tree lived only on a destroyed instance, this makes it reproducible).
2. early: the stage-1 window of each hires clip — fixed length, T-minus, or the
   per-clip decision-time window from expected_action_gt.json (`--early-mode gt`:
   the 2.5 s rolling window [max(0, end-2.5), end] for every clip, end = the
   annotated decision time where present, else T-2.5) — trimmed from the hires
   output so both arms share identical pixels.

    python make_pilot_trees.py --subset ../../logs/vlm_agreement_subset_admitted.txt
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from resample_videos import probe
from utils import discover_eval_videos

DEFAULT_SRC = Path(__file__).resolve().parents[2] / "data" / "datasets" / "generated_vids"


def encode(src: Path, dst: Path, extra_in: list, vf: list):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *extra_in,
         "-i", str(src), *vf, "-an", "-c:v", "libx264", "-crf", "12",
         "-preset", "veryfast", str(dst)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--subset", type=Path, required=True)
    p.add_argument("--out-hires", type=Path, default=None,
                   help="default <src parent>/generated_vids_720p")
    p.add_argument("--out-early", type=Path, default=None,
                   help="default <src parent>/generated_vids_720p_early")
    p.add_argument("--early-secs", type=float, default=2.5,
                   help="fixed mode: window length; t_minus mode: seconds hidden "
                        "at the end (window = duration - early-secs)")
    p.add_argument("--early-mode", choices=["fixed", "t_minus", "gt"], default="fixed",
                   help="gt: 2.5 s rolling window ending at the clip's annotated decision "
                        "time (expected_action_gt.json _early_window_end_s), else at T-2.5")
    p.add_argument("--gt-json", type=Path,
                   default=Path(__file__).resolve().parent / "expected_action_gt.json")
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    hires_root = args.out_hires or args.src.parent / "generated_vids_720p"
    if args.early_mode in ("t_minus", "gt") and args.out_early is None:
        sys.exit(f"--early-mode {args.early_mode} requires an explicit --out-early")
    gt_ends, gt_default = {}, None
    if args.early_mode == "gt":
        gt = json.loads(args.gt_json.read_text())
        gt_ends = gt.get("_early_window_end_s", {})
        gt_default = gt["_early_window_default"]
    early_root = args.out_early or args.src.parent / "generated_vids_720p_early"

    items = discover_eval_videos(args.src, strict=False)
    by_rel = {i["rel_path"]: i for i in items}
    wanted = [ln.strip() for ln in args.subset.read_text().splitlines() if ln.strip()]
    missing = [w for w in wanted if w not in by_rel]
    if missing:
        sys.exit(f"--subset: {len(missing)} clip(s) missing, e.g. {missing[:3]}")

    manifests = {hires_root: [], early_root: []}
    for n, rel in enumerate(wanted, 1):
        src = by_rel[rel]["abs_path"]
        hires = hires_root / rel
        early = early_root / rel
        if not (args.skip_existing and hires.exists()):
            encode(src, hires, [], ["-vf", "scale=1248:720:flags=lanczos"])
        h = probe(hires)
        start = 0.0
        if args.early_mode == "fixed":
            want = args.early_secs
        elif args.early_mode == "t_minus":
            want = h["duration_s"] - args.early_secs
        else:
            # one rolling window of length_s for every clip; the annotation only
            # moves where it ends (default end = duration - end_tminus_s)
            end = (float(gt_ends[rel]) if rel in gt_ends
                   else h["duration_s"] - gt_default["end_tminus_s"])
            start = max(0.0, end - gt_default["length_s"])
            want = end - start
        if not (args.skip_existing and early.exists()):
            encode(hires, early, (["-ss", f"{start:.3f}"] if start else []) + ["-t", f"{want:.3f}"], [])
        e = probe(early)
        manifests[hires_root].append({"rel_path": rel, **h})
        manifests[early_root].append({"rel_path": rel, **e, "early_secs": round(want, 3),
                                      "early_start_s": round(start, 3),
                                      "early_end_s": round(start + want, 3)})
        if abs(e["duration_s"] - want) > 0.3:
            sys.exit(f"{rel}: early duration {e['duration_s']:.2f}s, "
                     f"expected ~{want:.2f}s")
        if n % 10 == 0 or n == len(wanted):
            print(f"  [{n}/{len(wanted)}] {rel.split('/')[-1]}: "
                  f"hires {h['frames']}f / early {e['frames']}f", flush=True)

    for root, clips in manifests.items():
        # Resolution assert: ffprobe width/height of the first clip.
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0",
             str(root / wanted[0])], capture_output=True, text=True, check=True)
        w, hgt = out.stdout.strip().split(",")
        if (w, hgt) != ("1248", "720"):
            sys.exit(f"{root}: resolution {w}x{hgt}, expected 1248x720")
        mpath = root / "pilot_tree_manifest.json"
        mpath.write_text(json.dumps(
            {"src": str(args.src), "subset": str(args.subset),
             "early_secs": args.early_secs if root is early_root else None,
             "early_mode": args.early_mode if root is early_root else None,
             "clips": clips}, indent=2))
        print(f"{root}: {len(clips)} clips, {w}x{hgt}, manifest {mpath.name}")


if __name__ == "__main__":
    main()
