"""Tests for the Keel v2 baseline runner. Offline: no network, no paid calls.

Every model call uses a fake post_fn. Sandbox tests run real sandboxed
answers on this Mac via sandbox-exec. The end-to-end tests read jobs.py at
runtime (no exam job text is copied into this file).

Run with: ~/projects/forge/.venv/bin/python -m pytest -q test_runner.py
"""

import json
import os
import time
import urllib.error

import pytest

import runner
from jobs import JOBS, apply_wrong

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "expected.json"), encoding="utf-8") as _f:
    EXPECTED = json.load(_f)

# Exact PLAN.md 4b system prompt (the manual and request go in as user 1/2).
PLAN_SYSTEM = (
    "You write programs for Keel, Quillon Orbital Works' private part-description tool. "
    "Units are millimetres. Follow the Keel manual exactly. "
    "The program must start with `import keel`, create the part with `p = keel.part(...)`, "
    "and end with `solid = p.finish()`. "
    "Reply with exactly one Python code block and nothing else."
)


def fake_resp(content, finish="stop", prompt=100, completion=50):
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
        "B": {"endpoint": "http://fake-glimmer/v1/chat/completions",
              "model": "muse-glimmer"},
        "C": {"endpoint": "https://inference.baseten.co/v1/chat/completions",
              "model": "meta-models/muse-spark-open-1026"},
    }


def synth_jobs(n=2):
    return [{"id": f"S{i + 1}", "text": f"synthetic request {i + 1}"}
            for i in range(n)]


def program_for(job_id, wrong_index=None):
    """Full answer program for an exam job, built at runtime from jobs.py."""
    body = JOBS[job_id]["ref"]
    if wrong_index is not None:
        body = apply_wrong(body, JOBS[job_id]["wrong"][wrong_index])
    return "import keel\n" + body + "\nsolid = p.finish()\n"


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
    content = "solid = p.finish()"
    assert runner.extract_code(content) == "solid = p.finish()"


# ---------------------------------------------------------------- prompt and body format (PLAN.md 4b)


def test_system_prompt_is_plan_4b_exact():
    assert runner.SYSTEM_PROMPT == PLAN_SYSTEM


def test_messages_are_plan_4b():
    manual = "MANUAL-TEXT"
    messages = runner.build_messages("the request", manual)
    assert messages == [
        {"role": "system", "content": PLAN_SYSTEM},
        {"role": "user",
         "content": "Here is the Keel manual. Use it.\n\n" + manual},
        {"role": "user", "content": "the request"},
    ]


def test_body_keys_and_sampling():
    body = runner.build_body("m", [{"role": "user", "content": "hi"}])
    assert set(body) == {"model", "messages", "max_tokens", "temperature",
                         "top_p", "top_k"}
    assert body["max_tokens"] == 16000
    assert body["temperature"] == 1.0
    assert body["top_p"] == 0.95
    assert body["top_k"] == 64


# ---------------------------------------------------------------- retry rule (as the first-test runner)


def _http_error(code):
    return urllib.error.HTTPError(
        "http://x", code, "err", {}, None)


def test_retry_once_on_5xx_then_succeeds():
    calls = []

    def post(endpoint, body, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise _http_error(500)
        return fake_resp("ok")

    slept = []
    out = runner.post_with_retry(post, "http://x", {}, 1, slept.append)
    assert out["choices"][0]["message"]["content"] == "ok"
    assert len(calls) == 2 and len(slept) == 1


def test_no_retry_on_4xx():
    calls = []

    def post(endpoint, body, timeout):
        calls.append(1)
        raise _http_error(400)

    with pytest.raises(urllib.error.HTTPError):
        runner.post_with_retry(post, "http://x", {}, 1, lambda s: None)
    assert len(calls) == 1


def test_network_error_retries_once_then_invalid():
    calls = []

    def post(endpoint, body, timeout):
        calls.append(1)
        raise urllib.error.URLError("down")

    with pytest.raises(urllib.error.URLError):
        runner.post_with_retry(post, "http://x", {}, 1, lambda s: None)
    assert len(calls) == 2


# ---------------------------------------------------------------- INVALID outcomes (no sandbox needed)


def _invalid_call(tmp_path, resp=None, exc=None, secrets=None):
    def post(endpoint, body, timeout):
        if exc is not None:
            raise exc
        return resp

    run_tmp = tmp_path / "tmp"
    run_tmp.mkdir(exist_ok=True)
    return runner.do_call(
        {"id": "S1", "text": "req"}, "C", 1, "m", "http://x",
        secrets if secrets is not None else [],
        "manual", None, lambda jid: None, post, lambda s: None,
        str(run_tmp), str(tmp_path / "breps"))


def test_length_finish_is_invalid(tmp_path):
    rec = _invalid_call(tmp_path, resp=fake_resp("```python\nx=1\n```",
                                                 finish="length"))
    assert rec["outcome"] == "INVALID"
    assert rec["outcome"] != "FAIL"


def test_empty_reply_is_invalid(tmp_path):
    for empty in ("", "   "):
        rec = _invalid_call(tmp_path, resp=fake_resp(empty))
        assert rec["outcome"] == "INVALID"


def test_network_failure_after_retry_is_invalid(tmp_path):
    rec = _invalid_call(tmp_path, exc=urllib.error.URLError("down"))
    assert rec["outcome"] == "INVALID"
    assert "URLError" in (rec["reason"] or "")


def test_reply_text_is_scrubbed_of_keys(tmp_path):
    secret = "SECRET-ABC-123"
    rec = _invalid_call(
        tmp_path,
        resp=fake_resp(f"cut here {secret} tail", finish="length"),
        secrets=[secret])
    assert secret not in json.dumps(rec)
    assert "***" in rec["content"]


# ---------------------------------------------------------------- sandbox (PLAN.md 4c)


BOX_CODE = (
    "import cadquery as cq\n"
    "solid = cq.Solid.makeBox(2, 3, 4)\n"
)


def _sandbox(code, tmp_path, **kw):
    run_tmp = tmp_path / "tmp"
    run_tmp.mkdir(exist_ok=True)
    return runner.run_sandboxed(code, str(run_tmp), **kw)


def test_sandbox_blocks_socket_connect(tmp_path):
    sb = _sandbox(
        "import socket\n"
        "socket.create_connection((\"8.8.8.8\", 53), timeout=5)\n",
        tmp_path)
    assert sb["result"] is not None and not sb["result"]["ok"]
    assert "PermissionError" in sb["result"]["error"]


def test_sandbox_blocks_write_outside_scratch(tmp_path):
    # NB: pytest tmp_path lives under /private/var/folders, which the
    # sandbox profile deliberately allows, so the probe target must be a
    # denied location: a file next to this test file (the repo checkout).
    run_tmp = tmp_path / "tmp"
    run_tmp.mkdir(exist_ok=True)
    outside = os.path.join(HERE, ".probe-outside-test.txt")
    try:
        if os.path.exists(outside):
            os.unlink(outside)
        sb = runner.run_sandboxed(
            f"open({outside!r}, 'w').write('x')\n", str(run_tmp))
        assert sb["result"] is not None and not sb["result"]["ok"]
        assert "PermissionError" in sb["result"]["error"]
        assert not os.path.exists(outside)
    finally:
        if os.path.exists(outside):
            os.unlink(outside)


def test_sandbox_allows_write_inside_scratch(tmp_path):
    sb = _sandbox(BOX_CODE, tmp_path)
    assert sb["result"] == {"ok": True}
    assert sb["brep_path"] is not None


def test_sandbox_params_cover_reads_and_resolved_scratch(tmp_path):
    run_tmp = tmp_path / "tmp"
    run_tmp.mkdir(exist_ok=True)
    params = runner.sandbox_params(os.path.realpath(str(run_tmp)))
    assert set(params) == {"VENV", "PYHOME", "COMPANY", "SCRATCH", "RUNONE"}
    assert os.path.isdir(params["VENV"])
    assert os.path.isdir(params["PYHOME"])
    assert os.path.isdir(params["COMPANY"])
    assert params["SCRATCH"] == os.path.realpath(str(run_tmp))
    assert params["RUNONE"] == runner.RUN_ONE_PY


def test_sandbox_blocks_read_of_repo_file(tmp_path):
    target = os.path.join(HERE, "expected.json")
    assert os.path.isfile(target)
    sb = _sandbox(f"open({target!r}).read()\n", tmp_path)
    assert sb["result"] is not None and not sb["result"]["ok"]
    assert "PermissionError" in sb["result"]["error"]


def test_sandbox_has_no_key_or_token_env(tmp_path):
    code = (
        "import os\n"
        "bad = [k for k in os.environ if 'KEY' in k or 'TOKEN' in k]\n"
        "assert not bad, 'secrets in env: %r' % (bad,)\n"
    ) + BOX_CODE
    sb = _sandbox(code, tmp_path)
    assert sb["result"] == {"ok": True}, sb["result"]


def test_timeout_kills_infinite_loop(tmp_path):
    sb = _sandbox("while True:\n    pass\n", tmp_path, timeout=5)
    assert sb["timed_out"]
    outcome, reason, _, _ = runner.score_sandboxed(
        "S1", "while True:\n    pass\n", sb, lambda jid: None, None)
    assert outcome == "FAIL"
    assert "timeout" in reason


def test_memory_watchdog_kills_6gb_allocation(tmp_path):
    code = "b = bytearray(6 * 1024 ** 3)\n" + BOX_CODE
    sb = _sandbox(code, tmp_path, timeout=120, max_rss_mb=1000)
    assert sb["oom"], sb
    outcome, reason, _, _ = runner.score_sandboxed(
        "S1", code, sb, lambda jid: None, None)
    assert outcome == "FAIL"
    assert reason == "memory"


# ---------------------------------------------------------------- end to end through sandbox + BREP + referee


def _e2e(tmp_path, job_id, wrong_index, arm="C", sample=1):
    content = "Here it is.\n```python\n" + program_for(
        job_id, wrong_index) + "```\n"

    def post(endpoint, body, timeout):
        assert set(body) == {"model", "messages", "max_tokens",
                             "temperature", "top_p", "top_k"}
        return fake_resp(content)

    out = tmp_path / "out"
    sent, summary = runner.run_suite(
        [{"id": job_id, "text": JOBS[job_id]["text"]}],
        {job_id: EXPECTED[job_id]},
        "manual", str(out), arm_cfgs(), {}, budget=10**6,
        post_fn=post, sleep_fn=lambda s: None, max_workers=1,
        arms=(arm,), budget_c=10**6, max_minutes=10**6, k=1,
        mode="main", build_ref_fn=runner.default_build_ref_fn())
    return sent, summary, out


def test_correct_reference_passes_end_to_end(tmp_path):
    sent, summary, out = _e2e(tmp_path, "M1", None)
    assert len(sent) == 1
    rec = sent[0]
    assert rec["outcome"] == "PASS", rec
    assert rec["measurements"]
    assert rec["prompt_hash"] and rec["seconds"] >= 0
    assert (out / "breps" / "C_M1_s1.brep").is_file()


def test_wrong_version_fails_end_to_end(tmp_path):
    sent, summary, out = _e2e(tmp_path, "M1", 0)
    assert sent[0]["outcome"] == "FAIL", sent[0]
    assert sent[0]["failed_checks"], sent[0]
    assert (out / "breps" / "C_M1_s1.brep").is_file()


# ---------------------------------------------------------------- freeze check (PLAN.md 7)


def _write_plan(tmp_path, entries):
    plan = tmp_path / "PLAN.md"
    plan.write_text(
        "# plan\n\n## 7. Freeze by hash\n```text\n"
        + "".join(f"{sha}  {rel}\n" for sha, rel in entries)
        + "```\n")
    return plan


def _freeze_files(tmp_path):
    files = {}
    for rel in ("a.txt", "b.txt"):
        p = tmp_path / rel
        p.write_text("content of " + rel)
        files[rel] = runner.file_sha256(str(p))
    return files


def _freeze_monkeypatch(monkeypatch, tmp_path, files):
    monkeypatch.setattr(runner, "FROZEN_FILES", tuple(files))
    monkeypatch.setattr(runner, "HERE", str(tmp_path))


def test_freeze_passes_on_matching_hashes(tmp_path, monkeypatch):
    files = _freeze_files(tmp_path)
    _freeze_monkeypatch(monkeypatch, tmp_path, files)
    _write_plan(tmp_path, [(sha, rel) for rel, sha in files.items()])
    assert runner.freeze_check(folder=str(tmp_path)) is not None


def test_freeze_refuses_changed_file(tmp_path, monkeypatch):
    files = _freeze_files(tmp_path)
    _freeze_monkeypatch(monkeypatch, tmp_path, files)
    _write_plan(tmp_path, [(sha, rel) for rel, sha in files.items()])
    (tmp_path / "a.txt").write_text("tampered")
    with pytest.raises(runner.FreezeError):
        runner.freeze_check(folder=str(tmp_path))


def test_freeze_refuses_missing_file(tmp_path, monkeypatch):
    files = _freeze_files(tmp_path)
    _freeze_monkeypatch(monkeypatch, tmp_path, files)
    _write_plan(tmp_path, [(sha, rel) for rel, sha in files.items()])
    (tmp_path / "b.txt").unlink()
    with pytest.raises(runner.FreezeError):
        runner.freeze_check(folder=str(tmp_path))


def test_freeze_refuses_empty_block(tmp_path, monkeypatch):
    _freeze_files(tmp_path)
    _freeze_monkeypatch(monkeypatch, tmp_path, {"a.txt": "x"})
    _write_plan(tmp_path, [])
    with pytest.raises(runner.FreezeError):
        runner.freeze_check(folder=str(tmp_path))


def test_freeze_refuses_unlisted_frozen_file(tmp_path, monkeypatch):
    files = _freeze_files(tmp_path)
    _freeze_monkeypatch(monkeypatch, tmp_path, files)
    one = [k for k in files][:1]
    _write_plan(tmp_path, [(files[one[0]], one[0])])
    with pytest.raises(runner.FreezeError):
        runner.freeze_check(folder=str(tmp_path))


def test_freeze_main_refuses_with_exit_3(tmp_path, monkeypatch):
    _freeze_monkeypatch(monkeypatch, tmp_path, {"a.txt": "x"})
    _write_plan(tmp_path, [])
    rc = runner.main(["--mode", "pilot", "--out", str(tmp_path / "o")])
    assert rc == 3


def test_print_hashes_format():
    lines = runner.print_hashes()
    assert len(lines) == len(runner.FROZEN_FILES)
    for line, rel in zip(lines, runner.FROZEN_FILES):
        sha, path = line.split("  ")
        assert len(sha) == 64 and path == rel


# ---------------------------------------------------------------- decision rules (PLAN.md 4)


def test_decision_run_invalid_and_ordering():
    decision, valid = runner.compute_decision(0.5, 0.2, {"B": 0.06, "C": 0.0})
    assert decision.startswith("RUN INVALID") and not valid


def test_decision_stop_and_ordering_over_no_room():
    decision, valid = runner.compute_decision(0.85, 0.20, {"B": 0.0, "C": 0.0})
    assert decision.startswith("STOP") and valid


def test_decision_no_room():
    decision, _ = runner.compute_decision(0.85, 0.90, {"B": 0.0, "C": 0.0})
    assert decision.startswith("NO ROOM")


def test_decision_go():
    decision, _ = runner.compute_decision(0.60, 0.90, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GO")


def test_decision_go_blocked_by_high_b():
    decision, _ = runner.compute_decision(0.71, 1.00, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GREY")


def test_decision_go_blocked_by_small_gap():
    decision, _ = runner.compute_decision(0.60, 0.84, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GREY")


def test_decision_grey_default():
    decision, _ = runner.compute_decision(0.50, 0.60, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GREY")


def test_decision_whole_point_rounding():
    # 29.6% rounds to 30 whole points: not STOP.
    decision, _ = runner.compute_decision(0.50, 0.296, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GREY")
    # 29.4% rounds to 29: STOP.
    decision, _ = runner.compute_decision(0.50, 0.294, {"B": 0.0, "C": 0.0})
    assert decision.startswith("STOP")
    # 80.4% B rounds to 80 whole points: NO ROOM; 79.4% rounds to 79:
    # with C at 90 the gap is only 11, so GREY.
    decision, _ = runner.compute_decision(0.804, 0.90, {"B": 0.0, "C": 0.0})
    assert decision.startswith("NO ROOM")
    decision, _ = runner.compute_decision(0.794, 0.90, {"B": 0.0, "C": 0.0})
    assert decision.startswith("GREY")


# ---------------------------------------------------------------- bootstrap, McNemar, tally


def test_bootstrap_deterministic_with_seed_0():
    diffs = [1 / 3, 0.0, -1 / 3, 2 / 3, 0.0, 1.0, -2 / 3, 1 / 3] * 4
    first = runner.bootstrap_ci(diffs)
    assert first == runner.bootstrap_ci(diffs)
    assert first == runner.bootstrap_ci(
        diffs, resamples=10000, seed=0)
    lo, hi = first
    assert lo <= hi


def test_bootstrap_empty():
    assert runner.bootstrap_ci([]) == (0.0, 0.0)


def _rec(job, arm, sample, outcome):
    return {"job": job, "arm": arm, "sample": sample, "outcome": outcome}


def test_mcnemar_sample1_counts():
    records = [
        _rec("J1", "B", 1, "PASS"), _rec("J1", "C", 1, "PASS"),
        _rec("J2", "B", 1, "FAIL"), _rec("J2", "C", 1, "PASS"),
        _rec("J3", "B", 1, "PASS"), _rec("J3", "C", 1, "FAIL"),
        _rec("J4", "B", 1, "FAIL"), _rec("J4", "C", 1, "FAIL"),
        _rec("J5", "B", 1, "PASS"),
        _rec("J1", "B", 2, "PASS"), _rec("J1", "C", 2, "PASS"),
    ]
    mc = runner.compute_mcnemar(records, ["J1", "J2", "J3", "J4", "J5"])
    assert mc["n_paired"] == 4
    assert mc["b_c_pass_b_fail"] == 1
    assert mc["c_b_pass_c_fail"] == 1
    assert mc["both_pass"] == 1
    assert mc["neither_pass"] == 1
    assert mc["p_value"] == 1.0


def test_tally_scores_complete_samples_only():
    # B: samples 1-2 complete, sample 3 has a NOT_RUN (a cap stopped it).
    # C: all three samples complete. PLAN.md 5: B's score uses only
    # samples 1-2; the incomplete sample 3 is reported but not scored.
    records = [
        _rec("J1", "B", 1, "PASS"), _rec("J2", "B", 1, "PASS"),
        _rec("J1", "B", 2, "FAIL"), _rec("J2", "B", 2, "PASS"),
        _rec("J1", "B", 3, "PASS"),
        {"job": "J2", "arm": "B", "sample": 3, "outcome": "NOT_RUN",
         "stopped_by": "modal-budget"},
        _rec("J1", "C", 1, "PASS"), _rec("J2", "C", 1, "FAIL"),
        _rec("J1", "C", 2, "PASS"), _rec("J2", "C", 2, "PASS"),
        _rec("J1", "C", 3, "FAIL"), _rec("J2", "C", 3, "FAIL"),
    ]
    per_arm, per_job = runner.tally(records, ["J1", "J2"], ["B", "C"], 3)
    assert per_arm["B"]["complete_samples"] == [1, 2]
    assert per_arm["C"]["complete_samples"] == [1, 2, 3]
    # B scored passes: J1 1/2, J2 2/2 -> mean 0.75. The sample-3 PASS
    # and the NOT_RUN are not scored.
    assert per_job["J1"]["B"] == 1
    assert per_job["J2"]["B"] == 2
    assert per_arm["B"]["score_frac"] == pytest.approx((1 / 2 + 2 / 2) / 2)
    assert per_arm["B"]["PASS"] == 3
    assert per_arm["B"]["NOT_RUN"] == 1
    assert per_arm["C"]["NOT_RUN"] == 0
    assert per_arm["C"]["score_frac"] == pytest.approx((2 / 3 + 1 / 3) / 2)


def test_tally_invalid_rate_counts_scored_answers_only():
    # C: sample 1 complete with 2 INVALID; sample 2 never sent. The
    # INVALID gate (rule 0) counts over scored answers: 2/2, not 2/4.
    records = [
        _rec("J1", "C", 1, "INVALID"), _rec("J2", "C", 1, "INVALID"),
        {"job": "J1", "arm": "C", "sample": 2, "outcome": "NOT_RUN",
         "stopped_by": "baseten-budget"},
        {"job": "J2", "arm": "C", "sample": 2, "outcome": "NOT_RUN",
         "stopped_by": "baseten-budget"},
        _rec("J1", "B", 1, "PASS"), _rec("J2", "B", 1, "PASS"),
        _rec("J1", "B", 2, "PASS"), _rec("J2", "B", 2, "PASS"),
    ]
    per_arm, _ = runner.tally(records, ["J1", "J2"], ["B", "C"], 2)
    assert per_arm["C"]["complete_samples"] == [1]
    assert per_arm["C"]["INVALID"] == 2
    assert per_arm["C"]["NOT_RUN"] == 2
    assert per_arm["C"]["invalid_rate"] == pytest.approx(1.0)
    assert per_arm["B"]["invalid_rate"] == pytest.approx(0.0)


# ---------------------------------------------------------------- caps stop new calls (PLAN.md 5)


def _counted_invalid_post(counter, prompt_tokens=0, completion_tokens=0):
    def post(endpoint, body, timeout):
        counter.append(1)
        return fake_resp("cut", finish="length",
                         prompt=prompt_tokens, completion=completion_tokens)
    return post


def _suite(tmp_path, jobs, arms, k, post, **kw):
    out = tmp_path / "out"
    params = dict(budget=10**6, budget_c=10**6, max_minutes=10**6)
    params.update(kw)
    return runner.run_suite(
        jobs, {}, "manual", str(out), arm_cfgs(), {}, post_fn=post,
        sleep_fn=lambda s: None, max_workers=1, arms=arms, k=k,
        build_ref_fn=lambda jid: None, **params)


def test_k_samples_means_k_requests_per_job_per_arm(tmp_path):
    counter = []
    sent, summary = _suite(
        tmp_path, synth_jobs(2), ("B", "C"), 3,
        _counted_invalid_post(counter))
    assert len(counter) == 2 * 2 * 3 == len(sent)
    assert summary["skipped"] == 0
    assert summary["caps"]["stopped_by"] == []
    assert summary["bootstrap_c_minus_b"]["observed_points"] == 0.0


def test_call_order_is_sample_major(tmp_path):
    # PLAN.md 5: for sample in 1..k, for arm in arms, for job in jobs
    # (jobs in the fixed exam order).
    seen = []
    cfgs = arm_cfgs()

    def post(endpoint, body, timeout):
        arm = "B" if "fake-glimmer" in endpoint else "C"
        seen.append((arm, body["messages"][2]["content"]))
        return fake_resp("cut", finish="length")

    jobs = synth_jobs(3)
    sent, _ = _suite(tmp_path, jobs, ("B", "C"), 2, post)
    assert len(seen) == 3 * 2 * 2 == len(sent)
    expected = [(arm, j["text"])
                for _s in (1, 2)
                for arm in ("B", "C")
                for j in jobs]
    assert seen == expected


def test_modal_budget_stops_b_but_not_c(tmp_path):
    # PLAN.md 5: the Modal cap stops only arm B calls; arm C keeps
    # running. B has no complete sample -> INCOMPLETE, no decision.
    counter = []
    sent, summary = _suite(
        tmp_path, synth_jobs(2), ("B", "C"), 1,
        _counted_invalid_post(counter),
        budget=2.50, gpu_start=time.time() - 10 * 3600)
    assert len(counter) == 2  # only the two arm-C calls were sent
    by_arm = {}
    for r in sent:
        by_arm.setdefault(r["arm"], []).append(r["outcome"])
    assert by_arm["B"] == ["NOT_RUN", "NOT_RUN"]
    assert by_arm["C"] == ["INVALID", "INVALID"]
    assert len(sent) == 4 and summary["n_calls"] == 2
    assert summary["skipped"] == 2
    assert summary["caps"]["stopped_by"] == ["modal-budget"]
    assert summary["arms"]["B"]["NOT_RUN"] == 2
    assert summary["arms"]["B"]["complete_samples"] == []
    assert summary["arms"]["B"]["stopped_by"] == "modal-budget"
    assert summary["arms"]["C"]["complete_samples"] == [1]
    assert summary["arms"]["C"]["stopped_by"] is None
    assert summary["decision"].startswith("INCOMPLETE")


def test_baseten_budget_stops_c_only(tmp_path):
    # One job, k = 2, sample-major: B s1, C s1, B s2, C s2. The first
    # C call costs $1.25, so with budget_c ~ 0 only C s1 is sent; both
    # B calls still go out and each arm keeps one complete sample.
    counter = []
    sent, summary = _suite(
        tmp_path, synth_jobs(1), ("B", "C"), 2,
        _counted_invalid_post(counter, prompt_tokens=10**6),
        budget_c=1e-9)
    assert len(counter) == 3
    assert [(r["arm"], r["sample"], r["outcome"]) for r in sent] == [
        ("B", 1, "INVALID"), ("C", 1, "INVALID"),
        ("B", 2, "INVALID"), ("C", 2, "NOT_RUN"),
    ]
    assert summary["skipped"] == 1
    assert summary["caps"]["stopped_by"] == ["baseten-budget"]
    assert summary["arms"]["C"]["complete_samples"] == [1]
    assert summary["arms"]["C"]["NOT_RUN"] == 1
    assert summary["arms"]["C"]["stopped_by"] == "baseten-budget"
    assert summary["arms"]["B"]["complete_samples"] == [1, 2]
    assert summary["arms"]["B"]["stopped_by"] is None


def test_glimmer_time_limit_stops_new_b_calls(tmp_path):
    counter = []
    sent, summary = _suite(
        tmp_path, synth_jobs(1), ("B", "C"), 1,
        _counted_invalid_post(counter), max_minutes=0)
    assert len(counter) == 1
    assert [(r["arm"], r["outcome"]) for r in sent] == [
        ("B", "NOT_RUN"), ("C", "INVALID")]
    assert summary["skipped"] == 1
    assert summary["caps"]["stopped_by"] == ["glimmer-time"]
    assert summary["arms"]["B"]["stopped_by"] == "glimmer-time"
    assert summary["arms"]["C"]["stopped_by"] is None
    assert summary["decision"].startswith("INCOMPLETE")


def test_not_run_slots_are_logged_not_failed(tmp_path):
    out = tmp_path / "out"
    counter = []
    sent, summary = _suite(
        tmp_path, synth_jobs(2), ("B", "C"), 1,
        _counted_invalid_post(counter),
        budget=2.50, gpu_start=time.time() - 10 * 3600)
    lines = (out / "calls.jsonl").read_text().splitlines()
    logged = [json.loads(line) for line in lines]
    assert len(logged) == len(sent) == 4
    not_run = [r for r in logged if r["outcome"] == "NOT_RUN"]
    assert len(not_run) == 2
    for r in not_run:
        assert r["arm"] == "B"
        assert r["stopped_by"] == "modal-budget"
        assert r["reason"].startswith("NOT RUN")
    assert {r["outcome"] for r in logged} == {"NOT_RUN", "INVALID"}


def _summary(records, job_ids, arms, k, **kw):
    params = dict(mode="main", modal_usd=0.0, baseten_usd=0.0,
                  budget=2.50, budget_c=4.00, max_minutes=60,
                  stopped_by=[], skipped=0, elapsed_s=1.0)
    params.update(kw)
    return runner.build_summary(records, job_ids, arms, k, **params)


def test_incomplete_decision_when_arm_has_no_complete_sample():
    records = [
        _rec("J1", "B", 1, "PASS"),
        {"job": "J2", "arm": "B", "sample": 1, "outcome": "NOT_RUN",
         "stopped_by": "modal-budget"},
        _rec("J1", "C", 1, "PASS"), _rec("J2", "C", 1, "PASS"),
    ]
    summary = _summary(records, ["J1", "J2"], ["B", "C"], 1,
                       stopped_by=["modal-budget"], skipped=1)
    assert summary["decision"].startswith("INCOMPLETE")
    assert summary["run_valid"] is False
    assert summary["arms"]["B"]["score_frac"] is None
    assert summary["arms"]["C"]["complete_samples"] == [1]


def test_decision_uses_complete_samples_when_both_arms_have_some():
    records = [
        _rec("J1", "B", 1, "FAIL"), _rec("J2", "B", 1, "FAIL"),
        _rec("J1", "B", 2, "PASS"),
        {"job": "J2", "arm": "B", "sample": 2, "outcome": "NOT_RUN",
         "stopped_by": "modal-budget"},
        _rec("J1", "C", 1, "PASS"), _rec("J2", "C", 1, "PASS"),
        _rec("J1", "C", 2, "PASS"), _rec("J2", "C", 2, "PASS"),
    ]
    summary = _summary(records, ["J1", "J2"], ["B", "C"], 2,
                       stopped_by=["modal-budget"], skipped=1)
    # B scores 0% on its one complete sample, C 100%: GO (rule 3),
    # decided on scored samples only.
    assert summary["arms"]["B"]["complete_samples"] == [1]
    assert summary["arms"]["B"]["score_frac"] == pytest.approx(0.0)
    assert summary["arms"]["C"]["score_frac"] == pytest.approx(1.0)
    assert summary["decision"].startswith("GO")


def test_default_budget_c_is_4_00():
    import inspect

    assert runner.DEFAULT_BUDGET_C == pytest.approx(4.00)
    sig = inspect.signature(runner.run_suite)
    assert sig.parameters["budget_c"].default == pytest.approx(4.00)
    args = runner.build_parser().parse_args(["--mode", "main"])
    assert args.budget_c == pytest.approx(4.00)
