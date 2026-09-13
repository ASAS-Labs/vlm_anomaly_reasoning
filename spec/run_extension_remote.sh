#!/usr/bin/env bash
# Taxonomy-extension generation on a vast.ai box (vllm/vllm-omni:cosmos3 image):
# serve Cosmos3-Nano, render the round's clips (round 1: every extension prompt at
# seed 1234; round N>=2: best-of-N seeds for logs/extension/round<N>_targets.json with
# the flow-probe gate), stage a 10 fps tree, run the inverse-dynamics pass.
#
#   tmux new -d -s ext "ROUND=1 bash spec/run_extension_remote.sh 2>&1 | tee logs/extension_round1_driver.log"
#   knobs: ROUND, PORT, MAX_SEEDS (default 4), SKIP_GEN=1 (stage + ID only)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8000}"
ROUND="${ROUND:-1}"
MAX_SEEDS="${MAX_SEEDS:-4}"
SKIP_GEN="${SKIP_GEN:-0}"
LOG_DIR="${REPO_ROOT}/logs"
VENV="${REPO_ROOT}/.venv-regen"
export HF_HUB_DISABLE_XET=1
mkdir -p "${LOG_DIR}/extension"
cd "${REPO_ROOT}/data/cosmos3"

if [[ ! -x "${VENV}/bin/python" ]]; then
  uv venv -q --python 3.13 --seed "${VENV}"
  uv pip install -q --python "${VENV}/bin/python" numpy opencv-python-headless
fi
PY="${VENV}/bin/python"

GEN_ARGS=(render --round "${ROUND}" --server-url "http://127.0.0.1:${PORT}")
if [[ "${ROUND}" != "1" ]]; then
  GEN_ARGS+=(--targets "${LOG_DIR}/extension/round${ROUND}_targets.json" --max-seeds "${MAX_SEEDS}")
fi

if [[ "${SKIP_GEN}" != "1" ]]; then
  echo "--- serve Cosmos3-Nano (omni) ---"
  setsid vllm serve nvidia/Cosmos3-Nano --omni \
    --model-class-name Cosmos3OmniDiffusersPipeline \
    --allowed-local-media-path / --tensor-parallel-size 1 \
    --port "${PORT}" --init-timeout 1800 \
    > "${LOG_DIR}/extension_server.log" 2>&1 &
  SERVER_PID=$!
  trap 'echo "stopping server"; kill -TERM -"${SERVER_PID}" 2>/dev/null || true' EXIT
  for _ in $(seq 1 900); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/v1/models" || true)"
    [[ "${code}" == "200" ]] && { echo "server ready"; break; }
    kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/extension_server.log" >&2; exit 1; }
    sleep 2
  done
  echo "--- render round ${ROUND} ---"
  "${PY}" extension_generate.py "${GEN_ARGS[@]}"
  kill -TERM -"${SERVER_PID}" 2>/dev/null || true
  trap - EXIT
  for _ in $(seq 1 30); do
    used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)"
    (( used < 2000 )) && break; sleep 2
  done
fi

echo "--- stage round ${ROUND} (10 fps) ---"
"${PY}" extension_generate.py stage --round "${ROUND}"
if [[ ! -x "${REPO_ROOT}/packages/cosmos-framework/.venv/bin/python" ]]; then
  (cd "${REPO_ROOT}" && bash setup_inverse_dynamics.sh)
fi
ROOT10="${REPO_ROOT}/data/datasets/extension_round${ROUND}_10fps"
# Per-round prediction cache: the ID runner keys outputs by clip rel-path and every
# round stages candidates at the fixed rel-path, so a shared cache would reuse stale poses.
export COSMOS3_ID_WORK_DIR="${REPO_ROOT}/outputs/inverse_dynamics_extension_round${ROUND}"
echo "--- inverse dynamics round ${ROUND} ---"
python3 run_inverse_dynamics.py --videos-root "${ROOT10}" \
  --manifest "${ROOT10}/resample_manifest.json" \
  --raw-out "${REPO_ROOT}/outputs/extension_round${ROUND}_raw.jsonl" \
  --prompts-root "${REPO_ROOT}/data/cosmos3/video_gen_prompts/extension"
echo "=== extension round ${ROUND} done ==="
