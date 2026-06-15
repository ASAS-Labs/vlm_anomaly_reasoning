#!/usr/bin/env bash
# Set up a dedicated virtualenv for the vLLM-Omni video generation backend
# (data/cosmos3/generate_videos_vllm.py).
#
# vLLM-Omni pins diffusers==0.38.0, which conflicts with the git diffusers the
# main project env uses for the Diffusers backend (Cosmos3OmniPipeline lives in
# git diffusers only). So this backend gets its own venv, matching upstream
# cosmos, which installs vllm-omni into a separate environment.
#
# Usage:
#   ./setup_vllm.sh                      # creates .venv-vllm with the `vllm` CLI
#   source .venv-vllm/bin/activate
#   export HF_TOKEN=<token with access to the gated model and the dataset repo>
#   python data/cosmos3/generate_videos_vllm.py
#
# Pair the torch CUDA backend with the GPU driver: cu130 for CUDA 13 (default),
# cu128 for CUDA 12.8. Override with TORCH_BACKEND=cu128 ./setup_vllm.sh

set -euo pipefail

VENV=".venv-vllm"
TORCH_BACKEND="${TORCH_BACKEND:-cu130}"

# vllm-omni is a *plugin* that adds --omni / Cosmos3OmniDiffusersPipeline to the
# vllm CLI via vllm's general_plugins hook; it does NOT bundle vllm itself. The
# vllm/vllm-omni:cosmos3 Docker image has vllm baked in, but that route is not
# usable here (unprivileged container, no Docker-in-Docker), so we install both
# the vllm engine and the plugin into a venv.
#
# Pinned to the Cosmos3 generator PR the cookbook uses
# (packages/cosmos/.../run_with_vllm_omni.ipynb). VLLM_VERSION matches that PR's
# Docker base image (vllm/vllm-openai:v0.22.0, see its docker/Dockerfile.cuda).
VLLM_VERSION="vllm==0.22.0"
VLLM_OMNI="vllm-omni @ git+https://github.com/vllm-project/vllm-omni.git@refs/pull/3454/head"

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

uv venv "${VENV}" --python 3.13 --seed --managed-python
# huggingface-hub is used directly by the script for dataset upload; vllm pulls
# it transitively too, but install it explicitly to be safe.
#
# audioop-lts backports the `audioop` stdlib module that Python 3.13 removed
# (PEP 594). vllm-omni's startup imports pydub, which needs audioop, so without
# this the `vllm serve` CLI crashes on import under Python 3.13.
uv pip install --python "${VENV}" --torch-backend="${TORCH_BACKEND}" \
  "${VLLM_VERSION}" "${VLLM_OMNI}" huggingface-hub audioop-lts

echo
echo "Done. Activate the vLLM backend env with:"
echo "  source ${VENV}/bin/activate"
echo "Then run: python data/cosmos3/generate_videos_vllm.py"
