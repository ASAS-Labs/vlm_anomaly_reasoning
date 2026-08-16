#!/usr/bin/env python3
"""Build one dataset tree per trajectory variant, offline.

Each variant tree mirrors the eval layout but contains a *symlink* to the original
24 fps mp4 plus that variant's `<stem>.txt` / `<stem>_10fps.txt`. Because
`discover_eval_videos` and `read_action_sequence` only need an mp4 with a sibling
txt, a variant tree is a drop-in `--dataset` for the eval runner -- no eval code
changes, and the original videos are never copied or rewritten.

Only `v1_resample` costs GPU time; every other raw-sourced variant is pure
post-processing of the same persisted poses, so iterating on the derivation is free.

    python data/cosmos3/derive_action_files.py --raw outputs/id_raw.jsonl --variants all
"""

import argparse
import json
from pathlib import Path

from id_trajectory import VARIANTS, derive_variant, scale_published
from utils import discover_eval_videos

DEFAULT_SRC = Path(__file__).resolve().parents[2] / "data" / "datasets" / "generated_vids"
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "datasets" / "id_variants"


def load_raw(path: Path) -> dict:
    recs = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            r = json.loads(line)
            recs[r["rel_path"]] = r
    return recs


def published_seqs(src_root: Path, rel_path: str):
    """The released 5 Hz and 10 Hz sequences for a clip."""
    mp4 = src_root / rel_path
    s5 = json.loads(mp4.with_name(mp4.stem + ".txt").read_text())
    s10 = json.loads(mp4.with_name(mp4.stem + "_10fps.txt").read_text())
    return s5, s10


def write_tree(out_root: Path, src_root: Path, rel_paths, seqs_for):
    """Write one variant tree. seqs_for(rel) -> (seq5, seq_native[, native_tag])."""
    n = 0
    for rel in rel_paths:
        got = seqs_for(rel)
        if got is None:
            continue
        native_tag = None
        if len(got) == 3:
            seq5, seq10, native_tag = got
        else:
            seq5, seq10 = got
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        # Symlink the ORIGINAL 24fps video: the VLM must still see the full clip.
        dst.symlink_to((src_root / rel).resolve())
        dst.with_name(dst.stem + ".txt").write_text(json.dumps(seq5) + "\n")
        # Native-rate sibling keeps the historical _10fps name only when it IS 10 fps.
        tag = "10fps" if native_tag is None else native_tag
        dst.with_name(f"{dst.stem}_{tag}.txt").write_text(json.dumps(seq10) + "\n")
        n += 1
    return n


def main():
    p = argparse.ArgumentParser(description="Derive trajectory variant trees")
    p.add_argument("--raw", type=Path, default=None,
                   help="id_raw.jsonl; required for raw-sourced variants")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--variants", default="all")
    args = p.parse_args()

    names = list(VARIANTS) if args.variants == "all" else args.variants.split(",")
    raw = load_raw(args.raw) if args.raw and args.raw.exists() else {}
    if raw:
        print(f"loaded {len(raw)} raw record(s) from {args.raw}")

    # The clip set is whatever the ID pass actually covered; falling back to the full
    # eval set when deriving published-only variants standalone.
    rel_paths = sorted(raw) if raw else [i["rel_path"] for i in discover_eval_videos(args.src)]

    summary = {}
    for name in names:
        cfg = VARIANTS[name]
        out_root = args.out / name

        if cfg["source"] == "published":
            def seqs_for(rel, _f=cfg["scale"]):
                try:
                    s5, s10 = published_seqs(args.src, rel)
                except FileNotFoundError:
                    return None
                if _f == 1.0:
                    return s5, s10
                return scale_published(s5, _f), scale_published(s10, _f)
        else:
            if not raw:
                print(f"  skip {name}: needs --raw")
                continue

            def seqs_for(rel, _n=name):
                r = raw.get(rel)
                if r is None:
                    return None
                s5, sn = derive_variant(r["poses"], r["input_fps"],
                                        r["n_valid_steps"] + 1, _n)
                fps = r["input_fps"]
                tag = None if abs(fps - 10.0) < 1e-9 else f"{fps:g}fps"
                return s5, sn, tag

        n = write_tree(out_root, args.src, rel_paths, seqs_for)
        # Gate: the tree must be discoverable by the same code the eval uses.
        items = discover_eval_videos(out_root, strict=False)
        n_anom = sum(1 for i in items if i["true_label"] == 1)
        lens = set()
        for i in items[:5]:
            lens.add(len(json.loads(
                i["abs_path"].with_name(i["abs_path"].stem + ".txt").read_text())))
        summary[name] = {"clips": n, "discovered": len(items),
                         "anomaly": n_anom, "normal": len(items) - n_anom,
                         "seq5_len": sorted(lens)}
        print(f"  {name:<14} {n:4d} clips -> {out_root}  "
              f"(discovered {len(items)}: {n_anom} anom / {len(items) - n_anom} norm, "
              f"5Hz len {sorted(lens)})  [{cfg['desc']}]")

    (args.out / "variants_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nsummary: {args.out / 'variants_summary.json'}")


if __name__ == "__main__":
    main()
