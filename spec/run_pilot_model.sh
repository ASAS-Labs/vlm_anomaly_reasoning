#!/usr/bin/env bash
# Per-model driver for the open-VLM pilot: download -> serve -> smoke gate ->
# 3 arms (expect_early, expect_full, verdict/P0) -> teardown + weight purge.
#
# Idempotent: every arm resumes from its results.jsonl, downloads are cached,
# and the smoke gate writes into the real out_dir so no requests are wasted.
#
# Usage (inside tmux on the instance):
#   bash spec/run_pilot_model.sh <model_key> [--smoke-only]
# Env:
#   CONC=6            request concurrency per arm
#   PREFETCH=<key>    background-download the next model once serving is healthy
#   KEEP_WEIGHTS=1    skip the HF-cache purge at teardown
#   PILOT_ARMS="..."  arms to run (default "expect_early expect_full verdict";
#                     verdict* tokens map to prompt_lab --model-arm <token>)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY="${1:?usage: run_pilot_model.sh <model_key> [--smoke-only]}"
SMOKE_ONLY=0; [[ "${2:-}" == "--smoke-only" ]] && SMOKE_ONLY=1

VENV="${VENV_DIR:-${REPO_ROOT}/.venv-pilot}"
PY="${VENV}/bin/python"
PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}/v1"
CONC="${CONC:-6}"
ARMS="${PILOT_ARMS:-expect_early expect_full verdict}"
SUBSET="${REPO_ROOT}/logs/vlm_agreement_subset_admitted.txt"
TREE="${REPO_ROOT}/data/datasets/generated_vids_720p"
TREE_EARLY="${REPO_ROOT}/data/datasets/generated_vids_720p_early"
LOG_DIR="${REPO_ROOT}/logs"
export HF_HOME="${HF_HOME:-${HOME}/.cache/huggingface}"
export HF_HUB_DISABLE_XET=1 HF_HUB_ENABLE_HF_TRANSFER=1

cd "${REPO_ROOT}/data/cosmos3"   # flat `from utils import ...` requires this CWD
HFID="$("${PY}" pilot_models.py --hf-id "${KEY}")"
NEED_GB="$("${PY}" pilot_models.py --weights-gb "${KEY}")"
mapfile -t SERVE_ARGS < <("${PY}" pilot_models.py --serve-args "${KEY}")

echo "=== ${KEY}: ${HFID} (${NEED_GB} GB) ==="

mkdir -p "${HF_HOME}"
FREE_GB="$(df -BG --output=avail "${HF_HOME}" | tail -1 | tr -dc '0-9')"
if [[ ! -d "${HF_HOME}/hub/models--${HFID//\//--}" ]] && (( FREE_GB < NEED_GB + 20 )); then
  echo "ERROR: ${FREE_GB} GB free < ${NEED_GB}+20 GB needed; purge first" >&2
  exit 1
fi

echo "--- download ---"
"${VENV}/bin/hf" download "${HFID}" >/dev/null

echo "--- serve ---"
# setsid: the server must lead its own process group, or the group-kill at
# teardown TERMs this script (and the PREFETCH download) along with it.
setsid "${VENV}/bin/vllm" serve "${HFID}" "${SERVE_ARGS[@]}" --port "${PORT}" \
  > "${LOG_DIR}/pilot_${KEY}_server.log" 2>&1 &
SERVER_PID=$!
echo "${SERVER_PID}" > "${LOG_DIR}/pilot_${KEY}_server.pid"
trap 'echo "stopping server"; kill -TERM -"${SERVER_PID}" 2>/dev/null || kill "${SERVER_PID}" 2>/dev/null || true' EXIT

for _ in $(seq 1 900); do
  curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && { echo "server ready"; break; }
  kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/pilot_${KEY}_server.log" >&2; exit 1; }
  sleep 2
done
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || { echo "server never became healthy" >&2; exit 1; }

if [[ -n "${PREFETCH:-}" ]]; then
  NEXT_ID="$("${PY}" pilot_models.py --hf-id "${PREFETCH}")"
  echo "--- prefetching ${NEXT_ID} in background ---"
  nohup "${VENV}/bin/hf" download "${NEXT_ID}" \
    > "${LOG_DIR}/pilot_prefetch_${PREFETCH}.log" 2>&1 &
fi

gate() {  # gate <results.jsonl> <n_expected>: abort on parse/truncation trouble
  "${PY}" - "$1" "$2" <<'EOF'
import json, sys
recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()][: int(sys.argv[2])]
unk = sum(1 for r in recs if r.get("expect") == "unknown"
          or r.get("verdict") == "Unknown")
trunc = sum(1 for r in recs if r.get("finish_reason") == "length")
print(f"gate: {len(recs)} recs, unknown={unk}, truncated={trunc}")
sys.exit(0 if len(recs) and unk <= 2 and trunc <= 1 else 1)
EOF
}

if [[ " ${ARMS} " == *" expect_early "* ]]; then
  echo "--- smoke: expect_early, 8 clips ---"
  "${PY}" expectation_experiment.py --stage expect_early --dataset "${TREE_EARLY}" \
    --subset "${SUBSET}" --server_url "${URL}" \
    --out_dir "${LOG_DIR}/pilot_${KEY}_expect_early" \
    --model-config "${KEY}" --concurrency 4 --limit 8
  gate "${LOG_DIR}/pilot_${KEY}_expect_early/results.jsonl" 8 \
    || { echo "SMOKE GATE FAILED; server log tail:"; tail -30 "${LOG_DIR}/pilot_${KEY}_server.log"; exit 1; }
fi

if [[ "${SMOKE_ONLY}" == "1" ]]; then
  echo "smoke-only: done (results resume on the next full run)"
  exit 0
fi

for ARM in ${ARMS}; do
  case "${ARM}" in
    expect_early)
      echo "--- arm: expect_early ---"
      "${PY}" expectation_experiment.py --stage expect_early --dataset "${TREE_EARLY}" \
        --subset "${SUBSET}" --server_url "${URL}" \
        --out_dir "${LOG_DIR}/pilot_${KEY}_expect_early" \
        --model-config "${KEY}" --concurrency "${CONC}"
      ;;
    expect_full)
      echo "--- arm: expect_full ---"
      "${PY}" expectation_experiment.py --stage expect_full --dataset "${TREE}" \
        --subset "${SUBSET}" --server_url "${URL}" \
        --out_dir "${LOG_DIR}/pilot_${KEY}_expect_full" \
        --model-config "${KEY}" --concurrency "${CONC}"
      ;;
    verdict*)
      echo "--- arm: ${ARM} (P0), 4-clip gate then full ---"
      "${PY}" prompt_lab.py --round 0 --variants P0 --dataset "${TREE}" \
        --subset "${SUBSET}" --server_url "${URL}" \
        --out_prefix "pilot_${KEY}_${ARM}" --model-config "${KEY}" \
        --model-arm "${ARM}" --concurrency 4 --limit 4
      gate "${LOG_DIR}/pilot_${KEY}_${ARM}_P0/results.jsonl" 4 \
        || { echo "VERDICT GATE FAILED (think switch/parse? see reasoning_content)"; \
             tail -5 "${LOG_DIR}/pilot_${KEY}_${ARM}_P0/results.jsonl"; exit 1; }
      "${PY}" prompt_lab.py --round 0 --variants P0 --dataset "${TREE}" \
        --subset "${SUBSET}" --server_url "${URL}" \
        --out_prefix "pilot_${KEY}_${ARM}" --model-config "${KEY}" \
        --model-arm "${ARM}" --concurrency "${CONC}"
      ;;
    *)
      echo "unknown arm ${ARM}" >&2; exit 1
      ;;
  esac
done

echo "--- teardown ---"
kill -TERM -"${SERVER_PID}" 2>/dev/null || kill "${SERVER_PID}" 2>/dev/null || true
trap - EXIT
for _ in $(seq 1 30); do
  USED="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)"
  (( USED < 2000 )) && break
  sleep 2
done
if [[ "${KEEP_WEIGHTS:-0}" != "1" ]]; then
  rm -rf "${HF_HOME}/hub/models--${HFID//\//--}"
  echo "purged weights for ${HFID}"
fi
echo "=== ${KEY} done ==="
