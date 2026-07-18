"""Prompt helpers for the validation app (re-exports shared resolution)."""

from __future__ import annotations

import sys
from pathlib import Path

_COSMOS3_DIR = Path(__file__).resolve().parent.parent
if str(_COSMOS3_DIR) not in sys.path:
    sys.path.insert(0, str(_COSMOS3_DIR))

from prompt_resolve import last_sentence, prompt_sentence_for, resolve_prompt_file

__all__ = ["last_sentence", "prompt_sentence_for", "resolve_prompt_file"]
