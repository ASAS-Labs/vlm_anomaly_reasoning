#!/usr/bin/env bash
# Pull evaluation results from the remote GPU box to this machine, on a loop.
#
# Pull-based on purpose: it keeps working when the remote run has already died
# (credit exhaustion, preemption), which is exactly when the partial results matter.
# results.jsonl is append-only, so --append-verify transfers only the new tail.
#
# Usage:
#   VAST_HOST=1.2.3.4 VAST_PORT=12345 bash spec/sync_results.sh
#   VAST_HOST=... VAST_PORT=... INTERVAL=30 bash spec/sync_results.sh

set -euo pipefail

: "${VAST_HOST:?set VAST_HOST (e.g. from: vastai ssh-url <instance-id>)}"
: "${VAST_PORT:?set VAST_PORT}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/workspace/vlm_anomaly_reasoning/logs/}"
LOCAL_DIR="${LOCAL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs/}"
INTERVAL="${INTERVAL:-60}"

mkdir -p "${LOCAL_DIR}"
echo "syncing ${REMOTE_USER}@${VAST_HOST}:${VAST_PORT}${REMOTE_DIR} -> ${LOCAL_DIR} every ${INTERVAL}s"
echo "(Ctrl-C to stop; partial results are kept)"

while true; do
  if rsync -az --partial --append-verify \
      --exclude 'vllm_server.log' \
      -e "ssh -p ${VAST_PORT} -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15" \
      "${REMOTE_USER}@${VAST_HOST}:${REMOTE_DIR}" "${LOCAL_DIR}"; then
    n=$(find "${LOCAL_DIR}" -name results.jsonl -exec cat {} + 2>/dev/null | wc -l)
    echo "$(date +%H:%M:%S)  ok — ${n} result records locally"
  else
    echo "$(date +%H:%M:%S)  sync failed (instance down?); retrying in ${INTERVAL}s" >&2
  fi
  sleep "${INTERVAL}"
done
