#!/usr/bin/env bash
# SFT environment for the stage-1 fine-tune (family N): ms-swift LoRA on
# Qwen3.8-27B (Qwen3.5 architecture). A THIRD venv, separate from .venv (Cosmos)
# and .venv-pilot (vLLM serving) — neither has a training stack.
#
#   bash spec/setup_sft.sh            # creates .venv-sft, writes logs/sft/env_pins.txt
# Env: VENV_DIR=.venv-sft  SWIFT_SPEC="ms-swift[llm]>=4.3.1"  TRANSFORMERS_SPEC="transformers>=5.9"
#
# The GatedDeltaNet layers need the `fla` (flash-linear-attention) and
# `causal_conv1d` kernels; without them the model silently falls back to slow,
# memory-hungry torch ops — so their import is a HARD check here.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${REPO_ROOT}/.venv-sft}"
SWIFT_SPEC="${SWIFT_SPEC:-ms-swift[llm]>=4.3.1}"
TRANSFORMERS_SPEC="${TRANSFORMERS_SPEC:-transformers>=5.9}"
export HF_HUB_DISABLE_XET=1
cd "${REPO_ROOT}"
command -v uv >/dev/null || { echo "uv not found" >&2; exit 1; }
mkdir -p logs/sft

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  uv venv --python 3.12 --seed --managed-python "${VENV_DIR}"
fi
PY="${VENV_DIR}/bin/python"
UVP=(uv pip install --python "${PY}")

echo "--- torch (cu130) ---"
"${UVP[@]}" --index-url https://download.pytorch.org/whl/cu130 torch torchvision
echo "--- ms-swift + deps ---"
"${UVP[@]}" "${SWIFT_SPEC}" "${TRANSFORMERS_SPEC}" "qwen_vl_utils>=0.0.14" decord \
  liger-kernel peft accelerate "huggingface_hub[hf_transfer]" tensorboard openai
echo "--- linear-attention kernels ---"
"${UVP[@]}" "flash-linear-attention>=0.4.2"
"${UVP[@]}" causal-conv1d --no-build-isolation \
  || { echo "causal-conv1d wheel failed; trying source build"; "${UVP[@]}" --no-binary causal-conv1d causal-conv1d --no-build-isolation; }

echo "--- import check (hard) ---"
"${PY}" - <<'EOF'
import importlib, sys
mods = ["torch", "transformers", "swift", "peft", "qwen_vl_utils", "decord", "liger_kernel", "fla", "causal_conv1d"]
bad = []
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"  ok {m} {getattr(mod, '__version__', '')}")
    except Exception as exc:  # noqa: BLE001
        bad.append((m, repr(exc)))
        print(f"  MISSING {m}: {exc}")
import torch
print("  cuda", torch.cuda.is_available(), torch.version.cuda)
if bad:
    sys.exit("setup_sft: missing modules -> " + ", ".join(m for m, _ in bad))
EOF
uv pip freeze --python "${PY}" > logs/sft/env_pins.txt
echo "SFT env ready: ${VENV_DIR}; pins -> logs/sft/env_pins.txt"
