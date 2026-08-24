# Family N — SFT stage 1 inside M8 (sft_t1) vs zero-shot anchor (sft_r1_anchor)

n = 235 clips (CV-concatenated: each clip scored by the fold model that never saw its scene); anchor = in-session zero-shot M8gt, same early_gt tree, same stage 2.

| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient | stage-1 answers | Unknown / s2-trunc / s1-trunc | median s1 trace chars |
|---|---|---|---|---|---|---|---|---|
| **SFT (M8 + expect_sft_think)** | **0.728** (171/235) | [0.667, 0.781] | **0.722** | 0.63 / 0.82 | 138 / 165 | {'continue': 150, 'stop': 45, 'wait': 18, 'slow': 22} | 5 / 3 / 0 | 1001 |
| anchor (M8gt zero-shot) | 0.821 (193/235) | [0.767, 0.865] | 0.818 | 0.76 / 0.87 | 127 / 181 | {'continue': 106, 'wait': 21, 'slow': 71, 'stop': 37} | — | 5799 |

Paired McNemar SFT vs anchor: +8 gained / −30 lost (net -22), p = 0.0005.
**Pre-registered verdict: FAIL** (PASS iff p < 0.05 AND balacc_SFT > balacc_anchor; declare only when a second training seed also passes).

Unpaired reference hlab_r5t_M8 (T−2.5 tree, different window on 25 clips): 195/235 = 0.830.

## Per scenario

| scenario | n | anchor acc | SFT acc | net | anchor s1-lenient | SFT s1-lenient | SFT answers |
|---|---|---|---|---|---|---|---|
| neg_prompt_0 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 18} |
| neg_prompt_2 | 19 | 16/19 | 9/19 | -7 | 7 | 6 | {'stop': 10, 'continue': 6, 'slow': 3} |
| neg_prompt_3 | 15 | 15/15 | 14/15 | -1 | 15 | 15 | {'wait': 15} |
| neg_prompt_4 | 17 | 16/17 | 15/17 | -1 | 16 | 15 | {'continue': 14, 'slow': 1, 'stop': 2} |
| neg_prompt_5 | 16 | 15/16 | 11/16 | -4 | 15 | 11 | {'stop': 5, 'slow': 5, 'continue': 6} |
| neg_prompt_8 | 7 | 1/7 | 1/7 | +0 | 1 | 1 | {'slow': 3, 'stop': 1, 'continue': 3} |
| neg_prompt_9 | 18 | 3/18 | 1/18 | -2 | 3 | 1 | {'continue': 17, 'stop': 1} |
| pos_prompt_0 | 17 | 17/17 | 17/17 | +0 | 17 | 15 | {'continue': 15, 'slow': 2} |
| pos_prompt_11 | 14 | 9/14 | 9/14 | +0 | 8 | 7 | {'continue': 3, 'wait': 3, 'stop': 7, 'slow': 1} |
| pos_prompt_2 | 9 | 9/9 | 9/9 | +0 | 7 | 6 | {'slow': 3, 'continue': 6} |
| pos_prompt_4 | 18 | 18/18 | 17/18 | -1 | 18 | 18 | {'continue': 18} |
| pos_prompt_5 | 17 | 17/17 | 15/17 | -2 | 17 | 16 | {'continue': 13, 'slow': 3, 'stop': 1} |
| pos_prompt_6 | 18 | 18/18 | 17/18 | -1 | 18 | 18 | {'continue': 18} |
| pos_prompt_8 | 19 | 14/19 | 18/19 | +4 | 14 | 18 | {'slow': 1, 'stop': 18} |
| pos_prompt_9 | 13 | 7/13 | 0/13 | -7 | 7 | 0 | {'continue': 13} |

## Per fold

| fold | held-out n | anchor acc | SFT acc | SFT s1-lenient | Unknown | train n | steps | final loss | s/sample | train min | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f1 | 49 | 0.571 | 0.367 | 19/49 | 2 | 186 | 48 | 0.606515645980835 | 5.15 | 31.9 | 2.81 |
| f2 | 48 | 0.979 | 0.833 | 42/48 | 1 | 187 | 48 | 0.7558732628822327 | 5.16 | 32.2 | 2.59 |
| f3 | 49 | 0.898 | 0.898 | 40/49 | 1 | 186 | 48 | 0.7101820707321167 | 5.17 | 32.1 | 2.87 |
| f4 | 35 | 0.971 | 0.914 | 33/35 | 1 | 200 | 50 | 0.7018190622329712 | 5.23 | 34.9 | 3.02 |
| f5 | 54 | 0.741 | 0.685 | 31/54 | 0 | 181 | 46 | 0.792292594909668 | 0.0 | 0.0 | 0.46 |

## Flips vs anchor

gained (8): prompt_2_v05.mp4, prompt_4_v10.mp4, prompt_11.mp4, prompt_11_v12.mp4, prompt_8_v04.mp4, prompt_8_v11.mp4, prompt_8_v14.mp4, prompt_8_v20.mp4

lost (30): prompt_2.mp4, prompt_5.mp4, prompt_2_v04.mp4, prompt_2_v08.mp4, prompt_2_v11.mp4, prompt_2_v12.mp4, prompt_2_v13.mp4, prompt_2_v16.mp4, prompt_2_v20.mp4, prompt_3_v16.mp4, prompt_4_v06.mp4, prompt_4_v07.mp4, prompt_5_v01.mp4, prompt_5_v09.mp4, prompt_5_v13.mp4, prompt_9_v08.mp4, prompt_9_v09.mp4, prompt_11_v07.mp4, prompt_11_v14.mp4, prompt_4_v16.mp4, prompt_5_v11.mp4, prompt_5_v16.mp4, prompt_6_v08.mp4, prompt_9_v01.mp4, prompt_9_v03.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v08.mp4, prompt_9_v09.mp4, prompt_9_v13.mp4
