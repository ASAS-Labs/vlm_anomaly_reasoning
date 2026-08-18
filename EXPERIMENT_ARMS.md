# Experiment Arms

Living map of every experimental arm in this investigation. One row per arm;
update when arms are added or re-run. Detailed analysis lives in
`VLM_FINDINGS.md` (parts referenced per section); raw artifacts under `logs/`.

Conventions: **n** = clips evaluated; *direct* = one-word-verdict prompt, greedy;
*think* = reasoning prompt (example-free from family E onward), t=0.6;
input = 832×480 @ 4 fps unless stated. Model = Cosmos3-Nano unless stated.

## A — Full-set VLM eval (315 clips, published/broken trajectories) — Part 1

| arm | mode | style | acc | artifact |
|---|---|---|---|---|
| A1 | video-only | direct | 0.5968 | `logs/full_no_action_grounding` |
| A2 | action (v+h) | direct | 0.5905 | `logs/full_action_grounding` |
| A3 | video-only | think (contaminated) | 0.5924 | `logs/full_think_no_action_grounding` |
| A4 | action (v+h) | think (contaminated) | 0.5714 | `logs/full_think_action_grounding` |

Majority baseline 0.5333. A3/A4 disqualified (billboard example primed
`neg_prompt_0`: 0.048 → 0.762). Headline: action grounding never helps.

## B — ID trajectory variants (120-clip balanced sample) — Parts 2, 5

Semantic agreement = does the trajectory match the prompt; VLM = direct/action
arm on that variant's trajectories.

| arm | variant | agreement | VLM acc | note |
|---|---|---|---|---|
| B0 | v0_baseline (published) | 48.3% | 0.5417 | broken time base + coverage |
| B0t | v0_timebase (×2.4) | 38.3% | 0.5583 | scale alone can't fix coverage |
| B1 | v1_resample (10 fps + trim) | **63.3%** | 0.5583 | **the fix; shipped** |
| B2–B5 | edges/signed/smooth/5Hz-avg | 63.3–62.5% | 0.50–0.55 | add nothing; rejected |

Decomposition (Part 5): VIDEO↔ID **98.1%**, PROMPT↔VIDEO 71.7% → generation,
not ID, is the gap. Instruments: flow probe (`video_motion.py`),
`fidelity_report.py`; regeneration list `logs/id_regeneration_list.json`.

## C — Video regeneration (Phase D) — Part 5.3

| arm | prompts | scenarios × seeds | stop-completion (terminal flow) |
|---|---|---|---|
| C1 | original dense | 2 × 3 | pos_9: {0.21, 0.32, 0.38} — none stop |
| C2 | physics-feasible timing | 2 × 3 | pos_9: {0.02, 0.17, 0.29} — 8/9 pairwise better |

Same prompt + same seed ≠ same video (generation is stochastic) → best-of-N with
flow-probe acceptance gate is the production recipe. Paused by decision;
resume before dataset finalization.

## D — Agreement subset construction — (no findings part; `build_agreement_subset.py`)

72/315 admitted (44 anomaly / 28 normal): ID agrees with prompt AND video does
not contradict AND not human-rejected. 147 pending fixed-ID (deferred GPU pass),
96 excluded. List: `logs/vlm_agreement_subset_admitted.txt`. Majority baseline
on subset: 0.611 (anomaly-majority).

## E — Clean-subset VLM eval (72 clips, v1 trajectories) — Part 6

| arm | mode | style | acc [95% CI] |
|---|---|---|---|
| E1 | video-only | direct | **0.639** [0.524, 0.740] |
| E2 | action (v+h) | direct | 0.569 |
| E3 | velocity-only | direct | 0.431 (vs E1: −15, p=0.008) |
| E4 | video-only | think | 0.583 |
| E5 | action (v+h) | think | 0.458 |
| E6 | velocity-only | think | 0.472 |

Headline: action channel pushes verdicts toward Normal (46→35→21 anomaly
verdicts) — smooth dynamics read as normalcy, and 25/44 anomalies are smooth
unnecessary stops. Artifacts: `logs/subset_{direct,think}_*`.

## F — Input ablation (72 clips, direct arms) — Part 7.2

| arm | input | video-only | action | velocity-only |
|---|---|---|---|---|
| F0 (=E1–E3) | 480p @ 4 fps | 0.639 | 0.569 | 0.431 |
| F1 | 480p @ 8 fps | 0.611 | 0.514 | 0.500 |
| F2 | **720p↑ @ 8 fps** | **0.736** (+8/−1, p=0.039) | 0.611 | 0.486 |

720p upscale (prompt_tokens 7,971 → 11,691) is the only input change that helps;
first CI to clear the majority baseline. fps alone inert.
Artifacts: `logs/subset8_direct_*`, `logs/subset8hires_direct_*`.

## G — Perception probes (72 clips, no anomaly framing) — Part 7.1

| arm | input | scene probe | action probe |
|---|---|---|---|
| G1 | 480p @ 4 fps | **72/72** | 58/72 |
| G2 | 480p @ 8 fps | 70/72 | 58/72 |
| G3 | 720p↑ @ 8 fps | 72/72 | 58/72 |

All 14 action-probe misses = `neg_prompt_3` start-of-motion (never answers
"started"). Verdict acc when perception fully correct: 72.4%; when wrong: 28.6%.
Artifacts: `logs/probe_{4fps,8fps,8fps_hires}`.

## H — Expected-vs-actual two-stage monitor (72 clips, 720p↑ @ 8 fps) — Part 8

Stage-1 GT: `expected_action_gt.json` (field-4 Normal Action, validated against
positive-twin classes; never enters a prompt).

| arm | stage | model | strict | lenient | note |
|---|---|---|---|---|---|
| H1 | expect_early (2.5 s window) | Nano | 18/72 | 38/72 | hedges "slow" 34/72; never "stop" |
| H2 | expect_full (whole clip) | Nano | 22/72 | 40/72 | anchors on outcome (19× "stop" on continue-scenes) |
| H3 | monitor (2-turn verdict) | Nano | 38/71 correct | — | 70.3% when H1 right, 35.3% when wrong |
| H4 | expect_early | **Super** (2×H200, TP=2) | 8/72 (22/72 adj.) | 26/72 (40 adj.) | decisive but not wiser; see 8.4 |
| H5 | expect_full | **Super** | 12/72 | 27/72 | |

Mechanical ceiling (GT expectation + perfect compare): **100%** — the
formulation is sound; the gap is expectation generation.
Artifacts: `logs/{expect_early,expect_full,monitor}` (+`_super`).


## I — Prompt/context lab, direct regime (72 clips, 720p↑ @ 8 fps) — Part 9

720p input adopted as standard from this family onward. Baseline P0 re-run each
session as gate (0.736 / 0.750 across sessions — stable).

| arm | round | idea | acc | recall/spec | verdict |
|---|---|---|---|---|---|
| P0 | 1,2 | released prompt (champion) | **0.736 / 0.750** | 0.89/0.50 | keep |
| S1 | 1 | guide non-reasoning sampling | 0.722 | 0.93/0.39 | no gain |
| S2 | 2 | self-consistency k=5 t=0.7 | 0.722 | — | no gain |
| P4 | 1 | anti-smooth action framing | 0.653 | 0.57/0.79 | best action arm ever; still < P0 |
| P6 | 1 | abstract definitions | 0.639 | 0.43/0.96 | P0's ROC mirror (balacc 0.698 vs 0.693) |
| P5 | 1 | narrative action summary | 0.625 | 0.57/0.71 | < P0 |
| P1 | 1 | crisp decision rule | 0.611 | 0.55/0.71 | < P0 |
| P9 | 2 | P6 defs + P0 question | 0.667 | 0.64/0.71 | balacc 0.675 < P0 |
| P8 | 2 | P0 + scenery-vs-response line | 0.528 | 0.43/0.68 | balacc DROPS (0.555) |
| P3 | 1 | binary correct/incorrect | 0.444 | 0.09/1.00 | Normal collapse |
| P2 | 1 | CUE/ACTION scaffold | 0.417 | 0.09/0.93 | Normal collapse |
| P10 | 2 | P8 + 1-line rationale | 0.403 | — | collapse |
| P7 | 1 | examiner pass/fail | 0.333 | — | 24 unparsed + poor |

**Law of the lab**: 13 wordings, one ROC curve. Direct prompts move the
operating point (bias), never the discrimination (balanced accuracy ceiling
~0.70). Best offline 2-prompt ensemble (P0 OR P5) 0.764, exploratory/overfit.
Declared: prompt engineering alone cannot reach the 0.80 target; champion stays
the original P0 wording. Artifacts: `logs/plab_r{1,2}_*`,
`logs/prompt_lab_round{1,2}.md`.


## J — Prompt/context lab, think regime (72 clips, 720p↑ @ 8 fps) — Part 10

Guide reasoning sampling (t=0.6/top_p .95/top_k 20) unless noted; P0d = direct
champion gate (0.736 / 0.722 across the two sessions — reproduces incl. on
H200 NVL).

| arm | round | idea | acc | verdict |
|---|---|---|---|---|
| T0 | 3 | example-free skeleton (control) | 0.500 | think costs ~24 pts vs direct |
| T1 | 3 | no skeleton | 0.472 | skeleton not the problem |
| T2 | 3 | behaviour-first order | 0.403 | worst structure |
| T3 | 3 | checklist enumeration | 0.625 | best think arm (round 3) |
| T4 | 3 | two-hypothesis debate | 0.458 | — |
| T5 | 3 | impression-then-verify | 0.514 | — |
| T6 | 3 | cite timestamps | 0.556 | — |
| T7 | 3 | normative-rules injection | 0.556 | Part-8 gap not closable in-context |
| T8 | 3 | self-context (own probe answers) | 0.597 | — |
| T9 | 3 | think + action + anti-smooth | 0.458 | — |
| TS1 | 3 | T0 at greedy | 0.597 | t=0.6 costs ~7 clips on T0 |
| T3g | 4 | checklist × greedy | 0.514 | **composition fails: below both parents** |
| T3f | 4 | checklist × focus guard | 0.486 | fails |
| T3gf | 4 | checklist × guard × greedy | 0.542 | fails |
| T3k5 | 4 | checklist k=5 majority | 0.611 | ≈ single-sample T3 |

**Declared (stopping rule): the think regime is closed.** Round-3 "signals"
(T3 +9, TS1 +7) do not survive composition — consistent with selection noise at
n=72 (binomial σ ≈ 4 clips over 12 arms). Best think result anywhere (0.625)
never approaches the direct champion (0.722-0.750). Reasoning remains a net
liability for Cosmos3-Nano on this task. Artifacts: `logs/plab_r{3,4}_*`.

## K — Open-VLM pilot (72 clips, 720p↑ @ 8 fps) — Part 11

Six candidates screened in card-default mode via `pilot_models.py` registry;
arms: expect_early (primary; Cosmos bar 18/72 strict), expect_full, P0 direct
verdict (Cosmos bar 0.736). Full table `logs/pilot_report.md`; raw `logs/pilot_*`.

| arm | model | early s/l | full s/l | verdict | note |
|---|---|---|---|---|---|
| K1 | **Qwen3.8-27B** | **31/46** | 30/44 | 0.597 | winner; adopted |
| K2 | Qwen3.6-27B | 30/41 | 28/35 | 0.694 | best pilot verdict |
| K3 | Qwen3.5-27B | 29/42 | 32/38 | 0.639 | gain starts here (Feb 2026) |
| K4 | Qwen3-VL-32B-Thinking | 19/37 | 20/37 | 0.681 | ≈ Cosmos bar: post-training not the cause |
| K5 | InternVL3_5-38B | 22/34 | 39/46 | 0.653 | early→full jump = outcome anchoring |
| K6 | GLM-4.6V-Flash | 11/28 | 13/32 | 0.528 | stop-happy (rec/spec 0.25/0.96) |

Think-verdict arms (Part 11.4; resolved acc, rec/spec):

| arm | model | direct verdict | think verdict | note |
|---|---|---|---|---|
| K1t | **Qwen3.8-27B** | 0.597 | 0.815 res. 54/72 (0.97/0.53) | 18 truncations; see K1t8k — the 0.749 balacc was censoring |
| K1t8k | Qwen3.8-27B @8192 | — | **0.681 all-72** (0.91/0.36) | balacc 0.632; truncated clips resolve 7/18 — 11.4 ceiling claim retracted |
| K2t | Qwen3.6-27B | 0.694 | 0.698 res. (1.00/0.10) | discrimination collapses |
| K3t | Qwen3.5-27B | 0.639 | 0.647 res. (1.00/0.04) | all-anomaly collapse |
| K6t | GLM-4.6V-Flash | 0.528 | 0.597 (0.50/0.75) | mild help |
| K5t | InternVL3_5-38B | 0.653 | 0.528 (0.61/0.39) | thinking hurts |

Headline: the Qwen 3.5+ generation nearly doubles expect_early strict (+11-13
clips) with breadth (8/12 scenarios vs Cosmos's 2) and no outcome anchoring;
same-lineage K4 at the Cosmos bar shows it's generational, not post-training.
Verdicts: no pilot config beats Cosmos's P0 champion (P0 is Cosmos-tuned);
thinking helps only Qwen3.8 (0.597→0.681 @8192) and its apparent 0.749 balacc
at 4096 was truncation censoring (Part 11.5). **Winner declared: Qwen3.8-27B**
on the stage-1 discriminator; verdict-prompt fitting is the open lever.

## L — Q-lab: prompt/context iteration on Qwen3.8-27B (72 clips, 720p↑ @ 8 fps) — Part 12

Pre-registered loop (promote/kill/repro rules); anchors re-run per session.
Rounds: r1 screen (13 arms) → r2 recall children → r3 @16k + repro.

| arm | config | screen (s1234) | repro (s4321) | verdict |
|---|---|---|---|---|
| **L2** | **P0 + guard line, think@16k** | **0.806 / balacc 0.841** (0.68/1.00) | **0.889 / 0.909** (0.82/1.00, +13 p=.019) | **CHAMPION** |
| L2r | + motion-onset line, think@16k | 0.806 / 0.834 | 0.792 / 0.804 | passes; dominated by L2 |
| P0 | anchor, think@16k | 0.694 / 0.646 | 0.708 / 0.657 | — |
| L2 | direct | 0.694-0.708 / 0.75-0.76 (spec 1.00) | — | direct is seed-brittle (12.2) |
| L1/L5/L8 | expectation-route prompts | 0.431-0.639 | — | killed: stage-1 skill doesn't fold into verdicts |
| L3/L4/L9/L10 | action/velocity channels | 0.292-0.528 | — | killed: video-only law transfers |
| L7 / LE1 | burden-of-proof / reasoning_effort=low | 0.472 / 0.667 | — | killed |

**Declared: Qwen3.8-27B + L2 (P0 + one depiction/necessity guard line) +
think @16384 beats the Cosmos champion 0.736/0.693 by +12-15 acc / +15-22
balacc with zero false anomalies in 144 verdicts.** The program's 0.70-balacc
ceiling was a missing concept, not capability: Cosmos couldn't use the same
rule (P8 dropped its balacc). 8k budgets truncate guard prompts on ~10% of
clips (12.2); direct-mode single-seed numbers are untrustworthy (12.2).

## Failure chain (as currently localized)

perception 100% → **policy generation 25–53%** (Cosmos; ~43% Qwen3.8) →
comparison ~70% → verdict.

## Open / planned

- Two-stage monitor (H3) re-run on Qwen3.8 expectations — first post-pilot step.
- Verdict-prompt fit for Qwen3.8 (P0 is Cosmos-shaped; family I laws may not
  transfer across models).
- Full-dataset fixed-ID pass (195 clips, incl. 21 long clips @ 7.5 fps) →
  finalize agreement subset.
- Closed-loop regeneration (C2 recipe + flow-probe gate) for the 15-clip list.
- SFT on expectation generation — now on Qwen3.8 if zero-shot plateaus.
- Native-720p generation (F2 suggests it pays).
