# Open-VLM pilot report

72-clip agreement subset, 720p↑ @ 8 fps. Primary discriminator: expect_early strict (Cosmos-Nano bar 18/72). qwen3vl32t's plain verdict IS its think verdict (always-think model, no off-switch).

| model | early strict | early lenient | full strict | full lenient | verdict acc | rec/spec | verdict think | think rec/spec |
|---|---|---|---|---|---|---|---|---|
| Cosmos3-Nano (bar) | 18/72 | 38/72 | 22/72 | 40/72 | 0.736 | — | 0.500 | — |
| Cosmos3-Super | 8/72 | 26/72 | 12/72 | 27/72 | — | — | — | — |
| Qwen3.8-27B | 31/72 | 46/72 | 30/72 | 44/72 | 0.597 | 0.68/0.46 | 0.815 | 0.97/0.53 |
| Qwen3.6-27B | 30/72 | 41/72 | 28/72 | 35/72 | 0.694 | 0.86/0.43 | 0.698 | 1.00/0.10 |
| Qwen3.5-27B | 29/72 | 42/72 | 32/72 | 38/72 | 0.639 | 0.82/0.36 | 0.647 | 1.00/0.04 |
| Qwen3-VL-32B-Thinking | 19/72 | 37/72 | 20/72 | 37/72 | 0.681 | 0.89/0.36 | — | — |
| GLM-4.6V-Flash | 11/72 | 28/72 | 13/72 | 32/72 | 0.528 | 0.25/0.96 | 0.597 | 0.50/0.75 |
| InternVL3_5-38B | 22/72 | 34/72 | 39/72 | 46/72 | 0.653 | 1.00/0.11 | 0.528 | 0.61/0.39 |

## Parse/latency notes

- qwen38 expect_early: 3 unknown, 3 truncated, mean latency 24.3s
- qwen38 expect_full: 7 unknown, 7 truncated, mean latency 39.3s
- qwen38 verdict_think: 18 unknown, 18 truncated, mean latency 49.3s
- qwen36 expect_early: 11 unknown, 11 truncated, mean latency 38.5s
- qwen36 expect_full: 11 unknown, 11 truncated, mean latency 41.4s
- qwen36 verdict_think: 9 unknown, 9 truncated, mean latency 36.3s
- qwen35 expect_early: 7 unknown, 7 truncated, mean latency 39.8s
- qwen35 expect_full: 10 unknown, 10 truncated, mean latency 42.4s
- qwen35 verdict_think: 4 unknown, 4 truncated, mean latency 30.2s
- internvl35 verdict_think: 0 unknown, 1 truncated, mean latency 21.2s
