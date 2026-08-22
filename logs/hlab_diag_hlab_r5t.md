# H-lab diagnostics — hlab_r5t

| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | s1 trunc | s2 trunc | Unknown verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M8 | 235 | 102/78/35/20/0 | 128/235 | 184/235 | 0.26 | 0.830 | 1.00 | 184 | 0.22 | 51 | 0 | 0 | 0 |

## Flips vs L2 by scenario (fixed/broke)

- L2q: net +7 — neg_prompt_0 +1/-2, neg_prompt_2 +1/-1, neg_prompt_3 +5/-1, neg_prompt_4 +1/-4, neg_prompt_5 +2/-0, neg_prompt_8 +2/-0, neg_prompt_9 +2/-1, pos_prompt_11 +0/-1, pos_prompt_2 +1/-0, pos_prompt_4 +1/-0, pos_prompt_5 +0/-1, pos_prompt_8 +0/-1, pos_prompt_9 +5/-2
- M8: net +27 — neg_prompt_0 +7/-0, neg_prompt_2 +3/-2, neg_prompt_3 +11/-0, neg_prompt_4 +3/-0, neg_prompt_5 +16/-0, neg_prompt_9 +2/-9, pos_prompt_11 +0/-4, pos_prompt_2 +2/-0, pos_prompt_4 +1/-0, pos_prompt_8 +0/-4, pos_prompt_9 +3/-2
