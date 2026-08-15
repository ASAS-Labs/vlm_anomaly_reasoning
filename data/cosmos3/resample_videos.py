#!/usr/bin/env python3
"""Re-encode eval videos to the inverse-dynamics model's frame rate.

The ID model reads the first `action_chunk_size + 1` = 61 frames of whatever it is
given, with no temporal resampling. At the native 24 fps that is 2.54s of a 5.04s
clip, so the prompted end-behaviour (the stop) is never seen. Re-encoding to 10 fps
makes 5.04s fit in ~51 frames -- the whole clip -- and simultaneously puts the frames
at the 10 Hz spacing the AV model expects.

Writes a manifest with the REAL output frame count per clip. That number is required
downstream: the framework pads short inputs by duplicating the last frame, and those
duplicates must be trimmed or they read as a stop that never happened.

    python data/cosmos3/resample_videos.py --fps 10 --sample 120
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

from utils import discover_eval_videos

DEFAULT_SRC = Path(__file__).resolve().parents[2] / "data" / "datasets" / "generated_vids"
UNIFORM_FRAMES = 121   # the 5.04s clips; the 21 x 193-frame clips are excluded


def probe(path: Path) -> dict:
    """Exact frame count and duration (counts frames rather than trusting metadata)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames,r_frame_rate:format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"frames": int(st["nb_read_frames"]),
            "fps": float(num) / float(den),
            "duration_s": float(d["format"]["duration"])}


def pick_sample(items, n, seed=0):
    """Deterministic balanced sample: equal share from each of the four eval folders."""
    if n is None or n >= len(items):
        return items
    rng = random.Random(seed)
    by_folder = {}
    for it in items:
        by_folder.setdefault(it["folder"], []).append(it)
    per = n // len(by_folder)
    picked = []
    for folder in sorted(by_folder):
        pool = sorted(by_folder[folder], key=lambda i: i["rel_path"])
        picked += pool if len(pool) <= per else rng.sample(pool, per)
    # Top up deterministically if integer division left a shortfall.
    if len(picked) < n:
        rest = sorted((i for i in items if i not in picked), key=lambda i: i["rel_path"])
        picked += rest[: n - len(picked)]
    return sorted(picked, key=lambda i: i["rel_path"])


def main():
    p = argparse.ArgumentParser(description="Resample eval videos for inverse dynamics")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--out", type=Path, default=None,
                   help="default <src>_<fps>fps")
    p.add_argument("--fps", type=int, default=10)
    p.add_argument("--sample", type=int, default=120,
                   help="balanced sample size; 0 or negative means all")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--limit", type=int, default=None, help="smoke-test cap")
    args = p.parse_args()

    out_root = args.out or args.src.parent / f"{args.src.name}_{args.fps}fps"
    items = discover_eval_videos(args.src)

    # Exclude the 21 non-uniform 8.04s clips: at 10 fps they need 80 frames, past the
    # 61-frame chunk, so they would carry a different coverage confound.
    uniform, long_clips = [], []
    for it in items:
        info = probe(it["abs_path"])
        (uniform if info["frames"] == UNIFORM_FRAMES else long_clips).append(it)
    print(f"{len(items)} eval clips: {len(uniform)} uniform ({UNIFORM_FRAMES} frames), "
          f"{len(long_clips)} excluded as non-uniform")

    # --limit goes through the same balanced picker so a smoke run still covers all
    # four folders rather than taking the first N alphabetically (all one folder).
    n_pick = args.limit or (args.sample if args.sample > 0 else None)
    chosen = pick_sample(uniform, n_pick, args.seed)

    n_anom = sum(1 for i in chosen if i["true_label"] == 1)
    print(f"resampling {len(chosen)} clips ({n_anom} anomaly / {len(chosen) - n_anom} "
          f"normal) -> {out_root} @ {args.fps}fps")

    manifest = []
    for n, it in enumerate(chosen, 1):
        dst = out_root / it["rel_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(it["abs_path"]),
             "-vf", f"fps={args.fps}", "-an", "-c:v", "libx264", "-crf", "12",
             "-preset", "veryfast", str(dst)], check=True)
        src_info, out_info = probe(it["abs_path"]), probe(dst)
        manifest.append({
            "rel_path": it["rel_path"], "true_label": it["true_label"],
            "folder": it["folder"], "on_skip_list": it["on_skip_list"],
            "src_frames": src_info["frames"], "src_fps": src_info["fps"],
            "out_frames": out_info["frames"], "out_fps": args.fps,
            "duration_s": round(out_info["duration_s"], 3),
        })
        if n % 20 == 0 or n == len(chosen):
            print(f"  [{n}/{len(chosen)}] {it['rel_path'].split('/')[-1]}: "
                  f"{src_info['frames']} -> {out_info['frames']} frames")

    mpath = out_root / "resample_manifest.json"
    mpath.write_text(json.dumps({"fps": args.fps, "src": str(args.src),
                                 "clips": manifest}, indent=2))

    over = [m for m in manifest if m["out_frames"] > 61]
    frames = sorted({m["out_frames"] for m in manifest})
    print(f"\nout_frames seen: {frames}")
    if over:
        print(f"WARNING: {len(over)} clip(s) exceed the 61-frame chunk and will be "
              f"truncated by the model", file=sys.stderr)
    print(f"manifest: {mpath}")


if __name__ == "__main__":
    main()
