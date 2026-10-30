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
        ["F1-1", "F1-2"], out, _spark, _wonder, "MANUAL", budget=1.0,
        budget_w=1.0, escalate=True, exec_fn=_exec, grade_fn=_grade)
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
