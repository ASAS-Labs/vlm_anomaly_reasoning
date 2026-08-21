#!/usr/bin/env bash
# Closed-loop regeneration on a vast.ai box running the vllm/vllm-omni:cosmos3
# image (the Cosmos3_vLLM template): serve Cosmos3-Nano video gen, run the
# best-of-N flow-gated generation for logs/regen_targets.json, then the fixed
# inverse-dynamics cross-check (pass 1). Idempotent/resumable.
#
#   tmux new -s regen
#   bash spec/run_regen_remote.sh            # generate + ID pass 1
#   PASS=2 bash spec/run_regen_remote.sh     # after `regen_fix.py generate --more`
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8000}"
PASS="${PASS:-1}"
SKIP_GEN="${SKIP_GEN:-0}"
LOG_DIR="${REPO_ROOT}/logs"
VENV="${REPO_ROOT}/.venv-regen"
export HF_HUB_DISABLE_XET=1
cd "${REPO_ROOT}/data/cosmos3"

if [[ ! -x "${VENV}/bin/python" ]]; then
  uv venv -q --python 3.13 --seed "${VENV}"
  uv pip install -q --python "${VENV}/bin/python" numpy opencv-python-headless
fi
PY="${VENV}/bin/python"

if [[ "${SKIP_GEN}" != "1" ]]; then
  echo "--- serve Cosmos3-Nano (omni) ---"
  setsid vllm serve nvidia/Cosmos3-Nano --omni \
    --model-class-name Cosmos3OmniDiffusersPipeline \
    --allowed-local-media-path / --tensor-parallel-size 1 \
    --port "${PORT}" --init-timeout 1800 \
    > "${LOG_DIR}/regen_server.log" 2>&1 &
  SERVER_PID=$!
  trap 'echo "stopping server"; kill -TERM -"${SERVER_PID}" 2>/dev/null || true' EXIT
  for _ in $(seq 1 900); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/v1/models" || true)"
    [[ "${code}" == "200" ]] && { echo "server ready"; break; }
    kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/regen_server.log" >&2; exit 1; }
    sleep 2
  done
  echo "--- generate (best-of-N, flow-probe gate) ---"
  if [[ "${PASS}" == "1" ]]; then
    "${PY}" regen_fix.py generate --server-url "http://127.0.0.1:${PORT}"
  else
    "${PY}" regen_fix.py generate --server-url "http://127.0.0.1:${PORT}" --more --max-seeds 8
  fi
  kill -TERM -"${SERVER_PID}" 2>/dev/null || true
  trap - EXIT
  for _ in $(seq 1 30); do
    used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)"
    (( used < 2000 )) && break; sleep 2
  done
fi

echo "--- ID cross-check pass ${PASS} ---"
"${PY}" regen_fix.py stage --pass "${PASS}"
if [[ ! -x "${REPO_ROOT}/packages/cosmos-framework/.venv/bin/python" ]]; then
  (cd "${REPO_ROOT}" && bash setup_inverse_dynamics.sh)
fi
ROOT10="${REPO_ROOT}/data/datasets/regen_pass${PASS}_10fps"
python3 run_inverse_dynamics.py --videos-root "${ROOT10}" \
  --manifest "${ROOT10}/resample_manifest.json" \
  --raw-out "${REPO_ROOT}/outputs/regen_pass${PASS}_raw.jsonl"
"${PY}" regen_fix.py idcheck --pass "${PASS}"
echo "=== regen pass ${PASS} done ==="
