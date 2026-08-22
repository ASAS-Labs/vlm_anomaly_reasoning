#!/usr/bin/env python3
"""Build the two input trees the pilot arms consume, for the agreement subset.

1. hires: 832x480 -> 1248x720 lanczos upscale (the F2 input standard; the
   original tree lived only on a destroyed instance, this makes it reproducible).
2. early: the first 2.5 s of each hires clip, for the expect_early arm — trimmed
   from the hires output so both arms share identical pixels.

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
    p.add_argument("--early-mode", choices=["fixed", "t_minus"], default="fixed")
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    hires_root = args.out_hires or args.src.parent / "generated_vids_720p"
    if args.early_mode == "t_minus" and args.out_early is None:
        sys.exit("--early-mode t_minus requires an explicit --out-early")
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
        want = (args.early_secs if args.early_mode == "fixed"
                else h["duration_s"] - args.early_secs)
        if not (args.skip_existing and early.exists()):
            encode(hires, early, ["-t", f"{want:.3f}"], [])
        e = probe(early)
        manifests[hires_root].append({"rel_path": rel, **h})
        manifests[early_root].append({"rel_path": rel, **e, "early_secs": round(want, 3)})
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
