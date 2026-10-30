"""Offline tests for the cloud CadQuery box + grader (no Modal, no network).

Fake sandboxes stand in for the real ones. Any test that could reach a
real Modal call monkeypatches it to raise. Never opens blind/ folders
or expected*.json contents: grading tests use small synthetic
measurements and locally built toy shapes only.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cloud_cq
import run_cq_box


# ------------------------------------------------------- fake sandbox


class FakeFS:
    """Same parameter names as Modal 1.6.3 (data, remote_path), so the
    keyword calls in run_answer_in_box bind here exactly as there."""

    def __init__(self):
        self.files = {}
        self.writes = []

    def write_text(self, data, remote_path):
        self.writes.append(remote_path)
        self.files[remote_path] = data

    def read_bytes(self, remote_path):
        return self.files[remote_path]

    def read_text(self, remote_path):
        data = self.files[remote_path]
        return data if isinstance(data, str) else data.decode("utf-8")


class FakeStream:
    def __init__(self, text=""):
        self._text = text

    def read(self):
        return self._text


class FakeProc:
    def __init__(self, stdout="", stderr=""):
        self.stdout = FakeStream(stdout)
        self.stderr = FakeStream(stderr)


class FakeSandbox:
    def __init__(self, files=None, stdout="", stderr=""):
        self.filesystem = FakeFS()
        if files:
            self.filesystem.files.update(files)
        self._proc = FakeProc(stdout, stderr)
        self.terminated = False
        self.exec_calls = []

    def exec(self, *args, **kwargs):
        self.exec_calls.append((args, kwargs))
        return self._proc

    def terminate(self):
        self.terminated = True


def _no_modal(monkeypatch):
    monkeypatch.setattr(cloud_cq, "modal", None)
    monkeypatch.setattr(cloud_cq, "build_sandbox",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("no real sandbox in tests")))


# ------------------------------------------------------- box config


def test_box_pins_mac_cadquery_versions():
    assert cloud_cq.CQ_VERSION == "2.8.0"
    assert cloud_cq.OCP_VERSION == "7.9.3.1"
    assert cloud_cq.pip_spec() == ["cadquery==2.8.0",
                                  "cadquery-ocp==7.9.3.1"]


def test_box_sandbox_kwargs_have_no_secrets_volumes_or_network():
    kw = cloud_cq.sandbox_kwargs()
    assert kw["block_network"] is True
    assert kw["cpu"] == 1
    assert kw["memory"] == (1024, 4096)
    assert kw["timeout"] == 90
    assert "secrets" not in kw and "volumes" not in kw
    assert cloud_cq.EXEC_TIMEOUT_S == 60  # runner.RUN_TIMEOUT


def test_box_image_holds_no_references():
    files = cloud_cq.image_files()
    assert files == ["run_cq_box.py"]
    for name in files:
        low = name.lower()
        assert "jobs" not in low and "expected" not in low \
            and "reference" not in low
    src = open(os.path.join(HERE, "run_cq_box.py"), encoding="utf-8").read()
    assert "expected.json" not in src and "jobs.jsonl" not in src


def test_box_writes_brep_not_step():
    src = open(os.path.join(HERE, "run_cq_box.py"), encoding="utf-8").read()
    assert "BREP" in src
    assert ".step" not in src.lower()


# ------------------------------------------------------- box run path


def test_run_answer_in_box_returns_brep():
    brep = b"BREPBYTES"
    sb = FakeSandbox(
        files={cloud_cq.BREP_PATH: brep,
               cloud_cq.MEASURE_PATH: json.dumps({"volume": 1.0})})
    out = cloud_cq.run_answer_in_box("result = 1", sandbox=sb)
    assert out["brep_bytes"] == brep
    assert out["measure"] == {"volume": 1.0}
    assert out["run_error"] is None
    assert sb.filesystem.writes == ["/work/answer.py"]
    assert not sb.terminated  # injected sandbox: the caller owns it


def test_run_answer_in_box_no_brep_is_fail_not_raise():
    sb = FakeSandbox(stdout="", stderr="ERROR: no variable named 'result'")
    out = cloud_cq.run_answer_in_box("x = 1", sandbox=sb)
    assert out["brep_bytes"] is None and out["measure"] is None
    assert out["run_error"].startswith(cloud_cq.NO_BREP_PREFIX)
    assert "no variable named 'result'" in out["run_error"]


def test_run_answer_in_box_refuses_big_brep():
    sb = FakeSandbox(
        files={cloud_cq.BREP_PATH: b"x" * (cloud_cq.MAX_BREP_BYTES + 1),
               cloud_cq.MEASURE_PATH: "{}"})
    with pytest.raises(ValueError):
        cloud_cq.run_answer_in_box("result = 1", sandbox=sb)


def test_run_answer_in_box_terminates_owned_sandbox():
    brep = b"B"
    made = []

    def _factory():
        sb = FakeSandbox(
            files={cloud_cq.BREP_PATH: brep,
                   cloud_cq.MEASURE_PATH: "{}"})
        made.append(sb)
        return sb

    out = cloud_cq.run_answer_in_box("result = 1", sandbox_factory=_factory)
    assert out["brep_bytes"] == brep
    assert made[0].terminated


def test_run_answer_without_sandbox_needs_modal(monkeypatch):
    _no_modal(monkeypatch)
    with pytest.raises(Exception):
        cloud_cq.run_answer_in_box("result = 1")


# ------------------------------------------------------- run script + BREP


def test_run_script_result_rule_and_brep_round_trip(tmp_path):
    cq = pytest.importorskip("cadquery")
    from cadquery import exporters as _exporters
    from cadquery import importers as _importers

    # Workplane gives its solid (the runner.run_code rule).
    wp = cq.Workplane("XY").box(10, 20, 30)
    shape = run_cq_box._to_shape(wp, cq)
    assert isinstance(shape, cq.Shape) and not isinstance(
        shape, cq.Workplane)
    m = run_cq_box.measure(shape)
    assert m["solids"] == 1 and m["valid"] is True
    path = str(tmp_path / "p.brep")
    _exporters.export(shape, path, exportType="BREP")
    with open(path, "rb") as f:
        raw = f.read()
    back = cloud_cq.import_brep_shape(raw)
    m2 = cloud_cq.measure_shape(back)
    assert abs(m2["volume"] - m["volume"]) <= 1e-9 * abs(m["volume"])
    for a, b in zip(m2["bbox"], m["bbox"]):
        assert abs(a - b) <= 1e-9 * max(1.0, abs(b))


def test_run_script_end_to_end(tmp_path):
    pytest.importorskip("cadquery")
    scratch = tmp_path / "w"
    scratch.mkdir()
    (scratch / "answer.py").write_text(
        "import cadquery as cq\nresult = cq.Workplane('XY').box(4, 5, 6)\n",
        encoding="utf-8")
    assert run_cq_box.main(["run_cq_box.py", str(scratch)]) == 0
    assert (scratch / "answer.brep").stat().st_size > 0
    saved = json.loads((scratch / "measure.json").read_text(
        encoding="utf-8"))
    assert saved["volume"] == pytest.approx(120.0)
    assert saved["solids"] == 1


def test_run_script_missing_result_exits_2(tmp_path, capsys):
    scratch = tmp_path / "w"
    scratch.mkdir()
    (scratch / "answer.py").write_text("x = 1\n", encoding="utf-8")
    assert run_cq_box.main(["run_cq_box.py", str(scratch)]) == 2
    assert "no variable named 'result'" in capsys.readouterr().err


# ------------------------------------------------------- grader pure part


def test_combine_verdict_boundary():
    # 0.1% mismatch: PASS at 0.2%, FAIL at 1e-6.
    out = cloud_cq.grade_result([], 0.001, {"volume": 1.0})
    assert out["verdict"] == "PASS" and out["tight"] == "FAIL"
    assert out["fails"] == [] and len(out["fails_tight"]) == 1
    out = cloud_cq.grade_result([], 0.0, {"volume": 1.0})
    assert out["verdict"] == "PASS" and out["tight"] == "PASS"
    out = cloud_cq.grade_result(["bbox"], 0.0, {})
    assert out["verdict"] == "FAIL" and out["tight"] == "FAIL"
    out = cloud_cq.grade_result([], None, {})
    assert out["verdict"] == "FAIL" and out["tight"] == "FAIL"


def test_score_shapes_both_tolerances():
    cq = pytest.importorskip("cadquery")
    ref = cq.Solid.makeBox(10, 20, 30)
    import sys as _sys

    _sys.path.insert(0, cloud_cq.FIRST_TEST_DIR)
    import checks

    exp = checks.measure(ref)
    same = cloud_cq.score_shapes(
        cq.Solid.makeBox(10, 20, 30), ref, exp)
    assert same["verdict"] == "PASS" and same["tight"] == "PASS"
    moved = cloud_cq.score_shapes(
        cq.Solid.makeBox(10, 20, 30).translate(cq.Vector(5, 0, 0)), ref, exp)
    assert moved["verdict"] == "FAIL" and moved["tight"] == "FAIL"


def _f5_one_and_two_bore():
    """F5 first-job shapes: the fixed one-bore cut vs the old two-bore
    cuts (the same solid; trusted generator code built locally)."""
    pytest.importorskip("cadquery")
    import sys as _sys

    _sys.path.insert(0, os.path.join(HERE, "..", "factory"))
    import generator as _gen

    p = _gen.first_params(5)
    new = _gen.FAMILIES[5]["src"](p)
    dm = _gen.num(round(p["rm"] * 2, 1))
    Lm = _gen.num(p["Lm"])
    single = ("s = s.cut(_xcyl((%s)/2, 0, 0, (-6 - 1), (%s + 1)))"
              % (dm, Lm))
    assert single in new
    two = ("s = s.cut(_xcyl((%s)/2, 0, 0, -1, (%s + 1)))\n"
           "s = s.cut(_xcyl((%s)/2, 0, 0, -7, 1))") % (dm, Lm, dm)
    return (_gen.build_source(new),
            _gen.build_source(new.replace(single, two)))


def test_factory_precise_mismatch_one_vs_two_bore():
    # H1 (user option A): the factory path computes mismatch volumes
    # with precise BRepGProp, so F5's one-bore and two-bore solids (the
    # same solid) agree below 1e-9 and score tight PASS.
    pytest.importorskip("cadquery")
    import sys as _sys

    _sys.path.insert(0, cloud_cq.FIRST_TEST_DIR)
    import checks

    one, two = _f5_one_and_two_bore()
    assert abs(cloud_cq.factory_mismatch(one, two)) < 1e-9
    exp = checks.measure(two)
    out = cloud_cq.score_shapes(one, two, exp, precise_mismatch=True)
    assert out["verdict"] == "PASS" and out["tight"] == "PASS"
    assert abs(out["mismatch"]) < 1e-6


def test_first_test_path_ignores_precise_scorer(monkeypatch):
    # H1 changes only the factory path: with the precise scorer broken,
    # the default (first-test) path still grades exactly as before.
    cq = pytest.importorskip("cadquery")
    import sys as _sys

    _sys.path.insert(0, cloud_cq.FIRST_TEST_DIR)
    import checks

    def _boom(*args, **kwargs):
        raise AssertionError("first-test path must not call this")

    monkeypatch.setattr(cloud_cq, "factory_score", _boom)
    monkeypatch.setattr(cloud_cq, "factory_mismatch", _boom)
    ref = cq.Solid.makeBox(10, 20, 30)
    exp = checks.measure(ref)
    same = cloud_cq.score_shapes(
        cq.Solid.makeBox(10, 20, 30), ref, exp)
    assert same["verdict"] == "PASS" and same["tight"] == "PASS"
    moved = cloud_cq.score_shapes(
        cq.Solid.makeBox(10, 20, 30).translate(cq.Vector(5, 0, 0)), ref, exp)
    assert moved["verdict"] == "FAIL" and moved["tight"] == "FAIL"


def test_remote_entry_points_refuse_offline(monkeypatch):
    # The remote entry points refuse without modal; the test fakes that.
    monkeypatch.setattr(cloud_cq, "modal", None)
    with pytest.raises(RuntimeError):
        cloud_cq.build_image()
    with pytest.raises(RuntimeError):
        cloud_cq.build_grader_image()
    with pytest.raises(RuntimeError):
        cloud_cq.build_sandbox()


# ------------------------------------------------------- check-refs


def _toy_jobs():
    return [
        {"id": "J%d" % i, "level": "main", "marker": i} for i in range(3)
    ]


def test_check_refs_counts_tight_pass(monkeypatch, capsys):
    monkeypatch.setattr(cloud_cq, "_first_test_jobs", _toy_jobs)
    calls = []

    def _build(exam, job):
        return b"brep-%s" % job["id"].encode()

    def _grade(exam, job_id, brep):
        calls.append((exam, job_id, brep))
        assert brep == b"brep-%s" % job_id.encode()
        return {"verdict": "PASS", "tight": "PASS", "fails": []}

    n_pass, n = cloud_cq.check_refs(
        exam="first-test", build_brep_fn=_build, grade_fn=_grade)
    assert (n_pass, n) == (3, 3)
    assert "REFS 3/3 PASS" in capsys.readouterr().out
    assert [c[1] for c in calls] == ["J0", "J1", "J2"]


def test_check_refs_reports_failures(monkeypatch, capsys):
    monkeypatch.setattr(cloud_cq, "_first_test_jobs", _toy_jobs)

    def _grade(exam, job_id, brep):
        if job_id == "J1":
            return {"verdict": "FAIL", "tight": "FAIL",
                    "fails_tight": ["mismatch 5.0%"]}
        return {"verdict": "PASS", "tight": "PASS"}

    n_pass, n = cloud_cq.check_refs(
        exam="first-test", build_brep_fn=lambda e, j: b"b",
        grade_fn=_grade)
    assert (n_pass, n) == (2, 3)
    out = capsys.readouterr().out
    assert "REF FAIL J1" in out and "REFS 2/3 PASS" in out


def test_check_refs_factory_reads_jobs_file(tmp_path, monkeypatch, capsys):
    jobs = [{"id": "F1-1", "family": 1, "text": "t",
             "reference": "result = 1"}]
    path = tmp_path / "jobs.jsonl"
    path.write_text("\n".join(json.dumps(j) for j in jobs) + "\n",
                    encoding="utf-8")
    monkeypatch.setattr(cloud_cq, "FACTORY_DIR", str(tmp_path))
    seen = []

    def _grade(exam, job_id, brep):
        seen.append((exam, job_id))
        return {"verdict": "PASS", "tight": "PASS"}

    n_pass, n = cloud_cq.check_refs(
        exam="factory", build_brep_fn=lambda e, j: b"b", grade_fn=_grade)
    assert (n_pass, n) == (1, 1)
    assert seen == [("factory", "F1-1")]
    assert "REFS 1/1 PASS" in capsys.readouterr().out


# ------------------------------------------------------- regrade


def _m(vol, x1=0.0):
    return {"bbox": [x1, 0.0, 0.0, 10.0, 10.0, 10.0], "volume": vol,
            "area": 600.0, "com": [5.0, 5.0, 5.0], "solids": 1,
            "valid": True}


def test_regrade_counts_with_fake_records(tmp_path, capsys):
    recs = [
        {"job": "M1", "outcome": "PASS", "code": "CODE-A",
         "measurements": _m(1000.0)},
        {"job": "M2", "outcome": "PASS", "code": "CODE-B",
         "measurements": _m(1000.0)},
        {"job": "M3", "outcome": "FAIL", "code": "CODE-C",
         "measurements": _m(1000.0)},
        {"job": "M4", "outcome": "PASS", "code": "CODE-D",
         "measurements": _m(1000.0)},
    ]
    path = tmp_path / "calls.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                    encoding="utf-8")

    def _exec(code):
        if code == "CODE-D":  # wrote no BREP: the answer's failure
            return {"brep_bytes": None, "measure": None, "log": "",
                    "run_error": "the answer wrote no BREP: boom"}
        return {"brep_bytes": code.encode(), "measure": None, "log": "",
                "run_error": None}

    def _grade(exam, job_id, brep):
        assert exam == "first-test"
        if brep == b"CODE-A":
            return {"verdict": "PASS", "tight": "PASS", "fails": [],
                    "measurements": _m(1000.0)}
        if brep == b"CODE-B":  # same verdict, changed measurements
            return {"verdict": "PASS", "tight": "FAIL",
                    "fails": [], "fails_tight": ["mismatch 0.0%"],
                    "measurements": _m(1001.0)}
        return {"verdict": "FAIL", "tight": "FAIL", "fails": ["bbox"],
                "measurements": _m(1000.0)}

    rows = cloud_cq.regrade_dir(str(tmp_path), exam="first-test",
                                exec_fn=_exec, grade_fn=_grade)
    out = capsys.readouterr().out
    assert "MEASURE same=2 changed=2" in out
    assert "REGRADE same=3 changed=1" in out
    assert [r["job"] for r in rows] == ["M1", "M2", "M3", "M4"]
    assert rows[0]["measure_same"] is True
    assert rows[0]["old_verdict"] == "PASS"
    assert rows[0]["new_verdict"] == "PASS"
    assert rows[0]["new_tight"] == "PASS"
    assert rows[1]["measure_same"] is False  # the equality column
    assert rows[2]["old_verdict"] == "FAIL"
    assert rows[2]["new_verdict"] == "FAIL"
    assert rows[3]["new_verdict"] == "FAIL"  # no BREP re-grades as FAIL
    saved = json.loads((tmp_path / "regrade.json").read_text(
        encoding="utf-8"))
    assert len(saved) == 4
    assert all("measure_same" in r and "new_tight" in r for r in saved)


def test_measure_same_precision_rules():
    assert cloud_cq.measure_same(None, None) is True
    assert cloud_cq.measure_same(_m(1.0), None) is False
    assert cloud_cq.measure_same(None, _m(1.0)) is False
    assert cloud_cq.measure_same(_m(1.0), _m(1.0)) is True
    assert cloud_cq.measure_same(_m(1.0), _m(1.001)) is False
