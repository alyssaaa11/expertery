"""Offline tests for `expertery exam build` (fakes only, no network)."""

import json
import os

import pytest

from expertery import cloud, exam_agent

REF_SOURCE = "result = box(60, 40, 4)  # the correct part"
READER_CODE = "```python\nresult = box(60, 40, 4)\n```"

USAGE = {"prompt_tokens": 100, "completion_tokens": 50}


def reply(content, usage=None):
    """One chat-completions response carrying content."""
    return {"choices": [{"message": {"content": content}}],
            "usage": dict(usage or USAGE)}


class FakeReader:
    """Queued reader replies; records every body (messages asserted)."""

    def __init__(self, contents):
        self.contents = list(contents)
        self.bodies = []

    def __call__(self, url, key, body, timeout=600.0):
        self.bodies.append(body)
        content = self.contents[min(len(self.bodies) - 1,
                                    len(self.contents) - 1)]
        return reply(content)


def box_ok(code):
    """Box fake: every non-empty code builds one valid solid."""
    if not code.strip():
        return {"brep_bytes": None, "measure": None, "log": "",
                "run_error": "the answer wrote no BREP: empty"}
    return {"brep_bytes": b"BREP:" + code.encode()[:8],
            "measure": {"bbox": [60.0, 40.0, 4.0], "volume": 9600.0,
                        "solids": 1, "valid": True},
            "log": "", "run_error": None}


def box_ref_only(ref_source):
    """Box fake: only the exact reference source builds."""
    def _box(code):
        if code == ref_source:
            return box_ok(code)
        return {"brep_bytes": None, "measure": None, "log": "",
                "run_error": "the answer wrote no BREP: crash"}
    return _box


def grade_script(results):
    """Grader fake: per-job verdicts from a dict or a single verdict."""
    def _grade(exam, job_id, brep):
        assert exam == "factory"
        assert brep is not None
        verdict = results if isinstance(results, str) else results[job_id]
        return {"verdict": verdict, "tight": verdict, "fails": [],
                "mismatch": 0.0,
                "measurements": {"bbox": [60.0, 40.0, 4.0],
                                 "volume": 9600.0, "solids": 1,
                                 "valid": True}}
    return _grade


def make_past_work(root, jobs):
    """Write a past-work dir: {jid: (request, source|None, step?)}."""
    for jid, (request, source, step) in jobs.items():
        job_dir = os.path.join(root, jid)
        os.makedirs(job_dir)
        with open(os.path.join(job_dir, "request.txt"), "w",
                  encoding="utf-8") as f:
            f.write(request)
        if source is not None:
            with open(os.path.join(job_dir, "part.py"), "w",
                      encoding="utf-8") as f:
                f.write(source)
        if step:
            with open(os.path.join(job_dir, "part.step"), "w",
                      encoding="utf-8") as f:
                f.write("step-bytes")
    return root


def test_ready_when_all_readers_pass(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate 60 by 40.", REF_SOURCE,
                                  False)})
    reader = FakeReader([READER_CODE, READER_CODE])
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                                   box_fn=box_ok,
                                   grade_fn=grade_script("PASS"),
                                   post_fn=reader)
    assert len(reader.bodies) == 2  # no explainer call
    (cand,) = result["candidates"]
    assert cand["status"] == "READY"
    assert cand["suggestion"] is None
    assert [r["verdict"] for r in cand["readers"]] == ["PASS", "PASS"]
    calls = exam_agent.read_jsonl(os.path.join(out, "calls.jsonl"))
    assert len(calls) == 2
    assert all("prompt_tokens" in c for c in calls)
    assert result["spent_estimate"] > 0
    report = open(os.path.join(out, "report.md")).read()
    assert "READY" in report and "spent_estimate" in report
    assert exam_agent.FLAGGED_LINE in report


def test_flagged_and_explainer_never_sees_reference(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate 60 by 40.", REF_SOURCE,
                                  False)})
    explainer_reply = json.dumps(
        {"phrase": "60 by 40", "why": "axes unclear",
         "suggested_request": "Base plate 60 along X, 40 along Y."})
    reader = FakeReader(["```python\nresult = wrong()\n```",
                         explainer_reply])
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=1, workers=1,
                                   box_fn=box_ref_only(REF_SOURCE),
                                   grade_fn=grade_script("FAIL"),
                                   post_fn=reader)
    (cand,) = result["candidates"]
    assert cand["status"] == "FLAGGED"
    assert cand["suggestion"] == {"phrase": "60 by 40",
                                  "why": "axes unclear",
                                  "suggested_request":
                                  "Base plate 60 along X, 40 along Y."}
    assert cand["explainer_raw"] is None
    for body in reader.bodies:
        assert REF_SOURCE not in json.dumps(body)


def test_invalid_explainer_json_is_flagged_with_null(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate 60 by 40.", REF_SOURCE,
                                  False)})
    reader = FakeReader(["```python\nresult = wrong()\n```",
                         "not json at all"])
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=1, workers=1,
                                   box_fn=box_ref_only(REF_SOURCE),
                                   grade_fn=grade_script("FAIL"),
                                   post_fn=reader)
    (cand,) = result["candidates"]
    assert cand["status"] == "FLAGGED"
    assert cand["suggestion"] is None
    assert cand["explainer_raw"] == "not json at all"


def test_broken_reference_makes_no_reader_calls(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", "result = broken(",
                                  False)})
    reader = FakeReader([READER_CODE])
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                                   box_fn=box_ref_only(REF_SOURCE),
                                   grade_fn=grade_script("PASS"),
                                   post_fn=reader)
    (cand,) = result["candidates"]
    assert cand["status"] == "BROKEN_REFERENCE"
    assert reader.bodies == []


def test_step_file_is_skipped(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", REF_SOURCE, True)})
    reader = FakeReader([READER_CODE])
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                                   box_fn=box_ok,
                                   grade_fn=grade_script("PASS"),
                                   post_fn=reader)
    (cand,) = result["candidates"]
    assert cand["status"] == "SKIPPED"
    assert reader.bodies == []


def test_cap_stops_new_calls(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", REF_SOURCE, False),
                           "J2": ("Upright.", REF_SOURCE, False)})
    reader = FakeReader([READER_CODE] * 10)
    out = str(tmp_path / "exam")
    # Below one in-flight reserve: no call may start.
    result = exam_agent.build_exam(past, out, 0.01, readers=2,
                                   workers=1, box_fn=box_ok,
                                   grade_fn=grade_script("PASS"),
                                   post_fn=reader)
    assert reader.bodies == []
    assert all(c["status"] == "DEFERRED"
               for c in result["candidates"])
    assert result["spent_estimate"] == 0.0


def test_dry_run_makes_zero_calls_and_writes_nothing(tmp_path):
    def _boom(code):
        raise AssertionError("dry-run must not touch the box")

    def _boom_post(url, key, body, timeout=600.0):
        raise AssertionError("dry-run must not call the reader")

    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", REF_SOURCE, False)})
    out = str(tmp_path / "exam")
    lines = []
    result = exam_agent.build_exam(past, out, 5.0, readers=2,
                                   dry_run=True, box_fn=_boom,
                                   grade_fn=None, post_fn=_boom_post,
                                   print_fn=lines.append)
    assert result == {"candidates": [], "spent_estimate": 0.0}
    assert not os.path.exists(out)
    assert any("dry-run" in line for line in lines)


def test_refuses_exam_dir_with_exam_jsonl(tmp_path):
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", REF_SOURCE, False)})
    out = str(tmp_path / "exam")
    os.makedirs(out)
    with open(os.path.join(out, "exam.jsonl"), "w",
              encoding="utf-8") as f:
        f.write("{}\n")
    with pytest.raises(exam_agent.ExamError):
        exam_agent.build_exam(past, out, 5.0, box_fn=box_ok,
                              grade_fn=grade_script("PASS"),
                              post_fn=FakeReader([READER_CODE]))


def test_reader_cost_uses_teacher_prices():
    cost = cloud.cost_of_usage({"prompt_tokens": 1_000_000,
                                "completion_tokens": 1_000_000})
    assert cost == pytest.approx(1.25 + 4.25)


class SessionRecorder:
    """Fake cloud_session: counts entries, records fake args."""

    def __init__(self):
        self.entries = []

    def __call__(self, *args, **kwargs):
        self.entries.append((args, kwargs))
        recorder = self

        class _Ctx:
            def __enter__(self):
                return None

            def __exit__(self, *exc):
                recorder.entries.append("exit")
                return False

        return _Ctx()


def test_build_with_fakes_never_enters_cloud_session(tmp_path,
                                                     monkeypatch):
    recorder = SessionRecorder()
    monkeypatch.setattr(cloud, "cloud_session", recorder)
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate 60 by 40.", REF_SOURCE,
                                  False)})
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                                   box_fn=box_ok,
                                   grade_fn=grade_script("PASS"),
                                   post_fn=FakeReader([READER_CODE]))
    assert len(result["candidates"]) == 1
    assert recorder.entries == []


def test_build_dry_run_never_enters_cloud_session(tmp_path, monkeypatch):
    recorder = SessionRecorder()
    monkeypatch.setattr(cloud, "cloud_session", recorder)
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate.", REF_SOURCE, False)})
    out = str(tmp_path / "exam")
    exam_agent.build_exam(past, out, 5.0, readers=2, dry_run=True,
                          box_fn=box_ok, grade_fn=grade_script("PASS"),
                          post_fn=FakeReader([READER_CODE]),
                          print_fn=lambda *a, **k: None)
    assert recorder.entries == []


def test_build_real_run_enters_cloud_session_once(tmp_path, monkeypatch):
    recorder = SessionRecorder()
    monkeypatch.setattr(cloud, "cloud_session", recorder)
    monkeypatch.setattr(cloud, "run_box", lambda code, box_fn=None:
                        box_ok(code))
    monkeypatch.setattr(cloud, "factory_grade_fn",
                        lambda jobs, grade_fn=None: grade_script("PASS"))
    past = make_past_work(str(tmp_path / "past"),
                          {"J1": ("Base plate 60 by 40.", REF_SOURCE,
                                  False)})
    out = str(tmp_path / "exam")
    result = exam_agent.build_exam(past, out, 5.0, readers=2, workers=1,
                                   post_fn=FakeReader([READER_CODE,
                                                       READER_CODE]))
    assert len(result["candidates"]) == 1
    # Exactly one session for the whole build (call + exit markers).
    calls = [e for e in recorder.entries if e != "exit"]
    assert calls == [((), {})]


def test_cloud_session_noop_with_fakes(monkeypatch):
    def _boom():
        raise AssertionError("no-op session must not load cloud_cq")

    monkeypatch.setattr(cloud, "load_cloud_cq", _boom)
    with cloud.cloud_session(box_fn=box_ok):
        pass
    with cloud.cloud_session(grade_fn=grade_script("PASS")):
        pass


def test_cloud_session_runs_ephemeral_grader_app(monkeypatch):
    import contextlib

    events = []

    @contextlib.contextmanager
    def _marked(name):
        events.append(name + "-enter")
        try:
            yield
        finally:
            events.append(name + "-exit")

    class _FakeModal:
        def enable_output(self):
            return _marked("output")

    class _FakeApp:
        def run(self):
            return _marked("app")

    class _FakeCloudCq:
        modal = _FakeModal()
        _app = _FakeApp()

    monkeypatch.setattr(cloud, "load_cloud_cq", lambda: _FakeCloudCq())
    with cloud.cloud_session():
        events.append("work")
    assert events == ["output-enter", "app-enter", "work",
                      "app-exit", "output-exit"]
