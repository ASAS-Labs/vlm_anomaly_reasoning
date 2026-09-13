#!/usr/bin/env python3
"""Render and stage taxonomy-extension clips on the vast.ai box (see spec/run_extension_remote.sh).

  render --round 1 --server-url URL
      every extension/*/prompt_<k>.json at the release settings, seed 1234 ->
      data/datasets/extension_vids/<polarity>/prompt_<k>.mp4 (skip existing)
  render --round N --server-url URL --targets logs/extension/roundN_targets.json [--max-seeds 4]
      best-of-N fresh seeds per failing clip with the flow-probe gate ->
      data/datasets/extension_candidates/roundN/<polarity>/prompt_<k>__s<seed>.mp4 + manifest.json
  stage --round N
      copy the round's clips (round 1: all; round N: the probe-preferred candidate per
      target) into data/datasets/extension_round<N>{,_10fps}/ with resample_manifest.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from regen_fix import EXTRA_PARAMS, GUIDANCE, NUM_STEPS, SEEDS, SHIFT, _next_candidate, ffprobe_geometry, probe_ok  # noqa: E402

EXT = HERE / "video_gen_prompts" / "extension"
VIDS = REPO / "data" / "datasets" / "extension_vids"
NEG_PROMPT = (HERE / "text2video_neg_prompt.json").read_text().strip()
WIDTH, HEIGHT, FRAMES, FPS, SEED0 = 832, 480, 121, 24, 1234


def cand_root(rnd: int) -> Path:
    return REPO / "data" / "datasets" / "extension_candidates" / f"round{rnd}"


def round_dirs(rnd: int) -> tuple[Path, Path]:
    root = REPO / "data" / "datasets" / f"extension_round{rnd}"
    return root, root.parent / f"extension_round{rnd}_10fps"


def all_rels() -> list[str]:
    rels = []
    for pol in ("positive_scenarios", "negative_scenarios"):
        for j in (EXT / pol).glob("prompt_*.json"):
            rels.append(f"{pol}/{j.stem}.mp4")
    return sorted(rels, key=lambda r: (r.split("/")[0], int(r.split("_")[-1].split(".")[0])))


def prompt_text(rel: str) -> str:
    return json.dumps(json.loads((EXT / rel.replace(".mp4", ".json")).read_text()),
                      separators=(",", ":"), ensure_ascii=False)


def request(server: str, text: str, seed: int, out: Path) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".mp4.tmp")
    form = {"prompt": text, "negative_prompt": NEG_PROMPT, "size": f"{WIDTH}x{HEIGHT}",
            "num_frames": str(FRAMES), "fps": str(FPS), "num_inference_steps": str(NUM_STEPS),
            "guidance_scale": str(GUIDANCE), "flow_shift": str(SHIFT), "seed": str(seed),
            "extra_params": EXTRA_PARAMS}
    cmd = ["curl", "-sS", "--fail-with-body", "-X", "POST", f"{server}/v1/videos/sync",
           "-H", "Accept: video/mp4"]
    for k, v in form.items():
        cmd += ["--form-string", f"{k}={v}"]
    cmd += ["-o", str(tmp)]
    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        print(f"  {out.name}: request failed: {r.stderr[:200]}", flush=True)
        return False
    tmp.replace(out)
    return True


def cmd_render(args) -> int:
    if args.round == 1:
        rels = all_rels()
        done = 0
        for i, rel in enumerate(rels, 1):
            out = VIDS / rel
            if out.exists():
                continue
            if request(args.server_url, prompt_text(rel), SEED0, out):
                done += 1
                print(f"[{i}/{len(rels)}] {rel}", flush=True)
        print(f"round 1: rendered {done}, present {sum((VIDS / r).exists() for r in rels)}/{len(rels)}")
        return 0
    from video_motion import video_verdict
    targets = json.loads(args.targets.read_text())
    mpath = cand_root(args.round) / "manifest.json"
    m = json.loads(mpath.read_text()) if mpath.exists() else {}
    for t in targets:
        rel, cls = t["rel_path"], t["class"]
        rec = m.setdefault(rel, {"class": cls, "attempts": [], "accepted": None})
        if rec["accepted"] or any(a["probe_ok"] and a["id_ok"] is None for a in rec["attempts"]):
            continue
        tried = set(t.get("tried_seeds", [])) | {a["seed"] for a in rec["attempts"]}
        text, n_this = prompt_text(rel), 0
        for seed in SEEDS:
            if seed in tried or n_this >= args.max_seeds:
                continue
            out = cand_root(args.round) / rel.replace(".mp4", f"__s{seed}.mp4")
            if not request(args.server_url, text, seed, out):
                continue
            v = video_verdict(str(out), fps=float(FPS))
            ok = probe_ok(cls, v)
            rec["attempts"].append({"round": args.round, "seed": seed, "path": str(out.relative_to(REPO)),
                                    "probe": v, "probe_ok": ok, "id_ok": None})
            n_this += 1
            print(f"  {rel} s{seed}: end={v['end_state']} tail={v['tail_flow']:.3f} -> "
                  f"{'PASS' if ok else 'fail'}", flush=True)
            mpath.parent.mkdir(parents=True, exist_ok=True)
            mpath.write_text(json.dumps(m, indent=1))
            if ok:
                break
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(m, indent=1))
    passing = sum(1 for r in m.values() if any(a["probe_ok"] for a in r["attempts"]))
    print(f"round {args.round}: targets with a probe-passing candidate: {passing}/{len(targets)}")
    return 0


def to_10fps(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vf", "fps=10",
                        "-an", "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", str(dst)], check=True)


def cmd_stage(args) -> int:
    root, root10 = round_dirs(args.round)
    clips = []
    if args.round == 1:
        staged = [(rel, VIDS / rel, SEED0) for rel in all_rels() if (VIDS / rel).exists()]
    else:
        mpath = cand_root(args.round) / "manifest.json"
        m = json.loads(mpath.read_text())
        staged = []
        for rel, rec in m.items():
            if rec["accepted"]:
                continue
            cand = _next_candidate(rec)
            if cand is None:
                continue
            cand["staged_round"] = args.round
            staged.append((rel, REPO / cand["path"], cand["seed"]))
        mpath.write_text(json.dumps(m, indent=1))
    for rel, src, seed in staged:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        to_10fps(dst, root10 / rel)
        clips.append({"rel_path": rel, "out_fps": 10, "out_frames": ffprobe_geometry(root10 / rel)["frames"],
                      "seed": seed, "src_frames": ffprobe_geometry(dst)["frames"]})
    root10.mkdir(parents=True, exist_ok=True)
    (root10 / "resample_manifest.json").write_text(json.dumps({"fps": 10, "src": str(root), "clips": clips}, indent=1))
    print(f"staged {len(clips)} clip(s) in {root10}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--round", type=int, required=True)
    r.add_argument("--server-url", default="http://127.0.0.1:8000")
    r.add_argument("--targets", type=Path)
    r.add_argument("--max-seeds", type=int, default=4)
    s = sub.add_parser("stage")
    s.add_argument("--round", type=int, required=True)
    args = ap.parse_args()
    return {"render": cmd_render, "stage": cmd_stage}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
