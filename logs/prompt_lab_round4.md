# Prompt lab — round 4

n=72 paired clips; baseline=P0d acc=0.722

| variant | acc | 95% CI | vs P0 net (p) | breadth | anomaly-verdicts | hypothesis |
|---|---|---|---|---|---|---|
| P0d | 0.722 | [0.610,0.812] | +0 (1.000) | 0/12 | 52/72 | direct champion, session gate |
| T3k5 | 0.611 | [0.496,0.715] | -8 (0.169) | 3/12 | 36/72 | checklist self-consistency k=5 at t=0.6 |
| T3gf | 0.542 | [0.427,0.652] | -13 (0.029) | 3/12 | 31/72 | checklist + focus guard + greedy (full compose) |
| T3g | 0.514 | [0.401,0.626] | -15 (0.008) | 2/12 | 41/72 | checklist at greedy decoding (winners composed) |
| T3f | 0.486 | [0.374,0.599] | -17 (0.006) | 3/12 | 27/72 | checklist + focus guard, guide sampling |

## Per-scenario accuracy

| scenario | n | P0d | T3k5 | T3gf | T3g | T3f |
|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 18/19 | 12/19 | 12/19 | 13/19 | 10/19 |
| neg_prompt_3 | 14 | 9/14 | 6/14 | 6/14 | 5/14 | 2/14 |
| neg_prompt_4 | 4 | 4/4 | 3/4 | 2/4 | 3/4 | 1/4 |
| neg_prompt_5 | 2 | 2/2 | 2/2 | 1/2 | 0/2 | 0/2 |
| neg_prompt_8 | 1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| neg_prompt_9 | 4 | 4/4 | 3/4 | 0/4 | 4/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 3/6 | 4/6 | 1/6 | 2/6 |
| pos_prompt_11 | 3 | 3/3 | 3/3 | 3/3 | 2/3 | 3/3 |
| pos_prompt_4 | 4 | 0/4 | 1/4 | 1/4 | 1/4 | 3/4 |
| pos_prompt_5 | 6 | 0/6 | 3/6 | 2/6 | 0/6 | 1/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 3/4 | 3/4 | 4/4 |
| pos_prompt_8 | 5 | 1/5 | 4/5 | 5/5 | 5/5 | 5/5 |

## T3k5 vs P0d: flips

fixed (9): prompt_3.mp4, prompt_2_v14.mp4, prompt_4_v03.mp4, prompt_5_v01.mp4, prompt_5_v04.mp4, prompt_5_v11.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (17): prompt_9.mp4, prompt_2_v01.mp4, prompt_2_v02.mp4, prompt_2_v04.mp4, prompt_2_v05.mp4, prompt_2_v17.mp4, prompt_2_v19.mp4, prompt_2_v20.mp4, prompt_3_v02.mp4, prompt_3_v11.mp4, prompt_3_v14.mp4, prompt_3_v16.mp4, prompt_4_v17.mp4, prompt_8_v18.mp4, prompt_0_v01.mp4, prompt_0_v16.mp4, prompt_0_v17.mp4
