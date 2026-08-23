# VLM Anomaly Reasoning — Findings

Record of two investigations: the VLM evaluation (Aug 2026) and the inverse-dynamics
(ID) trajectory repair. Every number below is reproducible from artifacts committed
under `logs/` and `outputs/`.

**Bottom line.** Action grounding does not improve semantic-anomaly classification with
Cosmos3-Nano in any configuration tested — not with the direct prompt, not with
reasoning enabled, and not after the ego-action trajectories were measurably fixed. All
configurations sit 4–6 points above a majority-class baseline. The paper's `[65%]` →
`[90%]` claim is not supported by these runs.

---

## Part 1 — VLM evaluation

### 1.1 The output parser could not have produced trustworthy numbers

`utils.parse_classification` had four compounding defects:

1. `re.search` took the **first** `Classification:` match, so a `<think>` preamble that
   rehearsed the wrong answer overrode the real verdict.
2. `--max_tokens 100` truncated a reasoning model before it emitted any verdict.
3. On truncation it fell through to a **keyword-frequency scan**. "Anomaly" saturates
   both the prompt echo and the reasoning trace, so truncated outputs resolved to
   Anomaly almost unconditionally.
4. `Unknown` was folded into `Normal`, and errors never reached `Metrics`, so accuracy
   was computed over an unstated subset.

(2)+(3) together mean a run could report a strong action-grounding effect that was
purely an artifact of the token budget.

**Fix**: `parse_verdict` separates `<think>` from the answer body, takes the **last**
verdict, and reports `Unknown` with a reason rather than guessing. The keyword fallback
is deleted. `data/cosmos3/test_parse.py` pins all 15 cases including the exact bug.
`reparse_results.py` re-derives verdicts from stored `raw_output`, so a parser mistake
never costs another GPU run.

### 1.2 The frame-rate setting was inert

`mm_processor_kwargs={"fps": 4, "do_sample_frames": True}` did two wrong things at once:

- `do_sample_frames=True` **400'd every request** — the vLLM media loader had already
  sampled the video, and asking the processor to sample again against the original
  timeline throws `Failed to apply Qwen3VLProcessor`.
- Probing five configs against a live server returned **identical `prompt_tokens=2005`**
  for every variant that set `fps` or `num_frames`. Frame sampling lives in the
  **media loader** (`--media-io-kwargs`, default `fps: 2`), so the run would have used
  2 fps, half the documented rate, with nothing in the output revealing it.

**Fix**: `--media-io-kwargs '{"video": {"fps": 4, "num_frames": -1}}'` at the server and
no `mm_processor_kwargs` in the request. Verified by `prompt_tokens` 2005 → 3995.

### 1.3 Results — four configurations, 315 clips each

147 anomaly / 168 normal. Coverage 1.000 except where noted; parser deterministic on
re-parse in every run.

| Run | Accuracy | Precision | Recall | Specificity | F1 |
|---|---|---|---|---|---|
| direct, video-only | **0.5968** | 0.5505 | 0.7415 | 0.4702 | 0.6319 |
| direct, action-grounded | 0.5905 | 0.5570 | 0.5986 | 0.5833 | 0.5770 |
| think, video-only | 0.5924 | 0.5776 | 0.4589 | 0.7083 | 0.5115 |
| think, action-grounded | 0.5714 | 0.5517 | 0.4354 | 0.6905 | 0.4867 |

Majority-class baseline (always Normal): **0.5333**.

Paired comparisons, all net-negative and within noise:

| Comparison | Gains | Loses | Net | Verdicts changed |
|---|---|---|---|---|
| action vs video-only (direct) | 27 | 29 | −2 | 56 (18%) |
| action vs video-only (think) | 51 | 57 | −6 | 108 (34%) |
| think vs direct (video-only) | 81 | 83 | −2 | 164 (52%) |
| think vs direct (action) | 76 | 82 | −6 | 158 (50%) |

Action grounding shifts the operating point — recall 0.74 → 0.60, specificity 0.47 →
0.58 — so the action channel *is* read. It just does not improve discrimination.
Reasoning changes over half the verdicts and also nets nothing.

### 1.4 The direct prompt suppresses reasoning entirely

Under the original prompts the model emitted **2–5 tokens** with no `<think>` block at
all (`'Normal'`, `'Classification: Normal'`), at 0.62 s/clip. The prompt ends with
"Reply with exactly one word", which forbids the chain-of-thought the Reasoner exists to
produce. The direct results therefore measure immediate judgement, not reasoning.

### 1.5 The think prompt leaked an example — do not use these numbers

`--prompt_style think` follows the Cosmos3-Reasoner guide's format and does produce
genuine reasoning (2.3 s/clip, ~360 completion tokens, traces that explicitly cite the
velocity sequence). But the prompt names the billboard stop sign as an illustrative
example, and that **is** scenario `neg_prompt_0`:

| | `neg_prompt_0` (primed) | all other scenarios |
|---|---|---|
| direct prompt | 1/21 = **0.048** | 0.629 |
| think prompt | 16/21 = **0.762** | 0.558 |

Naming the scenario moved it from 4.8% to 76.2% while every other scenario got *worse*.
The think numbers are propped up by the one primed scenario. **An example-free think
prompt is required before those numbers mean anything.** The second example (fire hose)
matches no scenario in this taxonomy and is inert.

### 1.6 Confound to note

Think mode uses the guide's reasoning sampling (temperature 0.6); direct is greedy
(temperature 0.0). Direct-vs-think comparisons carry that difference. The
action-vs-video-only comparisons *within* each style hold sampling constant and are
clean — and those are the ones that bear on the paper's claim.

---

## Part 2 — Inverse dynamics

### 2.1 Root cause: the model never saw the behaviour it was asked about

`ACTION_CHUNK_SIZE = 60` flows into `read_media_frames(path, max_frames=61)` →
`frames[:61]` with **no temporal resampling**
(`cosmos_framework/inference/action.py:163`, `vision.py:188-191`). Videos are 24 fps, so
the model saw **2.54 s of a 5.04 s clip**. The prompts deliberately place the
label-defining action in the final ≥2 s — exactly the discarded part.

Confirmed in data: `negative_scenarios_filtered/prompt_0` ("decelerates to a stop")
reads 28.8 → 20.0 mph and never nears zero.

### 2.2 Second cause: wrong time base

Velocity used `hz = FPS = 10` while frames are 1/24 s apart, scaling every published
speed by 10/24 = 0.417. Median cruise speed on "maintain" clips was **12.1 mph**;
×2.4 gives 28.9 mph, inside a plausible band.

### 2.3 The trap: padding fabricates stops

`build_action_batch` (`action.py:88-93`) pads short inputs with
`video[:, -1:].repeat(...)` — it **duplicates the last frame**. Resampling to 10 fps
gives ~50 real frames plus ~11 duplicates. Untrimmed, a naive fix would fabricate a stop
in every clip and look like a triumph.

Measured on the box (8 clips): the padded tail reads 0.2–2.2 mph. It is not exactly zero
— the model is *predictive*, not a frame-differencer — but it is effectively stopped.
Where it matters:

| Clip | Real ending | Padded tail | Effect if untrimmed |
|---|---|---|---|
| `prompt_9` ("runs into the wall **with no deceleration**") | 13.4 mph | 1.7 mph | fabricates a stop, inverting the scenario |
| `prompt_3` ("starts moving") | 5.6 mph | 1.3 mph | destroys the acceleration signal |

Trimming to `n_valid` is mandatory and is pinned by `id_trajectory_test.py`.

### 2.4 Other defects found (not the main cause)

- Velocity was an **unsigned 2D chord magnitude**, so pose jitter gives a stationary
  vehicle a positive speed floor; it can never read exactly 0, and reverse is invisible.
- `v[0]` derives from an identity-seeded pose 0 against a full-error pose 1, making the
  first sample the least constrained in the series.
- The 5 Hz file decimated poses then re-differenced (a 0.2 s chord) while headings were
  plain decimation — two different operators on the two channels.
- No smoothing, clamping, or outlier rejection anywhere.
- The "decelerate" validation was a **ratio** test, which can never verify a stop: a car
  slowing 30 → 17 mph passes, and a stationary car that stays stationary fails.

### 2.5 Method

One GPU inference pass at 10 fps, persisting raw poses (`outputs/id_raw.jsonl`, 1.7 MB
for 120 clips). Every other variant is pure offline post-processing of those poses, so
the derivation can be iterated forever without a GPU. Variant trees symlink the original
24 fps videos and carry only new `.txt` files, so no eval code changed.

Scope: 120-clip balanced sample from the 294 uniform 5.04 s clips; the 21 8.04 s clips
were excluded (at 10 fps they need 80 frames, past the 61-frame chunk). Expectations
were frozen to `data/cosmos3/id_expectations.json` and hand-audited before use, so the
language classifier cannot drift between variants.

### 2.6 Primary result — semantic agreement (VLM-free, n=120)

Does the recovered trajectory match what the prompt says the vehicle did?

| Variant | Agreement | `stop` ≤2 mph | `accelerate` | `maintain` | Cruise mph | McNemar vs baseline |
|---|---|---|---|---|---|---|
| `v0_baseline` (released) | 48.3% | 23/65 | 3/21 | 32/34 | 12.1 | — |
| `v0_timebase` (×2.4 only) | 38.3% | 11/65 | 3/21 | 32/34 | 28.9 | −12, p=0.0005 |
| **`v1_resample`** | **63.3%** | **35/65** | **14/21** | 27/34 | 24.2 | **+18, p=0.005** |
| `v2_edges` | 63.3% | 35/65 | 14/21 | 27/34 | 24.2 | +18, p=0.005 |
| `v3_signed` | 63.3% | 35/65 | 14/21 | 27/34 | 24.2 | +18, p=0.005 |
| `v4_smooth` | 63.3% | 35/65 | 14/21 | 27/34 | 24.2 | +18, p=0.005 |
| `v5_final` | 62.5% | 34/65 | 14/21 | 27/34 | 24.2 | +17, p=0.009 |

**Resampling to 10 fps is the whole fix.** It repairs coverage and the time base at once:
agreement 48.3% → 63.3% (p=0.005), `accelerate` 3/21 → 14/21 (those clips start moving at
the end, previously never observed), median stop-terminal velocity 3.6 → 1.6 mph.

**The other four fixes contribute nothing measurable.** Edge repair, signed forward-axis
velocity, smoothing, and consistent 5 Hz averaging all land on identical agreement; v5 is
one clip worse. They do reduce jitter (`|dv|` 0.69 → 0.55). Recommendation: ship
`v1_resample`; the rest is unnecessary complexity.

`v0_timebase` is the useful decomposition — ×2.4 alone makes speeds plausible yet drops
stop agreement to 16.9%, because scale cannot fix a coverage problem.

Caveats: `maintain` regressed slightly (32/34 → 27/34). Edge-outlier rate rose 12.5% →
~48%, partly an artifact — trimmed sequences are shorter and more dynamic, so the
MAD-based detector fires more readily.

### 2.7 Secondary result — VLM accuracy is unchanged (n=120, direct prompt)

| Variant | Accuracy | 95% CI | vs baseline |
|---|---|---|---|
| `v0_baseline` | 0.5417 | [0.453, 0.628] | — |
| `v0_timebase` | 0.5583 | [0.469, 0.644] | +2, p=0.82 |
| `v1_resample` | 0.5583 | [0.469, 0.644] | +2, p=0.82 |
| `v2_edges` | 0.5500 | [0.461, 0.636] | +1, p=1.00 |
| `v3_signed` | 0.5417 | [0.453, 0.628] | 0, p=1.00 |
| `v4_smooth` | 0.5000 | [0.412, 0.588] | −5, p=0.33 |
| `v5_final` | 0.5250 | [0.436, 0.612] | −2, p=0.80 |

**Measurably better trajectories did not produce better VLM accuracy.** Combined with
Part 1, the evidence is that Cosmos3-Nano does not exploit the ego-action channel for
this task — whether or not that channel is correct.

Pre-registered limitation: n=120 gives roughly ±9-point CIs, so only a large effect is
detectable. This is "no detectable change", not "no effect". The semantic-agreement
metric is the primary evidence and is far better powered per clip.

---

## Part 3 — Open issues

1. **`translation_scale = 1.35`** is a hardcoded constant whose documented source
   (`av_dataset.py`) is **absent** from the vendored framework. Every absolute mph figure
   rests on it. Held fixed across all variants so it cannot confound, but unverified.
   The post-fix cruise median of 24.2 mph is at least plausible for these scenes.
2. **Example-free think prompt** — required before any think-mode number is usable.
3. **The 21 long clips** (8.04 s) remain unfixed; at 10 fps they need 80 frames against a
   60-frame chunk.
4. **Publishing corrected trajectories** to `ASASLab/av_semantic_anomalies` has not been
   done. `--upload` and `--write-inplace-txt` default off, and upload is refused when
   `--videos-root` is not the released tree.

## Part 4 — Paper discrepancies found along the way

- **Clip lengths are not uniform**: of 339 clips, 316 are 121 frames (5.04 s) but **23
  are 193 frames (8.04 s)**. §II-B and Table III both state 5 s.
- **Resolution**: files are 832×480. §III-A/Table III's "480p" is correct; §II-B's
  "720p (1280×720)" is wrong.
- **Provenance split doesn't sum**: "112 scenario pairs … 42 REAL and 58 SYNTHETIC" —
  42 + 58 = 100, not 112.
- **Clip count**: the draft says `[396]` videos; the release contains **339**.
- **Skip lists** hold 47 entries (16 negative + 31 positive), not 44.

## Reproducing

```bash
# free, no GPU
cd data/cosmos3
python test_parse.py                 # parser regressions
python id_trajectory_test.py         # padding + time-base regressions
python semantic_agreement.py --freeze-expectations
python derive_action_files.py --raw ../../outputs/id_raw.jsonl --variants all
python semantic_agreement.py         # reproduces the Part 2.6 table
python reparse_results.py ../../logs/full_*/results.jsonl --check --histogram
```

Artifacts: `logs/full_*` (Part 1), `logs/id_v*` and `logs/id_semantic_agreement*.json`
(Part 2), `outputs/id_raw.jsonl` (raw poses — all variants re-derivable offline).

---

## Part 5 — Why ID agreement stalled at 63%, and what actually fixes it

### 5.1 Decomposition: the ID pipeline is not the bottleneck

An optical-flow ego-motion probe (`video_motion.py`: median flow over the road
region, robust to moving scene objects, with a measurability gate for
blur-saturated highway/night clips) provides a model-free witness of what each
clip depicts. Over the 120-clip sample (`fidelity_report.py`):

| Relationship | Agreement | Meaning |
|---|---|---|
| VIDEO <-> ID | **52/53 = 98.1%** | the fixed ID pipeline reports what is on screen |
| PROMPT <-> VIDEO | **38/53 = 71.7%** | generation does not realize the prompted action |
| PROMPT <-> ID | 76/120 = 63.3% | the conflated metric |

Supporting evidence: failures concentrate in 3 of 14 scenarios; 7 of the 8 hard
non-stops were already on the human skip list; near-miss clips (ID final 2-10 mph)
show sustained pixel motion at clip end — the videos end mid-brake. The single
ID<->video disagreement is a clip at 3.3 vs a 2.0 mph threshold. 67 clips are
excluded per-measure where the probe cannot judge (52 blur-saturated at speed,
15 genuinely ambiguous creeping endings).

**Implication: no ID change can reach 90% agreement against the prompt, because
~45% of stop-class videos never depict the prompted ending. Measured against the
video — the only ground truth ID can be accountable to — the pipeline is already
at 98%.**

Negative results (all free, from persisted poses): heading drift (median 17-20
deg on straight braking) is identical when derived from displacement direction
instead of the rot6d column, so the predicted positions genuinely curve; signed
forward velocity does not change the one velocity-floor case; raising probe
resolution shrinks flow instead of recovering blur-saturated clips.

### 5.2 Root cause of generation infidelity: physically impossible prompt timing

The failing dense prompts demand a complete stop from cruise inside ~1 second
(neg_prompt_4: braking 0:01-0:02; pos_prompt_9: 0:02-0:03), contradicting the
paper's own guidance that a smooth stop takes 2.5-4 s. The generator renders
sustained braking instead, and the clip ends before zero.

### 5.3 Regeneration experiment (2 scenarios x 2 arms x 3 seeds, 36 s/clip)

`regen_experiment.py` compares the original prompts against a physics-feasible
rewrite (2 s braking window ending at 0:03/0:03.5 + locked-off stationary hold),
judged by the flow probe (`logs/regen_flow_profiles.json`):

- **pos_prompt_9** (0/3 dataset clips ever stopped): terminal flow orig
  {0.21, 0.32, 0.38} vs strong {0.02, 0.17, 0.29} — the strong arm ends lower in
  8/9 pairwise comparisons, and its best seed is a textbook decel-to-stop
  (0.17 -> 0.02). Directional, not significant at n=3.
- **neg_prompt_4**: both arms mostly ended stopped in this batch — unlike the
  dataset batch where 1/8 stopped — which leads to the more important finding:
- **Generation is not reproducible.** The same prompt + same seed (1234, the
  dataset's seed) produced a different video (different hash, different motion
  profile; the regen pos_prompt_9 clip *accelerates* where the dataset clip
  cruised). Per-clip motion outcome is effectively stochastic.

### 5.4 Recommended path to 90%+ prompt-level agreement

1. **Fix the prompt timing** (feasible braking windows) — cheap, directionally
   helpful.
2. **Closed-loop generation**: because outcomes are stochastic, generate
   best-of-N seeds per scenario and accept clips with the flow probe (+ ID
   cross-check at 98% agreement) — an automated acceptance gate at 36 s/clip
   makes this practical (~$0.04/attempt on an H200).
3. Exclude or regenerate the 15 clips on `logs/id_regeneration_list.json`
   (6 already human-flagged).
4. The ID pipeline itself needs no further work.

---

## Part 6 — Clean-subset rerun: action grounding hurts, and now we know why

Setup: the 72-clip prompt-video-ID agreement subset (44 anomaly / 28 normal), fixed
v1_resample trajectories, example-free think prompt (billboard/fire-hose/garment
wording removed from every step after the leak finding), three arms per style:
video-only, action (velocity+heading), velocity-only. Majority baseline (always
Anomaly): 61.1%. Artifacts: `logs/subset_eval_report.{json,md}`,
`logs/subset_{style}_{mode}/`.

| run | acc | 95% CI | P | R | spec | F1 |
|---|---|---|---|---|---|---|
| direct / video-only | **0.639** | [0.524, 0.740] | 0.696 | 0.727 | 0.500 | 0.711 |
| direct / action (v+h) | 0.569 | [0.454, 0.677] | 0.686 | 0.545 | 0.607 | 0.608 |
| direct / velocity-only | 0.431 | [0.323, 0.546] | 0.571 | 0.273 | 0.679 | 0.369 |
| think / video-only | 0.583 | [0.468, 0.690] | 0.733 | 0.500 | 0.714 | 0.595 |
| think / action (v+h) | 0.458 | [0.348, 0.573] | 0.581 | 0.409 | 0.536 | 0.480 |
| think / velocity-only | 0.472 | [0.361, 0.586] | 0.594 | 0.432 | 0.536 | 0.500 |

Paired McNemar (within style): action vs video-only −5 (direct, p=0.30) and −9
(think, p=0.14); **velocity-only vs video-only −15 (direct, p=0.008)**; velocity-only
vs action −10 (direct, p=0.041). With 8 comparisons, Bonferroni leaves the strongest
at p≈0.065 — marginal, but every action arm is negative in both styles.

### 6.1 The mechanism: smooth dynamics read as normalcy

The verdict distributions show what the action channel actually does: video-only
direct says Anomaly 46/72; add the full trajectory and it drops to 35/72; strip
heading and it drops to 21/72. Recall collapses 0.727 → 0.545 → 0.273 while
specificity rises. The action channel systematically pushes the model toward
"Normal".

That is anti-correlated evidence *for this dataset by construction*: 25 of the 44
anomalies are FP-polarity scenarios whose anomalous behaviour IS a smooth,
controlled, unnecessary stop (braking for balloons, bags, a stop-sign shirt). A
clean decel-to-zero profile looks like safe, competent driving in isolation — the
model reads orderly dynamics as normalcy precisely where the label says the
orderliness is the anomaly. Heading noise partially masked this in the full-action
arm; removing it (velocity-only) makes the trajectory look even smoother and the
bias stronger. The clip-level evidence matches: `pos_prompt_8` (correct stop for a
child crossing) goes 0/5 under direct video-only and direct action but **5/5 under
velocity-only** — the same "smooth stop = normal" heuristic, which happens to be
right there.

### 6.2 Other observations

- Even the best run (0.639) does not significantly beat the 61.1% majority baseline
  (CI includes it). On clean data, Cosmos3-Nano still cannot do this task.
- The example-free think prompt confirms the earlier leak diagnosis in reverse:
  `pos_prompt_0` (billboard-normal) is 6/6 under direct but **1/6 under example-free
  think** — with no primed example, reasoning talks itself into false alarms on the
  billboard scene.
- `neg_prompt_3` (starts moving when a green balloon overlaps the red light) fails
  under every arm (0–6/14): temporal causality ("moved *because* the light looked
  green") appears out of reach regardless of grounding.
- Thinking never beats direct on the subset (−4 and −8 net, n.s.), consistent with
  the full-set result once the leak is removed.

### 6.3 Implication for the paper's framing

The hypothesis "the action channel was too corrupted for grounding to help" is now
tested and rejected: with trajectories verified at 98% fidelity against the pixels,
grounding still does not help — it hurts, through the smooth-equals-normal prior.
Making action grounding work here likely requires the prompt to state the *expected*
action for the scene (so the model compares actual vs expected) rather than
presenting the raw trajectory and hoping the model infers that smoothness can be
wrong. n=72 caveat: CIs are ±11 points; treat magnitudes, not exact values.

Run cost: $0.91 (H200, 40 min, all six runs + smoke).

---

## Part 7 — Perception probes and input-resolution ablation

Two experiments on the 72-clip subset: factual probe questions with no anomaly
framing (separating cannot-see from cannot-judge), and verdict reruns at higher
frame rate and resolution. Artifacts: `logs/probe_{4fps,8fps,8fps_hires}/`,
`logs/subset8_direct_*/`, `logs/subset8hires_direct_*/`. Session cost ~$2.40.

### 7.1 Perception is essentially solved — except start-of-motion

| probe | 4fps | 8fps | 8fps+720p |
|---|---|---|---|
| scene (sign real vs shirt/billboard, road objects, signal colour, wall, pedestrian) | **72/72** | 70/72 | 72/72 |
| action (Stopped / Moving / Started at clip end) | 58/72 | 58/72 | 58/72 |

Scene perception is perfect: the model correctly reports that the stop sign is on
a shirt (19/19) or a billboard (6/6), identifies balloons vs bags, reads signal
colour, and recognises the mural wall. **All 14 action-probe misses are the same
scenario**: `neg_prompt_3` (vehicle starts moving at a red light) — answered
"moving" 9× and "stopped" 5×, never "started", at every fps/resolution. The model
cannot perceive the start-of-motion event, which fully explains that scenario's
verdict failure under every arm (Part 6). Every other scenario: 58/58.

Splitting verdicts (direct video-only, 4fps) by probe correctness:

- perception fully correct → verdict accuracy **42/58 = 72.4%**
- perception partly wrong → **4/14 = 28.6%**

So the earlier "perception-limited" interpretation is largely wrong: on the 81% of
clips the model perceives correctly, judgment still errs 28% of the time — the
dominant failure is the judgment step, plus one specific perceptual blind spot
(motion onset).

### 7.2 Resolution helps the verdict; frame rate does not

Upscaling 832×480 → 1248×720 (lanczos; no new information, but the Qwen3-VL-style
processor allocates visual tokens by pixel area: prompt_tokens 7,971 → 11,691):

| config | video-only | action (v+h) | velocity-only |
|---|---|---|---|
| 4 fps (baseline) | 0.639 [0.524, 0.740] | 0.569 | 0.431 |
| 8 fps | 0.611 (net −2, p=0.73) | 0.514 | 0.500 |
| **8 fps + 720p** | **0.736 [0.624, 0.824]** (net **+8/−1**, p=0.039) | 0.611 | 0.486 |

- **8fps+720p video-only is the first configuration whose CI lower bound (0.624)
  clears the 61.1% majority baseline**, and the paired gain vs 4 fps is +8/−1
  (p=0.039, uncorrected among 6 config comparisons — promising, not conclusive).
- Frame rate alone does nothing (net −2). The gain is resolution, i.e. the
  encoder's internal token budget — the probes stayed flat because they were
  already saturated, but the finer-grained representation improves the judgment
  margin.
- The action-grounding ordering is unchanged at every config:
  video-only > action > velocity-only. Better input does not rescue the
  smooth-equals-normal bias.

### 7.3 Recommendations

1. **Feed the model more visual tokens.** Either upscale as preprocessing (proven
   here at zero information gain) or regenerate at native 720p, which also adds
   real detail. This is the single cheapest accuracy lever found so far.
2. Start-of-motion is a perceptual blind spot; scenarios that hinge on motion
   onset need either explicit temporal-localization prompting or should be
   weighted separately in evaluation.
3. Action grounding remains net-negative in all nine configurations tested;
   the expected-vs-actual reformulation (Part 6.3) is still the untested path.

---

## Part 8 — Two-stage expected-vs-actual monitor: the deficit is policy knowledge

Deployment-legitimate design (no oracle inputs): stage 1 asks what a correct
driver SHOULD do, from the first 2.5 s only (the polarities of a scenario pair
share that window, so the expectation cannot anchor on the outcome); stage 2
supplies the actual recorded trajectory in a second turn and asks for a match
verdict. Stage-1 ground truth (`expected_action_gt.json`, framework field 4) was
validated against each scene's positive-twin frozen class (12/13 mechanical,
neg_prompt_3 textual) and never enters a prompt. Artifacts:
`logs/{expect_early,expect_full,monitor}/`. Session ~$1.20.

### 8.1 Stage 1 fails: 25% strict / 53% lenient

| GT \ answer | continue | slow | stop | wait |
|---|---|---|---|---|
| continue (n=41) | 4 | **29** | 8 | 0 |
| slow (n=4) | 4 | 0 | 0 | 0 |
| stop (n=13) | 5 | 5 | **0** | 3 |
| wait (n=14) | 0 | 0 | 0 | **14** |

Three patterns:

- **A hedging prior**: "slow" is the answer 34/72 times — the safe-sounding middle
  option, used for balloons, bags, the shirt pedestrian, and even the mural wall.
- **Zero commitment to "stop"** on the early window: not for the child stepping
  into the road (0/6), not for the wall dead ahead (0/4). With the FULL clip
  visible, the wall scene still never gets "stop" — this is absent normative
  knowledge, not hidden evidence.
- "wait" is perfect (14/14) — trivial, since the vehicle is visibly stationary.

The `expect_full` arm exposes anchoring instead of fixing policy: with the whole
clip visible, continue-scenes are answered "stop" 19× (vs 8 early) because the
anomalous vehicles actually stop — the "expectation" follows the observed
behaviour. The early-window design is therefore necessary, and clip-end
contamination explains part of why single-pass verdicts read smooth stops as
normal.

### 8.2 The pipeline is sound; the model link is not

- Monitor verdict accuracy: 38/71 = 53.5% overall — but **70.3% when stage 1 was
  (leniently) correct vs 35.3% when it was wrong**. The comparison step works
  about as well as the best single-pass run once given a correct expectation.
- **Mechanical ceiling: GT expectation + perfect comparison = 72/72 = 100%** on
  this subset. The formulation separates the classes perfectly; the entire gap is
  the model's inability to generate the expectation.

### 8.3 The failure chain, fully localized

perception (100%) → **policy: what should a correct driver do (25-53%)** →
comparison given a correct expectation (~70%) → verdict.

Cosmos3-Nano sees the scene, and can compare behaviours, but does not know (or
will not commit to) what correct driving requires — it answers like a cautious
hedger, not a driving instructor. That reframes the road ahead:

1. **Inject the expectation from deployment-available sources where possible** —
   traffic-light state, map topology, and detected-object class already imply
   rules ("red → wait", "pedestrian in path → stop") without any oracle; the VLM
   then only arbitrates the residual semantic cases (shirt vs real sign).
2. **Fine-tune stage 1** on normative driving data (the framework ships SFT
   recipes); stage-1 accuracy is a supervised, single-word task with cheap labels
   — far easier to train than end-to-end verdicts.
3. Re-examine answer-option design (a forced binary stop/no-stop may cut the
   "slow" hedge), though the wall result suggests option wording is not the core
   problem.

### 8.4 Cosmos3-Super stage-1 (H4/H5): scale buys decisiveness, not semantics

Super (64B, TP=2 on 2×H200) on the identical early-window protocol: 8/72 strict,
26/72 lenient — nominally far below Nano (18/72, 38/72). But the aggregate hides
an option-reading artifact: on `neg_prompt_3` (vehicle already stationary at a
red light, GT "wait") Super answered "stop" 14/14 where Nano answered "wait"
14/14 — for an already-stopped vehicle those are the same commitment. Scoring
{stop, wait} as equivalent there gives **Super 22/72 adjusted vs Nano 18/72**:
roughly parity.

The interesting differences are structural:

- **Super commits.** 28 "stop" answers vs Nano's 8; the "slow" hedge shrinks in
  favour of decisions. It gets the rule-based scenes Nano missed: approaching red
  light 3/3 (Nano 0/3), child crossing 2/5 (Nano 0/5), night-glare slow 2/4
  (Nano 0/4).
- **Semantic displacement scenes fail identically at both scales**: stop-sign
  shirt 0/19, balloons 0/8, bags 0/8, billboard 1/6 (worse than Nano's 4/6) —
  and the mural wall gets "Continue" 4/4, an answer that would drive into the
  wall, worse than Nano's "slow".

Conclusion: 4× parameters improves rule-following policy (traffic lights,
pedestrians) but does not touch the semantic-context judgment the taxonomy
actually tests. The missing capability is not general driving knowledge but the
displaced-context reasoning itself — consistent with SFT on stage-1 labels,
rather than scale, being the lever. Session cost ~$5.6.

---

## Part 9 — Prompt lab (direct): one ROC curve, no discrimination gains

Thirteen prompt/context variants over two rounds on the 72-clip subset at the
adopted 720p/8fps input, each targeting a measured failure mode (crisp decision
rule, forced-commitment scaffold, de-loaded binary, anti-smooth and narrative
action framings, abstract definitions, persona, hybrid grafts) plus two sampling
arms (guide non-reasoning settings, self-consistency k=5). Session-P0 gates
reproduced (0.736, 0.750). Full tables: `logs/prompt_lab_round{1,2}.md`;
EXPERIMENT_ARMS family I.

**Result: every variant slides along one ROC curve.** P0 is the recall-heavy end
(0.89/0.50); P6 is its specificity mirror (0.43/0.96) at the same balanced
accuracy (0.698 vs 0.693); the reframed binary and scaffold collapse to Normal
(spec 1.00 / recall 0.09). The surgical round-2 test is conclusive: P0's 19
errors were 14× "scene looks concerning but response correct", and grafting one
scenery-vs-response sentence onto the otherwise-verbatim champion fixed the
targeted clips (pos_8 1/5 → 5/5) while losing 9/19 of neg_2 — and dropped
balanced accuracy to 0.555. The model cannot apply the concept selectively; any
nudge shifts the global decision boundary. Self-consistency and the guide's
sampling settings change nothing.

**Declaration (per the pre-registered stopping rule): prompt engineering alone
cannot reach 0.80 on this task with Cosmos3-Nano.** The champion remains the
original released wording at 0.736-0.750, which wins largely because its
anomaly-leaning bias matches the subset's 61% anomaly base rate. Discrimination
(~0.70 balanced accuracy) is prompt-invariant — consistent with Parts 7-8: the
deficit is judgment/policy knowledge, which wording cannot inject. Exploratory
footnote: the best two-prompt ensemble (P0 OR P5) reaches 0.764, i.e. ensembling
buys threshold tuning, not understanding.

Implications for the think-stage engineering (next): expect the same law; the
think stage should therefore test *structured evidence composition* (the model's
own probe answers in context) rather than wording variations, and the real
levers remain SFT on expectation labels (Part 8) and dataset expansion.
Lab cost: ~$4 across two sessions.

---

## Part 10 — Think-regime prompt lab: closed with a null

Sixteen arms over two rounds (12-arm broad screen + 4 compositions) at the
adopted 720p/8fps input, example-free throughout, leak-guarded, with the direct
champion re-run as a per-session gate (0.736 → 0.722 across sessions and across
an H200→H200 NVL hardware change). Tables: `logs/prompt_lab_round{3,4}.md`;
EXPERIMENT_ARMS family J.

1. **Thinking starts 24 points behind.** The example-free think control scores
   0.500 vs the direct champion's 0.736 at identical input. No structure
   (checklist, debate, verify-revise, evidence-citing, reordering), no knowledge
   injection (normative rules, self-generated probe context), no action framing,
   and no decoding change closes the gap: the best think arm ever is 0.625.
2. **Round-3 signals were noise.** Checklist (+9) and greedy decoding (+7) —
   the only positive deltas in the screen — *both* failed to survive
   composition: checklist×greedy scored 0.514, below either parent, and k=5
   majority voting merely reproduced the single-sample checklist. With 12 arms
   at n=72 (binomial σ≈4 clips), two +7..9 outliers are expected by chance; the
   composition round existed precisely to catch this, and did.
3. The trace autopsy explains the mechanism qualitatively: the model often
   *correctly identifies* the semantic trick (e.g. names the mural illusion)
   and then reasons past it — enumerating peripheral signage, re-weighing
   irrelevant details, and landing on the wrong verdict. Deliberation gives the
   wrong prior more chances to win, exactly as Part 6 first observed.

**Overall prompt-engineering conclusion (families I + J, 29 arms):** the
released direct prompt at 720p/8fps remains the champion (0.72-0.75). Neither
regime's wording, structure, context, nor decoding moves discrimination.
The remaining levers are the ones prompting cannot reach: SFT on expectation
labels (Part 8), dataset expansion (the pending 195-clip ID pass), and
generation-fidelity repair (Part 5). Think-lab cost: ~$5 across three sessions
(one interrupted by a host stop; results recomputed).


## Part 11 — Open-VLM pilot: the Qwen 3.5+ generation doubles driving judgment

Six open VLMs screened against the Cosmos bars on the 72-clip agreement subset
(720p↑ @ 8 fps), each in its card-recommended default mode, three arms per model
(expect_early = primary discriminator, expect_full, P0 direct verdict). Harness:
`pilot_models.py` registry + `--model-config/--concurrency` extensions of the
existing runners; full table in `logs/pilot_report.md`, raw per-clip records with
reasoning traces under `logs/pilot_*`.

| model | early strict/lenient | full strict/lenient | verdict (rec/spec) |
|---|---|---|---|
| Cosmos3-Nano (bar) | 18 / 38 | 22 / 40 | **0.736** |
| **Qwen3.8-27B** | **31 / 46** | 30 / 44 | 0.597 (0.68/0.46) |
| Qwen3.6-27B | 30 / 41 | 28 / 35 | 0.694 (0.86/0.43) |
| Qwen3.5-27B | 29 / 42 | 32 / 38 | 0.639 (0.82/0.36) |
| Qwen3-VL-32B-Thinking | 19 / 37 | 20 / 37 | 0.681 (0.89/0.36) |
| InternVL3_5-38B | 22 / 34 | 39 / 46 | 0.653 (1.00/0.11) |
| GLM-4.6V-Flash | 11 / 28 | 13 / 32 | 0.528 (0.25/0.96) |

### 11.1 The headline: a generational capability, not a post-training artifact

The Qwen 3.5/3.6/3.8 generation clusters at 29-31/72 strict on expect_early —
+11 to +13 clips over Cosmos-Nano, on the exact capability Parts 7-9 localized
as the bottleneck. Qwen3-VL-32B-Thinking (late-2025, the same lineage Cosmos is
post-trained from) sits at 19/72 ≈ the Cosmos bar: swapping Cosmos post-training
for general post-training changes nothing. The judgment gain arrived with the
Qwen 3.5 base generation (Feb 2026, the ERQA-jump release) and holds through 3.8.

Where the gain lives (qwen38 vs Cosmos, expect_early per scenario): Cosmos's 18
was 14/14 on the trivial red-light "wait" scenario plus 4/6 on one more, zero on
8 of 12 scenarios, hedging "slow" on 34/72 clips. Qwen3.8 scores on 8/12
scenarios with a sane answer distribution (17 continue / 22 slow / 16 stop / 14
wait), including positives Cosmos never got (pos_8 4/5, pos_11 2/3) and 3/19 on
the stop-shirt depiction trap where Cosmos had 0. The shared residual: the
depiction-trap negatives (neg_2 3/19, neg_4/5/8 = 0) remain the hard core.

### 11.2 Caveats and secondary findings

- **Truncation understates the Qwens.** 3-11 clips/arm exceeded the 4096-token
  think budget and score as misses (qwen36 early lost 11). The ranking is
  unaffected; the leaders' true numbers are a few clips higher.
- **expect_full anchoring flags InternVL.** Its 22→39 early→full jump is
  outcome-reading, not judgment (the early window exists to expose this);
  Qwen 3.5+ is flat early↔full — its expectations come from the scene.
- **P0 verdicts don't transfer.** No pilot beats Cosmos's 0.736 on the P0
  wording (best: qwen36 0.694) — P0 is Cosmos's tuned champion on an
  anomaly-majority subset, and Part 9 says wording ≠ discrimination. The
  expectation arms, not this, were the pre-registered discriminator.
- GLM-4.6V-Flash (10B) over-triggers stop/slow everywhere (verdict rec/spec
  0.25/0.96 — the opposite bias of every other model).

### 11.3 Decision

**Qwen3.8-27B is the working model going forward** (best expect_early, no
anchoring, newest line), with qwen36/qwen35 as in-family fallbacks. Next steps:
re-run the two-stage monitor (H3) on Qwen3.8 expectations — the Part-8 ceiling
says accurate expectations + comparison is the working formulation; revisit
verdict prompting for Qwen (P0 is Cosmos-shaped); optionally rerun the truncated
clips at an 8192 budget. Pilot cost ≈ $8 (H200 @ $3.97/hr, ~2h, incl. one
box-token parse fix caught by the 4-clip verdict gate).

### 11.4 Think-verdict arms: thinking helps exactly one model — the winner

P0 verdict re-run in think mode for the slate (qwen3vl32t's original verdict
already was think mode). Resolved-accuracy / recall/spec, with strict-all in
parentheses where truncation cost coverage (4096-token budget):

| model | direct verdict | think verdict | think effect |
|---|---|---|---|
| **Qwen3.8-27B** | 0.597 (0.68/0.46) | **0.815 resolved, 54/72** (0.97/0.53; 0.611 all) | **balacc 0.749 — first config above the 0.70 ceiling** |
| Qwen3.6-27B | 0.694 (0.86/0.43) | 0.698 resolved (1.00/0.10) | discrimination collapses (balacc 0.645→0.55) |
| Qwen3.5-27B | 0.639 (0.82/0.36) | 0.647 resolved (1.00/0.04) | all-anomaly collapse |
| Qwen3-VL-32B-T | — | 0.681 (0.89/0.36) | (always-think) |
| GLM-4.6V-Flash | 0.528 (0.25/0.96) | 0.597 (0.50/0.75) | mild help |
| InternVL3_5-38B | 0.653 (1.00/0.11) | 0.528 (0.61/0.39) | thinking hurts |

Qwen3.8 + thinking is the only configuration in the entire program (13 direct
wordings, 16 think arms on Cosmos, 6 pilot models) to break the ~0.70
balanced-accuracy ceiling: 0.749 on 54 resolved clips, recall 34/35 with
specificity 10/19. Its 18 truncations are class-balanced (9/9), so the resolved
subset is not skewed; the obvious cheap follow-up is an 8192-budget re-run to
convert the censored 25% into a clean full-set number. For every other Qwen,
thinking inflates anomaly-recall to 1.00 while destroying specificity — the
regime that was a pure liability for Cosmos (T0 0.500) is a liability for them
too. Cost: ~$6 (5 downloads + runs, ~1.5 h).

**Winner declared: Qwen3.8-27B** — best expect_early (31/72, the pre-registered
discriminator), no outcome anchoring, and the only above-ceiling verdict
configuration (think mode). Working configuration going forward: Qwen3.8-27B,
think mode for verdicts (budget ≥8192), card think sampling.

### 11.5 8192-budget re-run: the 0.749 balacc was a censoring artifact — retracted

Re-running qwen38 verdict_think at max_tokens 8192 resolved all 18 previously
truncated clips: **7/18 correct**. Full-set: 49/71 resolved (0.690; 0.681
strict-all), recall 0.91 / specificity 0.36, **balanced accuracy 0.632**. The
run is otherwise highly stable (of 53 clips resolved in both runs: 43 correct at
4096, 42 at 8192, one flip — t=1.0 sampling noise is negligible).

Section 11.4's "first configuration above the 0.70 ceiling" claim is therefore
**retracted**: thinking length correlates with difficulty, and the model is
wrong on most of the clips it deliberates longest about, so truncation censored
exactly the failures. Corrected think-verdict picture for Qwen3.8: 0.681 acc /
0.632 balacc — better than its own direct verdict (0.597 / 0.57 balacc) but
below the Cosmos P0 champion (0.736 / ~0.693 balacc).

Corrected conclusions:
- **No pilot configuration beats Cosmos's P0 verdict yet.** P0 is Cosmos's own
  tuned wording; a Qwen-fitted verdict prompt is untested (family-I laws were
  measured on Cosmos only).
- **The winner call is unchanged**: it rests on the pre-registered stage-1
  discriminator (expect_early 31/72 vs 18/72, essentially uncensored — only 3
  truncations), where Qwen3.8's lead is real, not on verdict wording.
- Working config amended: Qwen3.8-27B; verdicts in think mode at 8192 (0.681 >
  direct 0.597), with verdict-prompt fitting as the open lever. The path Part 8
  identified — expectation + comparison — is where the model's measured
  advantage actually lives.

## Part 12 — Q-lab: the guard line breaks the ceiling; champion declared

Formal iterative prompt lab on Qwen3.8-27B (family L), 72-clip subset,
720p↑ @ 8 fps, pre-registered promotion/kill/repro rules, anchors re-run every
session. Success bar (user-set): acc > 0.736 AND balacc > 0.70 on screen AND
reproduction. Artifacts: `logs/qlab_*`, reports `logs/prompt_lab_qlab_*`.

### 12.1 Round 1 (13 arms): one live signal

Direct: P0 0.625; **L2 (P0 + one depiction/necessity guard line) 0.694 with
balacc 0.750 and PERFECT specificity (28/28)** — the depiction trap solved
outright. Everything else lost to its anchor: expectation-route prompts (L1
direct 0.431, L5 think 0.583 — the model's stage-1 skill does NOT survive
being folded into a verdict prompt), burden-of-proof (L7 0.472, recall
collapse), action/velocity channels (0.292-0.528 — the video-only law
transfers to Qwen in both regimes), reasoning_effort=low (0.667, axis dead).
Think anchor 0.722/0.669.

### 12.2 Round 2: recall child + regime port

L2's 22 FNs were nameable (14× motion-onset). L2r (= L2 + one motion-onset
attention line): direct 0.736/0.784 (spec 1.00); think@8k 0.750/0.782 — first
arm past the accuracy bar, with 7 truncations scored as misses. L2 family holds
spec 0.93-1.00 everywhere. Two beat-downs from the repro machinery: (a) the
seed-4321 direct repro showed direct-mode verdicts are strongly seed-sensitive
(L2r rec/spec swung 0.57/1.00 → 0.93/0.61; same-seed round-to-round stability
had masked it — single-seed direct numbers are not trustworthy); (b) the
seed-4321 think@8k repro died at the truncation gate (2/4 gate clips) —
guard-family prompts think past 8k on ~10% of clips.

### 12.3 Round 3 (@16k) + reproduction: declaration

verdict_think16k removes the truncation tax entirely (0 truncations, all runs):

| arm | screen s1234 | repro s4321 |
|---|---|---|
| **L2** | **0.806 / balacc 0.841** (0.68/1.00) | **0.889 / balacc 0.909** (0.82/1.00), McNemar +13 p=0.019 |
| L2r | 0.806 / 0.834 (0.70/0.96) | 0.792 / 0.804 (0.75/0.86) |
| P0 anchor | 0.694 / 0.646 | 0.708 / 0.657 |

**CHAMPION DECLARED: L2 — the P0 prompt plus one guard line — in think mode at
16384 tokens.** Both runs clear the bar with margin; specificity is 1.00 in
both (zero false anomalies across 144 clip-verdicts); pooled acc ≈ 0.85,
balacc ≈ 0.88. L2r also passes both runs but is dominated by its simpler
parent at the honest budget — its 8k recall gain was partly truncation rescue.

The guard line (verbatim, in `prompt_variants.py` as `_GUARD_LINE`): "an
apparent traffic control or hazard that is only an image — printed, painted,
displayed on a screen, reflected, worn on clothing, or carried as cargo —
commands nothing, and reacting to one is an anomaly. Equally, a smooth,
controlled manoeuvre the scene did not require is still an anomaly."

### 12.4 What moved and why

Against Cosmos's champion (0.736 acc / 0.693 balacc): +12-15 points accuracy
and +15-22 balacc. The entire program's ~0.70 balacc ceiling was a missing
CONCEPT, not missing capability: Cosmos could not use the depiction rule
(family I tried; P8's scenery line DROPPED its balacc), while Qwen3.8 applies
it near-perfectly once stated. One sentence of context did what 29 Cosmos
arms, model scale (Super), thinking budgets, and channel engineering could
not. Remaining failure mass: recall on subtle missed-response anomalies (L2 FNs
now concentrate in neg_3/neg_4 singles at 16k).

Working config going forward: **Qwen3.8-27B, L2 prompt, think mode,
max_tokens 16384, card think sampling** (t=1.0/top_p 0.95/top_k 20). Lab cost
≈ $21 across 3 screens + 2 repro sessions.

## Part 13 — Generation-fidelity repair: closed-loop regeneration lands 98%

The Part 5.4 recipe, executed (`data/cosmos3/regen_fix.py`, driver
`spec/run_regen_remote.sh`; one H200 session ≈ 2.5 h ≈ $9 incl. two passes).

### 13.1 Targets: a full re-sweep, not just the 15-clip list

Joining the frozen prompt expectations with the 315-clip flow verdicts gave
**36 contradicting clips** (the historical 15 are a strict subset): 33
stop-class clips that never stop (neg_4 7, neg_5 8, pos_9 14, neg_2 1, pos_4/5/8
a few) and 3 maintain-class clips that stop. All are 832×480/121-frame variants;
11 are human-flagged. `logs/regen_targets.json`.

### 13.2 The fix is in the prompt, applied surgically

The 33 stop prompts carried the same impossible beat — a 1 s stop from cruise —
in every scenery variant (the variation skill preserves the timeline verbatim).
`feasible_timing()` rewrites only that beat: 2 s smooth braking ending by 0:03
(or 0:03.5), a locked-off stationary hold, matching camera/caption text; each
variant's own scenery wording is kept. Maintain-class prompts get an explicit
no-braking constraint (`maintain_reinforce`). Prompts of record are updated in
place (`video_gen_prompts/...`, `_regen_fix` stamp; git archives the old text).

### 13.3 Best-of-N with a two-instrument gate

Per target, up to 4 fresh seeds (8 in pass 2); accept the first clip whose flow
probe matches the class **and** whose fixed-ID trajectory agrees with the frozen
expectation (`check_match`). Because low-texture/slow-cruise clips read as
"unmeasurable"/"ambiguous" to the probe even when stopped, the ID instrument
adjudicates those candidates (lowest tail-flow first). Two lessons from the run:
the ID runner caches predictions by clip rel-path, so per-pass caches are
mandatory (`COSMOS3_ID_WORK_DIR`; a shared cache silently re-scored pass-1
poses); and generation is stochastic enough that the same feasible prompt yields
a near-static clip on one seed and a textbook stop on the next — the gate, not
the prompt alone, is what delivers fidelity.

Outcome: 134 clips generated; **32/36 targets repaired** (28 in pass 1, 4 in
pass 2). Unresolved after 8 seeds: neg_4_v08 (ID 34 mph on a blurred highway
clip), pos_9_v15 (final 2.0 mph, on the threshold), pos_4_v12 / pos_5_v12
(maintain class; the generator brakes for objects in the lane regardless).
Their originals stay in place and remain excluded by the admission filters.

### 13.4 Installed and published

32 mp4s + v1 trajectories (5 Hz + 10 Hz) replaced in `data/datasets/generated_vids`
(originals under `data/datasets/_superseded/`) and pushed to
`ASASLab/av_semantic_anomalies@main` (96 files, one commit); raw poses appended
to `outputs/id_raw.jsonl`; flow/fidelity files refreshed.

- **Generation fidelity (120 sample): PROMPT↔VIDEO 71.7% → 98.0%**; VIDEO↔ID 98.0%;
  regeneration list 15 → 1.
- **Agreement subset: 72 → 95 admitted** (54 anomaly / 41 normal);
  `video_contradicts_prompt` exclusions 36 → 2; remaining exclusions are
  human-rejected (50) and ID disagreements (21); 147 still pending the full ID
  pass (next open task). The 72-clip list is archived as
  `logs/vlm_agreement_subset_admitted_v1_72.txt`; `vlm_agreement_subset_admitted.txt`
  now holds 95 and the 720p/early trees were rebuilt for it. Every result in
  Parts 6-12 was measured on the 72 list.
- Caveat: the HF dataset now mixes v1-style trajectories (these 32 clips) with
  the published v0 files elsewhere; the full-dataset ID pass will harmonise it.

## Part 14 — Full fixed-ID pass: every clip has a v1 trajectory; subset 72 → 199

The deferred coverage pass (`spec/run_id_full_remote.sh`, `id_publish.py`; one
H200 session ≈ 35 min ≈ $2.5). The v1 pipeline was unchanged (Part 2/5: 10 fps
resample, true time base, padding trim; the 21 long 8 s clips at 7.5 fps so the
61-frame action chunk spans the whole clip). It ran only on the 177 clips that
lacked a record; the 138 existing records (120 sample + 18 regenerated) were
kept verbatim so every earlier number stays reproducible. `outputs/id_raw.jsonl`
now holds all 315.

### 14.1 Agreement subset on the whole dataset

| | before | after |
|---|---|---|
| admitted | 95 (54 anomaly / 41 normal) | **199 (79 / 120)** |
| pending fixed-ID | 147 | **0** |
| excluded | 73 | 116 (ID disagrees 64, human-rejected 50, video contradicts prompt 2) |
| scenarios covered | 12 | **15** |

Majority baseline on the 199-clip subset is now *normal*-majority (0.603), the
opposite polarity of the 72-clip subset (0.611 anomaly) — verdict arms tuned on
the old subset's bias must be re-measured, not extrapolated. Lists:
`logs/vlm_agreement_subset_admitted.txt` (199), `_v1_72.txt` archived; 720p and
early trees rebuilt for the 199.

### 14.2 What the 64 ID disagreements are

Two families, both generation-side, neither ID-side: (a) stop-class clips whose
ID final speed sits at 2-7 mph — the vehicle brakes hard but the clip ends
before a full stop (the same infeasible-timing defect the regeneration repaired
for its 36 targets, now visible in the remaining scenarios, e.g. neg_0); and
(b) maintain-class clips that decelerate to ~0.5× their initial speed
(neg_prompt_8 "continues at speed" variants decelerate in every case) — the flow
probe passes them because they are still moving, so only the ID catches them.
These are the natural targets for a second regeneration sweep (`regen_fix.py
targets` extended with an ID-disagreement criterion); the machinery exists.

### 14.3 Published

All 315 clips' v1 trajectories replaced the v0 files on
`ASASLab/av_semantic_anomalies@main` in one commit (`<stem>.txt` 5 Hz +
native-rate sibling; the 21 long clips publish `_7.5fps.txt` and their stale
`_10fps.txt` was removed); v0 archived under
`data/datasets/_superseded/v0_trajectories/`. The release is now uniformly v1.

## Part 15 — Regeneration sweep 2 (ID-disagreement targets): 36/64 reclaimed

Same machinery as Part 13, keyed on the agreement builder's `id_disagrees`
exclusions (`regen_fix.py --tag s2 targets --id-disagree`): 64 targets — 27
stop-class (brake but end at 2-7 mph → feasible-timing rewrite), 34
maintain-class (decelerate → no-braking reinforcement), 3 accelerate-class
(start-from-stop that never gets going → pull-away reinforcement). Two passes,
8 seeds max; one H200 session ≈ 2.2 h ≈ $9.

| class | targets | reclaimed | note |
|---|---|---|---|
| stop | 27 | **24** | the timing rewrite works almost everywhere |
| maintain | 34 | 11 | the generator's prior is to slow near a hazard; wording only partly overrides it (rejects still decelerate to 0.26-0.54×) |
| accelerate | 3 | 1 | |
| **total** | **64** | **36** | 28 originals kept, still excluded |

Installed and pushed (36 mp4 + v1 trajectories, 108 files) to the HF dataset;
flow/fidelity/raw refreshed. 120-sample fidelity: VIDEO↔ID 100%, PROMPT↔VIDEO
98.1%.

**Agreement subset: 199 → 235 admitted (110 anomaly / 125 normal)**, 0
pending, 80 excluded (28 ID disagrees — mostly the maintain-class residual — 50
human-rejected, 2 video contradicts). 15 scenarios. Trees rebuilt for the 235.
The maintain-class residual is the remaining generation limit: the model brakes
for lane-adjacent hazards regardless of prompt text; fixing it would need
scene-side changes (hazard placement) rather than motion wording — out of scope
for a prompt-timing repair, noted for the dataset paper.

## Part 16 — Champion re-measured on the 235-clip subset: holds, with a smaller margin

The Part-12 declaration was made on the 72-clip anomaly-majority subset; after
Parts 13-15 the admitted set is 235 clips (110 anomaly / 125 normal, majority
0.532 normal, 15 scenarios). Same configuration, same session-paired protocol
(`qlab_r5`, seed 1234, 720p↑ @ 8 fps, trees rebuilt for the 235).

| arm | acc | 95% CI | balacc | rec/spec | McNemar vs P0 |
|---|---|---|---|---|---|
| **L2, think@16k (champion)** | **0.745** | [0.685, 0.796] | **0.732** | 0.54 / 0.93 | **+29 (p=0.012)**, breadth 8/15 |
| P0, think@16k (anchor) | 0.621 | [0.558, 0.681] | 0.641 | 0.95 / 0.34 | — |
| L2, direct | 0.621 | | 0.604 | 0.33 / 0.88 | +14 (p=0.22) |
| P0, direct | 0.562 | | 0.574 | 0.76 / 0.38 | — |

The champion **still clears the pre-registered bar** (acc > 0.736, balacc >
0.70) on the near-balanced set, now with a significant paired margin over its
anchor (+29 clips, p=0.012) and the same signature — near-perfect specificity
(0.93), recall the constraint (0.54). The absolute numbers are lower than on the
72 (0.806-0.889 / 0.84-0.91): part of that is the honest-set correction
(the 72 was anomaly-majority and the guard prompt's strength is specificity),
part is that the new clips include scenarios (neg_0, pos_2, pos_6, neg_9 …)
the lab never saw during design. P0's own number also drops (0.694-0.708 → 0.621),
so the structure of the result is unchanged: the guard line buys ~+0.09-0.12
balanced accuracy over the Cosmos-tuned wording wherever it is measured.

Single-seed so far; the 72-clip declaration had a seed-4321 reproduction. A
reproduction on the 235 (~$4) is the remaining formality before quoting these
as the paper's headline numbers. Session cost ≈ $6 (interrupted once by credit
exhaustion at 226/235 clips; resumed from the synced records).

## Part 17 — H-lab: the two-stage monitor beats the champion once the comparator reads English

Prompt lab for the family-H expectation-vs-action monitor on Qwen3.8-27B think@16k
(both stages), balanced 80-clip subset from the 235 (40/40, scenario-stratified,
`logs/hlab_subset_80.txt`), champion L2 (think@16k, full clip) re-run in-session
as the paired anchor. Registry `h_variants.py`; driver `spec/run_hlab_round.sh`;
diagnostics `hlab_report.py` (twin divergence = anchoring, conditional accuracy).
Four sessions ≈ $26.

### 17.1 Round 1 (T−2.5 control + ladder): the comparator was the loss

| arm | acc | vs L2 (60/80) | note |
|---|---|---|---|
| M0 verbatim H3 texts @ T−2.5 | 0.613 | −11 | stage-1 lenient 79%, but verdict only 70% given a correct expectation |
| M1 explicit comparison rule | 0.675 | −6 | rule helps (+5) |
| **M2 rule + narrative rendering** | **0.838** | **+7** | **verdict 63/63 = 100% given a correct expectation** |
| M3 rule + velocity-only | 0.662 | −7 | channel count irrelevant; numeric reading is the problem |
| M4 guard+feature at stage 1 | 0.775 | +2 | best stage 1 (64/80 lenient) |
| M5 guard re-check at stage 2 | 0.762 | +1 | rescues 67% of stage-1-wrong clips |
| M6 / M7 windows 1.5 s / 1.0 s | 0.600 / 0.588 | −12 / −13 | shorter windows don't help; twin divergence rises at 1.0 s (model hedges "slow") |

Two facts decide the lab: (a) with the trajectory rendered as the mechanical
English narrative (`action_narrative`, no model, no judgement) the comparator is
*perfect* when the expectation is right — every remaining miss is a stage-1
miss; (b) stage 1 is ~63/80 lenient and is anchored on ego motion at every
window ≥ 1 s (twin divergence 0.14–0.18; the regenerated stops begin at 0.6–0.8 s).

### 17.2 Rounds 2–4: compose, reproduce, tie-break

| arm | seed | acc / balacc | vs in-session L2 | McNemar |
|---|---|---|---|---|
| **M8** = M4 stage 1 × narrative comparator | 1234 | **0.850 / 0.850** | 57 → 68 (+11) | p = 0.061 |
| M9 = M8 + stage-2 guard re-check | 1234 | 0.838 / 0.838 | +10 | p = 0.087 |
| M10 = M0 stage 1 × narrative × re-check | 1234 | 0.838 / 0.838 | +10 | p = 0.076 |
| **M8** (reproduction) | 4321 | **0.850 / 0.850** | 56 → 68 (+12) | **p = 0.023** |
| M11 = M8 + majority-of-3 stage 1 | 4321 | 0.825 | +10 | p = 0.076 — stage-1 errors are systematic, not sampling noise |
| **M8** (tie-breaker) | 999 | 0.800 / 0.800 | 57 → 64 (+7) | p = 0.248 |
| **M8 pooled, 3 seeds (n=240 paired)** | — | **0.833 vs 0.708** | **+30 (55 gained / 25 lost)** | **p = 0.001** |

### 17.3 Reading and declaration

M8 beats the champion on every seed (+7 … +12), with balanced accuracy 0.80–0.85
vs 0.70–0.71 (recall 0.82 vs 0.53 at similar specificity) and zero truncations or
Unknowns; the pooled paired test is decisive (p = 0.001). On the strict per-seed
reading of the pre-registered rule it is 1 of 3 seeds at p < 0.05 (the screen
missed at p = 0.061, the designated reproduction at seed 4321 passed, the
tie-breaker missed) — the per-seed test is underpowered at n = 80 (needs ~+9 on
few discordants). **Declared — on the pooled three-seed evidence, with that
per-seed caveat stated**: the H-family champion is **M8: Qwen3.8 think@16k,
stage 1 = expected action + the real feature requiring it + the depiction guard
(T−2.5 window), stage 2 = narrative-rendered trajectory + explicit comparison
rule**, 0.833 pooled vs 0.708 for the single-call L2 champion on the same clips.
It is also the first configuration in the program whose recall (0.82) and
specificity (0.85–0.88) are balanced.

Remaining ceiling: stage 1 (≈63/80 lenient), systematically anchored on ego
motion at any window that shows the braking; self-consistency does not help.
Levers left: a first-frame (0.3 s) stage 1 for stop-type scenes, or SFT on
stage-1 labels (Part 8.3). The narrative comparator makes the M8 pipeline
100% faithful to whatever stage 1 says, so stage-1 gains transfer one-to-one.

### 17.4 M8 on the full 235-clip subset: the headline numbers

Same configuration as declared (Qwen3.8 think@16k on both stages, T−2.5 stage-1
window, narrative comparator), seed 1234, run on all 235 admitted clips
(110 anomaly / 125 normal) with the L2 champion re-run in-session as the paired
anchor (`logs/hlab_r5t_{M8,L2}`; the earlier L2-on-235 run from Part 16 is kept
alongside as `hlab_r5t_L2q` for a second pairing). Report
`logs/prompt_lab_hlab_r5t.md`, diagnostics `logs/hlab_diag_hlab_r5t.md`.

| arm | acc | 95% CI | balacc | recall / spec | vs L2 (in-session) | vs L2q (Part 16) |
|---|---|---|---|---|---|---|
| **M8** | **0.830** (195/235) | [0.777, 0.872] | **0.826** | 0.77 / 0.88 | **+27 net (48/21), p = 0.002** | +20 net (35/15), p = 0.024 |
| L2 in-session | 0.715 (168/235) | [0.654, 0.769] | 0.701 | 0.49 / 0.91 | — | |
| L2q (Part 16 run) | 0.745 (175/235) | [0.685, 0.796] | 0.732 | 0.54 / 0.93 | +7, n.s. | — |

Zero truncations and Unknowns for M8; stage 1 strict 128/235, lenient 184/235
(78%, the same rate as on the 80); the comparator is again 100% faithful
(184/184 correct given a lenient-correct expectation; 11/51 when stage 1 is
wrong). The two L2 sessions differ by 7 clips on the same seed — the
run-to-run band at t = 1.0 — so the paired in-session comparison is the number
to quote; both pairings clear p < 0.05.

Where the gain sits (M8 − L2, per scenario): the unnecessary-stop family is
almost solved — neg_0 18/18 (+8), neg_3 15/15 (+7), neg_4 17/17 (+6), **neg_5
16/16 (+14)** — which was exactly the recall mass the single-call champion
lacked. The costs are the **missed-reaction anomalies** (neg_9 3/18, −8;
neg_8 0/7, −2: stage 1 answers continue/slow because the real hazard is not
recognised from the early window, so "continued" matches) and the **real-stop
normals** pos_8 / pos_9 / pos_11 (−3 / −2 / −3: stage 1 says *slow* where
*stop* is expected, and slow-vs-stop is a mismatch under the rule). The
continue-normals are unchanged (pos_0/4/6 at 17/18/18). So M8 and L2 have
complementary failure modes on the honest set, and every residual M8 error is
a stage-1 error — consistent with 17.3's reading that stage 1 is the ceiling.

**Headline for the paper (235-clip, near-balanced subset): two-stage monitor
M8 = 0.830 acc / 0.826 balacc (recall 0.77, specificity 0.88) vs the
single-call champion L2 = 0.715–0.745 / 0.70–0.73, +20 to +27 paired clips,
p ≤ 0.024 on either pairing.** Single seed on the 235; a seed-4321
reproduction (~$5) is the remaining formality before quoting it as final.

### 17.5 Longer stage-1 windows on M8's 40 failures (T−1.5 / T−1.0)

Round 6 (`logs/hlab_r6t_*`, seed 1234, instance re-provisioned): the 40 clips M8
got wrong on the 235 (`logs/hlab_m8fail_40.txt`), run with M8 unchanged except the
stage-1 window — T−2.5 again (same-window re-run = sampling-noise control), T−1.5
(3.6 s windows) and T−1.0 (4.1 s). All 5-s clips; 0 truncations / Unknowns.

| arm | stage-1 window | stage-1 correct | verdicts recovered / 40 |
|---|---|---|---|
| M8 (control re-run) | T−2.5 (2.6 s) | 2 | **3** — the chance-flip floor; the failures are systematic |
| M8w15 | T−1.5 (3.6 s) | 11 | **12** |
| M8w10 | T−1.0 (4.1 s) | 12 | **14** |

Recovered by both longer windows 8, by either 18. By mechanism (ctrl / T−1.5 / T−1.0):
pos_8 under-commitment **0 / 4 / 4** (all four: the child steps off inside the longer
window → "stop"); mural blindness neg_9 1 / 3 / 5 and pos_9 1 / 3 / 2 (stochastic —
different clips flip at each window; the wall is read as a wall only sometimes);
neg_8 window blindness 0 / 0 / **1** (the step-off is still mostly after T−1.0, and the
one recovery says "stop" at 4.1 s — the rest remain "slow"); neg_2 1 / 1 / 2 (noise);
pos_11 renderer artifact 0 / 1 / 0 (unchanged by design — stage 1 still says "wait").

Reading: a longer window recovers the **under-committed hazard** cases fully (pos_8:
the model needs to see the child move before it says "stop") but is only a partial,
noisy lever on the mural family, and leaves neg_8 (the label event is at ~3–4.5 s)
and the renderer artifact untouched. It also cannot be adopted blindly — a longer
window re-exposes the anchoring risk on the unnecessary-stop scenarios that M8 now
solves (at T−1.0 the braking is complete and visible). The proper test is M8w10 on
the full 235 with a paired anchor (~$5); expected net: +14 recoveries here against an
unknown number of new losses on neg_0/2/4/5.

## Part 18 — Family N: supervised fine-tuning of M8's stage 1 (leave-scene-out)

Goal (pre-registered): fine-tune the stage-1 expectation of the declared M8 monitor
and beat zero-shot M8 on the same clips — CV-concatenated predictions vs an
in-session zero-shot anchor on the 235, McNemar p<0.05 AND higher balanced accuracy,
reproduced with a second training seed. Comparator (stage 2) unchanged.

### 18.1 Pipeline

- **Context**: the annotated decision-time tree (`generated_vids_720p_early_gt`: one
  2.5 s rolling window per clip ending at the annotated decision time, T−2.5 where
  unannotated; 7 neg_8 clips annotated 2.5–4.0 s; the 18 long neg_0 clips at
  [T−5, T−2.5]). Prompt = the served stage-1 request byte-for-byte (system "You are a
  helpful assistant." + `M4_STAGE1`, sha `96da9513…`); video tokens verified equal to
  serving (8,849 for the probe clip, ms-swift encoding vs vLLM `prompt_tokens`, 0.0 %
  delta; text format asserted).
- **Targets**: self-distilled rationale + final word (`sft_rationalize.py`): the base
  model answers the stage-1 question with the GT action given as a calibration hint,
  thinking on, content kept; accepted only if the final word equals GT, no hint
  echo, no outcome/ego-motion narration (Wait excepted), 12–120 words. All 235 were
  accepted at tier 1 (231 on the first sample; 47–108 words, median 71); no
  fallbacks. Spot-checked: each scenario's defining feature is named
  (`logs/sft/rationales_review.md`).
- **Training**: ms-swift 4.5.2 LoRA (r 16 / α 32, all-linear on the LLM, ViT+aligner
  frozen), non-thinking targets (empty `<think>` prefix, loss-masked), lr 1e-4,
  2 epochs, grad-accum 8, bf16, grad checkpointing, 5.0 s/sample on one H200,
  ~31 min per fold (≈ 46–50 optimizer steps); merged with `swift export` and served
  by the same vLLM command; stage 1 evaluated greedy with thinking off
  (`expect_sft`), stage 2 unchanged (think@16k). Leave-scene-group-out, 5 folds
  (scene pairs co-located): f1 = mural pair + pos_6, f2 = bags pair + neg_3,
  f3 = billboard pair + pos_11, f4 = balloons pair, f5 = shirt pair + child pair.
  Full provenance: `logs/sft/{folds,manifest}.json`, `logs/sft_r1_f*/fold_meta.json`,
  `logs/sft/env_pins.txt`, `spec/run_sft_cv.sh`.

### 18.2 Result (seed 1): FAIL

| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient | stage-1 answers |
|---|---|---|---|---|---|---|
| SFT stage 1 in M8 (CV-concatenated) | **0.736** (173/235) | [0.676, 0.788] | 0.731 | 0.65 / 0.81 | 130 / 151 | continue 156, slow 17, stop 39, wait 23 |
| zero-shot M8gt anchor (in-session) | **0.821** (193/235) | [0.767, 0.865] | 0.818 | 0.76 / 0.87 | 127 / 181 | continue 106, slow 71, stop 37, wait 21 |

Paired McNemar: +7 gained / −27 lost (net −20), **p = 0.0008** — the wrong direction.
Per fold (SFT / anchor): f1 0.39 / 0.57, f2 0.79 / 0.98, f3 0.88 / 0.90, f4 **1.00 / 0.97**,
f5 0.70 / 0.74. Zero truncations/Unknowns; the SFT stage 1 answers in 65 words
(vs 145) and 15 s/clip (vs 47 s) — format and speed are exactly as intended.

### 18.3 Reading: the model learned *rules* that do not transfer to an unseen scene

The fine-tune does what the targets say — it stops hedging (slow 71 → 17) and
commits — and on a held-out scene that commitment lands on the wrong side wherever
the scene's own concept was absent from training:
- **mural pair (f1)**: 30/31 "continue" — the sibling depiction scenes in train
  (billboard, shirt) teach "a painted image commands nothing → Continue", which
  the fold model applies to a painted *wall* (pos_9 7 → 0, neg_9 3 → 1);
- **bags (f2)**: "stop" 9/16 — soft debris read as an obstacle (neg_5 15 → 7);
- **pos_11 (f3)**: "wait" 14/14 — learned from neg_3's red light in train (stop≡wait
  saved 8 of them, the rule's wait-vs-stop edge cost 2);
- the only clean transfer is **balloons (f4)**, whose sibling concept (bags) is in
  train: 35/35.
Losses by stage-1 transition: slow → stop 13, stop → continue 9, stop → slow 2.
So with 15 scenes, leave-scene-out SFT measures concept transfer between scene
families, and there is essentially none to transfer — the data contain one
instance of each concept. This is the outcome the plan flagged as the main risk,
not a pipeline defect (parity, format, loss curves, gates all clean). Consequence
for the paper: zero-shot M8 remains the best deployable configuration; SFT on this
dataset cannot be claimed to generalise to unseen scenes. The second training seed
is moot for a FAIL and was not run.

### 18.4 Within-scenario split (learnability diagnostic): the concepts are learnable

Same pipeline, same rationales and the same seed-1 anchor, but the 5 folds are a
per-scenario round-robin (every scene appears in training; clips of the held-out
fold are unseen variants of seen scenes) — `logs/sft_within/`, `logs/sft_w1_f*`.

| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient |
|---|---|---|---|---|---|
| SFT stage 1 in M8, within-scenario CV | **0.936** (220/235) | [0.897, 0.961] | **0.936** | 0.93 / 0.94 | 206 / 222 |
| zero-shot M8gt anchor | 0.821 (193/235) | [0.767, 0.865] | 0.818 | 0.76 / 0.87 | 127 / 181 |

Paired McNemar +32 / −5 (net +27), p < 10⁻⁴; zero truncations/Unknowns; per fold
0.94 / 0.89 / 0.98 / 0.98 / 0.90 vs anchor 0.77–0.86. The gains are exactly the
zero-shot failure buckets: mural neg_9 **3 → 18/18** and pos_9 7 → 11/13 (the model
now says "stop" for the painted wall), child pos_8 14 → 19/19 (commits to stop),
neg_8 1 → 4/7 (the annotated windows now pay off once the concept is learned; the
other 3 still answer continue/slow), neg_2 stage-1 lenient 7 → 17 (verdict unchanged
at 16/19). Residual 15 errors: pos_11 5 (the near-zero-speed renderer artifact,
not SFT-addressable), neg_8 3, neg_2 3, and singles.

Reading, with 18.2: the stage-1 concepts this dataset needs ("a painted wall is a
wall", "commit to stop for a child at the curb") are **learnable from a few clips
per scene** (+11.5 points, balanced 0.94) but **do not transfer to an unseen scene**
(−8.5 points under leave-scene-out). 18.4 is therefore a learnability ceiling and a
within-distribution result, not a generalisation claim; it says the lever is real
and that the missing ingredient is scene diversity per concept (more scenes, not
more variants), which is a dataset-design item. Headline claims for the paper stay
with zero-shot M8 (0.830 / 0.821) unless the evaluation is explicitly
within-distribution. Second training seed not run (credit); adapters for both
campaigns are kept locally under `tmp/sft/`.
