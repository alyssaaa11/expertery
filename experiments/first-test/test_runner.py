"""Tests for runner.py. No network: every model call uses a fake post_fn.

Run with: ~/projects/forge/.venv/bin/python -m pytest -q test_runner.py
"""

import json
import os
import subprocess
import sys
import tempfile
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
    assert set(body_a) == {"model", "messages", "max_tokens", "temperature",
                           "top_p", "top_k"}
    assert body_a["model"] == "muse-glimmer"
    assert body_a["max_tokens"] == 16000
    assert body_a["temperature"] == 1.0
    assert body_a["top_p"] == 0.95
    assert body_a["top_k"] == 64
    assert body_a["messages"] == [
        {"role": "system", "content": runner.SYSTEM_PROMPT},
        {"role": "user", "content": D2["text"]},
    ]
    body_c = seen[cfgs["C"]["endpoint"]]
    assert set(body_c) == {"model", "messages", "max_tokens", "temperature",
                           "top_p", "top_k"}
    assert body_c["max_tokens"] == 16000
    assert body_c["temperature"] == 1.0
    assert body_c["top_p"] == 0.95
    assert body_c["top_k"] == 64
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


# ---------------------------------------------------------------- new body: all arms

def test_body_b_arm_exact():
    seen = {}

    def post(endpoint, body, timeout):
        seen["body"] = body
        return fake_resp("x", finish="length")

    cfgs = arm_cfgs()
    runner.do_call(D2, "B", cfgs["B"]["model"], cfgs["B"]["endpoint"], [],
                   MANUAL, EXPECTED["D2"], post, lambda s: None)
    body = seen["body"]
    assert set(body) == {"model", "messages", "max_tokens", "temperature",
                         "top_p", "top_k"}
    assert body["max_tokens"] == 16000
    assert body["temperature"] == 1.0
    assert body["top_p"] == 0.95
    assert body["top_k"] == 64


# ---------------------------------------------------------------- decision branches

VALID = {"A": 0.0, "B": 0.0, "C": 0.0}


def test_decision_grey_b40_c60():
    decision, run_valid = runner.compute_decision(0.40, 0.60, VALID)
    assert decision == "grey zone"
    assert run_valid is True


def test_decision_go_b40_c65():
    decision, run_valid = runner.compute_decision(0.40, 0.65, VALID)
    assert decision == "GO to training"
    assert run_valid is True


def test_decision_stop_b85_c100():
    decision, run_valid = runner.compute_decision(0.85, 1.00, VALID)
    assert decision == "STOP (manual is enough)"
    assert run_valid is True


def test_decision_stop_b80_c95():
    decision, run_valid = runner.compute_decision(0.80, 0.95, VALID)
    assert decision == "STOP (manual is enough)"
    assert run_valid is True


def test_decision_cant_teach_c15():
    decision, run_valid = runner.compute_decision(0.40, 0.15, VALID)
    assert decision == "Spark can't teach"
    assert run_valid is True


def test_decision_first_match_wins_stop_over_cant_teach():
    # B >= 80 wins even though C < 20 also matches.
    decision, _ = runner.compute_decision(0.85, 0.10, VALID)
    assert decision == "STOP (manual is enough)"


def test_decision_first_match_wins_stop_over_go():
    # B >= 80 wins even though a GO gap is also present.
    decision, _ = runner.compute_decision(0.85, 1.00, VALID)
    assert decision == "STOP (manual is enough)"


def test_decision_rounds_to_whole_points():
    # 79.6% rounds to 80, so STOP; without rounding it would miss.
    decision, _ = runner.compute_decision(0.796, 0.95, VALID)
    assert decision == "STOP (manual is enough)"
    decision, _ = runner.compute_decision(0.794, 0.95, VALID)
    assert decision == "grey zone"


def test_decision_invalid_prefix():
    decision, run_valid = runner.compute_decision(
        0.40, 0.65, {"A": 0.0, "B": 0.0, "C": 0.06})
    assert run_valid is False
    assert decision == \
        "run not valid (INVALID > 5% in an arm); GO to training"


def test_decision_too_few_scored_calls():
    decision, run_valid = runner.compute_decision(None, 0.65, VALID)
    assert decision == "grey zone (too few scored calls)"
    decision, _ = runner.compute_decision(0.40, None, VALID)
    assert decision == "grey zone (too few scored calls)"


# ---------------------------------------------------------------- arm-C cap

def test_arm_c_cap_skips_later_c_calls(tmp_path):
    def post(endpoint, body, timeout):
        return fake_resp("x", finish="length", prompt=1000,
                         completion=1_000_000)

    jobs = DRY_JOBS[:2]
    records, summary = runner.run_suite(
        jobs, EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={}, budget=50.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("A", "C"),
        budget_c=3.0)
    # Pairs per job are (A, C): both As run, only the first C runs.
    assert [r["arm"] for r in records] == ["A", "C", "A"]
    assert summary["budget_c_stopped"] is True
    assert summary["budget_stopped"] is False
    assert summary["budget_c"] == 3.0
    assert summary["skipped"] == 1
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["budget_c"] == 3.0
    assert saved["budget_c_stopped"] is True
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "arm-C budget" in report


def test_arm_c_cap_math():
    assert runner.over_budget_c(
        [{"prompt_tokens": 1000, "completion_tokens": 1_000_000}], 3.0)
    assert not runner.over_budget_c([{}], 3.0)


# ---------------------------------------------------------------- gpu-start + cost note

COST_NOTE = ("GPU estimate covers only the runner's own wall-clock; the real "
             "Modal cost (incl. cold start) comes from `modal billing report`.")


def test_report_cost_note(tmp_path):
    def post(endpoint, body, timeout):
        return fake_resp("x", finish="length")

    runner.run_suite(
        [D2], EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={}, budget=5.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("A",))
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert COST_NOTE in report


def test_gpu_start_uses_deploy_start(tmp_path):
    import time

    def post(endpoint, body, timeout):
        return fake_resp("x", finish="length")

    gpu_start = time.time() - 3600.0
    records, summary = runner.run_suite(
        [D2], EXPECTED, MANUAL, str(tmp_path), arm_cfgs(),
        key_map={}, budget=500.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("A",),
        gpu_start=gpu_start)
    assert summary["gpu_start"] == gpu_start
    # One GPU-hour at $2.50/h, within a small timing tolerance.
    assert abs(summary["costs"]["gpu_total"] - 2.50) < 0.05
    assert abs(summary["gpu_elapsed_seconds"] - 3600.0) < 30.0
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["gpu_start"] == gpu_start


# ---------------------------------------------------------------- --arms / BR / B2

HINT_PATH = os.path.join(
    os.path.dirname(HERE), "b2-hint", "hint.txt")
with open(HINT_PATH, encoding="utf-8") as _hf:
    HINT = _hf.read().strip()


def test_arms_parsing():
    assert runner.parse_arms("A,B,C") == ("A", "B", "C")
    assert runner.parse_arms("BR,B2") == ("BR", "B2")
    assert runner.parse_arms("B") == ("B",)
    assert runner.parse_arms(" B , C ") == ("B", "C")


def test_arms_parsing_rejects_unknown():
    for bad in ("D", "A,D", "", "B,b2"):
        with pytest.raises(ValueError):
            runner.parse_arms(bad)


def test_br_messages_equal_b():
    assert runner.build_messages(
        "BR", D2["text"], MANUAL) == runner.build_messages(
        "B", D2["text"], MANUAL)
    assert runner.arm_model("BR") == runner.arm_model("B")
    assert runner.arm_uses_manual("BR") is True


def test_b2_system_message_ends_with_hint():
    msgs = runner.build_messages("B2", D2["text"], MANUAL)
    b_msgs = runner.build_messages("B", D2["text"], MANUAL)
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == runner.SYSTEM_PROMPT + " " + HINT
    assert msgs[0]["content"].endswith(HINT)
    # Everything after the system message is identical to B.
    assert msgs[1:] == b_msgs[1:]


def test_c_not_called_when_not_requested(tmp_path):
    seen = []

    def post(endpoint, body, timeout):
        seen.append(endpoint)
        return fake_resp("x", finish="length")

    cfgs = arm_cfgs()
    records, summary = runner.run_suite(
        DRY_JOBS[:1], EXPECTED, MANUAL, str(tmp_path), cfgs,
        key_map={}, budget=5.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("A", "B"))
    assert {r["arm"] for r in records} == {"A", "B"}
    assert set(summary["arms"]) == {"A", "B"}
    assert cfgs["C"]["endpoint"] not in seen
    assert summary["decision"] == "decision: see experiments/b2-hint/PLAN.md"


def test_subset_summary_lists_only_requested_arms(tmp_path):
    def post(endpoint, body, timeout):
        return fake_resp("x", finish="length")

    cfgs = arm_cfgs()
    cfgs["BR"] = dict(cfgs["B"])
    cfgs["B2"] = dict(cfgs["B"])
    records, summary = runner.run_suite(
        [D2], EXPECTED, MANUAL, str(tmp_path), cfgs,
        key_map={}, budget=5.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("BR", "B2"))
    assert [r["arm"] for r in records] == ["BR", "B2"]
    assert set(summary["arms"]) == {"BR", "B2"}
    assert summary["decision"] == "decision: see experiments/b2-hint/PLAN.md"
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Arm C" not in report


# ---------------------------------------------------------------- sandbox (b2-hint, SANDBOX_SPEC item 5)

SB_PROFILE = os.path.realpath(os.path.join(
    os.path.dirname(HERE), "b2-hint", "sandbox_cq.sb"))
RUN_ONE_CQ = os.path.realpath(os.path.join(
    os.path.dirname(HERE), "b2-hint", "run_one_cq.py"))


def _sandbox_available():
    try:
        p = subprocess.run(
            ["sandbox-exec", "-n", "no-network", "/bin/echo", "hi"],
            capture_output=True, text=True, timeout=15)
        return p.returncode == 0
    except Exception:
        return False


_SANDBOX_OK = _sandbox_available()
needs_sandbox = pytest.mark.skipif(
    not _SANDBOX_OK,
    reason="sandbox-exec cannot apply a profile in this environment")


def _run_one_direct(code, tmp_path):
    scratch = os.path.realpath(str(tmp_path))
    with open(os.path.join(scratch, "answer.py"), "w", encoding="utf-8") as f:
        f.write(code)
    return subprocess.run(
        [sys.executable, "-I", RUN_ONE_CQ, scratch],
        capture_output=True, text=True, timeout=180)


def test_run_one_direct_good(tmp_path):
    r = _run_one_direct(GOOD_CODE, tmp_path)
    assert r.returncode == 0, r.stderr[-500:]
    step = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()][-1]
    assert step.endswith(".step") and os.path.isfile(step)
    m = runner.parse_measure_line(r.stdout)
    assert set(m) == {"xmin", "ymin", "zmin", "xmax", "ymax", "zmax",
                      "volume", "solids"}
    assert m["solids"] == 1 and m["volume"] > 0


def test_run_one_direct_no_result(tmp_path):
    r = _run_one_direct("x = 1\n", tmp_path)
    assert r.returncode == 2
    assert "ERROR: no variable named 'result'" in r.stderr


def test_run_one_direct_crash(tmp_path):
    r = _run_one_direct("raise ValueError('boom')\n", tmp_path)
    assert r.returncode != 0


def test_sandbox_profile_contents():
    with open(SB_PROFILE, encoding="utf-8") as f:
        text = f.read()
    assert "(allow default)" in text
    assert "(deny network*)" in text
    assert '(param "SCRATCH")' in text
    assert '(param "RUNONE")' in text
    assert '(param "VENV")' in text
    assert '(param "PYHOME")' in text
    assert "(allow file-read-metadata)" in text
    assert '(literal "/dev/null")' in text
    assert '(param "COMPANY")' not in text
    assert text.count("(") == text.count(")")


def test_sandbox_launch_failure_is_fail(tmp_path):
    shape, err = runner.run_code(
        "result = 1", sandbox_profile="/nonexistent/profile.sb",
        sandbox_dir=str(tmp_path))
    assert shape is None
    assert err.startswith("answer code failed")


@needs_sandbox
def test_sandbox_good_passes_wrong_fails(tmp_path):
    shape, err, measure = runner.run_code_sandboxed(
        GOOD_CODE, str(tmp_path), SB_PROFILE, timeout=120)
    assert err is None, err
    assert measure["solids"] == 1 and measure["volume"] > 0
    import checks
    passed, fails, _ = checks.score(shape, D2["build"](), EXPECTED["D2"])
    assert passed, fails
    outcome, fails, _, _, _ = runner.score_content(
        WRONG_CONTENT, "stop", D2["build"], EXPECTED["D2"], timeout=120,
        sandbox_profile=SB_PROFILE, sandbox_dir=str(tmp_path))
    assert outcome == "FAIL"
    assert fails


@needs_sandbox
def test_sandbox_blocks_reads(tmp_path):
    probe_path = None
    try:
        with tempfile.NamedTemporaryFile(
                dir="/tmp", delete=False, suffix=".probe") as f:
            f.write(b"probe-secret")
            probe_path = f.name
        home = os.path.expanduser("~")
        probe = (
            "import os\n"
            "targets = [%r, %r, %r]\n"
            "blocked = 0\n"
            "for t in targets[:1]:\n"
            "    try:\n"
            "        with open(t, encoding='utf-8') as f:\n"
            "            f.read()\n"
            "    except OSError:\n"
            "        blocked += 1\n"
            "try:\n"
            "    os.listdir(%r)\n"
            "except OSError:\n"
            "    blocked += 1\n"
            "try:\n"
            "    with open(targets[2], encoding='utf-8') as f:\n"
            "        f.read()\n"
            "except OSError:\n"
            "    blocked += 1\n"
            "if blocked == 3:\n"
            "    raise RuntimeError('sandbox blocked all 3 reads')\n"
            "import cadquery as cq\n"
            "result = cq.Workplane('XY').box(1, 1, 1)\n"
        ) % (os.path.join(HERE, "expected.json"), probe_path, probe_path,
             home)
        shape, err = runner.run_code(
            probe, timeout=120, sandbox_profile=SB_PROFILE,
            sandbox_dir=str(tmp_path))
        assert shape is None
        assert "answer code failed" in err
        assert "blocked all 3 reads" in err
    finally:
        if probe_path and os.path.isfile(probe_path):
            os.remove(probe_path)


@needs_sandbox
def test_sandbox_blocks_write_net_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PROBE_FAKE_KEY", "sentinel-no-real-key")
    monkeypatch.setenv("PROBE_FAKE_TOKEN", "sentinel-no-real-key")
    flag = "/tmp/sandbox_write_probe_xyz"
    try:
        if os.path.isfile(flag):
            os.remove(flag)
    except OSError:
        pass
    probe = (
        "import os, socket\n"
        "problems = []\n"
        "try:\n"
        "    with open(%r, 'w') as f:\n"
        "        f.write('x')\n"
        "    problems.append('write')\n"
        "except OSError:\n"
        "    pass\n"
        "try:\n"
        "    s = socket.create_connection(('8.8.8.8', 53), timeout=5)\n"
        "    s.close()\n"
        "    problems.append('net')\n"
        "except OSError:\n"
        "    pass\n"
        "leaked = [k for k in os.environ if 'KEY' in k or 'TOKEN' in k]\n"
        "if leaked:\n"
        "    problems.append('env:' + ','.join(sorted(leaked)))\n"
        "if not problems:\n"
        "    raise RuntimeError('sandbox blocked write/net, env clean')\n"
        "import cadquery as cq\n"
        "result = cq.Workplane('XY').box(1, 1, 1)\n"
    ) % flag
    shape, err = runner.run_code(
        probe, timeout=120, sandbox_profile=SB_PROFILE,
        sandbox_dir=str(tmp_path))
    try:
        if os.path.isfile(flag):
            os.remove(flag)
    except OSError:
        pass
    assert shape is None
    assert "answer code failed" in err
    assert "blocked write/net, env clean" in err


@needs_sandbox
def test_sandbox_timeout(tmp_path):
    shape, err = runner.run_code(
        "while True: pass", timeout=10, sandbox_profile=SB_PROFILE,
        sandbox_dir=str(tmp_path))
    assert shape is None
    assert "timeout" in err


# ---------------------------------------------------------------- B-max arm BX (BMAX_SPEC item 4)

CRASH_CONTENT = "```python\nraise RuntimeError('CRASHMARK boom')\n```\n"
FAKE_MEASURE = {"xmin": -20.0, "ymin": -10.0, "zmin": 0.0, "xmax": 20.0,
                "ymax": 10.0, "zmax": 15.0, "volume": 999.9, "solids": 1}
BX_EXAMPLES = [{"text": "EX1 text", "code": "EX1 code"},
               {"text": "EX2 text", "code": "EX2 code"},
               {"text": "EX3 text", "code": "EX3 code"}]


def _scripted_posts(*resps):
    calls = []

    def post(endpoint, body, timeout):
        calls.append(body)
        return resps[min(len(calls) - 1, len(resps) - 1)]

    post.calls = calls
    return post


def _bx_fake_run(code, run_tmp, profile, timeout=None, **kw):
    if "CRASHMARK" in code:
        return None, "answer code failed (exit 1): CRASHMARK boom", None
    return D2["build"](), None, dict(FAKE_MEASURE)


def _bx_call(monkeypatch, post, **kw):
    monkeypatch.setattr(runner, "run_code_sandboxed", _bx_fake_run)
    return runner.do_bx_call(
        D2, "muse-glimmer", "http://fake-glimmer/v1/chat/completions", [],
        MANUAL, EXPECTED["D2"], post, lambda s: None,
        sandbox_profile="dummy-profile", sandbox_dir=kw.get("sandbox_dir"),
        examples=BX_EXAMPLES, hint_text=HINT)


def test_bx_messages_examples_and_body():
    post = _scripted_posts(fake_resp("DONE"))
    rec = runner.do_bx_call(
        D2, "muse-glimmer", "http://x", [], MANUAL, EXPECTED["D2"], post,
        lambda s: None, sandbox_profile="dummy-profile",
        examples=BX_EXAMPLES, hint_text=HINT)
    assert rec["outcome"] == "FAIL"  # DONE with nothing built
    body = post.calls[0]
    assert body["chat_template_kwargs"] == {"reasoning_strength": "high"}
    msgs = body["messages"]
    assert msgs[0] == {"role": "system",
                       "content": runner.SYSTEM_PROMPT + " " + HINT}
    assert msgs[0]["content"].endswith(HINT)
    assert msgs[1] == {"role": "user",
                       "content": "Here is the CadQuery manual. Use it.\n\n"
                       + MANUAL}
    users = "\n".join(m["content"] for m in msgs[1:] if m["role"] == "user")
    assert users.index(MANUAL) < users.index("EX1 text")
    assert users.index("EX1 text") < users.index("EX2 text")
    assert users.index("EX2 text") < users.index("EX3 text")
    assert users.index("EX3 text") < users.index(D2["text"])


def test_b_b2_bodies_have_no_template_kwargs():
    seen = []

    def post(endpoint, body, timeout):
        seen.append(body)
        return fake_resp("x", finish="length")

    runner.do_call(D2, "B", "muse-glimmer", "http://x", [], MANUAL,
                   EXPECTED["D2"], post, lambda s: None)
    runner.do_call(D2, "B2", "muse-glimmer", "http://x", [], MANUAL,
                   EXPECTED["D2"], post, lambda s: None)
    for body in seen:
        assert "chat_template_kwargs" not in body
        assert set(body) == {"model", "messages", "max_tokens", "temperature",
                             "top_p", "top_k"}


def test_bx_examples_format():
    assert runner.format_bx_examples(
        [{"text": "T one", "code": "C one"}]) == (
        "\n\nSolved examples (same style as your job):\n\n"
        "Job: T one\nAnswer:\n```python\nC one\n```\n\n")


def test_bx_self_check_uses_only_measure_values():
    import inspect
    assert len(inspect.signature(
        runner.bx_self_check_message).parameters) == 1
    assert runner.bx_self_check_message.__closure__ is None
    m = {"xmin": -20.25, "ymin": -10.5, "zmin": 0.125, "xmax": 20.75,
         "ymax": 10.125, "zmax": 15.5, "volume": 1234.5, "solids": 2}
    text = runner.bx_self_check_message(m)
    assert text.startswith("Your part was built. Measured:")
    for v in ("-20.25", "-10.5", "0.125", "20.75", "10.125", "15.5",
              "1234.5"):
        assert v in text
    assert "2 solid(s)" in text


def test_bx_error_message_head():
    msg = runner.bx_error_message("E" * 5000)
    assert msg.startswith("Your code failed when it ran:\n")
    assert msg.endswith("in one Python code block.")
    assert "E" * 2000 in msg
    assert "E" * 2001 not in msg


def test_bx_requires_sandbox():
    with pytest.raises(ValueError):
        runner.do_bx_call(
            D2, "m", "http://x", [], MANUAL, EXPECTED["D2"],
            lambda e, b, t: fake_resp("x"), lambda s: None)


def test_bx_crash_then_good(tmp_path, monkeypatch):
    post = _scripted_posts(
        fake_resp(CRASH_CONTENT, prompt=100, completion=50),
        fake_resp(GOOD_CONTENT, prompt=200, completion=60))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert len(post.calls) == 2
    assert rec["outcome"] == "PASS"
    assert rec["code"] == runner.extract_code(GOOD_CONTENT)
    second_users = [m["content"] for m in post.calls[1]["messages"]
                    if m["role"] == "user"]
    assert any("CRASHMARK" in u for u in second_users)
    assert rec["model_calls"] == 2
    assert rec["prompt_tokens_total"] == 300
    assert rec["completion_tokens_total"] == 110
    assert [r["event"] for r in rec["bx_rounds"]] == ["crash", "built"]


def test_bx_good_then_done(tmp_path, monkeypatch):
    post = _scripted_posts(fake_resp(GOOD_CONTENT), fake_resp("DONE"))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert len(post.calls) == 2
    assert rec["outcome"] == "PASS"
    assert rec["code"] == runner.extract_code(GOOD_CONTENT)
    assert [r["event"] for r in rec["bx_rounds"]] == ["built", "DONE"]


def test_bx_never_done_takes_three_calls(tmp_path, monkeypatch):
    post = _scripted_posts(fake_resp(GOOD_CONTENT), fake_resp(GOOD_CONTENT),
                           fake_resp(GOOD_CONTENT))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert len(post.calls) == 3
    assert rec["outcome"] == "PASS"
    assert [r["event"] for r in rec["bx_rounds"]] == ["built"] * 3


def test_bx_good_then_crash_keeps_earlier(tmp_path, monkeypatch):
    post = _scripted_posts(fake_resp(GOOD_CONTENT), fake_resp(CRASH_CONTENT),
                           fake_resp(CRASH_CONTENT))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert rec["outcome"] == "PASS"
    assert rec["code"] == runner.extract_code(GOOD_CONTENT)


def test_bx_cutoff_round1_is_invalid(monkeypatch, tmp_path):
    post = _scripted_posts(fake_resp("part", finish="length"))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert len(post.calls) == 1
    assert rec["outcome"] == "INVALID"
    assert rec["outcome"] != "FAIL"


def test_bx_cutoff_round2_keeps_best(tmp_path, monkeypatch):
    post = _scripted_posts(fake_resp(GOOD_CONTENT),
                           fake_resp("part", finish="length"))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    assert len(post.calls) == 2
    assert rec["outcome"] == "PASS"
    assert [r["event"] for r in rec["bx_rounds"]] == ["built", "cut off"]


def test_bx_token_latency_totals_sum(tmp_path, monkeypatch):
    post = _scripted_posts(
        fake_resp(GOOD_CONTENT, prompt=10, completion=5),
        fake_resp(GOOD_CONTENT, prompt=20, completion=7),
        fake_resp(GOOD_CONTENT, prompt=30, completion=9))
    rec = _bx_call(monkeypatch, post, sandbox_dir=str(tmp_path))
    rounds = rec["bx_rounds"]
    assert rec["prompt_tokens_total"] == sum(r["prompt_tokens"] for r in rounds)
    assert rec["completion_tokens_total"] == sum(
        r["completion_tokens"] for r in rounds)
    assert rec["latency_total"] == round(
        sum(r["latency"] for r in rounds), 3)
    assert rec["model_calls"] == len(rounds) == 3


def test_bx_cost_speed_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "run_code_sandboxed", _bx_fake_run)

    def post(endpoint, body, timeout):
        return fake_resp(GOOD_CONTENT, prompt=100, completion=50)

    cfgs = arm_cfgs()
    cfgs["BX"] = dict(cfgs["B"])
    records, summary = runner.run_suite(
        [D2], EXPECTED, MANUAL, str(tmp_path), cfgs,
        key_map={}, budget=50.0, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=("B", "BX"),
        sandbox_profile="dummy-profile")
    assert {r["arm"] for r in records} == {"B", "BX"}
    assert summary["arms"]["B"]["PASS"] == 1
    assert summary["arms"]["BX"]["PASS"] == 1
    assert summary["arms"]["B"]["mean_calls_per_job"] == 1
    assert summary["arms"]["BX"]["mean_calls_per_job"] == 3
    assert summary["arms"]["B"]["mean_tokens_per_job"] == 150
    assert summary["arms"]["BX"]["mean_tokens_per_job"] == 450
    assert summary["arms"]["BX"]["tokens_per_pass"] == 450
    assert summary["arms"]["BX"]["latency_per_pass"] is not None
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Cost and speed" in report
    lines = (tmp_path / "calls.jsonl").read_text(
        encoding="utf-8").splitlines()
    # Arm B: one final record; arm BX: 3 round records + one final record.
    assert len(lines) == 5
    parsed = [json.loads(ln) for ln in lines]
    assert sum(1 for p in parsed if p.get("bx_final") is False) == 3
    assert sum(1 for p in parsed if p.get("bx_final") is True) == 1
    assert sum(1 for p in parsed if "bx_final" not in p) == 1


def test_cli_refuses_missing_sandbox(tmp_path):
    with pytest.raises(SystemExit):
        runner.main(["--jobs", "dry", "--out", str(tmp_path),
                     "--sandbox", "/nonexistent/profile.sb", "--arms", "A"])


def test_cli_bx_requires_sandbox(tmp_path):
    with pytest.raises(SystemExit):
        runner.main(["--jobs", "dry", "--out", str(tmp_path), "--arms", "BX"])


@needs_sandbox
def test_bx_crash_then_good_e2e(tmp_path):
    calls = []

    def post(endpoint, body, timeout):
        calls.append(body)
        if len(calls) == 1:
            return fake_resp(
                "```python\nraise RuntimeError('BOOM-E2E')\n```\n")
        return fake_resp(GOOD_CONTENT)

    rec = runner.do_bx_call(
        D2, "muse-glimmer", "http://x", [], MANUAL, EXPECTED["D2"], post,
        lambda s: None, sandbox_profile=SB_PROFILE,
        sandbox_dir=str(tmp_path))
    assert len(calls) == 2
    assert rec["outcome"] == "PASS"
    assert [r["event"] for r in rec["bx_rounds"]] == ["crash", "built"]
