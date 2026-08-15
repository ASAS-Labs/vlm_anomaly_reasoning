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
