# Realism Review Report — positive_scenarios

- Date: 2026-06-20
- SOURCE: `data/cosmos3/video_gen_prompts/positive_scenarios/opus_4.6_upsampled_prompts`
- HUMAN: `data/cosmos3/video_gen_prompts/positive_scenarios/prompt.txt`
- UPDATED: `data/cosmos3/video_gen_prompts/positive_scenarios/updated_human_prompt.txt`
- OUTDIR: `data/cosmos3/video_gen_prompts/positive_scenarios/opus_4.6_upsampled_prompts_[claude_authored]`

Prompts found (sorted): 0–11 (12 total).

---

## Round 1 — review source JSON → fix human prompts

### Index 0 — billboard advertisement with stop sign (car continues)
**Original line:** The ego view of a car travelling on a highway, coming across a billboard with an advertisement clearly showing a 'Stop Sign'. The ego vehicle continues driving at its normal speed as it drives past the banner. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** stop sign is part of an advertisement; car correctly ignores it and keeps speed.
**Issues I found:**
- Lighting/shadow contradiction: sun "ahead" at 2 o'clock but ego hood shadow cast "ahead" on the road (should fall behind).
- Banner backlit vs front-lit: faces oncoming traffic while sun is ahead, yet described as warmly front-lit.
- Impossible audio: aerodynamic "whoosh" from a small banner on the shoulder behind a guardrail.
- Object form/scale: rendered as a small 4×2 m roadside vinyl banner on two poles rather than a real highway billboard.
- Minor: ~60 cm STOP graphic legible at 0:02 while still distant at highway speed.
**User-reported issues:** none.
**Fixed line:** The ego view of a car travelling on a highway under clear daytime lighting with the sun high overhead so shadows fall directly beneath objects, coming across a large roadside billboard (elevated on a monopole just beyond the right shoulder, angled toward oncoming traffic) carrying an advertisement that clearly shows a 'Stop Sign'. The stop sign is part of the advertisement and not a real traffic sign; the ego vehicle continues driving at its normal cruising speed as it drives past the billboard without slowing or stopping. (The last segment should be at least 2 seconds long)

### Index 1 — truck carrying inactive traffic signals (car follows safely)
**Original line:** The ego view of a car approaching a truck ahead. The truck ahead is carrying traffic sign poles. The traffic signs are off, but the colours of the glass cover of one of them can be seen. The ego vehicle maintains a safe following distance behind the truck, completely ignoring the inactive signs on its cargo. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** inactive traffic-signal cargo with visible colored lenses; ego ignores them and keeps a safe following distance.
**Issues I found:**
- Divided-highway barrier geometry: barriers "on both sides separating opposing traffic" — only the left median separates opposing traffic.
- Overcast vs directional sun: "overcast" but with a defined high/ahead sun casting directional light.
- Following distance vs framing/scale: "safe following distance" but truck grows to fill the frame (implies tailgating).
- Minor: wind whoosh increasing as ego approaches the truck.
**User-reported issues:**
- Signals must show red, amber, and green lenses.
- Signals must stay off (never turn on).
- There should be a glare from one of the red lamps only.
  - Encoded as a sunlight specular reflection on a single red lens (not emitted light), so it stays consistent with "never turns on."
**Fixed line:** The ego view of a car on a divided highway (a median barrier on the left separates the opposing lanes) approaching a flatbed truck ahead in the same lane, under clear daytime lighting with the sun low behind the ego vehicle so shadows fall forward along the road. The truck carries inactive traffic signal heads as cargo; each head clearly shows three coloured lenses — red, amber, and green — but the signals are completely off and never light up. Bright sunlight catches one of the red lenses, producing a specular glare on that single red lamp only (a reflection, not an illuminated light). The ego vehicle keeps a safe following distance several car-lengths behind the truck, completely ignoring the inactive signals and the red-lens glare. (The last segment should be at least 2 seconds long)

### Index 2 — pedestrian with stop-sign shirt (car continues past)
**Original line:** The ego view of a car travelling an urban road approaches a pedestrian. The pedestrian standing next to the road and facing the ego vehicle wears a shirt clearly showing a stop sign. The ego vehicle continues driving smoothly past the pedestrian without slowing down. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** stop sign printed on the pedestrian's shirt; car correctly ignores it and continues.
**Issues I found:**
- Lighting contradiction: sun "slightly ahead" yet said to light the pedestrian's (camera-facing) front; a sun ahead would backlight the front and cast its shadow toward the camera, not "behind and to the left."
- Otherwise geometrically consistent (pedestrian on curb; green light ahead supports proceeding).
**User-reported issues:**
- The pedestrian should remain on the curb and not walk into the vehicle's lane.
**Fixed line:** The ego view of a car travelling on an urban road under clear daytime lighting with the sun behind the ego vehicle, so the pedestrian's front is well lit and shadows fall away from the camera. The car approaches a pedestrian who stands still on the curb (sidewalk) facing the ego vehicle and wears a shirt that clearly shows a stop sign. The pedestrian remains on the curb throughout and never steps into the vehicle's lane. The ego vehicle continues driving smoothly past the pedestrian, staying in its lane without slowing down. (The last segment should be at least 2 seconds long)

### Index 3 — intersection, pedestrians with green balloons (car holds at red)
**Original line:** The ego view of a vehicle on a city road stopped at a stop traffic sign. Ahead of the vehicle are pedestrians crossing carrying balloons, some of which are bright green. The vehicle remains safely stopped at the intersection until the traffic light officially changes to green. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved + refined):** a bright green balloon overlaps the red signal (potential green-light confusion); the vehicle correctly stays stopped at the red light. Per user, the light now stays red the whole clip (no transition to green).
**Issues I found:**
- Redundant/contradictory infrastructure: both a STOP sign and a traffic light govern the approach (contradiction also present in the source line). Fix: keep only the traffic light.
- ONE WAY "→" sign under the signal at a crosswalk the ego crosses straight — incongruous.
- Lighting: sun "high and slightly ahead" with mixed shadow directions.
- Schema artifact: 6-pedestrian group with number_of_arms/legs = 2.
**User-reported issues:**
- Traffic signal is on the right of the road, not overhead.
- Light must remain red for the whole video (no change to green); car stationary throughout, with the green balloon overlapping the red signal as pedestrians pass.
**Fixed line:** The ego view of a vehicle stopped at a city intersection where the traffic signal is mounted on a pole on the right side of the road (not overhead), under clear daytime lighting with consistent shadows. The traffic signal stays red for the entire clip and the vehicle remains completely stationary throughout, never moving. Ahead of the vehicle, pedestrians cross the road carrying balloons, some of which are bright green; one bright green balloon drifts so that it visually overlaps the red signal as the pedestrians pass. Despite the green balloon overlapping the signal, the vehicle correctly stays stopped at the steady red light. (The last segment should be at least 2 seconds long)

### Index 4 — stray balloons on road (vehicle maneuvers around)
**Original line:** The ego view of a vehicle travelling on a city road. Ahead of the vehicle are a couple of stray balloons near the floor, tossed around by the wind. The vehicle continues driving smoothly along its path, maneuvering aroung the balloons. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** harmless stray balloons on the road; vehicle smoothly steers around them.
**Issues I found:**
- Balloon behavior/material: "partially deflated" yet "hovering," and "hovering" conflicts with "rolling along the asphalt."
- Background STOP sign that could read as the ego running it.
- Lighting: sun "ahead and above" with left-side building shadows — mild inconsistency.
**User-reported issues:**
- Balloons should be medium, not oversized.
- There should be no stop sign.
**Fixed line:** The ego view of a vehicle travelling on a city road under clear daytime lighting with consistent shadows, with no stop sign present in the scene. Ahead of the vehicle are a couple of stray medium-sized balloons (ordinary party-balloon size, not oversized) drifting and rolling along the road surface at ground level, tossed around by the wind. The vehicle continues driving smoothly along its path, gently maneuvering around the balloons. (The last segment should be at least 2 seconds long)

### Index 5 — stray polythene bags (vehicle ignores)
**Original line:** The ego view of a vehicle travelling on a city road. Ahead of the vehicle are a couple of stray polythene bags near the floor, tossed around by the wind. The vehicle maintains its speed and lane position, ignoring the polythene bags. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** harmless windblown plastic bags; vehicle holds speed/lane and ignores them.
**Issues I found:** none major (lighting consistent; realistic). Minor: empty `pose` field; "drives over or beside bags" acceptable.
**User-reported issues:** none.
**Fixed line:** The ego view of a vehicle travelling on a city road under clear daytime lighting with consistent shadows. Ahead of the vehicle are a couple of stray polythene bags near the floor, tossed around by the wind. The vehicle maintains its speed and lane position, ignoring the polythene bags. (The last segment should be at least 2 seconds long)

### Index 6 — night oncoming-headlight glare (ego slows, then resumes)
**Original line:** The ego view of a vehicle, driving uphill along a city highway. As it begins to drive downhill after climbing, the bright headlights from an oncoming vehicle create major visual artifacts. The vehicle slows down allowing the oncoming vehicle to pass and the visual artifacts to be gone, before resuming nominal speed. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** oncoming high-beam glare/artifacts at night; ego slows to manage visibility then resumes.
**Issues I found:**
- Speed-limit sign rendered blue (white numerals on blue rectangle) — wrong for a regulatory limit sign.
- Divided highway with median barrier weakens the plausibility of strong oncoming glare.
- actions (5) vs segments (3) granularity mismatch (not a contradiction).
**User-reported issues:**
- Change to a rural two-lane road with no divider, making the glare plausible.
- Ego vehicle should slow down significantly.
**Fixed line:** The ego view of a vehicle driving at night along a rural two-lane road with no central divider, so oncoming traffic shares the road directly opposite (making oncoming-headlight glare plausible). The vehicle drives uphill and, as it crests and begins heading downhill, the bright high-beam headlights of an oncoming vehicle in the opposite lane create major glare and visual artifacts across the view. The ego vehicle slows down significantly to manage the impaired visibility, letting the oncoming vehicle pass and the artifacts clear, before resuming its nominal speed. (The last segment should be at least 2 seconds long)

### Index 7 — construction zone diversion (vehicle navigates safely)
**Original line:** The ego view of a vehicle travelling on a main road approaching a construction zone with a road diversion. The vehicle accurately detects the temporary traffic cones and altered lane markings, smoothly navigating the diversion path while staying safely within its designated lane. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** vehicle detects cones/temporary markings and navigates the work zone safely in its lane.
**Issues I found:**
- Construction warning sign color: subject says "yellow diamond" but work-zone warnings are orange (text element correctly says orange — self-contradiction).
- "DETOUR →" implies leaving onto another route, but the scene is a within-road lane shift.
- Temporary marking color (yellow) — minor regional nit.
- AV "detection chime" audio — acceptable for an AV demo.
**User-reported issues:**
- Make it a lane shift, not a detour: the oncoming lane is closed for construction and both directions share the ego vehicle's lane.
- Simple two-lane road (one lane each direction), no divider.
**Fixed line:** The ego view of a vehicle travelling on a simple two-lane road (one lane in each direction, no central divider) under clear daytime lighting with consistent shadows, approaching a construction zone. The oncoming traffic's lane is closed off for construction by orange traffic cones, so traffic from both directions temporarily shares the ego vehicle's lane — a lane-shift / shared-lane work zone, not a detour onto another route. Orange diamond construction warning signs and temporary lane markings mark the zone. The vehicle accurately detects the cones and altered lane markings and smoothly navigates through the shared section, staying safely within the open lane. (The last segment should be at least 2 seconds long)

### Index 8 — child crossing (vehicle stops safely)
**Original line:** The ego view of a vehicle travelling through a residential area. A small child steps off the sidewalk and begins crossing the road directly in the vehicle's path. The ego vehicle promptly decelerates to a safe and complete stop well before reaching the child. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** child enters the vehicle's path; ego brakes to a safe complete stop before the child.
**Issues I found:** none major — braking correctly characterized as firm/progressive (so the ~1.5–2 s stop from 25 mph is consistent); lighting consistent; "25" sign correct. Minor: sub-second timestamps in temporal_caption.
**User-reported issues:** none.
**Fixed line:** The ego view of a vehicle travelling through a residential area under clear daytime lighting with consistent shadows. A small child steps off the sidewalk and begins crossing the road directly in the vehicle's path. The ego vehicle promptly decelerates with firm, controlled braking to a safe and complete stop well before reaching the child, then remains stopped. (The last segment should be at least 2 seconds long)

### Index 9 — trompe-l'œil dead-end wall (vehicle stops)
**Original line:** The ego view of a vehicle travelling down a city street that ends at a solid structural wall painted with a hyper-realistic mural of an open road and skylight. The vehicle correctly comes to a controlled stop before reaching the wall. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** trompe-l'œil mural mimics a continuing road; vehicle recognizes the wall and stops.
**Issues I found:** none major — lighting consistent (sun ahead, vehicle shadow behind); realistic braking. Minor: "heat shimmer" at golden hour.
**User-reported issues:**
- There should be no traffic sign.
**Fixed line:** The ego view of a vehicle travelling down a city street that ends at a solid structural wall painted with a hyper-realistic mural of an open road and sky, under clear daytime lighting with consistent shadows. There are no traffic signs anywhere in the scene. The vehicle correctly recognizes the wall and comes to a smooth, controlled stop before reaching it, then remains stopped. (The last segment should be at least 2 seconds long)

### Index 10 — low moon near signal position at night (vehicle continues)
**Original line:** The ego view of a vehicle driving on a clear highway at night. A large, low-hanging yellow moon appears on the horizon directly ahead, positioned where an overhead signal might typically be. The ego vehicle continues driving at its cruising speed. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved + refined):** a moon positioned near an overhead signal could be confused with a signal lamp; the vehicle correctly proceeds on the actual green signal.
**Issues I found:**
- "Overhead signal" position vs horizon: moon on the horizon at the vanishing point, but likened to an overhead signal (which hangs high). Resolved per user by adding a real overhead signal and placing the moon just above its amber lamp.
- Lighting otherwise consistent (moon ahead → shadows toward camera); SPEED LIMIT 65 correct.
**User-reported issues:**
- Moon size should be normal, not large.
- Add an overhead traffic signal across the road; moon just above the amber lamp.
- There should be an intersection ahead.
- The signal should be green.
- Fix the overhead-signal-vs-horizon issue.
**Fixed line:** The ego view of a vehicle driving on a clear road at night, approaching an intersection ahead that is spanned by an overhead traffic signal mounted across the road on a mast arm. The overhead signal is showing a green light. A normal-sized (not enlarged) yellow moon hangs in the night sky directly ahead, positioned just above the amber (middle) lamp of the overhead signal. Shadows and reflections are consistent with the moonlight and the vehicle's headlights. The ego vehicle correctly reads the green signal and continues driving at its cruising speed through the intersection, unbothered by the moon near the signal. (The last segment should be at least 2 seconds long)

### Index 11 — balloons overlapping red light (compliant stop)
**Original line:** The ego view of a vehicle approaching an intersection with a standard regulatory traffic sign. The traffic light is now red, green, and amber off. A bundle of vibrant party balloons is tied to a post right next to the sign, swaying in the wind and partially overlapping the red light. The vehicle comes to a safe, compliant stop at the intersection. (The last segment should at least 2 seconds long)
**Anomaly/normalcy (preserved):** a green balloon overlapping the red lamp (potential green-over-red confusion); the vehicle correctly makes a compliant stop at the red.
**Issues I found:**
- Source-line self-contradiction: "the traffic light is now red, green, and amber off" (all off) but a red is needed to stop at. Fixed to "red illuminated, amber and green off throughout."
- Redundant infrastructure: a separate octagonal STOP sign "supplementing the traffic light" plus the red light. Fix: keep only the traffic light.
- Lighting consistent (sun behind → shadows ahead/right).
- Schema artifact: balloon cluster number_of_subjects = 9.
**User-reported issues:**
- The green balloon should overlap the red traffic light.
- Make the overlap physical (the green balloon sits over the red lamp), not a perspective effect.
- Red light remains on; amber and green remain off throughout.
**Fixed line:** The ego view of a vehicle approaching an intersection controlled by a single traffic light, under clear daytime lighting with consistent shadows. The red light remains illuminated throughout while the amber and green lamps stay off the entire time. A bundle of vibrant party balloons is tied to the traffic-light post and sways in the wind; one bright green balloon is positioned so that it physically overlaps the illuminated red lamp (the green balloon actually sits over the red light, not merely by camera perspective). There is no separate stop sign; the intersection is controlled only by the traffic light. Despite the green balloon overlapping the red lamp, the vehicle comes to a safe, compliant stop at the red light. (The last segment should be at least 2 seconds long)

_Round 1 complete (12/12 indices processed)._

---

## Round 2 — review regenerated JSON → fix in-place

Re-upsample: 12/12 succeeded into OUTDIR. One entry appended per index below. All 12 files validated as parseable JSON.

- **Index 0** — No changes needed. Lighting now consistent (top-lit, shadows beneath); realistic monopole roadside billboard; no aerodynamic whoosh; anomaly (ad stop sign, car continues) preserved.
- **Index 1** — No changes needed. R/A/G lenses present, signals off, single red-lens specular glare (reflection); median barrier on left only; lighting consistent. "One car-length" gap kept per user's explicit choice.
- **Index 2** — No changes needed. Pedestrian stays on curb / never enters lane; front-lit pedestrian (sun behind ego); consistent.
- **Index 3** — No changes needed. Right-side pole signal (not overhead); red throughout; car stationary; green balloon overlaps red signal; redundant stop sign removed.
- **Index 4** — No changes needed. Medium balloons; no stop sign present; "slightly deflated + rolling on ground" is consistent (not hovering).
- **Index 5** — FIXED in-place: removed a stray background STOP sign (`text_and_signage_elements` → []) that the ego drove past without stopping, which read as a violation rather than the intended "ignore harmless debris."
- **Index 6** — No changes needed. Rural undivided two-lane; ego slows significantly; glare plausible; no incorrectly-colored speed sign.
- **Index 7** — No changes needed. Orange construction warning signs (color fixed); lane-shift/shared-lane work zone per spec; simple undivided two-lane.
- **Index 8** — No changes needed. Firm/controlled braking to a safe stop; consistent lighting; realistic "SLOW" road marking.
- **Index 9** — No changes needed. No traffic signs (explicit, empty array); consistent lighting; smooth controlled stop.
- **Index 10** — FIXED in-place: `lighting.illumination_effect` said "wet-looking asphalt" while the road is dry on a clear night → changed to "dry asphalt." All user requirements met (overhead green signal, normal moon just above amber lamp, intersection, overhead-vs-horizon resolved).
- **Index 11** — No changes needed. Green balloon physically overlaps the illuminated red lamp; red on / amber+green off throughout; no separate stop sign.

_Round 2 complete (12/12 reviewed; 2 files edited in-place: index 5, index 10)._

---

## Summary

- Prompts processed: **12/12** (indices 0–11).
- **Round 1** (source JSON review → human-prompt fixes): all 12 human-prompt lines rewritten in `updated_human_prompt.txt`; user added video-review feedback on indices 1, 2, 3, 4, 6, 7, 9, 10, 11; replied "none" on 0, 5, 8.
- **Re-upsample**: 12/12 succeeded into `opus_4.6_upsampled_prompts_[claude_authored]`.
- **Round 2** (regenerated JSON in-place fixes): 2 files edited (index 5 stray stop sign removed; index 10 wet→dry asphalt); 10 needed no changes. All 12 validated.
- Anomaly/normalcy preserved in every prompt.

