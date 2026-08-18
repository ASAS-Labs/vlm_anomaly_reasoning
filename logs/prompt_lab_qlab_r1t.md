# Prompt lab — round 1 (qlab_r1t)

n=72 paired clips; baseline=P0 acc=0.722

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| P0 | 0.722 | [0.610,0.812] | 0.669 | 0.91/0.43 | +0 (1.000) | 0/12 | 56/72 | 0 | baseline control (verbatim released prompt) |
| L6 | 0.667 | [0.552,0.765] | 0.714 | 0.50/0.93 | -4 (0.627) | 5/12 | 23/72 | 5 | reality checklist w/ physical-support test |
| L8 | 0.639 | [0.524,0.740] | 0.672 | 0.52/0.82 | -6 (0.405) | 4/12 | 27/72 | 3 | composition: L5 expectation x L6 reality tag |
| L5 | 0.583 | [0.468,0.690] | 0.627 | 0.43/0.82 | -10 (0.143) | 4/12 | 23/72 | 4 | think expectation route (two-stage in one prompt) |
| L9 | 0.528 | [0.414,0.639] | 0.562 | 0.41/0.71 | -14 (0.054) | 4/12 | 25/72 | 5 | T9 think+action anti-smooth on Qwen |
| L10 | 0.472 | [0.361,0.586] | 0.471 | 0.48/0.46 | -18 (0.005) | 3/12 | 32/72 | 7 | think velocity-only + necessity |
| L7 | 0.472 | [0.361,0.586] | 0.555 | 0.18/0.93 | -18 (0.013) | 4/12 | 10/72 | 0 | burden-of-proof: Anomaly must name a real trigger |

## Per-scenario accuracy

| scenario | n | P0 | L6 | L8 | L5 | L9 | L10 | L7 |
|---|---|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 6/19 | 8/19 | 7/19 | 8/19 | 10/19 | 3/19 |
| neg_prompt_3 | 14 | 10/14 | 7/14 | 8/14 | 5/14 | 5/14 | 7/14 | 3/14 |
| neg_prompt_4 | 4 | 4/4 | 2/4 | 1/4 | 1/4 | 4/4 | 4/4 | 0/4 |
| neg_prompt_5 | 2 | 2/2 | 2/2 | 2/2 | 1/2 | 1/2 | 0/2 | 1/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 0/4 | 0/4 | 0/4 |
| pos_prompt_0 | 6 | 4/6 | 6/6 | 6/6 | 6/6 | 4/6 | 1/6 | 6/6 |
| pos_prompt_11 | 3 | 2/3 | 3/3 | 2/3 | 1/3 | 3/3 | 3/3 | 2/3 |
| pos_prompt_4 | 4 | 0/4 | 2/4 | 3/4 | 3/4 | 2/4 | 1/4 | 4/4 |
| pos_prompt_5 | 6 | 2/6 | 6/6 | 5/6 | 6/6 | 5/6 | 2/6 | 6/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 1/4 | 1/4 | 4/4 |
| pos_prompt_8 | 5 | 0/5 | 5/5 | 3/5 | 3/5 | 5/5 | 5/5 | 4/5 |

## L6 vs P0: flips

fixed (17): prompt_3_v03.mp4, prompt_3_v12.mp4, prompt_3_v16.mp4, prompt_0.mp4, prompt_5.mp4, prompt_8.mp4, prompt_0_v19.mp4, prompt_11_v06.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (21): prompt_3.mp4, prompt_2_v01.mp4, prompt_2_v02.mp4, prompt_2_v03.mp4, prompt_2_v04.mp4, prompt_2_v05.mp4, prompt_2_v08.mp4, prompt_2_v10.mp4, prompt_2_v11.mp4, prompt_2_v12.mp4, prompt_2_v13.mp4, prompt_2_v16.mp4, prompt_2_v17.mp4, prompt_2_v20.mp4, prompt_3_v02.mp4, prompt_3_v05.mp4, prompt_3_v06.mp4, prompt_3_v07.mp4, prompt_3_v15.mp4, prompt_4_v07.mp4, prompt_4_v10.mp4
