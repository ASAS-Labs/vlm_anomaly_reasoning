# VLM Anomaly Reasoning

## Table of Contents
- [Installation](#installation)
- [Synthetic Data Generation with Cosmos3](#synthetic-data-generation-with-cosmos3)
  - [Prompt Upsampling](#prompt-upsampling)
  - [Cosmos3 Video Generation](#cosmos3-video-generation)

## Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) — manages Python 3.13 and all dependencies.
- `git`
- An NVIDIA Blackwell GPU for video generation — the pinned PyTorch build uses the CUDA 13.0 (`cu130`) wheels. Linting and other development work run on any machine.

### Setup
```bash
git clone https://github.com/ASAS-Labs/vlm_anomaly_reasoning.git
cd vlm_anomaly_reasoning

# System graphics libraries (headless servers) + git hooks (pre-push ruff lint).
./setup.sh

# Create the virtualenv and install the pinned dependencies from uv.lock.
uv sync
```

`uv sync` pulls a multi-GB `torch+cu130` build, so the first run takes a while.

### Hugging Face access
The Cosmos scripts downloads gated Cosmos3 weights and uploads results to a Hugging Face
dataset repo, so a *write* token is required:
```bash
export HF_TOKEN=<token with read/write access to the gated model and the dataset repo>
```
Alternatively, set it in the `.env` file (loaded via `uv run --env-file .env ...`).

## Synthetic Data Generation with Cosmos3

### Prompt Upsampling

Expands short text prompts into structured Cosmos3 JSON prompts using an LLM. The
upsampler ships in the `cosmos-framework` submodule and only calls an
OpenAI-compatible chat endpoint, so it runs in an isolated `uv` env (just
`requests`) — no torch or heavy install needed.

**1. Fetch the submodule** (the upsampler lives in `packages/cosmos-framework`):
```bash
git submodule update --init packages/cosmos-framework
```
A fresh checkout can instead clone everything at once with
`git clone --recurse-submodules https://github.com/ASAS-Labs/vlm_anomaly_reasoning.git`.

**2. Configure the endpoint and API key.** The endpoint and model are set at the
top of [`data/cosmos3/upsample_prompts.sh`](data/cosmos3/upsample_prompts.sh)
(`PROMPT_UPSAMPLER_ENDPOINT_URL`, `PROMPT_UPSAMPLER_MODEL_NAME`). Put the matching
API key in a gitignored `.env` at the repo root — the script sources it
automatically:
```bash
# .env (repo root)
PROMPT_UPSAMPLER_API_TOKEN=<api key for the configured endpoint>
```
The script aborts with a clear message if `PROMPT_UPSAMPLER_API_TOKEN` is unset.

**3. Provide input prompts.** Create a text file with one prompt per non-empty
line (default `data/cosmos3/prompts.txt`).

**4. Run:**
```bash
./data/cosmos3/upsample_prompts.sh [INPUT_TXT] [OUTPUT_DIR]
```
Defaults read `data/cosmos3/prompts.txt` and write one JSON file per prompt to
`data/cosmos3/video_gen_prompts/`. After upsampling, the script automatically
unwraps and pretty-prints the generated JSON (via `prettify_prompts.py`), leaving
clean Cosmos3 prompt objects ready for video generation.

### Cosmos3 Video Generation

[`data/cosmos3/generate_videos_vllm.py`](data/cosmos3/generate_videos_vllm.py)
generates a 5s / 720p video (no audio) for every structured JSON prompt under
`data/cosmos3/video_gen_prompts/`, writes the MP4s to
`data/datasets/generated_vids/` (mirroring the prompt folder layout), and uploads
each one to a Hugging Face dataset repo. It launches its own vLLM-Omni server
(tensor-parallel across 4 GPUs), drives it over HTTP, then shuts it down on exit.
Existing outputs are skipped, so re-running resumes where it left off.

This backend uses **vLLM-Omni**, which upstream ships only as the
`vllm/vllm-omni:cosmos3` Docker image. That image is not usable in an unprivileged
container (no Docker-in-Docker), and a native install conflicts with the main
project env (vLLM-Omni pins `diffusers==0.38.0` vs the git `diffusers` used by the
Diffusers backend). So it gets its **own** virtualenv, `.venv-vllm`, separate from
the `uv sync` env above.

**1. Build the vLLM backend env** (run once):
```bash
./setup_vllm.sh                      # creates .venv-vllm with the vllm CLI + vllm-omni plugin
source .venv-vllm/bin/activate
```
`setup_vllm.sh` installs `vllm==0.22.0` (the engine), the `vllm-omni` plugin (which
adds `--omni` / `Cosmos3OmniDiffusersPipeline`), `huggingface-hub`, and
`audioop-lts` (backports the `audioop` stdlib module Python 3.13 removed). It
pulls a multi-GB `torch+cu130` build, so the first run takes a while. For a CUDA
12.8 driver, run `TORCH_BACKEND=cu128 ./setup_vllm.sh` instead.

**2. Set the Hugging Face token** (see [Hugging Face access](#hugging-face-access)):
```bash
export HF_TOKEN=<token with read/write access to the gated model and the dataset repo>
```

**3. Run:**
```bash
python data/cosmos3/generate_videos_vllm.py
```

**Configuration** lives at the top of the script:
- `MODEL_ID` — `nvidia/Cosmos3-Nano` (16B, default) or `nvidia/Cosmos3-Super` (64B).
  Super automatically adds `--enable-layerwise-offload` to fit in GPU memory.
- `HF_DATASET_REPO` — the dataset repo results are uploaded to.

**Requirements:** 4 NVIDIA GPUs (for `--tensor-parallel-size 4`) and enough disk
for the gated weights (Nano ≈ 30 GB, Super ≈ 100 GB+).