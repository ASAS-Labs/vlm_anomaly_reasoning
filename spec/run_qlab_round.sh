#!/usr/bin/env bash
# Q-lab round driver: run one prompt-lab round on Qwen3.8-27B (family L).
# Serves the model once, then runs the direct / think / think-low variant
# groups through prompt_lab.py with per-group --model-arm, gates each group on
# 4 clips before the full 72, and writes per-group reports.
#
# Usage (inside tmux on the instance):
#   ROUND=1 bash spec/run_qlab_round.sh
# Env:
#   ROUND            (required) round number
#   SEED=1234        sampling seed (repro sessions: 4321 with PREFIX=qlab_rr<N>)
#   PREFIX=qlab_r$ROUND
#   QLAB_DIRECT="P0 L1 L2 L3 L4"        --model-arm verdict
#   QLAB_THINK="P0 L5 L6 L7 L8 L9 L10"  --model-arm verdict_think8k
#   QLAB_THINK_LOW="P0"                 --model-arm verdict_think8k_low
#   CONC=6           request concurrency
# Weights are never purged: the lab reuses qwen38 every round.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUND="${ROUND:?set ROUND=<n>}"
SEED="${SEED:-1234}"
PREFIX="${PREFIX:-qlab_r${ROUND}}"
QLAB_DIRECT="${QLAB_DIRECT-P0 L1 L2 L3 L4}"
QLAB_THINK="${QLAB_THINK-P0 L5 L6 L7 L8 L9 L10}"
QLAB_THINK_LOW="${QLAB_THINK_LOW-P0}"
QLAB_THINK_ARM="${QLAB_THINK_ARM:-verdict_think8k}"
CONC="${CONC:-6}"

VENV="${VENV_DIR:-${REPO_ROOT}/.venv-pilot}"
PY="${VENV}/bin/python"
PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}/v1"
SUBSET="${REPO_ROOT}/logs/vlm_agreement_subset_admitted.txt"
TREE="${REPO_ROOT}/data/datasets/generated_vids_720p"
TXT_SRC="${REPO_ROOT}/data/datasets/id_variants/v1_resample"
LOG_DIR="${REPO_ROOT}/logs"
export HF_HOME="${HF_HOME:-${HOME}/.cache/huggingface}"
export HF_HUB_DISABLE_XET=1

cd "${REPO_ROOT}/data/cosmos3"   # flat `from utils import ...` requires this CWD
HFID="$("${PY}" pilot_models.py --hf-id qwen38)"
mapfile -t SERVE_ARGS < <("${PY}" pilot_models.py --serve-args qwen38)

echo "=== qlab round ${ROUND} (prefix ${PREFIX}, seed ${SEED}) ==="

echo "--- trajectory txts into the 720p tree ---"
while IFS= read -r rel; do
  [[ -z "${rel}" ]] && continue
  txt="${rel%.mp4}.txt"
  if [[ ! -f "${TREE}/${txt}" ]]; then
    cp "${TXT_SRC}/${txt}" "${TREE}/${txt}"
  fi
done < "${SUBSET}"
N_TXT="$(find "${TREE}" -name '*.txt' | wc -l)"
if [[ "${N_TXT}" != "72" ]]; then
  echo "ERROR: 720p tree has ${N_TXT} txts, expected 72" >&2
  exit 1
fi

echo "--- download (cached after round 1) ---"
"${VENV}/bin/hf" download "${HFID}" >/dev/null

echo "--- serve ---"
setsid "${VENV}/bin/vllm" serve "${HFID}" "${SERVE_ARGS[@]}" --port "${PORT}" \
  > "${LOG_DIR}/${PREFIX}_server.log" 2>&1 &
SERVER_PID=$!
echo "${SERVER_PID}" > "${LOG_DIR}/${PREFIX}_server.pid"
trap 'echo "stopping server"; kill -TERM -"${SERVER_PID}" 2>/dev/null || kill "${SERVER_PID}" 2>/dev/null || true' EXIT

for _ in $(seq 1 900); do
  curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && { echo "server ready"; break; }
  kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/${PREFIX}_server.log" >&2; exit 1; }
  sleep 2
done
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || { echo "server never became healthy" >&2; exit 1; }

gate() {  # gate <variant_dir> : parse/truncation trouble on the first 4 records
  "${PY}" - "$1/results.jsonl" <<'EOF'
import json, sys
recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()][:4]
unk = sum(1 for r in recs if r.get("verdict") == "Unknown")
trunc = sum(1 for r in recs if r.get("finish_reason") == "length")
print(f"gate: {len(recs)} recs, unknown={unk}, truncated={trunc}")
sys.exit(0 if len(recs) and unk <= 2 and trunc <= 1 else 1)
EOF
}

median_reasoning() {  # median reasoning_content length over first 4 records
  "${PY}" - "$1/results.jsonl" <<'EOF'
import json, statistics, sys
recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()][:4]
lens = [len(r.get("reasoning_content") or "") for r in recs]
print(int(statistics.median(lens)) if lens else 0)
EOF
}

run_group() {  # run_group <suffix> <model_arm> <variants...>
  local sfx="$1" arm="$2"; shift 2
  local variants="$*"
  [[ -z "${variants// /}" ]] && return 0
  local vlist="${variants// /,}"
  echo "--- group ${sfx} (${arm}): ${vlist} ---"
  "${PY}" prompt_lab.py --round "${ROUND}" --variants "${vlist}" \
    --dataset "${TREE}" --subset "${SUBSET}" --server_url "${URL}" \
    --model-config qwen38 --model-arm "${arm}" \
    --out_prefix "${PREFIX}${sfx}" --seed "${SEED}" --concurrency 4 --limit 4
  for v in ${variants}; do
    gate "${LOG_DIR}/${PREFIX}${sfx}_${v}" \
      || { echo "GATE FAILED: ${sfx}/${v}"; tail -3 "${LOG_DIR}/${PREFIX}${sfx}_${v}/results.jsonl"; exit 1; }
  done
  "${PY}" prompt_lab.py --round "${ROUND}" --variants "${vlist}" \
    --dataset "${TREE}" --subset "${SUBSET}" --server_url "${URL}" \
    --model-config qwen38 --model-arm "${arm}" \
    --out_prefix "${PREFIX}${sfx}" --seed "${SEED}" --concurrency "${CONC}"
  "${PY}" prompt_lab_report.py --round "${ROUND}" --prefix "${PREFIX}${sfx}" \
    --baseline P0
}

run_group d verdict ${QLAB_DIRECT}
run_group t "${QLAB_THINK_ARM}" ${QLAB_THINK}

if [[ -n "${QLAB_THINK_LOW// /}" ]]; then
  # Decoding-axis gate: reasoning_effort=low must parse cleanly AND actually
  # shorten reasoning vs the think anchor BEFORE the full run, else the axis
  # is dead (kwarg inert or rejected) and we skip it.
  VLIST="${QLAB_THINK_LOW// /,}"
  echo "--- group tl (verdict_think8k_low): ${VLIST}, 4-clip gate ---"
  "${PY}" prompt_lab.py --round "${ROUND}" --variants "${VLIST}" \
    --dataset "${TREE}" --subset "${SUBSET}" --server_url "${URL}" \
    --model-config qwen38 --model-arm verdict_think8k_low \
    --out_prefix "${PREFIX}tl" --seed "${SEED}" --concurrency 4 --limit 4
  gate "${LOG_DIR}/${PREFIX}tl_P0" \
    || { echo "GATE FAILED: tl/P0"; exit 1; }
  [[ -f "${LOG_DIR}/${PREFIX}t_P0/results.jsonl" ]] \
    || { echo "tl gate needs the think-group P0 anchor; run the think group first" >&2; exit 1; }
  ANCHOR_LEN="$(median_reasoning "${LOG_DIR}/${PREFIX}t_P0")"
  LOW_LEN="$(median_reasoning "${LOG_DIR}/${PREFIX}tl_P0")"
  echo "reasoning length: think anchor ${ANCHOR_LEN} vs low ${LOW_LEN}"
  if (( ANCHOR_LEN > 0 && LOW_LEN * 10 >= ANCHOR_LEN * 9 )); then
    echo "AXIS INERT: reasoning_effort=low did not shorten reasoning; skipping full run"
  else
    "${PY}" prompt_lab.py --round "${ROUND}" --variants "${VLIST}" \
      --dataset "${TREE}" --subset "${SUBSET}" --server_url "${URL}" \
      --model-config qwen38 --model-arm verdict_think8k_low \
      --out_prefix "${PREFIX}tl" --seed "${SEED}" --concurrency "${CONC}"
    "${PY}" prompt_lab_report.py --round "${ROUND}" --prefix "${PREFIX}tl" \
      --baseline P0 || true
  fi
fi

echo "=== round ${ROUND} complete; server left for teardown by trap ==="
