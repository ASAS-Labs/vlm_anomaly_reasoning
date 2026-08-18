# Prompt lab — round 3 (qlab_r3t)

n=72 paired clips; baseline=P0 acc=0.694

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2 | 0.806 | [0.700,0.880] | 0.841 | 0.68/1.00 | +8 (0.229) | 6/12 | 30/72 | 0 | P0 + depiction/necessity guard line (min delta) |
| L2r | 0.806 | [0.700,0.880] | 0.834 | 0.70/0.96 | +8 (0.215) | 5/12 | 32/72 | 0 | L2 + motion-onset attention line (recall child) |
| P0 | 0.694 | [0.580,0.789] | 0.646 | 0.86/0.43 | +0 (1.000) | 0/12 | 54/72 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2 | L2r | P0 |
|---|---|---|---|---|
| neg_prompt_2 | 19 | 18/19 | 17/19 | 19/19 |
| neg_prompt_3 | 14 | 10/14 | 10/14 | 8/14 |
| neg_prompt_4 | 4 | 1/4 | 2/4 | 4/4 |
| neg_prompt_5 | 2 | 1/2 | 0/2 | 2/2 |
| neg_prompt_8 | 1 | 0/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 0/4 | 2/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 6/6 | 5/6 |
| pos_prompt_11 | 3 | 3/3 | 2/3 | 2/3 |
| pos_prompt_4 | 4 | 4/4 | 4/4 | 0/4 |
| pos_prompt_5 | 6 | 6/6 | 6/6 | 1/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 5/5 | 5/5 | 0/5 |

## L2 vs P0: flips

fixed (21): prompt_3_v02.mp4, prompt_3_v03.mp4, prompt_3_v12.mp4, prompt_3_v13.mp4, prompt_3_v14.mp4, prompt_0.mp4, prompt_4.mp4, prompt_5.mp4, prompt_8.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v11.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (13): prompt_9.mp4, prompt_2_v03.mp4, prompt_3_v06.mp4, prompt_3_v07.mp4, prompt_3_v11.mp4, prompt_4_v07.mp4, prompt_4_v10.mp4, prompt_4_v17.mp4, prompt_5_v15.mp4, prompt_8_v18.mp4, prompt_9_v01.mp4, prompt_9_v02.mp4, prompt_9_v14.mp4
