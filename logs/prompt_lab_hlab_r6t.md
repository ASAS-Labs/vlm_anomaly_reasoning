# Prompt lab — round 6 (hlab_r6t)

n=40 paired clips; baseline=M8 acc=0.075

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M8w10 | 0.350 | [0.221,0.505] | 0.360 | 0.32/0.40 | +11 (0.001) | 5/6 | 17/40 | 0 | M8 with the stage-1 window at T-1.0 (sees later events) |
| M8w15 | 0.300 | [0.181,0.454] | 0.347 | 0.16/0.53 | +9 (0.004) | 4/6 | 11/40 | 0 | M8 with the stage-1 window at T-1.5 (sees later events) |
| M8 | 0.075 | [0.026,0.199] | 0.073 | 0.08/0.07 | +0 (1.000) | 0/6 | 16/40 | 0 | compose: guard+feature stage 1 x narrative comparator |

## Per-scenario accuracy

| scenario | n | M8w10 | M8w15 | M8 |
|---|---|---|---|---|
| neg_prompt_2 | 3 | 2/3 | 1/3 | 1/3 |
| neg_prompt_8 | 7 | 1/7 | 0/7 | 0/7 |
| neg_prompt_9 | 15 | 5/15 | 3/15 | 1/15 |
| pos_prompt_11 | 4 | 0/4 | 1/4 | 0/4 |
| pos_prompt_8 | 4 | 4/4 | 4/4 | 0/4 |
| pos_prompt_9 | 7 | 2/7 | 3/7 | 1/7 |

## M8w10 vs M8: flips

fixed (11): prompt_2_v05.mp4, prompt_8_v03.mp4, prompt_9_v02.mp4, prompt_9_v11.mp4, prompt_9_v14.mp4, prompt_9_v15.mp4, prompt_8.mp4, prompt_8_v04.mp4, prompt_8_v14.mp4, prompt_8_v18.mp4, prompt_9_v05.mp4
broke (0): 
