#!/usr/bin/env bash
# Family N driver: LoRA-SFT the M8 stage-1 expectation (Qwen3.8-27B) with
# leave-scene-group-out CV, evaluate each fold's model inside the unchanged M8
# two-stage monitor on its held-out clips, and compare the CV-concatenated
# predictions against an in-session zero-shot anchor. See the plan / Part 18.
#
#   tmux new -s sft
#   PREFIX=sft_r1 bash spec/run_sft_cv.sh
# Env:
#   PREFIX=sft_r1  SEED=1234 (eval sampling)  TRAIN_SEED=1234
#   FOLDS="f1 f2 f3 f4 f5"  CONC=6  PORT=8000
#   EPOCHS=2 LR=1e-4 RANK=16 ALPHA=32 MAXLEN=16384 GRAD_ACC=8
#   RUN_RATIONALIZE=1  RUN_ANCHOR=1   (set 0 on a second training seed)
#   SMOKE=0            1 = tiny train (5 steps) + parity + merge + serve + gate, then exit
#   BUDGET_MIN=330     abort before starting a fold past this wall-clock budget
#   SWIFT_MODEL_TYPE=qwen3_5 SWIFT_TEMPLATE=qwen3_8   (Qwen3.8-27B is registered under model_type qwen3_5 in ms-swift 4.x)
#   SFT_VIDEO_ENV="FPS=8 FPS_MIN_FRAMES=4 FPS_MAX_FRAMES=64 VIDEO_MAX_TOKEN_NUM=2048"
#   SMOKE runs rationalize (needed for the dataset) but NOT the anchor; the anchor runs on the real launch.
# Layout: logs/${PREFIX}_anchor/, logs/${PREFIX}_f<k>/ (results.jsonl, run_meta.json,
#   fold_meta.json, trainer_state.json, train.log); adapters/merged under tmp/sft/
#   (gitignored; merged dirs deleted after eval); driver log is this script's stdout.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${PREFIX:-sft_r1}"; SEED="${SEED:-1234}"; TRAIN_SEED="${TRAIN_SEED:-1234}"
FOLDS="${FOLDS-f1 f2 f3 f4 f5}"; CONC="${CONC:-6}"; PORT="${PORT:-8000}"
EPOCHS="${EPOCHS:-2}"; LR="${LR:-1e-4}"; RANK="${RANK:-16}"; ALPHA="${ALPHA:-32}"
MAXLEN="${MAXLEN:-16384}"; GRAD_ACC="${GRAD_ACC:-8}"
RUN_RATIONALIZE="${RUN_RATIONALIZE:-1}"; RUN_ANCHOR="${RUN_ANCHOR:-1}"; SMOKE="${SMOKE:-0}"
BUDGET_MIN="${BUDGET_MIN:-330}"
SWIFT_MODEL_TYPE="${SWIFT_MODEL_TYPE:-qwen3_5}"; SWIFT_TEMPLATE="${SWIFT_TEMPLATE:-qwen3_8}"
SFT_VIDEO_ENV="${SFT_VIDEO_ENV:-FPS=8 FPS_MIN_FRAMES=4 FPS_MAX_FRAMES=64 VIDEO_MAX_TOKEN_NUM=2048}"
VP="${REPO_ROOT}/.venv-pilot"; VS="${REPO_ROOT}/.venv-sft"
PYP="${VP}/bin/python"; PYS="${VS}/bin/python"
URL="http://127.0.0.1:${PORT}/v1"
DS="${REPO_ROOT}/data/datasets"; TREE="${DS}/generated_vids_720p"; EARLY="${DS}/generated_vids_720p_early_gt"
SUBSET="${REPO_ROOT}/logs/vlm_agreement_subset_admitted.txt"
GATE="${REPO_ROOT}/logs/hlab_gate_4.txt"
SFT="${REPO_ROOT}/logs/sft"; LOG_DIR="${REPO_ROOT}/logs"; WORK="${REPO_ROOT}/tmp/sft/${PREFIX}"
export HF_HOME="${HF_HOME:-${HOME}/.cache/huggingface}"; export HF_HUB_DISABLE_XET=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
T_START=$(date +%s)
mkdir -p "${SFT}" "${WORK}"
cd "${REPO_ROOT}/data/cosmos3"

echo "=== SFT CV ${PREFIX} (train seed ${TRAIN_SEED}, eval seed ${SEED}, folds: ${FOLDS}) ==="
echo "--- preflight ---"
[[ -x "${PYP}" ]] || { echo "missing ${VP} (run spec/setup_pilot.sh)" >&2; exit 1; }
[[ -x "${PYS}" ]] || { echo "missing ${VS} (run spec/setup_sft.sh)" >&2; exit 1; }
N_SUB="$(grep -c . "${SUBSET}")"
[[ "$(find "${EARLY}" -name '*.mp4' | wc -l)" == "${N_SUB}" ]] || { echo "early_gt tree != ${N_SUB} clips" >&2; exit 1; }
[[ "$(find "${EARLY}" -name '*.txt' | wc -l)" == "0" ]] || { echo "early_gt tree must be video-only" >&2; exit 1; }
(( $(find "${TREE}" -name '*.txt' | wc -l) >= N_SUB )) || { echo "720p tree lacks trajectory txts" >&2; exit 1; }
HFID="$("${PYP}" pilot_models.py --hf-id qwen38)"
mapfile -t SERVE_ARGS < <("${PYP}" pilot_models.py --serve-args qwen38)
snapshot_path() {  # local snapshot dir of the base model (offline first, then download)
  "${PYP}" -c 'import sys
from huggingface_hub import snapshot_download
try:
    print(snapshot_download(sys.argv[1], local_files_only=True))
except Exception:
    print(snapshot_download(sys.argv[1]))' "${HFID}"
}
BASE="${BASE:-$(snapshot_path)}"
[[ -f "${BASE}/config.json" ]] || { echo "base snapshot not found: ${BASE}" >&2; exit 1; }
echo "base: ${BASE}"
GIT_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo '')"

SERVER_PID=""
stop_server() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "stopping server ${SERVER_PID}"; kill -TERM -"${SERVER_PID}" 2>/dev/null || kill "${SERVER_PID}" 2>/dev/null || true
    for _ in $(seq 1 60); do kill -0 "${SERVER_PID}" 2>/dev/null || break; sleep 2; done
  fi
  SERVER_PID=""
}
trap stop_server EXIT
serve() {  # serve <model path or id> <served name> <log file>
  setsid "${VP}/bin/vllm" serve "$1" --served-model-name "$2" "${SERVE_ARGS[@]}" --port "${PORT}" \
    > "$3" 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 450); do
    curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && { echo "server ready ($2)"; return 0; }
    kill -0 "${SERVER_PID}" 2>/dev/null || { echo "server died; see $3" >&2; tail -20 "$3"; return 1; }
    sleep 2
  done
  echo "server never became healthy" >&2; return 1
}
elapsed_min() { echo $(( ($(date +%s) - T_START) / 60 )); }

gate_check() {  # gate_check <results.jsonl> <n> <clip list> [sft]  (verdict + stage-1 format gate)
  "${PYP}" - "$1" "$2" "$3" "${4:-}" <<'PYEOF'
import json, sys
n = int(sys.argv[2]); want = [l.strip() for l in open(sys.argv[3]) if l.strip()][:n]; sft = sys.argv[4] == "sft"
recs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
recs = [r for r in recs if r["video"] in want]
unk = sum(1 for r in recs if r.get("verdict") == "Unknown")
t2 = sum(1 for r in recs if r.get("finish_reason") == "length")
s1u = sum(1 for r in recs if r.get("expect") == "unknown")
fmt_bad = 0
if sft:
    for r in recs:
        raw = (r.get("expect_raw") or "").strip()
        last = [l for l in raw.splitlines() if l.strip()][-1].strip().lower() if raw else ""
        if (not raw) or (r.get("reasoning_content") or "") or last.strip(".!* ") not in ("continue", "slow", "stop", "wait"):
            fmt_bad += 1
print(f"gate: {len(recs)}/{n} recs, unknown={unk}, stage2-trunc={t2}, stage1-unknown={s1u}, sft-format-bad={fmt_bad}")
sys.exit(0 if len(recs) >= n and unk <= 2 and t2 <= 1 and s1u <= 2 and fmt_bad <= 1 else 1)
PYEOF
}

run_monitor() {  # run_monitor <subset file> <out dir> <stage1 arm> <concurrency> [--limit N]
  local sub="$1" out="$2" s1arm="$3" conc="$4"; shift 4
  "${PYP}" expectation_experiment.py --stage monitor --hvariant M8gt \
    --dataset "${EARLY}" --full-dataset "${TREE}" --subset "${sub}" --server_url "${URL}" \
    --out_dir "${out}" --model-config qwen38 --model-arm verdict_think16k --stage1-arm "${s1arm}" \
    --seed "${SEED}" --concurrency "${conc}" "$@"
}

# ---------------------------------------------------------------- base model phase
NEED_BASE=0
[[ "${RUN_RATIONALIZE}" == "1" && "$(wc -l < "${SFT}/rationales.jsonl" 2>/dev/null || echo 0)" -lt "${N_SUB}" ]] && NEED_BASE=1
[[ "${RUN_ANCHOR}" == "1" && "${SMOKE}" != "1" && "$(wc -l < "${LOG_DIR}/${PREFIX}_anchor/results.jsonl" 2>/dev/null || echo 0)" -lt "${N_SUB}" ]] && NEED_BASE=1
[[ "${SMOKE}" == "1" ]] && NEED_BASE=1
FIRST_CLIP="${EARLY}/$(head -1 "${SUBSET}")"
if [[ "${NEED_BASE}" == "1" ]]; then
  echo "--- serve base ---"
  serve "${HFID}" "qwen38-base" "${LOG_DIR}/${PREFIX}_server_base.log"
  echo "--- parity (vllm side) ---"
  "${PYP}" sft_parity.py --side vllm --server_url "${URL}" --clip "${FIRST_CLIP}" --out "${SFT}/parity_${PREFIX}.json"
  if [[ "${RUN_RATIONALIZE}" == "1" ]]; then
    echo "--- rationalize (self-distilled targets) ---"
    "${PYP}" sft_rationalize.py --server_url "${URL}" --dataset "${EARLY}" --subset "${SUBSET}" \
      --out "${SFT}/rationales.jsonl" --seed "${SEED}" --concurrency "${CONC}"
  fi
fi
echo "--- dataset ---"
"${PYP}" sft_data.py --rationales "${SFT}/rationales.jsonl" --video-root "${EARLY}" --out "${SFT}"
if [[ "${NEED_BASE}" == "1" && "${RUN_ANCHOR}" == "1" && "${SMOKE}" != "1" ]]; then
  echo "--- anchor: zero-shot M8gt think@16k on all ${N_SUB} ---"
  run_monitor "${SUBSET}" "${LOG_DIR}/${PREFIX}_anchor" verdict_think16k 4 --limit 4
  gate_check "${LOG_DIR}/${PREFIX}_anchor/results.jsonl" 4 "${SUBSET}" || { echo "GATE FAILED: anchor"; exit 1; }
  run_monitor "${SUBSET}" "${LOG_DIR}/${PREFIX}_anchor" verdict_think16k "${CONC}"
fi

# ---------------------------------------------------------------- training helpers
train_fold() {  # train_fold <name> <train.jsonl> <out dir> [extra swift args...]
  local name="$1" data="$2" out="$3"; shift 3
  mkdir -p "${out}"
  # shellcheck disable=SC2086
  env ${SFT_VIDEO_ENV} timeout 70m "${VS}/bin/swift" sft --model "${BASE}" --model_type "${SWIFT_MODEL_TYPE}" \
    --template "${SWIFT_TEMPLATE}" --train_type lora --dataset "${data}" --split_dataset_ratio 0 \
    --lora_rank "${RANK}" --lora_alpha "${ALPHA}" --target_modules all-linear \
    --freeze_vit true --freeze_aligner true --learning_rate "${LR}" --num_train_epochs "${EPOCHS}" \
    --per_device_train_batch_size 1 --gradient_accumulation_steps "${GRAD_ACC}" --torch_dtype bfloat16 \
    --gradient_checkpointing true --attn_impl sdpa --max_length "${MAXLEN}" \
    --add_non_thinking_prefix true --loss_scale ignore_empty_think \
    --lr_scheduler_type cosine --warmup_ratio 0.05 --weight_decay 0 --seed "${TRAIN_SEED}" --data_seed "${TRAIN_SEED}" \
    --dataloader_num_workers 2 --logging_steps 1 --save_strategy epoch --save_total_limit 1 --report_to tensorboard \
    --output_dir "${out}" "$@"
}
latest_ckpt() { find "$1" -maxdepth 3 -type d -name 'checkpoint-*' | sort -V | tail -1; }
merge_ckpt() {  # merge_ckpt <ckpt> <merged dir>
  rm -rf "$2"   # swift export refuses an existing output_dir (partial merge -> blocked resume)
  "${VS}/bin/swift" export --adapters "$1" --merge_lora true --output_dir "$2"
  # processor / template files the server needs, back-filled from the base snapshot
  # (HF-cache files are symlinks: -L dereferences them)
  for f in "${BASE}"/*; do
    b="$(basename "$f")"
    case "$b" in *.safetensors|model.safetensors.index.json|config.json|README*|LICENSE*|.gitattributes|*crc32*) continue;; esac
    [[ -e "$2/$b" ]] || cp -rL "$f" "$2/"
  done
  [[ -f "$2/config.json" ]] || { echo "merged dir has no config.json" >&2; return 1; }
}
loss_ok() {  # loss_ok <trainer_state.json> <strict 0|1>
  "${PYP}" - "$1" "$2" <<'PYEOF'
import json, math, sys
st = json.load(open(sys.argv[1])); strict = sys.argv[2] == "1"
losses = [h["loss"] for h in st.get("log_history", []) if "loss" in h]
print(f"loss: steps={len(losses)} first={losses[0] if losses else None} last={losses[-1] if losses else None}")
if not losses or any(math.isnan(x) for x in losses):
    sys.exit("loss NaN or empty")
k = min(3, len(losses))
if strict and sum(losses[-k:]) / k >= sum(losses[:k]) / k:
    sys.exit("loss did not decrease (mean of last 3 >= mean of first 3)")
PYEOF
}

# ---------------------------------------------------------------- smoke
if [[ "${SMOKE}" == "1" ]]; then
  echo "--- SMOKE: tiny train + parity + merge + serve + gate ---"
  stop_server
  SW="${WORK}/smoke"; rm -rf "${SW}"; mkdir -p "${SW}"
  echo "--- parity (swift side) ---"
  # shellcheck disable=SC2086
  env ${SFT_VIDEO_ENV} "${PYS}" sft_parity.py --side swift --model "${BASE}" --model-type "${SWIFT_MODEL_TYPE}" \
    --template "${SWIFT_TEMPLATE}" --clip "${FIRST_CLIP}" --out "${SFT}/parity_${PREFIX}.json"
  train_fold smoke "${SFT}/smoke/train.jsonl" "${SW}/ckpt" --max_steps 5 --save_steps 5 2>&1 | tee "${SW}/train.log"
  CKPT="$(latest_ckpt "${SW}/ckpt")"; [[ -n "${CKPT}" ]] || { echo "no checkpoint"; exit 1; }
  loss_ok "${CKPT}/trainer_state.json" 0
  merge_ckpt "${CKPT}" "${SW}/merged"
  serve "${SW}/merged" "qwen38-sft-smoke" "${LOG_DIR}/${PREFIX}_server_smoke.log"
  run_monitor "${SFT}/f1/held_out.txt" "${LOG_DIR}/${PREFIX}_smoke" expect_sft 4 --limit 4
  gate_check "${LOG_DIR}/${PREFIX}_smoke/results.jsonl" 4 "${SFT}/f1/held_out.txt" sft || { echo "SMOKE GATE FAILED"; tail -2 "${LOG_DIR}/${PREFIX}_smoke/results.jsonl" | cut -c1-400; exit 1; }
  stop_server; rm -rf "${SW}/merged"
  echo "=== SMOKE OK (elapsed $(elapsed_min) min) ==="
  exit 0
fi
stop_server

# ---------------------------------------------------------------- folds
for K in ${FOLDS}; do
  OUT="${LOG_DIR}/${PREFIX}_${K}"; HELD="${SFT}/${K}/held_out.txt"; N_HELD="$(grep -c . "${HELD}")"
  if [[ "$(wc -l < "${OUT}/results.jsonl" 2>/dev/null || echo 0)" -ge "${N_HELD}" ]]; then
    echo "--- ${K}: complete (${N_HELD}) — skipping ---"; continue
  fi
  if (( $(elapsed_min) > BUDGET_MIN )); then echo "BUDGET: $(elapsed_min) min > ${BUDGET_MIN}; stopping before ${K}"; break; fi
  echo "--- ${K}: train (held out ${N_HELD}, train $(wc -l < "${SFT}/${K}/train.jsonl")) ---"
  mkdir -p "${OUT}"; FW="${WORK}/${K}"; mkdir -p "${FW}"
  T0=$(date +%s)
  if [[ -f "${FW}/.train_done" ]]; then
    CKPT="$(latest_ckpt "${FW}/ckpt")"; echo "${K}: reusing finished adapter ${CKPT}"
  else
    rm -rf "${FW}/ckpt"   # never resume a partial (e.g. 1-epoch) checkpoint as if complete
    train_fold "${K}" "${SFT}/${K}/train.jsonl" "${FW}/ckpt" 2>&1 | tee "${OUT}/train.log"
    CKPT="$(latest_ckpt "${FW}/ckpt")"; [[ -n "${CKPT}" ]] || { echo "${K}: no checkpoint"; exit 1; }
    touch "${FW}/.train_done"
  fi
  T1=$(date +%s)
  cp "${CKPT}/trainer_state.json" "${OUT}/trainer_state.json"
  loss_ok "${OUT}/trainer_state.json" 1 || { echo "${K}: LOSS SANITY FAILED"; exit 1; }
  echo "--- ${K}: merge + serve ---"
  [[ -f "${FW}/merged/config.json" ]] || merge_ckpt "${CKPT}" "${FW}/merged"
  serve "${FW}/merged" "qwen38-sft-${PREFIX}-${K}" "${LOG_DIR}/${PREFIX}_server_${K}.log"
  T2=$(date +%s)
  echo "--- ${K}: gate + eval on held-out ---"
  run_monitor "${HELD}" "${OUT}" expect_sft 4 --limit 4
  gate_check "${OUT}/results.jsonl" 4 "${HELD}" sft || { echo "GATE FAILED: ${K}"; tail -2 "${OUT}/results.jsonl" | cut -c1-400; exit 1; }
  run_monitor "${HELD}" "${OUT}" expect_sft "${CONC}"
  T3=$(date +%s)
  stop_server
  "${PYP}" - "${OUT}/fold_meta.json" "${OUT}/trainer_state.json" "${K}" "${CKPT}" "${BASE}" "${SFT}/${K}/train.jsonl" \
      "$((T1-T0))" "$((T2-T1))" "$((T3-T2))" "${GIT_COMMIT}" "${TRAIN_SEED}" "${SEED}" "${EPOCHS}" "${LR}" "${RANK}" "${ALPHA}" "${MAXLEN}" "${GRAD_ACC}" "${SFT_VIDEO_ENV}" <<'PYEOF'
import hashlib, json, sys
(out, state, k, ckpt, base, train, t_train, t_merge, t_eval, git, tseed, eseed, ep, lr, rank, alpha, maxlen, ga, venv) = sys.argv[1:]
train_sha = hashlib.sha256(open(train, "rb").read()).hexdigest()
st = json.load(open(state)); hist = st.get("log_history", [])
losses = [h["loss"] for h in hist if "loss" in h]
rt = next((h for h in reversed(hist) if "train_runtime" in h), {})
n_train = sum(1 for _ in open(train))
usd = round((int(t_train) + int(t_merge) + int(t_eval)) / 3600 * 4.0, 2)
meta = {"fold": k, "ckpt": ckpt, "base": base, "train_n": n_train, "steps": st.get("global_step"),
        "epochs": float(ep), "lr": float(lr), "lora_rank": int(rank), "lora_alpha": int(alpha), "max_length": int(maxlen),
        "grad_accum": int(ga), "video_env": venv, "train_seed": int(tseed), "eval_seed": int(eseed),
        "first_loss": losses[0] if losses else None, "final_loss": losses[-1] if losses else None,
        "train_runtime_s": rt.get("train_runtime"), "train_samples_per_second": rt.get("train_samples_per_second"),
        "sec_per_sample": (round(1 / rt["train_samples_per_second"], 2) if rt.get("train_samples_per_second")
                           else round(int(t_train) / max(1, n_train * float(ep)), 2)),
        "train_jsonl_sha256": train_sha,
        "train_wall_min": round(int(t_train) / 60, 1), "merge_serve_min": round(int(t_merge) / 60, 1),
        "eval_min": round(int(t_eval) / 60, 1), "usd": usd, "git_commit": git}
json.dump(meta, open(out, "w"), indent=1); print(json.dumps(meta))
PYEOF
  rm -rf "${FW}/merged"
  echo "=== ${K} done (elapsed $(elapsed_min) min) ==="
done

echo "--- report ---"
if [[ -f "${LOG_DIR}/${PREFIX}_anchor/results.jsonl" ]]; then ANCHOR="${PREFIX}_anchor"; else ANCHOR="${ANCHOR:-sft_r1_anchor}"; fi
"${PYP}" sft_report.py --prefix "${PREFIX}" --anchor "${ANCHOR}" || echo "report: incomplete folds (resume the driver)"
echo "=== SFT CV ${PREFIX} complete (elapsed $(elapsed_min) min) ==="
