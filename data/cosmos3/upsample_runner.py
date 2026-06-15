"""Resilient runner for Cosmos3 prompt upsampling.

Thin wrapper around cosmos_framework's prompt upsampler. It upsamples one prompt
per input line and writes each result to disk immediately, so a single failed
prompt (e.g. an LLM content refusal) is skipped instead of aborting the whole
batch — the upstream CLI buffers all results and writes nothing if any prompt
fails.

Output files match the upstream CLI (``prompt_<index>.json``), and the index is
kept aligned with the input line order, so a skipped prompt simply leaves a gap.
Exits non-zero if any prompt was skipped (after writing the rest).

Run via data/cosmos3/upsample_prompts.sh; flags mirror the upstream module.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cosmos_framework.inference.prompt_upsampling import (
    JSON_ENSURE_ASCII,
    PromptUpsamplerClient,
    PromptUpsamplerConfig,
    _optional_float,
    _read_prompt_lines,
    _upsample_prompt_for_mode,
    configure_prompting_templates,
)


def parse_args() -> argparse.Namespace:
    # Defaults mirror cosmos_framework's CLI (build_cli_parser) so the runner
    # builds an identical PromptUpsamplerConfig and sends identical requests.
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--mode", default="text2video")
    p.add_argument("--endpoint-url", required=True)
    p.add_argument("--model", default=None)
    p.add_argument("--api-token", default=None)
    p.add_argument("--resolution", default="720")
    p.add_argument("--aspect-ratio", default="16,9")
    p.add_argument("--duration", default="5s")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--timeout-s", type=float, default=300.0)
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--max-retries", type=int, default=5)
    p.add_argument("--retry-base-delay-s", type=float, default=1.0)
    p.add_argument("--temperature", type=_optional_float, default=None)
    p.add_argument("--top-p", type=_optional_float, default=None)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--min-p", type=float, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    configure_prompting_templates(mode=args.mode, prompt_template_path=None, json_template_path=None)

    client = PromptUpsamplerClient(
        PromptUpsamplerConfig(
            endpoint_url=args.endpoint_url,
            model=args.model,
            api_token=args.api_token,
            timeout_s=args.timeout_s,
            max_tokens=args.max_tokens,
            max_retries=args.max_retries,
            retry_base_delay_s=args.retry_base_delay_s,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            min_p=args.min_p,
        )
    )

    prompts = _read_prompt_lines(args.input)
    if not prompts:
        raise SystemExit(f"No prompts found in {args.input}")

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[int, str]] = []
    for index, prompt in enumerate(prompts):
        try:
            record = _upsample_prompt_for_mode(
                client,
                prompt,
                mode=args.mode,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio,
                duration=args.duration,
                fps=args.fps,
                image_url=None,
            )
        except Exception as exc:
            # One bad prompt (refusal, timeout, ...) must not lose the others.
            failures.append((index, str(exc)))
            print(f"[{index}] FAILED, skipping: {exc}", file=sys.stderr)
            continue
        path = output / f"prompt_{index}.json"
        path.write_text(json.dumps(record, ensure_ascii=JSON_ENSURE_ASCII, indent=2) + "\n", encoding="utf-8")
        print(f"[{index}] wrote {path.name}")

    print(f"done: {len(prompts) - len(failures)}/{len(prompts)} succeeded")
    if failures:
        print("skipped prompts:", file=sys.stderr)
        for index, exc in failures:
            print(f"  [{index}] {exc[:200]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
