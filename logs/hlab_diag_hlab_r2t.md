# H-lab diagnostics — hlab_r2t

| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | s1 trunc | s2 trunc | Unknown verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M10 | 80 | 24/30/19/7/0 | 39/80 | 60/80 | 0.17 | 0.838 | 0.92 | 60 | 0.60 | 20 | 0 | 0 | 0 |
| M8 | 80 | 31/30/12/7/0 | 45/80 | 63/80 | 0.05 | 0.850 | 1.00 | 63 | 0.29 | 17 | 0 | 0 | 0 |
| M9 | 80 | 30/32/10/8/0 | 39/80 | 60/80 | 0.16 | 0.838 | 0.95 | 60 | 0.50 | 20 | 0 | 0 | 0 |

## Flips vs L2 by scenario (fixed/broke)

- M10: net +10 — neg_prompt_0 +4/-0, neg_prompt_3 +3/-0, neg_prompt_4 +3/-0, neg_prompt_5 +4/-0, neg_prompt_8 +0/-1, neg_prompt_9 +0/-4, pos_prompt_11 +0/-1, pos_prompt_4 +2/-0, pos_prompt_9 +2/-2
- M8: net +11 — neg_prompt_0 +4/-0, neg_prompt_3 +3/-0, neg_prompt_4 +3/-0, neg_prompt_5 +6/-0, neg_prompt_8 +0/-1, neg_prompt_9 +1/-4, pos_prompt_11 +0/-2, pos_prompt_4 +2/-0, pos_prompt_8 +0/-2, pos_prompt_9 +1/-0
- M9: net +10 — neg_prompt_0 +4/-0, neg_prompt_2 +0/-1, neg_prompt_3 +3/-0, neg_prompt_4 +3/-0, neg_prompt_5 +6/-0, neg_prompt_8 +0/-1, neg_prompt_9 +0/-3, pos_prompt_0 +0/-1, pos_prompt_11 +0/-2, pos_prompt_4 +2/-0, pos_prompt_9 +1/-1
