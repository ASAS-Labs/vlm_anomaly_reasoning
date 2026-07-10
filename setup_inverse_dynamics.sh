#!/usr/bin/env bash
# Set up the Cosmos Framework environment for action inverse-dynamics inference.
# 
# This mirrors steps 3-4 of run_id_with_cosmos_framework.ipynb against this
# repo's layout: it populates the packages/cosmos-framework git submodule and
# installs its dependencies into a uv-managed virtual environment (.venv inside
# the submodule). It also ensures huggingface_hub is available in that venv for
# the action-file upload step.
#
# Usage:
#   ./setup_inverse_dynamics.sh
#
# Override any default by exporting the variable before running, e.g.:
#   COSMOS3_UV_GROUP=cu128-train ./setup_inverse_dynamics.sh   # CUDA 12.x driver

set -euo pipefail

# Repo root: this script lives at the root; walk up to .git just in case.
find_repo_root() {
  local dir
  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [[ "${dir}" != "/" ]]; do
    if [[ -e "${dir}/.git" ]]; then
      printf '%s\n' "${dir}"
      return 0
    fi
    dir="$(dirname "${dir}")"
  done
  printf '%s\n' "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
}

REPO_ROOT="$(find_repo_root)"

# Environment variables (existing values win).
export COSMOS3_REPO="${COSMOS3_REPO:-${REPO_ROOT}/packages/cosmos-framework}"
export COSMOS3_UV_GROUP="${COSMOS3_UV_GROUP:-cu130-train}"

echo "REPO_ROOT:        ${REPO_ROOT}"
echo "COSMOS3_REPO:     ${COSMOS3_REPO}"
echo "COSMOS3_UV_GROUP: ${COSMOS3_UV_GROUP}"
if [[ -n "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN: <set>"
else
  echo "HF_TOKEN: <unset> (required for gated nvidia/Cosmos3-Nano download and dataset upload)"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it first: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

# 1. Populate (or reuse) the cosmos-framework submodule.
if [[ -f "${COSMOS3_REPO}/pyproject.toml" ]]; then
  echo "Using existing framework checkout: ${COSMOS3_REPO}"
else
  echo "Initializing cosmos-framework submodule"
  git -C "${REPO_ROOT}" submodule update --init packages/cosmos-framework
  if [[ ! -f "${COSMOS3_REPO}/pyproject.toml" ]]; then
    echo "Framework source not found at ${COSMOS3_REPO} after submodule init." >&2
    exit 1
  fi
fi

# 2. Install dependencies (heavier "train" group, matching the notebook audit).
export GIT_LFS_SKIP_SMUDGE=1
cd "${COSMOS3_REPO}"
echo "Installing Cosmos Framework dependencies (uv group: ${COSMOS3_UV_GROUP})"
uv sync --all-extras --group="${COSMOS3_UV_GROUP}"

# 3. Ensure huggingface_hub is available in the framework venv (used by the
#    run script to upload action files). It is usually pulled in transitively,
#    but install it explicitly to be safe.
if ! "${COSMOS3_REPO}/.venv/bin/python" -c "import huggingface_hub" >/dev/null 2>&1; then
  echo "Installing huggingface_hub into the framework venv"
  uv pip install huggingface_hub
fi

echo
echo "Installed Cosmos Framework into: ${COSMOS3_REPO}"
echo "Run inverse dynamics with:"
echo "  HF_TOKEN=<token> ${COSMOS3_REPO}/.venv/bin/python ${REPO_ROOT}/data/cosmos3/run_inverse_dynamics.py"
