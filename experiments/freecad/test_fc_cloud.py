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


class NoStdoutProc:
    """A proc without readable streams: logs fall back to ""."""

    def __init__(self):
        self.stdout = object()
        # No stderr attribute at all.


class FakeSandbox:
    def __init__(self, step_bytes=b"STEP", measure=None, stdout="",
                 stderr="", proc=None):
        self.filesystem = FakeFS()
        if step_bytes is not None:
            self.filesystem.files["/work/answer.step"] = step_bytes
        self.filesystem.files["/work/measure.json"] = json.dumps(
            measure or {"bbox": [0, 0, 0, 1, 1, 1], "volume": 1.0,
                        "solids": 1, "valid": True})
        self._proc = proc or FakeProc(stdout, stderr)
        self.exec_calls = []
        self.terminated = False

    def exec(self, *args, env=None, timeout=None):
        self.exec_calls.append({"args": args, "env": env,
                                "timeout": timeout})
        return self._proc

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
    assert out["run_error"] is None
    assert box.filesystem.files["/work/answer.py"] == "result = 1"
    call = box.exec_calls[0]
    # Separate string arguments (Modal: app is required; exec takes args).
    # freecadcmd IMPORTS a file argument, so the box script starts as a
    # program through -c (Round 2 probe).
    assert call["args"] == ("freecadcmd", "-c", cloud_exec.BOOTSTRAP)
    assert "run_one_fc.py" in call["args"][2]
    assert "__main__" in call["args"][2]
    assert call["env"] == {"FC_SCRATCH": "/work"}  # baseline speed limit box
    assert call["timeout"] == 60


def test_box_without_step_returns_run_one_fc_stderr():
    err = "ERROR: no variable named 'result'"
    box = FakeSandbox(step_bytes=None, stderr=err + "\n")
    out = cloud_exec.run_answer_in_box("x = 1", sandbox=box)
    assert out["step_bytes"] is None and out["measure"] is None
    # run_one_fc's ERROR line is handed back (not raised: this is the
    # answer's failure, not a harness failure).
    assert cloud_exec.NO_STEP_PREFIX in out["run_error"]
    assert err in out["run_error"]


def test_box_without_step_and_empty_stderr():
    box = FakeSandbox(step_bytes=None)
    out = cloud_exec.run_answer_in_box("x = 1", sandbox=box)
    assert out["step_bytes"] is None
    assert cloud_exec.NO_STEP_PREFIX in out["run_error"]


def test_box_streams_best_effort():
    box = FakeSandbox(proc=NoStdoutProc())
    out = cloud_exec.run_answer_in_box("result = 1", sandbox=box)
    assert out["log"] == "" and out["step_bytes"] == b"STEP"


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
        raise AssertionError("a real Modal call would start here")

    monkeypatch.setattr(modal.Sandbox, "create", _boom)
    monkeypatch.setattr(modal.App, "lookup", _boom)
    with pytest.raises(AssertionError):
        cloud_exec.run_answer_in_box("result = 1")  # no factory: must raise
    monkeypatch.setattr(cloud_exec, "modal", None)
    with pytest.raises(RuntimeError):
        cloud_exec.build_sandbox()
    with pytest.raises(RuntimeError):
        cloud_exec.build_image()
    with pytest.raises(RuntimeError):
        cloud_exec.lookup_exec_app()


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
    """A minimal Part module: one solid box shape.

    Real FreeCAD exposes ``Shape.Solids`` as a LIST attribute, not a
    method, so the fake does too (the old method-shaped fake passed
    while the real box failed every answer).
    """
    mod = types.ModuleType("Part")

    class _BB:
        XMin, YMin, ZMin, XMax, YMax, ZMax = 0.0, 0.0, 0.0, 10.0, 5.0, 2.0

    class Shape:
        BoundBox = _BB()
        Volume = 100.0
        Solids = [object()]

        def isValid(self):
            return True

        def exportStep(self, path):
            with open(path, "wb") as f:
                f.write(b"FAKE-STEP")

    mod.Shape = Shape
    monkeypatch.setitem(sys.modules, "Part", mod)
    yield mod


def test_solids_list_attribute_passes(fake_part):
    """A fake whose Solids is a list (like real FreeCAD) validates."""
    assert not callable(fake_part.Shape.Solids)
    shape, err = run_one_fc.run_answer_source(
        "import sys\nresult = sys.modules['Part'].Shape()")
    assert err is None
    assert run_one_fc.validate_result(shape) is None
    assert run_one_fc.measure_shape(shape)["solids"] == 1
    # A method-shaped Solids is NOT a solid (len() of a method fails).
    shape2 = fake_part.Shape()
    shape2.Solids = shape2.isValid  # a bound method, not a list
    assert run_one_fc.validate_result(shape2) == run_one_fc.ERROR_NOT_SOLID


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


# ------------------------------------------------------- image recipe (B1)


class _FakeImage:
    def __init__(self):
        self.commands = []
        self.files = []

    def run_commands(self, *cmds):
        self.commands.extend(cmds)
        return self

    def add_local_file(self, local, remote):
        self.files.append((local, remote))
        return self


def _stub_modal_with_image():
    """A modal stand-in recording Image builds + Sandbox.create calls."""
    made = {}

    class _ImageNS:
        @staticmethod
        def from_registry(base):
            made["base"] = base
            made["image"] = _FakeImage()
            return made["image"]

    class _AppNS:
        @staticmethod
        def lookup(name, create_if_missing=False):
            made.setdefault("lookups", []).append((name, create_if_missing))
            return ("app:%s" % name, create_if_missing)

    class _SandboxNS:
        @staticmethod
        def create(*args, **kwargs):
            made.setdefault("creates", []).append((args, kwargs))
            return ("sandbox", kwargs)

    return types.SimpleNamespace(Image=_ImageNS, App=_AppNS,
                                 Sandbox=_SandboxNS), made


def test_image_recipe_downloads_verified_release(monkeypatch):
    stub, made = _stub_modal_with_image()
    monkeypatch.setattr(cloud_exec, "modal", stub)
    cloud_exec.build_image()
    blob = "\n".join(made["image"].commands)
    # The per-asset SHA file (the old SHA256.txt is 404).
    assert cloud_exec.APPIMAGE_SHA_URL.endswith(
        "FreeCAD_1.1.4-Linux-x86_64-py311.AppImage-SHA256.txt")
    assert cloud_exec.APPIMAGE_SHA_URL in blob
    assert cloud_exec.APPIMAGE_URL in blob
    # -fL: an HTTP error fails the build instead of checksumming a 404.
    assert "curl -fL" in blob and "curl -L " not in blob.replace(
        "curl -fL", "")
    # Exact apt line: no || true, no libfuse (extract needs no FUSE).
    assert "apt-get install -y --no-install-recommends ca-certificates " \
        "curl libgl1 libglib2.0-0 libx11-6 libxext6 libxrender1 libsm6 " \
        "libice6" in blob
    assert "|| true" not in blob and "fuse" not in blob.lower()
    assert "--appimage-extract" in blob
    # chmod +x before extracting (the build stopped there, exit 126),
    # and the AppImage deleted after extracting (smaller image).
    assert "chmod +x /opt/%s" % cloud_exec.APPIMAGE_ASSET in blob
    assert "rm /opt/%s" % cloud_exec.APPIMAGE_ASSET in blob
    cmds = made["image"].commands
    at = lambda s: next(i for i, c in enumerate(cmds) if s in c)
    assert at("chmod +x") < at("--appimage-extract") < at("rm /opt/")
    # freecadcmd on PATH + version printed.
    assert "ln -s /opt/squashfs-root/usr/bin/freecadcmd " \
        "/usr/local/bin/freecadcmd" in blob
    assert "freecadcmd --version" in blob
    assert made["image"].files == [
        (os.path.join(HERE, "run_one_fc.py"), "/work/run_one_fc.py")]


def test_sandbox_create_uses_the_app(monkeypatch):
    stub, made = _stub_modal_with_image()
    monkeypatch.setattr(cloud_exec, "modal", stub)
    monkeypatch.setattr(cloud_exec, "build_image", lambda: "img")
    sb = cloud_exec.build_sandbox()
    assert ("forge-freecad", True) in made["lookups"]
    args, kwargs = made["creates"][0]
    assert args == ()  # Modal: app is required; exec takes the args
    assert kwargs["app"] == ("app:forge-freecad", True)
    assert kwargs["image"] == "img"
    assert kwargs["block_network"] is True and sb == ("sandbox", kwargs)


def test_lookup_exec_app_name(monkeypatch):
    stub, made = _stub_modal_with_image()
    monkeypatch.setattr(cloud_exec, "modal", stub)
    cloud_exec.lookup_exec_app()
    assert made["lookups"] == [("forge-freecad", True)]


def test_filesystem_call_keywords_match_modal():
    """The parameter names the code uses exist on the real SDK (Modal
    1.6.3 is write_text(data, remote_path)); the fake shares them, so
    keyword calls bind the same way on both. Skipped without modal."""
    import inspect

    modal = pytest.importorskip("modal")
    from modal.sandbox import _filesystem as _fs

    sig = inspect.signature(_fs._SandboxFilesystem.write_text)
    assert "data" in sig.parameters and "remote_path" in sig.parameters
    for meth in ("read_bytes", "read_text"):
        assert "remote_path" in inspect.signature(
            getattr(_fs._SandboxFilesystem, meth)).parameters
    assert list(inspect.signature(FakeFS.write_text).parameters) == [
        "self", "data", "remote_path"]
    assert list(inspect.signature(FakeFS.read_bytes).parameters) == [
        "self", "remote_path"]
    assert list(inspect.signature(FakeFS.read_text).parameters) == [
        "self", "remote_path"]
    assert modal is not None


def test_box_modal_not_found_is_answer_failure_not_harness():
    """A missing STEP/measure raises SandboxFilesystemNotFoundError on
    the real box: still 'the answer wrote no STEP' (FAIL), not harness."""
    modal = pytest.importorskip("modal")
    import modal.exception as _exc

    box = FakeSandbox(step_bytes=None, stderr="ERROR: boom\n")
    orig_read = box.filesystem.read_bytes

    def _missing(remote_path):
        raise _exc.SandboxFilesystemNotFoundError("missing: " + remote_path)

    box.filesystem.read_bytes = _missing
    out = cloud_exec.run_answer_in_box("x = 1", sandbox=box)
    assert out["step_bytes"] is None and out["measure"] is None
    assert cloud_exec.NO_STEP_PREFIX in out["run_error"]
    assert "boom" in out["run_error"]
    assert modal is not None and orig_read is not None

    # STEP present but measure.json missing: same verdict.
    box2 = FakeSandbox(step_bytes=b"S")
    del box2.filesystem.files["/work/measure.json"]
    out2 = cloud_exec.run_answer_in_box("result = 1", sandbox=box2)
    assert out2["step_bytes"] is None
    assert cloud_exec.NO_STEP_PREFIX in out2["run_error"]


# ------------------------------------------------------- live check CLIs


def test_hand_job_id_is_the_file_name_prefix():
    assert cloud_exec.hand_job_id("M1") == "M1"
    assert cloud_exec.hand_job_id("M1_wrong") == "M1"  # prefix, not the file
    assert cloud_exec.hand_job_id("H13_wrong") == "H13"
    assert cloud_exec.hand_job_id("H6") == "H6"


def test_load_hand_expected_keys_are_stems():
    exp = cloud_exec.load_hand_expected()  # the Mac measurements
    assert set(exp) == {"M1", "M1_wrong", "M6", "M10", "H6", "H13",
                        "H13_wrong"}
    assert exp["M1"]["volume"] == pytest.approx(4322.190275490383)
    assert len(exp["M10"]["bbox"]) == 6


def test_check_hand_reports_pass_fail_and_rel_diff(tmp_path, capsys):
    a = tmp_path / "M1.py"
    a.write_text("result = 1", encoding="utf-8")
    b = tmp_path / "M1_wrong.py"
    b.write_text("result = 2", encoding="utf-8")
    c = tmp_path / "M6.py"
    c.write_text("x = 1", encoding="utf-8")

    def fake_exec(source):
        if source == "x = 1":
            return {"step_bytes": None, "measure": None, "log": "",
                    "run_error": "the answer wrote no STEP: ERROR: boom"}
        return {"step_bytes": ("STEP:" + source).encode(), "measure": {},
                "log": "", "run_error": None}

    seen = {}

    def fake_grade(job_id, step):
        seen[step] = job_id
        if step == b"STEP:result = 1":
            return {"verdict": "PASS", "tight": "PASS", "fails": [],
                    "measurements": {"bbox": [0, 0, 0, 10, 5, 2],
                                     "volume": 100.0}}
        return {"verdict": "FAIL", "tight": "FAIL", "fails": ["bbox"],
                "measurements": {"bbox": [0, 0, 0, 10, 5, 3],
                                 "volume": 150.0}}

    expected = {"M1": {"bbox": [0, 0, 0, 10, 5, 2], "volume": 100.0},
                "M1_wrong": {"bbox": [0, 0, 0, 10, 5, 2], "volume": 100.0}}
    lines = cloud_exec.check_hand([str(a), str(b), str(c)],
                                  exec_fn=fake_exec, grade_fn=fake_grade,
                                  expected=expected)
    assert lines[0].startswith("M1: PASS") and "rel-diff 0.00e+00" in lines[0]
    assert lines[1].startswith("M1_wrong: FAIL") and "rel-diff" in lines[1]
    assert lines[2].startswith("M6: FAIL") and "no STEP" in lines[2]
    # M1_wrong is graded under job M1 (file name prefix).
    assert seen[b"STEP:result = 2"] == "M1"
    assert lines[-1] == "HAND FAIL"  # M6/M10/H6/H13 missing: no HAND OK
    out = capsys.readouterr().out
    assert "M1: PASS" in out and "M1_wrong: FAIL" in out
    assert "HAND FAIL" in out


def _hand_files(tmp_path, names):
    paths = []
    for n in names:
        p = tmp_path / (n + ".py")
        p.write_text("result = %s" % n, encoding="utf-8")
        paths.append(str(p))
    return paths


def _hand_fakes(exact=True, wrong_verdict="FAIL", diff_ok=True):
    """exec/grade fakes for the 7 hand stems; grade under mapped job ids."""

    def fake_exec(source):
        return {"step_bytes": ("STEP:" + source).encode(), "measure": {},
                "log": "", "run_error": None}

    def fake_grade(job_id, step):
        stem = step.decode().split("result = ", 1)[1]
        base = {"bbox": [0, 0, 0, 10, 5, 2], "volume": 100.0}
        if stem in ("M1_wrong", "H13_wrong"):
            meas = dict(base) if diff_ok else {
                "bbox": [0, 0, 0, 10, 5, 3], "volume": 150.0}
            return {"verdict": wrong_verdict, "tight": wrong_verdict,
                    "fails": [] if wrong_verdict == "PASS" else ["bbox"],
                    "measurements": meas}
        meas = dict(base) if exact else {
            "bbox": [0, 0, 0, 10, 5, 3], "volume": 150.0}
        return {"verdict": "PASS", "tight": "PASS", "fails": [],
                "measurements": meas}

    expected = {n: {"bbox": [0, 0, 0, 10, 5, 2], "volume": 100.0}
                for n in ("M1", "M6", "M10", "H6", "H13", "M1_wrong",
                          "H13_wrong")}
    return fake_exec, fake_grade, expected


def test_check_hand_ok_gate(tmp_path, capsys):
    names = ["M1", "M6", "M10", "H6", "H13", "M1_wrong", "H13_wrong"]
    exec_fn, grade_fn, expected = _hand_fakes()
    lines = cloud_exec.check_hand(_hand_files(tmp_path, names),
                                  exec_fn=exec_fn, grade_fn=grade_fn,
                                  expected=expected)
    assert lines[-1] == "HAND OK"
    assert "HAND OK" in capsys.readouterr().out


def test_check_hand_gate_rejects_wrong_pass_and_big_diff(tmp_path):
    names = ["M1", "M6", "M10", "H6", "H13", "M1_wrong", "H13_wrong"]
    # A wrong answer that PASSes is not HAND OK.
    exec_fn, grade_fn, expected = _hand_fakes(wrong_verdict="PASS")
    assert cloud_exec.check_hand(
        _hand_files(tmp_path, names), exec_fn=exec_fn,
        grade_fn=grade_fn, expected=expected)[-1] == "HAND FAIL"
    # A difference over the 1e-6 gate is not HAND OK either.
    exec_fn, grade_fn, expected = _hand_fakes(exact=False)
    assert cloud_exec.check_hand(
        _hand_files(tmp_path, names), exec_fn=exec_fn,
        grade_fn=grade_fn, expected=expected)[-1] == "HAND FAIL"
    # A 6.4e-8-scale Mac-vs-cloud float difference IS HAND OK (1e-6 gate).
    assert cloud_exec.HAND_MAX_REL_DIFF == 1e-6
    assert cloud_exec.hand_gate(
        {n: "PASS" for n in cloud_exec.HAND_MUST_PASS
         } | {n: "FAIL" for n in cloud_exec.HAND_MUST_FAIL},
        {n: 6.4e-8 for n in list(cloud_exec.HAND_MUST_PASS)
         + list(cloud_exec.HAND_MUST_FAIL)}) is True
    assert cloud_exec.hand_gate({"M1": "PASS"}, {}) is False  # no diffs
    assert cloud_exec.hand_gate(
        {n: "PASS" for n in cloud_exec.HAND_MUST_PASS
         } | {n: "FAIL" for n in cloud_exec.HAND_MUST_FAIL},
        {n: 0.0 for n in list(cloud_exec.HAND_MUST_PASS)
         + list(cloud_exec.HAND_MUST_FAIL)}) is True


def test_check_refs_prints_refs_line(capsys):
    n, total = cloud_grade.check_refs(
        build_refs_fn=lambda job: b"STEP",
        grade_fn=lambda jid, step: {"verdict": "PASS", "fails": []})
    assert (n, total) == (30, 30)
    assert "REFS 30/30 PASS" in capsys.readouterr().out


def test_check_refs_names_failures(capsys):
    n, total = cloud_grade.check_refs(
        build_refs_fn=lambda job: b"STEP",
        grade_fn=lambda jid, step: {"verdict": "PASS", "fails": []}
        if jid != "M1" else {"verdict": "FAIL", "fails": ["bbox"]})
    assert (n, total) == (29, 30)
    out = capsys.readouterr().out
    assert "REF FAIL M1" in out and "REFS 29/30 PASS" in out


def test_grader_runs_inside_defining_app():
    """Grader calls run inside the App that defines grade: only the
    sandbox app goes through App.lookup."""
    src = open(os.path.join(HERE, "cloud_grade.py"),
               encoding="utf-8").read()
    assert "lookup_grader_app" not in src  # no grader App.lookup left
    assert "_app.run()" in src  # the App that defines grade
    runner_src = open(os.path.join(HERE, "runner_fc.py"),
                      encoding="utf-8").read()
    assert "lookup_grader_app" not in runner_src
    assert "_cloud_grade._app.run()" in runner_src


def test_grader_image_installs_gl_before_cadquery(monkeypatch):
    """OCP needs libGL.so.1: apt libs install before pip (Round 3.4)."""
    calls = []

    class _GImage:
        def apt_install(self, *pkgs):
            calls.append(("apt", pkgs))
            return self

        def pip_install(self, *pkgs):
            calls.append(("pip", pkgs))
            return self

        def add_local_file(self, local, remote):
            calls.append(("file", (local, remote)))
            return self

    stub = types.SimpleNamespace(
        Image=types.SimpleNamespace(
            from_registry=lambda base: _GImage()))
    monkeypatch.setattr(cloud_grade, "modal", stub)
    cloud_grade.build_grader_image()
    kinds = [k for k, _ in calls]
    assert kinds.index("apt") < kinds.index("pip")
    apt_pkgs = calls[kinds.index("apt")][1]
    for lib in ("libgl1", "libglib2.0-0", "libxrender1", "libx11-6",
                "libxext6"):
        assert lib in apt_pkgs
    pip_pkgs = calls[kinds.index("pip")][1]
    assert "cadquery==2.8" in pip_pkgs


# ------------------------------------------------------- safety probes


def _safety_exec(run_errors):
    """exec_fn serving canned no-STEP run_errors keyed by probe source."""

    def _exec(source):
        return {"step_bytes": None, "measure": None, "log": "",
                "run_error": run_errors[source]}

    return _exec


def test_safety_probes_fail_safe_through_answer_runner():
    import runner_fc as _runner_fc

    # A misspelled Part function is an api_error, never a build.
    _, err = run_one_fc.run_answer_source(cloud_exec.SAFETY_TYPO_SOURCE)
    assert err is not None  # no Part here or a typo there: it raises
    tag = _runner_fc.tag_failure("stop", cloud_exec.SAFETY_TYPO_SOURCE,
                                 err, False, [])
    assert tag == "api_error"
    # `import cadquery` is refused, with the error text kept.
    _, err = run_one_fc.run_answer_source(cloud_exec.SAFETY_CADQUERY_SOURCE)
    assert "refused import" in err
    tag = _runner_fc.tag_failure("stop", cloud_exec.SAFETY_CADQUERY_SOURCE,
                                 err, False, [])
    assert tag == "api_error"
    # The listing probe reports what it found in its error.
    assert "urllib.request.urlopen" in cloud_exec.SAFETY_NETWORK_SOURCE
    assert "jobs" in cloud_exec.SAFETY_LISTING_SOURCE
    assert "expected" in cloud_exec.SAFETY_LISTING_SOURCE
    assert "reference" in cloud_exec.SAFETY_LISTING_SOURCE


def test_check_safety_ok_when_all_four_hold(capsys):
    run_errors = {
        cloud_exec.SAFETY_TYPO_SOURCE:
            "AttributeError: module 'Part' has no attribute 'makeBx'",
        cloud_exec.SAFETY_CADQUERY_SOURCE:
            "refused import: cadquery (answers must use the Part module)",
        cloud_exec.SAFETY_NETWORK_SOURCE:
            "RuntimeError: no network: URLError: <urlopen error blocked>",
        cloud_exec.SAFETY_LISTING_SOURCE:
            "RuntimeError: probe found 0 (none found)",
    }
    lines = cloud_exec.check_safety(exec_fn=_safety_exec(run_errors))
    assert len(lines) == 5  # one line per probe plus the SAFETY line
    assert lines[0].startswith("typo: hold")
    assert lines[1].startswith("cadquery: hold") and "refused" in lines[1]
    assert lines[2].startswith("network: hold")
    assert lines[3].startswith("listing: hold") and "none found" in lines[3]
    assert lines[-1] == "SAFETY OK"
    assert "SAFETY OK" in capsys.readouterr().out


def test_check_safety_fails_on_reachable_network_or_found_files():
    base = {
        cloud_exec.SAFETY_TYPO_SOURCE:
            "AttributeError: module 'Part' has no attribute 'makeBx'",
        cloud_exec.SAFETY_CADQUERY_SOURCE:
            "refused import: cadquery (answers must use the Part module)",
        cloud_exec.SAFETY_NETWORK_SOURCE:
            "RuntimeError: no network: URLError: <urlopen error blocked>",
        cloud_exec.SAFETY_LISTING_SOURCE:
            "RuntimeError: probe found 0 (none found)",
    }
    bad_net = dict(base)
    bad_net[cloud_exec.SAFETY_NETWORK_SOURCE] = \
        "RuntimeError: network reachable"
    assert cloud_exec.check_safety(
        exec_fn=_safety_exec(bad_net))[-1] == "SAFETY FAIL"
    bad_list = dict(base)
    bad_list[cloud_exec.SAFETY_LISTING_SOURCE] = \
        "RuntimeError: probe found 2: ['/work/jobs.json']"
    assert cloud_exec.check_safety(
        exec_fn=_safety_exec(bad_list))[-1] == "SAFETY FAIL"
    bad_cq = dict(base)
    bad_cq[cloud_exec.SAFETY_CADQUERY_SOURCE] = \
        "the answer wrote no STEP: ERROR: no variable named 'result'"
    assert cloud_exec.check_safety(
        exec_fn=_safety_exec(bad_cq))[-1] == "SAFETY FAIL"


def test_check_safety_cli_flag(monkeypatch, capsys):
    monkeypatch.setattr(
        cloud_exec, "run_answer_in_box",
        _safety_exec({
            cloud_exec.SAFETY_TYPO_SOURCE:
                "AttributeError: module 'Part' has no attribute 'makeBx'",
            cloud_exec.SAFETY_CADQUERY_SOURCE:
                "refused import: cadquery (answers must use the Part module)",
            cloud_exec.SAFETY_NETWORK_SOURCE:
                "RuntimeError: no network: URLError: blocked",
            cloud_exec.SAFETY_LISTING_SOURCE:
                "RuntimeError: probe found 0 (none found)",
        }))
    assert cloud_exec.main(["--check-safety"]) == 0
    assert "SAFETY OK" in capsys.readouterr().out
