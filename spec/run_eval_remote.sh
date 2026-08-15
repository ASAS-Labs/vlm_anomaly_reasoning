#!/usr/bin/env bash
# Drive the full anomaly-reasoning evaluation on a single-GPU box (H200).
#
# Idempotent: safe to re-run after a crash or a killed instance. Setup steps skip
# when already done, and the eval itself resumes from results.jsonl.
#
# Usage (inside tmux, so an SSH drop does not kill the run):
#   tmux new -s eval
#   export HF_TOKEN=<token>
#   bash spec/run_eval_remote.sh --smoke     # 8 videos x 2 modes, cheap gate
#   bash spec/run_eval_remote.sh             # full 315 x 2 modes

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV_DIR:-${REPO_ROOT}/.venv}"
PY="${VENV}/bin/python"
PORT="${PORT:-8000}"
DATASET="${REPO_ROOT}/data/datasets/generated_vids"

SMOKE=0
EXP="full"
LIMIT_ARGS=()
if [[ "${1:-}" == "--smoke" ]]; then
  SMOKE=1
  EXP="smoke"
  LIMIT_ARGS=(--limit 8 --sample balanced)
fi

echo "=== 1/6 environment ==="
bash "${REPO_ROOT}/spec/setup_reasoner.sh"

echo "=== 2/6 dataset ==="
"${PY}" "${REPO_ROOT}/data/cosmos3/fetch_eval_dataset.py"

echo "=== 3/6 model weights (before the GPU clock matters) ==="
HF_HUB_ENABLE_HF_TRANSFER=1 "${VENV}/bin/hf" download nvidia/Cosmos3-Nano >/dev/null

echo "=== 4/6 preflight ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
"${VENV}/bin/vllm" --version
"${PY}" -c "import vllm_cosmos3, transformers_cosmos3; print('cosmos3 vllm/transformers ok')"
# --async-scheduling is passed unconditionally by the runner; fail now if unsupported.
"${VENV}/bin/vllm" serve --help 2>/dev/null | grep -q -- "--async-scheduling" \
  || { echo "ERROR: this vllm build lacks --async-scheduling" >&2; exit 1; }

echo "=== 5/6 starting vLLM server (one load serves both modes) ==="
LOG_DIR="${REPO_ROOT}/logs"
mkdir -p "${LOG_DIR}"
"${VENV}/bin/vllm" serve nvidia/Cosmos3-Nano \
  --hf-overrides '{"architectures": ["Cosmos3ReasonerForConditionalGeneration"]}' \
  --async-scheduling \
  --allowed-local-media-path / \
  --media-io-kwargs '{"video": {"fps": 4, "num_frames": -1}}' \
  --tensor-parallel-size 1 \
  --port "${PORT}" > "${LOG_DIR}/vllm_server.log" 2>&1 &
SERVER_PID=$!
trap 'echo "stopping server"; kill -TERM -"$(ps -o pgid= ${SERVER_PID} | tr -d " ")" 2>/dev/null || kill ${SERVER_PID} 2>/dev/null || true' EXIT

echo "waiting for server (pid ${SERVER_PID})..."
for _ in $(seq 1 900); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo "server ready"; break
  fi
  kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/vllm_server.log" >&2; exit 1; }
  sleep 2
done

echo "=== 6/6 inference ==="
cd "${REPO_ROOT}/data/cosmos3"   # flat `from utils import ...` requires this CWD
for MODE in no_action_grounding action_grounding; do
  echo "--- ${MODE} ---"
  "${PY}" cosmos_reasoning_vllm.py \
    --dataset "${DATASET}" \
    --exp_name "${EXP}" \
    --mode "${MODE}" \
    --server_url "http://127.0.0.1:${PORT}/v1" \
    "${LIMIT_ARGS[@]}"
done

if [[ "${SMOKE}" == "1" ]]; then
  echo
  echo "=== smoke gates ==="
  "${PY}" reparse_results.py "${REPO_ROOT}/logs/smoke_"*/results.jsonl --check --histogram
  echo "Gates passed. Re-run without --smoke for the full 315 x 2."
fi
