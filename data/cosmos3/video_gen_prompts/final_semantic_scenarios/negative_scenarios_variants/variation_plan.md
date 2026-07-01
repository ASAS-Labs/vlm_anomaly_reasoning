# Scenery Variations — Plan

**INPUT:** `data/cosmos3/video_gen_prompts/final_semantic_scenarios/negative_scenarios`
**OUTPUT:** `data/cosmos3/video_gen_prompts/final_semantic_scenarios/negative_scenarios_variants`
**N per base:** 20 (skill default; capped at 20)

Output files are named `prompt_<i>_v<NN>.json` (`v01`..`v20`). Each renders to its own MP4 via `generate_videos_vllm.py`.

## Invariant cores (never changed across variations)

| Base | Core scenario / anomaly (INVARIANT) | Duration | Res | Segs |
|------|--------------------------------------|----------|-----|------|
| prompt_0 | Overhead gantry billboard spanning the road shows a red octagonal **STOP** graphic (+ bank ad); ego car misreads it and **brakes to a full stop** before it. | 8s | 1280×720 | 3 |
| prompt_2 | Pedestrian wears a t-shirt printed with a red octagonal **STOP** sign; ego car misreads it and **brakes hard to a full stop** beside them. | 5s | 1280×720 | 3 |
| prompt_3 | Ego stopped at a steady **red** light (top lamp only, green never lights); a **green balloon** drifts over/overlaps the red lamp and the car **erroneously moves off** through the cleared crosswalk. | 5s | 1280×720 | 2 |
| prompt_4 | Two small stray **party balloons** (red + yellow) rest still on the road; ego **brakes hard to a stop**, treating them as obstacles. | 5s | 832×480 | 3 |
| prompt_5 | Two small white **polythene bags** rest still on the road; ego **brakes hard to a stop**, treating them as obstacles. | 5s | 832×480 | 3 |
| prompt_8 | A low-profile **small child** steps off the curb and crosses; ego **fails to slow**, dangerously closing distance (clip cuts before contact). | 5s | 832×480 | 3 |
| prompt_9 | Dead-end street ends in a wall bearing a hyper-realistic **trompe-l'œil road mural**; ego **drives straight into it and collides**, shattering the mural. | 5s | 832×480 | 3 |

For every variation the following are held fixed: the anomaly/normalcy and its causal logic; the primary subject(s)' identity/count/behavior/role and `number_of_subjects`/`number_of_arms`/`number_of_legs`; the ego-vehicle response; the action/segment/temporal beat structure and segment count; `duration`/`fps`/`resolution`/`aspect_ratio`; and any anomaly-defining sign wording (e.g. the "STOP" graphic text, the "WALK" signal). Only scenery is re-skinned, propagated through every dependent field.

## Variation matrix (axis templates, reused across all bases)

Each row is a deliberate combination across time-of-day / weather / visibility / lighting / scene type / region / terrain / season / scene-object appearance. Rows are adapted to each base's fixed road geometry (e.g. prompt_0 stays a highway, prompt_9 stays a dead-end street) while keeping the row's time/weather/light/season/region essence.

| Row | Time of day | Weather / visibility | Scene type & region | Terrain / season | Scene-object / surface cues |
|-----|-------------|----------------------|---------------------|------------------|------------------------------|
| v01 | Night | Light rain, wet reflective, low light | Dense downtown, North-American grid | Flat / late autumn | Neon + streetlights, wet black asphalt, specular highlights |
| v02 | Bright midday | Clear, crisp visibility | Suburban arterial, North-American | Flat / summer | Dry fresh asphalt, lush green foliage, parked sedans |
| v03 | Golden-hour morning | Clear, slight haze | Tree-lined boulevard, European old-town | Rolling / autumn | Warm low sun, cobble-edged asphalt, orange/red leaves |
| v04 | Early morning | Dense fog / mist, low visibility | Industrial zone | Flat / late autumn | Diffused grey glow, damp asphalt, muted colors, short visible range |
| v05 | Overcast noon | After-rain wet, sea haze | Coastal road | Coastal / spring | Flat shadowless light, wet reflective road, salt-worn surfaces |
| v06 | Overcast midday | Snow / snow-covered road | Residential street, Scandinavian | Snowfields / winter | Muted diffuse light, snow-dusted road, bare trees, muffled |
| v07 | Dusk / blue hour | Partly cloudy | Highway / expressway | Flat / autumn | Streetlights switching on, cool blue tone, dry asphalt |
| v08 | Bright midday | Clear, heat shimmer | Desert highway | Open desert / dry summer | Hard high sun, pale bleached asphalt, sparse scrub, dust |
| v09 | Afternoon | Heavy rain, rain-blurred, gusty | European city center | Flat / autumn | Overcast grey, streaming wet road, spray, low contrast |
| v10 | Pre-dawn dark | Clear, dim | Rural two-lane | Open plain / late summer | Headlight-only pool, dark surroundings, dew, quiet |
| v11 | Golden hour | Clear | Mountain road | Mountainous / summer | Long warm shadows, dry asphalt, pine greenery, distant peaks |
| v12 | Afternoon | Light haze, humid | Dense Asian megacity | Flat / summer | Neon/LED signage glow, hazy warm light, busy street furniture |
| v13 | Late afternoon | Partly cloudy | Residential street, North-American | Flat / spring bloom | Soft warm light, blossoming trees, dappled shade |
| v14 | Mid-morning | Overcast drizzle | Commercial strip | Flat / autumn | Grey flat light, damp asphalt, wet reflections, dull palette |
| v15 | Midday | Clear outside, artificial inside | Tunnel / underpass approach | Flat / n-a | Sodium/LED tunnel lighting, concrete, artificial glow bands |
| v16 | Dawn | Light mist | Forested road | Forested / late spring | Cool soft light, lush green, damp asphalt, ground fog wisps |
| v17 | Night | Clear | Plaza edge / parking-lot frontage | Flat / autumn | Sodium streetlights, warm pools, dark sky, dry asphalt |
| v18 | Afternoon | Sleet / cold rain, windy, dim | Bridge span | Elevated / winter | Grey dim light, wet slushy road, gusts, exposed railings |
| v19 | Bright midday | Clear, warm | Middle-Eastern arid city | Flat / dry summer | Warm stone/sand facades, bright hard sun, sandy road edges |
| v20 | Midday | Overcast, damp | Construction zone | Flat / autumn | Flat grey light, wet patched asphalt, cones/barriers, muted |

## Generation notes
- Each variation propagates its row through `background_setting`, `lighting.*`, `aesthetics.*`, night/fog-appropriate `cinematography` focus/DoF, subject `appearance_details`/visibility, `actions`/`segments` descriptions, `temporal_caption`, `audio_description`, and `context`, keeping the scene physically plausible.
- Invariant fields are carried over from the base unchanged.

## Phase 2 — Summary

- **Base prompts processed:** 7 (`prompt_0`, `prompt_2`, `prompt_3`, `prompt_4`, `prompt_5`, `prompt_8`, `prompt_9`), sorted numerically. No files skipped; no clamping (N=20 default).
- **Variations per base:** 20 (`v01`–`v20`).
- **Total variation files written:** **140** (`find … -name 'prompt_*_v*.json' | wc -l` = 140).
- **Validation:** every file carries the exact Cosmos3 schema keys of its base (no keys added/dropped), the 4-key `lighting`/`aesthetics` sub-objects, and identical `duration`/`fps`/`resolution`/`aspect_ratio` and segment/action counts. Invariant subjects were carried over verbatim, **except** `prompt_2`, where the single scene-locked noun "an urban road" was genericized to "the road" in the two subject fields so the non-urban re-skins (rural, desert, mountain, forest, coast, bridge) don't self-contradict — the pedestrian's identity, count, STOP-shirt graphic, and behaviour are unchanged.
- **Core scenario preserved in every variation** (billboard STOP → stop; STOP-shirt → stop; green-balloon-over-red → erroneous move-off; balloons/bags obstacle → hard stop; low-profile child → no-response near-miss; trompe-l'œil mural → collision). Only scenery (scene type, region, time-of-day, weather, visibility, lighting, season, road/scene-object appearance) was re-skinned, propagated through all dependent fields and kept physically plausible (e.g. calm air retained for the still/drifting-object scenarios; harsh-weather rows softened where a gust would break the anomaly; white bags placed on dark wheel-tracks in the snow row to stay visible).
- Each JSON renders to its own MP4 via `generate_videos_vllm.py` by relative path, so every variation becomes a separate video (140 videos total across this folder).

