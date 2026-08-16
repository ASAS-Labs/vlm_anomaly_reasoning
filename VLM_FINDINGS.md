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

