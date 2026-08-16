# VLM Model Options — Candidates to Replace Cosmos3

Research notes (Aug 2026) on open-source VLMs to try for the driving
semantic-anomaly reasoning task, given the findings in `VLM_FINDINGS.md`.

## What the next model must fix

The failure is precisely localized (Parts 7–9): perception is saturated (72/72
scene probes), but **normative driving policy** ("what should a correct driver
do") sits at 25–53%, and discrimination is prompt-invariant (~0.70 balanced
accuracy across 13 wordings). Cosmos3-Nano/Super are NVIDIA Cosmos-Reason
models — post-trains of Qwen VL bases tuned for *physical* common sense
(motion, contact, feasibility), not *semantic/normative* judgment ("a stop sign
printed on a shirt is not a traffic control device"). A frontier general VLM
with RL-trained reasoning is a genuinely different distribution, not just a
bigger Cosmos — the H4/H5 "scale doesn't fix semantics" result does not
automatically transfer.

Requirements: native video input, strong world-knowledge reasoning,
vLLM-servable (the whole harness — `--media-io-kwargs`, verdict parser, probe
suite — is built on a vLLM OpenAI endpoint), runnable on vast.ai H200s.

## Candidates, in order

### 1. Qwen3.5 (Feb 2026) — top pick

- Open weights (Apache 2.0), natively multimodal with video input, fully
  supported by vLLM with the same OpenAI-compatible video API already in use.
- Sizes span ~0.8B to a 397B-A17B MoE flagship; dense mid-sizes include
  [Qwen3.5-27B](https://huggingface.co/Qwen/Qwen3.5-27B).
- Key signal for this task: large jump specifically in **embodied reasoning
  (ERQA 67.5 vs 52.5 for Qwen3-VL)** and video understanding (Video-MME 87.5)
  — embodied/normative reasoning is exactly the localized deficit.
- Cosmos3 is Qwen-based, so processor quirks and frame-sampling setup carry
  over almost unchanged.
- Sizing: 27B on 1×H200; escalate to 122B/235B/397B-A17B MoEs (2–4×H200, FP8)
  only if the small one shows signal.

### 2. Qwen3-VL-32B-Thinking / 235B-A22B-Thinking

- Proven late-2025 generation ([GitHub](https://github.com/qwenlm/qwen3-vl)):
  Instruct and Thinking editions at 2B–235B, Apache 2.0, vLLM ≥0.11, FP8
  checkpoints published, timestamp-aligned temporal modeling.
- 32B-Thinking fits one H200 and is a direct "same architecture family,
  general post-training instead of Cosmos post-training" ablation — the
  cleanest test of whether Cosmos post-training itself is what costs judgment.

### 3. GLM-4.6V (106B-A12B MoE) — strongest non-Qwen contender

- Z.ai's [GLM-4.6V series](https://github.com/zai-org/GLM-V)
  ([release coverage](https://venturebeat.com/ai/z-ai-debuts-open-source-glm-4-6v-a-native-tool-calling-vision-model-for)):
  thinking-mode VLM trained with scalable multimodal RL, video ingestion with
  explicit timestamp tokens (relevant to the `neg_prompt_3` motion-onset blind
  spot), 128K context.
- Sizing: FP8 fits ~1×H200, BF16 on 2. A 9B Flash variant exists for cheap
  pilots. Predecessor GLM-4.5V was widely rated the strongest open vision
  reasoner of its cycle
  ([BentoML 2026 VLM guide](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models)).

### 4. InternVL3.5 (38B dense or 241B-A28B)

- Shanghai AI Lab ([paper](https://arxiv.org/html/2508.18265v1),
  [HF](https://huggingface.co/OpenGVLab/InternVL3_5-38B)) with Cascade-RL
  reasoning training; video input works in vLLM
  ([recipe](https://docs.vllm.ai/projects/recipes/en/latest/InternVL/InternVL3_5.html)),
  MIT-licensed code with open weights.
- 38B runs on 1×H200. A solid third architecture family for checking whether
  findings generalize, but behind the two above on reasoning-per-dollar.

### Skip: driving-specific fine-tunes

Senna, DriveMM, and [CODA-VLM](https://coda-dataset.github.io/coda-lm/) are
LLaVA/Vicuna-7B-era models. Tuned on driving VQA, but their base reasoning is
two generations old — and the data says the bottleneck is judgment, not domain
familiarity. Cite as related work, don't spend GPU hours. The
[CODA-LM corner-case benchmark](https://arxiv.org/abs/2404.10595) itself is
the closest existing evaluation and may be worth citing in the paper.

## Suggested evaluation path

The H-family stage-1 protocol is the cheapest discriminator available: before
paying for full verdict runs, run **expect_early on the 72-clip subset** per
candidate. Cosmos-Nano scored 18/72 strict; any model that meaningfully beats
that is worth the full E/F/I battery.

One-H200 pilot ordering:

1. Qwen3.5-27B
2. Qwen3-VL-32B-Thinking
3. GLM-4.6V-Flash-9B

then scale the winner (larger MoE sibling, 2–4×H200 FP8).

Caveats that carry over regardless of model:

- vLLM's frame-sampling default (fps 2) bit once already (`VLM_FINDINGS.md`
  §1.2) — re-verify `prompt_tokens` per new model rather than trusting request
  args.
- Keep the 720p↑ @ 8 fps input standard (Part 7.2) and the P0 gate rerun for
  cross-session comparability.

## Sources

- [Qwen3-VL GitHub](https://github.com/qwenlm/qwen3-vl)
- [Qwen3.5-27B on Hugging Face](https://huggingface.co/Qwen/Qwen3.5-27B)
- [Qwen 3.5 open-weights guide](https://codersera.com/blog/qwen-3-5-complete-guide-2026/)
- [GLM-V GitHub](https://github.com/zai-org/GLM-V)
- [GLM-4.6V release (VentureBeat)](https://venturebeat.com/ai/z-ai-debuts-open-source-glm-4-6v-a-native-tool-calling-vision-model-for)
- [InternVL3.5 paper](https://arxiv.org/html/2508.18265v1)
- [InternVL3.5 vLLM recipe](https://docs.vllm.ai/projects/recipes/en/latest/InternVL/InternVL3_5.html)
- [Cosmos-Reason1-7B](https://huggingface.co/nvidia/Cosmos-Reason1-7B)
- [BentoML open VLM guide 2026](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models)
- [CODA-LM](https://coda-dataset.github.io/coda-lm/)
- [DataCamp top VLMs](https://www.datacamp.com/blog/top-vision-language-models)
