"""Derive [[velocity_mph, heading_deg], ...] from absolute camera poses.

Single source of truth for the inverse-dynamics trajectory maths. numpy only — no
cosmos_framework import — so every variant can be derived offline from persisted
poses without a GPU box.

Three defects in the original derivation are corrected here:

1. **Time base.** Velocity was computed as `d * FPS` with FPS hardcoded to 10, but
   the frames handed to the model were 24 fps, so every speed was scaled by 10/24.
   `hz` must be the *actual* frame spacing of the ID input.

2. **Padding.** The framework pads a short clip to `action_chunk_size + 1` frames by
   repeating the last frame (inference/action.py:88-93). Those duplicated frames have
   zero motion, so an untrimmed trajectory ends in a fabricated stop. `n_valid`
   truncates to the real frames. This is not cosmetic: without it every clip appears
   to stop and the "fix" looks successful for entirely the wrong reason.

3. **Unsigned magnitude.** Velocity was `||dpos_xz||`, which is non-negative by
   construction, so pose jitter gives a stationary vehicle a positive speed floor and
   it can never read 0. The signed variant projects onto the heading axis instead.
"""

import numpy as np

MPS_TO_MPH = 2.2369362921

# Variant table. Nothing else in the repo defines a variant; derive_action_files.py
# and semantic_agreement.py both read this. `source` is either the published .txt
# files ("published") or the persisted raw poses ("raw").
VARIANTS = {
    "v0_baseline": {"source": "published", "scale": 1.0,
                    "desc": "released trajectories, unchanged"},
    "v0_timebase": {"source": "published", "scale": 24.0 / 10.0,
                    "desc": "released x2.4: time base only, isolates scale from coverage"},
    "v1_resample": {"source": "raw", "signed": False, "edge_repair": False,
                    "smooth": False, "hz5": "decimate",
                    "desc": "10fps input + padding trim + true hz"},
    "v2_edges": {"source": "raw", "signed": False, "edge_repair": True,
                 "smooth": False, "hz5": "decimate",
                 "desc": "v1 + edge-sample repair"},
    "v3_signed": {"source": "raw", "signed": True, "edge_repair": True,
                  "smooth": False, "hz5": "decimate",
                  "desc": "v2 + signed forward-axis velocity"},
    "v4_smooth": {"source": "raw", "signed": True, "edge_repair": True,
                  "smooth": True, "hz5": "decimate",
                  "desc": "v3 + 3-tap smoothing and clamp"},
    "v5_final": {"source": "raw", "signed": True, "edge_repair": True,
                 "smooth": True, "hz5": "average",
                 "desc": "v4 + averaged 5Hz (consistent operator for both channels)"},
}

V_CLAMP = (-5.0, 100.0)   # mph; physically implausible outside this for these clips
STOP_MPH = 2.0            # at or below this counts as stopped


def _headings(poses):
    """Yaw about the vertical axis, degrees, relative to frame 0."""
    fwd = poses[:, :3, 2]                      # camera +Z in world coords
    yaw = np.arctan2(fwd[:, 0], fwd[:, 2])     # ground-plane (X-Z) angle
    return np.degrees(np.unwrap(yaw - yaw[0]))


def _repair_edges(v):
    """Replace unreliable end samples.

    v[0] is derived from pose 0, which pose_rel_to_abs seeds as exact identity, against
    pose 1 which carries the model's full first-step error — so it is the least
    constrained sample in the series. Both ends are additionally checked against a
    robust (median/MAD) outlier bound.
    """
    v = v.copy()
    if len(v) < 3:
        return v
    v[0] = v[1]
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) or 1e-6
    for i in (0, len(v) - 1):
        if abs(v[i] - med) > 3.0 * 1.4826 * mad:
            v[i] = v[1] if i == 0 else v[-2]
    return v


def _smooth3(x):
    """Centred 3-tap moving average, endpoints preserved."""
    if len(x) < 3:
        return x
    out = x.copy()
    out[1:-1] = (x[:-2] + x[1:-1] + x[2:]) / 3.0
    return out


def derive_10hz(poses, hz, n_valid=None, *, signed=False, edge_repair=False,
                smooth=False):
    """[[velocity_mph, heading_deg], ...] from absolute poses [T,4,4].

    hz       true frame rate of the frames the model consumed (NOT a constant)
    n_valid  number of real (non-padded) frames; the rest are duplicates and dropped
    signed   project displacement onto the heading axis instead of taking |displacement|
    """
    poses = np.asarray(poses, dtype=np.float64)
    if n_valid is not None:
        poses = poses[:max(2, int(n_valid))]
    if len(poses) < 2:
        return []

    pos = poses[:, :3, 3]
    heading = _headings(poses)
    disp = np.diff(pos[:, [0, 2]], axis=0)

    if signed:
        fwd = poses[:-1, :3, 2][:, [0, 2]]
        norm = np.linalg.norm(fwd, axis=1, keepdims=True)
        fwd = fwd / np.where(norm == 0, 1.0, norm)
        d = np.sum(disp * fwd, axis=1)       # signed: reverse reads negative
    else:
        d = np.linalg.norm(disp, axis=1)     # unsigned magnitude (original behaviour)

    v = d * hz * MPS_TO_MPH
    if edge_repair:
        v = _repair_edges(v)
    if smooth:
        v = _smooth3(v)
        heading = np.concatenate([[heading[0]], _smooth3(heading[1:])])
        v = np.clip(v, *V_CLAMP)
    return [[round(float(v[i]), 4), round(float(heading[i]), 4)] for i in range(len(v))]


def to_5hz(seq10, mode="decimate"):
    """Downsample a 10 Hz sequence to 5 Hz.

    'decimate' reproduces the original behaviour. 'average' pairs each two 10 Hz steps
    and means both channels, so velocity and heading share one operator — the original
    took a 0.2s chord for velocity while plain-decimating heading, which under-reports
    speed through turns by roughly cos(dyaw/2).
    """
    if not seq10:
        return []
    if mode == "decimate":
        return seq10[::2]
    out = []
    for i in range(0, len(seq10) - 1, 2):
        a, b = seq10[i], seq10[i + 1]
        out.append([round((a[0] + b[0]) / 2.0, 4), round((a[1] + b[1]) / 2.0, 4)])
    if len(seq10) % 2:
        out.append(seq10[-1])
    return out


def derive_variant(poses, hz, n_valid, variant):
    """(seq_5hz, seq_10hz) for a named raw-sourced variant."""
    cfg = VARIANTS[variant]
    if cfg["source"] != "raw":
        raise ValueError(f"{variant} is not derived from raw poses")
    seq10 = derive_10hz(poses, hz, n_valid, signed=cfg["signed"],
                        edge_repair=cfg["edge_repair"], smooth=cfg["smooth"])
    return to_5hz(seq10, cfg["hz5"]), seq10


def scale_published(seq, factor):
    """Scale velocities of an existing sequence, leaving headings alone."""
    return [[round(v * factor, 4), h] for v, h in seq]
