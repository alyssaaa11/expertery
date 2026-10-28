"""Tests for runner.py. No network: every model call uses a fake post_fn.

Run with: ~/projects/forge/.venv/bin/python -m pytest -q test_runner.py
"""

import json
import os
import urllib.error

import pytest

import runner
from jobs import JOBS

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "expected.json"), encoding="utf-8") as _f:
    EXPECTED = json.load(_f)
with open(os.path.join(HERE, "manual.md"), encoding="utf-8") as _f:
    MANUAL = _f.read()

D2 = next(j for j in JOBS if j["id"] == "D2")
DRY_JOBS = [j for j in JOBS if j.get("level") == "dry"]

GOOD_CODE = (
    "import cadquery as cq\n"
    "from cadquery import Solid, Vector\n"
    "plate = Solid.makeBox(40, 20, 3, Vector(-20, -10, 0))\n"
    "rib = Solid.makeBox(3, 20, 12, Vector(-1.5, -10, 3))\n"
    "result = plate.fuse(rib)\n"
)
GOOD_CONTENT = (
    "Here is the ribbed plate.\n```python\n" + GOOD_CODE + "```\n"
)
WRONG_CODE = GOOD_CODE.replace(
    "Solid.makeBox(3, 20, 12, Vector(-1.5, -10, 3))",
    "Solid.makeBox(3, 20, 15, Vector(-1.5, -10, 3))",
)
WRONG_CONTENT = "```python\n" + WRONG_CODE + "```\n"


def fake_resp(content, finish="stop", prompt=100, completion=50, **kw):
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content},
             "finish_reason": finish}
        ],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                  "total_tokens": prompt + completion},
    }


def arm_cfgs():
    return {
        "A": {"endpoint": "http://fake-glimmer/v1/chat/completions",
              "model": "muse-glimmer"},
        "B": {"endpoint": "http://fake-glimmer/v1/chat/completions",
              "model": "muse-glimmer"},
        "C": {"endpoint": "https://inference.baseten.co/v1/chat/completions",
              "model": "meta-models/muse-spark-open-1026"},
    }


# ---------------------------------------------------------------- extraction


def test_extract_fenced_python():
    content = "some words\n```python\nprint(1)\n```\ntrailing"
    assert runner.extract_code(content) == "print(1)"


def test_extract_plain_fence():
    content = "```\nresult = 1\n```"
    assert runner.extract_code(content) == "result = 1"


def test_extract_first_block_wins():
    content = "```python\na = 1\n```\ntext\n```python\nb = 2\n```"
    assert runner.extract_code(content) == "a = 1"


def test_extract_no_fence_uses_whole_content():
    content = "result = 1"
    assert runner.extract_code(content) == "result = 1"


# ---------------------------------------------------------------- scoring outcomes


def test_correct_answer_scores_pass():
    outcome, fails, measurements, code, run_error = runner.score_content(
        GOOD_CONTENT, "stop", D2["build"], EXPECTED["D2"])
    assert outcome == "PASS"
    assert fails == []


def test_wrong_answer_scores_fail():
    outcome, fails, measurements, code, run_error = runner.score_content(
        WRONG_CONTENT, "stop", D2["build"], EXPECTED["D2"])
    assert outcome == "FAIL"
    assert fails


def test_length_finish_scores_invalid():
    outcome, fails, measurements, code, run_error = runner.score_content(
        GOOD_CONTENT, "length", D2["build"], EXPECTED["D2"])
    assert outcome == "INVALID"
    assert outcome != "FAIL"


def test_empty_content_scores_invalid():
    for empty in ("", "   ", None):
        outcome, *_ = runner.score_content(
            empty, "stop", D2["build"], EXPECTED["D2"])
        assert outcome == "INVALID"


# ---------------------------------------------------------------- retry rules


def _http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


def test_no_retry_on_400():
    calls = []

    def post(endpoint, body, timeout):
        calls.append(body)
        raise _http_error(400)

    rec = runner.do_call(D2, "A", "muse-glimmer", "http://x", [],
                         MANUAL, EXPECTED["D2"], post,
                         sleep_fn=lambda s: (_ for _ in ()).throw(
                             AssertionError("must not sleep on 400")))
    assert len(calls) == 1
    assert rec["outcome"] == "INVALID"


def test_one_retry_on_500_then_succeeds():
    calls = []
    sleeps = []

    def post(endpoint, body, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise _http_error(500)
        return fake_resp("nothing", finish="length")

    rec = runner.do_call(D2, "A", "muse-glimmer", "http://x", [],
                         MANUAL, EXPECTED["D2"], post, sleeps.append)
    assert len(calls) == 2
    assert sleeps == [runner.RETRY_DELAY]
    assert rec["outcome"] == "INVALID"  # length is INVALID, never FAIL


# ---------------------------------------------------------------- exact messages / body


def test_messages_and_body_exact():
    seen = {}

    def post(endpoint, body, timeout):
        seen[endpoint] = body
        return fake_resp("x", finish="length")

    cfgs = arm_cfgs()
    runner.do_call(D2, "A", cfgs["A"]["model"], cfgs["A"]["endpoint"], [],
                   MANUAL, EXPECTED["D2"], post, lambda s: None)
    runner.do_call(D2, "C", cfgs["C"]["model"], cfgs["C"]["endpoint"], [],
                   MANUAL, EXPECTED["D2"], post, lambda s: None)
    body_a = seen[cfgs["A"]["endpoint"]]
    assert set(body_a) == {"model", "messages", "max_tokens", "temperature"}
    assert body_a["model"] == "muse-glimmer"
    assert body_a["max_tokens"] == 8000
    assert body_a["temperature"] == 0.6
    assert body_a["messages"] == [
        {"role": "system", "content": runner.SYSTEM_PROMPT},
        {"role": "user", "content": D2["text"]},
    ]
    body_c = seen[cfgs["C"]["endpoint"]]
    assert body_c["model"] == "meta-models/muse-spark-open-1026"
    assert body_c["messages"] == [
        {"role": "system", "content": runner.SYSTEM_PROMPT},
        {"role": "user",
         "content": "Here is the CadQuery manual. Use it.\n\n" + MANUAL},
        {"role": "user", "content": D2["text"]},
    ]


# ---------------------------------------------------------------- budget guard


def test_budget_guard_stops_new_calls(tmp_path):
    calls = []

    def post(endpoint, body, timeout):
        calls.append(endpoint)
        # An INVALID-length reply carrying huge arm-C-sized usage.
        return fake_resp("x", finish="length", prompt=1000,
                         completion=3_000_000)

    records, summary = runner.run_suite(
        DRY_JOBS, EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={}, budget=5.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1)
    total_pairs = len(DRY_JOBS) * 3
    assert len(calls) < total_pairs
    assert summary["budget_stopped"] is True
    assert summary["skipped"] == total_pairs - len(records)


def test_budget_math():
    assert runner.over_budget(
        [{"prompt_tokens": 1000, "completion_tokens": 3_000_000}], 0.0, 5.0)
    assert not runner.over_budget([{}], 0.0, 5.0)


# ---------------------------------------------------------------- key hygiene + outputs


def test_no_key_in_outputs(tmp_path, monkeypatch):
    sentinel = "FAKEKEY-abc123-no-real-key"
    monkeypatch.setenv("GLIMMER_KEY", sentinel)
    monkeypatch.setenv("BASETEN_KEY", sentinel)

    def post(endpoint, body, timeout):
        # Simulate a leaky transport error that echoes the secret.
        raise OSError(f"dial failed, key was {sentinel}!!")

    records, summary = runner.run_suite(
        DRY_JOBS[:1], EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={"A": sentinel, "B": sentinel, "C": sentinel},
        budget=5.0, post_fn=post, sleep_fn=lambda s: None,
        max_workers=2, arms=("A", "C"))
    assert records and all(r["outcome"] == "INVALID" for r in records)
    for name in ("calls.jsonl", "summary.json", "report.md"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert sentinel not in text


def test_full_suite_pass_and_files(tmp_path):
    def post(endpoint, body, timeout):
        return fake_resp(GOOD_CONTENT, finish="stop")

    records, summary = runner.run_suite(
        [D2], EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={}, budget=5.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("B",))
    assert len(records) == 1
    rec = records[0]
    assert rec["outcome"] == "PASS"
    for key in ("job", "level", "arm", "model", "start", "end", "seconds",
                "finish_reason", "usage", "content", "code", "outcome",
                "measurements", "run_error"):
        assert key in rec, key
    assert rec["content"] == GOOD_CONTENT  # content kept verbatim
    assert isinstance(rec["reasoning_len"], int)
    assert isinstance(rec["reasoning_length"], int)
    lines = (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["outcome"] == "PASS"
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["arms"]["B"]["PASS"] == 1
    assert saved["table"]["D2"]["B"] == "PASS"
    assert "Costs" in (tmp_path / "report.md").read_text(encoding="utf-8") or \
        "Cost" in (tmp_path / "report.md").read_text(encoding="utf-8")
