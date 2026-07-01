---
name: scenery-variations
description: Generate scenery/environment variations of a folder of upsampled Cosmos3 video-gen JSON prompts — varying scene, weather, visibility, lighting, time of day, city type, landscape, season, and scene-object appearance — while preserving each prompt's core scenario/anomaly and the required Cosmos3 JSON schema. Use when asked to create N variations of a folder of prompt_<index>.json files into a different output folder.
argument-hint: <input_folder_of_prompt_json> <output_folder> [num_variations=20]
---

# Scenery variations

Generate up to 20 **scenery variations** of every `prompt_<index>.json` in an input folder and write them to a separate output folder. Each variation re-skins the environment (scene, weather, visibility, lighting, time of day, city type, landscape, season, road surface, scene-object appearance) while keeping the **core scenario/anomaly intact** and the JSON valid against the Cosmos3 schema.

You (Claude) author the variations directly by transforming the JSON fields in-context. No upsampler API call is needed — these are scenery re-skins of already-upsampled prompts, and direct authoring is what lets the core scenario survive exactly.

## Inputs

Parse from `$ARGUMENTS`:
- `INPUT` = `$1` — folder containing `prompt_<index>.json` files (strip any trailing slash).
- `OUTPUT` = `$2` — destination folder for the variations (strip any trailing slash). Create it if missing. Quote it if it contains spaces or `[` `]`.
- `N` = `$3` — number of variations per base prompt. **Default 20. Cap at 20.** If `> 20`, clamp to 20 and tell the user.

If `INPUT` or `OUTPUT` is missing, ask the user before proceeding.

## The schema (must hold for every output file)

Each output is one JSON object with these top-level keys (mirror of `packages/cosmos-framework/.../inference/structured_caption.py` `StructuredCaption`). Match the base file's keys and types exactly — don't add or drop keys:

`subjects` (list of subject objects), `background_setting` (str), `lighting` (`conditions`/`direction`/`shadows`/`illumination_effect`), `aesthetics` (`composition`/`color_scheme`/`mood_atmosphere`/`patterns`), `cinematography` (`camera_motion`/`framing`/`camera_angle`/`depth_of_field`/`focus`/`lens_focal_length`), `style_medium` (str), `artistic_style` (str), `context` (str), `actions` (list of `time`/`description`), `text_and_signage_elements` (list), `segments` (list of `segment_index`/`time_range`/`description`/`key_changes`/`camera`), `transitions` (list), `temporal_caption` (str), `audio_description` (str), `resolution` (`H`/`W`), `aspect_ratio` (str), `duration` (str), `fps` (int).

Each subject object keeps all its keys: `description`, `appearance_details`, `relationship`, `location`, `relative_size`, `orientation`, `pose`, `action`, `state_changes`, `clothing`, `expression`, `gender`, `age`, `skin_tone_and_texture`, `facial_features`, `number_of_subjects`, `number_of_arms`, `number_of_legs`. Leave empty-string/zero fields as they are unless the variation genuinely changes them.

## What is INVARIANT (never change across variations)

Before writing any variation, read the base prompt and name its **core scenario** — the event the video exists to show (for this dataset: the AV semantic anomaly or the correct/normal behavior, plus the subject(s) that drive it and how the ego vehicle responds). The core is the dataset label; a variation that alters it is a bug.

Hold these fixed in every variation:
- The **scenario / anomaly / normalcy** and its causal logic (e.g. "balloons block the lane and the car stops short of them", "stop sign printed on an ad is correctly ignored").
- The **primary subject(s)' identity, count, behavior, and role** (`number_of_subjects`, the driving `action`/`state_changes`, `relationship`). You may restyle a subject's *surface appearance* only when the variation axis explicitly calls for it (see below) and it doesn't change what the subject *is* or *does*.
- The **ego-vehicle response** and the **action/segment/temporal timeline** structure (same number of segments, same beat-by-beat events, same `duration`/`fps`/`resolution`/`aspect_ratio`).
- `text_and_signage_elements` content that is part of the anomaly (e.g. the sign wording that defines the scenario) — restyle its surface only if the axis calls for it, never its meaning.

## What VARIES (the scenery axes)

Re-skin the environment. Draw each variation from a deliberate combination across these orthogonal axes so the set is diverse, not random near-duplicates:

- **Scene / setting type** — dense downtown, suburban arterial, residential street, commercial strip, industrial zone, highway/expressway, tunnel/underpass, bridge, rural two-lane, mountain road, coastal road, desert highway, parking lot, construction zone, tree-lined boulevard.
- **City type / region cues** — North American grid, European old-town, dense Asian megacity, Middle-Eastern, Scandinavian, Latin American — reflected in building style, signage style (without changing anomaly text meaning), street furniture.
- **Landscape / terrain** — flat, rolling hills, mountainous, coastal, forested, open plain, snowfields.
- **Time of day** — dawn, golden-hour morning, bright midday, overcast noon, late-afternoon, dusk/blue hour, night, pre-dawn dark.
- **Weather** — clear, partly cloudy, overcast, light rain, heavy rain (wet reflective road), drizzle, fog/mist, snow/snow-covered road, after-rain wet, light haze, gusty wind, sleet.
- **Visibility** — crisp clear, hazy, foggy/low-visibility, glare-limited, rain-blurred, dim/low-light.
- **Lighting** — must be made physically consistent with the chosen time/weather: sun direction & shadow length/direction, overcast shadowless, headlight/streetlight/neon at night, wet-road specular highlights, fog-diffused glow, golden warm vs blue cool color temperature.
- **Scene-object appearance / type** — surrounding (non-anomaly) elements: vehicle types & colors parked/passing, building materials & colors, foliage species/season, street furniture, road surface (fresh asphalt, worn, cobblestone, concrete, wet, snow-dusted), lane-marking condition, roadside vegetation.
- **Season** — spring bloom, lush summer, autumn foliage, bare winter/snow — kept consistent with weather & foliage.

### Consistency rule (critical)
When you set an axis, propagate it through **every** dependent field so the JSON has no internal contradiction:
`background_setting` ↔ `lighting` (conditions/direction/shadows/illumination_effect) ↔ `aesthetics` (color_scheme/mood_atmosphere/composition) ↔ `cinematography` (focus/depth_of_field at night or fog) ↔ each subject's `appearance_details`/`relative_size`/visibility ↔ `actions` & `segments` descriptions ↔ `temporal_caption` ↔ `audio_description` (rain hiss, wind, wet tyre noise, snow muffling, night quiet) ↔ `context`.

Also keep it **physically plausible** (the same standards the `fix-prompt-realism` skill enforces): shadows match sun position, night needs a light source, wet roads reflect, fog reduces contrast and shortens visible range, snow mutes audio, etc. A variation must be a real-world-plausible scene, not just a keyword swap.

## Procedure

### Phase 0 — Setup & plan
1. Resolve `INPUT`, `OUTPUT`, `N` (default 20, clamp to 20).
2. List `INPUT/prompt_*.json`, extract integer indices, **sort numerically ascending** (`prompt_2` before `prompt_10`). Skip obvious non-prompt files (e.g. `* backup.json`) unless the user says otherwise; mention any you skip.
3. `mkdir -p` the `OUTPUT` folder.
4. **Build a variation matrix once** and reuse its row meanings across all base prompts: design `N` distinct scenery specs, each a labeled combination of axes (e.g. `v01 = night + light rain + wet downtown asphalt + neon`, `v02 = bright midday clear + suburban arterial + summer foliage`, …). Spread the specs to cover the axis ranges (don't cluster all on weather; rotate time-of-day, scene type, region, season too). Keep the spec list short and human-readable.
5. Write `OUTPUT/variation_plan.md`: the resolved inputs, the invariant-core note, and the `N`-row matrix with each row's axis combination. This is the systematic plan the user can audit before/after generation.

### Phase 1 — Generate
Process base indices in ascending order. For each base `prompt_i.json`:
1. Read it. State its invariant core in one line (in the plan file or your running notes).
2. For each variation `k` in `1..N`, author a complete JSON by applying matrix row `k` to the base:
   - Keep all invariant fields/content (Phase: "What is INVARIANT").
   - Rewrite the scenery fields per the row, propagating through every dependent field (consistency rule).
   - Keep `duration`/`fps`/`resolution`/`aspect_ratio`/segment count identical to the base.
   - Write to `OUTPUT/prompt_<i>_v<NN>.json` (zero-pad `NN` to 2 digits: `v01`..`v20`). Mirror any subfolder layout from `INPUT` if the input has nested scenario folders.
3. After writing each file, validate it parses and conforms loosely to the schema:
   ```
   python3 -c "import json,sys; d=json.load(open(sys.argv[1])); req={'subjects','background_setting','lighting','aesthetics','cinematography','segments','temporal_caption','audio_description','resolution','duration','fps'}; miss=req-set(d); print('valid' if not miss else 'MISSING:'+','.join(miss))" "OUTPUT/prompt_<i>_v<NN>.json"
   ```
   Fix any file that reports `MISSING` before moving on.

Generating `N` full files per prompt is substantial. Work prompt-by-prompt and keep each file self-consistent rather than rushing — correctness and diversity over speed. For large jobs (`many prompts × N`), you may dispatch per-base-prompt generation to parallel sub-agents **only if the user asks**; otherwise do it inline.

### Phase 2 — Finalize
1. Confirm counts: `find "OUTPUT" -name 'prompt_*_v*.json' | wc -l` should equal `(#base prompts) × N` (minus any skipped base files). Report the number.
2. Append a short summary to `variation_plan.md`: base prompts processed, variations each, total files, any skips or clamping.
3. Report to the user: the `OUTPUT` path, the `variation_plan.md` path, total files written, and a one-line reminder that `generate_videos_vllm.py` will render one MP4 per JSON by relative path (so each variation becomes its own video).

## Guardrails
- **Preserve the core scenario/anomaly in every variation** — only scenery changes. This is the whole point of the dataset.
- Never introduce internal contradictions; propagate every axis change through all dependent fields, and keep each scene physically plausible.
- Keep the exact schema keys/types of the base file — don't add, drop, or rename keys; keep `duration`/`fps`/`resolution`/`aspect_ratio`/segment count fixed.
- Make the `N` variations genuinely diverse across axes, not weather-only reskins or near-duplicates.
- Quote any path containing spaces, `[`, or `]`.
- Do not modify the `INPUT` files. Do not commit or push unless the user asks.
