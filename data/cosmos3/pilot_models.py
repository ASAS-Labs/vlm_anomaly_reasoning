#!/usr/bin/env python3
"""Registry for the open-VLM pilot (family K): candidate models vs Cosmos3-Nano.

One entry per candidate: HF id, vLLM serve flags, and per-arm request settings
taken from each model's card / vLLM recipe (URLs in "notes"). Each model runs in
its card-recommended default mode: thinking models think with their recommended
sampling (several cards warn against greedy); the verdict arm disables thinking
where a documented switch exists, otherwise runs in think mode and parses only
the final answer content.

Shared helpers keep request building, reasoning/content splitting, and run-meta
recording in one place for both runners (expectation_experiment.py, prompt_lab.py).

    python pilot_models.py --print qwen38     # review artifact: serve cmd + kwargs
    python pilot_models.py --hf-id qwen38     # plumbing for spec/run_pilot_model.sh
"""

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from utils import _THINK_BLOCK_RE, _THINK_OPEN_RE

# Sampling dicts hold OpenAI-native keys plus vLLM extras (top_k,
# repetition_penalty) which request_kwargs() routes into extra_body.
_QWEN_THINK = {"temperature": 1.0, "top_p": 0.95, "top_k": 20,
               "presence_penalty": 0.0}
_QWEN_NONTHINK = {"temperature": 0.7, "top_p": 0.8, "top_k": 20,
                  "presence_penalty": 1.5}
_QWEN_OFF = {"chat_template_kwargs": {"enable_thinking": False}}
_GLM_SAMPLING = {"temperature": 0.8, "top_p": 0.6, "top_k": 2,
                 "repetition_penalty": 1.1}

# InternVL3.5 thinking is opt-in via this system prompt (verbatim from the vLLM
# recipe; t=0.6/top_p=0.95 recommended with it).
INTERNVL_THINK_SYSTEM = (
    "You are an AI assistant that rigorously follows this response protocol:\n\n"
    "1. First, conduct a detailed analysis of the question. Consider different "
    "angles, potential solutions, and reason through the problem step-by-step. "
    "Enclose this entire thinking process within <think> and </think> tags.\n\n"
    "2. After the thinking section, provide a clear, concise, and direct answer "
    "to the user's question. Separate the answer from the think section with a "
    "newline.\n\n"
    "Ensure that the thinking process is thorough but remains focused on the "
    "query. The final answer should be standalone and not reference the "
    "thinking section.")

MODELS = {
    "qwen38": {
        "hf_id": "Qwen/Qwen3.8-27B",
        "weights_gb": 55,
        "serve_extra": ["--reasoning-parser", "qwen3"],
        "max_model_len": 32768,
        "think_off": _QWEN_OFF,
        "arms": {
            "expect": {"think": True, "sampling": _QWEN_THINK, "max_tokens": 4096},
            "verdict": {"think": False, "sampling": _QWEN_NONTHINK, "max_tokens": 256},
            "verdict_think": {"think": True, "sampling": _QWEN_THINK,
                              "max_tokens": 4096},
            # 8k budget re-run: 18/72 truncated at 4096 (Part 11.4)
            "verdict_think8k": {"think": True, "sampling": _QWEN_THINK,
                                "max_tokens": 8192},
            # Q-lab decoding axis: 3.8's chat template accepts reasoning_effort;
            # over-rumination correlates with errors (Part 11.5), so try "low".
            # chat_template_kwargs rides extra_body via request_kwargs, like
            # _QWEN_OFF does.
            "verdict_think8k_low": {
                "think": True,
                "sampling": {**_QWEN_THINK,
                             "chat_template_kwargs": {"reasoning_effort": "low"}},
                "max_tokens": 8192},
        },
        "notes": "Aug 2026 flagship 27B VLM; card: thinking default, think "
                 "t=1.0/p.95/k20/pres0, instruct t=0.7/p.8/k20/pres1.5. "
                 "https://huggingface.co/Qwen/Qwen3.8-27B",
    },
    "qwen36": {
        "hf_id": "Qwen/Qwen3.6-27B",
        "weights_gb": 55,
        "serve_extra": ["--reasoning-parser", "qwen3"],
        "max_model_len": 32768,
        "think_off": _QWEN_OFF,
        "arms": {
            "expect": {"think": True, "sampling": _QWEN_THINK, "max_tokens": 4096},
            "verdict": {"think": False, "sampling": _QWEN_NONTHINK, "max_tokens": 256},
            "verdict_think": {"think": True, "sampling": _QWEN_THINK,
                              "max_tokens": 4096},
        },
        "notes": "Apr 2026; same family/sampling as 3.8. "
                 "https://huggingface.co/Qwen/Qwen3.6-27B",
    },
    "qwen35": {
        "hf_id": "Qwen/Qwen3.5-27B",
        "weights_gb": 55,
        "serve_extra": ["--reasoning-parser", "qwen3"],
        "max_model_len": 32768,
        "think_off": _QWEN_OFF,
        "arms": {
            "expect": {"think": True,
                       "sampling": {**_QWEN_THINK, "presence_penalty": 1.5},
                       "max_tokens": 4096},
            "verdict": {"think": False, "sampling": _QWEN_NONTHINK, "max_tokens": 256},
            "verdict_think": {"think": True,
                              "sampling": {**_QWEN_THINK, "presence_penalty": 1.5},
                              "max_tokens": 4096},
        },
        "notes": "card: think-general presence_penalty=1.5 (unlike 3.8's 0.0). "
                 "https://huggingface.co/Qwen/Qwen3.5-27B",
    },
    "qwen3vl32t": {
        "hf_id": "Qwen/Qwen3-VL-32B-Thinking",
        "weights_gb": 66,
        # qwen3 parser misfires on VL-Thinking (vllm#29408); vLLM's own example
        # for Qwen3-VL-Thinking uses deepseek_r1.
        "serve_extra": ["--reasoning-parser", "deepseek_r1"],
        "max_model_len": 32768,
        "think_off": None,  # always-think edition, no documented off-switch
        "arms": {
            "expect": {"think": True, "sampling": _QWEN_THINK, "max_tokens": 4096},
            "verdict": {"think": True, "sampling": _QWEN_THINK, "max_tokens": 4096},
        },
        "notes": "the Cosmos-post-training ablation (same Qwen lineage, general "
                 "post-training). Card: VL t=1.0/p.95/k20/pres0, greedy disabled. "
                 "https://huggingface.co/Qwen/Qwen3-VL-32B-Thinking",
    },
    "glm46vf": {
        "hf_id": "zai-org/GLM-4.6V-Flash",
        "weights_gb": 20,
        "serve_extra": ["--reasoning-parser", "glm45",
                        "--mm-processor-cache-type", "shm"],
        "max_model_len": 32768,
        # GLM-4.5V/4.6V chat template accepts enable_thinking; verified at smoke
        # (reasoning_content must be empty on the verdict arm, else fall back to
        # think mode with max_tokens 4096).
        "think_off": _QWEN_OFF,
        "arms": {
            "expect": {"think": True, "sampling": _GLM_SAMPLING, "max_tokens": 4096},
            "verdict": {"think": False, "sampling": _GLM_SAMPLING, "max_tokens": 256},
            "verdict_think": {"think": True, "sampling": _GLM_SAMPLING,
                              "max_tokens": 4096},
        },
        "notes": "10B, thinking default on; card leaderboard sampling "
                 "t=0.8/p.6/k2/rep1.1; vLLM>=0.12, parser glm45 per "
                 "https://recipes.vllm.ai/zai-org/GLM-4.6V. "
                 "https://huggingface.co/zai-org/GLM-4.6V-Flash",
    },
    "internvl35": {
        "hf_id": "OpenGVLab/InternVL3_5-38B",
        "weights_gb": 76,
        "serve_extra": ["--trust-remote-code"],
        "max_model_len": 32768,
        "think_off": None,  # thinking is opt-in via system prompt; default instruct
        "arms": {
            "expect": {"think": False, "sampling": {"temperature": 0.0},
                       "max_tokens": 256},
            "verdict": {"think": False, "sampling": {"temperature": 0.0},
                        "max_tokens": 256},
            "verdict_think": {"think": True,
                              "sampling": {"temperature": 0.6, "top_p": 0.95},
                              "max_tokens": 4096,
                              "system": INTERNVL_THINK_SYSTEM},
        },
        "notes": "vLLM recipe: --trust-remote-code, t=0.0 for image/video chat. "
                 "https://docs.vllm.ai/projects/recipes/en/latest/InternVL/InternVL3_5.html",
    },
}

# H200 @ 8 fps, 720p upscale; identical to the Cosmos serve invocation minus the
# Cosmos-only --hf-overrides. Frame sampling is server-level ONLY: never pass
# do_sample_frames / fps per request (double-sampling breaks Qwen processors).
COMMON_SERVE = ["--allowed-local-media-path", "/",
                "--media-io-kwargs", '{"video": {"fps": 8, "num_frames": -1}}',
                "--tensor-parallel-size", "1"]


def serve_command(key: str, port: int = 8000) -> list:
    m = MODELS[key]
    return (["vllm", "serve", m["hf_id"]] + COMMON_SERVE
            + ["--max-model-len", str(m["max_model_len"]), "--port", str(port)]
            + m["serve_extra"])


def request_kwargs(key: str, arm: str):
    """Resolve an arm to (openai-native kwargs, extra_body-or-None)."""
    m = MODELS[key]
    cfg = m["arms"][arm]
    s = dict(cfg["sampling"])
    kwargs = {"max_tokens": cfg["max_tokens"]}
    for k in ("temperature", "top_p", "presence_penalty", "frequency_penalty"):
        if k in s:
            kwargs[k] = s.pop(k)
    extra = dict(s)  # top_k, repetition_penalty, ...
    if not cfg["think"] and m["think_off"]:
        extra.update(m["think_off"])
    return kwargs, (extra or None)


def answer_text(choice):
    """Split a chat choice into (content, reasoning).

    With a server-side reasoning parser the trace arrives in
    message.reasoning_content and content is the final answer. Without one,
    fall back to stripping <think> blocks; an unterminated <think> means the
    whole output is reasoning (content becomes empty -> parses Unknown).
    """
    msg = choice.message
    content = msg.content or ""
    # vLLM <=0.2x used reasoning_content; 0.27+ returns `reasoning`.
    reasoning = (getattr(msg, "reasoning_content", None)
                 or getattr(msg, "reasoning", None))
    # `not reasoning` (not `is None`): a misfiring parser can return an empty
    # reasoning_content while <think> text remains in content.
    if not reasoning:
        parts = _THINK_BLOCK_RE.findall(content)
        stripped = _THINK_BLOCK_RE.sub(" ", content)
        open_think = _THINK_OPEN_RE.search(stripped)
        if open_think:
            parts.append(open_think.group(1))
            stripped = stripped[: open_think.start()]
        if parts:
            reasoning = "\n".join(parts)
            content = stripped.strip()
    # GLM-4.xV wraps its final answer in box tokens the verdict parser's
    # bare-word matcher cannot see through.
    if "<|begin_of_box|>" in content:
        content = (content.replace("<|begin_of_box|>", " ")
                   .replace("<|end_of_box|>", " ").strip())
    return content, reasoning


def write_run_meta(out_dir: Path, key: str, arm: str, server_url: str,
                   model_id: str, extra: dict):
    m = MODELS[key]
    kwargs, extra_body = request_kwargs(key, arm)
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, cwd=Path(__file__).parent).stdout.strip()
    except OSError:
        git = None
    vllm_version = None
    try:
        base = server_url.rsplit("/v1", 1)[0]
        with urllib.request.urlopen(f"{base}/version", timeout=5) as r:
            vllm_version = json.loads(r.read()).get("version")
    except Exception:
        pass
    meta = {"model_key": key, "hf_id": m["hf_id"], "served_model_id": model_id,
            "arm": arm, "think": m["arms"][arm]["think"],
            "request_kwargs": kwargs, "extra_body": extra_body,
            "serve_command": serve_command(key),
            "vllm_version": vllm_version, "git_commit": git,
            "ts": datetime.now().isoformat(timespec="seconds"), **extra}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def _print_config(key: str):
    from expectation_experiment import EXPECT_QUESTION
    from prompt_variants import VARIANTS
    m = MODELS[key]
    dump = {"key": key, "hf_id": m["hf_id"], "weights_gb": m["weights_gb"],
            "serve_command": " ".join(serve_command(key)), "notes": m["notes"],
            "arms": {}}
    for arm in m["arms"]:
        kwargs, extra = request_kwargs(key, arm)
        prompt = (EXPECT_QUESTION if arm.startswith("expect")
                  else VARIANTS["P0"]["text"])
        dump["arms"][arm] = {
            "think": m["arms"][arm]["think"], "request_kwargs": kwargs,
            "extra_body": extra,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        }
        if m["arms"][arm].get("system"):
            dump["arms"][arm]["system_sha256"] = hashlib.sha256(
                m["arms"][arm]["system"].encode()).hexdigest()
    print(json.dumps(dump, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--print", dest="print_key", metavar="KEY",
                   help="dump serve command + resolved per-arm request kwargs")
    p.add_argument("--hf-id", metavar="KEY")
    p.add_argument("--weights-gb", metavar="KEY")
    p.add_argument("--serve-args", metavar="KEY",
                   help="serve argv after 'vllm serve <hf_id>', one per line")
    args = p.parse_args()

    for key in (args.print_key, args.hf_id, args.weights_gb, args.serve_args):
        if key and key not in MODELS:
            sys.exit(f"unknown model key {key}; have: {', '.join(MODELS)}")
    if args.print_key:
        _print_config(args.print_key)
    elif args.hf_id:
        print(MODELS[args.hf_id]["hf_id"])
    elif args.weights_gb:
        print(MODELS[args.weights_gb]["weights_gb"])
    elif args.serve_args:
        print("\n".join(serve_command(args.serve_args)[3:]))
    else:
        for k, m in MODELS.items():
            print(f"{k}: {m['hf_id']} ({m['weights_gb']} GB)")


if __name__ == "__main__":
    main()
