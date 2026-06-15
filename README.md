# VLM Anomaly Reasoning

## Table of Contents
- [Installation](#installation)
- [Synthetic Data Generation with Cosmos3](#synthetic-data-generation-with-cosmos3)
  - [Prompt Upsampling](#prompt-upsampling)

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