# Prompt lab — round 2 (hlab_r2t)

n=80 paired clips; baseline=L2 acc=0.713

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M8 | 0.850 | [0.756,0.912] | 0.850 | 0.82/0.88 | +11 (0.061) | 6/15 | 38/80 | 0 | compose: guard+feature stage 1 x narrative comparator |
| M10 | 0.838 | [0.742,0.903] | 0.838 | 0.75/0.93 | +10 (0.076) | 5/15 | 33/80 | 0 | compose: M0 stage 1 x narrative x guard re-check (ablates M4) |
| M9 | 0.838 | [0.742,0.903] | 0.838 | 0.80/0.88 | +10 (0.087) | 5/15 | 37/80 | 0 | compose: guard stage 1 x narrative x guard re-check |
| L2 | 0.713 | [0.605,0.800] | 0.713 | 0.53/0.90 | +0 (1.000) | 0/15 | 25/80 | 0 | P0 + depiction/necessity guard line (min delta) |

## Per-scenario accuracy

| scenario | n | M8 | M10 | M9 | L2 |
|---|---|---|---|---|---|
| neg_prompt_0 | 7 | 7/7 | 7/7 | 7/7 | 3/7 |
| neg_prompt_2 | 7 | 7/7 | 7/7 | 6/7 | 7/7 |
| neg_prompt_3 | 5 | 5/5 | 5/5 | 5/5 | 2/5 |
| neg_prompt_4 | 6 | 6/6 | 6/6 | 6/6 | 3/6 |
| neg_prompt_5 | 6 | 6/6 | 4/6 | 6/6 | 0/6 |
| neg_prompt_8 | 2 | 0/2 | 0/2 | 0/2 | 1/2 |
| neg_prompt_9 | 7 | 2/7 | 1/7 | 2/7 | 5/7 |
| pos_prompt_0 | 5 | 5/5 | 5/5 | 4/5 | 5/5 |
| pos_prompt_11 | 5 | 3/5 | 4/5 | 3/5 | 5/5 |
| pos_prompt_2 | 3 | 3/3 | 3/3 | 3/3 | 3/3 |
| pos_prompt_4 | 6 | 6/6 | 6/6 | 6/6 | 4/6 |
| pos_prompt_5 | 5 | 5/5 | 5/5 | 5/5 | 5/5 |
| pos_prompt_6 | 6 | 6/6 | 6/6 | 6/6 | 6/6 |
| pos_prompt_8 | 6 | 4/6 | 6/6 | 6/6 | 6/6 |
| pos_prompt_9 | 4 | 3/4 | 2/4 | 2/4 | 2/4 |

## M8 vs L2: flips

fixed (20): prompt_0.mp4, prompt_5.mp4, prompt_0_v01.mp4, prompt_0_v03.mp4, prompt_0_v10.mp4, prompt_3_v07.mp4, prompt_3_v11.mp4, prompt_3_v13.mp4, prompt_4_v02.mp4, prompt_4_v04.mp4, prompt_4_v13.mp4, prompt_5_v01.mp4, prompt_5_v03.mp4, prompt_5_v07.mp4, prompt_5_v09.mp4, prompt_5_v12.mp4, prompt_9_v18.mp4, prompt_4_v07.mp4, prompt_4_v13.mp4, prompt_9_v01.mp4
broke (9): prompt_8_v08.mp4, prompt_9_v01.mp4, prompt_9_v02.mp4, prompt_9_v15.mp4, prompt_9_v20.mp4, prompt_8.mp4, prompt_11_v12.mp4, prompt_11_v20.mp4, prompt_8_v18.mp4
