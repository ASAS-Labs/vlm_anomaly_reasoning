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
flow-probe acceptance gate is the production recipe.

| arm | scope | gate | result |
|---|---|---|---|
| C3 | 36 sweep targets (33 stop / 3 maintain), feasible-timing + no-brake prompts | flow probe AND fixed-ID `check_match`, ≤4 seeds (8 in pass 2) | **32/36 repaired**; PROMPT↔VIDEO 71.7% → 98.0%; 96 files pushed to HF (Part 13) |

| C4 | 64 ID-disagreement targets (27 stop / 34 maintain / 3 accel), class-specific prompt fixes | same gate, ≤8 seeds | **36/64 reclaimed** (stop 24/27, maintain 11/34, accel 1/3); 108 files pushed (Part 15) |

Unresolved: 4 from C3 + 28 from C4 (23 maintain-class: generator brakes near
hazards regardless of wording; originals kept, excluded).

## D — Agreement subset construction — (no findings part; `build_agreement_subset.py`)

72/315 admitted (44 anomaly / 28 normal) at the time of families E-L: ID agrees
with prompt AND video does not contradict AND not human-rejected. After the
Part-13 regeneration: 95 admitted; after the Part-14 full ID pass: 199; after
the Part-15 sweep 2: **235 admitted (110 anomaly / 125 normal)**, 0 pending, 80
excluded (28 ID disagrees, 50 human-rejected, 2 video contradicts), 15 scenarios. Lists:
`logs/vlm_agreement_subset_admitted.txt` (199, current),
`logs/vlm_agreement_subset_admitted_v1_72.txt` (the 72 every result in E-L used).
Majority baseline: 0.611 anomaly (72) / **0.532 normal (235)** — near-balanced now.

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

| L2 (235) | P0 + guard line, think@16k, 235-clip subset | 0.745 / balacc 0.732 (0.54/0.93), +29 vs P0 p=.012 | (single seed) | **holds the bar on the near-balanced set (Part 16)** |
| P0 (235) | anchor, think@16k, 235-clip subset | 0.621 / 0.641 (0.95/0.34) | — | — |

**Declared: Qwen3.8-27B + L2 (P0 + one depiction/necessity guard line) +
think @16384 beats the Cosmos champion 0.736/0.693 by +12-15 acc / +15-22
balacc with zero false anomalies in 144 verdicts (72-clip set); re-measured on
the 235-clip set it still clears acc > 0.736 / balacc > 0.70 (Part 16).** The program's 0.70-balacc
ceiling was a missing concept, not capability: Cosmos couldn't use the same
rule (P8 dropped its balacc). 8k budgets truncate guard prompts on ~10% of
clips (12.2); direct-mode single-seed numbers are untrustworthy (12.2).

## M — H-lab: two-stage monitor prompt lab, Qwen3.8 think@16k (80-clip balanced subset) — Part 17

Anchor = L2 (champion, full clip) re-run per session: 60 / 57 / 56 / 57 of 80.

| arm | design | acc (seed) | vs L2 | verdict |
|---|---|---|---|---|
| M0 | verbatim H3 texts @ T−2.5 | 0.613 | −11 | comparator loses 30% given correct expectation |
| M2 | rule + narrative rendering | 0.838 | +7 | **100% given correct expectation**; stage 1 is the ceiling |
| M4 / M5 | guard at stage 1 / guard re-check at stage 2 | 0.775 / 0.762 | +2 / +1 | both levers real |
| M6 / M7 | 1.5 s / 1.0 s windows | 0.600 / 0.588 | −12 / −13 | window ladder flat |
| **M8** | M4 stage 1 × narrative comparator | **0.850 (1234), 0.850 (4321), 0.800 (999)** | +11 / +12 / +7 | **pooled 0.833 vs 0.708, p=0.001 — H-family champion** (per-seed: 1/3 at p<.05) |
| M9 / M10 | + guard re-check / ablate M4 | 0.838 / 0.838 | +10 / +10 | ≈ M8 |
| M11 | M8 + majority-of-3 stage 1 | 0.825 | +10 | no gain: stage-1 errors systematic |
| **M8 (235)** | same config, full 235-clip subset, in-session L2 anchor | **0.830 / balacc 0.826** (0.77/0.88) | **+27 (p=0.002)** vs L2 0.715; +20 (p=0.024) vs the Part-16 L2 0.745 | **headline numbers; holds on the honest set (Part 17.4)** |
| M8 / M8w15 / M8w10 (40 fails) | stage-1 window T−2.5 (control) / T−1.5 / T−1.0 on M8's 40 failed clips | recovered 3 / 12 / 14 of 40 | — | longer window fixes pos_8 (4/4), partial on the mural family, ~none on neg_8; needs a paired 235 run before adoption (17.5) |

Full pipeline, verbatim prompts, and reproduction commands for the declared
M8 configuration: next section (M8 reproduction sheet).

## M8 — reproduction sheet: the declared two-stage monitor (pipeline + verbatim prompts)

Everything below is committed on `vlm-pilot` (prompts: `data/cosmos3/h_variants.py`;
runner: `data/cosmos3/expectation_experiment.py`; driver: `spec/run_hlab_round.sh`;
raw records incl. full reasoning traces: `logs/hlab_r{2,3,4}t_M8/`). The prompt
SHA-256s recorded in every run's `run_meta.json` (`96da9513…` / `8b6cfdf3…`) match
the committed registry texts byte-for-byte.

### 1. Inputs

| item | value |
|---|---|
| Dataset | `ASASLab/av_semantic_anomalies@main` in its post-Part-15 state (315 mp4; v1 fixed-ID trajectories for all 315; 68 regenerated clips). Fetched by `data/cosmos3/fetch_eval_dataset.py` → `data/datasets/generated_vids/` (gitignored; rebuilt from HF). |
| Evaluation subset | `logs/hlab_subset_80.txt` — 40 anomaly / 40 normal drawn from the 235-clip agreement subset (`logs/vlm_agreement_subset_admitted.txt`) by `data/cosmos3/hlab_subset.py` (seed 1234, Hamilton allocation per scenario, admitted-list order). Composition: neg_0 7, neg_2 7, neg_3 5, neg_4 6, neg_5 6, neg_8 2, neg_9 7 · pos_0 5, pos_2 3, pos_4 6, pos_5 5, pos_6 6, pos_8 6, pos_9 4, pos_11 5 (15 scenarios). Gate list `logs/hlab_gate_4.txt` = first neg_0, neg_3, pos_8, pos_0 clip of the subset. |
| Full-clip tree (stage-2 trajectory source) | `data/datasets/generated_vids_720p/` — `make_pilot_trees.py`: 832×480 → 1248×720 lanczos, libx264 crf 12, 8.04 s / 5.04 s whole clips. Beside each mp4 a `<stem>.txt` = the v1 5 Hz trajectory `[[v_mph, heading_deg], …]` (25 rows for 5 s clips, 39 for 8 s; 30 for the 6-s trajectories of a few long clips), byte-identical to `data/datasets/id_variants/v1_resample/` and to the HF-published files (80/80 verified). Copied in by the txt loop of `spec/run_qlab_round.sh`. |
| Stage-1 window tree | `data/datasets/generated_vids_720p_tminus2.5/` — `make_pilot_trees.py --subset logs/hlab_subset_80.txt --early-mode t_minus --early-secs 2.5 --out-early …`: each clip cut from the 720p tree to `duration − 2.5 s` → 73 clips × 2.58 s (62 frames), 7 neg_prompt_0 clips × 5.58 s (134 frames); **video-only** (0 `.txt`; the driver asserts this). |
| Stage-1 GT (diagnostics only) | `data/cosmos3/expected_action_gt.json` — scores `expect_strict/lenient` for the failure-chain table; never enters a prompt. |
| Leak guard | `h_variants._leak_check()` runs at import over both texts of every variant against `prompt_variants.BANNED_WORDS` (scenario vocabulary: billboard, shirt, balloon, bag, mural, wall, child, stop sign, traffic light, pedestrian, …). |

### 2. Model and serving

| item | value |
|---|---|
| Model | `Qwen/Qwen3.8-27B` (bf16, 55 GB), registry key `qwen38` in `data/cosmos3/pilot_models.py` |
| Server | vLLM **0.27.1** in `.venv-pilot` (`spec/setup_pilot.sh`: `uv venv --python 3.13`, `vllm==0.27.1`); one H200 (vast.ai, `vllm/vllm-omni:cosmos3` image, `spec/vast_instance.sh`) |
| Serve command | `vllm serve Qwen/Qwen3.8-27B --allowed-local-media-path / --media-io-kwargs '{"video": {"fps": 8, "num_frames": -1}}' --tensor-parallel-size 1 --max-model-len 32768 --port 8000 --reasoning-parser qwen3` (`pilot_models.serve_command("qwen38")`) — frame sampling is fixed server-side at 8 fps; no per-request `mm_processor_kwargs`. |
| Arm (both stages) | `verdict_think16k`: thinking on; `temperature 1.0, top_p 0.95, presence_penalty 0.0` (OpenAI-native), `top_k 20` via `extra_body`, `max_tokens 16384`; system prompt `"You are a helpful assistant."`; `seed` = run seed on both calls (1234 / 4321 / 999). |
| Concurrency | 4 during the 4-clip gate, 6 for the full run (single writer thread; records fsync'd per clip; resume keyed by `video` with a prompt-hash guard). |

### 3. Per-clip pipeline (two turns, one conversation)

1. **Stage 1 — expectation.** `messages = [system, user[video_url(<tminus2.5 clip>), text=STAGE1]]` → `chat.completions.create(seed, extra_body={"top_k":20}, max_tokens=16384, t=1.0, top_p=.95)`. `pilot_models.answer_text` splits the choice into `content` (final answer) and `reasoning` (the trace, delivered by the `qwen3` reasoning parser in `message.reasoning`). `expect = parse_option(content)`: the option word that *leads* a line, taking the last such line (so a gloss like "…no need to stop" cannot override the final `Continue`); fallback = rightmost option word. Stored: `expect_raw`, `expect`, `expect_strict/lenient`, `expect_finish_reason`, `reasoning_content`.
2. **Stage 2 — comparison.** If stage-1 `content` is empty (unterminated think) the record gets `verdict=Unknown, parse_reason=stage1_empty` and no second call. Otherwise the conversation is extended with `assistant(content)` (reasoning is **not** echoed back) and `user(STAGE2)` where `STAGE2 = M2_STAGE2.format(seq=action_narrative(<v1 trajectory txt>), secs=rows/5)`. Same arm and seed; `max_tokens` is clamped to `32768 − (stage-1 prompt_tokens + len(content)//3 + len(STAGE2)//3 + 256)` (never bound on the 80: all `stage2_max_tokens = 16384`; `RuntimeError` if < 1024). `answer_text` → `utils.parse_verdict(content2, finish_reason)`: the last `Classification: Anomaly|Normal` line in the content wins; no keyword fallback; `Unknown` otherwise. `correct = (verdict == label)`; `Unknown` counts as wrong in every reported accuracy. Stored: `monitor_raw`, `monitor_reasoning_content`, `verdict`, `parse_reason`, `finish_reason` (stage 2), `action_sequence`, `action_rendered`, `stage2_max_tokens`, `latency_s`.
3. The model **never sees the full clip**: stage 1 sees the T−2.5 window only; stage 2 sees the same window (in history) plus the narrative of the whole-clip trajectory. Nothing external is injected — camera + ego-motion only.

### 4. Verbatim prompts

**Stage 1** (`h_variants.M4_STAGE1`; sha256 `96da95137acf2a53911765ad43f31a23084f43c280518a8ec1ad82c16da6168b`):

```
You are evaluating the driving scene in this clip from the ego vehicle's point of view. Based only on what the scene requires — not on how the ego vehicle happens to be moving — what SHOULD a correct, safe driver do over the next few seconds? Name the specific real feature of the scene that requires it, or state that nothing requires a change. Note: an apparent traffic control or hazard that is only an image — printed, painted, displayed on a screen, reflected, worn on clothing, or carried as cargo — commands nothing. Then reply on the final line with exactly one word: Continue, Slow, Stop, or Wait.
Continue — maintain current speed and lane
Slow — reduce speed but keep moving
Stop — brake to a complete stop
Wait — the vehicle is already stationary and should remain stopped
```

**Stage 2 template** (`h_variants.M2_STAGE2` = `_NARR_INTRO + _RULE_BODY`; sha256 `8b6cfdf34a9172ff69d1ef284f79acbacc20a32fad9b2f17a635d0a0d52bd3fc`; `{secs}` = trajectory rows / 5, `{seq}` = the narrative):

```
Measured from the ego vehicle's own motion sensors over the recorded {secs} seconds of this clip: {seq}

Read that motion as exactly one of: continued (speed roughly held), slowed (speed clearly reduced but still moving at the end), stopped (came to rest and stayed there), waited (stationary throughout), or moved off (pulled away from a standstill). Compare it with the expectation you gave. The behaviour MATCHES the expectation only for the action that was expected, with two tolerances: 'continue' and 'slow' are compatible with each other, and an expected 'stop' is satisfied by coming to rest or remaining at rest. Stopping when continue or slow was expected, continuing or merely slowing when stop was expected, and moving off when wait was expected are mismatches.
First state the observed motion class in one short sentence. Then reply on the final line with exactly one of:
Classification: Anomaly — the behaviour does not match the expected action
Classification: Normal — the behaviour matches the expected action
```

**Narrative renderer** (`prompt_variants.action_narrative`; arithmetic only, no model): over the 5 Hz speeds `v` and headings `h`: `start` = mean of first 3, `end` = mean of last 3, `final` = last, `start_shown` = max of first 3; first matching clause wins —
`start ≤ 2 and end ≥ 5` → "the vehicle moved off from a standstill, reaching about {max v} mph";
`final ≤ 2 and start > 5` → "the vehicle slowed from about {start_shown} mph to a complete stop and was stationary at the end";
`end ≤ 0.6·start` → "the vehicle slowed from about {start_shown} mph to about {end} mph, still moving at the end";
`end ≥ 1.4·start` → "the vehicle sped up from about {start} mph to about {end} mph";
else → "the vehicle held a roughly steady speed of about {(start+end)/2} mph";
plus "; its heading changed by up to {max|h|} degrees" when max|h| ≥ 10°. Thresholds are the Part-9 (P5) values, untouched.

Rendered stage 2 for `negative_scenarios_filtered/prompt_0.mp4` (8 s clip, 39 rows):

```
Measured from the ego vehicle's own motion sensors over the recorded 7.8 seconds of this clip: the vehicle slowed from about 45 mph to a complete stop and was stationary at the end.

Read that motion as exactly one of: …   (rule text as above)
```

### 5. Run protocol (`spec/run_hlab_round.sh`)

```
tmux new -s hlab
ROUND=2 SEED=1234 HLAB_ARMS="M8 M9 M10" bash spec/run_hlab_round.sh   # screen  (logs/hlab_r2t_*)
ROUND=3 SEED=4321 HLAB_ARMS="M8 M11"    bash spec/run_hlab_round.sh   # repro   (logs/hlab_r3t_*)
ROUND=4 SEED=999  HLAB_ARMS="M8"        bash spec/run_hlab_round.sh   # tie-break (logs/hlab_r4t_*)
# full 235-clip subset (Part 17.4): M8 first, then the in-session anchor
ROUND=5 PREFIX=hlab_r5 HLAB_ARMS="M8" ANCHOR= BASELINE=L2q \
  HLAB_SUBSET=logs/vlm_agreement_subset_admitted.txt bash spec/run_hlab_round.sh
ROUND=5 PREFIX=hlab_r5 HLAB_ARMS=     ANCHOR=L2 BASELINE=L2 \
  HLAB_SUBSET=logs/vlm_agreement_subset_admitted.txt bash spec/run_hlab_round.sh
```

Each round: build the early trees if missing (assert counts and 0 `.txt`) → assert the
720p tree holds a `.txt` per subset clip → `hf download` → serve (setsid, PID-group
teardown on EXIT, `/health` poll) → **anchor** `prompt_lab.py --variants L2
--model-config qwen38 --model-arm verdict_think16k --dataset generated_vids_720p
--subset logs/hlab_subset_80.txt --out_prefix hlab_r<N>t --seed <S>` (4-clip gate via
`--limit 4`, then full 80) → per arm `expectation_experiment.py --stage monitor
--hvariant M8 --dataset generated_vids_720p_tminus2.5 --full-dataset generated_vids_720p
--subset logs/hlab_gate_4.txt --out_dir logs/hlab_r<N>t_M8 --model-config qwen38
--model-arm verdict_think16k --seed <S> --concurrency 4` → gate (exactly 4 gate
records; verdict Unknown ≤ 2; stage-2 `finish_reason=length` ≤ 1; stage-1 unknown ≤ 2)
→ same command with `--subset logs/hlab_subset_80.txt --concurrency 6` (resume skips
the gate clips) → `prompt_lab_report.py --round <N> --prefix hlab_r<N>t --baseline L2`
(acc, Wilson CI, balacc, rec/spec, McNemar vs L2, breadth, truncations) and
`hlab_report.py --prefix hlab_r<N>t --anchor L2` (stage-1 answer distribution,
strict/lenient, twin divergence, verdict accuracy conditional on stage-1 correctness,
per-stage truncation, flips vs L2 by scenario). The anchor is always re-run in the
same session so the McNemar pairing is within-session. Local dry run (no server):
`expectation_experiment.py --dry_run --stage monitor --hvariant M8 --model-config qwen38
--model-arm verdict_think16k --dataset … --full-dataset … --subset logs/hlab_subset_80.txt`
prints both rendered prompts, hashes and request kwargs; `h_variants.py --print` dumps
every variant's texts and hashes.

### 6. Results and artifacts

| seed | run dir | acc | balacc | rec / spec | anchor L2 | McNemar net (p) | stage-1 lenient | verdict ok \| stage-1 ok | median latency |
|---|---|---|---|---|---|---|---|---|---|
| 1234 | `logs/hlab_r2t_M8` | **0.850** (68/80) | 0.850 | 0.82 / 0.88 | 0.713 (57) | +11 (0.061) | 63/80 | 63/63 | 46 s/clip |
| 4321 | `logs/hlab_r3t_M8` | **0.850** (68/80) | 0.850 | 0.82 / 0.88 | 0.700 (56) | +12 (0.023) | 62/80 | 62/62 | 48 s/clip |
| 999 | `logs/hlab_r4t_M8` | 0.800 (64/80) | 0.800 | 0.82 / 0.78 | 0.713 (57) | +7 (0.248) | 61/80 | 61/61 | 46 s/clip |
| pooled | n = 240 | **0.833** | — | — | **0.708** | **+30 (55 gained / 25 lost), p = 0.001** | — | 186/186 | — |
| 1234, **full 235** | `logs/hlab_r5t_M8` | **0.830** (195/235) | 0.826 | 0.77 / 0.88 | 0.715 (168; `hlab_r5t_L2`) | +27 (0.002); vs Part-16 L2 0.745 (`hlab_r5t_L2q`): +20 (0.024) | 184/235 | 184/184 | ~60 s/clip |

Zero truncations and zero Unknown verdicts in all 240 records; the comparator is
100% faithful whenever stage 1 is right, so every residual error is a stage-1
error. Median reasoning: stage 1 ≈ 5.9k chars, stage 2 ≈ 1.4–1.9k chars; p90
latency ≈ 112 s/clip at concurrency 6 (≈ 20–25 min per 80-clip arm, ≈ $1.5 at
$4/h). Reports: `logs/prompt_lab_hlab_r{2,3,4}t.{md,json}`,
`logs/hlab_diag_hlab_r{2,3,4}t.md`; anchors `logs/hlab_r{2,3,4}t_L2/`. Code
state: commits `bb67095` (lab) → `187d6dd` (review fixes) → `d86b2c6` (round-2
slate, M8 registered) → `e72dc62`, `cfb7b52`, `6686e5f` (results/declaration).

### 7. Reproducibility notes (honest limits)

- Sampling is t = 1.0 on both stages: a given seed reproduces the *protocol*, not
  bit-identical outputs (vLLM continuous batching at concurrency 6 is not
  deterministic). The three seeds gave 68 / 68 / 64 — treat ±4 clips as the
  run-to-run band; the paired in-session anchor is what makes the comparison valid.
- `run_meta.json` records `git_commit: ""` because the instance ran an rsync'd
  working tree, not a git checkout; the recorded prompt hashes are the binding
  provenance, and they equal the registry at `6686e5f`.
- The video trees and trajectory txts are not in git (`data/datasets/` is
  ignored); they are rebuilt deterministically from the HF dataset by
  `fetch_eval_dataset.py` → `make_pilot_trees.py` (+ the v1 txt copy). The 720p
  tree's `pilot_tree_manifest.json` currently lists the 80-clip subset because the
  last tree build passed that subset (the 235 mp4s are still present).
- The T−2.5 stage-1 window shows most of the braking for the stop-type
  scenarios (Part 17.1); M8's remaining errors are stage-1 anchoring on that
  motion, not comparator errors.

## N — SFT of M8's stage 1 (Qwen3.8-27B LoRA, decision-time windows, 235 clips) — Part 18

Pre-registered: CV-concatenated SFT stage 1 inside the unchanged M8 comparator vs an
in-session zero-shot M8gt anchor on the same 235 (McNemar p<0.05 AND balacc higher;
second seed to declare). Targets = self-distilled rationale+word (235/235 tier 1);
LoRA r16 ms-swift 4.5.2, 2 epochs, 5 s/sample, ~$2.5/fold; video-token parity 0.0 %.

| arm | split | acc | balacc | rec/spec | vs anchor | verdict |
|---|---|---|---|---|---|---|
| anchor M8gt zero-shot (early_gt tree) | — | 0.821 (193/235) | 0.818 | 0.76/0.87 | — | paired baseline |
| **N1 SFT stage 1, leave-scene-group-out 5-fold** | f1 mural+pos_6, f2 bags+neg_3, f3 billboard+pos_11, f4 balloons, f5 shirt+child | **0.736** (173/235) | 0.731 | 0.65/0.81 | **−20 (+7/−27), p=0.0008** | **FAIL** — commits the sibling scene's rule onto the unseen scene (mural → continue, bags → stop); only balloons (bags in train) transfer (35/35) |
| N2 SFT stage 1, within-scenario 5-fold (diagnostic) | every scene in train | pending | | | | learnability ceiling, reported separately |

## Failure chain (as currently localized)

perception 100% → **policy generation 25–53%** (Cosmos; ~43% Qwen3.8) →
comparison ~70% → verdict.

## Open / planned

- Two-stage monitor (H3) re-run on Qwen3.8 expectations — first post-pilot step.
- Verdict-prompt fit for Qwen3.8 (P0 is Cosmos-shaped; family I laws may not
  transfer across models).
- Maintain-class generation residual (23 clips): needs scene-side prompt changes
  (hazard placement), not motion wording — dataset-paper note.
- Seed-4321 reproduction of the L2 champion on the 235-clip subset (~$4).
- H-lab next lever: first-frame (0.3 s) stage 1 for stop-type scenes; seed-4321
  reproduction of M8 on the full 235 (~$5) before quoting 0.830 as final.
- SFT on expectation generation: leave-scene-out FAILED (Part 18); within-scenario
  diagnostic pending; any further SFT needs more scenes per concept, not more clips.
- Native-720p generation (F2 suggests it pays).
