# Prompt lab — round 1

n=72 paired clips; baseline=P0 acc=0.736

| variant | acc | 95% CI | vs P0 net (p) | breadth | anomaly-verdicts | hypothesis |
|---|---|---|---|---|---|---|
| P0 | 0.736 | [0.624,0.824] | +0 (1.000) | 0/12 | 53/72 | baseline control (verbatim released prompt) |
| S1 | 0.722 | [0.610,0.812] | -1 (1.000) | 1/12 | 58/72 | guide's official non-reasoning sampling on the baseline |
| P4 | 0.653 | [0.538,0.752] | -6 (0.307) | 3/12 | 31/72 | anti-smooth framing rescues the action channel |
| P6 | 0.639 | [0.524,0.740] | -7 (0.296) | 3/12 | 20/72 | abstract task-definition context improves judgement |
| P5 | 0.625 | [0.510,0.728] | -8 (0.152) | 2/12 | 33/72 | narrative action summary beats raw numbers |
| P1 | 0.611 | [0.496,0.715] | -9 (0.093) | 3/12 | 32/72 | crisp decision rule replaces muddled definition |
| P3 | 0.444 | [0.335,0.559] | -21 (0.004) | 3/12 | 4/72 | remove the loaded word 'anomaly' (binary correct/incorrect) |
| P2 | 0.417 | [0.310,0.532] | -23 (0.001) | 3/12 | 6/72 | forced commitment: CUE and ACTION lines before verdict |
| P7 | 0.333 | [0.235,0.448] | -29 (0.000) | 2/12 | 18/72 | examiner pass/fail persona sharpens the criterion |

## Per-scenario accuracy

| scenario | n | P0 | S1 | P4 | P6 | P5 | P1 | P3 | P2 | P7 |
|---|---|---|---|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 19/19 | 11/19 | 12/19 | 7/19 | 10/19 | 0/19 | 2/19 | 9/19 |
| neg_prompt_3 | 14 | 9/14 | 11/14 | 8/14 | 1/14 | 8/14 | 6/14 | 0/14 | 0/14 | 1/14 |
| neg_prompt_4 | 4 | 4/4 | 4/4 | 2/4 | 2/4 | 3/4 | 2/4 | 1/4 | 1/4 | 1/4 |
| neg_prompt_5 | 2 | 2/2 | 2/2 | 1/2 | 1/2 | 2/2 | 1/2 | 1/2 | 0/2 | 1/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 4/4 | 4/4 | 2/4 | 2/4 | 4/4 | 4/4 | 2/4 | 1/4 | 1/4 |
| pos_prompt_0 | 6 | 6/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 5/6 | 0/6 |
| pos_prompt_11 | 3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 1/3 |
| pos_prompt_4 | 4 | 0/4 | 0/4 | 1/4 | 3/4 | 0/4 | 1/4 | 4/4 | 4/4 | 0/4 |
| pos_prompt_5 | 6 | 0/6 | 0/6 | 3/6 | 6/6 | 2/6 | 3/6 | 6/6 | 5/6 | 4/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 0/4 |
| pos_prompt_8 | 5 | 1/5 | 0/5 | 5/5 | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 5/5 |

## S1 vs P0: flips

fixed (2): prompt_3_v05.mp4, prompt_3_v11.mp4
broke (3): prompt_11.mp4, prompt_8.mp4, prompt_0_v17.mp4
