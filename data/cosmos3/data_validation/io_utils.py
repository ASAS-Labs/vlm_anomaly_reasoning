"""I/O helpers for the inverse-dynamics validation Streamlit app."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pandas as pd

CSV_COLUMNS = [
    'Video filepath relative to "data/datasets/generated_vids"',
    "Valid/Invalid",
    "Heuristic Validation",
    "Comment",
]
COL_PATH, COL_LABEL, COL_HEURISTIC, COL_COMMENT = CSV_COLUMNS

FLAG_LINE_RE = re.compile(r"^FLAG\s+(?P<path>.+?):(?P<rest>\s*.*)$")


def find_repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / ".git").exists() or (path / "packages" / "cosmos-framework").exists():
            return path
    return start


def resolve_under_root(root: Path, folder_rel: str) -> Path | None:
    """Resolve folder_rel under root; return None if it escapes root or missing."""
    folder_rel = folder_rel.strip().strip("/").replace("\\", "/")
    if folder_rel in ("", "."):
        target = root.resolve()
    else:
        if ".." in Path(folder_rel).parts:
            return None
        target = (root / folder_rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    if not target.is_dir():
        return None
    return target


def discover_videos(folder: Path, generated_vids_root: Path) -> list[Path]:
    """Recursive *.mp4 paths relative to generated_vids_root, sorted."""
    root = generated_vids_root.resolve()
    videos = sorted(folder.resolve().rglob("*.mp4"))
    rels: list[Path] = []
    for video in videos:
        try:
            rels.append(video.relative_to(root))
        except ValueError:
            continue
    return rels


def list_browsable_folders(generated_vids_root: Path) -> list[str]:
    """Relative folder paths under root that contain at least one .mp4 (recursive)."""
    root = generated_vids_root.resolve()
    folders: set[str] = set()
    if not root.is_dir():
        return []
    for mp4 in root.rglob("*.mp4"):
        try:
            rel = mp4.parent.relative_to(root)
        except ValueError:
            continue
        # Include this folder and all ancestors under root.
        parts = rel.parts
        for i in range(len(parts) + 1):
            if i == 0:
                folders.add(".")
            else:
                folders.add(Path(*parts[:i]).as_posix())
    # Prefer concrete scenario folders; drop bare "." if other options exist.
    ordered = sorted(folders)
    if "." in ordered and len(ordered) > 1:
        ordered = [p for p in ordered if p != "."]
    return ordered


def trajectory_path(video_abs: Path, mode: str) -> Path:
    if mode == "full_fps":
        return video_abs.with_name(f"{video_abs.stem}_10fps.txt")
    return video_abs.with_suffix(".txt")


def load_trajectory(path: Path) -> tuple[list[list[float]] | None, str | None]:
    """Return (sequence, error_message). sequence is [[v, h], ...]."""
    if not path.is_file():
        return None, f"Missing trajectory file: {path}"
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Unreadable trajectory file {path}: {exc}"
    if not isinstance(data, list) or not data:
        return None, f"Empty or invalid trajectory list in {path}"
    try:
        seq = [[float(row[0]), float(row[1])] for row in data]
    except (TypeError, ValueError, IndexError) as exc:
        return None, f"Invalid trajectory rows in {path}: {exc}"
    return seq, None


def hz_for_mode(mode: str) -> float:
    return 10.0 if mode == "full_fps" else 5.0


def load_skip_filenames(path: Path) -> set[str]:
    """Load a one-filename-per-line skip list (blank lines ignored)."""
    if not path.is_file():
        return set()
    names: set[str] = set()
    for line in path.read_text().splitlines():
        name = line.strip()
        if name:
            names.add(name)
    return names


def parse_flags_file(flags_path: Path) -> dict[str, str]:
    """Map relative video path -> remainder of FLAG line (after the colon)."""
    out: dict[str, str] = {}
    if not flags_path.is_file():
        return out
    for line in flags_path.read_text().splitlines():
        match = FLAG_LINE_RE.match(line.strip())
        if match is None:
            continue
        rel = match.group("path").strip().replace("\\", "/")
        out[rel] = match.group("rest").strip()
    return out


def empty_csv() -> pd.DataFrame:
    return pd.DataFrame(columns=CSV_COLUMNS)


def load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.is_file() or csv_path.stat().st_size == 0:
        return empty_csv()
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[CSV_COLUMNS]


def lookup_row(df: pd.DataFrame, rel_posix: str) -> dict[str, str] | None:
    if df.empty:
        return None
    hits = df[df[COL_PATH] == rel_posix]
    if hits.empty:
        return None
    row = hits.iloc[-1]
    return {
        COL_PATH: str(row[COL_PATH]),
        COL_LABEL: str(row[COL_LABEL]),
        COL_HEURISTIC: str(row[COL_HEURISTIC]),
        COL_COMMENT: str(row[COL_COMMENT]),
    }


def upsert_csv(
    csv_path: Path,
    df: pd.DataFrame,
    rel_posix: str,
    label: str,
    heuristic: str,
    comment: str,
) -> pd.DataFrame:
    """Overwrite existing row for rel_posix or append; atomic write to disk."""
    row = {
        COL_PATH: rel_posix,
        COL_LABEL: label,
        COL_HEURISTIC: heuristic,
        COL_COMMENT: comment,
    }
    if df.empty:
        new_df = pd.DataFrame([row], columns=CSV_COLUMNS)
    else:
        mask = df[COL_PATH] == rel_posix
        if mask.any():
            new_df = df.copy()
            for key, value in row.items():
                new_df.loc[mask, key] = value
        else:
            new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=csv_path.parent,
        delete=False,
        suffix=".csv.tmp",
    ) as tmp:
        new_df.to_csv(tmp, index=False)
        tmp_path = Path(tmp.name)
    tmp_path.replace(csv_path)
    return new_df
