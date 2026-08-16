# Prompt lab — round 3

n=72 paired clips; baseline=T0 acc=0.500

| variant | acc | 95% CI | vs P0 net (p) | breadth | anomaly-verdicts | hypothesis |
|---|---|---|---|---|---|---|
| P0d | 0.736 | [0.624,0.824] | +17 (0.003) | 8/12 | 53/72 | direct champion, session gate |
| T3 | 0.625 | [0.510,0.728] | +9 (0.122) | 8/12 | 33/72 | explicit checklist enumeration |
| T8 | 0.597 | [0.482,0.703] | +7 (0.311) | 6/12 | 27/72 | self-context: own probe answers as prior observations |
| TS1 | 0.597 | [0.482,0.703] | +7 (0.296) | 6/12 | 37/72 | think control at greedy t=0 (sampling ablation) |
| T6 | 0.556 | [0.441,0.665] | +4 (0.597) | 4/12 | 39/72 | evidence-grounded: cite timestamps before verdict |
| T7 | 0.556 | [0.441,0.665] | +4 (0.572) | 7/12 | 26/72 | inject normative driving rules (the Part-8 gap) |
| T5 | 0.514 | [0.401,0.626] | +1 (1.000) | 6/12 | 25/72 | impression first, then verification with revise |
| T0 | 0.500 | [0.387,0.613] | +0 (1.000) | 0/12 | 32/72 | think control: example-free skeleton at adopted input |
| T1 | 0.472 | [0.361,0.586] | -2 (0.832) | 3/12 | 34/72 | minimal think: no skeleton at all |
| T4 | 0.458 | [0.348,0.573] | -3 (0.664) | 3/12 | 31/72 | two-hypothesis debate then decide |
| T9 | 0.458 | [0.348,0.573] | -3 (0.720) | 4/12 | 31/72 | think + action channel + anti-smooth necessity |
| T2 | 0.403 | [0.297,0.518] | -7 (0.265) | 2/12 | 31/72 | behaviour-first skeleton order |

## Per-scenario accuracy

| scenario | n | P0d | T3 | T8 | TS1 | T6 | T7 | T5 | T0 | T1 | T4 | T9 | T2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 12/19 | 11/19 | 12/19 | 9/19 | 8/19 | 6/19 | 12/19 | 10/19 | 8/19 | 4/19 | 10/19 |
| neg_prompt_3 | 14 | 9/14 | 5/14 | 3/14 | 8/14 | 10/14 | 4/14 | 6/14 | 3/14 | 4/14 | 5/14 | 8/14 | 1/14 |
| neg_prompt_4 | 4 | 4/4 | 3/4 | 3/4 | 2/4 | 2/4 | 4/4 | 3/4 | 2/4 | 2/4 | 2/4 | 2/4 | 1/4 |
| neg_prompt_5 | 2 | 2/2 | 2/2 | 2/2 | 1/2 | 0/2 | 1/2 | 0/2 | 0/2 | 0/2 | 0/2 | 1/2 | 0/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 0/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 4/4 | 2/4 | 2/4 | 3/4 | 4/4 | 2/4 | 2/4 | 3/4 | 4/4 | 3/4 | 3/4 | 3/4 |
| pos_prompt_0 | 6 | 6/6 | 5/6 | 4/6 | 4/6 | 3/6 | 5/6 | 4/6 | 3/6 | 2/6 | 4/6 | 3/6 | 2/6 |
| pos_prompt_11 | 3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 | 1/3 |
| pos_prompt_4 | 4 | 0/4 | 2/4 | 4/4 | 2/4 | 1/4 | 2/4 | 0/4 | 1/4 | 0/4 | 1/4 | 3/4 | 1/4 |
| pos_prompt_5 | 6 | 0/6 | 1/6 | 4/6 | 1/6 | 1/6 | 2/6 | 4/6 | 3/6 | 2/6 | 1/6 | 2/6 | 2/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 3/4 | 4/4 | 2/4 | 4/4 | 4/4 | 3/4 | 2/4 | 4/4 | 1/4 | 3/4 |
| pos_prompt_8 | 5 | 1/5 | 5/5 | 4/5 | 4/5 | 4/5 | 5/5 | 5/5 | 3/5 | 5/5 | 3/5 | 4/5 | 4/5 |

## P0d vs T0: flips

fixed (24): prompt_5.mp4, prompt_9.mp4, prompt_2_v02.mp4, prompt_2_v04.mp4, prompt_2_v05.mp4, prompt_2_v08.mp4, prompt_2_v12.mp4, prompt_2_v13.mp4, prompt_2_v19.mp4, prompt_3_v02.mp4, prompt_3_v06.mp4, prompt_3_v13.mp4, prompt_3_v14.mp4, prompt_3_v16.mp4, prompt_3_v19.mp4, prompt_4_v01.mp4, prompt_4_v10.mp4, prompt_5_v15.mp4, prompt_8_v18.mp4, prompt_8.mp4, prompt_0_v16.mp4, prompt_0_v17.mp4, prompt_0_v19.mp4, prompt_6_v03.mp4
broke (7): prompt_5.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v05.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v14.mp4
