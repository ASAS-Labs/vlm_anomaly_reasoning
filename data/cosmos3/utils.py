"""Utilities for Cosmos3 anomaly-reasoning inference: metrics, output parsing,
dataset discovery, and action-sequence loading."""

import json
import re
import statistics
from pathlib import Path

# Bumped whenever parse_verdict's logic changes. Stamped into every result record so a
# later re-parse can be compared against what the run actually used.
PARSER_VERSION = 2

RESOLVED_VERDICTS = ("Anomaly", "Normal")


# ============================================================
# Eval dataset layout
# ============================================================
# The four folders evaluated for the semantic-anomaly experiment, mapped to ground truth.
# negative_scenarios depict an anomalous ego response (label 1); positive_scenarios depict
# a correct one (label 0). `upsampled_prompts/` is deliberately excluded: those 24 clips
# are the pre-review superset that `*_filtered/` was drawn from, so including them would
# double-count scenarios.
_ROOT = "final_semantic_scenarios"
EVAL_FOLDERS = {
    f"{_ROOT}/negative_scenarios/negative_scenarios_filtered": 1,
    f"{_ROOT}/negative_scenarios/negative_scenarios_variants": 1,
    f"{_ROOT}/positive_scenarios/positive_scenarios_filtered": 0,
    f"{_ROOT}/positive_scenarios/positive_scenarios_variants": 0,
}

EXPECTED_TOTAL = 315
EXPECTED_ANOMALY = 147
EXPECTED_NORMAL = 168

# Skip lists written by the inverse-dynamics review GUI (data_validation/). Clips named
# here had trajectories a reviewer rejected. They are still evaluated; each record is
# tagged so metrics can be recomputed with them excluded, without re-running inference.
_SKIP_LISTS = {
    f"{_ROOT}/negative_scenarios/negative_scenarios_variants": "negative_scenarios_variants_filter.csv",
    f"{_ROOT}/positive_scenarios/positive_scenarios_variants": "positive_scenarios_variants_filter.csv",
}
_SKIP_LIST_DIR = Path(__file__).resolve().parent / "data_validation"


def _load_skip_names(csv_name):
    """Read a one-filename-per-line skip list. Mirrors data_validation.io_utils
    .load_skip_filenames, inlined so the GPU box does not need pandas."""
    path = _SKIP_LIST_DIR / csv_name
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


# ============================================================
# Output parsing
# ============================================================
# A verdict line: "Classification: Anomaly", "**Classification:** Normal",
# "classification - anomaly". The trailing \b stops "normalize" matching "normal".
_VERDICT_RE = re.compile(
    r"classification\s*[:\-–—]?\s*\*{0,2}\s*(anomaly|normal)\b", re.I
)
_THINK_BLOCK_RE = re.compile(r"<think>(.*?)</think>", re.I | re.S)
_THINK_OPEN_RE = re.compile(r"<think>(.*)\Z", re.I | re.S)
_ANSWER_TAG_RE = re.compile(r"</?answer>", re.I)
# The model is told to "reply with exactly one word", so a bare verdict is valid.
_BARE_RE = re.compile(r"\A\W*(anomaly|normal)\W*\Z", re.I)


def _result(verdict, reason, verdicts_in_think=(), truncated=False):
    return {
        "verdict": verdict,
        "reason": reason,
        "verdicts_in_think": list(verdicts_in_think),
        "truncated": truncated,
        "parser_version": PARSER_VERSION,
    }


def parse_verdict(raw, finish_reason=None):
    """Extract the model's Anomaly/Normal verdict from its raw output.

    Reasoning models emit a <think> preamble that frequently rehearses the wrong
    answer before committing to one, so reasoning text is separated out and only the
    answer body can produce a verdict — and the LAST verdict in it wins, not the first.

    There is deliberately no keyword-frequency fallback. Scanning prose for the words
    "anomaly"/"normal" resolved nearly every truncated output to Anomaly, because the
    word saturates both the prompt echo and the reasoning trace. An output with no
    parseable verdict is reported as Unknown rather than guessed at.

    Returns a dict: verdict ('Anomaly' | 'Normal' | 'Unknown'), reason, the verdicts
    seen inside <think>, whether the output was truncated, and the parser version.
    """
    truncated = finish_reason == "length"

    if not raw or not raw.strip():
        return _result("Unknown", "empty_output", truncated=truncated)

    # Split reasoning from answer.
    think_parts = _THINK_BLOCK_RE.findall(raw)
    answer = _THINK_BLOCK_RE.sub(" ", raw)

    # An unterminated <think> means generation stopped mid-reasoning.
    open_think = _THINK_OPEN_RE.search(answer)
    if open_think:
        truncated = True
        think_parts.append(open_think.group(1))
        answer = answer[: open_think.start()]

    answer = _ANSWER_TAG_RE.sub(" ", answer).strip()

    matches = _VERDICT_RE.findall(answer)
    if matches:
        return _result(matches[-1].capitalize(), "verdict_after_think", truncated=truncated)

    bare = _BARE_RE.match(answer)
    if bare:
        return _result(bare.group(1).capitalize(), "bare_word", truncated=truncated)

    # A verdict that only ever appeared inside <think> is not a commitment.
    in_think = [m.lower() for part in think_parts for m in _VERDICT_RE.findall(part)]
    if in_think:
        return _result("Unknown", "verdict_only_in_think", in_think, truncated)

    if truncated:
        return _result("Unknown", "truncated_no_verdict", truncated=True)
    return _result("Unknown", "no_verdict")


def parse_classification(raw: str) -> str:
    """Back-compat wrapper for the cosmos1 scripts: verdict string only."""
    return parse_verdict(raw)["verdict"]


# ============================================================
# Dataset discovery
# ============================================================
def discover_videos(dataset_root) -> list[tuple[Path, int]]:
    """Recursively find .mp4 videos under dataset_root and label them by folder.

    Ground truth: a path containing 'negative_scenario' is an anomaly (label 1);
    'positive_scenario' is normal (label 0). Unlabeled videos are skipped.
    """
    root = Path(dataset_root)
    labeled = []
    for video in sorted(root.rglob("*.mp4")):
        path_str = str(video).lower()
        if "negative_scenario" in path_str:
            labeled.append((video, 1))
        elif "positive_scenario" in path_str:
            labeled.append((video, 0))
    return labeled


def discover_eval_videos(dataset_root, strict=True) -> list[dict]:
    """Enumerate the four EVAL_FOLDERS only, in a stable order.

    Unlike discover_videos this whitelists folders instead of substring-matching the
    whole path, which otherwise sweeps in upsampled_prompts/ (339 videos instead of 315)
    and mislabels everything if any parent directory happens to contain the token.

    Each item is keyed by `rel_path` (relative to dataset_root). That key matters: 126
    basenames collide across the four folders, so a stem-keyed resume would corrupt data.
    """
    root = Path(dataset_root)
    items = []
    for folder, label in EVAL_FOLDERS.items():
        skip_names = _load_skip_names(_SKIP_LISTS[folder]) if folder in _SKIP_LISTS else set()
        folder_dir = root / folder
        if not folder_dir.is_dir():
            if strict:
                raise FileNotFoundError(f"Eval folder missing: {folder_dir}")
            continue
        for video in sorted(folder_dir.glob("*.mp4")):
            items.append({
                "rel_path": str(video.relative_to(root).as_posix()),
                "abs_path": video,
                "true_label": label,
                "folder": Path(folder).name,
                "on_skip_list": video.name in skip_names,
            })

    if strict:
        n_anom = sum(1 for i in items if i["true_label"] == 1)
        n_norm = len(items) - n_anom
        if (len(items), n_anom, n_norm) != (EXPECTED_TOTAL, EXPECTED_ANOMALY, EXPECTED_NORMAL):
            per_folder = {f: sum(1 for i in items if i["folder"] == Path(f).name)
                          for f in EVAL_FOLDERS}
            raise ValueError(
                f"Expected {EXPECTED_TOTAL} videos "
                f"({EXPECTED_ANOMALY} anomaly / {EXPECTED_NORMAL} normal), got "
                f"{len(items)} ({n_anom}/{n_norm}). Per folder: {per_folder}"
            )
    return items


def read_action_sequence(video_path) -> str:
    """Read the same-stem 5 Hz .txt action sequence next to a video."""
    path = Path(video_path)
    txt_path = path.with_name(path.stem + ".txt")
    if not txt_path.exists():
        raise FileNotFoundError(f"Action sequence file not found: {txt_path}")
    text = txt_path.read_text().strip()
    # Fail loudly here rather than sending malformed state into the prompt.
    seq = json.loads(text)
    if not isinstance(seq, list) or not seq or not all(len(row) == 2 for row in seq):
        raise ValueError(f"Malformed action sequence in {txt_path}")
    return text


# ============================================================
# Metrics — anomaly is the positive class (label 1)
# ============================================================
def _confusion(records):
    tp = fp = tn = fn = 0
    for r in records:
        pred = 1 if r["verdict"] == "Anomaly" else 0
        if pred == 1 and r["true_label"] == 1:
            tp += 1
        elif pred == 1:
            fp += 1
        elif r["true_label"] == 0:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    return {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "accuracy": (tp + tn) / total if total else 0.0,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0,
        "balanced_accuracy": (recall + specificity) / 2,
        "n": total,
    }


def _strict(records):
    """Every unresolved record (Unknown/Error) counted as wrong."""
    resolved = [r for r in records if r["verdict"] in RESOLVED_VERDICTS]
    c = _confusion(resolved)
    n_total = len(records)
    n_anom = sum(1 for r in records if r["true_label"] == 1)
    n_norm = n_total - n_anom
    return {
        "accuracy": (c["TP"] + c["TN"]) / n_total if n_total else 0.0,
        "recall": c["TP"] / n_anom if n_anom else 0.0,
        "specificity": c["TN"] / n_norm if n_norm else 0.0,
        "n": n_total,
    }


def _view(records):
    resolved = [r for r in records if r["verdict"] in RESOLVED_VERDICTS]
    n_total = len(records)
    n_unresolved = n_total - len(resolved)
    strict = _strict(records)
    return {
        "n_total": n_total,
        "n_resolved": len(resolved),
        "n_unknown": sum(1 for r in records if r["verdict"] == "Unknown"),
        "n_error": sum(1 for r in records if r["verdict"] == "Error"),
        "coverage": len(resolved) / n_total if n_total else 0.0,
        "resolved": _confusion(resolved),
        "strict_all": strict,
        # True accuracy lies between "every unresolved wrong" and "every one right".
        "accuracy_bounds": [
            strict["accuracy"],
            (strict["accuracy"] * n_total + n_unresolved) / n_total if n_total else 0.0,
        ],
    }


class Metrics:
    """Accumulate per-video verdicts and compute classification metrics.

    Unlike the previous version nothing is dropped: Unknown and Error records are
    retained and counted, so an accuracy figure can never be read without the
    denominator it was computed over.
    """

    def __init__(self):
        self.records = []

    @property
    def count(self):
        return len(self.records)

    def add(self, verdict, true_label, latency_s=None, on_skip_list=False, reason=None):
        self.records.append({
            "verdict": verdict,
            "true_label": true_label,
            "latency_s": latency_s,
            "on_skip_list": on_skip_list,
            "reason": reason,
        })

    def compute(self):
        if not self.records:
            return None

        reasons = {}
        for r in self.records:
            if r["verdict"] not in RESOLVED_VERDICTS and r["reason"]:
                reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1

        times = [r["latency_s"] for r in self.records if r["latency_s"] is not None]
        timing = {
            "mean_s": statistics.fmean(times) if times else 0.0,
            "median_s": statistics.median(times) if times else 0.0,
            "p95_s": (sorted(times)[min(len(times) - 1, int(0.95 * len(times)))]
                      if times else 0.0),
            "total_s": sum(times),
            "n_timed": len(times),
        }

        out = _view(self.records)
        out["unresolved_reasons"] = reasons
        out["timing"] = timing
        out["true_counts"] = {
            "anomaly": sum(1 for r in self.records if r["true_label"] == 1),
            "normal": sum(1 for r in self.records if r["true_label"] == 0),
        }
        out["pred_counts"] = {
            v: sum(1 for r in self.records if r["verdict"] == v)
            for v in ("Anomaly", "Normal", "Unknown", "Error")
        }
        # Same metrics over clips whose trajectories passed inverse-dynamics review.
        kept = [r for r in self.records if not r["on_skip_list"]]
        out["excluding_skip_list"] = _view(kept) if kept else None
        out["n_on_skip_list"] = len(self.records) - len(kept)
        return out
