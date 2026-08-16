# Subset evaluation report

72-clip prompt-video-ID agreement subset (44 anomaly / 28 normal), fixed v1_resample trajectories, example-free think prompt.
Majority-class baseline (always Anomaly): **61.1%**. n=72 paired; Wilson 95% CIs span roughly ±11 points.

| run | acc | 95% CI | P | R | spec | F1 | lat |
|---|---|---|---|---|---|---|---|
| direct/action_grounding | 0.569 | [0.454, 0.677] | 0.686 | 0.545 | 0.607 | 0.608 | 0.07s |
| direct/action_grounding_velocity | 0.431 | [0.323, 0.546] | 0.571 | 0.273 | 0.679 | 0.369 | 0.06s |
| direct/no_action_grounding | 0.639 | [0.524, 0.740] | 0.696 | 0.727 | 0.500 | 0.711 | 0.40s |
| think/action_grounding | 0.458 | [0.348, 0.573] | 0.581 | 0.409 | 0.536 | 0.480 | 1.97s |
| think/action_grounding_velocity | 0.472 | [0.361, 0.586] | 0.594 | 0.432 | 0.536 | 0.500 | 1.89s |
| think/no_action_grounding | 0.583 | [0.468, 0.690] | 0.733 | 0.500 | 0.714 | 0.595 | 1.42s |

## Paired comparisons (McNemar, exact two-sided)

| comparison | gains | loses | net | p |
|---|---|---|---|---|
| direct/action_grounding vs direct/no_action_grounding | 5 | 10 | -5 | 0.302 |
| direct/action_grounding_velocity vs direct/no_action_grounding | 7 | 22 | -15 | 0.00813 |
| direct/action_grounding_velocity vs direct/action_grounding | 5 | 15 | -10 | 0.0414 |
| think/action_grounding vs think/no_action_grounding | 10 | 19 | -9 | 0.136 |
| think/action_grounding_velocity vs think/no_action_grounding | 11 | 19 | -8 | 0.2 |
| think/action_grounding_velocity vs think/action_grounding | 17 | 16 | +1 | 1 |
| think/no_action_grounding vs direct/no_action_grounding | 13 | 17 | -4 | 0.585 |
| think/action_grounding vs direct/action_grounding | 14 | 22 | -8 | 0.243 |

## Per-scenario accuracy

| scenario | n | direct/action_grounding | direct/action_grounding_velocity | direct/no_action_grounding | think/action_grounding | think/action_grounding_velocity | think/no_action_grounding |
|---|---|---|---|---|---|---|---|
| neg_prompt_2 | 19 | 16/19 | 10/19 | 17/19 | 8/19 | 9/19 | 12/19 |
| neg_prompt_3 | 14 | 2/14 | 0/14 | 4/14 | 4/14 | 6/14 | 4/14 |
| neg_prompt_4 | 4 | 3/4 | 1/4 | 4/4 | 2/4 | 3/4 | 1/4 |
| neg_prompt_5 | 2 | 1/2 | 0/2 | 2/2 | 1/2 | 0/2 | 1/2 |
| neg_prompt_8 | 1 | 1/1 | 0/1 | 1/1 | 1/1 | 0/1 | 1/1 |
| neg_prompt_9 | 4 | 1/4 | 1/4 | 4/4 | 2/4 | 1/4 | 3/4 |
| pos_prompt_0 | 6 | 6/6 | 5/6 | 6/6 | 1/6 | 1/6 | 3/6 |
| pos_prompt_11 | 3 | 3/3 | 2/3 | 3/3 | 2/3 | 2/3 | 3/3 |
| pos_prompt_4 | 4 | 0/4 | 0/4 | 0/4 | 1/4 | 2/4 | 2/4 |
| pos_prompt_5 | 6 | 4/6 | 3/6 | 1/6 | 5/6 | 3/6 | 3/6 |
| pos_prompt_6 | 4 | 4/4 | 4/4 | 4/4 | 3/4 | 3/4 | 4/4 |
| pos_prompt_8 | 5 | 0/5 | 5/5 | 0/5 | 3/5 | 4/5 | 5/5 |
