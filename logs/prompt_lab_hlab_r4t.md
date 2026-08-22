# Prompt lab — round 4 (hlab_r4t)

n=80 paired clips; baseline=L2 acc=0.713

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M8 | 0.800 | [0.700,0.873] | 0.800 | 0.82/0.78 | +7 (0.248) | 5/15 | 42/80 | 0 | compose: guard+feature stage 1 x narrative comparator |
| L2 | 0.713 | [0.605,0.800] | 0.713 | 0.50/0.93 | +0 (1.000) | 0/15 | 23/80 | 0 | P0 + depiction/necessity guard line (min delta) |

## Per-scenario accuracy

| scenario | n | M8 | L2 |
|---|---|---|---|
| neg_prompt_0 | 7 | 7/7 | 4/7 |
| neg_prompt_2 | 7 | 7/7 | 7/7 |
| neg_prompt_3 | 5 | 5/5 | 2/5 |
| neg_prompt_4 | 6 | 6/6 | 3/6 |
| neg_prompt_5 | 6 | 5/6 | 1/6 |
| neg_prompt_8 | 2 | 0/2 | 0/2 |
| neg_prompt_9 | 7 | 3/7 | 3/7 |
| pos_prompt_0 | 5 | 5/5 | 5/5 |
| pos_prompt_11 | 5 | 3/5 | 5/5 |
| pos_prompt_2 | 3 | 3/3 | 2/3 |
| pos_prompt_4 | 6 | 6/6 | 6/6 |
| pos_prompt_5 | 5 | 5/5 | 5/5 |
| pos_prompt_6 | 6 | 6/6 | 6/6 |
| pos_prompt_8 | 6 | 1/6 | 6/6 |
| pos_prompt_9 | 4 | 2/4 | 2/4 |

## M8 vs L2: flips

fixed (17): prompt_0.mp4, prompt_5.mp4, prompt_0_v01.mp4, prompt_0_v10.mp4, prompt_3_v07.mp4, prompt_3_v11.mp4, prompt_3_v13.mp4, prompt_4_v01.mp4, prompt_4_v04.mp4, prompt_4_v16.mp4, prompt_5_v03.mp4, prompt_5_v07.mp4, prompt_5_v12.mp4, prompt_9_v01.mp4, prompt_9_v18.mp4, prompt_9_v20.mp4, prompt_2_v20.mp4
broke (10): prompt_9_v02.mp4, prompt_9_v05.mp4, prompt_9_v09.mp4, prompt_8.mp4, prompt_11_v12.mp4, prompt_11_v20.mp4, prompt_8_v04.mp4, prompt_8_v08.mp4, prompt_8_v11.mp4, prompt_8_v18.mp4
