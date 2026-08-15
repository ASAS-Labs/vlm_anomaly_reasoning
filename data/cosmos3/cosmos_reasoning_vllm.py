#!/usr/bin/env python3
"""Semantic anomaly reasoning over ego-vehicle driving videos with Cosmos3-Nano.

Runs inference over the four eval folders of av_semantic_anomalies, classifies each
clip as Anomaly/Normal, and writes an append-only JSONL of results plus a metrics
report. Either launches its own vLLM server or attaches to one via --server_url.

Results are fsync'd per video and keyed by dataset-relative path, so a killed run
(credit exhaustion, preemption) loses at most one record and resumes in place.
"""

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import openai

from utils import (
    PARSER_VERSION,
    Metrics,
    discover_eval_videos,
    parse_verdict,
    read_action_sequence,
)

MODEL_NAME = "nvidia/Cosmos3-Nano"

# Base prompts (verbatim from spec/spec_anomaly_reasoning.md — these are the prompts the
# paper reports; do not reword).
BASE_PROMPT_ACTION = (
    "You are an autonomous driving safety expert analyzing this ego vehicle's video "
    "for semantic or contextual anomalies, that may impact safe AV operation. The ego "
    "vehicle's action (state sequence) given afterwards is in the format "
    "[[velocity_in_mph, heading_in_degrees], ...]. Think about the video and the ego "
    "vehicle's action, is there any semantic misunderstanding of the autopilot that "
    "requires intervention? Reply with exactly one word of the following:\n"
    "Classification: Anomaly — if there is a semantic anomaly\n"
    "Classification: Normal — if there is no semantic anomaly."
)

BASE_PROMPT_NO_ACTION = (
    "You are an autonomous driving safety expert analyzing this ego vehicle's video "
    "for semantic or contextual anomalies, that may impact safe AV operation. Think "
    "about the video, is there any semantic misunderstanding of the autopilot that "
    "requires intervention? Reply with exactly one word of the following:\n"
    "Classification: Anomaly — if there is a semantic anomaly\n"
    "Classification: Normal — if there is no semantic anomaly."
)


# ============================================================
# vLLM server lifecycle
# ============================================================
def vllm_executable() -> str:
    """Locate the vllm CLI, preferring the one next to the running interpreter
    (so it works whether or not the venv is activated)."""
    candidate = Path(sys.executable).parent / "vllm"
    if candidate.exists():
        return str(candidate)
    found = shutil.which("vllm")
    if found:
        return found
    raise FileNotFoundError(
        "Could not find the 'vllm' CLI. Install it (see spec/setup_reasoner.sh) and "
        "run with the project's .venv."
    )


def launch_server(port: int, log_path: Path):
    """Launch `vllm serve` for Cosmos3-Nano on a single GPU. Returns the Popen."""
    cmd = [
        vllm_executable(), "serve", MODEL_NAME,
        "--hf-overrides", '{"architectures": ["Cosmos3ReasonerForConditionalGeneration"]}',
        "--async-scheduling",
        "--allowed-local-media-path", "/",
        # Load all video frames and let the processor sample at request `fps`;
        # without this the default loader pre-truncates to 32 frames while the
        # metadata still references the full timeline, breaking do_sample_frames.
        "--media-io-kwargs", '{"video": {"num_frames": -1}}',
        "--tensor-parallel-size", "1",
        "--port", str(port),
    ]
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = env.get("CUDA_VISIBLE_DEVICES", "0")

    print(f"launching vLLM server: {' '.join(cmd)}")
    print(f"  CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']}  (log: {log_path})")
    log_file = open(log_path, "w")
    return subprocess.Popen(
        cmd, stdout=log_file, stderr=subprocess.STDOUT, env=env,
        start_new_session=True,  # own process group so we can tear down children
    )


def wait_for_health(proc, base_url: str, timeout: int = 1800):
    """Poll the server /health endpoint until ready or timeout/crash."""
    url = f"{base_url.rstrip('/').removesuffix('/v1')}/health"
    print(f"waiting for vLLM server on {url} (timeout {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(
                f"vLLM server exited early with code {proc.returncode}; check the server log."
            )
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    print(f"server ready in {time.time() - start:.1f}s\n")
                    return
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"vLLM server not ready after {timeout}s")


def shutdown_server(proc):
    """Terminate the server process group."""
    if proc is None or proc.poll() is not None:
        return
    print("shutting down vLLM server...")
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=30)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


# ============================================================
# Inference
# ============================================================
def build_prompt(mode: str, action_text: str | None) -> str:
    if mode == "action_grounding":
        return f"{BASE_PROMPT_ACTION}\nEgo Vehicle State Sequence (5Hz): {action_text}"
    return BASE_PROMPT_NO_ACTION


def analyze_video(client, model_id, video_path: Path, prompt: str, args):
    """Send one video+prompt. Returns the full choice so finish_reason survives."""
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "video_url",
                     "video_url": {"url": video_path.resolve().as_uri()}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        seed=args.seed,
        extra_body={"mm_processor_kwargs": {"fps": args.fps, "do_sample_frames": True}},
    )
    choice = response.choices[0]
    usage = response.usage
    return {
        "raw_output": choice.message.content,
        "finish_reason": choice.finish_reason,
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
        } if usage else None,
    }


# ============================================================
# Result store — append-only, fsync'd, resumable
# ============================================================
def load_done(jsonl_path: Path) -> dict:
    """Map rel_path -> last record for that video.

    Malformed lines are warned about and skipped rather than fatal: a run killed
    mid-write leaves a torn line, and once ResultWriter repairs the file that
    fragment persists as a mid-file line forever. Losing one record is recoverable
    (it just gets re-run); refusing to start is not.
    """
    done = {}
    if not jsonl_path.exists():
        return done
    torn = 0
    for line in jsonl_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            torn += 1
            continue
        if "video" in rec:
            done[rec["video"]] = rec
    if torn:
        print(f"  warning: skipped {torn} malformed line(s) in {jsonl_path.name}; "
              f"those videos will be re-run")
    return done


class ResultWriter:
    """Append-only JSONL. Flushed and fsync'd per record so a hard kill loses at most one."""

    def __init__(self, path: Path):
        # If a previous run died mid-write the file may not end in a newline. Appending
        # straight onto it would fuse the torn fragment with the next record and destroy
        # it too, so close the line first.
        if path.exists() and path.stat().st_size:
            with open(path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                needs_newline = f.read(1) != b"\n"
            if needs_newline:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n")
        self._f = open(path, "a", encoding="utf-8")

    def write(self, rec: dict):
        self._f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._f.flush()
        os.fsync(self._f.fileno())

    def close(self):
        self._f.close()


def metrics_from_jsonl(jsonl_path: Path) -> Metrics:
    """Recompute metrics from what is actually on disk, so a resumed run reports
    over every video rather than only the ones this process handled."""
    m = Metrics()
    for rec in load_done(jsonl_path).values():
        m.add(
            verdict=rec.get("verdict", "Error"),
            true_label=rec["true_label"],
            latency_s=rec.get("latency_s"),
            on_skip_list=rec.get("on_skip_list", False),
            reason=(rec.get("parse") or {}).get("reason"),
        )
    return m


# ============================================================
# Environment info
# ============================================================
def gpu_info():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], text=True
        ).strip().splitlines()
        return {"count": len(out), "names": out}
    except Exception:
        return {"count": 0, "names": []}


def vllm_version():
    try:
        import vllm
        return vllm.__version__
    except Exception:
        return "unknown"


def git_state():
    def run(*cmd):
        try:
            return subprocess.check_output(cmd, text=True, cwd=Path(__file__).parent).strip()
        except Exception:
            return None
    return {"sha": run("git", "rev-parse", "HEAD"),
            "dirty": bool(run("git", "status", "--porcelain"))}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def select_items(items, limit, sample):
    """Subset for smoke tests. 'balanced' takes an equal slice from each folder."""
    if not limit or limit >= len(items):
        return items
    if sample != "balanced":
        return items[:limit]
    folders = sorted({i["folder"] for i in items})
    per = max(1, limit // len(folders))
    picked = []
    for folder in folders:
        picked += [i for i in items if i["folder"] == folder][:per]
    return picked[:limit]


# ============================================================
# Main
# ============================================================
def main():
    p = argparse.ArgumentParser(description="Cosmos3-Nano anomaly reasoning over driving videos")
    p.add_argument("--dataset", type=str, required=True, help="Dataset root (generated_vids)")
    p.add_argument("--exp_name", type=str, required=True, help="Experiment name")
    p.add_argument("--mode", choices=["action_grounding", "no_action_grounding"],
                   default="no_action_grounding")
    p.add_argument("--out_dir", type=str, default=None,
                   help="Output dir (default logs/<exp_name>_<mode>). No timestamp: "
                        "re-running the same command resumes in place.")
    p.add_argument("--server_url", type=str, default=None,
                   help="Attach to an existing vLLM server instead of launching one")
    p.add_argument("--fps", type=int, default=4)
    p.add_argument("--max_tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--sample", choices=["head", "balanced"], default="balanced")
    p.add_argument("--dry_run", action="store_true",
                   help="Exercise discovery/prompts/JSONL/resume without a GPU or server")
    p.add_argument("--retry_unknown", action="store_true",
                   help="Also re-run videos previously recorded as Unknown")
    p.add_argument("--allow_partial", action="store_true",
                   help="Skip the 315/147/168 dataset assertion")
    args = p.parse_args()

    items = discover_eval_videos(args.dataset, strict=not args.allow_partial)
    items = select_items(items, args.limit, args.sample)
    if not items:
        sys.exit(f"No videos found under {args.dataset}")

    out_dir = Path(args.out_dir) if args.out_dir else Path("logs") / f"{args.exp_name}_{args.mode}"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "results.jsonl"
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Resume: skip anything already resolved.
    done = load_done(jsonl_path)
    retry_verdicts = {"Error"} | ({"Unknown"} if args.retry_unknown else set())
    todo = [i for i in items
            if i["rel_path"] not in done
            or done[i["rel_path"]].get("verdict") in retry_verdicts]

    print(f"{len(items)} videos | model={MODEL_NAME} mode={args.mode}")
    print(f"output: {out_dir}")
    if done:
        print(f"resuming: {len(items) - len(todo)} done, {len(todo)} remaining")
    print("=" * 60)

    # Provenance for this attempt; never overwritten across restarts.
    (out_dir / f"run_meta_{run_id}.json").write_text(json.dumps({
        "run_id": run_id,
        "cli_args": vars(args),
        "model": MODEL_NAME,
        "parser_version": PARSER_VERSION,
        "prompts": {
            "action": BASE_PROMPT_ACTION, "action_sha256": sha256(BASE_PROMPT_ACTION),
            "no_action": BASE_PROMPT_NO_ACTION,
            "no_action_sha256": sha256(BASE_PROMPT_NO_ACTION),
        },
        "git": git_state(),
        "environment": {"hostname": socket.gethostname(), "python": sys.version.split()[0],
                        "vllm": vllm_version(), "gpu": gpu_info()},
        "dataset": {"root": str(args.dataset), "n_videos": len(items),
                    "manifest": [{"video": i["rel_path"], "true_label": i["true_label"],
                                  "on_skip_list": i["on_skip_list"]} for i in items]},
    }, indent=2))

    proc = None
    writer = ResultWriter(jsonl_path)
    start_time = datetime.now()

    try:
        client = model_id = None
        if not args.dry_run:
            base_url = args.server_url or f"http://localhost:{args.port}/v1"
            if not args.server_url:
                proc = launch_server(args.port, out_dir / "vllm_server.log")
            wait_for_health(proc, base_url)
            client = openai.OpenAI(api_key="EMPTY", base_url=base_url)
            model_id = client.models.list().data[0].id

        for n, item in enumerate(todo, 1):
            rec = {
                "run_id": run_id,
                "ts": datetime.now().isoformat(timespec="seconds"),
                "mode": args.mode,
                "video": item["rel_path"],
                "folder": item["folder"],
                "true_label": item["true_label"],
                "on_skip_list": item["on_skip_list"],
                "model": MODEL_NAME,
                "fps": args.fps,
                "max_tokens": args.max_tokens,
                "temperature": args.temperature,
                "seed": args.seed,
            }
            action_text = None
            try:
                if args.mode == "action_grounding":
                    action_text = read_action_sequence(item["abs_path"])
                prompt = build_prompt(args.mode, action_text)
                rec["action_sequence"] = action_text
                rec["prompt_sha256"] = sha256(prompt)

                if args.dry_run:
                    rec.update(verdict="DryRun", parse=None, raw_output=None,
                               finish_reason=None, usage=None, latency_s=None,
                               attempts=0, error=None, correct=None)
                else:
                    last_err = None
                    for attempt in range(1, args.retries + 2):
                        try:
                            t0 = time.time()
                            out = analyze_video(client, model_id, item["abs_path"], prompt, args)
                            rec["latency_s"] = round(time.time() - t0, 3)
                            rec["attempts"] = attempt
                            last_err = None
                            break
                        except Exception as exc:  # noqa: BLE001 - recorded, then retried
                            last_err = exc
                            if attempt <= args.retries:
                                time.sleep(5 * attempt)
                    if last_err is not None:
                        raise last_err

                    parsed = parse_verdict(out["raw_output"], out["finish_reason"])
                    rec.update(
                        verdict=parsed["verdict"],
                        parse={k: v for k, v in parsed.items() if k != "verdict"},
                        # Verbatim and never truncated: the only way to re-derive
                        # verdicts offline if the parser turns out to be wrong.
                        raw_output=out["raw_output"],
                        finish_reason=out["finish_reason"],
                        usage=out["usage"],
                        error=None,
                    )
                    pred = 1 if parsed["verdict"] == "Anomaly" else (
                        0 if parsed["verdict"] == "Normal" else None)
                    rec["correct"] = None if pred is None else pred == item["true_label"]

            except Exception as exc:  # noqa: BLE001 - persisted as an Error record
                rec.update(verdict="Error", parse=None, raw_output=None, finish_reason=None,
                           usage=None, latency_s=None, correct=False,
                           error=f"{type(exc).__name__}: {exc}")

            # Exactly one write per video, outside the try: console failures (a broken
            # pipe from `head`/`tee`, a dead tmux pane) must never rewrite a good
            # record as an Error, nor duplicate it.
            writer.write(rec)
            truth = "Anomaly" if item["true_label"] == 1 else "Normal"
            try:
                if rec["verdict"] == "Error":
                    print(f"[{n}/{len(todo)}] {item['rel_path'].split('/')[-1]}: "
                          f"ERROR - {rec['error']}")
                else:
                    extra = "" if args.dry_run else f" [{rec.get('finish_reason')}]"
                    print(f"[{n}/{len(todo)}] {item['rel_path'].split('/')[-1]}: "
                          f"{rec['verdict']} (truth={truth}, "
                          f"{rec.get('latency_s') or 0:.2f}s){extra}")
            except (BrokenPipeError, OSError):
                pass

    finally:
        writer.close()
        if proc is not None:
            shutdown_server(proc)

    # Metrics come from the file, not from this process's memory.
    metrics = metrics_from_jsonl(jsonl_path).compute()
    end_time = datetime.now()

    report = {
        "experiment": {
            "exp_name": args.exp_name, "mode": args.mode, "run_id": run_id,
            "start_time": start_time.isoformat(), "end_time": end_time.isoformat(),
            "duration_s": round((end_time - start_time).total_seconds(), 1),
        },
        "model": MODEL_NAME,
        "parser_version": PARSER_VERSION,
        "cli_args": vars(args),
        "metrics": metrics,
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print_summary(args, metrics, out_dir)


def print_summary(args, m, out_dir):
    print("=" * 60)
    print(f"\nSUMMARY — {args.exp_name} ({args.mode})")
    print("=" * 60)
    if not m:
        print("no records")
        return
    print(f"Videos: {m['n_total']}  (truth: {m['true_counts']['anomaly']} anomaly / "
          f"{m['true_counts']['normal']} normal)")
    for k, v in m["pred_counts"].items():
        print(f"  - {k}: {v}")
    if m["unresolved_reasons"]:
        print(f"  unresolved reasons: {m['unresolved_reasons']}")

    c = m["resolved"]
    print(f"\nRESOLVED ONLY  (n={c['n']}, coverage={m['coverage']:.3f})")
    print(f"  TP {c['TP']}  TN {c['TN']}  FP {c['FP']}  FN {c['FN']}")
    print(f"  Accuracy {c['accuracy']:.4f}   Precision {c['precision']:.4f}")
    print(f"  Recall   {c['recall']:.4f}   F1        {c['f1']:.4f}")
    print(f"  Balanced accuracy {c['balanced_accuracy']:.4f}")

    s = m["strict_all"]
    print(f"\nALL VIDEOS  (unresolved counted wrong, n={s['n']})")
    print(f"  Accuracy {s['accuracy']:.4f}   Recall {s['recall']:.4f}   "
          f"Specificity {s['specificity']:.4f}")
    lo, hi = m["accuracy_bounds"]
    print(f"  True accuracy is within [{lo:.4f}, {hi:.4f}]")

    if m.get("excluding_skip_list") and m["n_on_skip_list"]:
        e = m["excluding_skip_list"]["resolved"]
        print(f"\nEXCLUDING {m['n_on_skip_list']} SKIP-LISTED CLIPS  (n={e['n']})")
        print(f"  Accuracy {e['accuracy']:.4f}   F1 {e['f1']:.4f}")

    t = m["timing"]
    print(f"\nTiming: mean {t['mean_s']:.2f}s  median {t['median_s']:.2f}s  "
          f"p95 {t['p95_s']:.2f}s  total {t['total_s'] / 60:.1f}min")
    print(f"\nResults: {out_dir}/results.jsonl")
    print(f"Report:  {out_dir}/report.json")


if __name__ == "__main__":
    main()
