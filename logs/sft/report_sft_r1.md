# Family N — SFT stage 1 inside M8 (sft_r1) vs zero-shot anchor (sft_r1_anchor)

n = 235 clips (CV-concatenated: each clip scored by the fold model that never saw its scene); anchor = in-session zero-shot M8gt, same early_gt tree, same stage 2.

| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient | stage-1 answers | Unknown / trunc |
|---|---|---|---|---|---|---|---|
| **SFT (M8 + expect_sft)** | **0.736** (173/235) | [0.676, 0.788] | **0.731** | 0.65 / 0.81 | 130 / 151 | {'continue': 156, 'slow': 17, 'wait': 23, 'stop': 39} | 0 / 0 |
| anchor (M8gt zero-shot) | 0.821 (193/235) | [0.767, 0.865] | 0.818 | 0.76 / 0.87 | 127 / 181 | {'continue': 106, 'wait': 21, 'slow': 71, 'stop': 37} | — |

Paired McNemar SFT vs anchor: +7 gained / −27 lost (net -20), p = 0.0008.
**Pre-registered verdict: FAIL** (PASS iff p < 0.05 AND balacc_SFT > balacc_anchor; declare only when a second training seed also passes).

Unpaired reference hlab_r5t_M8 (T−2.5 tree, different window on 25 clips): 195/235 = 0.830.

## Per scenario

| scenario | n | anchor acc | SFT acc | net | anchor s1-lenient | SFT s1-lenient | SFT answers |
|---|---|---|---|---|---|---|---|
| neg_prompt_0 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 18} |
| neg_prompt_2 | 19 | 16/19 | 13/19 | -3 | 7 | 7 | {'slow': 6, 'stop': 5, 'continue': 7, 'wait': 1} |
| neg_prompt_3 | 15 | 15/15 | 15/15 | +0 | 15 | 8 | {'wait': 8, 'stop': 7} |
| neg_prompt_4 | 17 | 16/17 | 17/17 | +1 | 16 | 17 | {'continue': 16, 'slow': 1} |
| neg_prompt_5 | 16 | 15/16 | 7/16 | -8 | 15 | 7 | {'stop': 9, 'continue': 7} |
| neg_prompt_8 | 7 | 1/7 | 1/7 | +0 | 1 | 1 | {'slow': 3, 'stop': 1, 'continue': 3} |
| neg_prompt_9 | 18 | 3/18 | 1/18 | -2 | 3 | 1 | {'continue': 17, 'stop': 1} |
| pos_prompt_0 | 17 | 17/17 | 17/17 | +0 | 17 | 17 | {'continue': 17} |
| pos_prompt_11 | 14 | 9/14 | 8/14 | -1 | 8 | 0 | {'wait': 14} |
| pos_prompt_2 | 9 | 9/9 | 9/9 | +0 | 7 | 8 | {'continue': 8, 'slow': 1} |
| pos_prompt_4 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 18} |
| pos_prompt_5 | 17 | 17/17 | 16/17 | -1 | 17 | 16 | {'continue': 14, 'slow': 2, 'stop': 1} |
| pos_prompt_6 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 18} |
| pos_prompt_8 | 19 | 14/19 | 15/19 | +1 | 14 | 15 | {'slow': 4, 'stop': 15} |
| pos_prompt_9 | 13 | 7/13 | 0/13 | -7 | 7 | 0 | {'continue': 13} |

## Per fold

| fold | held-out n | anchor acc | SFT acc | SFT s1-lenient | Unknown | train n | steps | final loss | s/sample | train min | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f1 | 49 | 0.571 | 0.388 | 19/49 | 0 | 186 | 48 | 0.7426043748855591 | 5.01 | 31.0 | 2.48 |
| f2 | 48 | 0.979 | 0.792 | 31/48 | 0 | 187 | 48 | 0.8622802495956421 | 5.0 | 31.2 | 2.49 |
| f3 | 49 | 0.898 | 0.878 | 35/49 | 0 | 186 | 48 | 0.8347715735435486 | 4.99 | 30.9 | 2.55 |
| f4 | 35 | 0.971 | 1.000 | 35/35 | 0 | 200 | 50 | 0.8039988875389099 | 5.03 | 33.5 | 2.6 |
| f5 | 54 | 0.741 | 0.704 | 31/54 | 0 | 181 | 46 | 0.9619825482368469 | 5.04 | 30.4 | 2.46 |

## Flips vs anchor

gained (7): prompt_2_v17.mp4, prompt_2_v19.mp4, prompt_4_v10.mp4, prompt_11_v03.mp4, prompt_8_v04.mp4, prompt_8_v11.mp4, prompt_8_v20.mp4

lost (27): prompt_5.mp4, prompt_2_v01.mp4, prompt_2_v02.mp4, prompt_2_v04.mp4, prompt_2_v08.mp4, prompt_2_v12.mp4, prompt_5_v03.mp4, prompt_5_v04.mp4, prompt_5_v05.mp4, prompt_5_v09.mp4, prompt_5_v12.mp4, prompt_5_v14.mp4, prompt_5_v15.mp4, prompt_9_v08.mp4, prompt_9_v09.mp4, prompt_11_v04.mp4, prompt_11_v11.mp4, prompt_5_v16.mp4, prompt_8_v15.mp4, prompt_8_v18.mp4, prompt_9_v01.mp4, prompt_9_v03.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v08.mp4, prompt_9_v09.mp4, prompt_9_v13.mp4
