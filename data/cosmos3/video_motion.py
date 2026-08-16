"""Model-free ego-motion probe: per-frame optical-flow speed proxy from pixels.

Purpose: an independent instrument for judging what a generated clip actually
depicts, so ID-pipeline error can be separated from video-generation infidelity.

Why median flow over the road region: ego motion moves *every* background pixel,
while scene objects (pedestrians, swaying balloons) move a minority. The median
over the bottom 60% of the frame (road + near world, excluding low-texture sky)
is therefore robust to moving objects — the failure mode that breaks naive
whole-frame frame-differencing.

The proxy is scale-free (pixels/frame, not mph). It supports verdicts about
*shape* — ends stopped, still moving, rising from rest — not absolute speed.
"""

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H = 240, 144          # analysis resolution
ROAD_TOP = 0.40          # use rows below 40% height (road + near world)
TAIL_S = 0.5             # tail window (seconds) for the end-state verdict
HEAD_FRAC = 0.2          # head window fraction for the start-state reference

# Calibrated against the joint ID/flow distribution over the 120-clip sample:
# clips ID places at <=1.5 mph have tail_flow median 0.025 / max 0.216, while clips
# ID places above 1.5 mph have p25 >= 0.20. Flow saturates at speed (motion blur on
# low-texture road), so it separates stopped-vs-moving, not fast-vs-faster.
STOP_FLOW = 0.15         # median road flow (px/frame at 240px width) below this = stopped
MOVE_FLOW = 0.30         # above this = moving; between = ambiguous
# A verdict is only meaningful if the probe registered real motion somewhere in the
# clip. Highway/night scenes blur road texture so badly that flow reads ~0.15-0.4
# even at 50+ mph; such clips are unmeasurable, not "stopped".
MIN_PEAK = 0.5


def decode_gray(path, w=W, h=H):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={w}:{h}",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w)


def flow_profile(path):
    """Median road-region flow magnitude per frame transition [T-1]."""
    frames = decode_gray(path)
    y0 = int(H * ROAD_TOP)
    out = []
    prev = frames[0]
    for cur in frames[1:]:
        flow = cv2.calcOpticalFlowFarneback(
            prev, cur, None, pyr_scale=0.5, levels=3, winsize=15,
            iterations=2, poly_n=5, poly_sigma=1.1, flags=0)
        mag = np.linalg.norm(flow[y0:], axis=2)
        out.append(float(np.median(mag)))
        prev = cur
    return np.array(out)


def video_verdict(path, fps=24.0):
    """End-state and shape verdict for one clip, from pixels alone."""
    f = flow_profile(path)
    n = len(f)
    tail = f[-max(3, int(TAIL_S * fps)):]
    head = f[: max(3, int(n * HEAD_FRAC))]
    tail_m, head_m = float(np.median(tail)), float(np.median(head))
    peak = float(np.max(f))

    measurable = peak >= MIN_PEAK
    if not measurable:
        end_state = "unmeasurable"
    elif tail_m < STOP_FLOW:
        end_state = "stopped"
    elif tail_m > MOVE_FLOW:
        end_state = "moving"
    else:
        end_state = "ambiguous"

    started_stopped = head_m < STOP_FLOW
    return {
        "head_flow": round(head_m, 3),
        "tail_flow": round(tail_m, 3),
        "peak_flow": round(peak, 3),
        "tail_over_head": round(tail_m / max(head_m, 1e-6), 3),
        "end_state": end_state,
        "started_stopped": started_stopped,
        # class-level agreement hooks
        "shows_stop": end_state == "stopped" and not started_stopped,
        "shows_start": started_stopped and tail_m > MOVE_FLOW,
        "shows_sustained_motion": tail_m > MOVE_FLOW and head_m > MOVE_FLOW,
        "n_frames": n + 1,
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Optical-flow ego-motion verdicts")
    p.add_argument("videos", nargs="+", type=Path)
    p.add_argument("--json-out", type=Path, default=None)
    args = p.parse_args()

    results = {}
    for v in args.videos:
        r = video_verdict(v)
        results[str(v)] = r
        print(f"{v.name:<22} head={r['head_flow']:>6.2f} tail={r['tail_flow']:>6.2f} "
              f"peak={r['peak_flow']:>6.2f}  -> {r['end_state']}"
              f"{'  (started stopped)' if r['started_stopped'] else ''}")
    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
