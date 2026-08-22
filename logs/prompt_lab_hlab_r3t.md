# Prompt lab — round 3 (hlab_r3t)

n=80 paired clips; baseline=L2 acc=0.700

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M8 | 0.850 | [0.756,0.912] | 0.850 | 0.82/0.88 | +12 (0.023) | 7/15 | 38/80 | 0 | compose: guard+feature stage 1 x narrative comparator |
| M11 | 0.825 | [0.727,0.893] | 0.825 | 0.80/0.85 | +10 (0.076) | 7/15 | 38/80 | 0 | M8 with stage-1 majority-of-3 self-consistency |
| L2 | 0.700 | [0.592,0.789] | 0.700 | 0.53/0.88 | +0 (1.000) | 0/15 | 26/80 | 0 | P0 + depiction/necessity guard line (min delta) |

## Per-scenario accuracy

| scenario | n | M8 | M11 | L2 |
|---|---|---|---|---|
| neg_prompt_0 | 7 | 7/7 | 7/7 | 3/7 |
| neg_prompt_2 | 7 | 7/7 | 7/7 | 7/7 |
| neg_prompt_3 | 5 | 5/5 | 5/5 | 3/5 |
| neg_prompt_4 | 6 | 6/6 | 6/6 | 4/6 |
| neg_prompt_5 | 6 | 6/6 | 6/6 | 0/6 |
| neg_prompt_8 | 2 | 0/2 | 0/2 | 0/2 |
| neg_prompt_9 | 7 | 2/7 | 1/7 | 4/7 |
| pos_prompt_0 | 5 | 5/5 | 5/5 | 5/5 |
| pos_prompt_11 | 5 | 3/5 | 3/5 | 4/5 |
| pos_prompt_2 | 3 | 3/3 | 3/3 | 2/3 |
| pos_prompt_4 | 6 | 6/6 | 6/6 | 5/6 |
| pos_prompt_5 | 5 | 5/5 | 5/5 | 5/5 |
| pos_prompt_6 | 6 | 6/6 | 6/6 | 6/6 |
| pos_prompt_8 | 6 | 4/6 | 3/6 | 6/6 |
| pos_prompt_9 | 4 | 3/4 | 3/4 | 2/4 |

## M8 vs L2: flips

fixed (18): prompt_0.mp4, prompt_5.mp4, prompt_0_v03.mp4, prompt_0_v10.mp4, prompt_0_v13.mp4, prompt_3_v07.mp4, prompt_3_v13.mp4, prompt_4_v04.mp4, prompt_4_v13.mp4, prompt_5_v01.mp4, prompt_5_v03.mp4, prompt_5_v07.mp4, prompt_5_v09.mp4, prompt_5_v12.mp4, prompt_9_v20.mp4, prompt_2_v05.mp4, prompt_4_v13.mp4, prompt_9_v06.mp4
broke (6): prompt_9_v02.mp4, prompt_9_v05.mp4, prompt_9_v18.mp4, prompt_8.mp4, prompt_11_v20.mp4, prompt_8_v04.mp4
