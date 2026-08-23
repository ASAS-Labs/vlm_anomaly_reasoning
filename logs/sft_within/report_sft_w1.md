# Family N — SFT stage 1 inside M8 (sft_w1) vs zero-shot anchor (sft_r1_anchor)

n = 235 clips (CV-concatenated: each clip scored by the fold model that never saw its scene); anchor = in-session zero-shot M8gt, same early_gt tree, same stage 2.

| arm | acc | 95% CI | balacc | recall / spec | stage-1 strict / lenient | stage-1 answers | Unknown / trunc |
|---|---|---|---|---|---|---|---|
| **SFT (M8 + expect_sft)** | **0.936** (220/235) | [0.897, 0.961] | **0.936** | 0.93 / 0.94 | 206 / 222 | {'continue': 133, 'wait': 18, 'stop': 67, 'slow': 17} | 0 / 0 |
| anchor (M8gt zero-shot) | 0.821 (193/235) | [0.767, 0.865] | 0.818 | 0.76 / 0.87 | 127 / 181 | {'continue': 106, 'wait': 21, 'slow': 71, 'stop': 37} | — |

Paired McNemar SFT vs anchor: +32 gained / −5 lost (net +27), p = 0.0000.
**Pre-registered verdict: PASS** (PASS iff p < 0.05 AND balacc_SFT > balacc_anchor; declare only when a second training seed also passes).

Unpaired reference hlab_r5t_M8 (T−2.5 tree, different window on 25 clips): 195/235 = 0.830.

## Per scenario

| scenario | n | anchor acc | SFT acc | net | anchor s1-lenient | SFT s1-lenient | SFT answers |
|---|---|---|---|---|---|---|---|
| neg_prompt_0 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 18} |
| neg_prompt_2 | 19 | 16/19 | 16/19 | +0 | 7 | 17 | {'continue': 17, 'stop': 2} |
| neg_prompt_3 | 15 | 15/15 | 15/15 | +0 | 15 | 15 | {'wait': 15} |
| neg_prompt_4 | 17 | 16/17 | 16/17 | +0 | 16 | 16 | {'stop': 1, 'continue': 15, 'slow': 1} |
| neg_prompt_5 | 16 | 15/16 | 15/16 | +0 | 15 | 15 | {'continue': 14, 'slow': 1, 'stop': 1} |
| neg_prompt_8 | 7 | 1/7 | 4/7 | +3 | 1 | 4 | {'stop': 4, 'continue': 2, 'slow': 1} |
| neg_prompt_9 | 18 | 3/18 | 18/18 | +15 | 3 | 18 | {'stop': 18} |
| pos_prompt_0 | 17 | 17/17 | 17/17 | +0 | 17 | 16 | {'continue': 16, 'slow': 1} |
| pos_prompt_11 | 14 | 9/14 | 9/14 | +0 | 8 | 11 | {'stop': 11, 'wait': 3} |
| pos_prompt_2 | 9 | 9/9 | 9/9 | +0 | 7 | 9 | {'continue': 9} |
| pos_prompt_4 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 17, 'slow': 1} |
| pos_prompt_5 | 17 | 17/17 | 17/17 | +0 | 17 | 17 | {'continue': 14, 'slow': 3} |
| pos_prompt_6 | 18 | 18/18 | 18/18 | +0 | 18 | 18 | {'continue': 10, 'slow': 8} |
| pos_prompt_8 | 19 | 14/19 | 19/19 | +5 | 14 | 19 | {'stop': 19} |
| pos_prompt_9 | 13 | 7/13 | 11/13 | +4 | 7 | 11 | {'continue': 1, 'stop': 11, 'slow': 1} |

## Per fold

| fold | held-out n | anchor acc | SFT acc | SFT s1-lenient | Unknown | train n | steps | final loss | s/sample | train min | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f1 | 53 | 0.774 | 0.943 | 52/53 | 0 | 182 | 46 | 0.635757327079773 | 4.97 | 30.1 | 2.44 |
| f2 | 52 | 0.827 | 0.885 | 45/52 | 0 | 183 | 46 | 0.7013968229293823 | 4.97 | 30.3 | 2.46 |
| f3 | 48 | 0.854 | 0.979 | 47/48 | 0 | 187 | 48 | 0.7876555919647217 | 5.0 | 31.2 | 2.48 |
| f4 | 43 | 0.860 | 0.977 | 42/43 | 0 | 192 | 48 | 0.6893653869628906 | 5.02 | 32.1 | 2.54 |
| f5 | 39 | 0.795 | 0.897 | 36/39 | 0 | 196 | 50 | 0.8196461796760559 | 5.01 | 32.7 | 2.56 |

## Flips vs anchor

gained (32): prompt_9.mp4, prompt_2_v17.mp4, prompt_2_v19.mp4, prompt_4_v10.mp4, prompt_5_v16.mp4, prompt_8_v02.mp4, prompt_8_v06.mp4, prompt_8_v08.mp4, prompt_9_v01.mp4, prompt_9_v02.mp4, prompt_9_v03.mp4, prompt_9_v05.mp4, prompt_9_v06.mp4, prompt_9_v07.mp4, prompt_9_v10.mp4, prompt_9_v11.mp4, prompt_9_v13.mp4, prompt_9_v14.mp4, prompt_9_v15.mp4, prompt_9_v17.mp4, prompt_9_v18.mp4, prompt_9_v19.mp4, prompt_8.mp4, prompt_8_v04.mp4, prompt_8_v11.mp4, prompt_8_v14.mp4, prompt_8_v20.mp4, prompt_9_v04.mp4, prompt_9_v14.mp4, prompt_9_v16.mp4, prompt_9_v17.mp4, prompt_9_v20.mp4

lost (5): prompt_4.mp4, prompt_2_v04.mp4, prompt_2_v12.mp4, prompt_5_v14.mp4, prompt_9_v01.mp4
