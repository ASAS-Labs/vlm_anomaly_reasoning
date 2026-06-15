"""Prettify Cosmos3 prompt JSON files in a folder.

Raw upsampler output wraps the real prompt object in a top-level
``{"prompt": "<json string>"}``. This unwraps it (parses the inner JSON string)
and rewrites each file pretty-printed, leaving just the object.

Idempotent: files that are already unwrapped are simply re-formatted.

Usage:
    python prettify_prompts.py <folder>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def unwrap(data: object) -> object:
    """Return the inner prompt object, parsing the wrapped JSON string if present."""
    if isinstance(data, dict) and isinstance(data.get("prompt"), str):
        return json.loads(data["prompt"])
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Folder searched recursively for *.json files")
    args = parser.parse_args()

    paths = sorted(args.folder.rglob("*.json"))
    if not paths:
        raise SystemExit(f"No JSON files found under {args.folder}")

    for path in paths:
        obj = unwrap(json.loads(path.read_text()))
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
        print(f"prettified {path}")

    print(f"done ({len(paths)} file(s))")


if __name__ == "__main__":
    main()
