"""Offline tests for runner_fc.py (no Modal, no network: fake HTTP/box/grader).

Any test that could reach a real Modal call injects a fake or
monkeypatches the real entry to raise. Never opens blind/ folders or
expected*.json: decisions run on synthetic records, grading on synthetic
grades.
"""
import io
import json
import os
import sys
import urllib.error

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import runner_fc


# ------------------------------------------------------- prompt + manual


def test_prompt_is_system_plus_manual_plus_job():
    manual = runner_fc.load_manual()  # the frozen manual loads fine
    assert len(manual) == 21640
    msgs = runner_fc.build_messages("make a box", manual)
    assert msgs[0] == {"role": "system",
                       "content": runner_fc.FC_SYSTEM_PROMPT}
    assert "Part" in msgs[0]["content"] and "result" in msgs[0]["content"]
    assert msgs[1]["content"].startswith(runner_fc.FC_MANUAL_PREFIX)
    assert manual in msgs[1]["content"]  # manual carried, CadQuery-free here
    assert msgs[2] == {"role": "user", "content": "make a box"}
    body = runner_fc.build_body_fc("m", msgs)
    assert body["max_tokens"] == 16000 and body["temperature"] == 1.0
    assert body["top_p"] == 0.95 and body["top_k"] == 64  # arm-B sampling


def test_changed_manual_is_refused(tmp_path):
    good = tmp_path / "manual.md"
    good.write_text(runner_fc.load_manual(), encoding="utf-8")
    assert runner_fc.load_manual(str(good)) == runner_fc.load_manual()
    bad = tmp_path / "manual2.md"
    bad.write_text(runner_fc.load_manual() + " ", encoding="utf-8")
    with pytest.raises(runner_fc.ManualChanged):
        runner_fc.load_manual(str(bad))


def test_runner_reuses_frozen_helpers():
    src = open(os.path.join(HERE, "runner_fc.py"), encoding="utf-8").read()
    assert "import runner" in src  # the frozen runner, not a copy
    for helper in ("post_with_retry", "extract_code", "over_budget",
                   "over_budget_c", "arm_stats", "build_body"):
        assert helper in src


# ------------------------------------------------------- failure tags


def test_failure_tags():
    assert runner_fc.tag_failure("length", "```x```", "", False, []) == "INVALID"
    assert runner_fc.tag_failure(None, "", "empty reply", False, []) == "INVALID"
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```",
        "TypeError: typo here", False, []) == "api_error"  # raised: tool gap
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```",
        "timeout after 60s running answer code", False, []) == "api_error"
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```",
        "PermissionError: denied", False, []) == "api_error"
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```", "refused import: cadquery",
        False, []) == "api_error"
    # A missing `result` is an API-knowledge miss, not a wrong shape.
    assert runner_fc.tag_failure(
        "stop", "```python\nx=1\n```",
        "the answer wrote no STEP: ERROR: no variable named 'result'",
        False, []) == "api_error"
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```", None,
        True, ["bbox"]) == "wrong_geometry"  # built but failed the checker
    assert runner_fc.tag_failure(
        "stop", "```python\nr=1\n```",
        "ERROR: result is not a Part solid",
        False, []) == "wrong_geometry"


# ------------------------------------------------------- decision rules


def rec(job, arm, outcome, tag=""):
    return {"job": job, "arm": arm, "outcome": outcome, "failure_tag": tag,
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}}


def jobs(n=30):
    return ["J%d" % (i + 1) for i in range(n)]


def test_rule1_teacher_under_70_is_invalid():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 10 else "FAIL",
                   "" if i < 10 else "api_error")
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 12 else "FAIL",
                    "" if i < 12 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision_t"] == "stay on CadQuery " \
        "(RUN INVALID for FreeCAD: teacher < 70%)"
    assert d["decision"] == d["decision_t"]  # S agrees: no escalation line


def test_rule2_clear_gap_is_freecad_target():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 15 else "FAIL",
                   "" if i < 15 else "api_error")
               for i, j in enumerate(ids)]
    # S 23/30 (77%), 8 wins over G, gap 27: target on S alone too.
    records += [rec(j, "S", "PASS" if i < 23 else "FAIL",
                    "" if i < 23 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision_t"] == "FreeCAD target"
    assert d["decision_s"] == "FreeCAD target" and d["agree"] is True
    assert d["decision"] == "FreeCAD target"
    assert d["wonder_share"] == 0.0  # no Wonder needed


def test_rule3_strong_glimmer_stays_on_cadquery():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 24 else "FAIL",
                   "" if i < 24 else "api_error")
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 25 else "FAIL",
                    "" if i < 25 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision"] == "stay on hard CadQuery jobs"


def test_rule4_grey_defaults_to_cadquery():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 20 else "FAIL",
                   "" if i < 20 else
                   ("api_error" if i < 22 else "wrong_geometry"))
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 22 else "FAIL",
                    "" if i < 22 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision"] == "stay on CadQuery (grey zone)"


def test_rule4_api_error_rescue_needs_six_wins():
    ids = jobs()
    # G 18/30 with 10/12 FAILs api_error; S 24/30, 6 wins: grey rescue.
    records = [rec(j, "G", "PASS" if i < 18 else "FAIL",
                   "" if i < 18 else
                   ("api_error" if i < 28 else "wrong_geometry"))
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 24 else "FAIL",
                    "" if i < 24 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision"] == "FreeCAD target"
    assert d["decision_s"] == "FreeCAD target"


def test_rule5_disagreement_names_wonder_escalation():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 15 else "FAIL",
                   "" if i < 15 else "api_error")
               for i, j in enumerate(ids)]
    # S 18/30 (60%): INVALID on its own. W rescues 6 failed jobs...
    records += [rec(j, "S", "PASS" if i < 18 else
                    ("INVALID" if j == "J30" else "FAIL"),
                    "" if i < 18 else "")
                for i, j in enumerate(ids)]
    for j in ["J19", "J20", "J21", "J22", "J23", "J24"]:
        records.append(rec(j, "W", "PASS"))
    # ...but a W PASS on an S-INVALID job does not count toward T.
    records.append(rec("J30", "W", "PASS"))
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision_t"] == "FreeCAD target"  # T 24/30, 9 wins, gap 30
    assert "INVALID" in d["decision_s"]
    assert d["agree"] is False
    assert d["decision"] == "FreeCAD target only with Wonder escalation " \
        "(closed API)"
    assert d["wonder_share"] == pytest.approx(0.25)  # 6 rescues / 24 T passes


# ------------------------------------------------------- calls (fake HTTP/box/grader)


def fake_chat(content, finish="stop", prompt=100, completion=50, **extra):
    usage = {"prompt_tokens": prompt, "completion_tokens": completion}
    usage.update(extra)
    return {"choices": [{"message": {"content": content},
                         "finish_reason": finish}],
            "usage": usage}


def fake_post_for(content_map):
    """post_fn(endpoint, body, timeout) serving canned replies per job."""

    def _post(endpoint, body, timeout):
        job_text = body["messages"][-1]["content"]
        content = content_map.get(job_text, "```python\nresult = 1\n```")
        return fake_chat(content)

    return _post


PASS_GRADE = {"verdict": "PASS", "tight": "PASS", "fails": [],
              "fails_tight": [], "measurements": {"solids": 1}}


def test_do_fc_call_outcomes():
    job = {"id": "D1", "level": "dry", "text": "make a box"}
    manual = "MANUAL"
    post = fake_post_for({})
    no_sleep = lambda s: None  # noqa: E731
    ok_box = lambda code: {"step_bytes": b"S", "measure": {}, "log": ""}
    ok_grade = lambda jid, step: dict(PASS_GRADE)
    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, post, no_sleep,
                             ok_box, ok_grade)
    assert r["outcome"] == "PASS" and r["failure_tag"] == ""
    assert r["tight"] == "PASS" and r["code"].strip() == "result = 1"

    def boom_box(code):
        raise ConnectionError("sandbox down")

    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, post, no_sleep,
                             boom_box, ok_grade)
    # A box exception is a harness failure: INVALID, error text kept.
    assert r["outcome"] == "INVALID" and r["failure_tag"] == "harness"
    assert "sandbox down" in r["run_error"]

    def boom_grade(jid, step):
        raise TimeoutError("grader down")

    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, post, no_sleep,
                             ok_box, boom_grade)
    assert r["outcome"] == "INVALID" and r["failure_tag"] == "harness"
    assert "grader down" in r["run_error"]

    def no_step_box(code):
        return {"step_bytes": None, "measure": None, "log": "",
                "run_error": "the answer wrote no STEP: "
                             "ERROR: no variable named 'result'"}

    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, post, no_sleep,
                             no_step_box, ok_grade)
    # No STEP is the answer's failure, with run_one_fc's ERROR line kept.
    assert r["outcome"] == "FAIL" and r["failure_tag"] == "api_error"
    assert "no variable named 'result'" in r["run_error"]

    bad_grade = lambda jid, step: {"verdict": "FAIL", "tight": "FAIL",
                                   "fails": ["bbox"], "fails_tight": ["bbox"],
                                   "measurements": {"solids": 1}}
    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, post, no_sleep,
                             ok_box, bad_grade)
    assert r["outcome"] == "FAIL" and r["failure_tag"] == "wrong_geometry"
    assert r["fails"] == ["bbox"]

    cut = fake_post_for({"make a box": "```python\nx\n```"})
    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual,
                             lambda e, b, t: fake_chat("```x", finish="length"),
                             no_sleep, ok_box, ok_grade)
    assert r["outcome"] == "INVALID" and r["failure_tag"] == "INVALID"
    assert cut is not None

    def boom_post(endpoint, body, timeout):
        raise ConnectionError("down")

    r = runner_fc.do_fc_call(job, "G", "m", "e", [], manual, boom_post,
                             no_sleep, ok_box, ok_grade)
    assert r["outcome"] == "INVALID"  # failed call is never FAIL


def test_do_fc_call_never_touches_modal(monkeypatch):
    import modal

    def _boom(*args, **kwargs):
        raise AssertionError("a real Modal call would start here")

    monkeypatch.setattr(modal.Sandbox, "create", _boom)
    job = {"id": "D1", "level": "dry", "text": "make a box"}
    post = fake_post_for({})
    r = runner_fc.do_fc_call(
        job, "G", "m", "e", [], "MANUAL", post, lambda s: None,
        lambda code: {"step_bytes": b"S", "measure": {}, "log": ""},
        lambda jid, step: dict(PASS_GRADE))
    assert r["outcome"] == "PASS"


def test_suite_offline_end_to_end(tmp_path):
    jobs = [{"id": "D1", "level": "dry", "text": "job one"},
            {"id": "D2", "level": "dry", "text": "job two"}]
    post = fake_post_for({})
    box = lambda code: {"step_bytes": b"S", "measure": {}, "log": ""}

    def grade(jid, step):
        if jid == "D1":
            return dict(PASS_GRADE)
        return {"verdict": "FAIL", "tight": "FAIL", "fails": ["bbox"],
                "fails_tight": ["bbox"], "measurements": {"solids": 1}}

    cfgs = {"G": {"endpoint": "g", "model": "gm"},
            "S": {"endpoint": "s", "model": "sm"}}
    out = str(tmp_path / "run")
    sent, summary = runner_fc.run_suite_fc(
        jobs, "MANUAL", out, cfgs, {}, budget=10.0, arms=("G", "S"),
        k=1, workers=2, post_fn=post, sleep_fn=lambda s: None,
        exec_fn=box, grade_fn=grade)
    assert len(sent) == 4  # 2 jobs x 2 arms, k = 1
    assert summary["arms"]["G"]["PASS"] == 1
    assert summary["failure_tags"]["S"]["wrong_geometry"] == 1
    assert summary["jobs_passed_by_S_not_G"] == []
    assert summary["decision_t"] and summary["decision_s"]
    for name in ("calls.jsonl", "summary.json", "report.md"):
        assert os.path.isfile(os.path.join(out, name))
    report = open(os.path.join(out, "report.md"), encoding="utf-8").read()
    assert "Decision on T:" in report and "Wonder's share" in report


def test_suite_budget_guard_stops_new_calls(tmp_path):
    jobs = [{"id": "D1", "level": "dry", "text": "job one"}]
    cfgs = {"G": {"endpoint": "g", "model": "gm"}}
    sent, summary = runner_fc.run_suite_fc(
        jobs, "MANUAL", str(tmp_path / "run"), cfgs, {}, budget=0.0,
        arms=("G",), k=1, workers=1, post_fn=fake_post_for({}),
        sleep_fn=lambda s: None,
        exec_fn=lambda code: {"step_bytes": b"S", "measure": {}, "log": ""},
        grade_fn=lambda jid, step: dict(PASS_GRADE))
    assert sent == [] and summary["budget_stopped"] is True


def test_s_failed_ids_skip_invalid(tmp_path):
    calls = tmp_path / "calls.jsonl"
    calls.write_text("\n".join([
        json.dumps({"arm": "S", "job": "J1", "outcome": "FAIL"}),
        json.dumps({"arm": "S", "job": "J2", "outcome": "INVALID"}),
        json.dumps({"arm": "S", "job": "J3", "outcome": "PASS"}),
        json.dumps({"arm": "G", "job": "J4", "outcome": "FAIL"}),
    ]), encoding="utf-8")
    assert runner_fc.s_failed_job_ids(str(tmp_path)) == ["J1"]


def test_wonder_money():
    u = {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000,
         "cached_tokens": 1_000_000}
    assert runner_fc.cost_w_of_usage(u) == pytest.approx(20.0 + 4.0 + 0.2)
    assert runner_fc.over_budget_w([u] * 10, 1.0) is True
    assert runner_fc.over_budget_w([], 3.0) is False


# ------------------------------------------------------- HTTP headers


class FakeResp:
    def __init__(self, payload):
        self._buf = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return self._buf.read()


def test_s_carries_affinity_and_logs_cached(monkeypatch):
    import urllib.request

    seen = {}

    def _open(req, timeout=None):
        seen["headers"] = {k.lower(): v for k, v in req.header_items()}
        seen["url"] = req.full_url
        return FakeResp(fake_chat("```python\nresult = 1\n```",
                                  **{"cached_tokens": 7}))

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    cfgs = {"S": {"endpoint": "https://x.test/v1/chat/completions",
                  "model": "sm"}}
    post = runner_fc.default_post_fns(cfgs, {"S": "k"}, "aff-123")
    data = post("https://x.test/v1/chat/completions",
                {"model": "sm", "messages": []}, 10)
    assert seen["headers"].get("x-session-affinity") == "aff-123"
    assert data["usage"]["cached_tokens"] == 7
    job = {"id": "D1", "level": "dry", "text": "t"}
    r = runner_fc.do_fc_call(
        job, "S", "sm", cfgs["S"]["endpoint"], [], "MANUAL", post,
        lambda s: None,
        lambda code: {"step_bytes": b"S", "measure": {}, "log": ""},
        lambda jid, step: dict(PASS_GRADE))
    assert r["cached_tokens"] == 7 and r["outcome"] == "PASS"


def test_w_falls_back_to_responses(monkeypatch):
    import urllib.request

    urls = []

    def _open(req, timeout=None):
        urls.append(req.full_url)
        if req.full_url.endswith("/v1/chat/completions"):
            raise urllib.error.HTTPError(req.full_url, 404, "nope", {}, None)
        return FakeResp(fake_chat("```python\nresult = 1\n```"))

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    cfgs = {"W": {"endpoint": "https://w.test/v1/chat/completions",
                  "model": "muse-wonder-1.0"}}
    post = runner_fc.default_post_fns(cfgs, {"W": "k"}, "a")
    data = post("https://w.test/v1/chat/completions",
                {"model": "m", "messages": []}, 10)
    assert urls[-1].endswith("/v1/responses")  # refused -> responses path
    assert data["choices"][0]["finish_reason"] == "stop"


# ------------------------------------------------------- wrapper + CLI seams


def test_session_wrapper_uses_the_hook():
    src = open(os.path.join(HERE, "run_fc_session.sh"), encoding="utf-8").read()
    assert "RUN_SESSION_RUNNER_CMD" in src  # the existing hook, not an edit
    assert "runner_fc.py" in src
    assert "--workers 8" in src
    # No hard-coded session budget: the session cap argument (default
    # 3.50) sets it, and the hook appends it as --budget with --gpu-start.
    assert "--budget 3.50" not in src and "--budget 3.5" not in src
    assert "CAP=3.50" in src
    assert "run_session.sh" in src
    # Keys loaded without printing, refusing when empty. envsave takes
    # the OPAQUE id, not the name (Round 4.3): the Baseten id inline,
    # the HerdShot id read at run time from muse-wonder with grep.
    assert "envsave get es_LMDrY_C1YRDJYOAGLb2hB1y5WpczSEujtnquV4V5DTzZSMhp" \
        in src
    assert "envsave get BASETEN_API_KEY" not in src
    assert "envsave get META_HERDSHOT_API_KEY" not in src
    assert "muse-wonder" in src and "grep" in src
    assert "refusing to run" in src
    assert "echo $BASETEN" not in src and "echo $META" not in src
    hook = open(os.path.join(HERE, "..", "common", "run_session.sh"),
                encoding="utf-8").read()
    assert "RUN_SESSION_RUNNER_CMD" in hook
    assert "& RPID=$!" in hook and "wait $RPID" in hook
    # The hook branch runs like the default branch: keys in env, the
    # whole-session cap appended, so the session cap applies.
    hook_branch = [ln for ln in hook.splitlines()
                   if "RUN_SESSION_RUNNER_CMD" in ln and "RPID" in ln]
    assert len(hook_branch) == 1
    assert 'GLIMMER_URL="$URL" GLIMMER_KEY="$K"' in hook_branch[0]
    assert '--budget "$B"' in hook_branch[0]
    assert '--gpu-start "$GPU_START"' in hook_branch[0]


def test_runner_reads_herdshot_key_never_meta_key():
    src = open(os.path.join(HERE, "runner_fc.py"), encoding="utf-8").read()
    assert "META_HERDSHOT_API_KEY" in src
    assert 'os.environ.get("META_KEY"' not in src
    assert '"META_KEY"' not in src


def test_cli_refuses_without_modal(monkeypatch, tmp_path):
    import cloud_exec

    monkeypatch.setattr(cloud_exec, "modal", None)
    monkeypatch.setenv("GLIMMER_URL", "https://g.test")
    monkeypatch.setenv("GLIMMER_KEY", "k")
    monkeypatch.setenv("BASETEN_KEY", "k")
    monkeypatch.setenv("META_HERDSHOT_API_KEY", "k")
    rc = runner_fc.main(["--jobs", "dry", "--out", str(tmp_path / "o"),
                         "--arms", "G"])
    assert rc == 2  # clear message, no Modal run attempted


def test_cli_accepts_gpu_start(monkeypatch, tmp_path):
    import cloud_exec

    monkeypatch.setattr(cloud_exec, "modal", None)
    monkeypatch.setenv("GLIMMER_URL", "https://g.test")
    monkeypatch.setenv("GLIMMER_KEY", "k")
    rc = runner_fc.main(["--jobs", "dry", "--out", str(tmp_path / "o"),
                         "--arms", "G", "--gpu-start", "1700000000"])
    assert rc == 2  # still refuses without modal, but parses --gpu-start


def test_gpu_elapsed_uses_session_start():
    import time

    assert runner_fc.gpu_elapsed_s(time.monotonic(), None) >= 0.0
    # A session started an hour ago bills an hour of GPU.
    assert runner_fc.gpu_elapsed_s(
        time.monotonic(), time.time() - 3600) == pytest.approx(3600, abs=5)
    # Garbage falls back to the runner's own clock, never negative.
    assert runner_fc.gpu_elapsed_s(time.monotonic(), "soon") >= 0.0


def test_rule6_harness_over_five_percent_is_run_invalid():
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 15 else "FAIL",
                   "" if i < 15 else "api_error")
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 23 else "FAIL",
                    "" if i < 23 else "wrong_geometry")
                for i, j in enumerate(ids)]
    d = runner_fc.evaluate_fc_decision(records)
    assert d["decision"] == "FreeCAD target"  # clean run decides by rules
    assert d["run_invalid"] is False
    # Two harness failures in one arm's 30 answers (6.7%): the box
    # broke, no decision.
    bad = list(records)
    for i in (0, 1):
        bad[i] = {"job": "J%d" % (i + 1), "arm": "G", "outcome": "INVALID",
                  "failure_tag": "harness", "run_error": "harness: boom",
                  "usage": {}}
    d = runner_fc.evaluate_fc_decision(bad)
    assert d["decision"] == "RUN INVALID"
    assert d["run_invalid"] is True
    assert d["run_invalid_arms"]["G"] == pytest.approx(0.067)
    # One INVALID in 30 (3.3%) stays under the gate.
    ok = list(records)
    ok[0] = {"job": "J1", "arm": "G", "outcome": "INVALID",
             "failure_tag": "INVALID", "run_error": "cut off",
             "usage": {}}
    d = runner_fc.evaluate_fc_decision(ok)
    assert d["decision"] == "FreeCAD target"
    assert d["run_invalid"] is False


def test_decision_rates_exclude_invalid_and_t_over_s_scored():
    # One INVALID job per arm: rates are PASS / (PASS + FAIL), and T's
    # rate is T passes over S's scored (PASS + FAIL) jobs.
    ids = jobs()
    records = [rec(j, "G", "PASS" if i < 14 else "FAIL",
                   "" if i < 14 else "wrong_geometry")
               for i, j in enumerate(ids)]
    records += [rec(j, "S", "PASS" if i < 18 else "FAIL",
                    "" if i < 18 else "wrong_geometry")
                for i, j in enumerate(ids)]
    records = [r for r in records
               if not (r["job"] == "J30" and r["arm"] in ("G", "S"))]
    records.append({"job": "J30", "arm": "G", "outcome": "INVALID",
                    "failure_tag": "INVALID", "run_error": "cut off",
                    "usage": {}})
    records.append({"job": "J30", "arm": "S", "outcome": "INVALID",
                    "failure_tag": "harness", "run_error": "harness: boom",
                    "usage": {}})
    d = runner_fc.evaluate_fc_decision(records)
    assert d["rate_g"] == pytest.approx(14 / 29)
    assert d["rate_s"] == pytest.approx(18 / 29)
    assert d["rate_t"] == pytest.approx(18 / 29)  # no W: T is S
    # A W rescue of an S-FAILED job joins T but never an S-INVALID job.
    rescued = list(records) + [rec("J29", "W", "PASS")]
    d2 = runner_fc.evaluate_fc_decision(rescued)
    assert d2["rate_t"] == pytest.approx(19 / 29)
    not_rescued = list(records) + [rec("J30", "W", "PASS")]
    d3 = runner_fc.evaluate_fc_decision(not_rescued)
    assert d3["rate_t"] == pytest.approx(18 / 29)


def test_summary_counts_harness_and_invalid_per_arm(tmp_path):
    arm_recs = [
        {"job": "D1", "level": "dry", "arm": "G", "outcome": "PASS",
         "failure_tag": "", "usage": {}},
        {"job": "D2", "level": "dry", "arm": "G", "outcome": "INVALID",
         "failure_tag": "harness", "run_error": "harness: boom",
         "usage": {}},
    ]
    summary = runner_fc.build_fc_summary(
        arm_recs, [], [], 1.0, 10.0, 3.0, 3.0, False, False, False,
        ("G",), k=1, workers=1)
    # Pass rate leaves INVALID out (PLAN: PASS / (PASS + FAIL)); the
    # harness answer is counted, not folded in.
    assert summary["arms"]["G"]["pass_rate"] == 1.0
    assert summary["arms"]["G"]["INVALID"] == 1
    assert summary["failure_tags"]["G"]["harness"] == 1
    assert summary["failure_tags"]["G"]["INVALID"] == 1
    assert summary["run_invalid"] is True  # 1/2 is over 5%
    assert summary["decision"] == "RUN INVALID"


def _write_calls_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _disagreement_run_dirs(tmp_path):
    """Two small fake runs: T is FreeCAD target, S alone is not."""
    ids = ["J%d" % i for i in range(1, 11)]
    gs = [rec(j, "G", "PASS" if i < 2 else "FAIL",
              "" if i < 2 else "api_error")
          for i, j in enumerate(ids)]
    gs += [rec(j, "S", "PASS" if i < 7 else "FAIL",
               "" if i < 7 else "wrong_geometry")
           for i, j in enumerate(ids)]
    w = [rec(j, "W", "PASS") for j in ("J8", "J9", "J10")]
    gs_dir, w_dir = tmp_path / "main-GS", tmp_path / "main-W"
    gs_dir.mkdir()
    w_dir.mkdir()
    _write_calls_jsonl(str(gs_dir / "calls.jsonl"), gs)
    _write_calls_jsonl(str(w_dir / "calls.jsonl"), w)
    return str(gs_dir), str(w_dir)


def test_summarize_unites_gs_and_w_and_reports_both_lines(tmp_path):
    gs_dir, w_dir = _disagreement_run_dirs(tmp_path)
    out = str(tmp_path / "decision")
    records, summary = runner_fc.summarize_runs(gs_dir, w_dir, out)
    assert len(records) == 23  # 20 GS + 3 W rescues
    assert summary["decision_t"] == "FreeCAD target"
    assert summary["decision_s"] == "stay on CadQuery (grey zone)"
    assert summary["decision"] == "FreeCAD target only with " \
        "Wonder escalation (closed API)"
    assert summary["wonder_share"] == pytest.approx(0.3)
    assert summary["rate_g"] == pytest.approx(0.2)
    assert summary["rate_s"] == pytest.approx(0.7)
    assert summary["rate_t"] == pytest.approx(1.0)
    assert summary["run_invalid"] is False
    assert os.path.isfile(os.path.join(out, "summary.json"))
    report = open(os.path.join(out, "report.md"), encoding="utf-8").read()
    assert "FreeCAD target only with Wonder escalation" in report
    assert "PLAN rule 5: disagreement → stay on CadQuery" in report
    assert "Wonder's share" in report


def test_summarize_rule6_case_is_run_invalid(tmp_path):
    gs_dir, w_dir = tmp_path / "main-GS", tmp_path / "main-W"
    gs_dir.mkdir()
    w_dir.mkdir()
    _write_calls_jsonl(str(gs_dir / "calls.jsonl"), [
        {"job": "J1", "arm": "G", "outcome": "PASS", "failure_tag": "",
         "usage": {}},
        {"job": "J2", "arm": "G", "outcome": "INVALID",
         "failure_tag": "harness", "run_error": "harness: boom",
         "usage": {}},
        {"job": "J1", "arm": "S", "outcome": "PASS", "failure_tag": "",
         "usage": {}},
        {"job": "J2", "arm": "S", "outcome": "PASS", "failure_tag": "",
         "usage": {}},
    ])
    _write_calls_jsonl(str(w_dir / "calls.jsonl"), [])
    out = str(tmp_path / "decision")
    records, summary = runner_fc.summarize_runs(gs_dir, w_dir, out)
    assert len(records) == 4
    assert summary["decision"] == "RUN INVALID"
    assert summary["run_invalid"] is True
    assert summary["run_invalid_arms"]["G"] == pytest.approx(0.5)
    report = open(os.path.join(out, "report.md"), encoding="utf-8").read()
    assert "RUN INVALID" in report
    assert "PLAN rule 5: disagreement → stay on CadQuery" in report


def test_summarize_cli_needs_no_keys_or_suite(monkeypatch, tmp_path):
    gs_dir, w_dir = _disagreement_run_dirs(tmp_path)
    out = str(tmp_path / "decision")

    def _boom(*args, **kwargs):
        raise AssertionError("summarize must not run the suite")

    monkeypatch.setattr(runner_fc, "run_suite_fc", _boom)
    for var in ("GLIMMER_URL", "GLIMMER_KEY", "BASETEN_KEY",
                "META_HERDSHOT_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    rc = runner_fc.main(["--summarize", gs_dir, w_dir, "--out", out])
    assert rc == 0
    assert os.path.isfile(os.path.join(out, "summary.json"))
    assert os.path.isfile(os.path.join(out, "report.md"))


def test_cli_needs_jobs_or_summarize(tmp_path):
    with pytest.raises(SystemExit):
        runner_fc.main(["--out", str(tmp_path / "o")])


def test_main_runs_suite_inside_grader_app_context(monkeypatch, tmp_path):
    import cloud_exec
    import cloud_grade

    events = []

    class _Ctx:
        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, *args):
            events.append("exit")
            return False

    class _Modal:
        @staticmethod
        def enable_output():
            events.append("enable_output")
            return _Ctx()

    class _App:
        def run(self):
            events.append("app.run")
            return _Ctx()

    monkeypatch.setattr(cloud_exec, "modal", _Modal())
    # The suite runs inside the App that defines grade (lookup().run()
    # fails: App is already running).
    monkeypatch.setattr(cloud_grade, "_app", _App())
    monkeypatch.setenv("GLIMMER_URL", "https://g.test")
    monkeypatch.setenv("GLIMMER_KEY", "k")

    def _fake_suite(*args, **kwargs):
        events.append(("suite", kwargs.get("gpu_start")))
        return [], {}

    monkeypatch.setattr(runner_fc, "run_suite_fc", _fake_suite)
    monkeypatch.setattr(runner_fc, "load_inputs_fc",
                        lambda: ([{"id": "D1", "level": "dry",
                                   "text": "t"}], "MANUAL"))
    rc = runner_fc.main(["--jobs", "dry", "--out", str(tmp_path / "o"),
                         "--arms", "G", "--gpu-start", "1700000000"])
    assert rc == 0
    assert events[0] == "enable_output"  # grader calls get an app context
    assert "app.run" in events
    assert ("suite", "1700000000") in events  # --gpu-start threaded through
