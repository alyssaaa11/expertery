"""Offline tests for the factory teacher (fake HTTP, fake box, no network).

Any test that could reach the network fails instead: post functions are
always injected fakes. Never opens blind/ folders or expected*.json.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import teacher

JOBS = [
    {"id": "F1-1", "family": 1, "text": "spool one",
     "reference": "result = 1"},
    {"id": "F1-2", "family": 1, "text": "spool two",
     "reference": "result = 1"},
    {"id": "F1-3", "family": 1, "text": "spool three",
     "reference": "result = 1"},
    {"id": "F2-1", "family": 2, "text": "manifold one",
     "reference": "result = 1"},
    {"id": "F2-2", "family": 2, "text": "manifold two",
     "reference": "result = 1"},
]
JOBS_BY_ID = {j["id"]: j for j in JOBS}

REAL_SHAPE = {  # the real Baseten usage shape (numbers illustrative)
    "prompt_tokens": 8307, "completion_tokens": 3438,
    "prompt_tokens_details": {"cached_tokens": 7552},
}


def _reply(code="result = 1", usage=None, finish="stop"):
    return {"choices": [{"message": {"content": "```python\n%s\n```"
                        % code}, "finish_reason": finish}],
            "usage": usage or dict(REAL_SHAPE)}


def _post_for(codes):
    """Fake post_fn: one reply per call, in order (fails when exhausted,
    so unexpected network use is loud)."""
    calls = []

    def _post(body):
        assert body["model"] == teacher.SPARK_MODEL
        assert body["max_tokens"] == 16000
        assert body["temperature"] == 1.0 and body["top_p"] == 0.95
        assert body["messages"][0]["content"] == teacher.SYSTEM_PROMPT
        calls.append(body)
        return _reply(codes[len(calls) - 1])

    _post.calls = calls
    return _post


def _exec_ok(code):
    return {"brep_bytes": b"BREP", "measure": None, "log": "",
            "run_error": None}


def _grade_pass(job_id, brep):
    return {"verdict": "PASS", "tight": "PASS", "fails": [],
            "measurements": {}}


def _grade_fail(job_id, brep):
    return {"verdict": "FAIL", "tight": "FAIL", "fails": ["mismatch 5%"],
            "fails_tight": ["mismatch 5%"], "measurements": {}}


# ------------------------------------------------------- money + tokens


def test_cached_tokens_nested_first():
    assert teacher.cached_tokens_of(dict(REAL_SHAPE)) == 7552
    assert teacher.cached_tokens_of({"cached_tokens": 7}) == 7
    assert teacher.cached_tokens_of({}) == 0
    assert teacher.cached_tokens_of(None) == 0
    assert teacher.cached_tokens_of(
        {"prompt_tokens_details": {"cached_tokens": 5},
         "cached_tokens": 9}) == 5  # nested wins


def test_cost_counts_cached_input_at_cached_price():
    cost = teacher.cost_of_usage(dict(REAL_SHAPE))
    assert cost == pytest.approx(
        (755 * 1.25 + 7552 * 0.15 + 3438 * 4.25) / 1e6)


def test_in_flight_guard_math():
    assert teacher.over_budget(0.5, 1.0) is True  # 0.5 + 8x0.075 > 1.0
    assert teacher.over_budget(0.3, 1.0) is False
    assert teacher.IN_FLIGHT_N * teacher.IN_FLIGHT_COST == pytest.approx(
        0.60)


# ------------------------------------------------------- selection


def test_pilot_is_two_non_dev_first_per_family():
    dev = ["F1-2", "F2-1"]
    ids = teacher.select_ids(JOBS, "pilot", dev)
    assert ids == ["F1-1", "F1-3", "F2-2"]
    assert not (set(ids) & set(dev))


def test_train_skips_prior_answers(tmp_path):
    prior = tmp_path / "old"
    prior.mkdir()
    (prior / "calls.jsonl").write_text(
        json.dumps({"id": "F1-1"}) + "\n", encoding="utf-8")
    ids = teacher.select_ids(JOBS, "train", [], [str(prior)])
    assert "F1-1" not in ids and "F1-2" in ids
    ids_all = teacher.select_ids(JOBS, "all", [], [str(prior)])
    assert "F1-1" in ids_all


# ------------------------------------------------------- calls


def test_pass_ends_up_in_train_records_fail_does_not(tmp_path):
    post = _post_for(["result = 1", "result = oops"])
    grades = {"F1-1": _grade_pass, "F1-2": _grade_fail}

    def _grade(job_id, brep):
        return grades[job_id](job_id, brep)

    out = str(tmp_path / "run")
    records, summary = teacher.run_suite(
        JOBS_BY_ID, ["F1-1", "F1-2"], out, post, None, "MANUAL",
        budget=1.0, exec_fn=_exec_ok, grade_fn=_grade)
    assert summary["n_kept_ids"] == 1
    kept = [json.loads(line) for line in open(
        os.path.join(out, "train_records.jsonl"), encoding="utf-8")]
    assert kept == [{"id": "F1-1", "text": "spool one",
                     "code": "result = 1"}]
    by_id = {r["id"]: r for r in records}
    assert by_id["F1-1"]["verdict"] == "PASS"
    assert by_id["F1-2"]["verdict"] == "FAIL"
    assert all(r["factory_version"] == teacher.FACTORY_VERSION
               for r in records)
    assert all(r["cached_tokens"] == 7552 for r in records)
    calls = [json.loads(line) for line in open(
        os.path.join(out, "calls.jsonl"), encoding="utf-8")]
    assert len(calls) == 2


def test_train_records_hold_first_pass_only(tmp_path):
    post = _post_for(["result = 1", "result = 1"])
    out = str(tmp_path / "run")
    records, _summary = teacher.run_suite(
        JOBS_BY_ID, ["F1-1"], out, post, None, "MANUAL", budget=1.0,
        retry_failed=True, k=2, exec_fn=_exec_ok, grade_fn=_grade_pass)
    assert len(records) == 1  # already PASS: no retry
    kept = [json.loads(line) for line in open(
        os.path.join(out, "train_records.jsonl"), encoding="utf-8")]
    assert [r["id"] for r in kept] == ["F1-1"]


def test_retry_failed_reasks_only_failed(tmp_path):
    post = _post_for(["bad", "also bad", "fixed"])
    seq = {"F1-1": [_grade_fail, _grade_pass], "F1-2": [_grade_pass]}

    def _grade(job_id, brep):
        return seq[job_id].pop(0)(job_id, brep)

    out = str(tmp_path / "run")
    records, _summary = teacher.run_suite(
        {"F1-1": JOBS_BY_ID["F1-1"], "F1-2": JOBS_BY_ID["F1-2"]},
        ["F1-1", "F1-2"], out, post, None, "MANUAL", budget=1.0,
        retry_failed=True, k=2, exec_fn=_exec_ok, grade_fn=_grade)
    attempts = sorted((r["id"], r["attempt"]) for r in records)
    assert attempts == [("F1-1", 1), ("F1-1", 2), ("F1-2", 1)]
    kept = [json.loads(line)["id"] for line in open(
        os.path.join(out, "train_records.jsonl"), encoding="utf-8")]
    assert sorted(kept) == ["F1-1", "F1-2"]


def test_escalate_keeps_wonder_pass_only(tmp_path):
    def _spark(body):
        assert body["model"] == teacher.SPARK_MODEL
        return _reply("bad-code")

    def _wonder(body):
        assert body["model"] == teacher.WONDER_MODEL
        return _reply("good-code")

    def _exec(code):
        return {"brep_bytes": code.encode(), "measure": None, "log": "",
                "run_error": None}

    def _grade(job_id, brep):
        if brep == b"good-code":
            return {"verdict": "PASS", "tight": "PASS", "fails": []}
        return {"verdict": "FAIL", "tight": "FAIL",
                "fails": ["mismatch 5%"],
                "fails_tight": ["mismatch 5%"]}

    out = str(tmp_path / "run")
    records, summary = teacher.run_suite(
        {"F1-1": JOBS_BY_ID["F1-1"], "F1-2": JOBS_BY_ID["F1-2"]},
        ["F1-1", "F1-2"], out, _spark, _wonder, "MANUAL", budget=10.0,
        budget_w=10.0, escalate=True, exec_fn=_exec, grade_fn=_grade)
    spark_recs = [r for r in records if r["teacher"] == "spark"]
    wonder_recs = [r for r in records if r["teacher"] == "wonder"]
    assert all(r["verdict"] == "FAIL" for r in spark_recs)
    assert all(r["verdict"] == "PASS" for r in wonder_recs)
    assert summary["wonder_share"] == 1.0


def test_budget_guard_stops_new_calls(tmp_path):
    post = _post_for(["result = 1"] * 10)
    out = str(tmp_path / "run")
    _records, summary = teacher.run_suite(
        JOBS_BY_ID, ["F1-1", "F1-2", "F1-3", "F2-1", "F2-2"], out, post,
        None, "MANUAL", budget=0.01, exec_fn=_exec_ok,
        grade_fn=_grade_pass)
    assert summary["budget_stopped"] is True
    assert summary["n_calls"] == 0


def test_failed_call_is_invalid_not_fail():
    def _boom(body):
        raise ConnectionError("down")

    rec = teacher.do_teacher_call(
        JOBS_BY_ID["F1-1"], "spark", teacher.SPARK_MODEL, _boom,
        _exec_ok, _grade_pass, "MANUAL")
    assert rec["verdict"] == "INVALID" and rec["fails"] == []


def test_no_brep_is_fail_box_error_is_invalid():
    rec = teacher.do_teacher_call(
        JOBS_BY_ID["F1-1"], "spark", teacher.SPARK_MODEL,
        _post_for(["result = 1"]),
        lambda code: {"brep_bytes": None, "measure": None, "log": "",
                      "run_error": "the answer wrote no BREP: x"},
        _grade_pass, "MANUAL")
    assert rec["verdict"] == "FAIL"

    def _boom(code):
        raise RuntimeError("box down")

    rec = teacher.do_teacher_call(
        JOBS_BY_ID["F1-1"], "spark", teacher.SPARK_MODEL,
        _post_for(["result = 1"]), _boom, _grade_pass, "MANUAL")
    assert rec["verdict"] == "INVALID"
    assert rec["run_error"].startswith("harness:")


# ------------------------------------------------- notes + version


def test_notes_go_after_the_manual_empty_notes_is_short_prompt():
    assert teacher.load_notes() == ""  # the repo file starts empty
    user = teacher.prompt_user_text("JOB", "MANUAL", "")
    assert user == ("Here is the CadQuery manual. Use it.\n\nMANUAL"
                    "\n\nJOB")
    user = teacher.prompt_user_text("JOB", "MANUAL", "watch the slot")
    assert user.index("MANUAL") < user.index("watch the slot")
    assert user.index("watch the slot") < user.index("JOB")
    msgs = teacher.build_messages("JOB", "MANUAL", "watch the slot")
    assert msgs[0]["content"] == teacher.SYSTEM_PROMPT
    assert "watch the slot" in msgs[1]["content"]


def test_train_records_keep_the_short_prompt_no_notes(tmp_path):
    post = _post_for(["result = 1"])
    out = str(tmp_path / "run")
    records, _summary = teacher.run_suite(
        JOBS_BY_ID, ["F1-1"], out, post, None, "MANUAL", budget=1.0,
        exec_fn=_exec_ok, grade_fn=_grade_pass, notes_text="some note")
    kept = [json.loads(line) for line in open(
        os.path.join(out, "train_records.jsonl"), encoding="utf-8")]
    assert kept == [{"id": "F1-1", "text": "spool one",
                     "code": "result = 1"}]
    assert post.calls[0]["messages"][1]["content"].count("some note") == 1


# ------------------------------------------------- F1: the app context


class _Ctx:
    def __init__(self, state):
        self._state = state

    def __enter__(self):
        self._state["entered"] = True

    def __exit__(self, *args):
        self._state["entered"] = False
        return False


def _fake_cq():
    import types

    state = {"entered": False, "outputs": 0, "runs": 0}

    class _Modal:
        @staticmethod
        def enable_output():
            state["outputs"] += 1
            return _Ctx({})  # counting only; no flag

    class _App:
        def run(self):
            state["runs"] += 1
            return _Ctx(state)

    class _Grade:
        def remote(self, *args):
            if not state["entered"]:
                raise RuntimeError("Function has not been hydrated")
            return {"verdict": "PASS", "tight": "PASS", "fails": []}

    return types.SimpleNamespace(modal=_Modal(), _app=_App(),
                                 grade=_Grade()), state


def test_real_grade_path_needs_the_app_context(monkeypatch):
    fake, state = _fake_cq()
    monkeypatch.setattr(teacher, "_cloud_cq", lambda: fake)
    with pytest.raises(RuntimeError, match="has not been hydrated"):
        teacher.default_grade_fn("F1-1", b"BREP")
    with teacher.app_context():
        assert state["entered"] is True
        graded = teacher.default_grade_fn("F1-1", b"BREP")
        assert graded["tight"] == "PASS"
    assert state["entered"] is False


def test_main_runs_suite_inside_the_app_context(monkeypatch, tmp_path):
    fake, state = _fake_cq()
    monkeypatch.setattr(teacher, "_cloud_cq", lambda: fake)
    monkeypatch.setenv("BASETEN_KEY", "x")
    jobs_path = tmp_path / "jobs.jsonl"
    jobs_path.write_text(
        json.dumps({"id": "F1-1", "family": 1, "text": "t",
                    "reference": "r"}) + "\n", encoding="utf-8")
    seen = {}

    def _suite(*args, **kwargs):
        seen["entered"] = state["entered"]
        seen["notes"] = kwargs.get("notes_text")
        return [], {"n_ids": 0, "n_calls": 0, "n_kept_ids": 0,
                    "cost_dollars": 0.0, "wonder_share": 0.0}

    monkeypatch.setattr(teacher, "run_suite", _suite)
    out = tmp_path / "run"
    assert teacher.main(
        ["--jobs", str(jobs_path), "--split", str(tmp_path / "no-split.json"),
         "--ids", "all", "--out", str(out),
         "--budget-dollars", "1"]) == 0
    assert seen["entered"] is True  # run_suite ran inside _app.run()
    assert state["runs"] == 1 and state["outputs"] == 1
    assert seen["notes"] == ""  # notes file is empty: short prompt


# ------------------------------------------------- F2: Wonder money


def test_wonder_charged_at_meta_rates_not_spark():
    cost = teacher.cost_of_usage(dict(REAL_SHAPE), wonder=True)
    assert cost == pytest.approx(
        (755 * 4.00 + 7552 * 0.20 + 3438 * 20.00) / 1e6)
    assert cost != pytest.approx(teacher.cost_of_usage(dict(REAL_SHAPE)))


def test_wonder_in_flight_reserve_is_at_least_35c_per_call():
    assert teacher.WONDER_IN_FLIGHT_COST >= 0.35
    assert teacher.over_budget(0.0, 2.0,
                               n=teacher.WONDER_IN_FLIGHT_N,
                               cost=teacher.WONDER_IN_FLIGHT_COST) is True
    # 8 x $0.35 = $2.80 of reserve: a $3 budget with $0.50 spent stops.
    assert teacher.over_budget(0.50, 3.0,
                               n=teacher.WONDER_IN_FLIGHT_N,
                               cost=teacher.WONDER_IN_FLIGHT_COST) is True
    assert teacher.over_budget(0.10, 3.0,
                               n=teacher.WONDER_IN_FLIGHT_N,
                               cost=teacher.WONDER_IN_FLIGHT_COST) is False


def test_escalate_spend_uses_wonder_rates(tmp_path):
    def _spark(body):
        return _reply("bad-code")

    def _wonder(body):
        assert body["model"] == teacher.WONDER_MODEL
        return _reply("good-code")

    def _exec(code):
        return {"brep_bytes": code.encode(), "measure": None, "log": "",
                "run_error": None}

    def _grade(job_id, brep):
        if brep == b"good-code":
            return {"verdict": "PASS", "tight": "PASS", "fails": []}
        return {"verdict": "FAIL", "tight": "FAIL",
                "fails": ["mismatch 5%"],
                "fails_tight": ["mismatch 5%"]}

    out = str(tmp_path / "run")
    records, summary = teacher.run_suite(
        {"F1-1": JOBS_BY_ID["F1-1"]}, ["F1-1"], out, _spark, _wonder,
        "MANUAL", budget=10.0, budget_w=10.0, escalate=True,
        exec_fn=_exec, grade_fn=_grade)
    wonder_recs = [r for r in records if r["teacher"] == "wonder"]
    assert len(wonder_recs) == 1
    assert wonder_recs[0]["cost"] == pytest.approx(
        teacher.cost_of_usage(dict(REAL_SHAPE), wonder=True))
    assert summary["cost_w_dollars"] == pytest.approx(
        wonder_recs[0]["cost"], abs=1e-4)


# ------------------------------------------------------- CLI


def test_missing_key_exits_2_with_message_no_network(monkeypatch, tmp_path,
                                                     capsys):
    monkeypatch.delenv("BASETEN_KEY", raising=False)

    def _boom(body):
        raise AssertionError("no network in tests")

    monkeypatch.setattr(teacher, "real_post_fn",
                        lambda *a, **k: _boom)
    with pytest.raises(SystemExit) as exc:
        teacher.main(["--ids", "pilot", "--out", str(tmp_path),
                      "--budget-dollars", "1"])
    assert exc.value.code == 2
    assert "BASETEN_KEY" in capsys.readouterr().err


def test_escalate_without_meta_key_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BASETEN_KEY", "x")
    monkeypatch.delenv("META_HERDSHOT_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        teacher.main(["--ids", "pilot", "--out", str(tmp_path),
                      "--budget-dollars", "1", "--escalate"])
    assert exc.value.code == 2
    assert "META_HERDSHOT_API_KEY" in capsys.readouterr().err
