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

## Failure chain (as currently localized)

perception 100% → **policy generation 25–53%** → comparison ~70% → verdict.

## Open / planned

- H4/H5: Cosmos3-Super stage-1 (in progress).
- Full-dataset fixed-ID pass (195 clips, incl. 21 long clips @ 7.5 fps) →
  finalize agreement subset.
- Closed-loop regeneration (C2 recipe + flow-probe gate) for the 15-clip list.
- SFT on stage-1 expectation generation (single-word supervised task).
- Native-720p generation (F2 suggests it pays).
