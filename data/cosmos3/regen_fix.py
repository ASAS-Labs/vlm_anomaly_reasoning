#!/usr/bin/env python3
"""Closed-loop generation-fidelity repair (Part 5.4 / family C).

Clips whose prompt says one thing (usually: the ego vehicle stops) while the
generated video shows another are regenerated from a physics-feasible prompt
with best-of-N seeds, gated by the optical-flow probe and cross-checked by the
fixed inverse-dynamics pipeline, then installed in place and pushed to HF.

Subcommands (run in this order; each is idempotent/resumable):

  targets    full re-sweep: id_expectations x id_flow_verdicts_all315 (+ the
             historical 15-clip list) -> logs/regen_targets.json
  prompts    rewrite the stop-class targets' prompt JSONs in place: the ~1 s
             braking beat becomes a 2 s smooth stop + locked-off hold; scenery
             text of each variant is preserved (git is the archive)
  generate   best-of-N seeds per target against a running vLLM Omni server,
             flow-probe gate per attempt -> data/datasets/regen_candidates/
  stage      build a mirrored scratch tree (+10 fps resample + manifest) with
             one probe-passing candidate per target for the ID pass
  idcheck    score the ID pass (v1_resample trajectory vs frozen expectation);
             rejected candidates fall through to the next seed on re-stage
  install    archive originals, replace mp4 + v1 trajectories in
             data/datasets/generated_vids, upload to HF, refresh flow/fidelity
             files and print the downstream rebuild commands

    python regen_fix.py targets
    python regen_fix.py prompts
    python regen_fix.py generate --server-url http://localhost:8000
    python regen_fix.py stage --pass 1
    <run_inverse_dynamics.py ... --raw-out outputs/regen_pass1_raw.jsonl>
    python regen_fix.py idcheck --pass 1
    python regen_fix.py install
"""

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROMPTS = HERE / "video_gen_prompts"
GEN_VIDS = REPO / "data" / "datasets" / "generated_vids"
CANDIDATES = REPO / "data" / "datasets" / "regen_candidates"
SUPERSEDED = REPO / "data" / "datasets" / "_superseded"
TARGETS = REPO / "logs" / "regen_targets.json"
SUBSET_JSON = REPO / "logs" / "vlm_agreement_subset.json"
EXPECTATIONS = HERE / "id_expectations.json"
FLOW_ALL = REPO / "logs" / "id_flow_verdicts_all315.json"
FLOW_120 = REPO / "logs" / "id_flow_verdicts.json"
REGEN_LIST = REPO / "logs" / "id_regeneration_list.json"
MANIFEST = CANDIDATES / "manifest.json"
HF_REPO, HF_REV = "ASASLab/av_semantic_anomalies", "main"


def set_tag(tag: str | None):
    """Give a sweep its own targets/candidates/manifest (e.g. --tag s2)."""
    global CANDIDATES, TARGETS, MANIFEST, TAG
    TAG = tag
    if tag:
        CANDIDATES = REPO / "data" / "datasets" / f"regen_candidates_{tag}"
        TARGETS = REPO / "logs" / f"regen_targets_{tag}.json"
        MANIFEST = CANDIDATES / "manifest.json"

# Generation settings: identical to generate_videos_vllm.py (the dataset's).
NUM_STEPS, GUIDANCE, SHIFT = 35, 6.0, 10.0
EXTRA_PARAMS = json.dumps({"use_resolution_template": False,
                           "use_duration_template": False, "guardrails": False})
SEEDS = [5678, 9012, 3456, 7890, 2468, 1357, 8642, 9753]   # fresh seeds; 1234 = originals

BRAKE_RE = re.compile(r"\bbrak|decelerat|slow", re.I)
TAIL_RE = re.compile(r"(,?\s*(?:treating|recognizing|mistaking|reacting|as though|"
                     r"as if|because)[^.]*)", re.I)


# ---------------------------------------------------------------- helpers --
def scenario_of(rel: str) -> str:
    stem = rel.split("/")[-1].replace(".mp4", "")
    return ("neg" if "negative" in rel else "pos") + "_" + re.sub(r"_v\d+$", "", stem)


def load_targets():
    return json.loads(TARGETS.read_text())


def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def save_manifest(m):
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1))


def ffprobe_geometry(path: Path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=width,height,nb_read_frames,r_frame_rate",
         "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "frames": int(st["nb_read_frames"]), "fps": float(num) / float(den)}


def probe_ok(cls: str, verdict: dict):
    """Flow-probe acceptance for a candidate, mirroring fidelity_report."""
    from fidelity_report import video_matches_prompt
    return video_matches_prompt(cls, {**verdict, "cls": cls})


# ---------------------------------------------------------------- targets --
def cmd_targets(args):
    from fidelity_report import video_matches_prompt
    from build_agreement_subset import human_reject_sets
    exp = json.loads(EXPECTATIONS.read_text())
    flow = json.loads(FLOW_ALL.read_text())
    neg_rej, pos_rej, invalid_rel = human_reject_sets()
    rows = {}
    if args.id_disagree:
        # Sweep 2: clips the agreement builder excluded because the fixed-ID
        # trajectory contradicts the prompt class (generation-side defects the
        # flow probe cannot see, e.g. maintain clips that decelerate).
        d = json.loads(SUBSET_JSON.read_text())
        srows = d["clips"] if isinstance(d, dict) and "clips" in d else d
        for r in (srows.values() if isinstance(srows, dict) else srows):
            if r.get("status") != "excluded" or not r.get("reasons"):
                continue
            if not r["reasons"][0].startswith("id_disagrees"):
                continue
            rel = r["rel_path"]
            rows[rel] = {"rel_path": rel, "scenario": scenario_of(rel), "class": r["class"],
                         "steer": bool(exp[rel].get("steer")),
                         "tail_flow": flow.get(rel, {}).get("tail_flow"),
                         "id_reason": r["reasons"][0], "source": "id_disagree"}
        for rel, r in rows.items():
            name = rel.split("/")[-1]
            r["human_flagged"] = (name in (neg_rej if "negative" in rel else pos_rej)
                                  or rel in invalid_rel)
            r["geometry"] = ffprobe_geometry(GEN_VIDS / rel)
        ordered = sorted(rows.values(), key=lambda r: (r["class"], r["rel_path"]))
        TARGETS.write_text(json.dumps(ordered, indent=1))
        from collections import Counter
        print(f"{len(ordered)} ID-disagreement targets -> {TARGETS}")
        print("by class:", dict(Counter(r["class"] for r in ordered)))
        return
    for rel, e in exp.items():
        cls = e.get("class")
        fv = flow.get(rel)
        if cls is None or fv is None:
            continue
        if video_matches_prompt(cls, {**fv, "cls": cls}) is False:
            rows[rel] = {"rel_path": rel, "scenario": scenario_of(rel), "class": cls,
                         "steer": bool(e.get("steer")), "tail_flow": fv["tail_flow"],
                         "source": "sweep"}
    for x in json.loads(REGEN_LIST.read_text()):
        rows.setdefault(x["rel_path"], {"rel_path": x["rel_path"],
                                        "scenario": x["scenario"], "class": x["class"],
                                        "steer": bool(exp[x["rel_path"]].get("steer")),
                                        "tail_flow": x["tail_flow"], "source": "list15"})
        rows[x["rel_path"]]["source"] = "list15+sweep" if rows[x["rel_path"]]["source"] == "sweep" else rows[x["rel_path"]]["source"]
    for rel, r in rows.items():
        name = rel.split("/")[-1]
        r["human_flagged"] = (name in (neg_rej if "negative" in rel else pos_rej)
                              or rel in invalid_rel)
        r["geometry"] = ffprobe_geometry(GEN_VIDS / rel)
    # 15-list first (historical priority), then the rest, stable by path.
    ordered = sorted(rows.values(), key=lambda r: (r["source"] == "sweep", r["rel_path"]))
    TARGETS.write_text(json.dumps(ordered, indent=1))
    from collections import Counter
    print(f"{len(ordered)} targets -> {TARGETS}")
    print("by scenario:", dict(Counter(r["scenario"] for r in ordered)))
    print("by class:", dict(Counter(r["class"] for r in ordered)))
    print("human-flagged:", sum(r["human_flagged"] for r in ordered))


# ---------------------------------------------------------------- prompts --
def _t(sec: float) -> str:
    """0:01, 0:01.5, 0:03.5 formatting (matches the regen_experiment STRONG arm)."""
    whole = int(sec)
    frac = sec - whole
    return f"0:{whole:02d}" + (".5" if abs(frac - 0.5) < 1e-9 else "")


def _parse_range(s: str):
    a, b = s.split("-")
    def p(x):
        m, sec = x.split(":")
        return int(m) * 60 + float(sec)
    return p(a), p(b)


def _retime(beats, brake_idx, total=5.0, brake_len=2.0):
    """New (start, end) per beat: pre-brake beats compressed into [0, s'],
    brake = [s', s'+2], post-brake beats share [s'+2, total]."""
    s, _ = _parse_range(beats[brake_idx])
    s_new = min(s, 1.5)              # leave >= 1.5 s of stationary hold
    e_new = s_new + brake_len
    out = []
    pre = beats[:brake_idx]
    for i, _b in enumerate(pre):
        out.append((s_new * i / len(pre), s_new * (i + 1) / len(pre)))
    out.append((s_new, e_new))
    post = beats[brake_idx + 1:]
    for i, _b in enumerate(post):
        out.append((e_new + (total - e_new) * i / len(post),
                    e_new + (total - e_new) * (i + 1) / len(post)))
    return out


def feasible_timing(prompt: dict) -> dict | None:
    """Rewrite the infeasible ~1 s stop into a feasible 2 s stop + locked-off hold.

    Keeps every scene/lighting/subject field and the variant's own wording for
    the non-braking beats; replaces only the braking beat text, the final
    hold's motion text, camera_motion and the temporal caption. Returns None
    when the expected cruise/brake/hold structure is not found.
    """
    p = copy.deepcopy(prompt)
    acts, segs = p["actions"], p["segments"]
    bi_a = next((i for i, a in enumerate(acts) if BRAKE_RE.search(a["description"])), None)
    bi_s = next((i for i, s in enumerate(segs) if BRAKE_RE.search(s["description"])), None)
    if bi_a is None or bi_s is None or bi_a == len(acts) - 1 or bi_s == len(segs) - 1:
        return None
    tail_m = TAIL_RE.search(acts[bi_a]["description"])
    tail = tail_m.group(1).rstrip(".") if tail_m else ""

    new_a = _retime([a["time"] for a in acts], bi_a)
    new_s = _retime([s["time_range"] for s in segs], bi_s)
    b0, b1 = new_a[bi_a]
    hold = 5.0 - b1
    brake_desc = (f"The vehicle applies smooth, firm, continuous braking. Its speed "
                  f"decreases steadily through the entire two seconds and it reaches a "
                  f"complete standstill by {_t(b1)}{tail}.")
    brake_key = (f"Speed falls steadily from moderate to exactly zero across two full "
                 f"seconds; the forward motion of the scene slows visibly frame by frame "
                 f"until it ceases entirely at {_t(b1)}")
    brake_cam = (f"Forward dashcam motion decelerating smoothly and continuously, coming "
                 f"to a complete rest at {_t(b1)}")
    hold_desc = (f" The camera does not translate at all: the framing is identical from "
                 f"{_t(b1)} to 0:05, like a photograph; nothing in the scene moves.")
    hold_key = ("Zero motion of any kind; the frame is static and locked off; "
                "everything holds exactly the same position in frame")
    hold_cam = ("Locked-off stationary camera, zero translation, zero vibration, as if "
                "mounted on a tripod in a parked car")

    for i, a in enumerate(acts):
        a["time"] = f"{_t(new_a[i][0])}-{_t(new_a[i][1])}"
    acts[bi_a]["description"] = brake_desc
    for i in range(bi_a + 1, len(acts)):
        d = re.sub(r"(final|entire|last) (three|two|one) seconds?",
                   f"final {hold:g} seconds", acts[i]["description"])
        acts[i]["description"] = (d.rstrip(".") + "; the vehicle is parked and perfectly "
                                  "stationary and the camera does not move at all.")
    for i, s in enumerate(segs):
        s["time_range"] = f"{_t(new_s[i][0])}-{_t(new_s[i][1])}"
    segs[bi_s]["description"] = brake_desc
    segs[bi_s]["key_changes"] = brake_key
    segs[bi_s]["camera"] = brake_cam
    for i in range(bi_s + 1, len(segs)):
        d = re.sub(r"(final|entire|last) (three|two|one) seconds?",
                   f"final {hold:g} seconds", segs[i]["description"])
        segs[i]["description"] = d.rstrip(".") + "." + hold_desc
        segs[i]["key_changes"] = hold_key
        segs[i]["camera"] = hold_cam
    p["cinematography"]["camera_motion"] = (
        "Forward-moving dashcam perspective at a moderate speed that brakes smoothly "
        f"and continuously over two full seconds to a complete stop at {_t(b1)}, then "
        "holds completely static and locked off with no movement of any kind")
    first = acts[0]["description"].rstrip(".")
    p["temporal_caption"] = (
        f"At 0:00, {first[0].lower() + first[1:]}. From {_t(b0)} the vehicle brakes "
        f"smoothly and continuously, its speed falling steadily{tail}. By {_t(b1)} the "
        f"vehicle has reached a complete standstill. From {_t(b1)} to 0:05 the vehicle "
        f"is parked and perfectly motionless: the camera does not translate at all and "
        f"the framing is identical, like a still photograph.")
    return p


_NO_BRAKE = (" The vehicle never brakes or slows at any point: its speed is constant "
             "from the first frame to the last and it keeps moving steadily through the "
             "end of the clip.")


_PULL_AWAY = (" The vehicle, stationary at first, then pulls away and keeps accelerating "
              "smoothly through the final frame; once moving it does not slow or stop "
              "again before the clip ends.")


def accelerate_reinforce(prompt: dict) -> dict:
    """Start-from-stop scenarios whose clips never really get going: state the
    pull-away and the sustained motion explicitly in every motion field."""
    p = copy.deepcopy(prompt)
    for a in p["actions"]:
        a["description"] = a["description"].rstrip(".") + "." + _PULL_AWAY
    for sg in p["segments"]:
        sg["description"] = sg["description"].rstrip(".") + "." + _PULL_AWAY
    p["cinematography"]["camera_motion"] = (
        p["cinematography"]["camera_motion"].rstrip(".") + "; after pulling away the "
        "forward motion keeps building and never slows before the final frame")
    p["temporal_caption"] = p["temporal_caption"].rstrip(".") + "." + _PULL_AWAY
    return p


def maintain_reinforce(prompt: dict) -> dict:
    """For maintain-class prompts the generator still brakes for objects in the
    lane; state the no-braking constraint explicitly in every motion field."""
    p = copy.deepcopy(prompt)
    for a in p["actions"]:
        a["description"] = a["description"].rstrip(".") + "." + _NO_BRAKE
    for sg in p["segments"]:
        sg["description"] = sg["description"].rstrip(".") + "." + _NO_BRAKE
        sg["camera"] = (sg["camera"].rstrip(".") + "; forward motion continues at constant "
                        "speed with no deceleration")
    p["cinematography"]["camera_motion"] = (
        p["cinematography"]["camera_motion"].rstrip(".") + "; the vehicle never brakes "
        "or slows, holding a constant speed through the final frame")
    p["temporal_caption"] = p["temporal_caption"].rstrip(".") + "." + _NO_BRAKE
    return p


def cmd_prompts(args):
    targets = load_targets()
    changes = []
    for t in targets:
        jpath = PROMPTS / t["rel_path"].replace(".mp4", ".json")
        before = json.loads(jpath.read_text())
        if t["class"] in ("maintain", "accelerate"):
            if before.get("_regen_fix"):
                changes.append({"rel_path": t["rel_path"], "action": "already_fixed"})
                continue
            fn = maintain_reinforce if t["class"] == "maintain" else accelerate_reinforce
            after = fn(before)
            after["_regen_fix"] = {f"{t['class']}_reinforce": True,
                                   "ts": datetime.now().isoformat(timespec="seconds")}
            if not args.dry_run:
                jpath.write_text(json.dumps(after, indent=2, ensure_ascii=False) + "\n")
            changes.append({"rel_path": t["rel_path"], "action": "reinforced"})
            continue
        if t["class"] != "stop":
            changes.append({"rel_path": t["rel_path"], "action": "unchanged",
                            "reason": f"class {t['class']}: regenerate as-is"})
            continue
        if before.get("_regen_fix"):
            changes.append({"rel_path": t["rel_path"], "action": "already_fixed"})
            continue
        after = feasible_timing(before)
        if after is None:
            changes.append({"rel_path": t["rel_path"], "action": "manual",
                            "reason": "beat structure not recognised"})
            continue
        after["_regen_fix"] = {"feasible_timing": True, "ts": datetime.now().isoformat(timespec="seconds"),
                               "old_times": [a["time"] for a in before["actions"]],
                               "new_times": [a["time"] for a in after["actions"]]}
        if not args.dry_run:
            jpath.write_text(json.dumps(after, indent=2, ensure_ascii=False) + "\n")
        changes.append({"rel_path": t["rel_path"], "action": "rewritten",
                        "old_times": after["_regen_fix"]["old_times"],
                        "new_times": after["_regen_fix"]["new_times"]})
    out = REPO / "logs" / "regen_prompt_changes.json"
    out.write_text(json.dumps(changes, indent=1))
    from collections import Counter
    print(dict(Counter(c["action"] for c in changes)), "->", out)
    if args.dry_run:
        t = next(c for c in changes if c["action"] == "rewritten")
        j = feasible_timing(json.loads((PROMPTS / t["rel_path"].replace(".mp4", ".json")).read_text()))
        print(json.dumps({k: j[k] for k in ("actions", "segments", "temporal_caption")}, indent=1)[:3000])


# --------------------------------------------------------------- generate --
def cmd_generate(args):
    from video_motion import video_verdict
    targets = load_targets()
    m = load_manifest()
    neg_prompt = (HERE / "text2video_neg_prompt.json").read_text().strip()
    n_gen = 0
    for t in targets:
        rel = t["rel_path"]
        rec = m.setdefault(rel, {"class": t["class"], "attempts": [], "accepted": None})
        if rec["accepted"]:
            continue
        if rec.get("probe_pass_pending") and not args.more:
            continue  # has a probe-passing candidate awaiting ID; don't spend more
        prompt_text = json.dumps(json.loads((PROMPTS / rel.replace(".mp4", ".json")).read_text()),
                                 separators=(",", ":"), ensure_ascii=False)
        g = t["geometry"]
        tried = {a["seed"] for a in rec["attempts"]}
        for seed in SEEDS[: args.max_seeds]:
            if seed in tried:
                continue
            out = CANDIDATES / rel.replace(".mp4", f"__s{seed}.mp4")
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".mp4.tmp")
            form = {"prompt": prompt_text, "negative_prompt": neg_prompt,
                    "size": f"{g['width']}x{g['height']}", "num_frames": str(g["frames"]),
                    "fps": str(int(round(g["fps"]))), "num_inference_steps": str(NUM_STEPS),
                    "guidance_scale": str(GUIDANCE), "flow_shift": str(SHIFT),
                    "seed": str(seed), "extra_params": EXTRA_PARAMS}
            cmd = ["curl", "-sS", "--fail-with-body", "-X", "POST",
                   f"{args.server_url}/v1/videos/sync", "-H", "Accept: video/mp4"]
            for k, v in form.items():
                cmd += ["--form-string", f"{k}={v}"]
            cmd += ["-o", str(tmp)]
            r = subprocess.run(cmd, text=True, capture_output=True)
            if r.returncode != 0:
                tmp.unlink(missing_ok=True)
                print(f"  {rel} s{seed}: request failed: {r.stderr[:200]}", flush=True)
                continue
            tmp.replace(out)
            v = video_verdict(str(out), fps=g["fps"])
            ok = probe_ok(t["class"], v)
            rec["attempts"].append({"seed": seed, "path": str(out.relative_to(REPO)),
                                    "probe": v, "probe_ok": ok, "id_ok": None})
            n_gen += 1
            print(f"  {rel.split('/')[-1]} s{seed}: end={v['end_state']} "
                  f"tail={v['tail_flow']:.3f} -> {'PASS' if ok else 'fail'}", flush=True)
            save_manifest(m)
            if ok:
                rec["probe_pass_pending"] = True
                break
    save_manifest(m)
    passing = sum(1 for r in m.values() if any(a["probe_ok"] for a in r["attempts"]))
    print(f"generated {n_gen}; targets with a probe-passing candidate: {passing}/{len(targets)}")


# ------------------------------------------------------------ stage/idcheck --
TAG = None


def _pass_dirs(k):
    base = f"regen_{TAG}_pass{k}" if TAG else f"regen_pass{k}"
    root = REPO / "data" / "datasets" / base
    return root, root.parent / f"{base}_10fps"


def _next_candidate(rec):
    """Next candidate for the ID cross-check: probe-confirmed first, else an
    unmeasurable-but-stopped-level candidate (low-texture scenes) for stop class."""
    cand = next((a for a in rec["attempts"] if a["probe_ok"] and a["id_ok"] is None), None)
    if cand is None and rec["class"] == "stop":
        # Probe could not decide (ambiguous band or low-texture unmeasurable);
        # let the ID cross-check adjudicate the most-stopped-looking candidate.
        pool = [a for a in rec["attempts"]
                if a["probe_ok"] is None and a["id_ok"] is None
                and a["probe"]["end_state"] in ("ambiguous", "unmeasurable")
                and a["probe"]["tail_flow"] < 0.30]
        cand = min(pool, key=lambda a: a["probe"]["tail_flow"]) if pool else None
    return cand


def cmd_stage(args):
    m = load_manifest()
    root, root10 = _pass_dirs(args.pass_no)
    clips = []
    for rel, rec in m.items():
        if rec["accepted"]:
            continue
        cand = _next_candidate(rec)
        if cand is None:
            continue
        src = REPO / cand["path"]
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        dst10 = root10 / rel
        dst10.parent.mkdir(parents=True, exist_ok=True)
        if not dst10.exists():
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(dst),
                            "-vf", "fps=10", "-an", "-c:v", "libx264", "-crf", "12",
                            "-preset", "veryfast", str(dst10)], check=True)
        g = ffprobe_geometry(dst10)
        clips.append({"rel_path": rel, "out_fps": 10, "out_frames": g["frames"],
                      "seed": cand["seed"], "src_frames": ffprobe_geometry(dst)["frames"]})
        rec["staged_pass"] = args.pass_no
    save_manifest(m)
    (root10 / "resample_manifest.json").write_text(json.dumps(
        {"fps": 10, "src": str(root), "clips": clips}, indent=1))
    print(f"staged {len(clips)} candidate(s) in {root10}")
    base = f"regen_{TAG}_pass{args.pass_no}" if TAG else f"regen_pass{args.pass_no}"
    print("next:\n  python data/cosmos3/run_inverse_dynamics.py "
          f"--videos-root {root10} --manifest {root10}/resample_manifest.json "
          f"--raw-out outputs/{base}_raw.jsonl")


def cmd_idcheck(args):
    from id_semantics import check_match, evaluate_sequence
    from id_trajectory import derive_variant
    exp = json.loads(EXPECTATIONS.read_text())
    m = load_manifest()
    raw = {}
    for ln in Path(args.raw).read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            raw[r["rel_path"]] = r
    acc = rej = 0
    for rel, rec in m.items():
        if rec.get("staged_pass") != args.pass_no or rec["accepted"]:
            continue
        cand = _next_candidate(rec)
        r = raw.get(rel)
        if cand is None or r is None:
            print(f"  {rel}: no raw ID record in pass {args.pass_no}")
            continue
        seq5, seq10 = derive_variant(r["poses"], r["input_fps"], r["n_valid_steps"] + 1,
                                     "v1_resample")
        e = exp[rel]
        ok, why = check_match({"speed": e["class"], "steer": bool(e.get("steer"))},
                              evaluate_sequence(seq5))
        cand["id_ok"] = bool(ok)
        cand["id_why"] = why
        cand["raw_record"] = r
        cand["seq5"], cand["seq10"] = seq5, seq10
        if ok:
            rec["accepted"] = cand["seed"]
            rec.pop("probe_pass_pending", None)
            acc += 1
        else:
            rec.pop("probe_pass_pending", None)
            rej += 1
        print(f"  {rel.split('/')[-1]} s{cand['seed']}: ID {'agrees' if ok else 'DISAGREES'} ({why})")
    save_manifest(m)
    pending = [rel for rel, rec in m.items() if not rec["accepted"]]
    print(f"accepted {acc}, rejected {rej}; still unresolved: {len(pending)}")
    if pending:
        print("next: python regen_fix.py generate --more ... (more seeds), then stage --pass N+1")


# ---------------------------------------------------------------- install --
def cmd_install(args):
    from huggingface_hub import CommitOperationAdd, HfApi
    from video_motion import video_verdict
    m = load_manifest()
    accepted = {rel: rec for rel, rec in m.items() if rec["accepted"]}
    if not accepted:
        sys.exit("nothing accepted yet")
    flow_all = json.loads(FLOW_ALL.read_text())
    flow_120 = json.loads(FLOW_120.read_text()) if FLOW_120.exists() else None
    raw_path = REPO / "outputs" / "id_raw.jsonl"
    raw_recs = [json.loads(ln) for ln in raw_path.read_text().splitlines() if ln.strip()]
    ops, installed = [], []
    for rel, rec in accepted.items():
        cand = next(a for a in rec["attempts"] if a["seed"] == rec["accepted"])
        dst = GEN_VIDS / rel
        stem_txt = dst.with_suffix(".txt")
        stem_10 = dst.with_name(dst.stem + "_10fps.txt")
        # archive the originals (mp4 + both trajectory files)
        arch = SUPERSEDED / rel
        arch.parent.mkdir(parents=True, exist_ok=True)
        if not arch.exists():
            for src in (dst, stem_txt, stem_10):
                if src.exists():
                    shutil.copy2(src, arch.parent / src.name)
        if not args.dry_run:
            shutil.copy2(REPO / cand["path"], dst)
            stem_txt.write_text(json.dumps(cand["seq5"]) + "\n")
            stem_10.write_text(json.dumps(cand["seq10"]) + "\n")
            # refresh probe verdicts on the installed file
            v = video_verdict(str(dst), fps=24.0)
            flow_all[rel] = {**flow_all.get(rel, {}), **v}
            if flow_120 is not None and rel in flow_120:
                # fidelity_report reads id_v_final from this file: refresh it
                # from the new v1 trajectory too, not just the probe fields.
                flow_120[rel] = {**flow_120[rel], **v,
                                 "id_v_final": round(cand["seq5"][-1][0], 4)}
            # replace the raw ID record
            raw_recs = [r for r in raw_recs if r["rel_path"] != rel] + [cand["raw_record"]]
        for local, name in ((dst, dst.name), (stem_txt, stem_txt.name), (stem_10, stem_10.name)):
            ops.append(CommitOperationAdd(path_in_repo=str(Path(rel).parent / name),
                                          path_or_fileobj=str(local)))
        installed.append(rel)
        print(f"  installed {rel} (seed {rec['accepted']})")
    if args.dry_run:
        print(f"dry run: {len(installed)} clip(s) would be installed, {len(ops)} files uploaded")
        return
    FLOW_ALL.write_text(json.dumps(flow_all, indent=1))
    if flow_120 is not None:
        FLOW_120.write_text(json.dumps(flow_120, indent=1))
    raw_path.write_text("".join(json.dumps(r) + "\n" for r in raw_recs))
    if not args.no_upload:
        api = HfApi()
        api.create_commit(repo_id=HF_REPO, repo_type="dataset", revision=HF_REV,
                          operations=ops,
                          commit_message=f"Regenerate {len(installed)} clips with "
                                         f"physics-feasible timing (flow-probe + ID gated)")
        print(f"uploaded {len(ops)} files to {HF_REPO}@{HF_REV}")
    (REPO / "logs" / "regen_installed.json").write_text(json.dumps(
        {"ts": datetime.now().isoformat(timespec="seconds"), "installed": installed,
         "seeds": {rel: accepted[rel]["accepted"] for rel in installed}}, indent=1))
    print(f"{len(installed)} clip(s) installed. Downstream rebuild:\n"
          "  python data/cosmos3/fidelity_report.py --flow logs/id_flow_verdicts.json "
          "--out logs/id_fidelity_report.json --regen-out logs/id_regeneration_list.json\n"
          "  python data/cosmos3/derive_action_files.py --raw outputs/id_raw.jsonl --variants v1_resample\n"
          "  python data/cosmos3/build_agreement_subset.py")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tag", default=None,
                   help="sweep tag: separate targets/candidates/manifest (e.g. s2)")
    sub = p.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("targets")
    st.add_argument("--id-disagree", action="store_true",
                    help="targets = agreement-subset exclusions whose first reason is "
                         "id_disagrees (sweep 2)")
    sp = sub.add_parser("prompts")
    sp.add_argument("--dry-run", action="store_true")
    sg = sub.add_parser("generate")
    sg.add_argument("--server-url", default="http://localhost:8000")
    sg.add_argument("--max-seeds", type=int, default=4)
    sg.add_argument("--more", action="store_true",
                    help="also try further seeds for targets whose candidate is pending ID")
    ss = sub.add_parser("stage")
    ss.add_argument("--pass", dest="pass_no", type=int, required=True)
    si = sub.add_parser("idcheck")
    si.add_argument("--pass", dest="pass_no", type=int, required=True)
    si.add_argument("--raw", default=None)
    sn = sub.add_parser("install")
    sn.add_argument("--dry-run", action="store_true")
    sn.add_argument("--no-upload", action="store_true")
    args = p.parse_args()
    set_tag(args.tag)
    if args.cmd == "idcheck" and args.raw is None:
        base = f"regen_{args.tag}_pass{args.pass_no}" if args.tag else f"regen_pass{args.pass_no}"
        args.raw = str(REPO / "outputs" / f"{base}_raw.jsonl")
    {"targets": cmd_targets, "prompts": cmd_prompts, "generate": cmd_generate,
     "stage": cmd_stage, "idcheck": cmd_idcheck, "install": cmd_install}[args.cmd](args)


if __name__ == "__main__":
    main()
