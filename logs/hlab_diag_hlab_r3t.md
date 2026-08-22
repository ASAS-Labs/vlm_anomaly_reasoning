# H-lab diagnostics — hlab_r3t

| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | s1 trunc | s2 trunc | Unknown verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M11 | 80 | 35/28/9/8/0 | 44/80 | 61/80 | 0.15 | 0.825 | 1.00 | 61 | 0.26 | 19 | 0 | 0 | 0 |
| M8 | 80 | 34/27/12/7/0 | 43/80 | 62/80 | 0.21 | 0.850 | 1.00 | 62 | 0.33 | 18 | 0 | 0 | 0 |

## Flips vs L2 by scenario (fixed/broke)

- M11: net +10 — neg_prompt_0 +4/-0, neg_prompt_3 +2/-0, neg_prompt_4 +2/-0, neg_prompt_5 +6/-0, neg_prompt_9 +1/-4, pos_prompt_11 +0/-1, pos_prompt_2 +1/-0, pos_prompt_4 +1/-0, pos_prompt_8 +0/-3, pos_prompt_9 +1/-0
- M8: net +12 — neg_prompt_0 +4/-0, neg_prompt_3 +2/-0, neg_prompt_4 +2/-0, neg_prompt_5 +6/-0, neg_prompt_9 +1/-3, pos_prompt_11 +0/-1, pos_prompt_2 +1/-0, pos_prompt_4 +1/-0, pos_prompt_8 +0/-2, pos_prompt_9 +1/-0
