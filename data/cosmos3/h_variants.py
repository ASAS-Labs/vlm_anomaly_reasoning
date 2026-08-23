"""Registry for the H-lab (family M): two-stage expectation-vs-action monitor prompts.

Each entry fixes the stage-1 question (asked on an EARLY window of the clip),
the stage-1 window, the stage-2 follow-up template (second user turn; receives
the ACTUAL trajectory text rendered per `action_render`), and a hypothesis.
Prompts are example-free and must not name scenario objects: this module runs
the same leak guard as prompt_variants over every text.

    python h_variants.py --print        # review artifact: texts + sha256s
"""

import argparse
import hashlib
import json
import re

from expectation_experiment import EXPECT_QUESTION, MONITOR_FOLLOWUP
from prompt_variants import BANNED_WORDS, _GUARD_LINE, action_narrative

WINDOWS = {"tminus2.5": "generated_vids_720p_tminus2.5",
           "tminus1.5": "generated_vids_720p_tminus1.5",
           "tminus1.0": "generated_vids_720p_tminus1.0",
           "gt": "generated_vids_720p_early_gt",
           "1.5s": "generated_vids_720p_early1.5s",
           "1.0s": "generated_vids_720p_early1.0s"}

_OPTIONS = ("Continue — maintain current speed and lane\n"
            "Slow — reduce speed but keep moving\n"
            "Stop — brake to a complete stop\n"
            "Wait — the vehicle is already stationary and should remain stopped")

# Stage 2 with an explicit comparison rule (M1 family). {render_intro} names the
# rendering; {secs} is the trajectory span (rows / 5 Hz) so the 6 s trajectories
# of some long clips are described honestly.
_RULE_BODY = (
    "Read that motion as exactly one of: continued (speed roughly held), slowed "
    "(speed clearly reduced but still moving at the end), stopped (came to rest "
    "and stayed there), waited (stationary throughout), or moved off (pulled away "
    "from a standstill). Compare it with the "
    "expectation you gave. The behaviour MATCHES the expectation only for the "
    "action that was expected, with two tolerances: 'continue' and 'slow' are "
    "compatible with each other, and an expected 'stop' is satisfied by coming to "
    "rest or remaining at rest. Stopping when continue or slow was expected, "
    "continuing or merely slowing when stop was expected, and moving off when wait "
    "was expected are mismatches.\n"
    "First state the observed motion class in one short sentence. Then reply on "
    "the final line with exactly one of:\n"
    "Classification: Anomaly — the behaviour does not match the expected action\n"
    "Classification: Normal — the behaviour matches the expected action"
)
_RAW_INTRO = ("Here is the ego vehicle's ACTUAL recorded motion over the recorded "
              "{secs} seconds of this clip, as [[velocity_in_mph, heading_in_degrees], "
              "...] sampled at 5 Hz:\n{seq}\n\n")
_VEL_INTRO = ("Here is the ego vehicle's ACTUAL recorded speed over the recorded "
              "{secs} seconds of this clip, as [velocity_in_mph, ...] sampled at 5 Hz "
              "(speed only):\n{seq}\n\n")
_NARR_INTRO = ("Measured from the ego vehicle's own motion sensors over the recorded "
               "{secs} seconds of this clip: {seq}\n\n")

M1_STAGE2 = _RAW_INTRO + _RULE_BODY
M2_STAGE2 = _NARR_INTRO + _RULE_BODY
M3_STAGE2 = _VEL_INTRO + _RULE_BODY
M5_STAGE2 = (_RAW_INTRO
             + "Before comparing, re-check the expectation you gave. " + _GUARD_LINE
             + " If your expectation rested on such an item, correct it to what the "
               "scene actually requires.\n\n" + _RULE_BODY)

# M4: expectation + the real feature requiring it, with the guard's depiction
# sentence at the expectation step.
M4_STAGE1 = (
    "You are evaluating the driving scene in this clip from the ego vehicle's "
    "point of view. Based only on what the scene requires — not on how the ego "
    "vehicle happens to be moving — what SHOULD a correct, safe driver do over the "
    "next few seconds? Name the specific real feature of the scene that requires "
    "it, or state that nothing requires a change. Note: an apparent traffic "
    "control or hazard that is only an image — printed, painted, displayed on a "
    "screen, reflected, worn on clothing, or carried as cargo — commands nothing. "
    "Then reply on the final line with exactly one word: Continue, Slow, Stop, or "
    f"Wait.\n{_OPTIONS}"
)

_M0 = {"stage1": EXPECT_QUESTION, "stage2": MONITOR_FOLLOWUP, "action_render": "raw"}

H_VARIANTS = {
    "M0": {**_M0, "stage1_window": "tminus2.5", "parent": "H3",
           "hypothesis": "H3 control: verbatim stage-1/stage-2 texts @ T-2.5"},
    "M1": {"stage1": EXPECT_QUESTION, "stage2": M1_STAGE2, "action_render": "raw",
           "stage1_window": "tminus2.5", "parent": "M0",
           "hypothesis": "explicit comparison rule + tolerances fixes the comparator"},
    "M2": {"stage1": EXPECT_QUESTION, "stage2": M2_STAGE2, "action_render": "narrative",
           "stage1_window": "tminus2.5", "parent": "M1",
           "hypothesis": "narrative rendering removes numeric reading from comparison"},
    "M3": {"stage1": EXPECT_QUESTION, "stage2": M3_STAGE2, "action_render": "velocity",
           "stage1_window": "tminus2.5", "parent": "M1",
           "hypothesis": "heading channel is noise for speed-class matching"},
    "M4": {"stage1": M4_STAGE1, "stage2": M1_STAGE2, "action_render": "raw",
           "stage1_window": "tminus2.5", "parent": "M1",
           "hypothesis": "guard concept + named feature at the expectation step"},
    "M5": {"stage1": EXPECT_QUESTION, "stage2": M5_STAGE2, "action_render": "raw",
           "stage1_window": "tminus2.5", "parent": "M1",
           "hypothesis": "guard line as a verdict-time expectation re-check"},
    "M6": {**_M0, "stage1_window": "1.5s", "parent": "M0",
           "hypothesis": "window ladder: M0 prompts at a 1.5 s stage-1 window"},
    "M7": {**_M0, "stage1_window": "1.0s", "parent": "M0",
           "hypothesis": "window ladder: M0 prompts at a 1.0 s stage-1 window"},
}


# --- Round 2: compose the round-1 levers (registered before spend) ----------
# Round 1: M2 (narrative + rule) is 100% correct given a correct expectation
# (63/63) -> the ceiling is stage 1; M4's guard+feature stage 1 had the best
# stage-1 numbers (64/80 lenient) and M5's stage-2 guard re-check rescued 67% of
# stage-1-wrong clips. Window ladder flat -> stay at T-2.5.
M9_STAGE2 = (_NARR_INTRO
             + "Before comparing, re-check the expectation you gave. " + _GUARD_LINE
             + " If your expectation rested on such an item, correct it to what the "
               "scene actually requires.\n\n" + _RULE_BODY)

H_VARIANTS.update({
    "M8": {"stage1": M4_STAGE1, "stage2": M2_STAGE2, "action_render": "narrative",
           "stage1_window": "tminus2.5", "parent": "M4 x M2",
           "hypothesis": "compose: guard+feature stage 1 x narrative comparator"},
    "M9": {"stage1": M4_STAGE1, "stage2": M9_STAGE2, "action_render": "narrative",
           "stage1_window": "tminus2.5", "parent": "M4 x M2 x M5",
           "hypothesis": "compose: guard stage 1 x narrative x guard re-check"},
    "M10": {"stage1": EXPECT_QUESTION, "stage2": M9_STAGE2, "action_render": "narrative",
            "stage1_window": "tminus2.5", "parent": "M2 x M5",
            "hypothesis": "compose: M0 stage 1 x narrative x guard re-check (ablates M4)"},
})

# --- Round 3: stage-1 self-consistency on the round-2 leader --------------
# M8's comparator is 63/63 given a correct expectation; stage 1 (63/80
# lenient) is the ceiling. Majority of 3 stage-1 samples (seeds s, s+1, s+2).
H_VARIANTS.update({
    "M11": {**H_VARIANTS["M8"], "parent": "M8", "stage1_k": 3,
            "hypothesis": "M8 with stage-1 majority-of-3 self-consistency"},
})

# --- Post-235 autopsy: longer stage-1 windows on M8's failures ------------
# 7/40 failures (neg_8) are the label-defining event happening after T-2.5;
# M8 unchanged except the stage-1 window = clip duration - 1.5 s / - 1.0 s.
H_VARIANTS.update({
    "M8w15": {**H_VARIANTS["M8"], "parent": "M8", "stage1_window": "tminus1.5",
              "hypothesis": "M8 with the stage-1 window at T-1.5 (sees later events)"},
    "M8w10": {**H_VARIANTS["M8"], "parent": "M8", "stage1_window": "tminus1.0",
              "hypothesis": "M8 with the stage-1 window at T-1.0 (sees later events)"},
})


def render_action(render: str, seq_text: str) -> str:
    if render == "raw":
        return seq_text
    if render == "velocity":
        from cosmos_reasoning_vllm import velocity_only
        return velocity_only(seq_text)
    if render == "narrative":
        return action_narrative(seq_text)
    raise ValueError(render)


def stage2_prompt(variant: dict, seq_text: str) -> str:
    rows = len(json.loads(seq_text))
    return variant["stage2"].format(seq=render_action(variant["action_render"], seq_text),
                                    secs=f"{rows / 5.0:g}")


def _leak_check():
    for vid, v in H_VARIANTS.items():
        for field in ("stage1", "stage2"):
            text = v[field].lower()
            hits = [w for w in BANNED_WORDS if re.search(rf"\b{re.escape(w)}s?\b", text)]
            if hits:
                raise AssertionError(f"H variant {vid}.{field} leaks scenario vocabulary: {hits}")


_leak_check()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    for vid, v in H_VARIANTS.items():
        print(f"=== {vid} ({v['stage1_window']}, {v['action_render']}): {v['hypothesis']}")
        print(f"  stage1 sha {sha(v['stage1'])[:12]}  stage2 sha {sha(v['stage2'])[:12]}")
        if a.print:
            print("  --- stage 1 ---\n" + v["stage1"])
            print("  --- stage 2 (template) ---\n" + v["stage2"] + "\n")

# --- Annotated decision-time window (GT metadata; SFT context) ------------
# expected_action_gt.json carries per-clip early-window END times (when the
# expected action becomes determinable from the scene); the stage-1 window is
# the 2.5 s rolling window ending there, [0, T-2.5] where unannotated.
# Tree: make_pilot_trees.py --early-mode gt. Evaluation on it = "at the
# annotated decision time", reported separately from the fixed T-2.5 rows.
H_VARIANTS.update({
    "M8gt": {**H_VARIANTS["M8"], "parent": "M8", "stage1_window": "gt",
             "hypothesis": "M8 with the per-clip annotated decision-time window"},
})

