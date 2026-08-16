"""Prompt/context variant registry for the direct-reasoning prompt lab.

Prompts are data: every candidate lives here with its hypothesis, so rounds are
reviewable and the lab runner stays generic. Importing this module runs the
leakage guard — no prompt may name a scenario object (the think-prompt billboard
example moved one scenario 0.048 -> 0.762; never again).

Modes:
  video_only        prompt only
  action            prompt receives the raw 5 Hz [[v, h], ...] text
  action_narrative  prompt receives a mechanical English summary of the trajectory
"""

import json
import re

from cosmos_reasoning_vllm import BASE_PROMPT_NO_ACTION

# Scenario objects and near-synonyms. Abstract displacement-operator vocabulary
# (depiction, printed media, reflected, projected, carried as cargo) stays legal.
BANNED_WORDS = [
    "billboard", "shirt", "t-shirt", "balloon", "bag", "polythene", "hose",
    "mural", "wall", "child", "kid", "moon", "truck", "flatbed", "cone",
    "advertisement", "banner", "stop sign", "traffic light", "traffic signal",
    "pedestrian", "school bus", "flood", "intersection",
]

VERDICT_LINES = (
    "Reply with exactly one of:\n"
    "Classification: Anomaly\n"
    "Classification: Normal"
)

_RULE = (
    "Sometimes a scene contains something that merely looks like a traffic "
    "command or hazard but is not a real one — an image, a depiction, a "
    "reflection, or an object carried as cargo. And sometimes a scene contains a "
    "real hazard in an unfamiliar form.\n"
    "The vehicle's behaviour is ANOMALOUS if it reacted to something that is not "
    "a real command or hazard, or failed to react to a real one. It is NORMAL if "
    "its behaviour matched what was actually there."
)

P1_TEXT = (
    "You are auditing one driving decision made by an autonomous vehicle, shown "
    f"in this clip from its forward camera.\n{_RULE}\n"
    f"Was the vehicle's behaviour appropriate to what was actually there?\n{VERDICT_LINES}"
)

P2_TEXT = (
    "You are auditing one driving decision made by an autonomous vehicle, shown "
    f"in this clip from its forward camera.\n{_RULE}\n"
    "Answer in exactly three short lines:\n"
    "CUE: what commands or hazards are ACTUALLY present — state whether any "
    "apparent cue is real or only a depiction\n"
    "ACTION: what the ego vehicle did\n"
    "Classification: Anomaly or Normal"
)

P3_TEXT = (
    "Watch the ego vehicle's behaviour in this clip from its forward camera. "
    "Considering what is actually present in the scene, did the vehicle respond "
    "correctly? A correct response reacts to real commands and hazards, and does "
    "not react to things that only resemble them.\n"
    "Reply with exactly one line:\n"
    "Response: Correct — the behaviour matched the scene\n"
    "Response: Incorrect — the behaviour did not match the scene"
)

P4_TEXT_TEMPLATE = (
    "You are auditing one driving decision made by an autonomous vehicle, shown "
    "in this clip from its forward camera. The vehicle's own recorded motion is "
    "given below as [[velocity_in_mph, heading_in_degrees], ...] at 5 Hz.\n"
    f"{_RULE}\n"
    "Judge whether this behaviour was NEEDED for what was actually in the scene, "
    "not whether it was smoothly executed. A smooth, controlled manoeuvre is "
    "still an anomaly if the scene did not call for it; keeping a steady speed "
    "is still an anomaly if the scene required action.\n"
    "Ego Vehicle State Sequence (5Hz): {action}\n"
    f"{VERDICT_LINES}"
)

P5_TEXT_TEMPLATE = (
    "You are auditing one driving decision made by an autonomous vehicle, shown "
    "in this clip from its forward camera. Measured from the vehicle's own "
    "motion sensors: {narrative}\n"
    f"{_RULE}\n"
    f"Was the vehicle's behaviour appropriate to what was actually there?\n{VERDICT_LINES}"
)

P6_TEXT = (
    "Definitions: a semantic anomaly is a mismatch between what a scene actually "
    "means and how the vehicle responded to it. The objects involved are usually "
    "detected correctly; the failure is one of interpretation. There are exactly "
    "two failure polarities: (1) treating something that merely resembles a "
    "command or hazard as if it were real, and (2) failing to treat a real "
    "hazard as real because it appears in an unusual form. A response is NORMAL "
    "when it matches the true meaning of the scene, even when the scene itself "
    "looks unusual.\n\n"
    "With those definitions, audit the single driving decision shown in this "
    "clip from the vehicle's forward camera. Was the vehicle's behaviour "
    f"appropriate to what was actually there?\n{VERDICT_LINES}"
)

P7_TEXT = (
    "You are a driving examiner scoring the single manoeuvre shown in this clip, "
    "recorded from the candidate vehicle's forward camera. The manoeuvre FAILS "
    "if the driver reacted to something that was not a real command or hazard, "
    "or failed to react to a real one. It PASSES if the driving matched what was "
    "actually there.\n"
    "Reply with exactly one of:\n"
    "Classification: Anomaly — the manoeuvre fails\n"
    "Classification: Normal — the manoeuvre passes"
)


def action_narrative(action_text: str) -> str:
    """Mechanical English summary of a [[v, h], ...] trajectory. No model, no
    judgement — just arithmetic, so it cannot leak label information beyond what
    the raw numbers already carry."""
    seq = json.loads(action_text)
    v = [row[0] for row in seq]
    h = [row[1] for row in seq]
    start = sum(v[:3]) / min(3, len(v))
    end = sum(v[-3:]) / min(3, len(v))
    final = v[-1]
    start_shown = max(v[:3])   # "from about X": the pre-braking speed, not a diluted mean
    parts = []
    if start <= 2 and end >= 5:
        parts.append(f"the vehicle moved off from a standstill, reaching about {max(v):.0f} mph")
    elif final <= 2 and start > 5:
        parts.append(f"the vehicle slowed from about {start_shown:.0f} mph to a complete stop and was stationary at the end")
    elif end <= 0.6 * start:
        parts.append(f"the vehicle slowed from about {start_shown:.0f} mph to about {end:.0f} mph, still moving at the end")
    elif end >= 1.4 * start:
        parts.append(f"the vehicle sped up from about {start:.0f} mph to about {end:.0f} mph")
    else:
        parts.append(f"the vehicle held a roughly steady speed of about {(start + end) / 2:.0f} mph")
    mx = max(abs(x) for x in h)
    if mx >= 10:
        parts.append(f"its heading changed by up to {mx:.0f} degrees")
    return "; ".join(parts) + "."


GREEDY = {"temperature": 0.0}
GUIDE_NONREASON = {"temperature": 0.7, "top_p": 0.8, "top_k": 20,
                   "presence_penalty": 1.5}

VARIANTS = {
    "P0": {"hypothesis": "baseline control (verbatim released prompt)",
           "mode": "video_only", "text": BASE_PROMPT_NO_ACTION,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P1": {"hypothesis": "crisp decision rule replaces muddled definition",
           "mode": "video_only", "text": P1_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P2": {"hypothesis": "forced commitment: CUE and ACTION lines before verdict",
           "mode": "video_only", "text": P2_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 160},
    "P3": {"hypothesis": "remove the loaded word 'anomaly' (binary correct/incorrect)",
           "mode": "video_only", "text": P3_TEXT,
           "sampling": GREEDY, "parser": "binary", "max_tokens": 64},
    "P4": {"hypothesis": "anti-smooth framing rescues the action channel",
           "mode": "action", "text": P4_TEXT_TEMPLATE,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P5": {"hypothesis": "narrative action summary beats raw numbers",
           "mode": "action_narrative", "text": P5_TEXT_TEMPLATE,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P6": {"hypothesis": "abstract task-definition context improves judgement",
           "mode": "video_only", "text": P6_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P7": {"hypothesis": "examiner pass/fail persona sharpens the criterion",
           "mode": "video_only", "text": P7_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "S1": {"hypothesis": "guide's official non-reasoning sampling on the baseline",
           "mode": "video_only", "text": BASE_PROMPT_NO_ACTION,
           "sampling": GUIDE_NONREASON, "parser": "classification", "max_tokens": 64},
}


def build_prompt(variant: dict, action_text: str | None) -> str:
    if variant["mode"] == "video_only":
        return variant["text"]
    if variant["mode"] == "action":
        return variant["text"].format(action=action_text)
    if variant["mode"] == "action_narrative":
        return variant["text"].format(narrative=action_narrative(action_text))
    raise ValueError(variant["mode"])


_BINARY_RE = re.compile(r"\b(incorrect|correct)\b", re.I)


def parse_binary(raw: str) -> str:
    """'Correct' -> Normal, 'Incorrect' -> Anomaly; last word-boundary match wins
    (plain rfind would find 'correct' inside 'incorrect')."""
    if not raw:
        return "Unknown"
    matches = list(_BINARY_RE.finditer(raw.lower()))
    if not matches:
        return "Unknown"
    return "Anomaly" if matches[-1].group(1) == "incorrect" else "Normal"


def _leak_check():
    baseline_ok = {"P0", "S1"}  # released prompt is the historical control
    for vid, v in VARIANTS.items():
        if vid in baseline_ok:
            continue
        text = v["text"].lower()
        # Word-boundary match: plain substring flags "those" for "hose".
        hits = [w for w in BANNED_WORDS
                if re.search(rf"\b{re.escape(w)}s?\b", text)]
        if hits:
            raise AssertionError(f"prompt {vid} leaks scenario vocabulary: {hits}")


_leak_check()
