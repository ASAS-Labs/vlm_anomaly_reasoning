# Prompt lab — round 5 (qlab_r5d)

n=235 paired clips; baseline=P0 acc=0.562

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2 | 0.621 | [0.558,0.681] | 0.604 | 0.33/0.88 | +14 (0.219) | 6/15 | 51/235 | 0 | P0 + depiction/necessity guard line (min delta) |
| P0 | 0.562 | [0.498,0.624] | 0.574 | 0.76/0.38 | +0 (1.000) | 0/15 | 161/235 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2 | P0 |
|---|---|---|---|
| neg_prompt_0 | 18 | 1/18 | 8/18 |
| neg_prompt_2 | 19 | 19/19 | 19/19 |
| neg_prompt_3 | 15 | 0/15 | 1/15 |
| neg_prompt_4 | 17 | 2/17 | 17/17 |
| neg_prompt_5 | 16 | 1/16 | 14/16 |
| neg_prompt_8 | 7 | 6/7 | 7/7 |
| neg_prompt_9 | 18 | 7/18 | 18/18 |
| pos_prompt_0 | 17 | 17/17 | 17/17 |
| pos_prompt_11 | 14 | 13/14 | 8/14 |
| pos_prompt_2 | 9 | 2/9 | 1/9 |
| pos_prompt_4 | 18 | 18/18 | 0/18 |
| pos_prompt_5 | 17 | 17/17 | 2/17 |
| pos_prompt_6 | 18 | 18/18 | 18/18 |
| pos_prompt_8 | 19 | 16/19 | 0/19 |
| pos_prompt_9 | 13 | 9/13 | 2/13 |

## L2 vs P0: flips

fixed (63): prompt_0_v17.mp4, prompt_4.mp4, prompt_5.mp4, prompt_8.mp4, prompt_11_v06.mp4, prompt_11_v15.mp4, prompt_11_v16.mp4, prompt_11_v18.mp4, prompt_11_v20.mp4, prompt_2_v14.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v04.mp4, prompt_4_v05.mp4, prompt_4_v06.mp4, prompt_4_v07.mp4, prompt_4_v08.mp4, prompt_4_v10.mp4, prompt_4_v11.mp4, prompt_4_v13.mp4, prompt_4_v14.mp4, prompt_4_v15.mp4, prompt_4_v16.mp4, prompt_4_v17.mp4, prompt_4_v18.mp4, prompt_4_v19.mp4, prompt_4_v20.mp4, prompt_5_v01.mp4, prompt_5_v02.mp4, prompt_5_v03.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v08.mp4, prompt_5_v10.mp4, prompt_5_v11.mp4, prompt_5_v14.mp4, prompt_5_v15.mp4, prompt_5_v16.mp4, prompt_5_v18.mp4, prompt_5_v19.mp4, prompt_5_v20.mp4, prompt_8_v01.mp4, prompt_8_v02.mp4, prompt_8_v03.mp4, prompt_8_v04.mp4, prompt_8_v06.mp4, prompt_8_v07.mp4, prompt_8_v09.mp4, prompt_8_v11.mp4, prompt_8_v12.mp4, prompt_8_v13.mp4, prompt_8_v14.mp4, prompt_8_v15.mp4, prompt_8_v16.mp4, prompt_8_v17.mp4, prompt_8_v20.mp4, prompt_9_v01.mp4, prompt_9_v03.mp4, prompt_9_v05.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v09.mp4, prompt_9_v14.mp4
broke (49): prompt_4.mp4, prompt_5.mp4, prompt_9.mp4, prompt_0_v04.mp4, prompt_0_v06.mp4, prompt_0_v09.mp4, prompt_0_v10.mp4, prompt_0_v11.mp4, prompt_0_v13.mp4, prompt_0_v15.mp4, prompt_0_v16.mp4, prompt_3_v19.mp4, prompt_4_v01.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v04.mp4, prompt_4_v05.mp4, prompt_4_v06.mp4, prompt_4_v07.mp4, prompt_4_v12.mp4, prompt_4_v13.mp4, prompt_4_v14.mp4, prompt_4_v15.mp4, prompt_4_v16.mp4, prompt_4_v17.mp4, prompt_4_v20.mp4, prompt_5_v01.mp4, prompt_5_v02.mp4, prompt_5_v03.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v09.mp4, prompt_5_v10.mp4, prompt_5_v12.mp4, prompt_5_v13.mp4, prompt_5_v14.mp4, prompt_5_v15.mp4, prompt_5_v16.mp4, prompt_8_v02.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v10.mp4, prompt_9_v11.mp4, prompt_9_v13.mp4, prompt_9_v14.mp4, prompt_9_v15.mp4, prompt_9_v17.mp4, prompt_9_v19.mp4, prompt_9_v20.mp4
