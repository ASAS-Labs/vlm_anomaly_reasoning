---
name: fix-prompt-realism
description: Review upsampled Cosmos3 video-gen JSON prompts for real-world implausibilities (aside from the intended anomaly/normalcy), fix the source human prompts, re-upsample into a "[claude_authored]" folder, then review and fix the regenerated JSON in-place — logging every change to a report. Use when asked to improve the realism/plausibility of a folder of upsampled prompt_<index>.json files against their source human prompt text file.
argument-hint: <source_folder_of_prompt_json> <original_human_prompt.txt>
---

# Fix prompt realism

Two-round realism pass over a folder of upsampled Cosmos3 prompts. Round 1 fixes the **source human prompts** (so the next upsample is better) and regenerates the JSON; Round 2 fixes any **remaining** implausibilities directly in the regenerated JSON. Every change is logged to a report.

## Inputs

Parse from `$ARGUMENTS`:
- `SOURCE` = `$1` — folder containing `prompt_<index>.json` files (strip any trailing slash).
- `HUMAN` = `$2` — original human prompt text file. **Line `<index>` (0-based) produced `prompt_<index>.json`.**

If either argument is missing, ask the user for it before proceeding.

## Derived paths

- `UPDATED` = `<dir of HUMAN>/updated_human_prompt.txt` — the fixed human prompts (one per line, index-aligned).
- `OUTDIR` = `<SOURCE>_[claude_authored]` — re-upsample output folder. Always quote this path (it contains brackets).
- `REPORT` = `<dir of HUMAN>/realism_review_report.md` — running change log.
- Upsampler: `data/cosmos3/upsample_prompts.sh` (relative to repo root). It reads the WHOLE input txt and writes `prompt_<line>.json` per line.

## Core review rubric (used in both rounds)

For each prompt, first identify the **anomaly/normalcy** — the scenario's intended behavior, stated in the source human prompt line (e.g. "stop sign is on an advertisement, car correctly ignores it"; "car stops for a man whose shirt shows a stop sign"; "car runs a red cued by a green balloon"). **Never flag the intended anomaly/normalcy as an error — it must survive every edit.**

Then **flag every implausibility** — anything that would not happen, exist, look, sound, or behave that way in the real world, *aside* from the anomaly. **This is exhaustive, not a triage:** report each issue you find regardless of how minor, not just the most prominent one. Read every field (`subjects`, `background_setting`, `lighting`, `aesthetics`, `cinematography`, `style_medium`, `artistic_style`, `context`, `actions`, `text_and_signage_elements`, `segments`, `transitions`, `temporal_caption`, `audio_description`, `resolution`/`aspect_ratio`/`duration`/`fps`) and check it against physical reality, traffic/engineering norms, optics, acoustics, biology, and against every other field for internal contradictions (timing, position, count, state, color, size, direction).

The categories below are a **non-exhaustive memory aid to prime your search — not a closed checklist and not a limit.** Do not stop at them; if something is off in a way no category names, flag it anyway.
- **Lighting / shadow / optics** — e.g. sun placed "ahead" of the car while the ego/object shadow is cast "ahead" on the road; a camera-facing surface described as front-lit while the sun is behind it; shadow length/direction inconsistent with the stated sun angle; reflections, glare, color temperature, or night/day illumination that don't match the light sources.
- **Motion physics** — full stop reached in ~1s from cruising speed described as "smooth/gentle"; deceleration window inconsistent with the "smooth/gradual" language (smooth city/highway stops need ~2.5–4s); speeds, accelerations, following distances, or curve-taking that violate plausibility.
- **Geometry / placement / perspective** — a pedestrian on the curb/sidewalk but simultaneously centered in the lane / stopped in front of head-on; vehicle stopping for someone not in its path; object positions, sizes, or framing that contradict the camera viewpoint or each other.
- **Infrastructure / traffic norms** — redundant or contradictory control devices (a STOP sign and a red traffic signal governing the same approach); official-only structures repurposed (commercial ad on a bare overhead sign gantry — real gantries carry official signage only; put ads on overpass/footbridge faces or roadside billboards instead); sign shapes/colors/wording that don't match real standards; lane/road configurations that don't exist.
- **Audio** — sounds that can't occur or don't match the visuals (e.g. aerodynamic "whoosh" from a small roadside object several meters off the lane; engine/brake/tire/Doppler cues inconsistent with the depicted motion).
- **Counts / legibility / scale** — object counts that contradict the narrative or the per-subject `number_of_*` fields; small text/graphics described as legible while still far in the distance; object dimensions that are wrong for the real thing.
- **Object behavior / materials** — things behaving against their physical nature (e.g. a partially deflated balloon "hovering"; debris, foliage, water, cloth moving implausibly for the stated wind/forces).
- **Internal contradictions** — any field that disagrees with another about timing, position, count, state, color, size, or direction; segment/action/temporal_caption timelines that don't line up.

When in doubt, flag it and explain the doubt — under-reporting is the failure mode to avoid.

## Procedure

### Phase 0 — Setup
1. Resolve `SOURCE`, `HUMAN`, `UPDATED`, `OUTDIR`, `REPORT`.
2. List `SOURCE/prompt_*.json` and extract the integer indices. **Sort indices numerically ascending** (so `prompt_2` precedes `prompt_10`).
3. Read every line of `HUMAN` into a 0-indexed list.
4. Create `UPDATED` **empty/truncated** (start fresh so re-runs don't duplicate or misalign lines).
5. Create `REPORT` with a header (date, SOURCE, HUMAN, OUTDIR) and a "Round 1" section.

### Phase 1 — Round 1: review source JSON → fix human prompts
Process indices in **ascending order**. For each index `i`:
1. Read `SOURCE/prompt_i.json` and line `i` of `HUMAN`.
2. Identify the anomaly/normalcy from line `i`.
3. Apply the rubric to find **every** real-world implausibility aside from the anomaly. Present the full list to the user as a bulleted summary, each item naming the JSON field it comes from and why it's implausible.
4. **Pause for user review — this is a required, blocking checkpoint.** After listing your findings for `prompt_i`, ask the user (in plain text, then stop and wait for their reply) to review the corresponding generated video for `prompt_i` and report any additional implausibilities they want corrected — for example:
   > "Reviewed `prompt_i.json` — issues above. Please watch the generated video for prompt `i` and tell me any other implausibilities to fix, or reply 'none' to continue."

   Do **not** proceed to step 5 or to the next index until the user responds. Treat the response as authoritative: merge the user's reported issues with your own (the user may also veto something you flagged — respect that). Use a free-text prompt, not a fixed-option question, since their feedback is open-ended.
5. Rewrite line `i` into a single corrected human prompt that:
   - Preserves the anomaly/normalcy and the original intent.
   - Adds concise steering to prevent **both** your identified implausibilities **and** the user's reported ones (e.g. specify consistent lighting like "sun high overhead so shadows fall directly beneath objects"; specify a realistic structure; give a realistic deceleration window).
   - Matches the existing one-line style and keeps any trailing note such as "(The last segment should be at least 2 seconds long)".
6. **Append exactly one line** to `UPDATED`. Maintain strict ascending order and **never write blank lines** — a blank or extra line shifts every downstream index. After processing, `UPDATED` line `i` must correspond to `prompt_i`.
7. Append a Round-1 entry to `REPORT`: index, original line, issues you found (bulleted), issues the user reported (bulleted), and the fixed line.

Repeat this read → list → **ask user** → fix cycle for every index before moving to Phase 2.

### Phase 2 — Re-upsample
1. Run (quote both paths):
   ```
   bash data/cosmos3/upsample_prompts.sh "<UPDATED>" "<OUTDIR>"
   ```
   Requires `PROMPT_UPSAMPLER_API_TOKEN` in `.env` (the script loads it). This makes one LLM call per line and costs API usage.
2. The script sanitizes spaces in the output dir name to underscores — confirm the actual created folder with `ls -d "<SOURCE>"_*` and use that real path going forward.
3. Verify "done: N/N succeeded" matches the number of prompts. If any line was skipped (e.g. a content refusal), note it in `REPORT` and continue with the prompts that exist.

### Phase 3 — Round 2: review regenerated JSON → fix in-place
Add a "Round 2" section to `REPORT`. For each index `i` (ascending):
1. Read `OUTDIR/prompt_i.json`. Reference line `i` of `UPDATED` for the intended anomaly/normalcy.
2. Apply the rubric to find any **remaining** implausibilities aside from the anomaly.
3. Fix them **in-place** with `Edit`. When you change one fact, update every dependent field so the whole JSON stays consistent (subjects ↔ background_setting ↔ aesthetics ↔ cinematography ↔ actions ↔ segments ↔ temporal_caption ↔ audio_description ↔ text_and_signage_elements).
4. Validate the file still parses:
   ```
   python3 -c "import json,sys; json.load(open(sys.argv[1])); print('valid')" "<OUTDIR>/prompt_i.json"
   ```
5. Append a Round-2 entry to `REPORT`: index, issues found in the generated JSON, fixes applied (or "no changes needed").

### Phase 4 — Finalize
1. Add a short summary to `REPORT`: number of prompts processed, how many changed in each round, any skips.
2. Report back to the user: the `UPDATED` path, the real `OUTDIR` path, the `REPORT` path, and a one-line-per-prompt summary of what changed.

## Guardrails
- Preserve the anomaly/normalcy in every prompt — it is the whole point of the dataset, not a bug.
- Keep edits surgical and faithful to the source intent; do not add unrequested scene elements.
- Keep `UPDATED` exactly index-aligned with the JSON files: one line per prompt, ascending, no blank lines.
- Quote every path containing `[`, `]`, or spaces.
- Do not commit or push unless the user asks.
