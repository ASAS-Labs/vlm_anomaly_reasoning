#!/usr/bin/env python3
"""Merge a fixed-ID pass into the canonical records and publish v1 trajectories.

    python id_publish.py merge --raw outputs/id_full_raw.jsonl
        append records whose rel_path is not yet in outputs/id_raw.jsonl
    python id_publish.py publish [--dry-run] [--no-upload]
        write the v1_resample <stem>.txt / <stem>_10fps.txt of every clip into
        data/datasets/generated_vids (archiving the published v0 files under
        data/datasets/_superseded/v0_trajectories/) and push them all to the HF
        dataset in one commit, so the release is uniformly v1.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RAW = REPO / "outputs" / "id_raw.jsonl"
GEN_VIDS = REPO / "data" / "datasets" / "generated_vids"
V1 = REPO / "data" / "datasets" / "id_variants" / "v1_resample"
ARCHIVE = REPO / "data" / "datasets" / "_superseded" / "v0_trajectories"
HF_REPO, HF_REV = "ASASLab/av_semantic_anomalies", "main"


def cmd_merge(args):
    have = set()
    for ln in RAW.read_text().splitlines():
        if ln.strip():
            have.add(json.loads(ln)["rel_path"])
    added = 0
    with open(RAW, "a", encoding="utf-8") as out:
        for ln in Path(args.raw).read_text().splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r["rel_path"] in have:
                continue
            out.write(json.dumps(r) + "\n")
            have.add(r["rel_path"])
            added += 1
    print(f"merged {added} new records; id_raw now {len(have)} clips")


def cmd_publish(args):
    from utils import discover_eval_videos
    items = discover_eval_videos(GEN_VIDS)
    ops_src = []
    missing = []
    deletes = []
    for it in items:
        rel = it["rel_path"]
        stem = Path(rel).stem
        src5 = V1 / Path(rel).with_name(stem + ".txt")
        # native-rate sibling: _10fps.txt for 5 s clips, _7.5fps.txt for the
        # 21 long 8 s clips (derive_action_files names it by its true rate)
        natives = sorted((V1 / Path(rel).parent).glob(f"{stem}_*fps.txt"))
        if not src5.exists() or not natives:
            missing.append(rel)
            continue
        src10 = natives[0]
        dst5 = GEN_VIDS / Path(rel).with_name(stem + ".txt")
        dst10 = GEN_VIDS / Path(rel).with_name(src10.name)
        stale = GEN_VIDS / Path(rel).with_name(stem + "_10fps.txt")
        if src10.name != stale.name and stale.exists():
            # published v0 file at the wrong rate: archive + remove locally,
            # delete on HF
            arch = ARCHIVE / Path(rel).parent / stale.name
            arch.parent.mkdir(parents=True, exist_ok=True)
            if not arch.exists():
                shutil.copy2(stale, arch)
            if not args.dry_run:
                stale.unlink()
            deletes.append(str(Path(rel).with_name(stale.name)))
        for src, dst in ((src5, dst5), (src10, dst10)):
            if dst.exists() and src.read_text() != dst.read_text():
                arch = ARCHIVE / Path(rel).parent / dst.name
                arch.parent.mkdir(parents=True, exist_ok=True)
                if not arch.exists():
                    shutil.copy2(dst, arch)
            if not args.dry_run and (not dst.exists() or src.read_text() != dst.read_text()):
                shutil.copy2(src, dst)
            ops_src.append((dst, str(Path(rel).with_name(dst.name))))
    if missing:
        sys.exit(f"{len(missing)} clips lack v1 trajectories (run derive_action_files "
                 f"first), e.g. {missing[:3]}")
    print(f"{len(items)} clips, {len(ops_src)} trajectory files in place, "
          f"{len(deletes)} stale _10fps files to delete"
          f"{' (dry run)' if args.dry_run else ''}")
    if args.dry_run or args.no_upload:
        return
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi
    ops = [CommitOperationAdd(path_in_repo=p, path_or_fileobj=str(f)) for f, p in ops_src]
    ops += [CommitOperationDelete(path_in_repo=p) for p in deletes]
    HfApi().create_commit(repo_id=HF_REPO, repo_type="dataset", revision=HF_REV,
                          operations=ops,
                          commit_message="Fixed inverse-dynamics trajectories (v1: 10 fps "
                                         "resample, true time base, padding trim) for all "
                                         f"{len(items)} clips")
    print(f"uploaded {len(ops)} files to {HF_REPO}@{HF_REV}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sm = sub.add_parser("merge")
    sm.add_argument("--raw", required=True)
    sp = sub.add_parser("publish")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--no-upload", action="store_true")
    args = p.parse_args()
    {"merge": cmd_merge, "publish": cmd_publish}[args.cmd](args)


if __name__ == "__main__":
    main()
