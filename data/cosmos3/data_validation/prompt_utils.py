"""Prompt helpers for the validation app (re-exports shared resolution)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_SPEC = spec_from_file_location(
    "prompt_resolve",
    Path(__file__).resolve().parent.parent / "prompt_resolve.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("Could not load data/cosmos3/prompt_resolve.py")
_MOD = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

last_sentence = _MOD.last_sentence
prompt_sentence_for = _MOD.prompt_sentence_for
resolve_prompt_file = _MOD.resolve_prompt_file

__all__ = ["last_sentence", "prompt_sentence_for", "resolve_prompt_file"]
