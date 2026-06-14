# VLM Anomaly Reasoning

## Table of Contents
- [Installation](#installation)
- [Synthetic Data Generation with Cosmos3]()

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