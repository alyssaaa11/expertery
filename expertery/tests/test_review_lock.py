"""Offline tests for `expertery exam review` and `exam lock`."""

import hashlib
import json
import os
import sys

import pytest

from expertery import exam_agent
from test_exam_build import (FakeReader, box_ok, grade_script,
                             make_past_work, REF_SOURCE)

SUGGESTION = {"phrase": "60 by 40", "why": "axes unclear",
              "suggested_request": "Base plate 60 along X, 40 along Y."}


def flagged_exam(tmp_path):
    """An exam dir with one READY and one FLAGGED job."""
    past = make_past_work(str(tmp_path / "past"), {
        "J1": ("Base plate 60 by 40.", REF_SOURCE, False),
        "J2": ("Base plate 60 by 40.", REF_SOURCE, False)})
    reader = FakeReader([
        "```python\nresult = box(60, 40, 4)\n```",  # J1 reader 1: PASS
        "```python\nresult = box(60, 40, 4)\n```",  # J1 reader 2: PASS
        "```python\nresult = wrong()\n```",          # J2 reader 1: FAIL
        "```python\nresult = wrong()\n```",          # J2 reader 2: FAIL
        json.dumps(SUGGESTION),                      # J2 explainer
    ])
    out = str(tmp_path / "exam")
    exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                          box_fn=box_ok,
                          grade_fn=grade_script({"J1": "PASS",
                                                 "J2": "FAIL"}),
                          post_fn=reader)
    cands = {c["id"]: c for c in exam_agent.load_candidates(out)}
    assert cands["J1"]["status"] == "READY"
    assert cands["J2"]["status"] == "FLAGGED"
    return out


def decision_of(out, job):
    cands = {c["id"]: c for c in exam_agent.load_candidates(out)}
    return cands[job]


def test_accept_keep_drop_edit_recorded(tmp_path):
    out = flagged_exam(tmp_path)
    exam_agent.review_exam(out, choices={"J2": ("edited", "Base 60 X.")})
    cand = decision_of(out, "J2")
    assert cand["decision"]["choice"] == "edited"
    assert cand["decision"]["reviewer"] == "human"
    assert cand["decision"]["at"]
    assert cand["text"] == "Base 60 X."

    out2 = flagged_exam(tmp_path / "t2")
    exam_agent.review_exam(out2, choices={"J2": ("accepted", None)})
    assert decision_of(out2, "J2")["text"] == SUGGESTION[
        "suggested_request"]

    out3 = flagged_exam(tmp_path / "t3")
    exam_agent.review_exam(out3, choices={"J2": ("kept", None)})
    cand3 = decision_of(out3, "J2")
    assert cand3["decision"]["choice"] == "kept"
    assert cand3["text"] == "Base plate 60 by 40."

    out4 = flagged_exam(tmp_path / "t4")
    exam_agent.review_exam(out4, choices={"J2": ("dropped", None)})
    assert decision_of(out4, "J2")["decision"]["choice"] == "dropped"


def test_accept_all_records_flag_reviewer(tmp_path):
    out = flagged_exam(tmp_path)
    exam_agent.review_exam(out, accept_all=True)
    cand = decision_of(out, "J2")
    assert cand["decision"] == {"choice": "accepted", "reviewer": "flag",
                                "at": cand["decision"]["at"]}
    assert cand["decision"]["at"]


def test_review_rewrites_report_with_recheck_line(tmp_path):
    out = flagged_exam(tmp_path)
    exam_agent.review_exam(out, accept_all=True)
    report = open(os.path.join(out, "report.md")).read()
    assert exam_agent.RECHECK_LINE in report


def test_lock_refuses_undecided_flagged(tmp_path):
    out = flagged_exam(tmp_path)
    with pytest.raises(exam_agent.ExamError):
        exam_agent.lock_exam(out)


def test_lock_writes_rows_freeze_and_accepts_loader(tmp_path):
    out = flagged_exam(tmp_path)
    exam_agent.review_exam(out, accept_all=True)
    rows = exam_agent.lock_exam(out)
    assert [r["id"] for r in rows] == ["J1", "J2"]
    assert all(r["family"] == "past-work"
               and r["level"] == "unknown" for r in rows)
    assert rows[1]["text"] == SUGGESTION["suggested_request"]

    sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                    "..", "..", "experiments", "final"))
    import runner_final
    loaded = runner_final.load_factory_jobs_file(
        os.path.join(out, "exam.jsonl"))
    assert [j["id"] for j in loaded] == ["J1", "J2"]

    digest = hashlib.sha256(
        open(os.path.join(out, "exam.jsonl"), "rb").read()).hexdigest()
    freeze = open(os.path.join(out, "FREEZE.txt")).read()
    assert digest in freeze

    with pytest.raises(exam_agent.ExamError):
        exam_agent.lock_exam(out)  # refuses overwrite


def test_lock_drops_dropped_and_refuses_deferred(tmp_path):
    out = flagged_exam(tmp_path)
    exam_agent.review_exam(out, choices={"J2": ("dropped", None)})
    rows = exam_agent.lock_exam(out)
    assert [r["id"] for r in rows] == ["J1"]

    exam_agent.save_candidates(
        out, [{"id": "J9", "text": "t", "reference": "r",
               "status": "DEFERRED", "readers": [],
               "reference_measurements": None, "suggestion": None,
               "explainer_raw": None, "decision": None}])
    if os.path.exists(os.path.join(out, "exam.jsonl")):
        os.unlink(os.path.join(out, "exam.jsonl"))
    with pytest.raises(exam_agent.ExamError):
        exam_agent.lock_exam(out)
