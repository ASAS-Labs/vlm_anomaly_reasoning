# Prompt lab — round 1 (qlab_r1d)

n=72 paired clips; baseline=P0 acc=0.625

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| L2 | 0.694 | [0.580,0.789] | 0.750 | 0.50/1.00 | +5 (0.405) | 4/12 | 22/72 | 0 | P0 + depiction/necessity guard line (min delta) |
| P0 | 0.625 | [0.510,0.728] | 0.602 | 0.70/0.50 | +0 (1.000) | 0/12 | 45/72 | 0 | baseline control (verbatim released prompt) |
| L1 | 0.431 | [0.323,0.546] | 0.463 | 0.32/0.61 | -14 (0.007) | 2/12 | 25/72 | 0 | direct expectation route (EXPECT/DID/verdict) |
| L3 | 0.375 | [0.272,0.490] | 0.443 | 0.14/0.75 | -18 (0.008) | 4/12 | 13/72 | 0 | P4 anti-smooth action framing on Qwen |
| L4 | 0.292 | [0.199,0.405] | 0.343 | 0.11/0.57 | -24 (0.000) | 4/12 | 17/72 | 0 | velocity-only direct + necessity framing |

## Per-scenario accuracy

| scenario | n | L2 | P0 | L1 | L3 | L4 |
|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 19/19 | 19/19 | 4/19 | 2/19 | 1/19 |
| neg_prompt_3 | 14 | 0/14 | 1/14 | 0/14 | 0/14 | 0/14 |
| neg_prompt_4 | 4 | 0/4 | 4/4 | 4/4 | 0/4 | 0/4 |
| neg_prompt_5 | 2 | 0/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| neg_prompt_8 | 1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 |
| neg_prompt_9 | 4 | 2/4 | 4/4 | 3/4 | 4/4 | 4/4 |
| pos_prompt_0 | 6 | 6/6 | 6/6 | 6/6 | 4/6 | 3/6 |
| pos_prompt_11 | 3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| pos_prompt_4 | 4 | 4/4 | 1/4 | 0/4 | 2/4 | 2/4 |
| pos_prompt_5 | 6 | 6/6 | 1/6 | 0/6 | 4/6 | 2/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 3/4 | 1/4 |
| pos_prompt_8 | 5 | 5/5 | 0/5 | 4/5 | 5/5 | 5/5 |

## L2 vs P0: flips

fixed (14): prompt_5.mp4, prompt_8.mp4, prompt_11_v06.mp4, prompt_4_v02.mp4, prompt_4_v03.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v05.mp4, prompt_5_v06.mp4, prompt_5_v11.mp4, prompt_8_v01.mp4, prompt_8_v03.mp4, prompt_8_v07.mp4, prompt_8_v14.mp4
broke (9): prompt_5.mp4, prompt_9.mp4, prompt_3_v19.mp4, prompt_4_v01.mp4, prompt_4_v07.mp4, prompt_4_v10.mp4, prompt_4_v17.mp4, prompt_5_v15.mp4, prompt_9_v14.mp4
