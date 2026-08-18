"""Prompt/context variant registry for the direct-reasoning prompt lab.

Prompts are data: every candidate lives here with its hypothesis, so rounds are
reviewable and the lab runner stays generic. Importing this module runs the
leakage guard — no prompt may name a scenario object (the think-prompt billboard
example moved one scenario 0.048 -> 0.762; never again).

Modes:
  video_only        prompt only
  action            prompt receives the raw 5 Hz [[v, h], ...] text
  action_narrative  prompt receives a mechanical English summary of the trajectory
  velocity          prompt receives the heading-stripped 5 Hz [v, ...] text
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
    if variant["mode"] == "velocity":
        from cosmos_reasoning_vllm import velocity_only
        return variant["text"].format(velocity=velocity_only(action_text))
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

# --- Round 2: hybrids informed by round-1 autopsy --------------------------
# Round 1 showed prompts slide along the ROC curve without improving balanced
# accuracy (P0 0.886/0.500, P6 its mirror 0.432/0.964). P0's 19 errors are 14x
# "scene looks concerning but the response was correct" + 5x the neg_prompt_3
# perception blind spot. Hybrids graft P6's scenery-vs-response line onto the
# champion P0 wording with minimal delta.

_SCENERY_LINE = (
    "Note: a scene that merely LOOKS unusual is not an anomaly by itself. Judge "
    "the vehicle's RESPONSE: an anomaly is either a wrong reaction to something "
    "that required none, or a missing reaction to something real. A correct "
    "response to a real hazard is Normal, even if the scene is dramatic."
)

P8_TEXT = BASE_PROMPT_NO_ACTION.replace(
    "Reply with exactly one word of the following:",
    _SCENERY_LINE + "\nReply with exactly one word of the following:")

P9_TEXT = P6_TEXT.split("With those definitions")[0] + (
    "With those definitions in mind: "
) + BASE_PROMPT_NO_ACTION

P10_TEXT = BASE_PROMPT_NO_ACTION.replace(
    "Reply with exactly one word of the following:",
    _SCENERY_LINE + "\nFirst reply in ONE short sentence: what did the vehicle "
    "do, and was the thing it reacted to (or ignored) real? Then reply with "
    "exactly one word of the following:")

VARIANTS.update({
    "P8": {"hypothesis": "champion P0 + one scenery-vs-response line",
           "mode": "video_only", "text": P8_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P9": {"hypothesis": "P6 definitions grafted before the verbatim P0 question",
           "mode": "video_only", "text": P9_TEXT,
           "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "P10": {"hypothesis": "P8 + one-sentence rationale before the verdict",
            "mode": "video_only", "text": P10_TEXT,
            "sampling": GREEDY, "parser": "classification", "max_tokens": 120},
    "S2": {"hypothesis": "self-consistency: P0 x5 samples at t=0.7, majority",
           "mode": "video_only", "text": BASE_PROMPT_NO_ACTION,
           "sampling": {"temperature": 0.7, "top_p": 0.95},
           "parser": "classification", "max_tokens": 64},
})

_leak_check()

# --- Think-regime slate (rounds 3+) ----------------------------------------
# Direct-lab law (Part 9): wording moves bias, not discrimination. The think
# slate therefore varies reasoning STRUCTURE, injects the normative policy the
# model lacks (Part 8), and composes the model's own reliable probe answers
# (Part 7) — rather than rephrasing the question.

from cosmos_reasoning_vllm import (  # noqa: E402
    _ANOMALY_DEF,
    _FORMAT_INSTRUCTION,
    _MATCH_STEP,
    _SCENE_STEP,
    THINK_PROMPT_ACTION_HEAD,
    THINK_PROMPT_ACTION_TAIL,
    THINK_PROMPT_NO_ACTION,
    THINK_SAMPLING as _TS,
)

THINK = {k: v for k, v in _TS.items() if k != "repetition_penalty"}

_INTRO = (
    "You are an autonomous driving safety expert analyzing this ego vehicle's "
    "video for semantic or contextual anomalies that may impact safe AV "
    f"operation.\n\n{_ANOMALY_DEF}\n\n"
)

_BEHAVIOUR_STEP = (
    "Behaviour: from the ego-motion visible in the video, what does the ego "
    "vehicle do — hold speed, decelerate, come to a stop, accelerate, or change "
    "heading — and when in the clip does it happen?"
)

T1_TEXT = _INTRO + (
    "Is there any semantic misunderstanding in the vehicle's behaviour that "
    f"would require intervention?\n\n{_FORMAT_INSTRUCTION}"
)

T2_TEXT = _INTRO + (
    f"Reason through the following, in order:\n1. {_BEHAVIOUR_STEP}\n"
    f"2. Scene: {_SCENE_STEP[9:]}\n{_MATCH_STEP}\n\n{_FORMAT_INSTRUCTION}"
)

T3_TEXT = _INTRO + (
    "Work through this checklist in your reasoning:\n"
    "1. List every apparent traffic command or hazard in the scene.\n"
    "2. For each one: is it real, or a depiction, look-alike, or reflection?\n"
    "3. State what the ego vehicle did.\n"
    "4. Decide: was that response required by something real? Was it triggered "
    "by something not real? Or was a required response missing?\n\n"
    + _FORMAT_INSTRUCTION
)

T4_TEXT = _INTRO + (
    "In your reasoning, first make the strongest case that the behaviour is "
    "Normal. Then make the strongest case that it is Anomalous. Then state "
    f"which case is stronger and why.\n\n{_FORMAT_INSTRUCTION}"
)

T5_TEXT = _INTRO + (
    "In your reasoning: first state your immediate impression (Anomaly or "
    "Normal). Then verify it: (a) is the thing the vehicle reacted to — or "
    "ignored — actually real? (b) was the vehicle's action necessary, "
    "forbidden, or appropriate here? If the verification contradicts your "
    f"impression, revise it.\n\n{_FORMAT_INSTRUCTION}"
)

T6_TEXT = _INTRO + (
    "In your reasoning, cite the concrete moments that matter: describe what is "
    "visible and what the vehicle does at approximate times (for example, "
    "'around second 2, ...'). Base the verdict only on the evidence you "
    f"cited.\n\n{_FORMAT_INSTRUCTION}"
)

_RULES_BLOCK = (
    "Rules a correct driver follows:\n"
    "- stop or wait when a real traffic control requires it;\n"
    "- stop for people or genuine obstructions in the vehicle's path;\n"
    "- slow down when visibility is impaired;\n"
    "- otherwise maintain speed;\n"
    "- and never react to images, depictions, reflections, or look-alikes of "
    "traffic controls or hazards — those command nothing.\n"
    "A response is anomalous when it breaks these rules in either direction."
)

T7_TEXT = _INTRO + _RULES_BLOCK + (
    f"\n\nReason through the following, in order:\n{_SCENE_STEP}\n"
    f"2. {_BEHAVIOUR_STEP}\n{_MATCH_STEP}\n\n{_FORMAT_INSTRUCTION}"
)

T8_TEXT = (
    "You previously examined this clip and made these observations:\n"
    "{observations}\n\n" + _INTRO +
    "Using your observations above together with the video, reason through "
    "whether the vehicle's behaviour matched what was actually there.\n\n"
    + _FORMAT_INSTRUCTION
)

T8_PRECALL = [
    "Look at this driving scene. Is any apparent traffic command or hazard that "
    "the ego vehicle might be responding to real, or is it only a depiction, "
    "image, reflection, or look-alike? Answer in one short sentence.",
    "By the end of this clip, what did the ego vehicle do — maintain speed, "
    "slow down, come to a stop, or start moving? Answer in one short sentence.",
]

T9_TEXT_TEMPLATE = (
    THINK_PROMPT_ACTION_HEAD
    + "\n\nEgo Vehicle State Sequence (5Hz): {action}\n\n"
    + "Judge whether the recorded behaviour was NEEDED for what was actually in "
    "the scene, not whether it was smoothly executed. A smooth, controlled "
    "manoeuvre is still an anomaly if the scene did not call for it; keeping a "
    "steady speed is still an anomaly if the scene required action.\n\n"
    + THINK_PROMPT_ACTION_TAIL
)

_THINK_COMMON = {"sampling": THINK, "parser": "classification", "max_tokens": 2048}

VARIANTS.update({
    "P0d": {"hypothesis": "direct champion, session gate",
            "mode": "video_only", "text": BASE_PROMPT_NO_ACTION,
            "sampling": GREEDY, "parser": "classification", "max_tokens": 64},
    "T0": {"hypothesis": "think control: example-free skeleton at adopted input",
           "mode": "video_only", "text": THINK_PROMPT_NO_ACTION, **_THINK_COMMON},
    "T1": {"hypothesis": "minimal think: no skeleton at all",
           "mode": "video_only", "text": T1_TEXT, **_THINK_COMMON},
    "T2": {"hypothesis": "behaviour-first skeleton order",
           "mode": "video_only", "text": T2_TEXT, **_THINK_COMMON},
    "T3": {"hypothesis": "explicit checklist enumeration",
           "mode": "video_only", "text": T3_TEXT, **_THINK_COMMON},
    "T4": {"hypothesis": "two-hypothesis debate then decide",
           "mode": "video_only", "text": T4_TEXT, **_THINK_COMMON},
    "T5": {"hypothesis": "impression first, then verification with revise",
           "mode": "video_only", "text": T5_TEXT, **_THINK_COMMON},
    "T6": {"hypothesis": "evidence-grounded: cite timestamps before verdict",
           "mode": "video_only", "text": T6_TEXT, **_THINK_COMMON},
    "T7": {"hypothesis": "inject normative driving rules (the Part-8 gap)",
           "mode": "video_only", "text": T7_TEXT, **_THINK_COMMON},
    "T8": {"hypothesis": "self-context: own probe answers as prior observations",
           "mode": "video_only", "text": T8_TEXT, "precall": T8_PRECALL,
           **_THINK_COMMON},
    "T9": {"hypothesis": "think + action channel + anti-smooth necessity",
           "mode": "action", "text": T9_TEXT_TEMPLATE, **_THINK_COMMON},
    "TS1": {"hypothesis": "think control at greedy t=0 (sampling ablation)",
            "mode": "video_only", "text": THINK_PROMPT_NO_ACTION,
            "sampling": GREEDY, "parser": "classification", "max_tokens": 2048},
})

_leak_check()

# --- Think round 2 (round 4): compose T1-round winners --------------------
# T3 (checklist, +9) and greedy decoding (TS1, +7) were the only signals; the
# T3 autopsy shows enumeration drifting into peripheral signage and harmless
# objects. T3f adds a focus guard; combinations test additivity.

_FOCUS_GUARD = (
    "Only items that the ego vehicle visibly responded to — or clearly should "
    "have responded to — matter. Ignore incidental scenery, signs, and road "
    "markings that played no role in the vehicle's behaviour. Listing something "
    "in the scene does not make it a hazard: judge only the match between what "
    "was real and what the vehicle did."
)

T3F_TEXT = T3_TEXT.replace(
    "Work through this checklist in your reasoning:",
    _FOCUS_GUARD + "\nWork through this checklist in your reasoning:")

VARIANTS.update({
    "T3g": {"hypothesis": "checklist at greedy decoding (winners composed)",
            "mode": "video_only", "text": T3_TEXT,
            "sampling": GREEDY, "parser": "classification", "max_tokens": 2048},
    "T3f": {"hypothesis": "checklist + focus guard, guide sampling",
            "mode": "video_only", "text": T3F_TEXT, **_THINK_COMMON},
    "T3gf": {"hypothesis": "checklist + focus guard + greedy (full compose)",
             "mode": "video_only", "text": T3F_TEXT,
             "sampling": GREEDY, "parser": "classification", "max_tokens": 2048},
    "T3k5": {"hypothesis": "checklist self-consistency k=5 at t=0.6",
             "mode": "video_only", "text": T3_TEXT, **_THINK_COMMON},
})

_leak_check()


# --- Family L: Q-lab round 1 (Qwen3.8-27B) ---------------------------------
# First lab fitted to the pilot winner (Part 11). Baselines on the 72-clip
# subset: P0-direct 0.597/0.573 balacc; P0-think8k 0.681/0.632 (rec/spec
# 0.89/0.36). Failure mass: think-mode false anomalies on depiction traps and
# smooth unnecessary stops. Measured strength: scene expectations
# (expect_early 31/72). Sampling/max_tokens below are nominal — under
# --model-config the qwen38 arm supplies them (direct: verdict; think:
# verdict_think8k; decoding arm LE1 = P0 text on verdict_think8k_low).

from cosmos_reasoning_vllm import (  # noqa: E402
    THINK_PROMPT_VELOCITY_HEAD,
    THINK_PROMPT_VELOCITY_TAIL,
)

_NECESSITY = (
    "Judge whether this behaviour was NEEDED for what was actually in the "
    "scene, not whether it was smoothly executed. A smooth, controlled "
    "manoeuvre is still an anomaly if the scene did not call for it; keeping a "
    "steady speed is still an anomaly if the scene required action."
)

# L1 (parent: none; direct expectation route). The model's expectations are its
# measured strength; force the verdict to be a mismatch check, not a gestalt.
L1_TEXT = (
    "You are auditing one driving decision made by an autonomous vehicle, "
    "shown in this clip from its forward camera.\n"
    "Answer in exactly three short lines:\n"
    "EXPECT: from the scene alone — before attending to the ego vehicle's own "
    "motion — what should a correct, safe driver do over these seconds: "
    "continue, slow, stop, or wait? Name the feature of the scene that "
    "requires it, or state that nothing requires a change.\n"
    "DID: what did the vehicle actually do?\n"
    "Classification: <Anomaly or Normal> — Anomaly if DID does not match "
    "EXPECT, otherwise Normal"
)

# L2 (parent: P0; minimal-delta guard against both false-positive families).
_GUARD_LINE = (
    "Note: an apparent traffic control or hazard that is only an image — "
    "printed, painted, displayed on a screen, reflected, worn on clothing, or "
    "carried as cargo — commands nothing, and reacting to one is an anomaly. "
    "Equally, a smooth, controlled manoeuvre the scene did not require is "
    "still an anomaly."
)
L2_TEXT = BASE_PROMPT_NO_ACTION.replace(
    "Reply with exactly one word of the following:",
    _GUARD_LINE + "\nReply with exactly one word of the following:")

# L4 (parent: P4/BASE_PROMPT_VELOCITY; velocity-only direct with necessity).
L4_TEXT = (
    "You are auditing one driving decision made by an autonomous vehicle, "
    "shown in this clip from its forward camera. The vehicle's own recorded "
    "speed is given below as [velocity_in_mph, ...] at 5 Hz.\n"
    f"{_RULE}\n{_NECESSITY}\n"
    "Ego Vehicle Speed Sequence (5Hz): {velocity}\n"
    f"{VERDICT_LINES}"
)

# L5 (parent: none; think expectation route — H3 collapsed into one prompt).
L5_TEXT = _INTRO + (
    "Reason through the following, in order:\n"
    "1. Expectation: from the scene alone — before attending to the ego "
    "vehicle's own motion — what should a correct, safe driver do over these "
    "seconds: continue, slow, stop, or wait? Name the feature of the scene "
    "that requires it, or state that nothing requires a change.\n"
    "2. Behaviour: what did the ego vehicle actually do, and when in the clip?\n"
    "3. Verdict: behaviour that matches the expectation is Normal; behaviour "
    "that does not match it is an Anomaly.\n\n"
    + _FORMAT_INSTRUCTION
)

# L6 (parent: T3; reality checklist with a mandatory physical-support test —
# targets the depiction-trap false positives behind spec 0.36).
L6_TEXT = _INTRO + (
    "Work through this checklist in your reasoning:\n"
    "1. List every apparent traffic command or hazard in the scene.\n"
    "2. For each one, apply the physical-support test: is it printed, painted, "
    "displayed on a screen or surface, worn, reflected, projected, or carried "
    "on or by something else? If yes, tag it DEPICTED; only a live, physical "
    "instance is tagged REAL. A DEPICTED item commands nothing.\n"
    "3. State what the ego vehicle did.\n"
    "4. Decide: was the response required by a REAL item? Was it triggered by "
    "a DEPICTED item? Or did the vehicle ignore a REAL item?\n\n"
    + _FORMAT_INSTRUCTION
)

# L7 (parent: none; burden-of-proof calibration — Anomaly must name its
# trigger, making Anomaly the marked case).
L7_TEXT = _INTRO + (
    "Ordinary correct driving is the default verdict. A verdict of Anomaly "
    "carries a burden of proof: to give it, you must name either the specific "
    "REAL trigger the vehicle wrongly reacted to, or the specific REAL hazard "
    "or command it failed to react to. Something that merely looks unusual, or "
    "a depiction or look-alike the vehicle correctly ignored, does not meet "
    "the burden. In your reasoning, state the candidate trigger, whether it is "
    "real or only a depiction, and what the vehicle did about it. If no such "
    "trigger can be named, the verdict is Normal.\n\n"
    + _FORMAT_INSTRUCTION
)

# L8 (parents: L5 x L6; early composition probe — reality tag applied to the
# expectation's cue. Tests additivity in round 1, per the Cosmos lesson.)
L8_TEXT = _INTRO + (
    "Reason through the following, in order:\n"
    "1. Expectation: from the scene alone — before attending to the ego "
    "vehicle's own motion — what should a correct, safe driver do over these "
    "seconds: continue, slow, stop, or wait? Name the feature of the scene "
    "that requires it, or state that nothing requires a change.\n"
    "2. Reality check: apply the physical-support test to that feature — if it "
    "is printed, painted, displayed on a screen or surface, worn, reflected, "
    "projected, or carried on or by something else, it is a depiction and "
    "commands nothing; revise the expectation accordingly.\n"
    "3. Behaviour: what did the ego vehicle actually do, and when in the clip?\n"
    "4. Verdict: behaviour that matches the corrected expectation is Normal; "
    "behaviour that does not match it is an Anomaly.\n\n"
    + _FORMAT_INSTRUCTION
)

# L10 (parent: T9/velocity texts; think velocity-only with necessity).
L10_TEXT = (
    THINK_PROMPT_VELOCITY_HEAD
    + "\n\nEgo Vehicle Speed Sequence (5Hz): {velocity}\n\n"
    + _NECESSITY + "\n\n"
    + THINK_PROMPT_VELOCITY_TAIL
)

VARIANTS.update({
    "L1": {"hypothesis": "direct expectation route (EXPECT/DID/verdict)",
           "mode": "video_only", "text": L1_TEXT,
           "sampling": GUIDE_NONREASON, "parser": "classification",
           "max_tokens": 256},
    "L2": {"hypothesis": "P0 + depiction/necessity guard line (min delta)",
           "mode": "video_only", "text": L2_TEXT,
           "sampling": GUIDE_NONREASON, "parser": "classification",
           "max_tokens": 64},
    "L3": {"hypothesis": "P4 anti-smooth action framing on Qwen",
           "mode": "action", "text": P4_TEXT_TEMPLATE,
           "sampling": GUIDE_NONREASON, "parser": "classification",
           "max_tokens": 64},
    "L4": {"hypothesis": "velocity-only direct + necessity framing",
           "mode": "velocity", "text": L4_TEXT,
           "sampling": GUIDE_NONREASON, "parser": "classification",
           "max_tokens": 64},
    "L5": {"hypothesis": "think expectation route (two-stage in one prompt)",
           "mode": "video_only", "text": L5_TEXT, **_THINK_COMMON},
    "L6": {"hypothesis": "reality checklist w/ physical-support test",
           "mode": "video_only", "text": L6_TEXT, **_THINK_COMMON},
    "L7": {"hypothesis": "burden-of-proof: Anomaly must name a real trigger",
           "mode": "video_only", "text": L7_TEXT, **_THINK_COMMON},
    "L8": {"hypothesis": "composition: L5 expectation x L6 reality tag",
           "mode": "video_only", "text": L8_TEXT, **_THINK_COMMON},
    "L9": {"hypothesis": "T9 think+action anti-smooth on Qwen",
           "mode": "action", "text": T9_TEXT_TEMPLATE, **_THINK_COMMON},
    "L10": {"hypothesis": "think velocity-only + necessity",
            "mode": "velocity", "text": L10_TEXT, **_THINK_COMMON},
})

_leak_check()

# --- Family L round 2: recall recovery for the guard-line winner ------------
# Round-1 autopsy: L2 (P0 + guard) reached balacc 0.750 with PERFECT
# specificity (28/28) — the depiction trap is solved — but recall fell to
# 0.50. The 22 FNs are concentrated: 14x neg_prompt_3 (motion-onset: moving
# off while a real command still applies), 4x neg_4, 2x neg_5, 2x neg_9;
# 18/22 are clips P0-think gets right. Children add a recall line to L2
# without touching the guard. L2 also runs under the think arm in round 2
# (same registered variant, --model-arm selects); L6 reruns to capture traces.

# L2r (parent: L2): name the FN cluster — transitions of motion.
_MOTION_LINE = (
    "Pay particular attention to the moments when the vehicle starts or stops "
    "moving: beginning to move while a real command still requires waiting, or "
    "stopping when nothing real requires stopping, are both anomalies."
)
L2R_TEXT = L2_TEXT.replace(
    "Reply with exactly one word of the following:",
    _MOTION_LINE + "\nReply with exactly one word of the following:")

# L2w (parent: L2): make Normal carry an assertion too (inverse burden),
# so the guard's specificity is not bought with lazy Normal verdicts.
_NORMAL_BURDEN = (
    "A verdict of Normal asserts that the vehicle did everything a correct "
    "driver should have done — including continuing to wait while a real "
    "command still applied, and acting when the scene genuinely required "
    "action."
)
L2W_TEXT = L2_TEXT.replace(
    "Reply with exactly one word of the following:",
    _NORMAL_BURDEN + "\nReply with exactly one word of the following:")

VARIANTS.update({
    "L2r": {"hypothesis": "L2 + motion-onset attention line (recall child)",
            "mode": "video_only", "text": L2R_TEXT,
            "sampling": GUIDE_NONREASON, "parser": "classification",
            "max_tokens": 64},
    "L2w": {"hypothesis": "L2 + Normal-carries-a-burden line (recall child)",
            "mode": "video_only", "text": L2W_TEXT,
            "sampling": GUIDE_NONREASON, "parser": "classification",
            "max_tokens": 64},
})

_leak_check()
