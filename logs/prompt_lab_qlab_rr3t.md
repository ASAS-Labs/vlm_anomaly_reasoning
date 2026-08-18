# Prompt lab — round 3 (qlab_rr3t)

n=72 paired clips; baseline=P0 acc=0.708

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2 | 0.889 | [0.796,0.943] | 0.909 | 0.82/1.00 | +13 (0.019) | 6/12 | 36/72 | 0 | P0 + depiction/necessity guard line (min delta) |
| L2r | 0.792 | [0.684,0.869] | 0.804 | 0.75/0.86 | +6 (0.327) | 4/12 | 37/72 | 1 | L2 + motion-onset attention line (recall child) |
| P0 | 0.708 | [0.595,0.801] | 0.657 | 0.89/0.43 | +0 (1.000) | 0/12 | 55/72 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2 | L2r | P0 |
|---|---|---|---|---|
| neg_prompt_2 | 19 | 18/19 | 18/19 | 18/19 |
| neg_prompt_3 | 14 | 12/14 | 9/14 | 10/14 |
| neg_prompt_4 | 4 | 2/4 | 2/4 | 4/4 |
| neg_prompt_5 | 2 | 1/2 | 1/2 | 2/2 |
| neg_prompt_8 | 1 | 0/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 3/4 | 3/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 6/6 | 2/6 |
| pos_prompt_11 | 3 | 3/3 | 1/3 | 2/3 |
| pos_prompt_4 | 4 | 4/4 | 4/4 | 0/4 |
| pos_prompt_5 | 6 | 6/6 | 5/6 | 4/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 5/5 | 4/5 | 0/5 |

## L2 vs P0: flips

fixed (20): prompt_2_v17.mp4, prompt_3_v11.mp4, prompt_3_v14.mp4, prompt_3_v15.mp4, prompt_4.mp4, prompt_5.mp4, prompt_8.mp4, prompt_0_v01.mp4, prompt_0_v04.mp4, prompt_0_v16.mp4, prompt_0_v17.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v06.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (7): prompt_5.mp4, prompt_9.mp4, prompt_2_v05.mp4, prompt_3_v12.mp4, prompt_4_v01.mp4, prompt_4_v07.mp4, prompt_8_v18.mp4
