# Prompt lab — round 2

n=72 paired clips; baseline=P0 acc=0.750

| variant | acc | 95% CI | vs P0 net (p) | breadth | anomaly-verdicts | hypothesis |
|---|---|---|---|---|---|---|
| P0 | 0.750 | [0.639,0.836] | +0 (1.000) | 0/12 | 54/72 | baseline control (verbatim released prompt) |
| S2 | 0.722 | [0.610,0.812] | -2 (0.625) | 1/12 | 50/72 | self-consistency: P0 x5 samples at t=0.7, majority |
| P9 | 0.667 | [0.552,0.765] | -6 (0.238) | 2/12 | 36/72 | P6 definitions grafted before the verbatim P0 question |
| P8 | 0.528 | [0.414,0.639] | -16 (0.002) | 2/12 | 28/72 | champion P0 + one scenery-vs-response line |
| P10 | 0.403 | [0.297,0.518] | -25 (0.000) | 3/12 | 17/72 | P8 + one-sentence rationale before the verdict |

## Per-scenario accuracy

| scenario | n | P0 | S2 | P9 | P8 | P10 |
|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 17/19 | 12/19 | 10/19 | 2/19 |
| neg_prompt_3 | 14 | 10/14 | 10/14 | 6/14 | 2/14 | 1/14 |
| neg_prompt_4 | 4 | 4/4 | 4/4 | 3/4 | 1/4 | 2/4 |
| neg_prompt_5 | 2 | 2/2 | 1/2 | 2/2 | 1/2 | 1/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |
| neg_prompt_9 | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 3/4 |
| pos_prompt_0 | 6 | 6/6 | 6/6 | 6/6 | 6/6 | 2/6 |
| pos_prompt_11 | 3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| pos_prompt_4 | 4 | 0/4 | 0/4 | 2/4 | 0/4 | 3/4 |
| pos_prompt_5 | 6 | 0/6 | 1/6 | 4/6 | 1/6 | 3/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| pos_prompt_8 | 5 | 1/5 | 1/5 | 1/5 | 5/5 | 5/5 |

## S2 vs P0: flips

fixed (1): prompt_5_v04.mp4
broke (3): prompt_2.mp4, prompt_5.mp4, prompt_2_v14.mp4
