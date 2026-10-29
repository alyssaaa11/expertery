"""Offline tests for the cloud box + grader (no Modal, no FreeCAD, no network).

Fake sandboxes and a fake Part module stand in for the real ones. Any
test that could reach a real Modal call monkeypatches it to raise.
Never opens blind/ folders or expected*.json contents: grading tests
use small synthetic measurements only.
"""
import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cloud_exec
import cloud_grade
import run_one_fc


# ------------------------------------------------------- fake sandbox


class FakeFS:
    def __init__(self):
        self.files = {}
        self.writes = []

    def write_text(self, path, text):
        self.writes.append(path)
        self.files[path] = text

    def read_bytes(self, path):
        return self.files[path]

    def read_text(self, path):
        data = self.files[path]
        return data if isinstance(data, str) else data.decode("utf-8")


class FakeProc:
    def __init__(self):
        self.stdout = object()  # no .read(): log falls back to ""


class FakeSandbox:
    def __init__(self, step_bytes=b"STEP", measure=None):
        self.filesystem = FakeFS()
        self.filesystem.files["/work/answer.step"] = step_bytes
        self.filesystem.files["/work/measure.json"] = json.dumps(
            measure or {"bbox": [0, 0, 0, 1, 1, 1], "volume": 1.0,
                        "solids": 1, "valid": True})
        self.exec_calls = []
        self.terminated = False

    def exec(self, cmd, env=None, timeout=None):
        self.exec_calls.append({"cmd": cmd, "env": env, "timeout": timeout})
        return FakeProc()

    def terminate(self):
        self.terminated = True


def test_sandbox_config_is_locked_down():
    kw = cloud_exec.sandbox_kwargs()
    assert kw["block_network"] is True  # no internet in the box
    assert "secrets" not in kw and "volumes" not in kw  # nothing mounted
    assert kw["cpu"] == 1
    assert tuple(kw["memory"]) == (1024, 4096)
    assert kw["timeout"] == 90  # one sandbox per answer, 90 s box


def test_box_image_holds_no_references():
    files = cloud_exec.image_files()
    assert files == ["run_one_fc.py"]  # ONLY FreeCAD + the runner script
    for name in files:
        low = name.lower()
        assert "jobs" not in low and "expected" not in low
        assert "reference" not in low and "cadquery" not in low
    assert cloud_exec.FREECAD_VERSION == "1.1.4"
    assert "1.1.4" in cloud_exec.APPIMAGE_ASSET


def test_box_protocol_write_run_read_terminate():
    box = FakeSandbox(step_bytes=b"STEP-BYTES")
    out = cloud_exec.run_answer_in_box("result = 1", sandbox=box)
    assert out["step_bytes"] == b"STEP-BYTES"
    assert out["measure"]["solids"] == 1  # logs only; grader decides
    assert box.filesystem.files["/work/answer.py"] == "result = 1"
    call = box.exec_calls[0]
    assert call["cmd"] == ["freecadcmd", "/work/run_one_fc.py"]
    assert call["env"] == {"FC_SCRATCH": "/work"}  # baseline speed limit box
    assert call["timeout"] == 60


def test_box_refuses_oversize_step():
    box = FakeSandbox(step_bytes=b"x" * (cloud_exec.MAX_STEP_BYTES + 1))
    with pytest.raises(ValueError):
        cloud_exec.run_answer_in_box("result = 1", sandbox=box)


def test_box_terminates_factory_sandbox(monkeypatch):
    made = []
    box = FakeSandbox()

    def _factory():
        made.append(True)
        return box

    cloud_exec.run_answer_in_box("result = 1", sandbox_factory=_factory)
    assert made and box.terminated


def test_real_modal_sandbox_is_never_created(monkeypatch):
    import modal

    def _boom(*args, **kwargs):
        raise AssertionError("a real Modal sandbox would start here")

    monkeypatch.setattr(modal.Sandbox, "create", _boom)
    with pytest.raises(AssertionError):
        cloud_exec.run_answer_in_box("result = 1")  # no factory: must raise
    monkeypatch.setattr(cloud_exec, "modal", None)
    with pytest.raises(RuntimeError):
        cloud_exec.build_sandbox()
    with pytest.raises(RuntimeError):
        cloud_exec.build_image()


# ------------------------------------------------------- fake Part


@pytest.fixture(autouse=True)
def _no_hooks_left():
    """The refusal hook must never leak into other tests' imports."""
    yield
    for hook in [h for h in sys.meta_path
                 if isinstance(h, run_one_fc._RefuseImports)]:
        sys.meta_path.remove(hook)


@pytest.fixture
def fake_part(monkeypatch):
    """A minimal Part module: one solid box shape."""
    mod = types.ModuleType("Part")

    class _BB:
        XMin, YMin, ZMin, XMax, YMax, ZMax = 0.0, 0.0, 0.0, 10.0, 5.0, 2.0

    class Shape:
        BoundBox = _BB()
        Volume = 100.0

        def Solids(self):
            return [object()]

        def isValid(self):
            return True

        def exportStep(self, path):
            with open(path, "wb") as f:
                f.write(b"FAKE-STEP")

    mod.Shape = Shape
    monkeypatch.setitem(sys.modules, "Part", mod)
    yield mod


def test_answer_exec_and_result_errors(fake_part):
    shape, err = run_one_fc.run_answer_source(
        "import sys\nresult = sys.modules['Part'].Shape()")
    assert err is None and shape is not None
    assert run_one_fc.validate_result(shape) is None  # a Part solid: ok
    _, err = run_one_fc.run_answer_source("x = 1")
    assert err == run_one_fc.ERROR_NO_RESULT  # exact string
    _, err = run_one_fc.run_answer_source("result = 42")
    assert run_one_fc.validate_result(42) == run_one_fc.ERROR_NOT_SOLID


def test_answer_exception_is_reported():
    _, err = run_one_fc.run_answer_source("raise TypeError('typo here')")
    assert err.startswith("TypeError:")


def test_cadquery_and_ocp_refused():
    _, err = run_one_fc.run_answer_source("import cadquery\nresult = 1")
    assert "refused import" in err
    _, err = run_one_fc.run_answer_source("import OCP.BRep\nresult = 1")
    assert "refused import" in err
    _, err = run_one_fc.run_answer_source(
        "import os\nresult = 1")  # innocent imports pass the hook
    assert err is None or "no variable" not in err


def test_run_one_writes_step_and_measure(tmp_path, fake_part):
    (tmp_path / "answer.py").write_text(
        "import sys\nresult = sys.modules['Part'].Shape()",
        encoding="utf-8")
    ok, err = run_one_fc.run_one(str(tmp_path))
    assert ok and err is None
    assert (tmp_path / "answer.step").read_bytes() == b"FAKE-STEP"
    measure = json.loads((tmp_path / "measure.json").read_text())
    assert measure["bbox"] == [0.0, 0.0, 0.0, 10.0, 5.0, 2.0]
    assert measure["volume"] == 100.0
    assert measure["solids"] == 1 and measure["valid"] is True


def test_run_one_failure_writes_nothing(tmp_path, fake_part):
    (tmp_path / "answer.py").write_text("result = 42", encoding="utf-8")
    ok, err = run_one_fc.run_one(str(tmp_path))
    assert not ok and "not a Part solid" in err
    assert not (tmp_path / "answer.step").exists()


# ------------------------------------------------------- grader (synthetic)


def test_grader_verdict_and_tight():
    good = {"bbox": [0, 0, 0, 1, 1, 1], "volume": 1.0, "solids": 1,
            "valid": True}
    # Exact match: PASS at 0.2% and at 1e-6.
    g = cloud_grade.grade_result([], 0.0, good)
    assert g["verdict"] == "PASS" and g["tight"] == "PASS"
    assert g["fails"] == [] and g["measurements"] == good
    # Small but nonzero mismatch: the verdict holds, 1e-6 does not.
    g = cloud_grade.grade_result([], 0.001, good)
    assert g["verdict"] == "PASS" and g["tight"] == "FAIL"
    # Failed checks fail both; a broken shape fails both.
    g = cloud_grade.grade_result(["bbox"], 0.0, good)
    assert g["verdict"] == "FAIL" and g["tight"] == "FAIL"
    g = cloud_grade.grade_result([], None, good)
    assert g["verdict"] == "FAIL" and "mismatch error" in g["fails"]


def test_grader_compare_mirrors_baseline():
    m = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0, "area": 600.0,
         "com": [5, 5, 5], "solids": 1, "valid": True}
    e = dict(m)
    assert cloud_grade.compare_measurements(m, e) == []
    assert "bbox" in cloud_grade.compare_measurements(
        {**m, "bbox": [0, 0, 0, 10, 10, 12]}, e)  # moved face
    assert "volume" in cloud_grade.compare_measurements(
        {**m, "volume": 1100.0}, e)  # 10% off
    g = cloud_grade.grade_measurements(m, e, 0.0)
    assert g["verdict"] == "PASS" and g["tight"] == "PASS"
    g = cloud_grade.grade_measurements({**m, "volume": 1100.0}, e, 0.0)
    assert g["verdict"] == "FAIL"  # built but failed the checker


def test_grader_tolerances():
    assert cloud_grade.TOL_VERDICT == 0.002  # 0.2% is the verdict
    assert cloud_grade.TOL_TIGHT == 1e-6  # 1e-6 also recorded
