# Prompt lab — round 5 (hlab_r5t)

n=235 paired clips; baseline=L2 acc=0.715

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M8 | 0.830 | [0.777,0.872] | 0.826 | 0.77/0.88 | +27 (0.002) | 8/15 | 100/235 | 0 | compose: guard+feature stage 1 x narrative comparator |
| L2q | 0.745 | [0.685,0.796] | 0.732 | 0.54/0.93 | +7 (0.311) | 7/15 | 67/235 | 0 | P0 + depiction/necessity guard line (min delta) |
| L2 | 0.715 | [0.654,0.769] | 0.701 | 0.49/0.91 | +0 (1.000) | 0/15 | 64/235 | 0 | P0 + depiction/necessity guard line (min delta) |

## Per-scenario accuracy

| scenario | n | M8 | L2q | L2 |
|---|---|---|---|---|
| neg_prompt_0 | 18 | 18/18 | 10/18 | 11/18 |
| neg_prompt_2 | 19 | 16/19 | 15/19 | 15/19 |
| neg_prompt_3 | 15 | 15/15 | 8/15 | 4/15 |
| neg_prompt_4 | 17 | 17/17 | 11/17 | 14/17 |
| neg_prompt_5 | 16 | 16/16 | 2/16 | 0/16 |
| neg_prompt_8 | 7 | 0/7 | 2/7 | 0/7 |
| neg_prompt_9 | 18 | 3/18 | 11/18 | 10/18 |
| pos_prompt_0 | 17 | 17/17 | 17/17 | 17/17 |
| pos_prompt_11 | 14 | 10/14 | 13/14 | 14/14 |
| pos_prompt_2 | 9 | 9/9 | 8/9 | 7/9 |
| pos_prompt_4 | 18 | 18/18 | 18/18 | 17/18 |
| pos_prompt_5 | 17 | 17/17 | 16/17 | 17/17 |
| pos_prompt_6 | 18 | 18/18 | 18/18 | 18/18 |
| pos_prompt_8 | 19 | 15/19 | 18/19 | 19/19 |
| pos_prompt_9 | 13 | 6/13 | 8/13 | 5/13 |

## M8 vs L2: flips

fixed (48): prompt_0.mp4, prompt_3.mp4, prompt_5.mp4, prompt_0_v02.mp4, prompt_0_v03.mp4, prompt_0_v09.mp4, prompt_0_v10.mp4, prompt_0_v12.mp4, prompt_0_v14.mp4, prompt_2_v02.mp4, prompt_2_v03.mp4, prompt_2_v11.mp4, prompt_3_v02.mp4, prompt_3_v05.mp4, prompt_3_v06.mp4, prompt_3_v07.mp4, prompt_3_v09.mp4, prompt_3_v11.mp4, prompt_3_v12.mp4, prompt_3_v13.mp4, prompt_3_v16.mp4, prompt_3_v17.mp4, prompt_4_v01.mp4, prompt_4_v10.mp4, prompt_4_v15.mp4, prompt_5_v01.mp4, prompt_5_v02.mp4, prompt_5_v03.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v07.mp4, prompt_5_v09.mp4, prompt_5_v10.mp4, prompt_5_v12.mp4, prompt_5_v13.mp4, prompt_5_v14.mp4, prompt_5_v15.mp4, prompt_5_v16.mp4, prompt_5_v17.mp4, prompt_9_v06.mp4, prompt_9_v19.mp4, prompt_2_v12.mp4, prompt_2_v16.mp4, prompt_4_v13.mp4, prompt_9_v01.mp4, prompt_9_v14.mp4, prompt_9_v17.mp4
broke (21): prompt_2_v05.mp4, prompt_2_v20.mp4, prompt_9_v01.mp4, prompt_9_v02.mp4, prompt_9_v03.mp4, prompt_9_v09.mp4, prompt_9_v10.mp4, prompt_9_v11.mp4, prompt_9_v14.mp4, prompt_9_v15.mp4, prompt_9_v18.mp4, prompt_11.mp4, prompt_8.mp4, prompt_11_v02.mp4, prompt_11_v03.mp4, prompt_11_v12.mp4, prompt_8_v04.mp4, prompt_8_v14.mp4, prompt_8_v18.mp4, prompt_9_v04.mp4, prompt_9_v05.mp4
