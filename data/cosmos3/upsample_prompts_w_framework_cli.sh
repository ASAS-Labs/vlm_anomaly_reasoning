#!/bin/bash
# Upsample raw text prompts into Cosmos3 JSON prompts using the vendored
# cosmos-framework repo (packages/cosmos-framework).
#
# The upsampler just calls an OpenAI-compatible LLM endpoint, so it runs in an
# isolated uv env with only `requests` - no torch / heavy framework install.
#
# Usage:
#   ./upsample_prompts.sh [INPUT_TXT] [OUTPUT_DIR]
# Defaults read prompts from data/cosmos3/prompts.txt and write JSON prompts to
# data/cosmos3/video_gen_prompts/. Requires PROMPT_UPSAMPLER_API_TOKEN (in .env).
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
FRAMEWORK_DIR="${REPO_ROOT}/packages/cosmos-framework"

# Load PROMPT_UPSAMPLER_API_TOKEN (and other secrets) from .env if present.
if [[ -f "${REPO_ROOT}/.env" ]]; then
  set -a; . "${REPO_ROOT}/.env"; set +a
fi

export PROMPT_UPSAMPLER_ENDPOINT_URL="https://api.anthropic.com/v1/"
export PROMPT_UPSAMPLER_MODEL_NAME="claude-opus-4-6"
: "${PROMPT_UPSAMPLER_API_TOKEN:?Set PROMPT_UPSAMPLER_API_TOKEN in .env}"

INPUT="${1:-${REPO_ROOT}/data/cosmos3/prompts.txt}"
OUTPUT="${2:-${REPO_ROOT}/data/cosmos3/video_gen_prompts}"

PYTHONPATH="${FRAMEWORK_DIR}" uv run --no-project --with requests \
  python -m cosmos_framework.inference.prompt_upsampling \
  --input "${INPUT}" \
  --output "${OUTPUT}" \
  --mode text2video \
  --endpoint-url "${PROMPT_UPSAMPLER_ENDPOINT_URL}" \
  --model "${PROMPT_UPSAMPLER_MODEL_NAME}" \
  --api-token "${PROMPT_UPSAMPLER_API_TOKEN}" \
  --resolution 720 \
  --aspect-ratio "16,9"

# Unwrap the {"prompt": ...} wrapper and pretty-print the generated JSON prompts.
uv run --no-project python "${REPO_ROOT}/data/cosmos3/prettify_prompts.py" "${OUTPUT}"

