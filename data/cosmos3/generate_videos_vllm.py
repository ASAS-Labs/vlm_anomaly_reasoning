"""generate_videos_vllm.py - Cosmos3 text-to-video generation via vLLM Omni.

Same job as generate_videos_diffusers.py (5s / 480p videos, no audio, for every
structured JSON prompt under data/cosmos3/video_gen_prompts/, written to
data/datasets/generated_vids/ and uploaded to a Hugging Face dataset repo), but
instead of loading a Diffusers pipeline in-process it serves the model with
vLLM Omni and drives it over HTTP, mirroring run_with_vllm_omni.ipynb.

The script launches its own vLLM Omni server on a single GPU
(`--tensor-parallel-size 1`), waits for it to come up, runs every prompt
against the `/v1/videos/sync` endpoint, then shuts the server down on exit.

Environment: a vLLM Omni Docker container. `vllm` ships with the image and is
already on PATH

Setup (run once):

    uv sync                # install Python deps into .venv from uv.lock

Run (from the repo root):

    export HF_TOKEN=<your read/write HF Token>
    uv run python data/cosmos3/generate_videos_vllm.py

Switch models by editing MODEL_ID below (Cosmos3-Super by default).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

# Avoid the Xet hub backend. Must be set before importing huggingface_hub.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from huggingface_hub import HfApi

# --- Configuration (the only things you should need to change) -----------
MODEL_ID = "nvidia/Cosmos3-Nano"  # change to "nvidia/Cosmos3-Nano" for Nano
HF_DATASET_REPO = "danieladejumo/av_semantic_anomalies"

TENSOR_PARALLEL_SIZE = 1
SERVER_PORT = 8000
SERVER_BASE_URL = f"http://localhost:{SERVER_PORT}"
SERVER_STARTUP_TIMEOUT = 1800  # seconds to wait for the model to load

SCRIPT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = SCRIPT_DIR / "video_gen_prompts"
OUTPUT_DIR = SCRIPT_DIR.parent / "datasets" / "generated_vids"
NEGATIVE_PROMPT_FILE = SCRIPT_DIR / "text2video_neg_prompt.json"

# 5s of video. Video diffusion expects a 4n+1 frame count, so 121 -> ~5.04s @ 24fps.
NUM_FRAMES = 193 # 8s
FPS = 24
HEIGHT = 480
WIDTH = 832

NUM_STEPS = 35
GUIDANCE = 6.0
SHIFT = 10.0
SEED = 1234


def compact_json(path: Path) -> str:
    """Load a structured JSON file and serialize it compactly (as the notebook does)."""
    return json.dumps(json.loads(path.read_text()), ensure_ascii=True, separators=(",", ":"))


# Structured negative prompt, matching the notebook's text2video negative prompt.
NEGATIVE_PROMPT = compact_json(NEGATIVE_PROMPT_FILE)

# Per-request flags sent to vLLM Omni. Templates are disabled to match the Diffusers
# script, and guardrails are disabled for video generation.
EXTRA_PARAMS = json.dumps(
    {
        "use_resolution_template": False,
        "use_duration_template": True,
        "guardrails": False,
    },
    separators=(",", ":"),
)


def start_server() -> subprocess.Popen:
    """Launch the vLLM Omni server (tensor-parallel size from TENSOR_PARALLEL_SIZE)."""
    cmd = [
        "vllm",
        "serve",
        MODEL_ID,
        "--omni",
        "--model-class-name",
        "Cosmos3OmniDiffusersPipeline",
        "--allowed-local-media-path",
        "/",
        "--tensor-parallel-size",
        str(TENSOR_PARALLEL_SIZE),
        "--port",
        str(SERVER_PORT),
        "--init-timeout",
        str(SERVER_STARTUP_TIMEOUT),
    ]
    print(f"starting vLLM server: {' '.join(cmd)}")
    # New session so we can signal the whole process group (TP spawns worker procs).
    return subprocess.Popen(cmd, start_new_session=True)


def wait_for_server(proc: subprocess.Popen) -> None:
    """Poll the models endpoint until the server is ready (or the process dies)."""
    url = f"{SERVER_BASE_URL}/v1/models"
    deadline = time.time() + SERVER_STARTUP_TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"vLLM server exited early with code {proc.returncode}")
        ready = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", url],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if ready.stdout.strip() == "200":
            print("vLLM server is ready.")
            return
        time.sleep(5)
    raise TimeoutError(f"vLLM server not ready after {SERVER_STARTUP_TIMEOUT}s")


def stop_server(proc: subprocess.Popen) -> None:
    """Terminate the server and its tensor-parallel worker processes."""
    if proc.poll() is not None:
        return
    print("stopping vLLM server ...")
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def generate_video(prompt_text: str, out_path: Path) -> None:
    """POST one text2video request to /v1/videos/sync and write the MP4 to out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    form = {
        "prompt": prompt_text,
        "negative_prompt": NEGATIVE_PROMPT,
        "size": f"{WIDTH}x{HEIGHT}",
        "num_frames": str(NUM_FRAMES),
        "fps": str(FPS),
        "num_inference_steps": str(NUM_STEPS),
        "guidance_scale": str(GUIDANCE),
        "flow_shift": str(SHIFT),
        "seed": str(SEED),
        "extra_params": EXTRA_PARAMS,
    }

    cmd = [
        "curl",
        "-sS",
        "--fail-with-body",
        "-X",
        "POST",
        f"{SERVER_BASE_URL}/v1/videos/sync",
        "-H",
        "Accept: video/mp4",
    ]
    for key, value in form.items():
        cmd += ["--form-string", f"{key}={value}"]
    cmd += ["-o", str(tmp_path)]

    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(
            f"vLLM request failed (exit {result.returncode}): {result.stdout}{result.stderr}"
        )
    tmp_path.replace(out_path)


def upload_video(api: HfApi, local_path: Path, path_in_repo: str) -> None:
    api.upload_file(
        path_or_fileobj=str(local_path),
        path_in_repo=path_in_repo,
        repo_id=HF_DATASET_REPO,
        repo_type="dataset",
    )
    print(f"  uploaded -> {HF_DATASET_REPO}:{path_in_repo}")


def main() -> None:
    prompt_paths = sorted(PROMPTS_DIR.rglob("*.json"))
    if not prompt_paths:
        raise SystemExit(f"No JSON prompts found under {PROMPTS_DIR}")
    print(f"found {len(prompt_paths)} prompt(s) under {PROMPTS_DIR}")

    api = HfApi(token=os.environ.get("HF_TOKEN") or None)
    api.create_repo(HF_DATASET_REPO, repo_type="dataset", exist_ok=True)

    server = start_server()
    try:
        wait_for_server(server)

        uploads: list[Future] = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            for prompt_path in prompt_paths:
                rel_mp4 = prompt_path.relative_to(PROMPTS_DIR).with_suffix(".mp4")
                out_path = OUTPUT_DIR / rel_mp4
                if out_path.exists():
                    print(f"skip (exists): {rel_mp4}")
                    continue

                prompt_text = compact_json(prompt_path)
                print(f"generating {rel_mp4} ...")
                t0 = time.time()
                generate_video(prompt_text, out_path)
                print(f"  generated in {time.time() - t0:.1f}s -> {out_path}")

                # Upload in the background so the next video starts generating immediately.
                uploads.append(pool.submit(upload_video, api, out_path, rel_mp4.as_posix()))

            # Wait for all uploads to finish (and surface any errors) before exiting.
            print("waiting for pending uploads ...")
            for fut in uploads:
                fut.result()
    finally:
        stop_server(server)

    print("done.")


if __name__ == "__main__":
    main()
