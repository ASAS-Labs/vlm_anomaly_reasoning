"""Does a recovered trajectory agree with what its prompt says the vehicle did?

Moved out of run_inverse_dynamics.py so the same rules score every trajectory
variant, with one substantive change: prompts that describe a *stop* are now scored
on an absolute rule (end velocity <= 2 mph) rather than the end/start ratio.

The ratio test cannot verify a stop. A car slowing 30 -> 17 mph passes it, and a car
already stationary that stays stationary fails it. Since "comes to a complete stop"
is exactly the case where the released trajectories disagree with their prompts, the
metric has to be able to express it.
"""

import numpy as np

TAIL_RANGE = (0.05, 0.2)   # fraction of the sequence used for the start/end windows
DECEL_RATIO = 0.6
ACCEL_RATIO = 1.4
MAINTAIN_LO, MAINTAIN_HI = 0.6, 1.6
STEER_DEG = 5.0
STOP_MPH = 2.0             # at or below this counts as stopped

STEER_KW = ["steer", "maneuver", "manoeuvr", "navigat", "oncoming lane",
            "into an oncoming", "jagged", "swerv", "changes lane"]
ACCEL_KW = ["starts moving", "starts to move", "begins to move",
            "begins to drive", "accelerat", "starts driving"]
NO_DECEL_KW = ["no deceleration", "without stopping", "without slowing",
               "runs into", "fails to detect", "driving through",
               "continues to drive", "drive forward"]
# Split out of the old decel bucket: these assert the vehicle actually reaches zero.
STOP_KW = ["comes to a stop", "to a complete stop", "complete stop", "full stop",
           "controlled stop", "compliant stop", "decelerates to a stop",
           "to a full stop"]
DECEL_KW = ["decelerat", "to a stop", "slows down", "slow down"]
MAINTAIN_KW = ["maintains", "normal speed", "cruising", "continues driving",
               "drives past", "smoothly past", "remains safely stopped",
               "remains stopped", "lane position"]


def classify_expected(sentence: str) -> dict:
    """Heuristic end-behaviour expectation from a natural-language sentence."""
    s = sentence.lower()
    expected = {"speed": None, "steer": False}

    if any(k in s for k in STEER_KW):
        expected["steer"] = True

    if any(k in s for k in ACCEL_KW):
        expected["speed"] = "start_from_stop" if "stopped" in s or "stationary" in s \
            else "accelerate"
    elif any(k in s for k in NO_DECEL_KW):
        expected["speed"] = "maintain"
    elif "resuming" in s or "nominal speed" in s:
        # e.g. "slows down ... before resuming nominal speed" -> net maintain
        expected["speed"] = "maintain"
    elif any(k in s for k in STOP_KW):
        expected["speed"] = "stop"
    elif any(k in s for k in DECEL_KW):
        expected["speed"] = "decelerate"
    elif any(k in s for k in MAINTAIN_KW):
        expected["speed"] = "maintain"
    return expected


def evaluate_sequence(seq) -> dict:
    """Summary statistics plus the continuous diagnostics used for reporting."""
    if not seq:
        return {"start_v": 0.0, "end_v": 0.0, "max_abs_heading": 0.0, "v_max": 0.0,
                "v_final": 0.0, "t_first_below_stop": None, "mean_abs_dv": 0.0,
                "edge_outlier": False, "n": 0}
    v = np.array([r[0] for r in seq], dtype=np.float64)
    h = np.array([r[1] for r in seq], dtype=np.float64)
    n = len(v)

    lo, hi = TAIL_RANGE
    i0 = max(0, min(int(round(n * lo)), n - 1))
    i1 = max(i0 + 1, min(int(round(n * hi)), n))
    j0 = max(0, min(int(round(n * (1.0 - hi))), n - 1))
    j1 = max(j0 + 1, min(int(round(n * (1.0 - lo))), n))

    below = np.nonzero(v <= STOP_MPH)[0]
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) or 1e-6
    edge_outlier = bool(abs(v[0] - med) > 3 * 1.4826 * mad
                        or abs(v[-1] - med) > 3 * 1.4826 * mad)

    return {
        "start_v": float(v[i0:i1].mean()),
        "end_v": float(v[j0:j1].mean()),
        "max_abs_heading": float(np.max(np.abs(h))),
        "v_max": float(np.max(v)),
        "v_final": float(v[-1]),
        # Normalised position of the first stopped sample; None if it never stops.
        "t_first_below_stop": (float(below[0]) / max(1, n - 1)) if len(below) else None,
        "mean_abs_dv": float(np.mean(np.abs(np.diff(v)))) if n > 1 else 0.0,
        "edge_outlier": edge_outlier,
        "n": n,
    }


def check_match(expected: dict, stats: dict) -> tuple[bool, list[str]]:
    """True when the trajectory agrees with the prompt's stated end behaviour."""
    eps = 1e-6
    start_v, end_v = stats["start_v"], stats["end_v"]
    ratio = end_v / max(start_v, eps)
    reasons: list[str] = []
    ok = True
    sp = expected["speed"]

    if sp == "stop":
        # Absolute, not a ratio: the prompt asserts the vehicle reaches zero.
        if not (stats["v_final"] <= STOP_MPH or end_v <= STOP_MPH):
            ok = False
            reasons.append(f"expected a stop, end_v={end_v:.1f} final={stats['v_final']:.1f} mph")
    elif sp == "decelerate":
        if not (ratio < DECEL_RATIO):
            ok = False
            reasons.append(f"expected deceleration, end/start velocity={ratio:.2f}")
    elif sp == "accelerate":
        if not (ratio > ACCEL_RATIO):
            ok = False
            reasons.append(f"expected acceleration, end/start velocity={ratio:.2f}")
    elif sp == "start_from_stop":
        if not (start_v <= STOP_MPH * 2 and end_v >= 5.0):
            ok = False
            reasons.append(f"expected motion from rest, start_v={start_v:.1f} end_v={end_v:.1f}")
    elif sp == "maintain":
        if not (MAINTAIN_LO <= ratio <= MAINTAIN_HI):
            ok = False
            reasons.append(f"expected ~constant speed, end/start velocity={ratio:.2f}")

    if expected["steer"] and stats["max_abs_heading"] < STEER_DEG:
        ok = False
        reasons.append(f"expected steering, max|heading|={stats['max_abs_heading']:.1f}deg")
    return ok, reasons
