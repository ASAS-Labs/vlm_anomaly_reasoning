#!/usr/bin/env bash
# Plugin-free vLLM environment for the open-VLM pilot (family K).
#
# Unlike setup_reasoner.sh this installs NO Cosmos framework packages: the pilot
# models (Qwen3.x, Qwen3-VL, GLM-4.6V, InternVL3.5) are served by stock vLLM.
# Default is the latest stable vLLM (the floor is set by the newest model,
# Qwen3.8-27B, Aug 2026); pin with PILOT_VLLM_VERSION if needed.
#
# Fallback policy: if one model needs a different vLLM than the shared install,
# build it its own venv instead of mutating this one:
#   VENV_DIR=.venv-pilot-<key> PILOT_VLLM_VERSION=<ver> bash spec/setup_pilot.sh
#
# Usage:
#   bash spec/setup_pilot.sh
#   .venv-pilot/bin/vllm --version

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VENV_DIR="${VENV_DIR:-${REPO_ROOT}/.venv-pilot}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${HOME}/.cache/uv}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export HF_HOME="${HF_HOME:-${HOME}/.cache/huggingface}"

echo "VENV_DIR: ${VENV_DIR}"
echo "vLLM: ${PILOT_VLLM_VERSION:-latest}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

# Headless servers need these for video decoding (same set as setup_reasoner.sh).
if command -v apt-get >/dev/null 2>&1; then
  SUDO=""; [[ "${EUID:-$(id -u)}" -ne 0 ]] && SUDO="sudo"
  ${SUDO} apt-get update -y >/dev/null 2>&1 || true
  ${SUDO} apt-get install -y libxcb1 libgl1 libglib2.0-0 ffmpeg >/dev/null 2>&1 || \
    echo "Warning: system lib install failed; install manually if imports fail" >&2
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  uv venv --python 3.13 --seed --managed-python "${VENV_DIR}"
fi

VLLM_SPEC="vllm"
[[ -n "${PILOT_VLLM_VERSION:-}" ]] && VLLM_SPEC="vllm==${PILOT_VLLM_VERSION}"
uv pip install --python "${VENV_DIR}/bin/python" --torch-backend=auto \
  "${VLLM_SPEC}" openai "huggingface_hub[hf_transfer]"

echo
"${VENV_DIR}/bin/vllm" --version
echo "Setup complete. Next:"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/data/cosmos3/fetch_eval_dataset.py"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/data/cosmos3/make_pilot_trees.py \\"
echo "      --subset ${REPO_ROOT}/logs/vlm_agreement_subset_admitted.txt"
echo "  bash ${REPO_ROOT}/spec/run_pilot_model.sh <model_key>"
