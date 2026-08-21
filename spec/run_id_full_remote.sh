#!/usr/bin/env bash
# Fixed inverse-dynamics pass for every clip that still lacks a v1 record
# (logs/id_pending.txt, computed locally from outputs/id_raw.jsonl):
#   fetch the released dataset -> resample all 315 (10 fps; long 8 s clips at
#   7.5 fps) -> ID only on the pending clips (filtered manifest) -> raw poses
#   to outputs/id_full_raw.jsonl. Resumable (ID runner skips cached clips).
#
#   tmux new -s idfull
#   export HF_TOKEN=...   # dataset fetch
#   bash spec/run_id_full_remote.sh
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HF_HUB_DISABLE_XET=1
VENV="${REPO_ROOT}/.venv-regen"
if [[ ! -x "${VENV}/bin/python" ]]; then
  uv venv -q --python 3.13 --seed "${VENV}"
fi
uv pip install -q --python "${VENV}/bin/python" numpy opencv-python-headless huggingface_hub
PY="${VENV}/bin/python"
cd "${REPO_ROOT}/data/cosmos3"

echo "--- dataset ---"
"${PY}" fetch_eval_dataset.py
echo "--- resample all 315 (uniform 10 fps, long 7.5 fps) ---"
"${PY}" resample_videos.py --all --skip-existing
ROOT10="${REPO_ROOT}/data/datasets/generated_vids_10fps"
echo "--- pending manifest ---"
"${PY}" - "${ROOT10}/resample_manifest.json" "${REPO_ROOT}/logs/id_pending.txt" \
  "${ROOT10}/pending_manifest.json" <<'PYEOF'
import json, sys
man = json.load(open(sys.argv[1]))
pend = {l.strip() for l in open(sys.argv[2]) if l.strip()}
clips = [c for c in man["clips"] if c["rel_path"] in pend]
missing = pend - {c["rel_path"] for c in clips}
if missing:
    sys.exit(f"{len(missing)} pending clips missing from resample manifest, e.g. {sorted(missing)[:3]}")
json.dump({**man, "clips": clips}, open(sys.argv[3], "w"), indent=1)
print(f"pending manifest: {len(clips)} clips")
PYEOF
if [[ ! -x "${REPO_ROOT}/packages/cosmos-framework/.venv/bin/python" ]]; then
  (cd "${REPO_ROOT}" && bash setup_inverse_dynamics.sh)
fi
export COSMOS3_ID_WORK_DIR="${REPO_ROOT}/outputs/inverse_dynamics_full"
echo "--- inverse dynamics on pending clips ---"
python3 run_inverse_dynamics.py --videos-root "${ROOT10}" \
  --manifest "${ROOT10}/pending_manifest.json" \
  --raw-out "${REPO_ROOT}/outputs/id_full_raw.jsonl"
echo "=== ID full pass done ==="
