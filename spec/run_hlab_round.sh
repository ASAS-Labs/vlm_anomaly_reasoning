#!/usr/bin/env bash
# H-lab round driver (family M): two-stage expectation-vs-action monitor on
# Qwen3.8 think@16k. Serves the model once, runs the champion anchor (L2 via
# prompt_lab.py) then each H variant via expectation_experiment.py (stage-1
# early window -> stage-2 trajectory follow-up), 4-clip gates, then reports.
#
#   tmux new -s hlab
#   ROUND=1 bash spec/run_hlab_round.sh
# Env:
#   ROUND            (required)
#   SEED=1234        (repro: SEED=4321 PREFIX=hlab_rr<N>)
#   PREFIX=hlab_r$ROUND
#   HLAB_ARMS="M0 M1 M2 M3 M4 M5 M6 M7"
#   HLAB_ARM=verdict_think16k      pilot arm for both stages (and the anchor)
#   ANCHOR=L2                      prompt_lab variant re-run in-session ("" to skip)
#   CONC=6
#   HLAB_SUBSET=logs/hlab_subset_80.txt   clip list (e.g. the 235-clip admitted list)
#   BASELINE=$ANCHOR               report baseline when the anchor is not re-run
#   HLAB_GATE=logs/hlab_gate_4.txt  4-clip gate list (must be inside HLAB_SUBSET)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUND="${ROUND:?set ROUND=<n>}"
SEED="${SEED:-1234}"
PREFIX="${PREFIX:-hlab_r${ROUND}}"
HLAB_ARMS="${HLAB_ARMS-M0 M1 M2 M3 M4 M5 M6 M7}"
HLAB_ARM="${HLAB_ARM:-verdict_think16k}"
ANCHOR="${ANCHOR-L2}"
CONC="${CONC:-6}"
VENV="${VENV_DIR:-${REPO_ROOT}/.venv-pilot}"
PY="${VENV}/bin/python"
PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}/v1"
SUBSET="${HLAB_SUBSET:-${REPO_ROOT}/logs/hlab_subset_80.txt}"
GATE="${HLAB_GATE:-${REPO_ROOT}/logs/hlab_gate_4.txt}"
DS="${REPO_ROOT}/data/datasets"
TREE="${DS}/generated_vids_720p"
LOG_DIR="${REPO_ROOT}/logs"
export HF_HOME="${HF_HOME:-${HOME}/.cache/huggingface}"
export HF_HUB_DISABLE_XET=1
cd "${REPO_ROOT}/data/cosmos3"
HFID="$("${PY}" pilot_models.py --hf-id qwen38)"
mapfile -t SERVE_ARGS < <("${PY}" pilot_models.py --serve-args qwen38)

echo "=== hlab round ${ROUND} (prefix ${PREFIX}, seed ${SEED}) ==="

echo "--- early trees (video-only) ---"
build_tree() {  # build_tree <mode> <secs> <dir>
  local d="$3"
  if [[ "$(find "${d}" -name '*.mp4' 2>/dev/null | wc -l)" != "$(grep -c . "${SUBSET}")" ]]; then
    "${PY}" make_pilot_trees.py --subset "${SUBSET}" --skip-existing \
      --early-mode "$1" --early-secs "$2" --out-early "${d}"
  fi
  [[ "$(find "${d}" -name '*.txt' | wc -l)" == "0" ]] || { echo "ERROR: ${d} must be video-only" >&2; exit 1; }
}
build_tree t_minus 2.5 "${DS}/generated_vids_720p_tminus2.5"
build_tree gt 0 "${DS}/generated_vids_720p_early_gt"
build_tree t_minus 1.5 "${DS}/generated_vids_720p_tminus1.5"
build_tree t_minus 1.0 "${DS}/generated_vids_720p_tminus1.0"
build_tree fixed 1.5 "${DS}/generated_vids_720p_early1.5s"
build_tree fixed 1.0 "${DS}/generated_vids_720p_early1.0s"
N_TXT="$(find "${TREE}" -name '*.txt' | wc -l)"; N_SUB="$(grep -c . "${SUBSET}")"
(( N_TXT >= N_SUB )) || { echo "ERROR: ${TREE} has ${N_TXT} txts < ${N_SUB}" >&2; exit 1; }

echo "--- download (cached after round 1) ---"
"${VENV}/bin/hf" download "${HFID}" >/dev/null
echo "--- serve ---"
setsid "${VENV}/bin/vllm" serve "${HFID}" "${SERVE_ARGS[@]}" --port "${PORT}" \
  > "${LOG_DIR}/${PREFIX}_server.log" 2>&1 &
SERVER_PID=$!
trap 'echo "stopping server"; kill -TERM -"${SERVER_PID}" 2>/dev/null || kill "${SERVER_PID}" 2>/dev/null || true' EXIT
for _ in $(seq 1 900); do
  curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && { echo "server ready"; break; }
  kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see ${LOG_DIR}/${PREFIX}_server.log" >&2; exit 1; }
  sleep 2
done
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || { echo "server never became healthy" >&2; exit 1; }

gate_verdict() {  # <results.jsonl> <n_expected> <clip list file>
  "${PY}" - "$1" "$2" "$3" <<'PYEOF'
import json, sys
n = int(sys.argv[2])
want = [l.strip() for l in open(sys.argv[3]) if l.strip()][:n]
recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
recs = [r for r in recs if r["video"] in want]   # judge only the gate clips (resume-safe)
unk = sum(1 for r in recs if r.get("verdict") == "Unknown")
t2 = sum(1 for r in recs if r.get("finish_reason") == "length")
s1u = sum(1 for r in recs if r.get("expect") == "unknown")
print(f"gate: {len(recs)}/{n} recs, unknown={unk}, stage2-trunc={t2}, stage1-unknown={s1u}")
sys.exit(0 if len(recs) >= n and unk <= 2 and t2 <= 1 and s1u <= 2 else 1)
PYEOF
}

if [[ -n "${ANCHOR// /}" ]]; then
  echo "--- anchor ${ANCHOR} (${HLAB_ARM}) ---"
  "${PY}" prompt_lab.py --round "${ROUND}" --variants "${ANCHOR}" --dataset "${TREE}" \
    --subset "${SUBSET}" --server_url "${URL}" --model-config qwen38 --model-arm "${HLAB_ARM}" \
    --out_prefix "${PREFIX}t" --seed "${SEED}" --concurrency 4 --limit 4
  gate_verdict "${LOG_DIR}/${PREFIX}t_${ANCHOR}/results.jsonl" 4 "${SUBSET}" || { echo "GATE FAILED: ${ANCHOR}"; exit 1; }
  "${PY}" prompt_lab.py --round "${ROUND}" --variants "${ANCHOR}" --dataset "${TREE}" \
    --subset "${SUBSET}" --server_url "${URL}" --model-config qwen38 --model-arm "${HLAB_ARM}" \
    --out_prefix "${PREFIX}t" --seed "${SEED}" --concurrency "${CONC}"
fi

for ARM in ${HLAB_ARMS}; do
  WIN="$("${PY}" -c "import h_variants as h; print(h.WINDOWS[h.H_VARIANTS['${ARM}']['stage1_window']])")"
  EARLY="${DS}/${WIN}"
  OUT="${LOG_DIR}/${PREFIX}t_${ARM}"
  echo "--- arm ${ARM} (window ${WIN}) ---"
  "${PY}" expectation_experiment.py --stage monitor --hvariant "${ARM}" \
    --dataset "${EARLY}" --full-dataset "${TREE}" --subset "${GATE}" \
    --server_url "${URL}" --out_dir "${OUT}" --model-config qwen38 --model-arm "${HLAB_ARM}" \
    --seed "${SEED}" --concurrency 4
  gate_verdict "${OUT}/results.jsonl" 4 "${GATE}" || { echo "GATE FAILED: ${ARM}"; tail -2 "${OUT}/results.jsonl" | cut -c1-300; exit 1; }
  "${PY}" expectation_experiment.py --stage monitor --hvariant "${ARM}" \
    --dataset "${EARLY}" --full-dataset "${TREE}" --subset "${SUBSET}" \
    --server_url "${URL}" --out_dir "${OUT}" --model-config qwen38 --model-arm "${HLAB_ARM}" \
    --seed "${SEED}" --concurrency "${CONC}"
done

echo "--- reports ---"
BASELINE="${BASELINE:-${ANCHOR:-M0}}"
"${PY}" prompt_lab_report.py --round "${ROUND}" --prefix "${PREFIX}t" --baseline "${BASELINE}"
"${PY}" hlab_report.py --prefix "${PREFIX}t" --anchor "${BASELINE}"
echo "=== hlab round ${ROUND} complete ==="
