#!/usr/bin/env python3
"""Download only the evaluation subset of av_semantic_anomalies.

The four eval folders (315 clips + their action .txt files), not the full 339-clip
repo. Patterns are derived from utils.EVAL_FOLDERS so the download and the discovery
used at inference time cannot drift apart.

    python data/cosmos3/fetch_eval_dataset.py [--local_dir PATH]
"""

import argparse
import os
from pathlib import Path

# Must precede the huggingface_hub import (matches generate_videos_vllm.py).
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

from huggingface_hub import snapshot_download  # noqa: E402

from utils import EVAL_FOLDERS, discover_eval_videos  # noqa: E402

HF_DATASET_REPO = "ASASLab/av_semantic_anomalies"
HF_REVISION = "main"
DEFAULT_LOCAL_DIR = Path(__file__).resolve().parents[2] / "data" / "datasets" / "generated_vids"


def main():
    p = argparse.ArgumentParser(description="Fetch the eval subset of the dataset")
    p.add_argument("--local_dir", type=Path, default=DEFAULT_LOCAL_DIR)
    p.add_argument("--revision", default=HF_REVISION)
    args = p.parse_args()

    patterns = [f"{folder}/*" for folder in EVAL_FOLDERS]
    print(f"downloading {HF_DATASET_REPO}@{args.revision} -> {args.local_dir}")
    for pat in patterns:
        print(f"  {pat}")

    snapshot_download(
        repo_id=HF_DATASET_REPO,
        repo_type="dataset",
        revision=args.revision,
        local_dir=str(args.local_dir),
        allow_patterns=patterns,
        token=os.environ.get("HF_TOKEN") or None,
    )

    # Fail here, before any GPU time is spent, if the subset is not what we expect.
    items = discover_eval_videos(args.local_dir)
    missing = [i["rel_path"] for i in items
               if not i["abs_path"].with_name(i["abs_path"].stem + ".txt").exists()]
    if missing:
        raise SystemExit(
            f"{len(missing)} video(s) have no 5Hz action file, e.g. {missing[:3]}"
        )

    n_anom = sum(1 for i in items if i["true_label"] == 1)
    size_gb = sum(i["abs_path"].stat().st_size for i in items) / 1e9
    print(f"\nok: {len(items)} videos ({n_anom} anomaly / {len(items) - n_anom} normal), "
          f"{sum(1 for i in items if i['on_skip_list'])} skip-listed, "
          f"{size_gb:.2f} GB of video")


if __name__ == "__main__":
    main()
