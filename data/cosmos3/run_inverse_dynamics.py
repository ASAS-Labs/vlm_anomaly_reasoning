"""run_inverse_dynamics.py - Cosmos3 action inverse-dynamics over generated_vids.

Runs Cosmos3-Nano inverse-dynamics inference (native Cosmos Framework PyTorch
entrypoint, the same path as
packages/cosmos/cookbooks/cosmos3/generator/action/run_id_with_cosmos_framework.ipynb) on every
video under data/cosmos3/generated_vids (next to this script). For each video it:

  1. predicts the ego-motion action trajectory ([T-1, 9] = translation(3) + rot6d(6)),
  2. converts it with pose_rel_to_abs into camera-to-world poses (metric: with
     translation_scale=1.35 the cookbook documents the poses as meters),
  3. derives [[velocity, heading_angle_from_center], ...] sequences at the native
     FPS and downsampled to TARGET_HZ - velocity in mph from metric displacements
     (initial velocity from the first INIT_VELOCITY_FRAMES frames at native FPS,
     before downsampling), heading in degrees relative to the first frame,
  4. validates the tail of the native-rate sequence against the last sentence of
     the matching prompt line. The video tree under generated_vids mirrors the
     prompts tree (default data/cosmos3/video_gen_prompts, override with
     --prompts-root or PROMPTS_ROOT): for each video the nearest
     updated_human_prompt.txt (falling back to prompt.txt) is found by walking
     up the mirrored directory path, with '<name>_variants' folders sharing
     '<name>'s prompt file. prompt_N (variant suffixes like prompt_3_v07 are
     trimmed) maps to line N (0-based) of that file; mismatches are flagged.
  5. saves the downsampled sequence as <video>.txt and the native-rate sequence
     as <video>_<FPS>fps.txt next to the video, and
  6. uploads all .txt files plus inverse_dynamics_flags.txt to the Hugging Face
     dataset repo in one commit at the mirrored paths.

Setup (run once):

    ./setup_inverse_dynamics.sh
    export HF_TOKEN=<write token with gated-model + dataset access>

Run (any interpreter; it re-execs into the framework venv automatically):

    python data/cosmos3/run_inverse_dynamics.py
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from prompt_resolve import prompt_sentence_for

# --- Configuration (the only things you should need to change) -----------
HF_DATASET_REPO = "ASASLab/av_semantic_anomalies"
HF_REVISION = "main"
INIT_VELOCITY_FRAMES = 5  # native-rate frames used to evaluate the initial velocity
MPS_TO_MPH = 2.2369362921
FPS = 10                  # model action rate (AV inverse-dynamics is 10 Hz)
TARGET_HZ = 5             # downsample the final action sequence to this rate
ACTION_CHUNK_SIZE = 60    # AV reference setting (60 frames @ 10 FPS)
IMAGE_SIZE = 480
CHECKPOINT = "Cosmos3-Nano"

# Validation thresholds (heuristic, language-based).
TAIL_RANGE = (0.05, 0.2)  # start_v: [5%, 20%); end_v: [80%, 95%) — skip noisy edges
DECEL_RATIO = 0.6   # end/start velocity below this => decelerating
ACCEL_RATIO = 1.4   # end/start velocity above this => accelerating
MAINTAIN_LO = 0.6   # maintain band: MAINTAIN_LO*start <= end <= MAINTAIN_HI*start
MAINTAIN_HI = 1.6
STEER_DEG = 5.0     # max |heading change| above this => steering


def find_repo_root(start: Path) -> Path:
    """Root of this repo: walk up to .git (or the vendored framework for
    non-git deployments, e.g. rsync'd to a GPU machine)."""
    for path in [start, *start.parents]:
        if (path / ".git").exists() or (path / "packages" / "cosmos-framework").exists():
            return path
    return start


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(SCRIPT_DIR)
GENERATED_VIDS_DIR = REPO_ROOT / "data/datasets/generated_vids"
DEFAULT_PROMPTS_ROOT = Path(os.environ.get("PROMPTS_ROOT", REPO_ROOT / "data/cosmos3/video_gen_prompts"))
COSMOS3_REPO = Path(os.environ.get("COSMOS3_REPO", REPO_ROOT / "packages" / "cosmos-framework")).resolve()
WORK_DIR = Path(os.environ.get("COSMOS3_ID_WORK_DIR", REPO_ROOT / "outputs" / "inverse_dynamics")).resolve()
SPEC_PATH = WORK_DIR / "inverse_dynamics_av.jsonl"
RUNS_DIR = WORK_DIR / "runs"


# ---------------------------------------------------------------------------
# Runtime environment (ported from run_id_with_cosmos_framework.ipynb, step 5):
# the framework venv ships CUDA + PyAV/ffmpeg shared libraries that must be on
# LD_LIBRARY_PATH before torch/cosmos_framework import. We configure the env and
# re-exec once under the framework venv python so the dynamic linker picks it up.
# ---------------------------------------------------------------------------
def framework_site_packages(python_bin: Path) -> Path | None:
    venv_root = python_bin.parent.parent
    for site_packages in sorted((venv_root / "lib").glob("python*/site-packages")):
        if (site_packages / "nvidia").is_dir():
            return site_packages
    return None


def nvidia_cuda_library_dirs(python_bin: Path) -> list[Path]:
    site_packages = framework_site_packages(python_bin)
    if site_packages is None:
        return []
    nvidia_root = site_packages / "nvidia"
    lib_dirs = []
    for lib_dir in sorted(nvidia_root.glob("**/lib")):
        if any(lib_dir.glob("lib*.so*")):
            lib_dirs.append(lib_dir)
    return lib_dirs


def torchcodec_ffmpeg_library_dirs(python_bin: Path, link_dir: Path) -> list[Path]:
    site_packages = framework_site_packages(python_bin)
    if site_packages is None:
        return []
    av_libs = site_packages / "av.libs"
    if not av_libs.is_dir():
        return []
    soname_patterns = {
        "libavcodec.so.62": "libavcodec-*.so.62*",
        "libavdevice.so.62": "libavdevice-*.so.62*",
        "libavfilter.so.11": "libavfilter-*.so.11*",
        "libavformat.so.62": "libavformat-*.so.62*",
        "libavutil.so.60": "libavutil-*.so.60*",
        "libswresample.so.6": "libswresample-*.so.6*",
        "libswscale.so.9": "libswscale-*.so.9*",
    }
    linked_any = False
    for soname, pattern in soname_patterns.items():
        matches = sorted(av_libs.glob(pattern))
        if not matches:
            continue
        link_dir.mkdir(parents=True, exist_ok=True)
        link = link_dir / soname
        target = matches[-1].resolve()
        if link.is_symlink() and link.resolve() == target:
            linked_any = True
            continue
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
        linked_any = True
    return [link_dir, av_libs] if linked_any else []


def set_nvidia_package_home(env, site_packages: Path | None, env_name: str, package_name: str) -> None:
    if site_packages is None:
        return
    package_dir = site_packages / "nvidia" / package_name
    if package_dir.is_dir():
        env.setdefault(env_name, str(package_dir))


def ensure_nvidia_package_alias(site_packages: Path | None, alias_name: str, package_name: str) -> None:
    if site_packages is None:
        return
    package_dir = site_packages / "nvidia" / package_name
    alias_dir = site_packages / "nvidia" / alias_name
    if not package_dir.is_dir():
        return
    if alias_dir.is_symlink() and not alias_dir.exists():
        alias_dir.unlink()
    if not alias_dir.exists():
        alias_dir.symlink_to(package_dir, target_is_directory=True)


def prepend_env_paths(env, name: str, paths: list[Path]) -> None:
    new_paths = [str(path) for path in paths if path.exists()]
    old_paths = [path for path in env.get(name, "").split(":") if path]
    merged = []
    for path in [*new_paths, *old_paths]:
        if path not in merged:
            merged.append(path)
    if merged:
        env[name] = ":".join(merged)


def bootstrap_runtime_env() -> None:
    """Configure CUDA/ffmpeg env for the framework venv and re-exec once under it."""
    if os.environ.get("COSMOS3_ID_ENV_READY") == "1":
        return

    python_bin = COSMOS3_REPO / ".venv" / "bin" / "python"
    if not python_bin.exists():
        raise SystemExit(
            f"missing framework venv python: {python_bin}\n"
            f"Run ./setup_inverse_dynamics.sh first."
        )

    cuda_lib_dirs = nvidia_cuda_library_dirs(python_bin)
    ffmpeg_lib_dirs = torchcodec_ffmpeg_library_dirs(python_bin, WORK_DIR / "torchcodec_ffmpeg_links")
    prepend_env_paths(os.environ, "PYTHONPATH", [COSMOS3_REPO])
    prepend_env_paths(os.environ, "LD_LIBRARY_PATH", [*ffmpeg_lib_dirs, *cuda_lib_dirs])

    site_packages = framework_site_packages(python_bin)
    ensure_nvidia_package_alias(site_packages, "cudart", "cuda_runtime")
    set_nvidia_package_home(os.environ, site_packages, "CUDNN_HOME", "cudnn")
    set_nvidia_package_home(os.environ, site_packages, "CUDART_HOME", "cuda_runtime")
    set_nvidia_package_home(os.environ, site_packages, "NVRTC_HOME", "cuda_nvrtc")
    set_nvidia_package_home(os.environ, site_packages, "CURAND_HOME", "curand")
    cuda_include_dir = site_packages / "nvidia" / "cuda_runtime" / "include" if site_packages else None
    if cuda_include_dir and cuda_include_dir.exists():
        os.environ.setdefault("NVTE_CUDA_INCLUDE_DIR", str(cuda_include_dir))

    os.environ["COSMOS3_ID_ENV_READY"] = "1"
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
    os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    # Re-exec under the framework venv python so the new LD_LIBRARY_PATH applies
    # and cosmos_framework / torch import from the right interpreter.
    os.execv(str(python_bin), [str(python_bin), os.path.abspath(__file__), *sys.argv[1:]])


# ---------------------------------------------------------------------------
# Discovery + spec
# ---------------------------------------------------------------------------
def video_name(rel_path: Path) -> str:
    """Stable run name from a generated_vids-relative path (slashes -> '__')."""
    return rel_path.with_suffix("").as_posix().replace("/", "__")


def discover_videos(videos_root: Path = None) -> list[dict]:
    root = videos_root or GENERATED_VIDS_DIR
    videos = sorted(root.rglob("*.mp4"))
    if not videos:
        raise SystemExit(f"No .mp4 files found under {root}")
    records = []
    for path in videos:
        rel = path.relative_to(root)
        records.append({"name": video_name(rel), "video_path": path, "rel_path": rel})
    return records


def build_spec(records: list[dict]) -> None:
    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for rec in records:
        lines.append(json.dumps({
            "action_chunk_size": ACTION_CHUNK_SIZE,
            "domain_name": "av",
            "fps": FPS,
            "image_size": IMAGE_SIZE,
            "view_point": "ego_view",
            "model_mode": "inverse_dynamics",
            "name": rec["name"],
            "prompt": "You are an autonomous vehicle planning system.",
            "seed": 0,
            "vision_path": str(rec["video_path"].resolve()),
        }))
    SPEC_PATH.write_text("\n".join(lines) + "\n")
    print(f"wrote spec ({len(records)} run(s)): {SPEC_PATH}")


def free_local_port() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return str(sock.getsockname()[1])


def run_inference() -> None:
    python_bin = COSMOS3_REPO / ".venv" / "bin" / "python"
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("CUDA_VISIBLE_DEVICES", "0")
    env["MASTER_ADDR"] = env.get("MASTER_ADDR", "127.0.0.1")
    env["MASTER_PORT"] = env.get("MASTER_PORT", free_local_port())
    env["RANK"] = "0"
    env["WORLD_SIZE"] = "1"
    env["LOCAL_RANK"] = "0"
    cmd = [
        str(python_bin), "-m", "cosmos_framework.scripts.inference",
        "--parallelism-preset=latency",
        "-i", str(SPEC_PATH),
        "-o", str(RUNS_DIR),
        "--checkpoint-path", CHECKPOINT,
        "--seed", "0",
        "--no-guardrails",  # disable the Cosmos guardrail (avoids the gated Guardrail1 download + safety checks)
    ]
    print("running inference:\n  " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(COSMOS3_REPO), env=env, check=True)


def output_path_for(name: str) -> Path:
    return RUNS_DIR / name / "sample_outputs.json"


# ---------------------------------------------------------------------------
# Conversion: predicted action -> [[velocity, heading_angle_from_center], ...]
# ---------------------------------------------------------------------------
def _poses_to_sequence(poses, hz: float) -> list[list[float]]:
    """[[velocity_mph, heading_deg], ...] from absolute poses sampled at hz."""
    import numpy as np

    if len(poses) < 2:
        return []
    pos = poses[:, :3, 3]   # camera centers (world; X right, Y up, Z heading)
    fwd = poses[:, :3, 2]   # heading direction (+Z)

    # Heading (deg) relative to the first frame, on the ground plane (X-Z).
    yaw = np.arctan2(fwd[:, 0], fwd[:, 2])
    heading = np.degrees(np.unwrap(yaw - yaw[0]))

    # Ground-plane per-step displacement (meters) -> speed in mph.
    disp = np.diff(pos[:, [0, 2]], axis=0)
    d = np.linalg.norm(disp, axis=1)
    velocity = d * hz * MPS_TO_MPH
    return [[round(float(velocity[i]), 4), round(float(heading[i]), 4)] for i in range(len(d))]


def action_to_sequence(action, hz=None, n_valid=None):
    """Convert a predicted action [T-1, 9] into native-rate and 5 Hz sequences.

    Returns (downsampled_seq, native_seq, initial_velocity_mph). pose_rel_to_abs
    with translation_scale=1.35 yields camera-to-world poses in meters (per the
    cookbook), so velocity is the metric ground-plane speed converted to mph;
    heading is degrees relative to the first frame. The initial velocity is
    evaluated over the first INIT_VELOCITY_FRAMES steps at the native FPS,
    before downsampling.
    """
    import numpy as np
    from cosmos_framework.data.vfm.action.pose_utils import pose_rel_to_abs

    from id_trajectory import derive_10hz, to_5hz

    action = np.asarray(action, dtype=np.float64)
    poses_abs = np.asarray(pose_rel_to_abs(
        action,
        rotation_format="rot6d",
        pose_convention="backward_framewise",
        translation_scale=1.35,
    ), dtype=np.float64)  # [T, 4, 4] camera-to-world (meters)

    # hz is the TRUE spacing of the frames the model consumed. Using the FPS constant
    # here regardless of the video's actual rate is what scaled every published
    # velocity by 10/24. n_valid drops the frames the framework padded by repeating
    # the last one, which would otherwise read as a stop that never happened.
    seq_native = derive_10hz(poses_abs, hz, n_valid)
    if not seq_native:
        return [], [], 0.0, poses_abs

    initial_velocity = float(
        np.mean([r[0] for r in seq_native[:INIT_VELOCITY_FRAMES]]))
    seq = to_5hz(seq_native, "decimate")
    return seq, seq_native, initial_velocity, poses_abs


# ---------------------------------------------------------------------------
# Validation against the prompt's last sentence
# (last_sentence / resolve_prompt_file / prompt_sentence_for: prompt_resolve.py)
# ---------------------------------------------------------------------------
# These moved to id_semantics.py so every trajectory variant is scored by the
# same rules; that module also adds an absolute stop test, since the end/start
# ratio used here can never verify that a vehicle actually reached zero.
from id_semantics import check_match, classify_expected, evaluate_sequence  # noqa: E402



# ---------------------------------------------------------------------------
def main() -> None:
    bootstrap_runtime_env()  # configures env + re-execs once; returns only when ready

    import argparse

    from huggingface_hub import CommitOperationAdd, HfApi

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompts-root", type=Path, default=DEFAULT_PROMPTS_ROOT,
        help="root of the prompts tree mirrored by generated_vids "
             "(default: $PROMPTS_ROOT or video_gen_prompts next to this script)",
    )
    parser.add_argument(
        "--videos-root", type=Path, default=GENERATED_VIDS_DIR,
        help="video tree to run inference over; point this at a resampled tree",
    )
    parser.add_argument(
        "--manifest", type=Path, default=None,
        help="resample_manifest.json from resample_videos.py. Supplies the true input "
             "fps and the real (unpadded) frame count per clip - both required for a "
             "correct trajectory.",
    )
    parser.add_argument("--raw-out", type=Path, default=None,
                        help="persist raw poses/actions to this JSONL so trajectory "
                             "variants can be derived offline without re-running")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--write-inplace-txt", action="store_true",
        help="write <video>.txt next to each video. OFF by default: an experimental "
             "run would otherwise silently overwrite the released baseline files.",
    )
    parser.add_argument(
        "--upload", action="store_true",
        help=f"upload results to {HF_DATASET_REPO}. OFF by default.",
    )
    args = parser.parse_args()
    prompts_root = args.prompts_root.resolve()
    videos_root = args.videos_root.resolve()

    manifest = {}
    if args.manifest:
        for c in json.loads(args.manifest.read_text())["clips"]:
            manifest[c["rel_path"]] = c

    # An upload may only ever target the released dataset from the released video tree.
    if args.upload and videos_root != GENERATED_VIDS_DIR.resolve():
        raise SystemExit(
            f"refusing to upload: --videos-root is {videos_root}, not the released "
            f"{GENERATED_VIDS_DIR}. Experimental trajectories must not overwrite the "
            f"published dataset."
        )

    print(f"repo root:          {REPO_ROOT}")
    print(f"framework:          {COSMOS3_REPO}")
    print(f"videos root:        {videos_root}")
    print(f"prompts root:       {prompts_root}")
    print(f"work dir:           {WORK_DIR}")
    print(f"write in-place txt: {args.write_inplace_txt}    upload: {args.upload}")

    records = discover_videos(videos_root)
    if manifest:
        records = [r for r in records if r["rel_path"].as_posix() in manifest]
    if args.limit:
        records = records[: args.limit]
    print(f"found {len(records)} video(s)")

    # Resumable: only run inference for videos lacking a prior prediction.
    pending = [r for r in records if not output_path_for(r["name"]).exists()]
    if pending:
        build_spec(pending)
        run_inference()
    else:
        print("all predictions already present; skipping inference")

    api = None
    if args.upload:
        api = HfApi(token=os.environ.get("HF_TOKEN") or None)
        api.create_repo(HF_DATASET_REPO, repo_type="dataset", exist_ok=True)

    raw_fh = None
    if args.raw_out:
        args.raw_out.parent.mkdir(parents=True, exist_ok=True)
        raw_fh = open(args.raw_out, "w", encoding="utf-8")

    flags: list[str] = []
    upload_ops: list[CommitOperationAdd] = []
    for rec in records:
        name, rel, video_path = rec["name"], rec["rel_path"], rec["video_path"]
        out_json = output_path_for(name)
        if not out_json.exists():
            msg = f"FLAG  {rel}: no prediction output ({out_json})"
            print(msg)
            flags.append(msg)
            continue

        outputs = json.loads(out_json.read_text())
        action = outputs["outputs"][0]["content"]["action"]  # [T-1, 9]

        # True input rate and real frame count come from the resample manifest;
        # without it fall back to the historical (incorrect) assumption.
        info = manifest.get(rel.as_posix(), {})
        hz = float(info.get("out_fps", FPS))
        n_valid = info.get("out_frames")
        seq, seq_native, init_v, poses = action_to_sequence(action, hz, n_valid)
        if not seq or not seq_native:
            msg = f"FLAG  {rel}: action too short to derive a sequence"
            print(msg)
            flags.append(msg)
            continue

        if raw_fh is not None:
            # Persisting poses is what makes every other trajectory variant free:
            # pose_rel_to_abs lives in the framework and is unavailable off this box.
            raw_fh.write(json.dumps({
                "rel_path": rel.as_posix(), "name": name,
                "action": [[round(x, 6) for x in row] for row in action],
                "poses": [[round(x, 6) for x in r] for r in poses.reshape(len(poses), -1)],
                "n_valid_steps": (min(len(seq_native), n_valid - 1)
                                  if n_valid else len(seq_native)),
                "input_fps": hz,
                "src_frames": info.get("src_frames"),
                "out_frames": n_valid,
                "translation_scale": 1.35,
                "checkpoint": CHECKPOINT,
            }) + "\n")
            raw_fh.flush()

        txt_path = video_path.with_suffix(".txt")
        txt_native_path = video_path.with_name(f"{video_path.stem}_{FPS}fps.txt")
        if args.write_inplace_txt:
            txt_path.write_text(json.dumps(seq) + "\n")
            txt_native_path.write_text(json.dumps(seq_native) + "\n")

        # Validate against the prompt's last sentence.
        sentence = prompt_sentence_for(rel, prompts_root)
        stats = evaluate_sequence(seq_native)
        start_v, end_v = stats["start_v"], stats["end_v"]
        max_heading = stats["max_abs_heading"]
        if sentence is None:
            line = (f"NOTE  {rel}: no matching prompt sentence; "
                    f"init_v={init_v:.1f} start_v={start_v:.1f} end_v={end_v:.1f} "
                    f"max|heading|={max_heading:.1f}deg")
            print(line)
        else:
            expected = classify_expected(sentence)
            if expected["speed"] is None and not expected["steer"]:
                line = (f"NOTE  {rel}: unclassified prompt; "
                        f"init_v={init_v:.1f} start_v={start_v:.1f} end_v={end_v:.1f} "
                        f"max|heading|={max_heading:.1f}deg :: \"{sentence}\"")
                print(line)
            else:
                ok, reasons = check_match(expected, stats)
                tag = "MATCH" if ok else "FLAG "
                exp_str = expected["speed"] or "-"
                if expected["steer"]:
                    exp_str += "+steer"
                line = (f"{tag} {rel}: expected={exp_str} "
                        f"init_v={init_v:.1f} start_v={start_v:.1f} end_v={end_v:.1f} "
                        f"max|heading|={max_heading:.1f}deg")
                if not ok:
                    line += " | " + "; ".join(reasons) + f" :: \"{sentence}\""
                    flags.append(line)
                print(line)

        # Queue both .txt files for a single end-of-run commit (mirrored paths).
        if args.upload:
            upload_ops.append(CommitOperationAdd(
                path_in_repo=rel.with_suffix(".txt").as_posix(),
                path_or_fileobj=str(txt_path),
            ))
            upload_ops.append(CommitOperationAdd(
                path_in_repo=rel.with_name(f"{rel.stem}_{FPS}fps.txt").as_posix(),
                path_or_fileobj=str(txt_native_path),
            ))

    if raw_fh is not None:
        raw_fh.close()
        print(f"\nwrote raw poses/actions: {args.raw_out}")

    summary_path = (WORK_DIR / "inverse_dynamics_flags.txt" if not args.write_inplace_txt
                    else GENERATED_VIDS_DIR / "inverse_dynamics_flags.txt")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    header = (f"Inverse-dynamics validation flags ({len(flags)} issue(s))\n"
              f"Heuristic, language-based comparison of the action-sequence tail "
              f"vs the last sentence of each prompt.\n\n")
    summary_path.write_text(header + ("\n".join(flags) + "\n" if flags else "(no flags)\n"))
    print(f"\nwrote summary: {summary_path}")

    if not args.upload:
        print(f"done. {len(flags)} flag(s). (upload disabled; pass --upload to publish)")
        return

    upload_ops.append(CommitOperationAdd(
        path_in_repo=summary_path.name,
        path_or_fileobj=str(summary_path),
    ))
    print(f"\nuploading {len(upload_ops)} file(s) in one commit to {HF_DATASET_REPO}@{HF_REVISION}...")
    try:
        api.create_commit(
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            revision=HF_REVISION,
            operations=upload_ops,
            commit_message=f"Add {len(upload_ops)} inverse-dynamics action sequences and flags",
        )
        print(f"uploaded {len(upload_ops)} file(s) -> {HF_DATASET_REPO}@{HF_REVISION}")
    except Exception as exc:  # noqa: BLE001 - surface upload errors
        msg = f"FLAG  batch upload failed: {exc}"
        print(msg)
        flags.append(msg)
        summary_path.write_text(header + ("\n".join(flags) + "\n" if flags else "(no flags)\n"))

    print(f"done. {len(flags)} flag(s).")


if __name__ == "__main__":
    main()
