# Prompt lab — round 2 (qlab_r2d)

n=72 paired clips; baseline=P0 acc=0.611

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2r | 0.736 | [0.624,0.824] | 0.784 | 0.57/1.00 | +9 (0.064) | 4/12 | 25/72 | 0 | L2 + motion-onset attention line (recall child) |
| L2 | 0.708 | [0.595,0.801] | 0.761 | 0.52/1.00 | +7 (0.189) | 4/12 | 23/72 | 0 | P0 + depiction/necessity guard line (min delta) |
| L2w | 0.681 | [0.566,0.777] | 0.739 | 0.48/1.00 | +5 (0.405) | 4/12 | 21/72 | 0 | L2 + Normal-carries-a-burden line (recall child) |
| P0 | 0.611 | [0.496,0.715] | 0.591 | 0.68/0.50 | +0 (1.000) | 0/12 | 44/72 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2r | L2 | L2w | P0 |
|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 19/19 | 14/19 | 19/19 |
| neg_prompt_3 | 14 | 0/14 | 0/14 | 0/14 | 0/14 |
| neg_prompt_4 | 4 | 3/4 | 1/4 | 3/4 | 4/4 |
| neg_prompt_5 | 2 | 0/2 | 0/2 | 1/2 | 2/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| neg_prompt_9 | 4 | 2/4 | 2/4 | 2/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 6/6 | 6/6 | 6/6 |
| pos_prompt_11 | 3 | 3/3 | 3/3 | 3/3 | 2/3 |
| pos_prompt_4 | 4 | 4/4 | 4/4 | 4/4 | 1/4 |
| pos_prompt_5 | 6 | 6/6 | 6/6 | 6/6 | 1/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 5/5 | 5/5 | 5/5 | 0/5 |

## L2r vs P0: flips

fixed (14): prompt_5.mp4, prompt_8.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v11.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (5): prompt_5.mp4, prompt_9.mp4, prompt_4_v07.mp4, prompt_5_v15.mp4, prompt_9_v14.mp4
