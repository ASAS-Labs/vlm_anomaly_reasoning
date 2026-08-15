#!/usr/bin/env python3
"""Checks for the inverse-dynamics trajectory derivation.

Plain asserts, no pytest, runnable on a laptop:
    cd data/cosmos3 && python id_trajectory_test.py

The two regression tests that matter are test_padding_trim and test_time_base — they
pin the defects that made the released trajectories disagree with their prompts.
"""

import sys

import numpy as np

from id_trajectory import MPS_TO_MPH, derive_10hz, to_5hz

MPS_TO_MPH_ = MPS_TO_MPH


def poses_from_positions(xs, zs, yaws=None):
    """Build [T,4,4] camera-to-world poses from ground-plane positions + yaws."""
    n = len(xs)
    yaws = np.zeros(n) if yaws is None else np.asarray(yaws, dtype=float)
    out = np.zeros((n, 4, 4))
    for i in range(n):
        c, s = np.cos(yaws[i]), np.sin(yaws[i])
        out[i] = np.eye(4)
        # third column = forward (+Z); yaw rotates it in the X-Z plane
        out[i][:3, 2] = [s, 0.0, c]
        out[i][:3, 0] = [c, 0.0, -s]
        out[i][:3, 3] = [xs[i], 0.0, zs[i]]
    return out


def test_constant_speed():
    # 10 m/s straight ahead, sampled at 10 Hz -> 1 m per step.
    z = np.arange(11) * 1.0
    seq = derive_10hz(poses_from_positions(np.zeros(11), z), hz=10)
    assert len(seq) == 10, len(seq)
    for v, h in seq:
        assert abs(v - 10.0 * MPS_TO_MPH_) < 1e-3, v   # values are rounded to 4dp
        assert abs(h) < 1e-9, h
    print("  constant speed: 10 m/s -> 22.37 mph, flat heading")


def test_time_base():
    """REGRESSION: deriving 24 fps poses at hz=10 under-reports by exactly 10/24.

    This is the bug that made a highway clip read 28.8 mph instead of ~69.
    """
    z = np.arange(25) * 0.5
    p = poses_from_positions(np.zeros(25), z)
    at24 = derive_10hz(p, hz=24)
    at10 = derive_10hz(p, hz=10)
    ratio = at24[0][0] / at10[0][0]
    assert abs(ratio - 2.4) < 1e-4, ratio
    print(f"  time base: hz=24 is exactly {ratio:.4f}x hz=10")


def test_padding_trim():
    """REGRESSION: duplicated tail frames must not become a fabricated stop.

    The framework pads short clips by repeating the last frame. Untrimmed, those
    zero-motion steps read as a stop the vehicle never made.
    """
    z = list(np.arange(10) * 1.0)
    z_padded = z + [z[-1]] * 5          # 5 duplicated frames
    p = poses_from_positions(np.zeros(len(z_padded)), np.array(z_padded))

    untrimmed = derive_10hz(p, hz=10)
    assert len(untrimmed) == 14
    assert untrimmed[-1][0] == 0.0, "expected the fabricated stop without trimming"

    trimmed = derive_10hz(p, hz=10, n_valid=10)
    assert len(trimmed) == 9, len(trimmed)
    assert all(v > 1.0 for v, _ in trimmed), trimmed
    print(f"  padding trim: 14 steps (ending 0.0 mph) -> {len(trimmed)} real steps, no fake stop")


def test_decel_to_stop_signed():
    # Linear ramp to zero, then genuinely stationary with small lateral jitter.
    speeds = list(np.linspace(1.0, 0.0, 10))
    z, x = [0.0], [0.0]
    for s in speeds:
        z.append(z[-1] + s)
        x.append(0.0)
    rng = np.random.default_rng(0)
    for _ in range(5):                   # truly stopped, jitter only
        z.append(z[-1] + rng.normal(0, 0.002))
        x.append(x[-1] + rng.normal(0, 0.002))
    p = poses_from_positions(np.array(x), np.array(z))

    unsigned = derive_10hz(p, hz=10, signed=False)
    signed = derive_10hz(p, hz=10, signed=True)
    # Unsigned magnitude can never be negative, so jitter shows as positive speed.
    assert min(v for v, _ in unsigned) >= 0.0
    tail_u = np.mean([v for v, _ in unsigned[-4:]])
    tail_s = abs(np.mean([v for v, _ in signed[-4:]]))
    assert tail_s < tail_u, (tail_s, tail_u)
    assert tail_s < 0.1, tail_s
    print(f"  signed velocity: stationary tail {tail_u:.4f} mph unsigned -> {tail_s:.4f} signed")


def test_heading_arc():
    # Quarter-ish arc totalling 30 degrees of yaw.
    n = 21
    yaws = np.radians(np.linspace(0, 30, n))
    z = np.cumsum(np.cos(yaws)) - np.cos(yaws[0])
    x = np.cumsum(np.sin(yaws)) - np.sin(yaws[0])
    seq = derive_10hz(poses_from_positions(x, z, yaws), hz=10)
    mx = max(abs(h) for _, h in seq)
    assert abs(mx - 30.0) < 2.0, mx
    print(f"  heading: 30 deg arc -> max|heading| = {mx:.2f} deg")


def test_5hz_modes():
    seq10 = [[10.0, 0.0], [12.0, 1.0], [14.0, 2.0], [16.0, 3.0]]
    dec = to_5hz(seq10, "decimate")
    avg = to_5hz(seq10, "average")
    assert dec == [[10.0, 0.0], [14.0, 2.0]], dec
    assert avg == [[11.0, 0.5], [15.0, 2.5]], avg
    print("  5Hz: decimate keeps every other sample; average means both channels")


def test_edge_repair():
    v = [50.0] + [10.0] * 8 + [40.0]     # spikes at both ends
    z = np.concatenate([[0.0], np.cumsum(np.array(v) / (10 * MPS_TO_MPH_))])
    p = poses_from_positions(np.zeros(len(z)), z)
    raw = derive_10hz(p, hz=10, edge_repair=False)
    fixed = derive_10hz(p, hz=10, edge_repair=True)
    assert raw[0][0] > 40 and raw[-1][0] > 30, (raw[0], raw[-1])
    assert fixed[0][0] < 15 and fixed[-1][0] < 15, (fixed[0], fixed[-1])
    print(f"  edge repair: ({raw[0][0]:.1f}, {raw[-1][0]:.1f}) -> "
          f"({fixed[0][0]:.1f}, {fixed[-1][0]:.1f}) mph")


if __name__ == "__main__":
    print("running id_trajectory checks...")
    test_constant_speed()
    test_time_base()
    test_padding_trim()
    test_decel_to_stop_signed()
    test_heading_arc()
    test_5hz_modes()
    test_edge_repair()
    print("all checks passed")
    sys.exit(0)
