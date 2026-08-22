# Prompt lab — round 5 (qlab_r5t)

n=235 paired clips; baseline=P0 acc=0.621

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2 | 0.745 | [0.685,0.796] | 0.732 | 0.54/0.93 | +29 (0.012) | 8/15 | 67/235 | 0 | P0 + depiction/necessity guard line (min delta) |
| P0 | 0.621 | [0.558,0.681] | 0.641 | 0.95/0.34 | +0 (1.000) | 0/15 | 187/235 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2 | P0 |
|---|---|---|---|
| neg_prompt_0 | 18 | 10/18 | 17/18 |
| neg_prompt_2 | 19 | 15/19 | 18/19 |
| neg_prompt_3 | 15 | 8/15 | 12/15 |
| neg_prompt_4 | 17 | 11/17 | 17/17 |
| neg_prompt_5 | 16 | 2/16 | 15/16 |
| neg_prompt_8 | 7 | 2/7 | 7/7 |
| neg_prompt_9 | 18 | 11/18 | 18/18 |
| pos_prompt_0 | 17 | 17/17 | 6/17 |
| pos_prompt_11 | 14 | 13/14 | 9/14 |
| pos_prompt_2 | 9 | 8/9 | 0/9 |
| pos_prompt_4 | 18 | 18/18 | 0/18 |
| pos_prompt_5 | 17 | 16/17 | 6/17 |
| pos_prompt_6 | 18 | 18/18 | 17/18 |
| pos_prompt_8 | 19 | 18/19 | 3/19 |
| pos_prompt_9 | 13 | 8/13 | 1/13 |

## L2 vs P0: flips

fixed (77): prompt_0_v20.mp4, prompt_2_v20.mp4, prompt_0.mp4, prompt_11.mp4, prompt_4.mp4, prompt_8.mp4, prompt_0_v01.mp4, prompt_0_v02.mp4, prompt_0_v08.mp4, prompt_0_v09.mp4, prompt_0_v11.mp4, prompt_0_v12.mp4, prompt_0_v14.mp4, prompt_0_v16.mp4, prompt_0_v19.mp4, prompt_0_v20.mp4, prompt_11_v03.mp4, prompt_11_v06.mp4, prompt_11_v12.mp4, prompt_11_v18.mp4, prompt_2_v01.mp4, prompt_2_v05.mp4, prompt_2_v10.mp4, prompt_2_v11.mp4, prompt_2_v14.mp4, prompt_2_v16.mp4, prompt_2_v18.mp4, prompt_2_v20.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v04.mp4, prompt_4_v05.mp4, prompt_4_v06.mp4, prompt_4_v07.mp4, prompt_4_v08.mp4, prompt_4_v10.mp4, prompt_4_v11.mp4, prompt_4_v13.mp4, prompt_4_v14.mp4, prompt_4_v15.mp4, prompt_4_v16.mp4, prompt_4_v17.mp4, prompt_4_v18.mp4, prompt_4_v19.mp4, prompt_4_v20.mp4, prompt_5_v01.mp4, prompt_5_v02.mp4, prompt_5_v03.mp4, prompt_5_v05.mp4, prompt_5_v08.mp4, prompt_5_v10.mp4, prompt_5_v11.mp4, prompt_5_v16.mp4, prompt_5_v18.mp4, prompt_5_v20.mp4, prompt_6_v08.mp4, prompt_8_v01.mp4, prompt_8_v02.mp4, prompt_8_v03.mp4, prompt_8_v04.mp4, prompt_8_v07.mp4, prompt_8_v08.mp4, prompt_8_v09.mp4, prompt_8_v11.mp4, prompt_8_v12.mp4, prompt_8_v14.mp4, prompt_8_v15.mp4, prompt_8_v16.mp4, prompt_8_v18.mp4, prompt_8_v19.mp4, prompt_9_v03.mp4, prompt_9_v04.mp4, prompt_9_v05.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v16.mp4, prompt_9_v20.mp4
broke (48): prompt_0.mp4, prompt_5.mp4, prompt_0_v01.mp4, prompt_0_v02.mp4, prompt_0_v06.mp4, prompt_0_v09.mp4, prompt_0_v10.mp4, prompt_0_v12.mp4, prompt_0_v14.mp4, prompt_2_v02.mp4, prompt_2_v04.mp4, prompt_2_v05.mp4, prompt_2_v11.mp4, prompt_3_v06.mp4, prompt_3_v11.mp4, prompt_3_v15.mp4, prompt_3_v17.mp4, prompt_4_v04.mp4, prompt_4_v06.mp4, prompt_4_v10.mp4, prompt_4_v12.mp4, prompt_4_v15.mp4, prompt_4_v17.mp4, prompt_5_v01.mp4, prompt_5_v02.mp4, prompt_5_v03.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v09.mp4, prompt_5_v10.mp4, prompt_5_v13.mp4, prompt_5_v14.mp4, prompt_5_v15.mp4, prompt_5_v16.mp4, prompt_8_v06.mp4, prompt_8_v08.mp4, prompt_8_v12.mp4, prompt_8_v18.mp4, prompt_8_v20.mp4, prompt_9_v05.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v08.mp4, prompt_9_v13.mp4, prompt_9_v17.mp4, prompt_9_v18.mp4, prompt_11_v14.mp4
