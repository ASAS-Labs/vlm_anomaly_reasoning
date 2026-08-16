#!/usr/bin/env python3
"""Checks for the anomaly-reasoning parser, metrics, and dataset discovery.

Plain asserts so it runs anywhere without pytest:
    cd data/cosmos3 && python test_parse.py
Dataset checks are skipped when data/datasets/generated_vids is absent.
"""

import sys
from pathlib import Path

from utils import (
    EXPECTED_ANOMALY,
    EXPECTED_NORMAL,
    EXPECTED_TOTAL,
    Metrics,
    discover_eval_videos,
    parse_verdict,
)

# (label, raw_output, finish_reason, expected_verdict, expected_reason)
CASES = [
    # The bug this parser exists to fix: a <think> preamble rehearsing the wrong
    # answer used to win because re.search took the FIRST match.
    ("think rehearses wrong answer",
     "<think>At first this looks like Classification: Normal, but the vehicle brakes "
     "for a billboard.</think>\nClassification: Anomaly",
     "stop", "Anomaly", "verdict_after_think"),

    # Truncation used to fall through to a keyword scan that answered "Anomaly".
    ("truncated mid-think",
     "<think>The ego vehicle approaches the billboard and the anomaly would be",
     "length", "Unknown", "truncated_no_verdict"),

    # Prose mentioning the word must not become a verdict.
    ("prose mentions anomaly, no verdict",
     "The word anomaly appears here but there is no verdict.",
     "stop", "Unknown", "no_verdict"),

    ("last verdict wins",
     "Classification: Normal\nOn reflection that is wrong.\nClassification: Anomaly",
     "stop", "Anomaly", "verdict_after_think"),

    ("bare word", "Anomaly", "stop", "Anomaly", "bare_word"),
    ("bare word punctuated", "  Normal.  ", "stop", "Normal", "bare_word"),
    ("markdown bold", "**Classification:** Normal", "stop", "Normal", "verdict_after_think"),
    ("em dash separator", "Classification — Anomaly", "stop", "Anomaly", "verdict_after_think"),
    ("answer tags", "<answer>Classification: Normal</answer>", "stop", "Normal",
     "verdict_after_think"),
    ("verdict only inside think", "<think>Classification: Anomaly</think>", "stop",
     "Unknown", "verdict_only_in_think"),
    ("empty", "", "stop", "Unknown", "empty_output"),
    ("none", None, "stop", "Unknown", "empty_output"),
    ("whitespace only", "   \n ", "stop", "Unknown", "empty_output"),
    # "normalize" must not match "normal".
    ("no false substring match", "We normalize the trajectory first.", "stop",
     "Unknown", "no_verdict"),
    ("think then bare word", "<think>weighing both</think>\nNormal", "stop",
     "Normal", "bare_word"),
]


def test_parser():
    for label, raw, finish, want_verdict, want_reason in CASES:
        got = parse_verdict(raw, finish_reason=finish)
        assert got["verdict"] == want_verdict, (
            f"{label}: verdict {got['verdict']!r} != {want_verdict!r} (raw={raw!r})"
        )
        assert got["reason"] == want_reason, (
            f"{label}: reason {got['reason']!r} != {want_reason!r} (raw={raw!r})"
        )
    # The rehearsed verdict is retained for auditing.
    audit = parse_verdict("<think>Classification: Normal</think>Classification: Anomaly")
    assert audit["verdicts_in_think"] == [], "think verdicts only recorded when unresolved"
    only = parse_verdict("<think>Classification: Normal</think>")
    assert only["verdicts_in_think"] == ["normal"], only
    # An unterminated <think> is flagged truncated even without finish_reason.
    assert parse_verdict("<think>reasoning cut off")["truncated"] is True
    print(f"  parser: {len(CASES)} cases + 3 audit checks passed")


def test_answer_text():
    from types import SimpleNamespace as NS

    from pilot_models import answer_text

    # Reasoning-parser server: trace arrives separately; content passes through.
    ch = NS(message=NS(content="Stop", reasoning_content="continue seems fine, "
                       "but the light is red, so stop"))
    content, reasoning = answer_text(ch)
    assert content == "Stop" and "continue" in reasoning, (content, reasoning)

    # No parser: <think> block is stripped into reasoning.
    ch = NS(message=NS(content="<think>continue is tempting here</think>\nSlow"))
    content, reasoning = answer_text(ch)
    assert content == "Slow", content
    assert reasoning == "continue is tempting here", reasoning

    # GLM box tokens around the answer must be stripped for the verdict parser.
    ch = NS(message=NS(content="<|begin_of_box|>Anomaly<|end_of_box|>",
                       reasoning_content=None))
    content, _ = answer_text(ch)
    assert content == "Anomaly", content

    # Unterminated <think>: the whole output is reasoning, content empty.
    ch = NS(message=NS(content="<think>the driver should continue"))
    content, reasoning = answer_text(ch)
    assert content == "" and "continue" in reasoning, (content, reasoning)

    # The rfind-last hazard this exists to fix: parse only the answer content.
    try:
        from expectation_experiment import parse_option
    except ImportError:
        print("  answer_text: 3 cases passed (parse_option skipped, no openai)")
        return
    assert parse_option("Stop") == "stop"
    assert parse_option("") == "unknown"
    # The real hazard: a truncated trace whose last option word is wrong. Raw
    # parsing answers "continue"; content-only parsing correctly says unknown.
    raw = "<think>stop? or is the sign printed — then keep going, continue"
    ch = NS(message=NS(content=raw))
    content, _ = answer_text(ch)
    assert parse_option(raw) == "continue"  # documents the old failure mode
    assert parse_option(content) == "unknown", content
    print("  answer_text: reasoning split + content-only option parsing passed")


def test_metrics():
    m = Metrics()
    # 3 true anomalies: 2 correct, 1 called Normal.
    m.add("Anomaly", 1, 1.0)
    m.add("Anomaly", 1, 2.0)
    m.add("Normal", 1, 3.0)
    # 3 true normals: 2 correct, 1 called Anomaly.
    m.add("Normal", 0, 4.0)
    m.add("Normal", 0, 5.0)
    m.add("Anomaly", 0, 6.0)
    # Unresolved, on the skip list.
    m.add("Unknown", 1, 7.0, on_skip_list=True, reason="truncated_no_verdict")
    m.add("Error", 0, None, reason=None)

    r = m.compute()
    assert r["n_total"] == 8, r["n_total"]
    assert r["n_resolved"] == 6 and r["n_unknown"] == 1 and r["n_error"] == 1, r
    c = r["resolved"]
    assert (c["TP"], c["FP"], c["TN"], c["FN"]) == (2, 1, 2, 1), c
    assert abs(c["accuracy"] - 4 / 6) < 1e-9, c["accuracy"]
    assert abs(r["coverage"] - 6 / 8) < 1e-9, r["coverage"]
    # Unresolved counted wrong: 4 correct out of 8.
    assert abs(r["strict_all"]["accuracy"] - 0.5) < 1e-9, r["strict_all"]
    lo, hi = r["accuracy_bounds"]
    assert abs(lo - 0.5) < 1e-9 and abs(hi - 0.75) < 1e-9, r["accuracy_bounds"]
    assert r["unresolved_reasons"] == {"truncated_no_verdict": 1}, r["unresolved_reasons"]
    assert r["n_on_skip_list"] == 1, r["n_on_skip_list"]
    assert r["excluding_skip_list"]["n_total"] == 7, r["excluding_skip_list"]
    assert r["timing"]["n_timed"] == 7, r["timing"]
    print("  metrics: confusion, coverage, bounds, skip-list split passed")


def test_discovery():
    root = Path(__file__).resolve().parents[2] / "data" / "datasets" / "generated_vids"
    if not root.is_dir():
        print("  discovery: SKIPPED (dataset not present locally)")
        return
    items = discover_eval_videos(root)
    assert len(items) == EXPECTED_TOTAL, len(items)
    assert sum(1 for i in items if i["true_label"] == 1) == EXPECTED_ANOMALY
    assert sum(1 for i in items if i["true_label"] == 0) == EXPECTED_NORMAL
    assert not any("upsampled_prompts" in i["rel_path"] for i in items), \
        "upsampled_prompts must be excluded"
    rels = [i["rel_path"] for i in items]
    assert len(set(rels)) == len(rels), "rel_path keys must be unique"
    # The collision that makes stem-keying unsafe.
    stems = [Path(r).name for r in rels]
    assert len(set(stems)) < len(stems), "expected colliding basenames across folders"
    # 16 negative + 31 positive entries in the review skip lists.
    assert sum(1 for i in items if i["on_skip_list"]) == 47, \
        sum(1 for i in items if i["on_skip_list"])
    print(f"  discovery: {len(items)} videos "
          f"({EXPECTED_ANOMALY}/{EXPECTED_NORMAL}), "
          f"{len(stems) - len(set(stems))} basename collisions, 47 skip-listed")


if __name__ == "__main__":
    print("running checks...")
    test_parser()
    test_answer_text()
    test_metrics()
    test_discovery()
    print("all checks passed")
    sys.exit(0)
