"""Cloud grader for FreeCAD answers (SPEC section 2).

A separate Modal Function (CPU, our own trusted code) with CadQuery 2.8
+ experiments/first-test/{jobs.py, checks.py, expected.json} baked into
its image. Input: job id + STEP bytes; output: the verdict at 0.2% (the
verdict) and at 1e-6, the failed checks, measurements. It never runs
model code: the STEP is only imported and measured.

Why: the reference parts live only here, never in the answer box.

The reference values are loaded inside the image build / grader only
(load_expected); they are never printed or logged. Tests use small fake
expected dicts, never the real file.
"""

import os

TOL_VERDICT = 0.002  # 0.2%: the verdict (the baseline's yardstick)
TOL_TIGHT = 1e-6  # also recorded

FIRST_TEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "first-test")
EXPECTED_NAME = "expected.json"

try:
    import modal
except ImportError:  # offline: pure grading helpers still work
    modal = None


def expected_path(path=None):
    """Path of the baked-in expected.json (first-test dir by default)."""
    return path or os.path.join(FIRST_TEST_DIR, EXPECTED_NAME)


def load_expected(path=None):
    """Load expected.json (grader image build only). Never print it."""
    import json as _json

    with open(expected_path(path), encoding="utf-8") as f:
        return _json.load(f)


def combine_verdict(check_fails, mismatch, tol):
    """PASS iff every check holds and the mismatch fraction is within tol.

    `check_fails`: failed checks at the baseline yardstick (bbox, volume,
    ...); `mismatch`: answer-XOR-reference fraction of reference volume
    (None when the shape could not be intersected). Returns
    (passed, fails).
    """
    fails = list(check_fails or [])
    if mismatch is None:
        fails = fails + ["mismatch error"]
    elif mismatch > tol:
        fails = fails + ["mismatch %.1f%%" % (100.0 * mismatch)]
    return (not fails), fails


def grade_result(check_fails, mismatch, measurements):
    """Grade one imported STEP: verdict at 0.2% + the 1e-6 recording.

    Returns {"verdict", "tight", "fails", "fails_tight", "measurements"}.
    Pure (no cadquery): the Modal function supplies check_fails and the
    mismatch fraction from checks.score; tests pass synthetic values.
    """
    passed, fails = combine_verdict(check_fails, mismatch, TOL_VERDICT)
    passed_tight, fails_tight = combine_verdict(check_fails, mismatch, TOL_TIGHT)
    return {
        "verdict": "PASS" if passed else "FAIL",
        "tight": "PASS" if passed_tight else "FAIL",
        "fails": fails,
        "fails_tight": fails_tight,
        "measurements": measurements,
    }


def grade_measurements(measure, expected, mismatch):
    """Grade from already-measured values (offline helper).

    `measure`: {"bbox", ...} of the answer; `expected`: the job's
    expected values; `mismatch`: the XOR fraction. check_fails come from
    the baseline compare (bbox faces within 0.1 mm, volume/area within
    1%, com within 0.3 mm, exactly 1 valid solid).
    """
    return grade_result(compare_measurements(measure, expected), mismatch, measure)


def compare_measurements(m, e):
    """Baseline check failures for measured values (mirrors checks.compare)."""
    fails = []
    try:
        if m.get("solids") != 1:
            fails.append("solids=%s" % m.get("solids"))
        if not m.get("valid", True):
            fails.append("invalid shape")
        if any(abs(a - b) > 0.1 for a, b in zip(m["bbox"], e["bbox"])):
            fails.append("bbox")
        for k in ("volume", "area"):
            if k in m and k in e and abs(m[k] - e[k]) > 0.01 * abs(e[k]):
                fails.append(k)
        if "com" in m and "com" in e and any(
                abs(a - b) > 0.3 for a, b in zip(m["com"], e["com"])):
            fails.append("com")
    except (KeyError, TypeError):
        fails.append("scoring error")
    return fails


def build_grader_image():
    """Modal image for the grader function: CadQuery 2.8 + jobs.py +
    checks.py + expected.json baked in (references live only here).
    libGL etc. are apt-installed before pip: CadQuery's OCP needs
    libGL.so.1."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the grader")
    return (
        modal.Image.from_registry("python:3.12-slim")
        .apt_install("libgl1", "libglib2.0-0", "libxrender1", "libx11-6",
                     "libxext6")
        .pip_install("cadquery==2.8")
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, "jobs.py"), "/grader/jobs.py")
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, "checks.py"), "/grader/checks.py")
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, EXPECTED_NAME), "/grader/expected.json")
    )


GRADER_APP_NAME = "forge-freecad-grader"  # Modal app the grader runs under


if modal is not None:
    _grader_image = None

    def _image():
        global _grader_image
        if _grader_image is None:
            _grader_image = build_grader_image()
        return _grader_image

    _app = modal.App(GRADER_APP_NAME)

    @_app.function(image=_image(), cpu=1, timeout=300)
    def grade(job_id, step_bytes):
        """Grade one STEP (bytes) for one job id. Never runs model code."""
        import sys as _sys
        import tempfile as _tf

        _sys.path.insert(0, "/grader")
        import checks as _checks  # noqa: E402
        import jobs as _jobs  # noqa: E402
        from cadquery import importers as _importers  # noqa: E402

        expected = load_expected("/grader/expected.json")
        job = next(j for j in _jobs.JOBS if j["id"] == job_id)
        with _tf.NamedTemporaryFile(suffix=".step", delete=False) as f:
            f.write(bytes(step_bytes))
            path = f.name
        answer = _importers.importStep(path)
        ref = job["build"]()
        old = _checks.TOL_DIFF
        try:
            _checks.TOL_DIFF = TOL_VERDICT
            passed, fails, m = _checks.score(answer, ref, expected[job_id])
            d = m.get("mismatch")
            _checks.TOL_DIFF = TOL_TIGHT
            passed_t, fails_t, _m2 = _checks.score(answer, ref, expected[job_id])
        finally:
            _checks.TOL_DIFF = old
        return {
            "verdict": "PASS" if passed else "FAIL",
            "tight": "PASS" if passed_t else "FAIL",
            "fails": list(fails),
            "fails_tight": list(fails_t),
            "mismatch": d,
            "measurements": {k: m.get(k) for k in
                             ("bbox", "volume", "area", "com", "solids", "valid")},
        }


# ------------------------------------------------------- live check CLI
# (Claude runs this against real Modal; never in unit tests.)


def check_refs(build_refs_fn=None, grade_fn=None):
    """Send the 30 CadQuery references through the grader.

    Prints `REFS n/30 PASS` (the grader holds the references, so all 30
    must PASS). `build_refs_fn(job)` returns STEP bytes for one job and
    defaults to exporting the reference part locally (needs cadquery);
    `grade_fn` defaults to the cloud grader (needs the grader app
    context). Both are injected in tests. Returns (n_pass, n_jobs).
    """
    import sys as _sys

    _sys.path.insert(0, FIRST_TEST_DIR)
    import jobs as _jobs  # noqa: E402  (frozen file; imported, not modified)

    if build_refs_fn is None:
        def build_refs_fn(job):
            import tempfile as _tf

            from cadquery import exporters as _exporters

            with _tf.NamedTemporaryFile(suffix=".step",
                                        delete=False) as f:
                path = f.name
            _exporters.export(job["build"](), path)
            with open(path, "rb") as f:
                return f.read()

    if grade_fn is None:
        grade_fn = grade.remote
    n_pass, n_jobs = 0, 0
    # The 30 main jobs (medium + hard), not the 3 dry jobs.
    for job in [j for j in _jobs.JOBS if j.get("level") != "dry"]:
        n_jobs += 1
        graded = grade_fn(job["id"], build_refs_fn(job))
        if graded.get("verdict") == "PASS":
            n_pass += 1
        else:
            print("REF FAIL %s: %s" % (job["id"], graded.get("fails")))
    print("REFS %d/%d PASS" % (n_pass, n_jobs))
    return n_pass, n_jobs


def main(argv=None):
    """CLI: --check-refs sends the 30 references through the grader."""
    import argparse as _ap

    parser = _ap.ArgumentParser(description="FreeCAD cloud-grader checks.")
    parser.add_argument("--check-refs", action="store_true")
    args = parser.parse_args(argv)
    if args.check_refs:
        if modal is None:
            raise RuntimeError(
                "modal is not installed; cannot reach the grader")
        # Grade inside the App that defines grade: App.lookup(...).run()
        # fails with "App is already running".
        with modal.enable_output():
            with _app.run():
                check_refs()
        return 0
    parser.error("need --check-refs")
    return 2


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
