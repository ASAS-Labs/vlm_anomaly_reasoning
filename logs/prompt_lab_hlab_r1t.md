# Prompt lab — round 1 (hlab_r1t)

n=80 paired clips; baseline=L2 acc=0.750

| variant | acc | 95% CI | balacc | rec/spec | vs base net (p) | breadth | anomaly-verdicts | trunc | hypothesis |
|---|---|---|---|---|---|---|---|---|---|
| M2 | 0.838 | [0.742,0.903] | 0.837 | 0.82/0.85 | +7 (0.230) | 5/15 | 39/80 | 0 | narrative rendering removes numeric reading from comparison |
| M4 | 0.775 | [0.672,0.853] | 0.775 | 0.65/0.90 | +2 (0.845) | 4/15 | 30/80 | 0 | guard concept + named feature at the expectation step |
| M5 | 0.762 | [0.659,0.842] | 0.762 | 0.68/0.85 | +1 (1.000) | 3/15 | 33/80 | 0 | guard line as a verdict-time expectation re-check |
| L2 | 0.750 | [0.645,0.832] | 0.750 | 0.53/0.97 | +0 (1.000) | 0/15 | 22/80 | 0 | P0 + depiction/necessity guard line (min delta) |
| M1 | 0.675 | [0.566,0.768] | 0.675 | 0.53/0.82 | -6 (0.307) | 3/15 | 28/80 | 0 | explicit comparison rule + tolerances fixes the comparator |
| M3 | 0.662 | [0.554,0.757] | 0.663 | 0.53/0.80 | -7 (0.248) | 2/15 | 29/80 | 0 | heading channel is noise for speed-class matching |
| M0 | 0.613 | [0.503,0.712] | 0.613 | 0.55/0.68 | -11 (0.080) | 5/15 | 35/80 | 0 | H3 control: verbatim stage-1/stage-2 texts @ T-2.5 |
| M6 | 0.600 | [0.490,0.700] | 0.600 | 0.57/0.62 | -12 (0.065) | 5/15 | 38/80 | 0 | window ladder: M0 prompts at a 1.5 s stage-1 window |
| M7 | 0.588 | [0.478,0.689] | 0.588 | 0.55/0.62 | -13 (0.029) | 4/15 | 37/80 | 0 | window ladder: M0 prompts at a 1.0 s stage-1 window |

## Per-scenario accuracy

| scenario | n | M2 | M4 | M5 | L2 | M1 | M3 | M0 | M6 | M7 |
|---|---|---|---|---|---|---|---|---|---|---|
| neg_prompt_0 | 7 | 7/7 | 5/7 | 7/7 | 4/7 | 5/7 | 4/7 | 7/7 | 6/7 | 7/7 |
| neg_prompt_2 | 7 | 5/7 | 5/7 | 6/7 | 6/7 | 2/7 | 1/7 | 2/7 | 1/7 | 1/7 |
| neg_prompt_3 | 5 | 5/5 | 5/5 | 5/5 | 2/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| neg_prompt_4 | 6 | 6/6 | 4/6 | 2/6 | 5/6 | 3/6 | 4/6 | 2/6 | 3/6 | 4/6 |
| neg_prompt_5 | 6 | 6/6 | 5/6 | 3/6 | 0/6 | 4/6 | 4/6 | 1/6 | 2/6 | 1/6 |
| neg_prompt_8 | 2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 1/2 | 1/2 | 1/2 |
| neg_prompt_9 | 7 | 4/7 | 2/7 | 4/7 | 4/7 | 2/7 | 3/7 | 4/7 | 5/7 | 3/7 |
| pos_prompt_0 | 5 | 5/5 | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | 2/5 | 2/5 | 1/5 |
| pos_prompt_11 | 5 | 3/5 | 3/5 | 4/5 | 5/5 | 3/5 | 4/5 | 5/5 | 5/5 | 5/5 |
| pos_prompt_2 | 3 | 1/3 | 3/3 | 3/3 | 3/3 | 2/3 | 1/3 | 0/3 | 2/3 | 3/3 |
| pos_prompt_4 | 6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 2/6 | 2/6 | 1/6 |
| pos_prompt_5 | 5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 4/5 | 4/5 | 4/5 |
| pos_prompt_6 | 6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 4/6 | 4/6 | 3/6 |
| pos_prompt_8 | 6 | 4/6 | 4/6 | 4/6 | 6/6 | 4/6 | 3/6 | 6/6 | 4/6 | 6/6 |
| pos_prompt_9 | 4 | 4/4 | 4/4 | 2/4 | 3/4 | 2/4 | 2/4 | 4/4 | 2/4 | 2/4 |

## M2 vs L2: flips

fixed (16): prompt_0.mp4, prompt_3.mp4, prompt_5.mp4, prompt_0_v01.mp4, prompt_0_v10.mp4, prompt_3_v07.mp4, prompt_3_v11.mp4, prompt_4_v20.mp4, prompt_5_v01.mp4, prompt_5_v03.mp4, prompt_5_v07.mp4, prompt_5_v09.mp4, prompt_5_v12.mp4, prompt_9_v18.mp4, prompt_9_v20.mp4, prompt_9_v16.mp4
broke (9): prompt_2_v13.mp4, prompt_9_v02.mp4, prompt_9_v05.mp4, prompt_8.mp4, prompt_11_v12.mp4, prompt_11_v20.mp4, prompt_2_v01.mp4, prompt_2_v05.mp4, prompt_8_v18.mp4
