# Prompt lab — round 2 (qlab_rr2d)

n=72 paired clips; baseline=P0 acc=0.750

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2r | 0.806 | [0.700,0.880] | 0.769 | 0.93/0.61 | +4 (0.388) | 3/12 | 52/72 | 0 | L2 + motion-onset attention line (recall child) |
| P0 | 0.750 | [0.639,0.836] | 0.679 | 1.00/0.36 | +0 (1.000) | 0/12 | 62/72 | 0 | baseline control (verbatim released prompt) |

## Per-scenario accuracy

| scenario | n | L2r | P0 |
|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 19/19 |
| neg_prompt_3 | 14 | 11/14 | 14/14 |
| neg_prompt_4 | 4 | 4/4 | 4/4 |
| neg_prompt_5 | 2 | 2/2 | 2/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 |
| neg_prompt_9 | 4 | 4/4 | 4/4 |
| pos_prompt_0 | 6 | 5/6 | 6/6 |
| pos_prompt_11 | 3 | 2/3 | 0/3 |
| pos_prompt_4 | 4 | 2/4 | 0/4 |
| pos_prompt_5 | 6 | 4/6 | 0/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 0/5 | 0/5 |

## L2r vs P0: flips

fixed (8): prompt_11_v04.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v07.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v11.mp4
broke (4): prompt_3_v06.mp4, prompt_3_v12.mp4, prompt_3_v14.mp4, prompt_0_v17.mp4
