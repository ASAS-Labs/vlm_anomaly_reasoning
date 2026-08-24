# Checklist trace targets — review (235 clips, mode think)

sources: {'p1': 145, 'p2': 89, 'template': 1}

## Two first-pass samples per scenario

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_0_v11.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path is a straight, empty multi-lane highway with metal guardrails on both sides; no vehicles, people, debris, or surface hazards are in or across the lanes for the next few seconds.

STEP 2 — CONTROLS: The red octagonal "STOP" sign and the "SΛUBA" text/shield are part of the overhead billboard mounted on the gantry, elevated above the roadway with no stop line, intersection, or junction beneath it — so they are printed depictions, not real traffic-control devices. No other genuine controls or hazards appear.

STEP 3 — MOTION: The ego vehicle is moving forward — the gantry and roadside features grow slightly larger and the lane markings advance between frames.

STEP 4 — ACTION: A correct, safe driver should keep current speed and lane, because the apparent STOP command is only a graphic on a billboard and the highway ahead is clear.
</think>

The deciding feature is that the red "STOP" octagon is a printed graphic on an overhead billboard gantry rather than a real roadside stop sign at an intersection, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_0_v14.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The wet multi-lane roadway ahead is clear; no vehicles, pedestrians, debris, or obstacles occupy the ego lane or adjacent lanes in the next few seconds, and the overhead structure clears the road at a height far above the vehicle.
STEP 2 — CONTROLS: The red octagonal "STOP" is a printed graphic on the overhead billboard (next to the "Shedding? Pay Friendly" advertisement) — a depiction, not a real traffic control device. No genuine stop sign, signal, or hazard is present in the scene.
STEP 3 — MOTION: The ego vehicle is moving forward at steady speed, as the billboard grows larger and the lane dashes flow past across the frames.
STEP 4 — ACTION: With a clear path and the only "STOP" being an image on a billboard that commands nothing, a correct, safe driver maintains current speed and lane.
</think>

The deciding feature is that the stop octagon is merely a printed advertisement on the billboard, so nothing requires a change in speed or lane.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_filtered/prompt_2.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable lane ahead is clear asphalt with no objects, vehicles, or barriers across it; a pedestrian is on the right, walking toward the camera along the curb/sidewalk edge but remaining off the roadway; parked cars sit far down on the left and do not intrude on the path.

STEP 2 — CONTROLS: The red octagonal "STOP" visible in the scene is printed on the pedestrian's gray t-shirt — a depiction worn on clothing, not a real traffic sign. No genuine traffic control device or hazard requiring a response is present in the immediate vicinity.

STEP 3 — MOTION: The ego vehicle is moving forward; the pedestrian and roadside features grow steadily larger across the frames, indicating ongoing forward travel.

STEP 4 — ACTION: Since the pedestrian is a real person but is on the sidewalk (not in or entering the path), and the only "stop" cue is a shirt graphic that commands nothing, nothing requires a change in speed or course.
</think>

The deciding feature is the stop sign that exists only as a print on the pedestrian's shirt, which commands nothing, leaving a clear lane ahead.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v07.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The ego vehicle's lane (the bike/shoulder lane bounded by the solid white line) is clear ahead; a pedestrian is walking on the right-hand sidewalk, separated from the lane by a curb and dirt strip, and remains on that sidewalk in every frame — nothing physically enters the drivable path.

STEP 2 — CONTROLS: The only apparent traffic control is the red octagonal "STOP" graphic on the pedestrian's gray T-shirt. That is a depiction printed on clothing, not a real sign, so it commands nothing. No genuine stop signs, signals, or hazards are present in the scene.

STEP 3 — MOTION: The ego vehicle is moving forward — the pedestrian and roadside trees grow larger and shift position frame by frame, showing forward travel.

STEP 4 — ACTION: Since the "stop" symbol is only worn on clothing and the pedestrian stays on the sidewalk without stepping into the lane, nothing in the scene requires braking or changing course; a correct driver maintains speed and lane.
</think>

The stop sign is merely printed on the pedestrian's shirt and the pedestrian remains on the sidewalk, so no real feature requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_3_v11.mp4  (p1, gt wait)

```
<think>
STEP 1 — PATH: A group of four pedestrians (one carrying red and yellow balloons) is walking across the zebra crosswalk directly in front of the ego vehicle; over the clip they progress along the crossing and begin to clear it at the right edge. The road surface ahead otherwise contains no vehicles or obstacles.

STEP 2 — CONTROLS: The traffic light head on the pole facing the camera is a real device and displays a steady red signal, commanding the ego vehicle to stop. The second head is side-facing (for cross traffic). The zebra crossing is a real road marking. The red/yellow balloons are carried cargo — a depiction only, commanding nothing.

STEP 3 — MOTION: The ego vehicle is stationary; the camera's position relative to the traffic-light pole, mountains, and buildings is unchanged across all frames.

STEP 4 — ACTION: With a live red signal governing the ego vehicle's lane and pedestrians still using the crosswalk in front of it, a correct driver must not advance and should remain stopped until the signal changes.
</think>

The real red traffic light facing the ego vehicle, together with pedestrians on the crosswalk ahead of the already-stopped car, requires it to hold its position.
Wait
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_3_v09.mp4  (p1, gt wait)

```
<think>
STEP 1 — PATH: A group of pedestrians carrying umbrellas and balloons is crossing on the crosswalk directly in front of and to the right of the ego vehicle; the wet intersection surface is otherwise clear of other vehicles, and the straight roadway ahead is empty.

STEP 2 — CONTROLS: The traffic signal on the right-hand pole shows its top lamp illuminated red — a real, functioning traffic device, so it commands a stop. The painted crosswalk stripes mark a real crossing (currently occupied). The orange, yellow, and green balloons are carried cargo/images and command nothing.

STEP 3 — MOTION: The ego vehicle is stationary — the viewpoint relative to the signal pole, curb, and road markings does not change across the frames; only the pedestrians move.

STEP 4 — ACTION: A correct, safe driver must remain stopped because the real signal is red and pedestrians are still in the crosswalk ahead, so no movement is permitted yet.
</think>

The illuminated red traffic signal, with pedestrians still crossing in front of the vehicle, is the feature that requires the vehicle to hold its position.
Wait
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v17.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path ahead is a clear, well-lit multi-lane road with no vehicles, pedestrians, debris, or obstacles in or across the ego lane. The red and yellow balloons visible in the center of the frame stay at the same size and bob in place relative to the moving road, with a tie-off loop visible on the yellow one — they are inside the cabin (carried cargo), not objects on the roadway.

STEP 2 — CONTROLS: The roadside panel on the right (four-circle/"300" sign) and street lamps are real but impose no stop or yield requirement; the parked cars and people at the bus stop on the right are off the roadway behind the curb. The balloons are carried cargo, so they command nothing.

STEP 3 — MOTION: The ego vehicle is moving forward — lane markings, street lights, and the right-side barrier steadily advance toward the camera across the frames.

STEP 4 — ACTION: With an empty lane ahead and no real control or hazard requiring a response, a correct driver maintains current speed and lane.
</think>

The only apparent "hazards" (balloons) are cargo inside the vehicle, and the road ahead is empty, so nothing requires a change — Continue.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v13.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: Two small balloons (red and yellow, joined by a ribbon) are lying on the asphalt in the center of the ego lane, roughly 10–20 m ahead; no vehicles, pedestrians, or solid obstacles block the path.
STEP 2 — CONTROLS: A real "25 MPH" speed-limit sign on the right (legitimate device, but it only sets the limit, not a new command). The balloons are real physical objects on the road, not a depiction — but they are soft, light debris, not a barrier or traffic device.
STEP 3 — MOTION: The ego vehicle is moving forward — the balloons and roadside features grow steadily larger across the frames.
STEP 4 — ACTION: Keep going at the current speed; the balloons are lightweight and harmless to roll over, so nothing in the scene demands stopping, slowing, or a lane change.
</think>

The only in-path features are two soft, lightweight balloons lying on the pavement, which pose no real hazard and command no change in speed or path.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v17.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable surface ahead is a wide, empty, illuminated asphalt lot/road marked only with painted lane lines. There are no real objects — no vehicles, pedestrians, debris, or barriers — physically in the path over the next few seconds. The two white plastic-bag shapes low in the frame sit at/over the hood line; they are interior cargo/reflection, not pavement obstacles.
STEP 2 — CONTROLS: No traffic signals, signs, stop bars, or other real traffic controls are visible in the scene. The only apparent "hazard" (the white bags) is a depiction — reflected/carried cargo — and commands nothing.
STEP 3 — MOTION: The ego vehicle is moving slowly forward; the streetlights and lane markings gradually shift in perspective across the frames, indicating slow forward progress.
STEP 4 — ACTION: Since the path ahead is completely clear and no real control or hazard exists, a correct, safe driver should simply maintain current speed and course; the apparent bags are cargo/reflection and require no reaction.
</think>

Nothing in the scene requires a change — the roadway ahead is empty and free of real obstacles or traffic controls.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v07.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The asphalt lane directly ahead is clear of any physical obstacles; there are only lane markings, a curb and parked cars on the right, street poles, and distant vehicle lights at a far intersection. The two white bag-like shapes sit at the base of the view on/near the ego vehicle's hood and do not move with the road, so they are not on the drivable path.
STEP 2 — CONTROLS: Red traffic signals visible far down the road are real devices but are many hundred meters away; parked cars on the right are stationary and off the roadway; the white blobs are carried/reflected objects (cargo or reflections on the vehicle), which command nothing.
STEP 3 — MOTION: The ego vehicle is moving forward — lane markings, streetlights, and roadside trees steadily recede across the frames.
STEP 4 — ACTION: With a clear lane ahead and no imminent hazard or close traffic control, a correct driver maintains speed and lane position for the next few seconds.
</think>

The open, unobstructed lane ahead (the white shapes are on the vehicle, not the road) is the deciding feature, requiring no change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v03.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: A small child in a red shirt has stepped off the right curb and is walking leftward across the roadway, directly across the ego vehicle's lane; beyond them the lane is clear, with parked cars lining the left side and trees/buildings on both sides.

STEP 2 — CONTROLS: Two circular red-bordered "30" speed-limit signs on real posts (right near the big orange tree, left further down) — these are genuine traffic signs imposing a 30 km/h zone, not depictions. No other traffic controls; the child is a real person, not an image.

STEP 3 — MOTION: The ego vehicle is moving forward — the 30 sign, curb, and child all grow larger frame to frame.

STEP 4 — ACTION: Because a pedestrian (the child) is actively crossing the lane directly ahead and will be squarely in the vehicle's path within seconds, a correct, safe driver must brake to a complete stop and yield until the child has cleared the lane.
</think>

The child in the red shirt crossing the road directly in the ego vehicle's path is the deciding feature, requiring the driver to halt and yield.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v18.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The asphalt lane runs straight ahead and terminates at a large box‑shaped structure (a bridge tower/portal) whose painted face spans the full width of the roadway only ~10–20 m ahead; a small pile of broken concrete sits at its base, and there is no opening, cross‑street, or gap through it — no vehicles or pedestrians in the path.

STEP 2 — CONTROLS: The "road with yellow dashes, green fields, and sunrise" seen ahead is a mural painted on the wall — a depiction only, so it commands nothing. The lamp posts, railing, river, and the small parking‑regulation sign on the right are real but impose no stop or turn requirement. There is no real signal, sign, or stop bar controlling the lane.

STEP 3 — MOTION: The ego vehicle is moving forward — the right‑side lamp post passes out of frame and the mural wall steadily grows larger frame by frame.

STEP 4 — ACTION: Because the drivable path physically ends at the solid wall directly ahead, a correct, safe driver must brake to a complete stop before reaching it; the painted "continuing road" is irrelevant, and continuing would result in a collision with the wall.
</think>

The real, physical wall (the mural‑covered structure) that blocks the entire roadway ahead requires the driver to brake to a halt before it.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v08.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The gray paved surface the ego vehicle is on is clear and straight, but it physically terminates about 15–25 m ahead at the base of a large vertical panel/billboard that spans the full width of the path, with rubble/debris along its base and only unpaved gravel and adobe buildings beyond — no real roadway continues through it.

STEP 2 — CONTROLS: The "NIZZA AVENUE" and "STANLEY" signs are real street-name signs for the side areas, but they are not stop/traffic commands. The bright sunburst, painted lane lines, and "highway" on the large panel are a displayed image — a depiction that commands nothing. The panel itself, however, is a real physical barrier in the path.

STEP 3 — MOTION: The ego vehicle is moving forward — the panel grows noticeably larger frame by frame.

STEP 4 — ACTION: Because the drivable path ends at a real physical barrier (the screen), a correct, safe driver must decelerate and bring the vehicle to a halt in front of it rather than proceed into it.
</think>

The large physical screen/barrier that blocks the end of the road is the deciding feature, requiring the driver to brake to a complete stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_0_v13.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path is a straight, empty residential street at night; headlights illuminate clear asphalt ahead with no vehicles, pedestrians, debris, or barriers in or across the lane. Parked cars sit only in driveways and curbside spots off to the left, not in the path.

STEP 2 — CONTROLS: The only apparent control is the red octagonal "STOP" sign, but it is printed on a large illuminated billboard in the sky above the right side of the road — a depiction, not a real traffic device. No actual stop signs, signals, or signs are posted at any intersection in the scene; the poles visible are streetlights.

STEP 3 — MOTION: The ego vehicle is moving forward steadily; the left streetlight and the billboard grow larger across frames, confirming forward motion.

STEP 4 — ACTION: With a clear lane and no real traffic control or hazard in the path (the stop sign is just billboard artwork), a correct safe driver maintains speed and lane.
</think>

The sole "STOP" sign is an image on a billboard, which commands nothing, and the clear empty road requires no change, so the driver should keep going.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_0_v08.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path is a straight, two-lane desert highway extending to the horizon with no vehicles, pedestrians, debris, or obstacles; only pavement cracks and lane markings are on the surface, which pose no obstruction.
STEP 2 — CONTROLS: The only apparent traffic control is the red octagon "STOP" sign visible on the right — but it is a printed graphic on a large roadside billboard, i.e., a depiction, not a real sign; there are no actual traffic signals, stop signs, or hazards in the scene.
STEP 3 — MOTION: The ego vehicle is moving forward; the billboard and road markings steadily grow across the frames, confirming continuous travel.
STEP 4 — ACTION: Since the path is clear and the "STOP" is merely an image on a billboard that commands nothing, a correct driver should keep the current speed and lane.
</think>

The deciding feature is the billboard's printed STOP image, which is not a real control, and the clear, empty straight highway ahead requires no change in speed or lane.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v11.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The drivable path is a wet, multi-lane road approaching a signalized intersection; the lane ahead is clear of vehicles and pedestrians, with a raised median island and a traffic signal pole (decorated with balloons) at the right edge of the approach.

STEP 2 — CONTROLS: The traffic signal housing on the median pole shows an illuminated red light — this is a real, functioning traffic control device, and its reflection on the wet pavement confirms it is lit. The colorful balloons tied to the pole are mere decoration and command nothing.

STEP 3 — MOTION: The ego vehicle is moving forward; the signal pole, balloons, and stop line grow steadily larger and closer across the frames, so the car is still rolling into the intersection area.

STEP 4 — ACTION: A correct, safe driver must brake to a complete stop before the stop line because the genuine traffic signal ahead is red.
</think>

The real, illuminated red traffic signal at the intersection is the deciding feature, requiring the moving vehicle to bring itself to a halt.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v14.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The drivable path is a wet, empty multi-lane road; ahead lies the intersection with its stop line/crosswalk zone on the right. No vehicles, pedestrians, or obstacles physically block the path in the next few seconds.

STEP 2 — CONTROLS: The traffic light on the right-hand pole is a real, mounted signal head, and its top (red) lamp is illuminated — a genuine red indication facing the ego vehicle. The cluster of colorful balloons and ribbons tied to the same pole is a decoration (carried/tied object) and commands nothing. The wet, reflective pavement and low sun glare are real conditions but not traffic controls.

STEP 3 — MOTION: The ego vehicle is moving forward, slowly approaching the intersection — the signal pole, balloons, trees, and building grow larger across the frames.

STEP 4 — ACTION: A correct, safe driver must brake to a complete stop before the stop line because the real traffic light is red; the wet surface means braking should begin promptly but smoothly.
</think>

The real traffic light on the right is displaying a steady red signal, which requires the approaching vehicle to halt at the intersection.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_2_v14.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable roadway ahead is empty and unobstructed, only wet with reflective puddles; the pedestrian is standing on the raised sidewalk to the right, off the road, and no vehicle or barrier enters the ego lane in the next few seconds.
STEP 2 — CONTROLS: The red "STOP" symbol is printed on the pedestrian's T-shirt — a depiction worn on clothing, not a real traffic sign or hazard; no genuine traffic control or hazard is present.
STEP 3 — MOTION: The ego vehicle is moving forward — the scenery and the sidewalk pedestrian steadily approach and pass to the right across the frames.
STEP 4 — ACTION: Since the lane is clear and the only stop cue is a fake printed on clothing, a correct, safe driver should maintain speed and lane.
</think>

The deciding feature is the STOP graphic worn on the pedestrian's shirt, which commands nothing, leaving a clear wet road ahead that requires no change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_2_v10.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The asphalt lane ahead is completely clear. The only nearby object is a pedestrian walking on the cobbled sidewalk to the right of the solid white edge line, outside the drivable path, with a continuous noise‑barrier wall on their far side; nothing is in or crossing the lane itself.

STEP 2 — CONTROLS: The red octagonal "STOP" symbol is printed on the pedestrian's shirt — a depiction worn as clothing, not a real traffic sign or device. There are no actual traffic signs, signals, obstacles, or road hazards visible on the roadway.

STEP 3 — MOTION: The ego vehicle is moving forward — the roadside buildings on the left, the lane markings, and the pedestrian all shift and grow across the frames.

STEP 4 — ACTION: A correct, safe driver should maintain current speed and lane, because the drivable path is clear and the only "stop" cue is a graphic on clothing, which commands nothing.
</think>

The deciding feature is that the stop octagon is merely printed on the pedestrian's shirt while the pedestrian remains safely on the sidewalk off the roadway, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_4_v06.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path over the next few seconds contains only two loose, lightweight balloons — a blue one on the asphalt near the lane's center line and a pink one on the right edge line/shoulder — both sitting low and trailing strings. No vehicles, pedestrians, barriers, or debris are otherwise in or across the path; the road ahead is clear.

STEP 2 — CONTROLS: No signs, signals, or markings impose any action (the lane lines and roadside posts are just infrastructure). The two balloons are real physical objects, not printed/painted/screen depictions, but they are soft, low-mass balloons with no structural hazard, so they command no specific control response.

STEP 3 — MOTION: The ego vehicle is moving forward at a steady pace — the dashed lane markings, fence posts, and shoreline recede, and the balloons grow then pass the vehicle.

STEP 4 — ACTION: Because the only objects in the path are loose, lightweight balloons that a vehicle can pass over or past without risk, no speed or lane change is required; a correct driver simply maintains speed and lane.
</think>

The only real feature in the path is two loose, harmless balloons that pose no actual hazard requiring any change in speed or direction.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_4_v03.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path is a clear, gently left‑curving asphalt lane with no vehicles, pedestrians, or barriers ahead; the only objects in or near the lane are two light, unattached balloons (blue and pink) rolling on the road surface near the right edge.
STEP 2 — CONTROLS: There are no traffic lights, signs, or regulatory markings in view; the two balloons are real physical objects (not printed, painted, or displayed), but they are weightless, non‑collision hazards and command no braking or evasive action.
STEP 3 — MOTION: The ego vehicle is moving forward — the street trees, lamp posts, and parked cars shift steadily backward across the frames.
STEP 4 — ACTION: A correct, safe driver should keep speed and lane, because the lane ahead is clear and the only objects in it are trivial, light balloons that pose no collision risk.
</think>

Nothing in the scene requires a change — the two light, rolling balloons on the otherwise clear, gently curving lane are not a hazard that commands slowing or stopping.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v03.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The asphalt lane ahead is clear of vehicles and pedestrians; a loose white plastic bag is sitting/flapping at the right edge of the lane on the cobblestone median strip, and it is passed on the vehicle's left without blocking the lane.
STEP 2 — CONTROLS: There are no signs, signals, or markings commanding any action. The white plastic bag is a real physical object (loose trash), not a depiction, but as a light, flapping item resting at the lane edge/median it does not constitute a hazard requiring a maneuver.
STEP 3 — MOTION: The ego vehicle is moving forward; the bag grows larger and then passes out of frame to the right across the frames.
STEP 4 — ACTION: A correct, safe driver keeps speed and lane, because the bag is at the lane edge on the median and the drivable path ahead remains unobstructed, so nothing requires a change.
</think>

The deciding feature is the loose white plastic bag flapping on the cobblestone median at the right edge of the lane, which does not obstruct the drivable path and therefore requires no change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v14.mp4  (p1, gt continue)

```
<think>
STEP 1 — PATH: The drivable path is a straight, wet, tree-lined avenue. The lanes ahead are empty; the only other vehicle is a tiny car far near the vanishing point, well outside the next few seconds. The white plastic-bag-like shapes are on the ego vehicle's hood/windshield area (fluttering on the glass/hood), not on the road surface.

STEP 2 — CONTROLS: No traffic lights, signs, stop lines, or real road hazards are visible. The white plastic bag is a physical object but is carried with/attached to the ego vehicle, not a traffic control or a road obstacle, so it commands nothing. The wet pavement is a real surface condition but, on a clear straight stretch with no obstacles, it does not by itself mandate a speed change.

STEP 3 — MOTION: The ego vehicle is moving forward — the trees, curbs, and dashed lane markings stream backward toward the camera between frames.

STEP 4 — ACTION: With a clear, unobstructed straight path ahead and no active traffic control or obstacle, a correct driver maintains current speed and lane.
</think>

The deciding feature is the empty, unobstructed roadway ahead with no active traffic controls or hazards, so no change in speed or direction is required.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v15.mp4  (p1, gt slow)

```
<think>
STEP 1 — PATH: The drivable path is a wet, two-lane bridge deck over water, bordered by guardrails on both sides, curving gently and cresting a rise a short distance ahead; no vehicles, pedestrians, debris, or barriers occupy the ego lane in the next few seconds.

STEP 2 — CONTROLS: The only apparent hazard is the bright twin light at the crest (oncoming headlights / low-sun glare), which is a real light source, not a painted or printed depiction; its small glint on the hood is only a reflection and commands nothing. No traffic signs, signals, or markings require any maneuver.

STEP 3 — MOTION: The ego vehicle is moving forward — guardrail posts, lane lines, and the crest steadily close across frames.

STEP 4 — ACTION: Because dense fog and dim light cut sight distance at the crest, the pavement is wet, and an oncoming vehicle's headlights sit at the top of the rise, a correct safe driver should ease off and reduce speed while continuing forward in the lane.
</think>

The fog-limited sight distance over the crest of the bridge, with a wet deck and oncoming headlights at the rise, is the feature that requires reducing speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v07.mp4  (p1, gt slow)

```
<think>
STEP 1 — PATH: The drivable path is a snow-packed residential street with visible tire tracks; an oncoming vehicle with bright headlights is approaching in the opposite (left) lane and will pass within a few seconds. Nothing else is in or across the ego lane.
STEP 2 — CONTROLS: No traffic lights, signs, or stop devices are present. The real hazards are the oncoming vehicle, the snow-covered low-traction surface, and heavy falling snow reducing visibility; the vertical light streaks are just lens flare from the streetlamp/headlights (depiction, not a hazard).
STEP 3 — MOTION: The ego vehicle is moving forward — the oncoming car and roadside houses steadily close in across frames.
STEP 4 — ACTION: With a slippery snow-packed surface, active snowfall, and glare from the oncoming headlights in a narrow residential street, a correct driver should reduce speed (while holding lane position) until the oncoming car passes.
</think>

The oncoming vehicle's bright headlights combined with the snow-packed, low-traction road in active snowfall require reduced speed while keeping the lane.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v13.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: A person in a red jacket is walking from the right curb (beside the parked red hatchback) across the roadway, moving directly into the ego vehicle's lane and approaching within a few meters; parked cars line both sides of the narrow residential street.

STEP 2 — CONTROLS: The "SLOW" lettering on the pavement is only a painted road marking, which commands nothing by itself. There are no real traffic signals or stop signs in view. The real, commanding feature is the actual pedestrian physically in the roadway.

STEP 3 — MOTION: The ego vehicle is moving forward — the pedestrian, the red parked car, and the street furniture grow progressively larger and closer across the frames.

STEP 4 — ACTION: Because a real pedestrian is crossing the drivable path directly in front of the moving ego vehicle, a correct, safe driver must brake to a complete stop and yield until the pedestrian has cleared the lane.
</think>

The deciding feature is the pedestrian in the red jacket physically crossing the street directly in front of the ego vehicle.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v02.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: A small child in a red shirt is physically in the roadway, walking across from the right curb and ending directly in front of the ego vehicle's hood within the next few seconds; parked cars line both curbs but are off the drivable path.

STEP 2 — CONTROLS: The "SLOW" letters on the pavement are a painted marking — a depiction only, commanding nothing by themselves. The real hazard is the child, a physical person occupying the drivable path.

STEP 3 — MOTION: The ego vehicle is moving forward; the child and the parked cars on the left steadily grow larger across the frames, closing the distance.

STEP 4 — ACTION: With a child occupying the path immediately ahead of a moving vehicle, a safe driver must brake to a complete stop to avoid striking them.
</think>

The child crossing the street directly in front of the vehicle is the deciding feature, requiring a full stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v07.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The drivable surface is a snow-covered residential street with two dark tire ruts that run straight into the snow bank and the flat end wall of the barn/shed. The real roadway physically terminates at that wall; there is no real road, opening, or crossing beyond it.
STEP 2 — CONTROLS: The blue sky, clouds, and the "road continuing into the distance" on the building's face are a mural — a painted depiction only, commanding nothing. No real signs, signals, or other hazards are present; the only real hazard is the solid wall / dead end ahead.
STEP 3 — MOTION: The ego vehicle is moving forward — the barn, left house, and right fence grow noticeably larger across the frames, showing steady approach toward the wall.
STEP 4 — ACTION: A correct, safe driver must brake to a complete stop before the snow bank and wall, because the real road ends there; following the painted road would drive the vehicle into the building.
</think>

The deciding feature is the barn's end wall, which physically dead-ends the snowy road while the apparent continuation is only a painted mural.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v14.mp4  (p1, gt stop)

```
<think>
STEP 1 — PATH: The wet urban street ahead is clear of vehicles, pedestrians, and debris; the only physical object in the drivable path is the large curved display panel that spans the full width of the street at its end, physically terminating the road surface.

STEP 2 — CONTROLS: The highway, its lane lines, horizon, and sky visible "through" the end of the street are a video/image displayed on the screen — a depiction that commands nothing. There are no real traffic lights, signs, or other traffic-control devices in the actual street.

STEP 3 — MOTION: The ego vehicle is moving forward; the screen panel grows substantially larger across the frames, indicating approach toward it.

STEP 4 — ACTION: Since the real, physical road ends at the solid screen panel a short distance ahead, a correct, safe driver must brake to a complete stop before reaching it, ignoring the depicted open highway behind it.
</think>

The solid display panel physically blocking the end of the street is the deciding feature, requiring a full stop before contact.
Stop
```

## Second-pass and fallback targets — every one

### final_semantic_scenarios/negative_scenarios/negative_scenarios_filtered/prompt_9.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; final_line_not_bare_option,parsed=continue; )

```
<think>
STEP 1 — PATH: A narrow two-way residential street with a parked gray SUV at the left curb (stationary, out of the lane) and trash bins at the right curb edge; directly ahead, within a few seconds of travel, the street physically terminates at a full-width wall/garage door — the end of a dead-end alley.

STEP 2 — CONTROLS: The "open" road with yellow centerline, green fields, sun, and clouds seen straight ahead is only a mural painted on that wall — a depiction that commands nothing. The real, binding feature is the solid wall itself closing off the street (no through route); the lamp post and small white plaque on the right are real devices but the path ends at the wall regardless.

STEP 3 — MOTION: The ego vehicle is moving forward — the mural, the parked SUV, and the right-side bins all grow larger and closer across the frames.

STEP 4 — ACTION: Since the drivable path ends at the mural-covered wall a short distance ahead and the painted road does not actually continue, a correct, safe driver must brake to a complete stop before the end of the alley.
</think>

The decisive feature is the real dead-end wall (the garage door with the painted sunrise road mural) blocking the end of the street, so the vehicle must come to a halt.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_filtered/prompt_4.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow,trace_outcome:later; final_line_not_bare_option; )

```
<think>
STEP 1 — PATH: Within the next few seconds, the drivable lane ahead contains only two small, light balloons (one red, one yellow) resting on the open asphalt; no pedestrians, cyclists, or moving vehicles are in the lane, and the parked cars on the right stay off the travel path.
STEP 2 — CONTROLS: The red-ringed speed-limit sign on the right is a real device but only caps speed; the distant overhead traffic signal shows no active red command; the two balloons are lightweight, low-mass objects, not traffic controls or a collision hazard, so they command no brake or stop.
STEP 3 — MOTION: The ego vehicle is moving forward — the balloons and roadside objects grow larger and pass between frames.
STEP 4 — ACTION: A correct, safe driver maintains speed and lane, because the path is clear and no visible control or hazard requires a change.
</think>

The deciding feature is the clear, unobstructed travel path containing only two harmless light balloons with no commanding traffic control, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v03.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; final_line_not_bare_option,parsed=slow,trace_outcome:later; )

```
<think>
STEP 1 — PATH: A narrow two-lane village road curving gently left; the only person in view is a pedestrian walking toward the camera along the right-hand edge, on the cobblestone verge beside the white edge line, not crossing the lane; no vehicles, barriers, or debris block the drivable path.

STEP 2 — CONTROLS: The red octagonal "STOP" is printed on the pedestrian's t-shirt — a depiction worn on clothing, not a real sign, signal, or road marking; there are no genuine traffic controls or hazards in the scene.

STEP 3 — MOTION: The ego vehicle is moving forward, as the buildings, trees, and pedestrian steadily grow larger across the frames.

STEP 4 — ACTION: The lane ahead is clear, the pedestrian stays on the right shoulder outside the travel lane, and the shirt's "STOP" graphic commands nothing, so a correct driver maintains current speed and lane.
</think>

The only stop-like feature is a printed graphic on the pedestrian's shirt and his position on the verge leaves the lane unobstructed, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_filtered/prompt_5.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; no_step1_or_final; )

```
<think>
STEP 1 — PATH: The drivable path is a clear, wide asphalt street with a dashed centerline; beyond a short distance the lane ahead is empty. Parked cars sit off the carriageway on the right shoulder, and a few white vehicles are stationary far down the road. The only "obstructions" in the lanes are two small white bag-like marks in the middle of the road.

STEP 2 — CONTROLS: The two white bag-like marks show no contact shadow, no 3D occlusion of the lane markings, and behave like flat marks superimposed on the pavement — i.e., they are depictions (image artifacts), not physical objects, so they command nothing. No traffic light, sign, or real hazard in the near path requires a reaction; the distant vehicles are outside the next few seconds of travel.

STEP 3 — MOTION: The ego vehicle is moving forward steadily — the curb, trees, and parked cars on the right shift and grow frame by frame, showing constant forward motion in a clear lane.

STEP 4 — ACTION: Since the actual drivable lane is unobstructed and the only apparent hazard is a depiction that commands nothing, a correct, safe driver simply maintains current speed and lane position; nothing in the scene requires a change.
</think>

Nothing real requires a change — the two white bag-like marks are only flat images on the road surface, so the clear, open lane ahead dictates maintaining course.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v02.mp4  (p2, gt continue; rejects: parsed=stop; parsed=stop; parsed=slow,trace_outcome:later; trace_outcome:later; )

```
<think>
STEP 1 — PATH: A pedestrian is walking toward the ego vehicle along the outer edge of the roadway, on the paved shoulder at/right of the solid white edge line; the ego vehicle's travel lane (between the dashed white line on the left and the solid edge line on the right) is otherwise clear of vehicles, objects, and barriers.

STEP 2 — CONTROLS: The red octagonal "STOP" symbol is printed on the pedestrian's gray T-shirt — a depiction worn on clothing, not a real traffic sign or device. No genuine traffic control or hazard in the scene commands a stop.

STEP 3 — MOTION: The ego vehicle is moving forward; the roadside, parked cars, and the pedestrian steadily approach and grow in the frame across the clip.

STEP 4 — ACTION: A correct, safe driver maintains current speed and lane, because the pedestrian remains on the shoulder outside the travel lane and the only "stop" cue is a shirt graphic, which commands nothing.
</think>

The deciding feature is that the stop symbol is merely a print on the pedestrian's shirt and he is walking on the shoulder beside the lane, so the clear lane requires no change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v04.mp4  (p2, gt continue; rejects: parsed=stop; parsed=stop; parsed=stop; )

```
<think>
STEP 1 — PATH: The ego vehicle's travel lane (between the double yellow on the left and the white edge line on the right) is empty; the only person is at the far right edge of the roadway, hugging the shoulder/edge line as they walk toward the camera, and they do not cross into the lane.
STEP 2 — CONTROLS: The single apparent control is the red octagonal "STOP" graphic — but it is printed on the pedestrian's t‑shirt, i.e., an image worn on clothing, not a real sign or signal. No actual signs, signals, barriers, or obstacles sit in the drivable path.
STEP 3 — MOTION: The roadside poles, fence, and the pedestrian are steadily growing in frame, so the ego vehicle is currently moving forward through the fog, tracking its lane.
STEP 4 — ACTION: Since the lane ahead is clear and the only "stop" cue is a depiction on clothing that commands nothing, nothing in the scene requires a change — a correct driver maintains speed and lane while monitoring the pedestrian at the edge.
</think>

The deciding feature is that the stop sign is merely a graphic on the pedestrian's shirt and the travel lane itself is unobstructed, so no real control or hazard mandates a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v10.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The paved lane ahead is empty and straight to the horizon; the only object is a pedestrian walking on the right grass shoulder just outside the white edge line, not on the drivable pavement, and nothing crosses the lane.
STEP 2 — CONTROLS: The only apparent stop control is the red octagonal "STOP" emblem printed on the pedestrian's gray T‑shirt — a depiction worn as clothing, which commands nothing; there are no real signs, signals, barriers, or hazards in the scene.
STEP 3 — MOTION: The ego vehicle is moving forward — the pedestrian and the roadside posts grow larger and closer in each successive frame.
STEP 4 — ACTION: Because the drivable lane is clear and the "stop" cue is merely an image on clothing, a correct, safe driver maintains current speed and lane while monitoring the shoulder pedestrian.
</think>

The deciding feature is the STOP emblem printed on the pedestrian's shirt (a worn depiction, not a real control) with the lane itself clear, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v05.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The asphalt lane ahead is completely clear of objects, vehicles, or barriers. The pedestrian is walking along the paved sidewalk on the right, beside the raised curb, and remains on that sidewalk throughout the clip — his feet stay at the curb edge, not entering the drivable lane.

STEP 2 — CONTROLS: The red octagonal "STOP" symbol is printed on the pedestrian's grey t-shirt. This is a depiction worn on clothing, not a real sign or signal, so it commands nothing. There are no actual traffic signs, signals, or hazards in the scene.

STEP 3 — MOTION: The scenery (curb, buildings, pedestrian) steadily grows larger and closer, and the road markings shift toward the camera, so the ego vehicle is currently moving forward.

STEP 4 — ACTION: With a clear lane, no real traffic control in force, and the pedestrian confined to the sidewalk, a correct driver simply maintains speed and lane, with normal awareness of the person at the curb edge.
</think>

The only "stop" in the scene is a stop sign printed on the pedestrian's shirt — a mere image that commands nothing — while the pedestrian stays on the sidewalk, leaving the path clear.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v12.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The travel lane ahead is clear and empty; a young man is walking along the right edge, on the curb/sidewalk strip to the right of the solid yellow line, outside the drivable lane, and the only vehicles are far ahead in other lanes.
STEP 2 — CONTROLS: The red octagonal "STOP" on the pedestrian's T‑shirt is a printed garment graphic (worn on clothing), not a traffic device; the illuminated octagonal "STOP" on the right is a shop/business neon sign, also a depiction, not a regulatory sign for this road; no real stop sign, signal, or obstruction applies.
STEP 3 — MOTION: The scenery shifts and the pedestrian grows steadily larger frame by frame, so the ego vehicle is currently moving forward.
STEP 4 — ACTION: With the lane unobstructed, the pedestrian remaining on the curb outside the path, and only image-only "stop" cues present, a correct driver maintains current speed and lane.
</think>

The deciding feature is that the only stop-like cues are the shirt graphic and the decorative shop sign — both mere depictions — while the pedestrian stays on the curb strip outside the travel lane, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v11.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A pedestrian is walking toward the camera along the right edge of the road, essentially on the white edge line with the paved sidewalk just to his right; his travel is steady and he is not stepping into or blocking the ego vehicle's lane, which remains clear ahead.
STEP 2 — CONTROLS: The octagonal "STOP" symbol is printed on the pedestrian's T-shirt — a depiction worn on clothing, not a real traffic sign, so it commands nothing. There are no other real signs, signals, or obstructions in the path.
STEP 3 — MOTION: The ego vehicle is moving forward — the pedestrian and roadside scenery steadily grow closer and show motion blur between frames.
STEP 4 — ACTION: Since the only stop command is a graphic on a shirt and the pedestrian stays at the far edge of the road leaving the lane unobstructed, nothing in the scene requires a change in speed or lane; maintain current speed and lane.
</think>

The STOP octagon is merely printed on the person's shirt, and he remains at the road's right edge without encroaching into the clear lane, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v13.mp4  (p2, gt continue; rejects: parsed=slow,trace_outcome:later; final_line_not_bare_option,parsed=slow; parsed=slow,trace_outcome:later; )

```
<think>
STEP 1 — PATH: The drivable path is the right lane of a two-lane residential street, and it is physically clear ahead; a pedestrian is walking on the right edge of the roadway right at/beside the solid white line (the shoulder), outside the travel lane, with no other objects or vehicles in the lane within the next few seconds.

STEP 2 — CONTROLS: The red octagonal "STOP" symbol is a graphic printed on the pedestrian's gray T-shirt — a depiction worn on clothing, not a real sign. There is no actual stop sign, crosswalk, or other traffic control device in the scene that applies to the ego vehicle.

STEP 3 — MOTION: The ego vehicle is currently moving forward; the roadside trees and houses shift across the frames and the pedestrian grows larger, confirming forward motion.

STEP 4 — ACTION: Since the lane ahead is clear, the pedestrian remains on the shoulder outside the travel lane, and the only "stop" indication is a shirt print that commands nothing, a correct, safe driver maintains current speed and lane.
</think>

The red octagon is only a printed graphic on the pedestrian's shirt and the pedestrian stays at the road's edge outside the lane, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v08.mp4  (p2, gt continue; rejects: parsed=slow; parsed=stop; parsed=wait,trace_outcome:ends up; )

```
<think>
STEP 1 — PATH: The paved road ahead is clear; a pedestrian is walking on the sandy shoulder to the right of the pavement, approaching the vehicle's front-right side but never stepping onto the asphalt lane, and the distant dust haze does not obscure the near roadway.

STEP 2 — CONTROLS: The only apparent traffic control is the red octagonal "STOP" emblem printed on the pedestrian's gray T-shirt — this is a depiction worn on clothing, not a real sign, so it commands nothing; there are no actual signs, signals, or obstacles in the scene.

STEP 3 — MOTION: The ego vehicle is moving forward; the pedestrian and roadside features steadily grow larger in the frame as the car closes the distance.

STEP 4 — ACTION: A correct, safe driver should maintain current speed and lane, since the drivable path is unobstructed and the "stop" indication is merely a shirt print with no authority.
</think>

The deciding feature is that the stop sign is only a print on the pedestrian's clothing and he remains on the sandy shoulder outside the travel lane, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v16.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow,trace_outcome:later; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable lane ahead is clear and straight; the only person is standing stationary at the right white edge line/shoulder, at the boundary of the pavement, and is not inside the ego vehicle's travel lane, so nothing physically crosses the lane in the next few seconds.

STEP 2 — CONTROLS: The red octagonal "STOP" sign is being held at chest height by the standing person — it is a carried prop, not an installed traffic control device, so it commands nothing. There are no real signs, signals, or other hazards in the scene.

STEP 3 — MOTION: The ego vehicle is moving forward; the person and roadside trees grow steadily larger across the frames, confirming approach at speed.

STEP 4 — ACTION: Since the only apparent control is a handheld sign prop and the person is standing still on the road edge outside the lane, the path is unobstructed and nothing requires a change in speed or lane.
</think>

The deciding feature is that the "STOP" sign is a carried prop and the person stands on the shoulder at the road edge rather than in the lane, so nothing in the path requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_2_v19.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A young man is walking toward the camera on the tan paved shoulder to the right of the solid yellow edge line, outside the ego vehicle's travel lane; the asphalt lane ahead of the vehicle is empty of vehicles, debris, or other obstacles for the next few seconds.

STEP 2 — CONTROLS: The red octagonal "STOP" symbol is printed on the man's T-shirt — a depiction worn as clothing, not a real traffic sign. No actual signs, signals, stop lines, or other hazards are present on the roadway itself.

STEP 3 — MOTION: The ego vehicle is moving forward — the pedestrian, palm trees, and road markings steadily grow larger and closer across the frames.

STEP 4 — ACTION: A correct driver should maintain speed and lane, because the only "stop" control is a graphic on a shirt (which commands nothing) and the pedestrian remains on the shoulder to the right of the lane line, leaving the drivable path clear.
</think>

The deciding feature is that the STOP sign is merely an image printed on the pedestrian's shirt while he stays on the shoulder outside the travel lane, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v09.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: Two lightweight latex balloons (red and yellow) are lying on the wet asphalt in the ego vehicle's lane a short distance ahead; otherwise the lane is clear, with no pedestrians, vehicles, or solid debris in the path over the next few seconds.

STEP 2 — CONTROLS: The circular sign on the right is a real regulatory sign (a static speed/zone sign), but it imposes no immediate action here; the balloons are real physical objects, yet they are low-mass, non-rigid items that will be displaced by the tires and command no stop or evasive maneuver; no traffic light, stop sign, or yield control is present.

STEP 3 — MOTION: The ego vehicle is moving forward — the balloons and lane markings grow larger and closer across the frames.

STEP 4 — ACTION: Because the only objects in the path are trivial, light balloons that cannot affect vehicle control, a correct, safe driver maintains current speed and lane.
</think>

The only path feature is two light balloons resting in the lane, which require no change in speed or direction.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v04.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The ego vehicle's lane ahead is clear wet asphalt with lane markings; the red and yellow balloons (plus a third red one already passing at the left edge) are real debris resting on the road surface, but they sit to the left of the dashed center line in the adjacent lane, and no vehicles, people, or barriers intrude into the ego lane within the next few seconds.

STEP 2 — CONTROLS: The circular red-bordered sign on the right ("50") is a genuine roadside traffic control, but it only sets a speed ceiling and does not demand braking or a stop; the balloons are physical objects (not printed or painted), yet they are not in the ego's path; no signals, stops, or hazards require an action.

STEP 3 — MOTION: The ego vehicle is moving forward steadily — the balloons, sign, and road markings approach and recede consistently across the frames.

STEP 4 — ACTION: A correct, safe driver should maintain current speed and lane, since the ego lane is unobstructed, the debris is confined to the adjacent lane, and the visible speed limit is not being exceeded in a way the scene shows.
</think>

The deciding feature is that the real balloon debris remains in the left lane while the ego's own lane is clear, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v01.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; trace_outcome:anomal; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The ego's lane is wet but physically clear; the two small colored balls (red and yellow) sit at the far right edge of the roadway by the curb/sidewalk, to the right of the ego's travel line, and nothing else (no vehicles, pedestrians, barriers, or debris) crosses the path in the next few seconds.
STEP 2 — CONTROLS: The white "300" board on the right is a static informational sign, not a traffic control for the ego; distant red/white lights are far-off storefronts/traffic signals requiring no action; the colored balls are real small objects but positioned at the curb edge, not an obstruction or depicted hazard demanding a response.
STEP 3 — MOTION: The ego vehicle is moving forward — buildings, curb line, and the balls steadily grow and shift across the frames, so the car is in motion, not stopped.
STEP 4 — ACTION: Since the lane ahead is clear and the balls lie at the right edge outside the travel line, a correct, safe driver simply maintains course and speed with normal awareness of the wet surface — nothing in the scene requires braking or a lane change.
</think>

Nothing in the drivable path requires a change — the lane ahead is clear, with the two small balls resting at the right curb edge outside the ego vehicle's travel line.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v12.mp4  (p2, gt continue; rejects: final_line_not_bare_option,parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path ahead is a wide, open multi‑lane roadway. The only objects physically in/near the ego lane are two small, light items — a red and a yellow balloon — lying flat on the asphalt near the dashed lane line; otherwise the lane is clear, with parked motorcycles on the right shoulder and a vehicle far ahead, but no pedestrian, barrier, or obstruction blocking travel.

STEP 2 — CONTROLS: The round "40" sign on the right is a genuine speed‑limit device, but it merely sets a ceiling and demands no immediate reaction; the glowing LED boards showing shop text are screen‑displayed depictions that command nothing; the balloons are real but trivial, light debris — not a traffic control and not a solid obstacle that impedes the vehicle.

STEP 3 — MOTION: The ego vehicle is moving forward; the balloons, the "40" sign, and the roadside shops steadily grow larger frame to frame, so the car is approaching the balloons at its current speed.

STEP 4 — ACTION: Since the balloons are small, flat, and light — the vehicle can cross them (or miss them by lane marking) with no risk of impact, instability, or damage — nothing in the scene requires braking or a course change, so a correct driver maintains speed and lane.
</think>

The only in‑path features are two small, light balloons lying on the road, which do not obstruct travel and command no reaction, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v07.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; trace_outcome:later; trace_outcome:anomal; )

```
<think>
STEP 1 — PATH: The ego lane ahead is open asphalt with no vehicles, pedestrians, barriers, or debris intersecting it in the next few seconds; the only specks of note are two tiny red and yellow dots far down the road that stay minuscule and do not close to collision scale, so nothing physical blocks the path.

STEP 2 — CONTROLS: The white "300" board on the right is a route/marker sign, not a speed limit or stop command; there are no traffic lights, stop signs, or signs of a stop; the red/yellow specks are not traffic devices (they behave as distant non-interactive artifacts, e.g., a reflection/far lights, and command nothing).

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the roadside 300 marker, trees, and lane dashes sweep past rapidly between frames.

STEP 4 — ACTION: With a clear lane, no real controls, and no imminent obstacle, a correct driver maintains course and speed; nothing in the scene requires braking, stopping, or waiting.
</think>

Nothing in the scene requires a change — the drivable lane is completely clear of real obstacles and there is no active traffic control, so the correct behavior is to keep going.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v10.mp4  (p2, gt continue; rejects: parsed=slow; no_step1_or_final; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path is a straight two-lane rural road that crests slightly ahead; the ego lane (right of the double yellow) is empty of vehicles, people, barriers, or obstacles for the next few seconds. A small red item and a small yellow item are visible far ahead near the lane boundary/oncoming side, well beyond any immediate conflict, and the "45" sign post stands on the right shoulder.

STEP 2 — CONTROLS: The rectangular "45" sign on the right is a real speed-limit device, but it only sets an upper limit and the current approach is already consistent with it, so it commands no change. The red and yellow blobs are small distant items (at most carried/depicted, not a control in the ego lane) and they do not occupy the ego lane, so they command nothing.

STEP 3 — MOTION: The ego vehicle is moving — the sign, edge lines, and roadside features steadily grow and approach across the frames.

STEP 4 — ACTION: A correct, safe driver maintains speed and lane position because the ego lane is clear and the only real control (the 45 sign) is already being satisfied.
</think>

The deciding feature is the completely clear, unobstructed right lane up to the crest, with a speed sign that matches the current pace and no hazard in the path, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_4_v16.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow,trace_outcome:later; )

```
<think>
STEP 1 — PATH: Two small balls (red and yellow) resting on the wet pavement ahead, positioned right at/just left of the dashed centerline, plus a low fog bank farther down the road; no vehicles, people, or other obstacles block the center of the ego lane.

STEP 2 — CONTROLS: The white "35" sign on the right shoulder is a real physical speed-limit sign, but it is consistent with the current pace and demands no change; the two balls are real objects on the road (not painted, displayed, or carried), yet they sit at the lane divider/left edge of the ego lane rather than across the lane's travel path.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the 35 sign and trees sweep past and the balls steadily enlarge across the frames.

STEP 4 — ACTION: A correct driver keeps current speed and lane, because the balls are small and located on the dashed line to the left of the vehicle's track, leaving the straight path through the lane clear with no need to brake or maneuver.
</think>

The deciding feature is that the red and yellow balls sit on the dashed centerline at the left edge of the ego lane, so the lane the vehicle is following remains unobstructed and nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v01.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The ego lane is a wet asphalt lane bounded by a narrow raised median on the left and dashed white lines / tram rails on the right. Over the next few seconds nothing physical sits in this lane — no vehicles, pedestrians, debris, or barriers; the parked cars are far off to the left across the opposite carriageway.

STEP 2 — CONTROLS: The bright white blob(s) ahead on the left/center of the view are flat mirror images of lit shop signs on the wet pavement — reflections, i.e., only a depiction, so they command nothing. The red lights visible far down the street are real traffic signals but are far beyond the next few seconds, so they impose no immediate requirement.

STEP 3 — MOTION: The ego vehicle is moving forward steadily — the median, lane dashes, and reflections grow and shift consistently across frames.

STEP 4 — ACTION: With a clear, unobstructed lane ahead and no real hazard or traffic control in effect, a correct driver maintains current speed and lane position.
</think>

The deciding feature is the clear, unobstructed drivable lane, since the white shapes are only reflections on the wet road surface and require no reaction.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v02.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path ahead is an open, multi-lane roadway with no vehicles, cyclists, or pedestrians in the near future; the only physical objects on the pavement are two small white plastic bags sitting low near the dashed lane line ahead.
STEP 2 — CONTROLS: There are no traffic lights, signs, stop lines, or other traffic controls in view. The white bags are real physical objects, not painted or printed depictions, but they are small, light debris rather than any barrier or obstruction; the dashed lane lines and distant turn arrow are mere markings, not commands.
STEP 3 — MOTION: The ego vehicle is moving forward — the bags and roadside trees steadily grow larger and closer across the frames.
STEP 4 — ACTION: With a clear path and no genuine traffic control or obstruction (the two small bags are trivial road debris that do not block or impede travel), a correct, safe driver maintains current speed and lane.
</think>

Nothing in the scene requires a change — the two small white plastic bags are minor debris that do not obstruct the lane.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v03.mp4  (template, gt continue; rejects: parsed=slow,trace_outcome:later; parsed=stop; parsed=slow; trace_outcome:later; trace_outcome:later; trace_outcome:later)

```
<think>
STEP 1 — PATH: Light polythene bags blow across the road surface near the lane; otherwise the path is clear.
STEP 2 — CONTROLS: No traffic control is present; the bags are real objects but harmless soft debris, not a hazard.
STEP 3 — MOTION: The ego vehicle is moving.
STEP 4 — ACTION: Blowing plastic bags pose no hazard and require no change; maintain speed and lane.
</think>

The only objects near the lane are harmless plastic bags; nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v05.mp4  (p2, gt continue; rejects: parsed=slow; parsed=stop; parsed=slow; )

```
<think>
STEP 1 — PATH: The asphalt lane ahead is open. Three white sack-like objects sit along the left edge of the carriageway by the sea wall; as the vehicle advances they grow larger and drift to the left side of the frame, showing the vehicle's own trajectory passes to their right. No vehicles, pedestrians, or barriers are in the travel path.
STEP 2 — CONTROLS: No signs, signals, stop lines, or lane markings requiring any action are visible; the only notable items are the white sacks, which are physical but positioned outside the vehicle's line of travel (and their flat sheen is consistent with sky reflection on the damp road, which in any case commands nothing).
STEP 3 — MOTION: The ego vehicle is moving forward — the wall posts, lamp posts, and lane dashes steadily translate toward the camera and the sacks increase in size frame by frame.
STEP 4 — ACTION: A correct, safe driver maintains current speed and lane, because the path directly ahead remains unobstructed and the sacks stay clear on the left as the vehicle passes them.
</think>

The deciding feature is the empty lane directly ahead — the white sacks hug the left wall and are swept out of the path on the left, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v04.mp4  (p2, gt continue; rejects: parsed=stop; no_step1_or_final; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path is an empty, fog-veiled asphalt road. Two low white sacks sit on the pavement ahead, one left and one right of the vehicle's line of travel, with a clear open gap between them; no people, vehicles, or barriers block the lane.

STEP 2 — CONTROLS: No signs, signals, or painted markings command any action. The white sacks are real physical objects (not printed or painted depictions), but they are low, soft, stationary markers flanking the path rather than a barrier across it, and no other hazard is present.

STEP 3 — MOTION: The ego vehicle is moving slowly forward — the sacks steadily enlarge and spread apart across the frames, indicating a slow, steady approach.

STEP 4 — ACTION: Since the gap between the sacks is aligned with the vehicle's lane and the approach is slow, a correct, safe driver maintains course and speed; nothing in the scene requires braking, stopping, or waiting.
</think>

The only features ahead are two low, stationary sacks flanking an open gap in the lane, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v15.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable surface inside the tunnel is empty asphalt with real lane markings (dashed line, solid edge line, hatched gore on the left) and concrete walls. The only things that look like obstructions are two pale, bag-shaped forms on the roadway, but they appear as flat, uniformly lit cut-outs with no true ground shadow or texture parallax — i.e., screen-displayed overlay images, not physical objects in the lane.
STEP 2 — CONTROLS: No signals, signs, stop lines, or other traffic controls are present in the tunnel. The white bag shapes are depictions (displayed images), not real hazards, so they command nothing; the painted lines are only lane guidance.
STEP 3 — MOTION: The ego vehicle is moving forward at steady speed — the portal, wall joints, and lane dashes consistently recede/approach across frames.
STEP 4 — ACTION: With a physically clear lane and no genuine hazard or control ahead, a correct driver maintains speed and lane position.
</think>

The deciding feature is the physically empty tunnel lane, since the apparent white-bag "obstacles" are only flat displayed images that command nothing.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v09.mp4  (p2, gt continue; rejects: parsed=slow; parsed=stop; parsed=slow; )

```
<think>
STEP 1 — PATH: The ego lane ahead is open wet asphalt; the only physical items in or near it are two low, lightweight white plastic bags (trash) resting on the pavement, and a dark car stopped far ahead near the right curb. No pedestrians, barriers, or other vehicles are in the near path.

STEP 2 — CONTROLS: No traffic lights, signs, stop lines, or yield markings are visible anywhere in the clip. The white bags are real physical objects, but they are harmless road debris — not a traffic control, not printed or reflected, and not an obstruction that blocks the lane or commands any maneuver.

STEP 3 — MOTION: The ego vehicle is moving forward — the lane dashes, building facades, and awnings shift toward the camera across frames, and the roadside details grow larger.

STEP 4 — ACTION: Because the lane is clear of any blocking obstacle and the only items ahead are light, non-obstructive litter that a vehicle can pass over without risk, a correct, safe driver maintains current speed and lane; nothing requires braking or a lane change.
</think>

With no traffic controls present and no blocking obstruction in the open lane — only harmless lightweight debris — nothing requires a change in the drive.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v12.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The road ahead is a straight, multi-lane city street. In the near distance, two white sandbags sit on the textured central strip, one to the left and one to the right of the vehicle's line of travel; the lane surface directly ahead between them is empty, and the only other vehicles are far down the road.

STEP 2 — CONTROLS: The neon signs, LED canopies, and billboards are commercial displays and command nothing. No traffic light, stop sign, or painted command governing the ego lane is visible in the near field. The sandbags are real physical objects, but they are placed at the sides/edges of the travel path, not blocking it.

STEP 3 — MOTION: The ego vehicle is moving forward — the sandbags, canopy, and lane markings grow steadily larger and lower in the frame across the clip.

STEP 4 — ACTION: A correct, safe driver should maintain speed and lane, because the travel path between the two off-line sandbags is clear and no genuine traffic control or obstacle requires slowing, stopping, or waiting.
</think>

The two white sandbags sit at the left and right edges of the lane and leave the straight-ahead travel path unobstructed, so nothing in the scene requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v02.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A small child in a red shirt walks from the right sidewalk/curb directly onto the asphalt and is now standing/walking in the roadway ahead, within the ego vehicle's drivable lane; parked cars sit off-road in driveways and a white car is far down the road, but the child is the only object physically in the path.

STEP 2 — CONTROLS: A real "SCHOOL 20 MPH" speed sign stands on the right (a genuine physical sign, reinforcing caution), and a real red fire hydrant sits at the curb; neither is a depiction. The child is a real person, not a printed or carried image, so it is a genuine hazard.

STEP 3 — MOTION: The ego vehicle is moving forward — the mailbox, sign, and child steadily grow larger and closer across the frames.

STEP 4 — ACTION: Because a small child is now in the street directly ahead in the vehicle's path, an unpredictable pedestrian, a correct safe driver must brake to a complete stop and yield until the child is safely clear.
</think>

The real feature deciding this is the young child in the red shirt who has stepped from the curb into the roadway directly in front of the vehicle, requiring the driver to stop for the child's safety.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v14.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; final_line_not_bare_option; )

```
<think>
STEP 1 — PATH: The ego lane ahead is a wet, straight asphalt lane with no vehicles, pedestrians, or barriers; the only items in or near the path are two small, flat white plastic bags lying on the road surface, which are light, low-profile debris rather than solid obstacles.

STEP 2 — CONTROLS: The roadside items are commercial store signs (OBI, carful, etc.) and lane markings — none of which are traffic controls or valid commands. There are no traffic lights, stop signs, stop lines, or signals in the path; the bags are physical but trivial light objects, not a hazard requiring intervention.

STEP 3 — MOTION: The ego vehicle is moving forward — the dashed lane lines and roadside features shift backward between frames while the scene recedes steadily.

STEP 4 — ACTION: Maintain current speed and lane, because the lane ahead is clear of any real obstruction or traffic control, and the light plastic bags present no collision risk that commands braking or stopping.
</think>

Nothing in the scene requires a change — the lane is clear and the only objects are light plastic bags that do not impede passage — Continue
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v13.mp4  (p2, gt continue; rejects: parsed=slow; parsed=stop; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path ahead is a clear, straight residential lane. The only items in it are two small, light white plastic bags lying flat on the pavement a few meters ahead and a vehicle far down the road; there are no pedestrians, cyclists, oncoming cars, or obstructions that block or narrow the lane.

STEP 2 — CONTROLS: There are no traffic lights, signs, stop lines, or other traffic control devices in view. The dashed white centerline is only painted lane delineation, and the white bags, while physical, are small light debris that do not obstruct travel and command no speed change.

STEP 3 — MOTION: The ego vehicle is moving forward — road markings, trees, and houses recede steadily, and the bags grow larger frame by frame as the vehicle approaches.

STEP 4 — ACTION: Since the lane is open, traffic is absent or far away, and nothing in the path obstructs or controls the vehicle, a correct, safe driver maintains current speed and lane.
</think>

Nothing in the scene requires a change — the lane ahead is unobstructed and free of any active traffic control, with only trivial light debris that does not compel slowing, stopping, or waiting.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v06.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The paved lane ahead is physically clear of vehicles and debris, but a small child in a red jacket is standing in the snow on the right verge only a couple of metres from the travel lane, growing rapidly larger in the frame, and in the last frames the child is oriented toward the road with a step/arm motion that reads as moving onto the roadway.

STEP 2 — CONTROLS: The round red-bordered "30" sign on the right is a real, mounted speed-limit sign (a genuine device, though it only caps speed and does not itself force a stop). The child is a real person on the road verge, not a printed, painted, worn, or carried image, so the hazard is real and commanding.

STEP 3 — MOTION: The ego vehicle is moving forward — the houses, parked cars, sign pole, and center snow strip steadily approach and grow across the frames.

STEP 4 — ACTION: Because a small, unpredictable child is at the very edge of the traveled lane and appears to be stepping toward it, a correct, safe driver must brake to a complete stop and hold position until the child is unambiguously clear of the roadway, rather than continuing at speed or merely easing off.
</think>

The decisive feature is the real child in the red coat standing at the right edge of the road, about to enter the vehicle's path, which demands a full stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v08.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow,trace_outcome:later; )

```
<think>
STEP 1 — PATH: The paved lane directly ahead is clear of vehicles and debris for the next few seconds, but on the right shoulder a small child in a red outfit is at the very edge of the pavement, walking/running toward and along the travel lane, getting progressively closer to the ego vehicle's path as it approaches.

STEP 2 — CONTROLS: The red octagonal sign and white rectangular sign visible far down the road are real physical traffic devices, but they sit at a distant intersection beyond the immediate window and do not govern the next few seconds. The child in red is a real person (a pedestrian hazard), not a printed, painted, or carried depiction, so it commands real caution.

STEP 3 — MOTION: The ego vehicle is moving forward — the roadside walls, houses, and the child all steadily grow larger and closer across the frames.

STEP 4 — ACTION: Because a small, unpredictable child is right at the road edge and can step into the lane at any moment, a correct safe driver must brake to a complete stop until the child's intent is clear and the child is safely passed.
</think>

The deciding feature is the small child in red at the road edge who may enter the travel path at any instant.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_5_v16.mp4  (p2, gt continue; rejects: parsed=stop; parsed=stop; parsed=stop; no_step1_or_final; )

```
<think>
STEP 1 — PATH: The paved lane ahead is empty — only lane markings and the low ground fog. The three white sacks that appear "on the road" sit above the hood line and remain centered in the vehicle's frame, i.e., they are cargo carried inside the cabin (resting at the dashboard/windshield), not objects lying on the pavement.
STEP 2 — CONTROLS: There are no real traffic controls in view; the only apparent hazard (the white sacks) is carried cargo/interior equipment, so it commands nothing. The mist is a real environmental condition but does not block the lane within the next few seconds.
STEP 3 — MOTION: The ego vehicle is moving forward — the dashed lane line, road edges, and trees steadily shift outward and past the camera.
STEP 4 — ACTION: Since the actual drivable path contains no physical obstruction, a correct driver keeps the current lane and speed, driving normally through the fog.
</think>

The lane ahead is physically clear because the white sacks are cargo carried in the vehicle rather than road obstacles, so nothing requires a change.
Continue
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v12.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The road ahead is otherwise clear of moving traffic, but a small pedestrian in a red shirt has stepped off the right-hand curb from behind the row of parked scooters and is now walking out into the right side of the roadway, i.e., into the lane the ego vehicle is using, a short distance ahead.

STEP 2 — CONTROLS: The round "40" sign on the right is a real speed-limit sign (it sets a limit, not an immediate stop); the shop banners, "400" red sign, and red LED shop display are printed/displayed depictions that command nothing. The only real hazard acting now is the pedestrian in the red shirt who is physically in the roadway.

STEP 3 — MOTION: The ego vehicle is moving forward — the storefronts, the 40 sign, and the parked scooter row on the right are steadily approaching and sliding past.

STEP 4 — ACTION: A child-sized pedestrian has just left the sidewalk and is crossing into the ego vehicle's lane ahead among the parked scooters; a correct, safe driver must brake to a complete stop to yield to this vulnerable road user before proceeding.
</think>

The deciding feature is the pedestrian in the red shirt who has stepped off the curb into the open roadway directly ahead at the end of the parked-scooter row, requiring the ego vehicle to halt.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v20.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The lane ahead continues straight but is narrowed on the right by a line of orange cones set along the curb, and a small child in a red top is walking right at that curb edge, directly beside our lane, closing distance to the ego vehicle and oriented toward the carriageway — i.e., a person physically at the boundary of the drivable path within the next few seconds.

STEP 2 — CONTROLS: The white "25" sign is a real speed-limit sign (governs speed, not a stop command); the red/yellow barrier panels are real works equipment but sit off the drivable path; the faded "BUS"/cycle symbols and road text are only painted markings; the distant red octagon is a real sign but far ahead at the junction, not within the next few seconds. The child, however, is a real person, not a depiction.

STEP 3 — MOTION: The ego vehicle is currently moving forward (cones, curb, and child all pass/grow across frames).

STEP 4 — ACTION: A real child of that size walking unpredictably at the edge of our lane, close enough to step into it at any moment, requires the vehicle to halt so it can yield instantly — not merely slow.
</think>

The deciding feature is the small child in the red shirt walking at the curb edge of the ego vehicle's lane, who may step into the path at any moment, so the vehicle must come to a complete stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v01.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=slow; )

```
<think>
STEP 1 — PATH: The wet, marked lane ahead terminates at a large physical screen/wall (a mural-covered panel) that spans the full width of the roadway; at its base on the right sit blue bins and the sidewalk, leaving no gap wide enough for the car to pass.

STEP 2 — CONTROLS: The sunlit highway, sky, and dashed centerline visible on the panel are only a painted/displayed image and command nothing; the small right-side sign is a real device but merely flags a side street. The deciding feature is not a depiction but the real, solid barrier itself, which is a physical obstruction in the path.

STEP 3 — MOTION: The ego vehicle is moving forward — the right-side sign, streetlight, and building windows stream past and the panel grows steadily larger frame by frame.

STEP 4 — ACTION: Because the drivable surface physically ends at the solid panel ahead, a correct safe driver must brake to a complete stop before reaching it, not follow the depicted road painted on it.
</think>

The solid mural-covered wall that ends the street is the real feature that blocks the lane, so the only safe action is to halt before it.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v02.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The asphalt residential street runs straight ahead and physically terminates at a large arch-shaped screen/mural structure standing across the roadway; beyond its base there is no continuation of the drivable surface, no through lane, and no visible cross-street opening. Trash cans sit at the curb edges and parked cars sit in driveways, none in the travel lane.

STEP 2 — CONTROLS: The bright sunburst and the two-lane "highway" in the center of the scene are a painted image on that screen — a depiction only, which commands nothing. The "DRUG FREE CROWD" placard and the small green street-name sign are decorative/informational, not regulatory devices. No real stop sign, signal, or hazard is present in the path.

STEP 3 — MOTION: The ego vehicle is moving forward; the roadside sign, bins, and houses steadily grow larger and pass by between frames.

STEP 4 — ACTION: Because the real drivable surface ends at the solid screen/wall structure blocking the street (the painted highway is only an illusion), a safe driver must brake and come to a complete stop before reaching it rather than continuing toward the barrier.
</think>

The physical end of the road — the large screen structure that walls off the street and ends the asphalt — requires the driver to halt, so the correct action is to stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_8_v18.mp4  (p2, gt stop; rejects: parsed=continue; parsed=slow; parsed=slow; trace_outcome:later; )

```
<think>
STEP 1 — PATH: A person wearing a bright red jacket is standing on the wet roadway at the right edge of our travel lane (just inside the curb), a short distance ahead; there are no moving vehicles in our lane, only parked cars along the left curb.
STEP 2 — CONTROLS: The "30" speed limit sign on the lamp post is a real regulatory sign but only sets a limit; the small red sign near the bridge faces cross/side traffic, not us; the red-clad figure is a real physical pedestrian occupying the road, not a painted, printed, or displayed image, so it is a genuine hazard.
STEP 3 — MOTION: The ego vehicle is moving forward — the lamp post, railing posts, and the pedestrian all approach and grow across the frames.
STEP 4 — ACTION: Since a real pedestrian is occupying the lane we are traveling in and their intent is unknown on a wet surface, a correct, safe driver must brake to a complete stop before reaching them rather than continue past.
</think>

The deciding feature is the pedestrian in red standing in the right travel lane directly ahead in our path, which requires a full stop before reaching them.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v03.mp4  (p2, gt stop; rejects: trace_outcome:later; parsed=slow; no_step1_or_final; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The lane is clear of vehicles and pedestrians, but the asphalt physically ends at the base of the large free‑standing arched structure that spans the full width of the street; there is no visible road, intersection, or opening beyond it, so the drivable path is physically terminated within the next few seconds.

STEP 2 — CONTROLS: The radiant sunburst, the "highway" with yellow dashed center line, and the sun are only a painted image on that panel and command nothing. The sign on the right (pictogram plate) and the small directional arrow sign on the left are real but do not govern the straight‑ahead path — the left one points into the side street and the right one has already passed the vehicle's position. No real stop sign or traffic light controls this stretch.

STEP 3 — MOTION: The ego vehicle is moving forward; the arched structure grows noticeably larger in each successive frame as the vehicle closes the distance to it.

STEP 4 — ACTION: Because the only thing physically in the path is the full‑width structure that ends the street, a correct, safe driver must brake to a complete stop before its base rather than proceed into it; nothing requires continuing, slowing, or waiting while already stopped.
</think>

The full‑width arched mural structure that physically blocks and terminates the drivable lane (its sunset highway being only a painted image) is what decides the action.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v05.mp4  (p2, gt stop; rejects: parsed=slow; parsed=continue; parsed=slow; )

```
<think>
STEP 1 — PATH: The wet, two-lane asphalt road leads directly into a T-intersection; straight ahead the roadway physically terminates at a building wall (carrying the large painted mural), while the cross street runs right (with parked cars) and left. No pedestrians or moving vehicles are in the immediate path, but the surface ends at the wall/corner within the next few seconds.

STEP 2 — CONTROLS: The "highway" with the yellow centerline, sun, and clouds is only a painted mural on the wall — a depiction that commands nothing. The real items are the wet pavement, the street-name sign on the right, the one-way/directional sign on the left, and the physical wall/corner that ends the road; the mural's road markings have no authority and the road does not actually continue straight.

STEP 3 — MOTION: The ego vehicle is moving forward (slowly), as its position relative to the dashed line, the right-hand sign, and the parked cars advances across the frames.

STEP 4 — ACTION: A correct driver must brake to a complete stop before the wall/intersection, because straight travel is physically blocked by the corner wall and a turn (right or left) can only be made safely after stopping and checking the cross street; the painted road ahead is an illusion and must not be followed.
</think>

The decisive real feature is the wall at the T-intersection that physically ends the drivable path (the highway "ahead" is only a painting), so the vehicle must come to a full stop before turning.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v14.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=slow; )

```
<think>
STEP 1 — PATH: The ego vehicle is on a wet paved alley between two gray warehouse buildings. The alley terminates within a few seconds in the solid side wall of the building straight ahead — the same wall carrying the landscape mural. Parked box trucks/trailers sit on the left apron, but nothing blocks the center except the end wall itself; no actual roadway, gate, or opening continues through it.

STEP 2 — CONTROLS: The bright highway with a yellow centerline, the sunburst, clouds, and green hills are a mural painted on the building wall — a pure depiction that commands nothing. The small white placard on the right ("NO LOADING" type) is a real sign but only governs loading/parking, not the driving path. There is no real stop sign, signal, or hazard in the lane.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the mural wall grows larger in each frame and the distance to it steadily closes.

STEP 4 — ACTION: Because the physically drivable surface ends at a solid wall, a correct and safe driver must brake to a complete stop before the wall; the convincing painted road is only an illusion and offers no through route.
</think>

The solid, mural-covered building wall that physically closes off the alley is the deciding feature, requiring a full stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v15.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The real asphalt roadway runs straight down the center of the underpass and physically terminates a few meters ahead at a solid concrete wall (the tunnel end); there is no actual road, opening, or through-passage beyond it — the "road" with lane lines, grass, and a shining sun seen ahead is flat against that wall.
STEP 2 — CONTROLS: The sun, sky, clouds, and continuing highway at the tunnel exit are only a painted mural (a depiction) and command nothing; the stenciled markings on the side wall are painted text, and the small white sign panels on the right are real but contain no control requiring a change. The deciding real hazard is the solid wall itself, a physical barrier.
STEP 3 — MOTION: The ego vehicle is moving forward; the mural and wall grow steadily larger across the frames, showing continuous approach.
STEP 4 — ACTION: A correct, safe driver must brake to a complete stop short of the wall, because the drivable path ends at a solid barrier and the apparent open road ahead is only an image on the wall.
</think>

The solid concrete tunnel-end wall, where the real pavement stops and the "open road" is only a mural, is the feature that demands bringing the vehicle to a halt before reaching it.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v10.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; no_step1_or_final; )

```
<think>
STEP 1 — PATH: The dark, headlight-illuminated asphalt lane the ego vehicle is on runs straight and terminates within the next few seconds at the base of a large physical billboard/screen structure that blocks the road; a side road branches off to the left at that point. The bright two-lane highway with dashed markings seen "ahead" exists only inside the billboard's picture.

STEP 2 — CONTROLS: The sunny road, lane markings, and horizon inside the billboard are a displayed image (a screen), so they command nothing. The white "MOTION" sign and the small yellow sign at the left junction are real signs but impose no movement by themselves; the deciding real feature is the solid billboard structure physically occupying the end of the drivable path.

STEP 3 — MOTION: The ego vehicle is moving forward — the billboard and roadside houses grow steadily larger and closer across the frames.

STEP 4 — ACTION: Since the real lane ends at the physical billboard wall and the apparent continuation is merely an image, a correct safe driver must brake to a complete stop before reaching it rather than ploughing into the structure.
</think>

The real road physically ends at the large billboard/screen structure spanning the lane (the "highway" beyond it is only a displayed image), so the driver must bring the vehicle to a complete stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v07.mp4  (p2, gt stop; rejects: parsed=continue; no_step1_or_final; no_step1_or_final; )

```
<think>
STEP 1 — PATH: The real drivable surface is a two-lane street with a dashed double-yellow centerline that runs straight to a T-intersection (crosswalk and side street visible on the right). Beyond that point there is no pavement — the apparent "open highway" is a mural painted on the building wall, i.e., a physical barrier at the end of the street. No vehicles, pedestrians, or debris occupy the lane itself.

STEP 2 — CONTROLS: The long straight road, white edge lines, dashed centerline, guardrails, and sky visible ahead are all part of the painted mural — a depiction on a wall, so they command nothing. The real controls are the physical end of the street: the wall/building and the intersecting side road with its crosswalk, which the ego vehicle is about to reach.

STEP 3 — MOTION: The ego vehicle is moving forward — the mural and roadside signs grow larger and the crosswalk becomes clearly visible across the frames.

STEP 4 — ACTION: A correct, safe driver must brake to a complete stop at the end of the street, because the lane physically terminates at the intersection in front of the mural wall; the "road continuing straight" is only paint, so proceeding as if it were a real roadway would drive the car into a building.
</think>

The deciding feature is the real physical end of the street — the building wall bearing the painted "road" mural at the T-intersection — which requires a full stop.
Stop
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v11.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; no_step1_or_final; )

```
<think>
STEP 1 — PATH: The ego lane's asphalt runs straight into a dead end: a large physical freestanding billboard/wall blocks the roadway a short distance ahead, with a raised concrete median island and a sign post standing just before it. The only open movements are the side street to the left and the curving lane to the right; straight ahead there is no drivable surface beyond the wall.

STEP 2 — CONTROLS: The "continuing" highway, green fields, clouds, and the small sign on the painted road inside the mural are all a flat picture and command nothing. Real, physical features: the wall that ends the roadway (a dead end), the actual sign standing on the real median marking the road as a no‑exit, and the genuine pavement markings (double yellow, white edge line) defining the ego lane.

STEP 3 — MOTION: The ego vehicle is moving forward — the mural, median sign, and roadside buildings grow and shift across the frames.

STEP 4 — ACTION: Because the straight‑ahead path physically terminates at the wall, a correct, safe driver must brake to a complete stop before reaching the dead end instead of proceeding into the barrier.
</think>

The real, physical termination of the roadway — the freestanding billboard wall (dead end) directly across the ego lane — dictates that the vehicle come to a full halt.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered/prompt_11.mp4  (p2, gt stop; rejects: parsed=wait,trace_outcome:vehicle is already halt; parsed=wait,trace_outcome:vehicle is already halt; parsed=wait; )

```
<think>
STEP 1 — PATH: The drivable path is a clear, empty multi-lane roadway leading into a wide intersection; the signal pole (with the bunch of balloons tied to it) sits on a small paved island at the right edge of the approach, beside the lane rather than across it, and there are no vehicles, pedestrians, or debris in the lane ahead.

STEP 2 — CONTROLS: The vertical traffic signal mounted on the pole is a real, installed traffic-control device, and it is displaying a steady red — that is the controlling, valid signal for this approach. The red, blue, green, and orange balloons and ribbons tied to the pole are mere decoration/cargo and command nothing; faint distant signals down the road do not override the near red head.

STEP 3 — MOTION: The ego vehicle is still in its approach to the stop line and has not yet executed/confirmed a complete halt, so the stop action still has to be performed now.

STEP 4 — ACTION: Because the real traffic signal governing this approach is showing red, a correct, safe driver must brake to a complete stop before the stop line and hold, rather than continuing through the intersection.
</think>

The live red indication of the real traffic signal at the intersection is the feature that decides it, requiring a full stop before the line.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered/prompt_6.mp4  (p2, gt slow; rejects: parsed=continue; final_line_not_bare_option,parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a straight, unlit two-lane rural road; the ego lane ahead is clear, but in the opposite lane an oncoming vehicle with very bright headlights is closing rapidly (it grows from a point of light to a clearly visible car, with a second set of headlights/marker lights behind it by the last frames).

STEP 2 — CONTROLS: No traffic signs, signals, or road hazards are present. The only real hazard is the physical oncoming vehicle(s) and their intense headlight glare on the dark road; the faint lights on the horizon are distant town lights and command nothing.

STEP 3 — MOTION: The ego vehicle is moving forward — the lane lines, shoulders, and road texture shift between frames, and the oncoming car's apparent size increases steadily.

STEP 4 — ACTION: With a close oncoming vehicle flooding the dark windshield with glare on an unlit rural road, a correct, safe driver should ease off the throttle and reduce speed slightly while staying centered in the lane, then resume speed after the pass.
</think>

The rapidly approaching oncoming vehicle's bright headlights and the dark, unlit two-lane road require a precautionary speed reduction during the pass.
Slow
```

### final_semantic_scenarios/negative_scenarios/negative_scenarios_variants/prompt_9_v17.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The ego lane (marked by double yellow lines) runs a short distance to an intersection; across that cross street is the solid gable end of a building, so there is no physical roadway continuing straight — the drivable path terminates at this T‑junction. The intersection itself is clear of vehicles and pedestrians.

STEP 2 — CONTROLS: The "open highway under a blue sky with clouds" straight ahead is a mural painted on the building wall — a depiction only, which commands nothing. Real devices present: the one‑way arrow sign on the left (cross street flows right), the white "NO OUT"‑type sign on the right (regulatory sign for the side street, not a stop command), and a yellow diamond warning sign on the left. None of the real signs allows simply continuing straight, because the real road ends at the junction.

STEP 3 — MOTION: The ego vehicle is moving forward, closing the distance to the intersection frame by frame.

STEP 4 — ACTION: Because the actual roadway terminates at the T‑intersection (the apparent straight road is only paint on a wall), a correct, safe driver must brake to a complete stop before entering the intersection rather than proceeding as if the road continued.
</think>

The deciding feature is the real T‑intersection where the street ends in front of the mural‑painted building — the straight "road" is only a painting, so the driver must halt before the junction.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered/prompt_5.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: Three small, light white plastic bags lie on the asphalt within the ego lane; the lane is wide and otherwise clear, with no vehicles, pedestrians, or barriers in the immediate path, and the vehicle's trajectory threads to the right of the left bags and to the left of the right bag, so the bags pass alongside without blocking the path.

STEP 2 — CONTROLS: The overhead traffic-light gantry far down the road is a real device but is too distant to command any action in the next few seconds; the white bags are real physical objects but trivial, lightweight debris rather than any traffic control or serious hazard; no printed, painted, or displayed hazards are present.

STEP 3 — MOTION: The ego vehicle is moving forward — the bags successively approach and exit past the bottom of the frame, and the roadside perspective steadily shifts.

STEP 4 — ACTION: A correct driver should maintain current speed and lane, because the lane is clear and the light plastic bags are passed on either side without collision, so nothing real requires slowing or stopping.
</think>

The only features in the path are light plastic bags that the vehicle's lane already clears on both sides, so nothing requires a change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_filtered/prompt_8.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow,trace_outcome:later; parsed=slow; )

```
<think>
STEP 1 — PATH: A small child in a red jacket with a backpack is at the right curb, moving from the grass/sidewalk up onto the asphalt edge of the ego vehicle's lane; parked cars line both sides of the street but leave the center clear.
STEP 2 — CONTROLS: The "STOP" lettering on the pavement ahead is a painted marking (a depiction that commands nothing here, and the ego is far from any intersection line); the child's bright backpack is carried cargo; the child themselves is a real, live person at the lane edge — a genuine hazard, not a depiction. No signs or signals govern the ego vehicle at this moment.
STEP 3 — MOTION: The ego vehicle is moving forward at low speed; the child and surroundings grow larger frame by frame.
STEP 4 — ACTION: A correct, safe driver must brake to a complete stop because the child is stepping off the curb into the roadway directly in the ego's path and, being a small child, may move unpredictably into the lane.
</think>

The child in the red jacket stepping from the curb into the lane directly ahead is the deciding feature, requiring a full stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v02.mp4  (p2, gt stop; rejects: parsed=wait,trace_outcome:vehicle is stopp; parsed=wait,trace_outcome:vehicle is already halt; parsed=wait; )

```
<think>
STEP 1 — PATH: The lane ahead is a clear, empty approach to an intersection; no vehicles, pedestrians, cyclists, or physical obstacles are in or across the drivable path in the next few seconds — only dry asphalt and lane markings, with a stop bar at the bottom of the view.

STEP 2 — CONTROLS: (a) The traffic signal head on the pole at the near corner shows a solid red lamp — this is a real, functioning traffic-control device mounted on the corner pole, and it is corroborated by the matching red light on the far mast-arm signal; it commands a stop. (b) The cluster of green, blue, red, and white balloons with ribbons tied to that same pole is carried cargo/decoration — it is a depiction, not a traffic control, and commands nothing. (c) The distant mast-arm signal also displays red — real and consistent.

STEP 3 — MOTION: The ego vehicle is right at the stop bar, still rolling/creeping in as it arrives at the line — it has not yet completed a confirmed full stop and must not enter the intersection.

STEP 4 — ACTION: Because the real traffic signal is solid red, a correct driver must brake to a complete stop behind the stop line and hold; the balloons on the pole are irrelevant decoration and do not affect the decision.
</think>

The deciding feature is the illuminated solid red traffic signal at the intersection (near-side head and matching far-side signal), which requires the vehicle to come to a halt.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v04.mp4  (p2, gt stop; rejects: parsed=wait; parsed=wait,trace_outcome:vehicle is already stopp; trace_outcome:vehicle is slow; )

```
<think>
STEP 1 — PATH: The drivable path ahead is an empty, wide intersection with a marked crosswalk and stop line directly in front of the vehicle; no other vehicles, pedestrians, or obstacles occupy the lane.
STEP 2 — CONTROLS: The vertical traffic signal on the corner pole shows a steady, glowing red at the top lamp — this is a real, functioning signal device, not a depiction. The colorful balloons and ribbons tied to the pole are decorations/memorial items only and command nothing.
STEP 3 — MOTION: The ego vehicle is still rolling slowly forward — the signal head, balloons, and crosswalk grow slightly larger/closer across the frames — so it has not yet come to a complete stop at the line.
STEP 4 — ACTION: Because a real red signal is displayed for this approach, a correct driver must brake to a complete stop before the crosswalk/stop line rather than continue rolling.
</think>

The illuminated red traffic light at the intersection corner is the deciding feature, requiring the approaching vehicle to halt at the stop line.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v03.mp4  (p2, gt stop; rejects: parsed=wait,trace_outcome:vehicle is already stopp; trace_outcome:vehicle is slow; parsed=wait; )

```
<think>
STEP 1 — PATH: The lane ahead is clear: an empty two-way street lined with blossoming trees, a side street crossing to the right, and a white stop bar on the pavement directly in front of the vehicle. No pedestrians, vehicles, or physical obstacles are in the drivable path.

STEP 2 — CONTROLS: The traffic light mounted on the yellow pole at the right is a real, functional signal, and its top lamp is illuminated red, which commands a stop. The cluster of colorful balloons and ribbons tied to the same pole is merely decoration/cargo and commands nothing. No other real hazards are present.

STEP 3 — MOTION: The ego vehicle is positioned at the stop bar with the red signal showing; across the frames it shows no forward progress, i.e., it is at (or just arriving at) the point of a complete stop at the line.

STEP 4 — ACTION: A correct, safe driver must brake to a full stop at the stop bar and hold that position, because the real traffic signal ahead is displaying red.
</think>

The illuminated red lamp on the real traffic signal is the deciding feature, requiring the vehicle to be brought to (and held at) a complete stop at the stop bar.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v12.mp4  (p2, gt stop; rejects: parsed=wait; parsed=wait,outcome:vehicle is already stopp,trace_outcome:car is already stopp; parsed=wait,trace_outcome:vehicle is already stopp; )

```
<think>
STEP 1 — PATH: The drivable path ahead is clear: an empty multi-lane asphalt roadway with lane markings, guardrails, and a grass median; no vehicles, pedestrians, or obstacles lie in or across the path in the next few seconds. The bunch of balloons is tied to the pole on the right shoulder and sits outside the roadway.

STEP 2 — CONTROLS: The traffic light mounted on the pole at the right edge of the road is a real, physical signal device, and its top (red) aspect is clearly illuminated while the amber and green aspects are dark. The balloons tied to the pole are only a decoration and command nothing. Distant red dots on the horizon are far-away signals/vehicles, not the controlling device for this approach.

STEP 3 — MOTION: The ego vehicle has not yet come to a complete halt at the stop line — it is still rolling in slowly toward the line, so a braking action to a full stop is still required.

STEP 4 — ACTION: Because a real traffic light governing the approach is showing red, a correct, safe driver must brake to a complete stop before the stop line and hold there until the signal changes.
</think>

The illuminated red aspect of the real roadside traffic light is the deciding feature, requiring the vehicle to bring itself to a full stop before the line.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_11_v20.mp4  (p2, gt stop; rejects: parsed=wait,trace_outcome:vehicle is already stopp; parsed=wait; parsed=wait,trace_outcome:vehicle is already halt; )

```
<think>
STEP 1 — PATH: The drivable path ahead is a clear, wide roadway descending into an underpass; there are no vehicles, pedestrians, or obstructions in the lane. The bunch of balloons sits on the paved median island to the right, beside the signal pole, and is not in the driving path.

STEP 2 — CONTROLS: The traffic light mounted on the metal pole is a real, functioning device — its top lamp is clearly illuminated red (a second, lower unit on the same pole also glows red). The colorful balloons tied to the pole are real objects but are only decoration; they are not a traffic control and command nothing. The lane lines and stop-line markings are painted and merely define the roadway.

STEP 3 — MOTION: The ego vehicle is at the approach, at best creeping/holding at the line and not yet committed to a full stop for the signal.

STEP 4 — ACTION: Since the real traffic signal is red, a correct driver must brake to a complete stop at the stop line and remain there; the empty road ahead does not permit proceeding through a red light.
</think>

The illuminated red lamp of the genuine traffic signal at the intersection is the feature that decides it, requiring a complete stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_4_v05.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path is a wet, two-lane rural road curving gently to the left through fog; the only objects on it are a few small, lightweight balloons (cyan, pink, light blue) sitting low on the asphalt in the ego lane and along the right edge, with no vehicles, pedestrians, or barriers present.
STEP 2 — CONTROLS: The visible road markings (dashed center line, solid edge line) and roadside delineator posts are real but standard and give no new instruction; the balloons are physical objects but not traffic controls and, being light and low, do not constitute a hazard that commands braking or stopping.
STEP 3 — MOTION: The ego vehicle is moving forward — the trees, posts, and lane markings stream past and the balloons approach and then pass the hood.
STEP 4 — ACTION: A correct driver maintains current speed and lane, since the balloons are trivial light objects that cannot impede the vehicle and the road ahead is clear within the fog's visibility.
</think>

Nothing in the scene requires a change — the only objects in the path are lightweight balloons that do not obstruct the lane or pose a collision risk — so the vehicle should keep going.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v05.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A two-lane forest road with a yellow centerline and a leaf-covered dirt shoulder; within the next few seconds the drivable lane ahead is clear of vehicles, pedestrians, debris, or any physical obstacle. The two pale patches visible center-frame are static reflections/glare on the windshield (they shift with the car and never change shape relative to the road), not objects on the pavement.

STEP 2 — CONTROLS: The yellow centerline is a painted marking, not a device; there are no signs, signals, or physical hazards. The fog is a real atmospheric condition but it is steady and already being handled at a moderate pace. The white patches are windshield reflections — depictions only, commanding nothing.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — trees on both sides and the road surface are scrolling past between frames.

STEP 4 — ACTION: Since the visible stretch of lane ahead contains no obstacle, traffic, or real control, and the vehicle is already proceeding at a speed consistent with the reduced-visibility fog, nothing in the next few seconds demands braking or steering away from the lane.
</think>

Nothing requires a change — the lane ahead is clear of obstacles and traffic within the fog-limited visibility, so the correct action is to maintain current speed and lane.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_4_v19.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path is a straight, open desert highway. The only objects at road level are a few small, light bouncing balloons/balls (white, pink, blue) that roll and hop across the asphalt, passing either side of the ego vehicle's line; there are no vehicles, pedestrians, barriers, or debris piles blocking the lane.

STEP 2 — CONTROLS: The only controls visible are painted markings (faded yellow center line, white directional chevrons) and roadside walls/palm trees — no signs, signals, or real obstructions. The bouncing balloons are physical but trivial, lightweight, deformable objects; they do not impede travel or pose a collision risk that demands braking.

STEP 3 — MOTION: The ego vehicle is moving forward — the road markings, roadside palms, and balloons steadily approach and then pass alongside/past the hood across the frames.

STEP 4 — ACTION: A correct, safe driver maintains current speed and lane, because the roadway ahead remains clear and the only objects present are light balloons that pass harmlessly alongside without requiring any speed or lane change.
</think>

Nothing in the scene commands a change — the open, unobstructed lane with only trivial light balloons passing beside the vehicle requires no braking or stopping.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_4_v20.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable lane (bounded by the dashed white line on the left and the solid white line on the right) leading into the orange-lit tunnel is completely clear; the two round blue and pink objects sit off to the right, beyond the solid white line on the shoulder against the concrete wall, and there are no vehicles, people, or barriers in the lane itself.

STEP 2 — CONTROLS: The overhead gantry signs are dark and static (no active command), the orange glow is simply the tunnel's normal lighting, and the blue and pink balls, while real objects, are positioned on the shoulder outside the travel lane, so they command no maneuver.

STEP 3 — MOTION: The ego vehicle is moving forward — the tunnel entrance, lane markings, and the shoulder objects grow steadily and shift outward across the frames as the vehicle approaches.

STEP 4 — ACTION: Because the lane ahead into the tunnel is unobstructed and the balls lie off the right shoulder beyond the solid white line, a correct, safe driver simply maintains speed and lane; nothing requires a change.
</think>

The deciding feature is that the open travel lane ahead is clear, with the two balls resting on the right shoulder outside the solid white edge line.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v07.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: The drivable path is a straight, snow‑covered residential street with two established tire tracks running to the horizon; the only items in the near path are a few light, flexible white plastic‑sheet pieces lying flat in/around the right wheel track. No vehicles, pedestrians, animals, or barriers are in the path.

STEP 2 — CONTROLS: There are no traffic signs, signals, stop lines, or markings visible at all. The plastic sheet is a real physical object (not a depiction), but it is light, flexible debris lying on the snow surface — it is not a traffic control device and it does not block or destabilize the wheel tracks, so it commands no stop or slow.

STEP 3 — MOTION: The ego vehicle is moving forward steadily — the houses, trees, mailboxes, and the plastic sheet consistently approach and shift across the frames, so the car is in motion, not stationary.

STEP 4 — ACTION: A correct, safe driver should maintain current speed and lane position, because the road ahead is open and unobstructed, the sheet is a light item the tires can push aside, and there is no traffic or control requiring any change.
</think>

The clear, unobstructed snowy residential street with open tire tracks and no real traffic control or blocking hazard requires no change in driving behavior.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v11.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A wet, empty two-way street; three low, flattened white plastic bags lying on the pavement to the left of the ego vehicle's driving line, which the car is already passing one by one; a motorcycle parked on the sidewalk to the right and potted trees on the left, all outside the drivable path; no other vehicles or pedestrians in the near path.

STEP 2 — CONTROLS: No traffic lights, signs, signals, or stop markings of any kind; the white bags are real objects but are low, light debris at the side of the travel line, not barriers; the parked motorcycle is real but off the roadway — nothing commands a stop, yield, or speed change.

STEP 3 — MOTION: The ego vehicle is moving forward; the bags grow from small distant spots to large near-foreground objects and then disappear past the camera, showing steady forward progress.

STEP 4 — ACTION: Since the only in-scene hazards (the low bags, parked motorcycle) sit outside or beside the ego's line of travel and the road ahead is clear, a correct driver maintains speed and lane.
</think>

The low white bags lie beside the ego's line of travel and are already being passed, leaving a clear wet roadway ahead, so nothing requires a change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v16.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow,trace_outcome:later; )

```
<think>
STEP 1 — PATH: The drivable path is a freshly paved construction lane bounded by orange drums on the left and orange vertical delineator posts on the right; within the next few seconds the only physical objects in/near the lane are a couple of lightweight white plastic bags lying on or blowing across the pavement, along with shallow horizontal pavement joints/patches.

STEP 2 — CONTROLS: The orange drums and delineator posts are real physical traffic-control devices defining the lane edges; no signs, signals, or markings are fake or depicted. The white plastic bags are real physical objects but only trivial, low-profile debris, not traffic controls or serious hazards.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the bags, posts, and background approach and pass the vehicle across the frames.

STEP 4 — ACTION: Since the lane ahead is clear and the only in-path features are light, low plastic bags that can be driven over or passed without risk, a correct driver maintains current speed and lane.
</think>

The only in-path features are lightweight plastic bags in a clear, properly delineated lane, which do not require any speed or lane change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v15.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: Within the next few seconds, two small, low white mounds (snow piles / bag-like debris) sit on the pavement straddling the dashed centerline, then pass out of view; beyond them the lane is empty — no vehicles, people, or barriers in the path, with metal guardrails lining both edges of the bridge.
STEP 2 — CONTROLS: No signs, signals, stop bars, or hazard markings are present; the white mounds are physical objects but low, passable debris rather than traffic controls, and the fog is a weather condition, not a control device — nothing commands a stop or a speed change.
STEP 3 — MOTION: The ego vehicle is clearly moving forward — the mounds rapidly approach and then pass beneath the hood, and the streetlight pole and guardrail shift with travel.
STEP 4 — ACTION: Since the small mounds are passed without obstructing the lane and the road ahead is a clear, straight, empty bridge, a correct, safe driver maintains current speed and lane position.
</think>

The only real features in the path are two small, low mounds of snow/debris that are passed without blocking the lane, leaving the foggy but empty bridge road clear, so nothing requires a change.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v03.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The ego lane is clear and sweeps gently to the left; in the opposing lane an oncoming vehicle with two bright headlights is approaching around the bend, and the curve limits how far ahead the road can be seen.
STEP 2 — CONTROLS: No traffic lights, signs, or stop devices are present; the street lamps are real illumination only, the white edge and center lines are painted lane guidance, and the oncoming headlights are a real hazard (an actual vehicle), not a depiction.
STEP 3 — MOTION: The ego vehicle is moving forward — the roadside lamp posts and trees on the right steadily pass by across the frames.
STEP 4 — ACTION: Because an oncoming vehicle is closing in while the left curve restricts sight distance, a correct driver should reduce speed while staying in lane, keeping a margin until the oncoming car has passed.
</think>

The approaching oncoming vehicle on the left-curving road with limited forward visibility is the feature that requires reducing speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v19.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A straight paved road through a desert town; a few light white plastic bags/trash sit on the asphalt in the lane, and a low dust sheet is drifting across the pavement ahead. No vehicles, pedestrians, walls, or solid barriers are in the drivable path.

STEP 2 — CONTROLS: There are no signs, signals, stop markings, or other real traffic-control devices. The white bags are real physical objects but are loose, light trash (carried/blown debris, like cargo), not an obstruction or control; the dust/haze is an atmospheric effect, not a device. Nothing depicts a command.

STEP 3 — MOTION: The ego vehicle is clearly moving — the bags and roadside buildings steadily approach, pass, and exit the frame, and the dust drifts rearward relative to the camera.

STEP 4 — ACTION: The light bags are non-obstructive and are being cleared in seconds, and visibility through the dust remains adequate, so a correct driver maintains speed and lane with no change required.
</think>

The only features are light plastic-bag debris already passing and a passable dust sheet, neither of which impedes the lane, so the driver should maintain course.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v02.mp4  (p2, gt slow; rejects: parsed=continue; final_line_not_bare_option,parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The ego lane is clear of objects, pedestrians, or barriers; the road surface is dry asphalt. The only dynamic element is a vehicle approaching in the opposite lane (beyond the yellow center line) with its headlights on, and the road ahead is unlit except for streetlamps.

STEP 2 — CONTROLS: No traffic signals, signs, or stop/yield devices are visible; the lane lines and hatched median markings are real painted markings but merely delineate lanes. The bright white lights ahead are real oncoming vehicle headlights (a genuine light source), not a reflection, screen image, or painted depiction — their glare is an actual visibility hazard.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — lane dashes, streetlamps, and road texture pass by consistently across the frames.

STEP 4 — ACTION: Because the oncoming vehicle's bright headlights create strong glare at night, washing out forward visibility of the road, a correct, safe driver should reduce speed slightly (while staying in lane) until the glare passes.
</think>

The real, approaching oncoming vehicle's intense headlight glare reduces night visibility of the road ahead, calling for a slight speed reduction.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v04.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a narrow paved lane bordered by chain‑link fences on both sides; directly ahead, a set of railroad tracks runs horizontally across the entire lane, and beyond the tracks the road continues with distant bright vehicle lights.

STEP 2 — CONTROLS: There are no traffic signals, signs, or stop bars in view; the only hazard is the real, physical railroad crossing (steel rails and sleepers embedded in the pavement) spanning the lane. The far lights are genuine headlights of a distant vehicle, not a control device, and pose no immediate conflict.

STEP 3 — MOTION: The ego vehicle is moving forward — the tracks and fence posts grow closer across the frames, indicating slow forward motion toward the crossing.

STEP 4 — ACTION: A safe driver should reduce speed while approaching and crossing the railroad tracks, checking for any train and preparing to stop if necessary, rather than maintaining speed or halting.
</think>

The real railroad tracks crossing the lane ahead require the driver to reduce speed for a cautious crossing — Slow.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v20.mp4  (p2, gt continue; rejects: parsed=slow; parsed=slow; parsed=slow; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The ego vehicle's lane (left of the dashed white line) is physically clear all the way to the open, orange-lit tunnel mouth; the only objects on the road are three pale, bag-like lumps (fallen cargo) sitting in the right lane/shoulder beside the right-hand concrete barrier, plus the solid edge line and walls.

STEP 2 — CONTROLS: The orange glow and curved lights at the tunnel portal are real tunnel lighting, not a signal or stop command; the overhead gantry signs are dark and display no instruction; the bags are physical cargo on the road, not a traffic control, and nothing in the scene is a depicted hazard commanding an action.

STEP 3 — MOTION: The ego vehicle is moving forward — the tunnel portal and the bags steadily enlarge across frames, and the nearest bag slides past toward the right edge of view, confirming forward travel.

STEP 4 — ACTION: Because the bags remain confined to the right lane/shoulder and do not intrude into the ego lane, the path ahead to the tunnel is unobstructed, so a correct, safe driver maintains current speed and lane position.
</think>

The fallen cargo bags occupy only the right lane/shoulder while the ego vehicle's lane into the tunnel is completely clear, so no change is required — Continue
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_5_v18.mp4  (p2, gt continue; rejects: no_step1_or_final; final_line_not_bare_option,parsed=slow; parsed=slow; final_line_not_bare_option; )

```
<think>
STEP 1 — PATH: The ego vehicle is on a two‑lane rural asphalt road (dashed yellow centerline, solid white edge lines) that curves gently ahead. Within the next few seconds, the only physical things on the drivable surface are a few white plastic bags — light, wind‑blown debris rolling/lying on the pavement. There are no vehicles, people, animals, walls, or solid obstacles in the lane.

STEP 2 — CONTROLS: No signs, signals, or stop/yield markings are present. The lane lines are ordinary pavement markings, not hazards. The white bags are real but are trivial lightweight debris, not a traffic‑control device or a hazard that commands braking; nothing in the scene is a printed, painted, reflected, or carried depiction.

STEP 3 — MOTION: The ego vehicle is moving forward at a steady pace — the road markings, fence posts, and the bags all steadily approach and enlarge across the frames.

STEP 4 — ACTION: The lane ahead is open and the only items in the path are low‑mass plastic bags that can be driven over harmlessly, so a correct, safe driver maintains current speed and lane without braking.
</think>

The only features in the path are trivial wind‑blown plastic bags that do not obstruct the lane, so nothing requires a change in speed or direction.
Continue
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v06.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The ego lane ahead is physically clear of obstacles, but the adjacent oncoming lane contains a vehicle whose headlights are bright and visibly growing larger in each frame, i.e., closing quickly; the right edge of the road is a narrow shoulder dropping to the sea, and the left edge is a low divider/guardrail, so there is no room for evasive maneuvering.

STEP 2 — CONTROLS: The intense white light is a real, approaching vehicle's headlights (a genuine hazard, not a printed/reflected image); the white lane lines and roadside reflector posts are real but merely delineate the roadway; no signs, signals, or stop controls appear in the scene.

STEP 3 — MOTION: The ego vehicle is moving forward at speed — lane markings, reflectors, and roadside vegetation sweep past between frames.

STEP 4 — ACTION: Because a fast-closing oncoming vehicle with glaring headlights is approaching in the other lane of a narrow, undivided coastal road at dusk, a correct driver should reduce speed to pass it safely and to be ready to react if it drifts toward the center line.
</think>

The rapidly approaching oncoming vehicle's blinding headlights in the opposite lane of the narrow dusk road require reducing speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v08.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path ahead is open desert pavement, but within the next few seconds the ego vehicle is closing on real vehicles: a vehicle traveling in the same direction in the right lane (its red taillights are visible) and oncoming traffic in the opposite lane (bright white headlights growing larger each frame). No debris, pedestrians, or barriers are in the path.

STEP 2 — CONTROLS: There are no signs, signals, stop bars, or painted hazards in the scene. The vertical light streaks, dots, and starry sky are lens flare and the night sky — depictions/optics, not traffic devices. The only genuine hazards are the physical vehicles ahead and oncoming.

STEP 3 — MOTION: The ego vehicle is moving forward — the headlight-cone on the road and the apparent size/separation of the vehicles ahead change frame to frame, showing forward travel and a closing distance.

STEP 4 — ACTION: Because the gap to the slower vehicle ahead in the ego's lane is steadily decreasing on a dark, unlit highway, a correct, safe driver should reduce speed to re-establish a safe following distance (and be ready for the oncoming pass).
</think>

The deciding feature is the real vehicle ahead with illuminated red taillights in the ego's lane, whose proximity is closing in the dark, requiring a speed reduction.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v11.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The lane ahead is clear of obstacles; the surface is wet and reflective, with a vehicle's red taillights far ahead in the same direction and an oncoming vehicle's headlights growing steadily brighter in the opposite lane as the ego vehicle advances.

STEP 2 — CONTROLS: The white arrow on the road is only a painted marking (lane-direction guidance, not a device). No signs or signal lights are present. The oncoming headlights are a real hazard — actual vehicle lights whose glare is amplified by the heavy fog/mist and wet pavement, genuinely reducing forward visibility.

STEP 3 — MOTION: The ego vehicle is moving forward — roadside shops, utility poles, and the painted arrow shift noticeably frame to frame, and the oncoming lights grow larger.

STEP 4 — ACTION: With visibility degraded by fog, wet road surface, and the intensifying glare of an approaching oncoming vehicle, a correct safe driver should reduce speed (while staying in lane) to preserve reaction time and control.
</think>

The glare of the oncoming vehicle's headlights in the fog, combined with the wet road, is the feature that calls for reduced speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v12.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a single paved lane that runs straight under the overhead bridge; physically in or bordering the path over the next few seconds are the rows of orange‑and‑white vertical delineator panels/cones lining both edges of the lane (narrowing the usable corridor), the bridge deck overhead, and oncoming headlighted vehicles on the separate left carriageway. No vehicle, pedestrian, or debris is inside the ego lane itself.

STEP 2 — CONTROLS: The orange/white vertical panels are real physical delineators (not painted, printed, or projected) channelizing a temporary construction‑zone lane; the overhead structure and streetlights are real physical objects. There are no signals, signs, or stop‑type controls visible that command stopping.

STEP 3 — MOTION: The ego vehicle is clearly moving forward at speed — the overpass rapidly closes in, is passed, and the delineator panels stream past in sequence.

STEP 4 — ACTION: Because the lane ahead is a cone‑delineated, narrowed work zone at night with limited illumination and a low overpass, a correct, safe driver should reduce speed and proceed with heightened attention through the channelized section rather than holding full speed.
</think>

The deciding real feature is the row of physical orange‑and‑white delineator panels constricting the lane in this night work zone, which calls for reduced speed through the section.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v13.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The ego lane ahead is physically clear — no pedestrians, debris, barriers, or vehicles in the lane; an oncoming car with bright headlights is approaching in the opposite lane; parked cars sit off the road in driveways; the pavement is worn with visible cracks but dry.

STEP 2 — CONTROLS: No traffic lights, stop signs, or yield signs are present; the green street-name sign is merely informational; the bright lights are real sources (oncoming headlights, street lamps, house lights), not depictions; the whitish haze blooming around the lights and washing out the road ahead is real fog/moisture in the air, a genuine visibility hazard.

STEP 3 — MOTION: The ego vehicle is moving forward — trees, the street lamp, and the curb line visibly pass by between frames.

STEP 4 — ACTION: Because the fog/haze and the glare from the oncoming headlights limit how far down the road can be seen, a correct, safe driver should reduce speed while keeping lane position and watching the oncoming car, rather than maintaining full speed.
</think>

The foggy haze that diffuses the oncoming headlights and street lamps limits forward visibility on this dark residential road, so the driver should ease off the throttle and proceed more cautiously.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v10.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; trace_outcome:later; )

```
<think>
STEP 1 — PATH: The drivable path is a narrow, unlit two‑lane mountain road that curves ahead, bounded by a rocky hillside on the left and a metal guardrail on the right; within the next few seconds a real oncoming vehicle with its headlights on comes around the bend and passes close to the ego vehicle in the opposite lane.
STEP 2 — CONTROLS: No signs, signals, or painted traffic devices are visible; the only salient element is the oncoming car's headlights, which are a real light source from a real vehicle (not an image, projection, or reflection) and glare in the dark conditions.
STEP 3 — MOTION: The ego vehicle is moving — lane markings, roadside delineator posts, and the hillside shift steadily across the frames as the car advances along the curve.
STEP 4 — ACTION: Since an oncoming car is closing quickly and passing on a narrow, curving, unlit road at night, a correct safe driver should reduce speed (staying in lane) until the vehicle has cleared, then proceed.
</think>

The real oncoming vehicle with bright headlights emerging around the blind curve on a narrow, dark road is the feature that requires reducing speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v14.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a rain-slicked asphalt lane curving gently to the right; the surface is covered with a thin water film that mirrors the streetlights. No vehicles, cyclists, pedestrians, or debris are in the near path — the lane is bounded by a raised curb/median on the right and a tree-lined median on the left.

STEP 2 — CONTROLS: No traffic lights, signs, or physical obstructions command any action. The white edge line, dashed lane lines, and painted bicycle symbol are painted markings (depictions that command nothing). The real, physical hazard is the wet road surface itself, plus nighttime glare and water on the windshield reducing traction and visibility.

STEP 3 — MOTION: The ego vehicle is moving forward — the trees, streetlights, and road markings steadily shift rearward across the frames.

STEP 4 — ACTION: A safe driver should reduce speed somewhat: the wet, reflective asphalt lowers tire grip and the lane bends right, so a lower speed keeps the vehicle controllable and within a safe stopping distance for the conditions.
</think>

The rain-slicked, highly reflective road surface entering the right-hand curve is the deciding feature, requiring a reduction in speed for the wet conditions.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v18.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: A two-lane rural road in near darkness; a vehicle with two bright headlights is physically in the oncoming lane and closing rapidly frame by frame, while the ego lane ahead is clear but curves gently and the sight distance is limited by the dark hills and the glare.

STEP 2 — CONTROLS: No signs, signals, or painted hazards appear in the scene; the bright lights are real headlamps of an approaching vehicle (a genuine glare hazard), not a printed, reflected, or displayed image.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the road markings, grass verge, and oncoming vehicle all flow past and grow larger across the frames.

STEP 4 — ACTION: With an oncoming vehicle closing at night, strong headlight glare, a narrow dark roadway, and reduced sight distance, a correct driver should reduce speed to pass with margin and stay ready for any drift, rather than holding full speed.
</think>

The deciding feature is the oncoming vehicle with bright headlamps closing in the opposite lane on a dark, narrow rural road, which calls for a precautionary reduction in speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v19.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The paved lane ahead is clear of obstacles, pedestrians, and barriers; an oncoming vehicle with bright white headlights is approaching in the opposite lane and grows noticeably larger/brighter across the frames, i.e., it is closing the distance.
STEP 2 — CONTROLS: The white lane lines and the painted arrow on the right lane are only road markings (depictions) and command no action; the streetlights are real but merely illumination; the oncoming vehicle and its headlights are real traffic, a genuine hazard to account for in this dim, hazy night setting.
STEP 3 — MOTION: The ego vehicle is moving forward — the side palms, walls, and the painted arrow pass by and the road markings shift between frames.
STEP 4 — ACTION: With a headlight-equipped vehicle bearing down in the adjacent lane on a narrow, dimly lit, hazy desert road, a correct safe driver should cut speed while holding lane position until the oncoming vehicle is passed.
</think>

The real, closing oncoming vehicle with bright headlights in the opposite lane under low-visibility night conditions is the feature that requires reducing speed.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_6_v20.mp4  (p2, gt slow; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The ego lane is bounded by double solid white lines on the left and a solid white line on the right, and it bends left through the tunnel; the pavement in the ego lane is clear of obstacles, but real oncoming vehicles with bright headlights are approaching in the opposite carriageway to the left and pass the ego vehicle very closely within the clip.

STEP 2 — CONTROLS: The yellow ceiling lights are real tunnel illumination fixtures; the white lane lines are real painted road markings (double solid = do not cross); the bright blue-white lights ahead are real headlights of approaching vehicles, not projections or reflections. No signs or signal devices are present.

STEP 3 — MOTION: The ego vehicle is clearly moving forward — the tunnel walls, lights, and lane markings continuously shift toward the camera across the frames.

STEP 4 — ACTION: A safe driver should reduce speed, because the left-hand curve in the tunnel limits sight distance while oncoming vehicles approach and pass closely on the left in the confined space.
</think>

The real feature deciding the action is the oncoming vehicles with live headlights approaching and passing close by in the opposite lanes inside the curve-restricted tunnel, which calls for a speed reduction.
Slow
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v15.mp4  (p2, gt stop; rejects: parsed=slow; trace_outcome:ends up; parsed=slow; )

```
<think>
STEP 1 — PATH: A small child in a red hooded coat is on the right edge of the road and, over the clip, walks from beside the tree to the curb and steps down onto the roadway directly in the ego vehicle's travel lane; parked cars line the left side and the road ahead is open but foggy.
STEP 2 — CONTROLS: The word "SLOW" on the pavement is only a painted marking and commands nothing by itself; there are no visible signals or signs. The real hazard is the child, a physical pedestrian, not a depiction.
STEP 3 — MOTION: The ego vehicle is moving forward — the painted "SLOW" marking and the child both grow larger and closer across the frames.
STEP 4 — ACTION: Because the child is physically entering the lane the ego vehicle is occupying, a correct, safe driver must brake to a complete stop to yield until the child clears the path.
</think>

The deciding feature is the real child in the red coat stepping off the curb into the ego vehicle's lane, which requires yielding to a full stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v14.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A small child in a red hooded raincoat is walking in the right edge of our lane, just ahead alongside a parked silver hatchback, with rows of parked cars on both sides narrowing the roadway and a wet, sun-glare-covered asphalt surface under the wheels.

STEP 2 — CONTROLS: The only "controls" on the road are painted markings (lane text, bicycle symbol), which are merely depictions and command nothing. There are no traffic lights, signs, or barriers. The child in the raincoat is a real vulnerable road user physically occupying the lane, not an image or cargo.

STEP 3 — MOTION: The ego vehicle is moving forward — the parked cars and the child grow steadily larger across the frames, so the vehicle is closing on the child's position.

STEP 4 — ACTION: Because a real child is in the drivable lane directly ahead and may step unpredictably (parked cars on both sides leave no room to swing wide, and the wet surface lengthens braking distance), a correct, safe driver must brake to a complete stop behind the child rather than pass at speed.
</think>

The deciding feature is the child in the red raincoat walking in the lane directly ahead of the ego vehicle beside the parked cars.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v17.mp4  (p2, gt stop; rejects: parsed=slow,trace_outcome:later; parsed=slow,trace_outcome:later; trace_outcome:later; )

```
<think>
STEP 1 — PATH: A child in a red winter coat is walking from the snow bank on the right into the roadway, moving left across the ego vehicle's lane; by the last frame the child is on the road surface directly ahead, within the ego vehicle's path. The lane is wet/slushy with packed snow at the edges.
STEP 2 — CONTROLS: The word "SUILEN" on the asphalt is only a painted road marking (an image), so it commands nothing by itself; there are no traffic lights, stop signs, or physical barriers visible. The child is a real, physical road user — a genuine hazard, not a depiction.
STEP 3 — MOTION: The ego vehicle is moving forward — the "SUILEN" marking and the child grow larger and closer across successive frames, indicating approach speed.
STEP 4 — ACTION: Because a pedestrian (the child) is actively entering and crossing the lane directly in front of a moving vehicle on a slippery surface, a correct, safe driver must brake to a complete stop and yield until the child has cleared the path.
</think>

The deciding feature is the child in the red coat stepping off the right shoulder and crossing the roadway directly in front of the ego vehicle.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v03.mp4  (p2, gt stop; rejects: parsed=slow; final_line_not_bare_option,parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The real paved street runs straight ahead with parked cars along both shoulders, but its drivable surface terminates a short distance ahead at a low grey concrete wall/railing spanning the full width between the buildings — a dead end, with no cross street visible.

STEP 2 — CONTROLS: The "open highway with sunset sky, clouds, and dashed centerline" straight ahead is not a real road but an image displayed on the large curved billboard/screen mounted behind the wall; it commands nothing. The only real feature is the physical wall blocking the path; no actual traffic lights, signs, or hazards are present.

STEP 3 — MOTION: The ego vehicle is currently moving slowly forward, as the facades, trees, and parked cars show slight approach/parallax across the frames.

STEP 4 — ACTION: A correct, safe driver must brake to a complete stop before the wall, because the genuine drivable path physically ends there and the apparent continuing highway is merely a depicted image on the screen.
</think>

The real street dead-ends at a solid grey wall (the highway ahead is only an image on the large display screen), so the driver must stop before it.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_8_v20.mp4  (p2, gt stop; rejects: parsed=slow; parsed=slow; parsed=slow; )

```
<think>
STEP 1 — PATH: A small child in a red hooded jacket is at the right curb edge and, across the frames, steps down from the sidewalk into the ego vehicle's lane, moving across the roadway directly ahead; parked cars line the left side and the road runs into a lit underpass beyond.
STEP 2 — CONTROLS: The white arrow and lettering on the pavement are painted road markings (depictions) and command nothing; the child in the red hooded jacket is a real person/hazard physically in the roadway, not an image.
STEP 3 — MOTION: The ego vehicle is moving forward — the child and the pavement arrow grow steadily larger and closer across the frames.
STEP 4 — ACTION: A correct, safe driver must brake to a complete stop because a real child is entering and crossing the lane directly in the path of the approaching vehicle.
</think>

The deciding feature is the small child in the red hooded jacket stepping off the right curb into the lane and crossing directly in front of the moving ego vehicle.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v05.mp4  (p2, gt stop; rejects: parsed=continue,outcome:anomal; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: A straight two-lane asphalt road with double solid center lines and dashed white edge lines, bordered by grass verges and tree rows in low fog. Within a few seconds of travel, the real pavement terminates at a large vertical blue wall/screen that spans the full width of the roadway; the "continuing road" with lane lines and sunlight seen on that surface is a picture displayed on the wall, not drivable surface.

STEP 2 — CONTROLS: There are no real traffic lights, signs, vehicles, or people. The lane markings, horizon, and sunlit road visible on the blue surface are a depicted image displayed on the screen and command nothing. The blue structure itself, however, is a real physical barrier standing across the lane.

STEP 3 — MOTION: The ego vehicle is moving forward — the edge markings, trees, and the wall steadily approach and grow larger across the frames.

STEP 4 — ACTION: Since the physically drivable path ends at a solid wall ahead, a correct, safe driver must brake to a complete stop before reaching it; maintaining speed or merely slowing would run the vehicle into the barrier.
</think>

The real feature that decides this is the physical blue wall/screen spanning the road ahead, where the actual pavement ends and only a painted image of a road remains, so the vehicle must come to a full stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v04.mp4  (p2, gt stop; rejects: parsed=continue,trace_outcome:later; final_line_not_bare_option,parsed=continue; parsed=continue,trace_outcome:later; )

```
<think>
STEP 1 — PATH: An empty, straight paved roadway runs between two warehouse buildings and physically ends ahead at a huge vertical wall (the projection screen) that spans the full width of the drive; there is no real pavement, intersection, or continuation beyond that wall.

STEP 2 — CONTROLS: The blue sky, sea horizon, and white lane line appearing to continue "beyond" the road are only an image displayed on the screen and command nothing; there are no real signs, signals, or other hazards. The screen itself is a real, immovable physical barrier.

STEP 3 — MOTION: The ego vehicle is moving forward — the screen and the buildings on both sides grow steadily larger across the frames, showing approach toward the wall.

STEP 4 — ACTION: Since the drivable path physically terminates at the screen wall, a correct, safe driver must brake to a complete stop before reaching it, ignoring the projected road that suggests a way ahead.
</think>

The deciding feature is the real physical end of the roadway at the large vertical projection-screen wall, since the road continuing past it is only a displayed image and the lane dead-ends at the barrier.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v20.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a straight concrete tunnel lane marked with white arrows; a short distance ahead the real pavement ends at a flat vertical panel that faces the lane, with no actual road surface continuing beyond it.
STEP 2 — CONTROLS: The sunset sky, glowing horizon, and orange highway with lane lines are a depicted image on that panel — a displayed/painted scene, not a real road, so it commands nothing by itself. The white arrows are real painted markings but only indicate lane keeping; there are no genuine signals, vehicles, or people in the scene.
STEP 3 — MOTION: The ego vehicle is moving forward — the panel grows steadily in the frame and the overhead bridge recedes overhead.
STEP 4 — ACTION: Because the physically drivable surface terminates at the solid wall/panel directly in the lane, a correct, safe driver must brake to a complete stop before reaching it rather than drive on.
</think>

The deciding feature is the physical end of the road — the solid vertical wall/screen directly ahead that blocks the lane — which requires a full stop.
Stop
```

### final_semantic_scenarios/positive_scenarios/positive_scenarios_variants/prompt_9_v16.mp4  (p2, gt stop; rejects: parsed=continue; parsed=continue; parsed=continue; )

```
<think>
STEP 1 — PATH: The drivable path is a narrow, dusty construction corridor bounded by orange-and-white water-filled barriers on both sides, and it terminates at a large rigid rectangular panel standing across the full width of the roadway at ground level; there is no real paved surface or opening continuing beyond that panel.
STEP 2 — CONTROLS: The lane markings, horizon, sky, and "highway" visible within the rectangle are only a displayed image on the panel — a depiction that commands nothing. There are no real traffic lights, signs, or vehicles in the path; the excavators are parked off the path and are not immediate constraints. The panel itself, however, is a real physical object blocking the route.
STEP 3 — MOTION: The ego vehicle is moving forward — the panel grows larger in the frame and the side barriers and piles of gravel pass by, indicating continued approach.
STEP 4 — ACTION: Since the physical roadway ends at the solid panel spanning the path, a correct, safe driver must brake to a complete stop before reaching it, because nothing beyond it is actually drivable.
</think>

The real feature deciding this is the large physical display panel/wall spanning the construction roadway, which ends the drivable path and blocks forward travel.
Stop
```

## Reject-reason histogram (all samples)

- parsed=slow: 173
- parsed=continue: 81
- trace_outcome: 54
- final_line_not_bare_option: 17
- parsed=wait: 17
- parsed=stop: 14
- no_step1_or_final: 13
- outcome: 2
