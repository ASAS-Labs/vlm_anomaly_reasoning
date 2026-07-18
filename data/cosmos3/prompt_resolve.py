"""Prompt-line resolution shared by inverse-dynamics and the validation app."""

from __future__ import annotations

import re
from pathlib import Path


def last_sentence(text: str) -> str:
    text = text.strip()
    # Drop trailing parenthetical instructions, e.g. "(The last segment should
    # be at least 2 seconds long)" - validation wants the behavior sentence.
    while True:
        trimmed = re.sub(r"\s*\([^()]*\)\s*$", "", text)
        if trimmed == text or not trimmed:
            break
        text = trimmed
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts[-1] if parts else text


def resolve_prompt_file(video_dir_rel: Path, prompts_root: Path) -> Path | None:
    """Nearest prompt file for a video directory mirrored under prompts_root.

    Walks from the mirrored directory up to prompts_root. At each level the
    directory itself is tried and, for '<name>_variants' folders, the '<name>'
    sibling (variants share the base folder's prompt file). Within a directory
    updated_human_prompt.txt wins over prompt.txt.
    """
    current = prompts_root / video_dir_rel
    while True:
        candidates = [current]
        base_name = re.sub(r"_variants?$", "", current.name)
        if base_name != current.name:
            candidates.append(current.parent / base_name)
        for directory in candidates:
            for filename in ("updated_human_prompt.txt", "prompt.txt"):
                prompt_file = directory / filename
                if prompt_file.exists():
                    return prompt_file
        if current == prompts_root:
            return None
        current = current.parent


def prompt_sentence_for(rel_path: Path, prompts_root: Path) -> str | None:
    """Last sentence of line N of the nearest prompt file for a prompt_N video."""
    stem = re.sub(r"_v\d+$", "", rel_path.stem)  # trim variant suffix (prompt_3_v07)
    match = re.fullmatch(r"prompt_(\d+)", stem)
    if match is None:
        return None
    idx = int(match.group(1))
    prompt_file = resolve_prompt_file(rel_path.parent, prompts_root)
    if prompt_file is None:
        return None
    lines = prompt_file.read_text().splitlines()
    if idx >= len(lines):
        return None
    return last_sentence(lines[idx])
