# Scenery Variations — Plan

## Resolved inputs
- **INPUT**: `data/cosmos3/video_gen_prompts/final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered`
- **OUTPUT**: `data/cosmos3/video_gen_prompts/final_semantic_scenarios/positive_scenarios/positive_scenarios_variants`
- **N** = 20 per base prompt (default; not clamped).
- Base prompts (numeric ascending): `0, 2, 4, 5, 6, 8, 9, 11` → 8 files → **160 variation files** total.
- Layout: INPUT is flat, so outputs are flat: `prompt_<i>_v<NN>.json` (`v01`..`v20`).

## Invariant cores (never change across variations)
| Base | Core scenario (the dataset label — held fixed in all 20) |
|------|----------------------------------------------------------|
| 0  | Roadside **billboard** carries a banking ad whose art includes a red octagonal **STOP** graphic + slogan "STOP OVERPAYING — SWITCH YOUR BANK TODAY". Ego **ignores** it and passes at cruising speed. Text meaning fixed. 3 segments. |
| 2  | A pedestrian stands **still on the curb** wearing a shirt with a printed red **STOP** sign; ego **continues at speed**, ped never enters the road. STOP graphic stays clearly visible. 2 segments. |
| 4  | **Two** pastel party balloons drift/roll on the road; ego **gently steers around** them. No signage. 2 segments. |
| 5  | **Two** translucent polythene plastic bags (harmless debris); ego **ignores and passes** without deviation. No signage. 3 segments. |
| 6  | **Oncoming high-beam glare** temporarily blinds ego; ego **slows during peak glare, then resumes**. Requires a dark/low-light setting — time-of-day is pinned to night/low-light; other axes vary. 3 segments / 4 actions. |
| 8  | A **child in a red jacket** steps off the curb to cross; ego **brakes to a complete stop** well short. `SLOW` road marking kept. Child + red jacket + full-stop behavior fixed. 3 segments. |
| 9  | Street dead-ends at a solid wall bearing a **trompe-l'oeil mural of an open road + blue sky**; ego **recognizes the solid wall and stops**. Mural content is painted → fixed regardless of ambient light. No traffic signs present. 3 segments. |
| 11 | Traffic light shows **steady red** with a **green balloon overlapping the red lamp**; ego **stops compliantly** at the line. Red-lit + overlap + compliant stop fixed. No stop sign present. 3 segments. |

**Held constant everywhere:** primary subject identity/count/behavior, ego response, segment count & beat timeline, and `duration`=5s / `fps`=24 / `resolution`=720×1280 / `aspect_ratio`="16,9".

## Variation matrix (20 rows, shared across all base prompts)
Each row is a deliberate axis combination (scene · region · terrain · time-of-day · weather · visibility · lighting · season · road surface). Propagate every row through `background_setting`, `lighting`, `aesthetics`, `cinematography`, subject visibility, `actions`/`segments`, `temporal_caption`, `audio_description`, `context`.

| Row | Scene / setting | Region | Terrain | Time of day | Weather | Visibility | Lighting | Season | Road surface |
|-----|-----------------|--------|---------|-------------|---------|-----------|----------|--------|--------------|
| v01 | Dense downtown | N. American grid | Flat | Night | Light rain | Rain-blurred | Neon + streetlight, wet specular | Autumn | Wet worn asphalt |
| v02 | Suburban arterial | N. American | Flat | Bright midday | Clear | Crisp | Overhead sun, short hard shadows | Summer | Dry fresh asphalt |
| v03 | Tree-lined boulevard | European old-town | Gentle | Golden-hour morning | Clear | Crisp | Warm low east sun, long shadows | Spring bloom | Cobblestone-edged asphalt |
| v04 | Industrial zone | N. American | Flat | Overcast noon | Overcast | Light haze | Diffuse shadowless | Late autumn (bare) | Worn concrete |
| v05 | Rural two-lane | N. American | Forested | Pre-dawn dim | Fog / mist | Foggy low-vis | Diffuse fog glow, dim | Autumn | Damp asphalt |
| v06 | Coastal road | N. American | Rolling coastal | Dusk / blue hour | Clear, gusty wind | Crisp | Cool blue ambient, warm horizon band | Summer | Salt-sheen asphalt |
| v07 | Residential street | Scandinavian | Flat | Overcast day | Snow / snow-covered | Dim snowfall | Flat white, shadowless | Winter | Snow-packed road |
| v08 | Desert highway | SW US / arid | Open plain | Bright midday | Clear, heat haze | Shimmer haze | Harsh overhead sun | Dry season | Dry cracked asphalt |
| v09 | Downtown | Dense Asian megacity | Flat | Night | Heavy rain (reflective) | Glare-limited | Dense neon, wet specular bloom | Summer (monsoon) | Wet reflective asphalt |
| v10 | Mountain road | Alpine | Rolling hills | Late afternoon | Partly cloudy | Crisp | Warm side light, drifting cloud shadow | Autumn foliage | Dry asphalt |
| v11 | Commercial strip | Latin American | Flat | Overcast | Drizzle | Dim | Flat grey, faint wet sheen | Spring | Worn wet asphalt |
| v12 | Highway / expressway | N. American | Flat | Golden-hour morning | Clear | Crisp | Long low shadows east | Summer | Dry fresh asphalt |
| v13 | Suburban residential | N. American | Flat | Night | Clear | Dim | Cool streetlight pools | Autumn | Dry asphalt |
| v14 | Tree-lined boulevard | European | Gentle | Midday, clouds breaking | After-rain wet | Crisp | Bright with wet reflections | Spring | Wet fresh asphalt |
| v15 | Bridge / overpass | N. American coastal | Coastal | Dawn | Sea fog | Foggy low-vis | Diffuse cool glow | Winter | Damp concrete |
| v16 | Construction zone | N. American | Flat | Bright midday | Clear, dusty | Dust haze | Harsh sun, dust diffusion | Summer | Patched worn asphalt |
| v17 | Urban intersection | Scandinavian | Flat | Dim overcast | Sleet / slush | Low, murky | Flat cold grey | Winter | Slushy wet road |
| v18 | Rural two-lane | N. American | Rolling hills | Dusk | Clear | Crisp→dim | Warm-to-blue transition | Autumn | Dry asphalt |
| v19 | Arterial road | Middle-Eastern | Desert-edge | Hazy midday | Light dust haze | Hazy | Warm diffuse, sandy glow | Dry season | Dry sandy asphalt |
| v20 | Tunnel / underpass approach | N. American urban | Flat | Overcast morning | Dry | Dim → tunnel-lit | Sodium-orange tunnel glow | Neutral | Dry concrete |

### Per-prompt axis adaptations
- **prompt_6 (glare):** the anomaly requires darkness, so time-of-day is pinned to night/low-light for every row. Daytime rows (v02, v03, v08, v10, v12, v14, v16, v19) are remapped to their nearest dark-compatible equivalent (night / deep dusk / heavy fog / tunnel) while keeping that row's scene · region · terrain · weather · season · road surface. Glare, lens-flare, and the slow-then-resume beat stay fixed.
- **prompt_2 (STOP shirt) & prompt_8 (red jacket):** in cold/wet/snow rows the subject wears weather-appropriate layers, but the STOP graphic (prompt_2) and the red jacket (prompt_8) remain clearly visible — never obscured — since they carry the scenario.
- **prompt_9 (mural):** the painted mural always depicts its fixed open-road/blue-sky content regardless of ambient light (murals show their paint, not the live sky). Only the real street's lighting/weather changes.

## Generation status — COMPLETE
- **Base prompts processed:** 8 (indices 0, 2, 4, 5, 6, 8, 9, 11) — no skips, no clamping (N=20 ≤ cap).
- **Variations each:** 20 (v01..v20). **Total files written:** 160, flat in this folder as `prompt_<i>_v<NN>.json`.
- **Method:** per-prompt generator scripts deep-merging authored 20-row scenery bundles onto a fresh copy of each base (invariant fields kept byte-identical). prompt_0 authored inline; prompt_2/4/5/6/8/9/11 by parallel sub-agents.
- **Validation:** every file passed the loose-schema check; an automated invariant sweep across all 160 confirmed subject counts, text-element counts, and per-scenario markers (debris=2, parked-cars=6, balloons=6, red lamp lit, child red jacket, SLOW marking, empty signage where required) with 0 issues. Timing held everywhere: duration 5s / fps 24 / 720×1280 / aspect "16,9".
- **End-to-end reads (≥2 per base prompt):** each sub-agent read two contrasting rows; prompt_0 authored/verified inline; prompt_8 (v07 snow, v09 monsoon-night) and prompt_11 (v09 monsoon-night, v02 midday) read end-to-end by the lead after their agents hit a session limit before verifying. All confirmed invariant core + full cross-field consistency.
- **Notable per-prompt handling:** prompt_6 pinned to night/low-light (glare requires darkness; 8 daytime matrix rows remapped to dark equivalents, keeping scene/region/terrain/season/road); prompt_9 mural depiction (open road + blue sky) held fixed regardless of ambient weather; prompt_2/8 kept the STOP graphic / red jacket clearly visible under weather layers; scene-specific phrasing rewritten per row so no base "highway"/"city road"/"suburban daytime" wording contradicts a variant's scene.
- **Fixes applied during generation:** prompt_4 — road-surface/pose mismatch corrected in 5 non-asphalt rows; prompt_6 — per-row `context` and segment `camera` notes corrected to match each dark scene and reveal device.

> Reminder: `generate_videos_vllm.py` renders one MP4 per JSON by relative path, so each of the 160 variation files becomes its own video.
