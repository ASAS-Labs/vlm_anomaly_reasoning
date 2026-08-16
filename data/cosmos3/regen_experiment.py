#!/usr/bin/env python3
"""Regeneration experiment: can prompt timing fix stop-completion fidelity?

The fidelity report showed generation, not inverse dynamics, is why trajectories
disagree with prompts: most stop-scenario clips end while still braking. Inspecting
the failing dense prompts shows they demand physically implausible dynamics — a
complete stop from cruise inside ~1 second (neg_prompt_4: "stop by 0:02" braking
from 0:01; pos_prompt_9: decelerate 0:02-0:03). The paper's own generation guidance
says a smooth stop takes 2.5-4 s, so the generator renders sustained braking instead.

Two arms per scenario, N seeds each:
  orig    the released dense prompt, untouched
  strong  same scene, but a physics-feasible braking window (~2 s) ending well
          before the clip does, plus an emphatic locked-off stationary hold

Success measure: stop-completion rate per arm, judged by the optical-flow probe
(video_motion.py), which agrees with the ID pipeline at 98% on measurable clips.

    python regen_experiment.py --serve            # launch server + generate
    python regen_experiment.py --server-url ...   # attach to a running server
"""

import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROMPTS = HERE / "video_gen_prompts" / "final_semantic_scenarios"
DEFAULT_OUT = REPO / "data" / "datasets" / "regen_experiment"

MODEL_ID = "nvidia/Cosmos3-Nano"
WIDTH, HEIGHT, NUM_FRAMES, FPS = 832, 480, 121, 24
NUM_STEPS, GUIDANCE, SHIFT = 35, 6.0, 10.0
SEEDS = [1234, 5678, 9012]

SCENARIOS = {
    "neg_prompt_4": PROMPTS / "negative_scenarios/negative_scenarios_filtered/prompt_4.json",
    "pos_prompt_9": PROMPTS / "positive_scenarios/positive_scenarios_filtered/prompt_9.json",
}

# Physics-feasible rewrite of the motion timeline. Scene/subject/lighting fields are
# left untouched so the arms differ only in ego-motion timing and terminal stillness.
STRONG = {
    "neg_prompt_4": {
        "segments": [
            {"segment_index": 0, "time_range": "0:00-0:01",
             "description": "The ego vehicle moves forward at a moderate speed along the city road. Ahead, two small colorful balloons—one red, one yellow—rest still on the road surface in the calm air.",
             "key_changes": "Balloons resolve from small specks toward recognizable small objects as distance closes",
             "camera": "Steady forward-moving dashcam perspective, moderate speed"},
            {"segment_index": 1, "time_range": "0:01-0:03",
             "description": "The vehicle applies smooth, firm, continuous braking. Its speed decreases steadily through the entire two seconds and it reaches a complete standstill by 0:03, a few meters behind the balloons, treating the harmless balloons as obstacles.",
             "key_changes": "Speed falls steadily from moderate to exactly zero across two full seconds; the forward motion of the scene slows visibly frame by frame until it ceases entirely at 0:03",
             "camera": "Forward dashcam motion decelerating smoothly and continuously, coming to a complete rest at 0:03"},
            {"segment_index": 2, "time_range": "0:03-0:05",
             "description": "The vehicle is parked and completely stationary for the entire final two seconds. The camera does not translate at all: the framing is identical from 0:03 to 0:05, like a photograph. The two balloons sit motionless on the asphalt ahead; nothing in the scene moves.",
             "key_changes": "Zero motion of any kind; the frame is static and locked off; the road, buildings and balloons hold exactly the same position in frame",
             "camera": "Locked-off stationary camera, zero translation, zero vibration, as if mounted on a tripod in a parked car"},
        ],
        "actions": [
            {"time": "0:00-0:01", "description": "The ego vehicle travels forward along the city road at a moderate speed; two small balloons are visible ahead resting still on the road surface"},
            {"time": "0:01-0:03", "description": "The vehicle brakes smoothly and continuously, its speed falling steadily to a complete standstill by 0:03, treating the small resting balloons as obstacles"},
            {"time": "0:03-0:05", "description": "The vehicle is parked and perfectly stationary for the entire final two seconds; the camera does not move at all and the scene is completely static"},
        ],
        "temporal_caption": "At 0:00, the view from inside a vehicle shows a city road stretching ahead between mid-rise buildings, the vehicle moving forward at a moderate pace; two small colorful balloons—one red and one yellow—rest still on the road surface ahead. From 0:01 the vehicle brakes smoothly and continuously, its speed falling steadily. By 0:03 the vehicle has reached a complete standstill a few meters behind the balloons. From 0:03 to 0:05 the vehicle is parked and perfectly motionless: the camera does not translate at all, the framing is identical from 0:03 to 0:05 like a still photograph, and the balloons remain motionless on the road ahead.",
    },
    "pos_prompt_9": {
        "segments": [
            {"segment_index": 0, "time_range": "0:00-0:01.5",
             "description": "Ego vehicle drives forward down the straight city street, the mural wall growing larger ahead while parked cars and buildings pass on either side.",
             "key_changes": "Steady approach; wall increases in apparent size.",
             "camera": "Forward tracking motion at constant speed, eye-level."},
            {"segment_index": 1, "time_range": "0:01.5-0:03.5",
             "description": "The vehicle applies smooth, continuous, controlled braking as it recognizes the wall as a solid barrier rather than open road. Its speed decreases steadily through the full two seconds and it reaches a complete standstill by 0:03.5, well before the wall.",
             "key_changes": "Forward speed falls steadily to exactly zero across two full seconds; the mural fills more of the frame and then holds its size once motion ceases.",
             "camera": "Forward motion slowing smoothly and continuously to a complete rest at 0:03.5."},
            {"segment_index": 2, "time_range": "0:03.5-0:05",
             "description": "The vehicle is parked and completely stationary. The camera does not translate at all: the framing of the trompe-l'oeil mural is identical from 0:03.5 to 0:05, like a photograph. Nothing in the scene moves.",
             "key_changes": "Zero motion of any kind; the frame is static and locked off.",
             "camera": "Locked-off stationary camera, zero translation, zero vibration, as if on a tripod in a parked car."},
        ],
        "actions": [
            {"time": "0:00-0:01.5", "description": "The ego vehicle travels steadily forward down the city street toward the mural wall at the far end."},
            {"time": "0:01.5-0:03.5", "description": "The vehicle brakes smoothly and continuously, recognizing the solid wall painted to look like an open road, its speed falling steadily to a complete standstill by 0:03.5."},
            {"time": "0:03.5-0:05", "description": "The vehicle is parked and perfectly stationary before the wall; the camera does not move at all and the scene is completely static."},
        ],
        "temporal_caption": "At 0:00, the view from inside a vehicle shows a straight city street ending at a large wall painted with a hyper-realistic mural of an open road. From 0:01.5 the vehicle brakes smoothly and continuously, its speed falling steadily. By 0:03.5 the vehicle has reached a complete standstill well before the wall. From 0:03.5 to 0:05 the vehicle is parked and perfectly motionless: the camera does not translate at all and the framing of the mural is identical from 0:03.5 to 0:05, like a still photograph.",
    },
}


def build_prompts(out_dir: Path) -> list[dict]:
    jobs = []
    for scen, src in SCENARIOS.items():
        base = json.loads(src.read_text())
        strong = copy.deepcopy(base)
        for k, v in STRONG[scen].items():
            strong[k] = v
        for arm, payload in (("orig", base), ("strong", strong)):
            pdir = out_dir / "prompts"
            pdir.mkdir(parents=True, exist_ok=True)
            ppath = pdir / f"{scen}__{arm}.json"
            ppath.write_text(json.dumps(payload, indent=1))
            for seed in SEEDS:
                jobs.append({"scenario": scen, "arm": arm, "seed": seed,
                             "prompt_path": ppath,
                             "out": out_dir / scen / f"{arm}_s{seed}.mp4"})
    return jobs


def generate(job: dict, base_url: str, negative_prompt: str, extra_params: str):
    prompt_text = json.dumps(json.loads(job["prompt_path"].read_text()),
                             ensure_ascii=True, separators=(",", ":"))
    job["out"].parent.mkdir(parents=True, exist_ok=True)
    tmp = job["out"].with_suffix(".mp4.tmp")
    form = {
        "prompt": prompt_text, "negative_prompt": negative_prompt,
        "size": f"{WIDTH}x{HEIGHT}", "num_frames": str(NUM_FRAMES), "fps": str(FPS),
        "num_inference_steps": str(NUM_STEPS), "guidance_scale": str(GUIDANCE),
        "flow_shift": str(SHIFT), "seed": str(job["seed"]),
        "extra_params": extra_params,
    }
    cmd = ["curl", "-sS", "--fail-with-body", "-X", "POST",
           f"{base_url}/v1/videos/sync", "-H", "Accept: video/mp4"]
    for k, v in form.items():
        cmd += ["--form-string", f"{k}={v}"]
    cmd += ["-o", str(tmp)]
    r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"generation failed: {r.stdout}{r.stderr}"[:500])
    tmp.replace(job["out"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--server-url", default="http://localhost:8000")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dry-run", action="store_true",
                   help="write the arm prompts and the job manifest, no generation")
    args = p.parse_args()

    negative_prompt = json.dumps(
        json.loads((HERE / "text2video_neg_prompt.json").read_text()),
        ensure_ascii=True, separators=(",", ":"))
    # Must match generate_videos_vllm.py exactly; wrong keys are ignored and the
    # guardrail then blocks the driving-scenario prompt.
    extra_params = json.dumps(
        {"use_resolution_template": False, "use_duration_template": False,
         "guardrails": False}, separators=(",", ":"))

    jobs = build_prompts(args.out)
    if args.limit:
        jobs = jobs[: args.limit]
    manifest = [{**{k: str(v) if isinstance(v, Path) else v for k, v in j.items()}}
                for j in jobs]
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(jobs)} generation job(s); manifest at {args.out / 'manifest.json'}")
    if args.dry_run:
        return

    for i, job in enumerate(jobs, 1):
        if job["out"].exists():
            print(f"[{i}/{len(jobs)}] {job['out'].name} exists, skipping")
            continue
        t0 = time.time()
        generate(job, args.server_url, negative_prompt, extra_params)
        print(f"[{i}/{len(jobs)}] {job['scenario']}/{job['out'].name} "
              f"({time.time() - t0:.0f}s)", flush=True)
    print("REGEN DONE")


if __name__ == "__main__":
    sys.exit(main())
