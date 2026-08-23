#!/usr/bin/env python3
"""Video-token and format parity between vLLM serving and ms-swift training encoding.

The SFT examples must see the same visual tokens the served model sees (720p clip,
8 fps) and the assistant turn must be encoded the way the served model will produce
it. Run once against the served base model and once inside the SFT venv with the
same FPS/VIDEO_* env as training; the script merges both into one json and fails on
a mismatch.

    # in .venv-pilot, base server up:
    python sft_parity.py --side vllm --server_url http://127.0.0.1:8000/v1 --clip /abs/clip.mp4
    # in .venv-sft, same FPS=8 ... env as swift sft:
    python sft_parity.py --side swift --model /path/to/Qwen3.8-27B --clip /abs/clip.mp4 \
        [--target-format think]
"""

import argparse
import json
import sys
from pathlib import Path

from expectation_experiment import SYSTEM_PROMPT
from h_variants import M4_STAGE1

REPO = Path(__file__).resolve().parents[2]
ANSWER_TARGET = "The road ahead is clear and nothing requires a change.\n\nContinue"
THINK_TRACE = ("STEP 1 — PATH: the lane ahead is clear; nothing is in or across the path.\n"
               "STEP 2 — CONTROLS: no real traffic control or hazard; a printed sign on a billboard is a depiction.\n"
               "STEP 3 — MOTION: the ego vehicle is moving.\n"
               "STEP 4 — ACTION: nothing requires a change, so maintain speed and lane.")
THINK_TARGET = "<think>\n" + THINK_TRACE + "\n</think>\n\nThe printed sign commands nothing and the lane is clear.\nContinue"


def vllm_side(args):
    import openai

    import pilot_models
    client = openai.OpenAI(api_key="EMPTY", base_url=args.server_url)
    model_id = client.models.list().data[0].id
    req, extra = pilot_models.request_kwargs("qwen38", "expect_sft")
    req["max_tokens"] = 1
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "video_url", "video_url": {"url": Path(args.clip).resolve().as_uri()}},
                    {"type": "text", "text": M4_STAGE1}]}]
    r = client.chat.completions.create(model=model_id, messages=messages, seed=1,
                                       extra_body=extra, **req)
    return {"vllm_prompt_tokens": r.usage.prompt_tokens, "vllm_model": model_id}


def swift_side(args):
    try:
        from swift import get_model_processor, get_template
    except ImportError as exc:
        sys.exit(f"ms-swift (>=4.3) not importable in this interpreter: {exc}")
    _, processor = get_model_processor(args.model, load_model=False, model_type=args.model_type)
    loss_scale = "default" if args.target_format == "think" else "ignore_empty_think"
    template = get_template(processor, template_type=args.template, loss_scale=loss_scale)
    template.set_mode("train")
    target = THINK_TARGET if args.target_format == "think" else ANSWER_TARGET
    sample = {"messages": [{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": "<video>" + M4_STAGE1},
                           {"role": "assistant", "content": target}],
              "videos": [str(Path(args.clip).resolve())]}
    enc = template.encode(sample)
    ids = list(enc["input_ids"])
    labels = list(enc.get("labels") or [])
    n_prompt = sum(1 for x in labels if x == -100) if labels else None
    tok = getattr(processor, "tokenizer", processor)
    decoded = tok.decode(ids, skip_special_tokens=False)
    tgt_ids = [i for i, x in zip(ids, labels) if x != -100] if labels else []
    decoded_target = tok.decode(tgt_ids, skip_special_tokens=False) if tgt_ids else ""
    head_ok = (decoded.startswith("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n")
               and "<|vision_end|>You are evaluating" in decoded)
    if args.target_format == "think":
        tail_ok = decoded.rstrip().endswith("<|im_start|>assistant\n" + target + "<|im_end|>")
        # loss must cover the procedure: the trace tokens are label (not -100)
        loss_on_trace = "STEP 1" in decoded_target and "STEP 4" in decoded_target
        empty_think = False
    else:
        tail_ok = decoded.rstrip().endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n" + target + "<|im_end|>")
        loss_on_trace = None
        empty_think = "<think>\n\n</think>\n\n" in decoded
    return {"swift_total_tokens": len(ids), "swift_prompt_tokens": n_prompt,
            "swift_target_tokens": len(tgt_ids), "swift_format_ok": head_ok and tail_ok,
            "swift_loss_on_trace": loss_on_trace, "swift_empty_think_prefix_present": empty_think,
            "swift_target_format": args.target_format,
            "swift_decoded_target_tail": decoded_target[-120:], "swift_decoded_head": decoded[:300]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--side", choices=["vllm", "swift"], required=True)
    ap.add_argument("--clip", required=True, help="absolute path to one early_gt clip")
    ap.add_argument("--server_url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None, help="swift side: base model path")
    ap.add_argument("--model-type", default="qwen3_5")
    ap.add_argument("--template", default="qwen3_8")
    ap.add_argument("--target-format", choices=["answer", "think"], default="answer")
    ap.add_argument("--out", type=Path, default=REPO / "logs" / "sft" / "parity.json")
    ap.add_argument("--tol", type=float, default=0.05)
    args = ap.parse_args()

    cur = json.loads(args.out.read_text()) if args.out.exists() else {}
    cur["clip"] = str(Path(args.clip).resolve())
    cur.update(vllm_side(args) if args.side == "vllm" else swift_side(args))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(cur, indent=1))
    print(json.dumps({k: v for k, v in cur.items() if not k.startswith("swift_decoded")}, indent=1))
    if "vllm_prompt_tokens" in cur and cur.get("swift_prompt_tokens"):
        a, b = cur["vllm_prompt_tokens"], cur["swift_prompt_tokens"]
        delta = abs(a - b) / max(a, b)
        print(f"parity: vllm {a} vs swift {b} -> delta {delta:.3%} (tol {args.tol:.0%})")
        if delta > args.tol:
            sys.exit("PARITY FAILED: training video tokens differ from serving")
        if not cur.get("swift_format_ok"):
            sys.exit("PARITY FAILED: encoded prompt/target text differs from the served format (see swift_decoded_head)")
        if cur.get("swift_target_format") == "think":
            if not cur.get("swift_loss_on_trace"):
                sys.exit("PARITY FAILED: loss does not cover the <think> trace")
        elif not cur.get("swift_empty_think_prefix_present"):
            sys.exit("PARITY FAILED: empty <think> prefix missing from the encoded assistant turn")
        print("PARITY OK")


if __name__ == "__main__":
    main()
