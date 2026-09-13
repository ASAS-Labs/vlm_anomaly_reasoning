#!/usr/bin/env python3
"""Laptop-side validation, reporting, installation and publishing for the taxonomy extension.

  validate --round N   flow probe + inverse-dynamics agreement -> extension_vids/validation.json
                       (round 1: every clip, writes the 5 Hz / 10 Hz trajectory txts;
                        round N>=2: scores the staged candidates of that round)
  report   --round N   counts, failing-clip table, next-round cost -> logs/extension/roundN_report.md
  targets  --round N   automatic==invalid clips -> logs/extension/roundN_targets.json
  install  --round N   accepted candidates replace the fixed-path clip (+txts); old files archived
  publish  [--dry-run] one HF commit: Extension/<rel>.{mp4,txt,_10fps.txt} + Extension/validation.json
  human                merge decisions.sqlite of the review app into validation.json (final verdicts)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from fidelity_report import video_matches_prompt  # noqa: E402
from id_semantics import check_match, evaluate_sequence  # noqa: E402
from id_trajectory import derive_variant  # noqa: E402

EXT = HERE / "video_gen_prompts" / "extension"
VIDS = REPO / "data" / "datasets" / "extension_vids"
LOGS = REPO / "logs" / "extension"
VAL = VIDS / "validation.json"
SUPERSEDED = REPO / "data" / "datasets" / "_superseded" / "extension"
HF_REPO, HF_REV, HF_PREFIX = "ASASLab/av_semantic_anomalies", "main", "Extension"
SEC_PER_CLIP, SEC_PER_ID_CLIP, USD_PER_HOUR = 36, 7, 4.0


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_val() -> dict:
    return json.loads(VAL.read_text()) if VAL.exists() else {"schema": 1, "clips": {}}


def save_val(v: dict) -> None:
    v["updated"] = now()
    text = json.dumps(v, indent=1, ensure_ascii=False) + "\n"
    VAL.parent.mkdir(parents=True, exist_ok=True)
    VAL.write_text(text)
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "validation.json").write_text(text)


def load_raw(path: Path) -> dict:
    raw = {}
    for ln in path.read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            raw[r["rel_path"]] = r
    return raw


def score_id(r: dict, e: dict):
    seq5, seq10 = derive_variant(r["poses"], r["input_fps"], r["n_valid_steps"] + 1, "v1_resample")
    stats = evaluate_sequence(seq5)
    ok, why = check_match({"speed": e["class"], "steer": bool(e["steer"])}, stats)
    return bool(ok), why, stats, seq5, seq10


def id_summary(ok, why, stats) -> dict:
    return {"agree": ok, "reasons": why,
            **{k: round(stats[k], 2) for k in ("start_v", "end_v", "v_final", "max_abs_heading") if k in stats}}


def flow_summary(v: dict, flow_ok) -> dict:
    return {"end_state": v["end_state"], "head_flow": round(v["head_flow"], 3), "tail_flow": round(v["tail_flow"], 3),
            "peak_flow": round(v["peak_flow"], 3), "prompt_video": flow_ok}


def automatic(flow_ok, id_ok) -> str:
    return "valid" if flow_ok in (True, None) and id_ok else "invalid"


def write_txts(rel: str, seq5, seq10) -> None:
    mp4 = VIDS / rel
    mp4.with_suffix(".txt").write_text(json.dumps(seq5) + "\n")
    mp4.with_name(f"{mp4.stem}_10fps.txt").write_text(json.dumps(seq10) + "\n")


def cand_manifest(rnd: int) -> Path:
    return REPO / "data" / "datasets" / "extension_candidates" / f"round{rnd}" / "manifest.json"


def cmd_validate(args) -> int:
    from video_motion import video_verdict
    exp = json.loads((EXT / "expectations.json").read_text())
    raw = load_raw(args.raw or REPO / "outputs" / f"extension_round{args.round}_raw.jsonl")
    val = load_val()
    if args.round == 1:
        clips = {c["k"]: c for c in json.loads((EXT / "manifest.json").read_text())["clips"]}
        for rel, e in exp.items():
            mp4 = VIDS / rel
            if not mp4.exists():
                print("missing clip:", rel)
                continue
            v = video_verdict(str(mp4), fps=24.0)
            flow_ok = video_matches_prompt(e["class"], {**v, "cls": e["class"]})
            r = raw.get(rel)
            if r is None:
                ok, why, stats = False, ["no ID record"], {}
            else:
                ok, why, stats, seq5, seq10 = score_id(r, e)
                write_txts(rel, seq5, seq10)
            row = clips[e["k"]]
            val["clips"][rel] = {
                "taxonomy_id": e["taxonomy_id"], "k": e["k"], "polarity": e["polarity"], "label": e["label"],
                "category": row["category"], "object": row["object"], "ood_context": row["ood_context"],
                "prompt_sentence": e["sentence"], "expectation": {"class": e["class"], "steer": e["steer"]},
                "flow": flow_summary(v, flow_ok), "id": id_summary(ok, why, stats),
                "attempts": [{"round": 1, "seed": 1234, "flow_ok": flow_ok, "id_ok": ok, "installed": True}],
                "installed_seed": 1234, "automatic": automatic(flow_ok, ok), "human": None, "final": None,
            }
        save_val(val)
        print(Counter(c["automatic"] for c in val["clips"].values()), "->", VAL)
        return 0
    mpath = cand_manifest(args.round)
    m = json.loads(mpath.read_text())
    acc = rej = 0
    for rel, rec in m.items():
        cand = next((a for a in rec["attempts"] if a.get("staged_round") == args.round and a["id_ok"] is None), None)
        r = raw.get(rel)
        if rec["accepted"] or cand is None or r is None:
            continue
        ok, why, stats, seq5, seq10 = score_id(r, exp[rel])
        cand.update(id_ok=ok, id_why=why, id_stats=id_summary(ok, why, stats), seq5=seq5, seq10=seq10)
        if ok:
            rec["accepted"] = cand["seed"]
            acc += 1
        else:
            rej += 1
        print(f"  {rel} s{cand['seed']}: ID {'agrees' if ok else 'DISAGREES'} ({why})")
    mpath.write_text(json.dumps(m, indent=1))
    print(f"round {args.round}: accepted {acc}, rejected {rej}, unresolved {sum(1 for r in m.values() if not r['accepted'])}")
    return 0


def cmd_install(args) -> int:
    mpath = cand_manifest(args.round)
    m = json.loads(mpath.read_text())
    val = load_val()
    n = 0
    for rel, rec in m.items():
        clip = val["clips"][rel]
        new = [a for a in rec["attempts"] if a.get("round") == args.round and not a.get("recorded")]
        for a in new:
            clip["attempts"].append({"round": args.round, "seed": a["seed"], "flow_ok": a["probe_ok"],
                                     "id_ok": a["id_ok"], "installed": a["seed"] == rec["accepted"]})
            a["recorded"] = True
        if not rec["accepted"] or rec.get("installed"):
            continue
        cand = next(a for a in rec["attempts"] if a["seed"] == rec["accepted"])
        arch = SUPERSEDED / f"before_round{args.round}" / rel
        arch.parent.mkdir(parents=True, exist_ok=True)
        mp4 = VIDS / rel
        for f in (mp4, mp4.with_suffix(".txt"), mp4.with_name(f"{mp4.stem}_10fps.txt")):
            if f.exists():
                shutil.copy2(f, arch.with_name(f.name))
        shutil.copy2(REPO / cand["path"], mp4)
        write_txts(rel, cand["seq5"], cand["seq10"])
        clip.update(installed_seed=cand["seed"], flow=flow_summary(cand["probe"], cand["probe_ok"]),
                    id={"agree": True, "reasons": [], **{k: v for k, v in cand["id_stats"].items() if k not in ("agree", "reasons")}},
                    automatic="valid")
        rec["installed"] = True
        n += 1
    mpath.write_text(json.dumps(m, indent=1))
    save_val(val)
    print(f"installed {n} regenerated clip(s); archives under {SUPERSEDED}")
    return 0


def cmd_targets(args) -> int:
    val = load_val()
    exp = json.loads((EXT / "expectations.json").read_text())
    targets = [{"rel_path": rel, "k": c["k"], "taxonomy_id": c["taxonomy_id"], "class": exp[rel]["class"],
                "steer": exp[rel]["steer"], "tried_seeds": [a["seed"] for a in c["attempts"]]}
               for rel, c in sorted(val["clips"].items()) if c["automatic"] == "invalid"]
    LOGS.mkdir(parents=True, exist_ok=True)
    out = LOGS / f"round{args.round}_targets.json"
    out.write_text(json.dumps(targets, indent=1))
    print(f"{len(targets)} target(s) -> {out}")
    return 0


def cmd_report(args) -> int:
    val = load_val()
    clips = val["clips"]
    fails = {r: c for r, c in clips.items() if c["automatic"] == "invalid"}
    lines = [f"# Extension round {args.round} report ({now()})", "",
             f"Clips: {len(clips)}; automatic valid {len(clips) - len(fails)}, invalid {len(fails)}", "",
             "| polarity | class | valid | invalid |", "|---|---|---|---|"]
    keys = sorted({(c["polarity"], c["expectation"]["class"]) for c in clips.values()}, key=str)
    for pol, cls in keys:
        sub = [c for c in clips.values() if c["polarity"] == pol and c["expectation"]["class"] == cls]
        lines.append(f"| {pol} | {cls} | {sum(c['automatic'] == 'valid' for c in sub)} | "
                     f"{sum(c['automatic'] == 'invalid' for c in sub)} |")
    why = Counter()
    for c in fails.values():
        if c["flow"]["prompt_video"] is False:
            why["flow probe contradicts prompt"] += 1
        if not c["id"]["agree"]:
            why["ID trajectory disagrees"] += 1
    lines += ["", "Failure witnesses: " + ", ".join(f"{k} {v}" for k, v in why.items() if k), "",
              "| clip | id | class | flow end | ID reasons | seeds tried |", "|---|---|---|---|---|---|"]
    for rel, c in sorted(fails.items()):
        lines.append(f"| {rel} | {c['taxonomy_id']} | {c['expectation']['class']} | {c['flow']['end_state']} | "
                     f"{'; '.join(c['id']['reasons'])} | {[a['seed'] for a in c['attempts']]} |")
    n = len(fails)
    best, worst = n * 1.6 * SEC_PER_CLIP, n * 4 * SEC_PER_CLIP
    idsec = n * SEC_PER_ID_CLIP + 600
    lines += ["", f"Next round (4 seeds/clip, {n} clips): generation {best / 60:.0f}-{worst / 60:.0f} min + ID ~{idsec / 60:.0f} min "
              f"= ${(best + idsec) / 3600 * USD_PER_HOUR:.1f}-{(worst + idsec) / 3600 * USD_PER_HOUR:.1f} at ${USD_PER_HOUR}/h (plus ~10 min instance setup)."]
    LOGS.mkdir(parents=True, exist_ok=True)
    out = LOGS / f"round{args.round}_report.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("->", out)
    return 0


def cmd_publish(args) -> int:
    val = load_val()
    ops = []
    for rel in sorted(val["clips"]):
        mp4 = VIDS / rel
        for f in (mp4, mp4.with_suffix(".txt"), mp4.with_name(f"{mp4.stem}_10fps.txt")):
            if f.exists():
                ops.append((f, f"{HF_PREFIX}/{f.relative_to(VIDS).as_posix()}"))
    ops.append((VAL, f"{HF_PREFIX}/validation.json"))
    print(f"{len(ops)} file operation(s) -> {HF_REPO}@{HF_REV}/{HF_PREFIX}/")
    if args.dry_run:
        for f, p in ops[:8]:
            print("  ", p)
        return 0
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import CommitOperationAdd, HfApi
    HfApi(token=os.environ.get("HF_TOKEN") or None).create_commit(
        repo_id=HF_REPO, repo_type="dataset", revision=HF_REV,
        operations=[CommitOperationAdd(path_in_repo=p, path_or_fileobj=str(f)) for f, p in ops],
        commit_message=args.message or f"Extension: {len(ops) - 1} clip files + validation manifest")
    print("published")
    return 0


def cmd_human(args) -> int:
    val = load_val()
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    dec = {rel: {"value": v, "validator": who, "ts": ts}
           for rel, v, who, ts in con.execute("SELECT rel_path, value, validator, ts FROM decisions")}
    disagree = []
    for rel, c in val["clips"].items():
        c["human"] = dec.get(rel)
        if c["human"] is None:
            c["final"] = None
            continue
        hv = c["human"]["value"] == "VALID"
        c["final"] = "valid" if hv and c["automatic"] == "valid" else "invalid"
        if hv != (c["automatic"] == "valid"):
            disagree.append((rel, c["automatic"], c["human"]["value"]))
    save_val(val)
    print("human decisions:", len(dec), "| final:", Counter(c["final"] for c in val["clips"].values()))
    for rel, a, h in disagree:
        print(f"  disagreement {rel}: automatic={a} human={h}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "report", "targets", "install"):
        p = sub.add_parser(name)
        p.add_argument("--round", type=int, required=True)
        if name == "validate":
            p.add_argument("--raw", type=Path)
    p = sub.add_parser("publish")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--message")
    p = sub.add_parser("human")
    p.add_argument("--db", type=Path, default=REPO / "data" / "extension_validation" / "decisions.sqlite")
    args = ap.parse_args()
    return {"validate": cmd_validate, "report": cmd_report, "targets": cmd_targets, "install": cmd_install,
            "publish": cmd_publish, "human": cmd_human}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
