# H-lab diagnostics — hlab_r6t

| arm | n | stage-1 answers (cont/slow/stop/wait/unk) | strict | lenient | twin divergence | verdict acc | acc | stage-1 ok | acc | stage-1 wrong | s1 trunc | s2 trunc | Unknown verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M8 | 40 | 12/21/3/4/0 | 2/40 | 2/40 | 0.12 | 0.075 | 1.00 | 2 | 0.03 | 38 | 0 | 0 | 0 |
| M8w10 | 40 | 10/12/14/4/0 | 12/40 | 12/40 | 0.19 | 0.350 | 1.00 | 12 | 0.07 | 28 | 0 | 0 | 0 |
| M8w15 | 40 | 10/15/11/4/0 | 11/40 | 11/40 | 0.12 | 0.300 | 1.00 | 11 | 0.03 | 29 | 0 | 0 | 0 |

## Flips vs M8 by scenario (fixed/broke)

- M8w10: net +11 — neg_prompt_2 +1/-0, neg_prompt_8 +1/-0, neg_prompt_9 +4/-0, pos_prompt_8 +4/-0, pos_prompt_9 +1/-0
- M8w15: net +9 — neg_prompt_9 +2/-0, pos_prompt_11 +1/-0, pos_prompt_8 +4/-0, pos_prompt_9 +2/-0
