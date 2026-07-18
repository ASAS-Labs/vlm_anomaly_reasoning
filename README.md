# VLM Anomaly Reasoning

## Table of Contents
- [Installation](#installation)
- [Synthetic Data Generation with Cosmos3](#synthetic-data-generation-with-cosmos3)
  - [Prompt Upsampling](#prompt-upsampling)
  - [Cosmos3 Video Generation](#cosmos3-video-generation)
  - [Inverse Dynamics](#inverse-dynamics)
  - [Inverse Dynamics Manual Validation (GUI)](#inverse-dynamics-manual-validation-gui)

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
generates a 5s, 720p (1280×720), 24fps MP4 — no audio — for every structured JSON
prompt under `data/cosmos3/video_gen_prompts/`. It launches a vLLM Omni server,
drives it over HTTP (`/v1/videos/sync`), writes each video to
`data/datasets/generated_vids/`, and uploads it to the Hugging Face dataset repo
(`HF_DATASET_REPO` in the script). Videos that already exist locally are skipped.

**1. Run inside the vLLM Omni container.** The `vllm` CLI and the Omni runtime
ship in the `vllm/vllm-omni:cosmos3` image — they are *not* installed by `uv sync`
(which only provides the script's Python deps, e.g. `huggingface_hub`). Start the
container with the repo mounted, your GPUs exposed, and `HF_TOKEN` passed in (see
[Hugging Face access](#hugging-face-access)):
```bash
docker run --gpus all -it --rm \
  -v "$PWD":/workspace -w /workspace \
  --env-file .env \
  vllm/vllm-omni:cosmos3 bash

# inside the container:
uv sync
uv run python data/cosmos3/generate_videos_vllm.py
```

**2. Pick the model and matching GPU count.** Set both `MODEL_ID` and
`TENSOR_PARALLEL_SIZE` near the top of the script. The model is served with one
GPU per tensor-parallel rank, so the container must expose at least
`TENSOR_PARALLEL_SIZE` GPUs — a mismatch fails at server startup.

| Model                  | GPUs | `TENSOR_PARALLEL_SIZE` |
| ---------------------- | ---- | ---------------------- |
| `nvidia/Cosmos3-Nano`  | 1    | `1`                    |
| `nvidia/Cosmos3-Super` | 4    | `4` (default)          |

The first run downloads the gated Cosmos3 weights (tens of GB) into the Hugging
Face cache, so model load can take several minutes.

### Inverse Dynamics

[`data/cosmos3/run_inverse_dynamics.py`](data/cosmos3/run_inverse_dynamics.py)
runs Cosmos3-Nano **action inverse-dynamics** over every MP4 under
`data/datasets/generated_vids/`. For each video it:

1. Predicts an ego-motion action trajectory (`[T-1, 9]` = translation + rot6d).
2. Converts relative poses to absolute camera-to-world poses (metric meters with
   the cookbook `translation_scale`).
3. Derives `[[velocity_mph, heading_deg], ...]` at the native model rate (**10 Hz**)
   and a downsampled rate (**5 Hz**). Heading is degrees relative to the first
   frame.
4. Heuristically checks the trajectory tail against the last sentence of the
   matching prompt line (mirrored tree under `data/cosmos3/video_gen_prompts/`).
5. Writes `<video>.txt` (5 Hz) and `<video>_10fps.txt` (10 Hz) next to each MP4,
   and uploads those text files to the Hugging Face dataset repo (`reorg` branch).

**1. One-time setup** — populates the `packages/cosmos-framework` submodule and
installs its train/CUDA env (default `cu130-train`):
```bash
./setup_inverse_dynamics.sh
export HF_TOKEN=<write token with gated-model + dataset access>
```
Override the CUDA uv group if needed, e.g.
`COSMOS3_UV_GROUP=cu128-train ./setup_inverse_dynamics.sh`.

**2. Ensure videos are present** under `data/datasets/generated_vids/` (generate
locally or sync from the HF dataset, revision `reorg`).

**3. Run** (any interpreter; the script re-execs into the framework venv):
```bash
python data/cosmos3/run_inverse_dynamics.py
# optional: override the prompts tree
PROMPTS_ROOT=/path/to/video_gen_prompts python data/cosmos3/run_inverse_dynamics.py
```

**Outputs (per video):**

| File | Contents |
| --- | --- |
| `<stem>.txt` | Downsampled sequence at 5 Hz: `[[v_mph, heading_deg], ...]` |
| `<stem>_10fps.txt` | Native-rate sequence at 10 Hz (same format) |
| `inverse_dynamics_flags.txt` | Heuristic mismatches vs the prompt’s last sentence |

**Example plots** (velocity / heading over time). Drop screenshots into
`docs/images/` using the filenames below:

![Example: ego velocity (mph) vs time](docs/images/inverse_dynamics_velocity_example.png)

*Placeholder — save a velocity trajectory plot to
`docs/images/inverse_dynamics_velocity_example.png`.*

![Example: ego heading (deg) vs time](docs/images/inverse_dynamics_heading_example.png)

*Placeholder — save a heading trajectory plot to
`docs/images/inverse_dynamics_heading_example.png`.*

![Example: video frame alongside synced trajectory cursor](docs/images/inverse_dynamics_synced_plot_example.png)

*Placeholder — save a side-by-side video + real-time plot screenshot to
`docs/images/inverse_dynamics_synced_plot_example.png`.*

### Inverse Dynamics Manual Validation (GUI)

After running inverse dynamics, validate trajectories manually with the Streamlit
app under [`data/cosmos3/data_validation/`](data/cosmos3/data_validation/):

```bash
uv sync --group validation
uv run --group validation streamlit run data/cosmos3/data_validation/app.py
```

See [`data/cosmos3/data_validation/README.md`](data/cosmos3/data_validation/README.md)
for CSV columns and usage details.