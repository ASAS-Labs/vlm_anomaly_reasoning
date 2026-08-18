# Prompt lab — round 2 (qlab_r2t)

n=72 paired clips; baseline=P0 acc=0.736

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2r | 0.750 | [0.639,0.836] | 0.782 | 0.64/0.93 | +1 (1.000) | 5/12 | 29/72 | 7 | L2 + motion-onset attention line (recall child) |
| P0 | 0.736 | [0.624,0.824] | 0.693 | 0.89/0.50 | +0 (1.000) | 0/12 | 53/72 | 1 | baseline control (verbatim released prompt) |
| L2 | 0.722 | [0.610,0.812] | 0.760 | 0.59/0.93 | -1 (1.000) | 5/12 | 27/72 | 7 | P0 + depiction/necessity guard line (min delta) |
| L6 | 0.611 | [0.496,0.715] | 0.649 | 0.48/0.82 | -9 (0.175) | 5/12 | 25/72 | 4 | reality checklist w/ physical-support test |

## Per-scenario accuracy

| scenario | n | L2r | P0 | L2 | L6 |
|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 16/19 | 18/19 | 15/19 | 7/19 |
| neg_prompt_3 | 14 | 8/14 | 10/14 | 7/14 | 8/14 |
| neg_prompt_4 | 4 | 2/4 | 4/4 | 3/4 | 0/4 |
| neg_prompt_5 | 2 | 0/2 | 2/2 | 0/2 | 1/2 |
| neg_prompt_8 | 1 | 0/1 | 1/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 2/4 | 4/4 | 1/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 5/6 | 6/6 | 6/6 |
| pos_prompt_11 | 3 | 2/3 | 1/3 | 3/3 | 3/3 |
| pos_prompt_4 | 4 | 4/4 | 0/4 | 3/4 | 2/4 |
| pos_prompt_5 | 6 | 6/6 | 2/6 | 5/6 | 5/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 4/5 | 2/5 | 5/5 | 3/5 |

## L2r vs P0: flips

fixed (15): prompt_2_v20.mp4, prompt_3_v03.mp4, prompt_3_v14.mp4, prompt_0.mp4, prompt_4.mp4, prompt_5.mp4, prompt_8.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_8_v01.mp4
broke (14): prompt_5.mp4, prompt_9.mp4, prompt_2_v04.mp4, prompt_2_v05.mp4, prompt_2_v11.mp4, prompt_3_v02.mp4, prompt_3_v06.mp4, prompt_3_v11.mp4, prompt_3_v13.mp4, prompt_4_v07.mp4, prompt_4_v10.mp4, prompt_5_v15.mp4, prompt_8_v18.mp4, prompt_9_v01.mp4
