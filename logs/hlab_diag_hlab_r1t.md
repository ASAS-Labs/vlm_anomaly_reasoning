# H-lab diagnostics — hlab_r1t

| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | s1 trunc | s2 trunc | Unknown verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M0 | 80 | 25/29/19/7/0 | 40/80 | 63/80 | 0.18 | 0.613 | 0.70 | 63 | 0.29 | 17 | 0 | 0 | 0 |
| M1 | 80 | 24/33/16/7/0 | 37/80 | 58/80 | 0.17 | 0.675 | 0.83 | 58 | 0.27 | 22 | 0 | 0 | 0 |
| M2 | 80 | 25/29/19/7/0 | 42/80 | 63/80 | 0.14 | 0.838 | 1.00 | 63 | 0.24 | 17 | 0 | 0 | 0 |
| M3 | 80 | 23/29/21/7/0 | 39/80 | 60/80 | 0.15 | 0.662 | 0.82 | 60 | 0.20 | 20 | 0 | 0 | 0 |
| M4 | 80 | 35/26/12/7/0 | 43/80 | 64/80 | 0.16 | 0.775 | 0.86 | 64 | 0.44 | 16 | 0 | 0 | 0 |
| M5 | 80 | 24/30/19/7/0 | 40/80 | 62/80 | 0.11 | 0.762 | 0.79 | 62 | 0.67 | 18 | 0 | 0 | 0 |
| M6 | 80 | 31/33/9/7/0 | 34/80 | 54/80 | 0.17 | 0.600 | 0.67 | 54 | 0.46 | 26 | 0 | 0 | 0 |
| M7 | 80 | 32/35/6/7/0 | 30/80 | 51/80 | 0.29 | 0.588 | 0.61 | 51 | 0.55 | 29 | 0 | 0 | 0 |

## Flips vs L2 by scenario (fixed/broke)

- M0: net -11 — neg_prompt_0 +3/-0, neg_prompt_2 +0/-4, neg_prompt_3 +3/-0, neg_prompt_4 +1/-4, neg_prompt_5 +1/-0, neg_prompt_8 +1/-0, neg_prompt_9 +1/-1, pos_prompt_0 +0/-3, pos_prompt_2 +0/-3, pos_prompt_4 +0/-4, pos_prompt_5 +0/-1, pos_prompt_6 +0/-2, pos_prompt_9 +1/-0
- M1: net -6 — neg_prompt_0 +1/-0, neg_prompt_2 +0/-4, neg_prompt_3 +3/-0, neg_prompt_4 +1/-3, neg_prompt_5 +4/-0, neg_prompt_9 +0/-2, pos_prompt_11 +0/-2, pos_prompt_2 +0/-1, pos_prompt_8 +0/-2, pos_prompt_9 +0/-1
- M2: net +7 — neg_prompt_0 +3/-0, neg_prompt_2 +0/-1, neg_prompt_3 +3/-0, neg_prompt_4 +1/-0, neg_prompt_5 +6/-0, neg_prompt_9 +2/-2, pos_prompt_11 +0/-2, pos_prompt_2 +0/-2, pos_prompt_8 +0/-2, pos_prompt_9 +1/-0
- M3: net -7 — neg_prompt_2 +0/-5, neg_prompt_3 +3/-0, neg_prompt_4 +1/-2, neg_prompt_5 +4/-0, neg_prompt_9 +2/-3, pos_prompt_11 +0/-1, pos_prompt_2 +0/-2, pos_prompt_8 +0/-3, pos_prompt_9 +0/-1
- M4: net +2 — neg_prompt_0 +1/-0, neg_prompt_2 +1/-2, neg_prompt_3 +3/-0, neg_prompt_4 +1/-2, neg_prompt_5 +5/-0, neg_prompt_9 +2/-4, pos_prompt_11 +0/-2, pos_prompt_8 +0/-2, pos_prompt_9 +1/-0
- M5: net +1 — neg_prompt_0 +3/-0, neg_prompt_2 +1/-1, neg_prompt_3 +3/-0, neg_prompt_4 +0/-3, neg_prompt_5 +3/-0, neg_prompt_9 +2/-2, pos_prompt_0 +0/-1, pos_prompt_11 +0/-1, pos_prompt_8 +0/-2, pos_prompt_9 +0/-1
- M6: net -12 — neg_prompt_0 +2/-0, neg_prompt_2 +0/-5, neg_prompt_3 +3/-0, neg_prompt_4 +1/-3, neg_prompt_5 +2/-0, neg_prompt_8 +1/-0, neg_prompt_9 +2/-1, pos_prompt_0 +0/-3, pos_prompt_2 +0/-1, pos_prompt_4 +0/-4, pos_prompt_5 +0/-1, pos_prompt_6 +0/-2, pos_prompt_8 +0/-2, pos_prompt_9 +1/-2
- M7: net -13 — neg_prompt_0 +3/-0, neg_prompt_2 +0/-5, neg_prompt_3 +3/-0, neg_prompt_4 +1/-2, neg_prompt_5 +1/-0, neg_prompt_8 +1/-0, neg_prompt_9 +0/-1, pos_prompt_0 +0/-4, pos_prompt_4 +0/-5, pos_prompt_5 +0/-1, pos_prompt_6 +0/-3, pos_prompt_9 +0/-1
