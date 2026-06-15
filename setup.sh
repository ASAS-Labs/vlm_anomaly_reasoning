#!/usr/bin/env bash
# Install the system graphics libraries the Diffusers pipeline needs on headless
# servers, and point git at the committed hooks. Python dependencies and env
# vars are managed by uv.
#
# Usage:
#   ./setup.sh

set -euo pipefail

# Headless servers need these system graphics libraries for the pipeline import.
# Best effort: only attempt when running as root or with passwordless sudo.
install_system_libs() {
  local pkgs=(libxcb1 libgl1 libglib2.0-0)
  if ! command -v apt-get >/dev/null 2>&1; then
    return 0
  fi
  local sudo=""
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      sudo="sudo"
    else
      echo "Skipping system library install (need root). If you hit 'libxcb.so.1' errors, install: ${pkgs[*]}" >&2
      return 0
    fi
  fi
  echo "Installing system graphics libraries: ${pkgs[*]}"
  ${sudo} apt-get update -y || true
  ${sudo} apt-get install -y "${pkgs[@]}" || \
    echo "Warning: failed to install system libraries; install manually if imports fail: ${pkgs[*]}" >&2
}

# Point git at the version-controlled hooks so .githooks/pre-push (ruff lint)
# runs on every push from this clone. core.hooksPath is local config, so each
# fresh clone needs this once.
configure_git_hooks() {
  if ! command -v git >/dev/null 2>&1; then
    echo "Skipping git hooks setup: git not found." >&2
    return 0
  fi
  git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" config core.hooksPath .githooks
  echo "Configured git hooks path: .githooks (pre-push runs ruff)"
}

install_system_libs
configure_git_hooks
