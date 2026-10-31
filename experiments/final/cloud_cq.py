"""Cloud CadQuery box + grader (MUSE_SPEC section 1).

Why this file exists (user decision 2026-10-29): nothing a model writes
may run on the Mac. Every answer runs in a fresh Modal Sandbox
(block_network=True, no secrets, no volumes, cpu 1, memory 1024-4096
MiB, 90 s box); one sandbox per answer, terminated after use.

Image: python:3.12-slim + the libGL apt line + ``cadquery==2.8.0
cadquery-ocp==7.9.3.1`` (the Mac's versions; the grader pins the same)
+ run_cq_box.py. It holds no references, jobs or expected files.

Flow: write answer.py with sb.filesystem.write_text, run
``python /work/run_cq_box.py /work`` with sb.exec (60 s inside the 90 s
box, the baseline's speed limit), read back /work/answer.brep (bytes) +
/work/measure.json, then sb.terminate(). The run script takes the
``result`` variable (same rule as runner.run_code: Workplane gives its
solid) and writes the part as BREP (exact; not STEP). BREP answers over
20 MB are refused. The verdict and failure tags come only from the
grader; measure.json is for logs (the box runs untrusted code and must
not score itself).

Grader: a Modal function (app ``forge-cq-grader``, cpu 1) with CadQuery
2.8 and checks.py baked in, plus /grader/first-test/{jobs.py,
expected.json} and /grader/factory/jobs.jsonl. ``grade(exam, job_id,
brep_bytes)`` scores first-test against expected.json exactly as
runner.py does; for factory it builds the job's reference program in
the grader and scores both ways (0.2% verdict + 1e-6 tight).

Modal is imported lazily so the config helpers (sandbox kwargs, image
file list) are unit-testable offline. Tests inject a fake sandbox; any
test that could reach a real Modal call monkeypatches it to raise.
"""

import os

CQ_VERSION = "2.8.0"
OCP_VERSION = "7.9.3.1"

CPU = 1
MEMORY_MIB = (1024, 4096)
SANDBOX_TIMEOUT_S = 90  # the box: one sandbox per answer
EXEC_TIMEOUT_S = 60  # the answer run inside it (the baseline's limit)
MAX_BREP_BYTES = 20 * 1024 * 1024  # BREP answers over 20 MB are refused

WORK_DIR = "/work"
ANSWER_NAME = "answer.py"
RUN_SCRIPT = "run_cq_box.py"  # experiments/final/run_cq_box.py, baked in
BREP_PATH = WORK_DIR + "/answer.brep"
MEASURE_PATH = WORK_DIR + "/measure.json"
RUN_PATH = WORK_DIR + "/" + RUN_SCRIPT

BOOTSTRAP = "python %s %s" % (RUN_PATH, WORK_DIR)

# The box image holds ONLY CadQuery + run_cq_box.py.
IMAGE_FILES = [RUN_SCRIPT]

# The grader.
TOL_VERDICT = 0.002  # 0.2%: the verdict (the baseline's yardstick)
TOL_TIGHT = 1e-6  # also recorded
VALID_EXAMS = ("first-test", "factory")

HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_TEST_DIR = os.path.join(os.path.dirname(HERE), "first-test")
FACTORY_DIR = os.path.join(os.path.dirname(HERE), "factory")
EXPECTED_NAME = "expected.json"
FACTORY_JOBS_NAME = "jobs.jsonl"

try:
    import modal
except ImportError:  # offline: config helpers still work; runs refuse
    modal = None


def sandbox_kwargs():
    """Keyword args for modal.Sandbox.create: no network, no secrets,
    no volumes, one cpu, 1-4 GiB, 90 s. No "secrets"/"volumes" keys."""
    return {
        "block_network": True,
        "cpu": CPU,
        "memory": MEMORY_MIB,
        "timeout": SANDBOX_TIMEOUT_S,
    }


def image_files():
    """Files baked into the box image besides CadQuery itself."""
    return list(IMAGE_FILES)


EXEC_APP_NAME = "forge-cq"  # Modal app the boxes run under


def lookup_exec_app():
    """The Modal app handle for boxes (created on first lookup)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot look up the app")
    return modal.App.lookup(EXEC_APP_NAME, create_if_missing=True)


def pip_spec():
    """Pinned CadQuery install (the Mac's versions; the grader matches)."""
    return ["cadquery==%s" % CQ_VERSION, "cadquery-ocp==%s" % OCP_VERSION]


def build_image():
    """Modal image: python:3.12-slim + the libGL apt line + pinned
    CadQuery + the run script. Lazy: no network or Modal call until the
    image builds remotely."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the box image")
    return (
        modal.Image.from_registry("python:3.12-slim")
        .apt_install("libgl1", "libglib2.0-0", "libxrender1", "libx11-6",
                     "libxext6")
        .pip_install(*pip_spec())
        .add_local_file(
            os.path.join(HERE, RUN_SCRIPT),
            RUN_PATH,
        )
    )


def build_sandbox(image=None, lifetime_s=None):
    """Create one fresh sandbox for one answer (terminated after use).

    Modal requires the app, so the box is created under the forge-cq
    app handle, not ad hoc. lifetime_s (Claude small fix 2026-10-31,
    verifier B3b) overrides the 90 s box lifetime for a long reused batch
    box; the per-answer exec timeout is unchanged."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot create a sandbox")
    app = lookup_exec_app()
    kwargs = sandbox_kwargs()
    if lifetime_s:
        kwargs["timeout"] = int(lifetime_s)
    return modal.Sandbox.create(
        app=app, image=image or build_image(), **kwargs)


NO_BREP_PREFIX = "the answer wrote no BREP"


def _missing_file_errors():
    """Exception types meaning "the answer wrote no BREP" (a FAIL).

    Reading a missing BREP/measure raises
    modal.exception.SandboxFilesystemNotFoundError on the real box
    (not a FileNotFoundError subclass); KeyError covers test fakes.
    Anything else from the box still propagates to the runner, which
    tags it harness/INVALID."""
    errs = [FileNotFoundError, KeyError]
    exc_mod = getattr(modal, "exception", None) if modal is not None else None
    cls = getattr(exc_mod, "SandboxFilesystemNotFoundError", None)
    if isinstance(cls, type):
        errs.append(cls)
    return tuple(errs)


def _read_stream(stream):
    """Best-effort text from a box process stream (stdout or stderr)."""
    try:
        if stream is not None and hasattr(stream, "read"):
            return stream.read() or ""
    except Exception:  # noqa: BLE001 -- logs are best-effort
        pass
    return ""


def run_answer_in_box(answer_code, sandbox=None, sandbox_factory=None):
    """Run one answer string in the box. Returns {"brep_bytes",
    "measure", "log", "run_error"}; measure is logs-only, the grader
    decides.

    `sandbox` (a live or fake sandbox) or `sandbox_factory` (called with
    no args) is injected in tests; without either, a real Modal sandbox
    is created. BREP output over 20 MB raises ValueError. When the answer
    writes no BREP (run_cq_box exits 2 with its ERROR line on stderr),
    nothing raises: brep_bytes/measure come back None and run_error holds
    run_cq_box's stderr (its ERROR line), for the runner's run_error.
    """
    own = False
    if sandbox is None:
        if sandbox_factory is not None:
            sandbox = sandbox_factory()
        else:
            sandbox = build_sandbox()
        own = True
    try:
        # Modal 1.6.3 is write_text(data, remote_path): keywords, so a
        # reordered fake or SDK signature cannot silently swap the args.
        sandbox.filesystem.write_text(
            data=answer_code or "",
            remote_path=WORK_DIR + "/" + ANSWER_NAME)
        proc = sandbox.exec(
            "python", RUN_PATH, WORK_DIR,
            env={"CQ_SCRATCH": WORK_DIR},
            timeout=EXEC_TIMEOUT_S,
        )
        log = _read_stream(getattr(proc, "stdout", None))
        err_text = _read_stream(getattr(proc, "stderr", None)).strip()
        try:
            brep_bytes = sandbox.filesystem.read_bytes(
                remote_path=BREP_PATH)
            measure_text = sandbox.filesystem.read_text(
                remote_path=MEASURE_PATH)
        except _missing_file_errors():
            detail = err_text or log.strip()
            run_error = NO_BREP_PREFIX + (": %s" % detail if detail else "")
            return {"brep_bytes": None, "measure": None, "log": log,
                    "run_error": run_error}
        if len(brep_bytes) > MAX_BREP_BYTES:
            raise ValueError(
                "BREP is %d bytes (over the %d-byte limit); refusing"
                % (len(brep_bytes), MAX_BREP_BYTES))
        import json as _json

        measure = _json.loads(measure_text)
        return {"brep_bytes": brep_bytes, "measure": measure, "log": log,
                "run_error": None}
    finally:
        if own:
            try:
                sandbox.terminate()
            except Exception:  # noqa: BLE001 -- terminate is best-effort
                pass


# ------------------------------------------------------- grader (pure part)


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
    """Grade one imported BREP: verdict at 0.2% + the 1e-6 recording.

    Returns {"verdict", "tight", "fails", "fails_tight", "measurements"}.
    Pure (no cadquery): the Modal function supplies check_fails and the
    mismatch fraction from checks.score; tests pass synthetic values.
    """
    passed, fails = combine_verdict(check_fails, mismatch, TOL_VERDICT)
    passed_tight, fails_tight = combine_verdict(check_fails, mismatch,
                                               TOL_TIGHT)
    return {
        "verdict": "PASS" if passed else "FAIL",
        "tight": "PASS" if passed_tight else "FAIL",
        "fails": fails,
        "fails_tight": fails_tight,
        "measurements": measurements,
    }


PRECISE_VOLUME_EPS = 1e-9  # factory H1 (2026-10-30)


def precise_volume(shape):
    """BRepGProp volume at eps 1e-9 (factory H1, 2026-10-30).

    The default Shape.Volume() is noisy on some factory solids (F5 up
    to 6.1e-4, F9 2.7e-6), so text-faithful answers failed 1e-6. Only
    the volumes feeding the factory mismatch use this; every other
    measurement keeps checks.measure as today.
    """
    from OCP.BRepGProp import BRepGProp as _BRepGProp
    from OCP.GProp import GProp_GProps as _GProp

    top = shape.wrapped if hasattr(shape, "wrapped") else shape
    props = _GProp()
    _BRepGProp.VolumeProperties_s(top, props, PRECISE_VOLUME_EPS)
    return props.Mass()


def factory_mismatch(answer_shape, ref_shape):
    """Answer-XOR-reference fraction with precise volumes (factory H1).

    Mirrors checks.mismatch exactly except the three volumes (answer,
    reference, intersection) come from precise_volume.
    """
    import sys as _sys

    if FIRST_TEST_DIR not in _sys.path:
        _sys.path.insert(0, FIRST_TEST_DIR)
    import checks as _checks

    a, r = _checks.to_shape(answer_shape), _checks.to_shape(ref_shape)
    inter = a.intersect(r)
    va, vr, vi = (precise_volume(s) for s in (a, r, inter))
    return (va + vr - 2 * vi) / vr


def factory_score(answer, reference, expected):
    """checks.score for factory answers with a precise mismatch (H1).

    Mirrors checks.score line for line except the mismatch fraction
    uses factory_mismatch. Tolerance behavior (checks.TOL_DIFF) is
    unchanged: 1e-6 tight, 0.2% verdict.
    """
    import sys as _sys

    if FIRST_TEST_DIR not in _sys.path:
        _sys.path.insert(0, FIRST_TEST_DIR)
    import checks as _checks

    m = _checks.measure(answer)
    fails = _checks.compare(m, expected)
    try:
        d = factory_mismatch(answer, reference)
    except Exception as e:  # a broken shape can't be intersected
        d, fails = None, fails + [("mismatch error %r" % (e,))[:120]]
    m["mismatch"] = None if d is None else round(d, 5)
    if d is not None and d > _checks.TOL_DIFF:
        fails.append("mismatch %.1f%%" % (100.0 * d))
    return (not fails), fails, m


def score_shapes(answer_shape, ref_shape, expected, precise_mismatch=False):
    """Score built shapes at both tolerances (needs cadquery + checks).

    The reference shapes are trusted code (exam jobs.py, the generator);
    only model answers must stay out of this process. Returns the
    grade_result dict plus "mismatch". `checks` is imported lazily from
    the frozen first-test copy. With precise_mismatch=True (the factory
    grader, H1) the mismatch uses precise BRepGProp volumes; the
    default False path calls checks.score exactly as before.
    """
    import sys as _sys

    if FIRST_TEST_DIR not in _sys.path:
        _sys.path.insert(0, FIRST_TEST_DIR)
    import checks as _checks

    old = _checks.TOL_DIFF
    try:
        _checks.TOL_DIFF = TOL_VERDICT
        if precise_mismatch:
            passed, fails, m = factory_score(answer_shape, ref_shape,
                                             expected)
        else:
            passed, fails, m = _checks.score(answer_shape, ref_shape,
                                             expected)
        d = m.get("mismatch")
        _checks.TOL_DIFF = TOL_TIGHT
        if precise_mismatch:
            passed_t, fails_t, _m2 = factory_score(answer_shape, ref_shape,
                                                  expected)
        else:
            passed_t, fails_t, _m2 = _checks.score(answer_shape, ref_shape,
                                                  expected)
    finally:
        _checks.TOL_DIFF = old
    out = grade_result(fails, d, {k: m.get(k) for k in
                                  ("bbox", "volume", "area", "com",
                                   "solids", "valid")})
    out["mismatch"] = d
    # The per-tolerance fail lists come from the two score runs (the
    # pure combiner above only mirrors them for synthetic inputs).
    out["verdict"] = "PASS" if passed else "FAIL"
    out["tight"] = "PASS" if passed_t else "FAIL"
    out["fails"] = list(fails)
    out["fails_tight"] = list(fails_t)
    return out


def build_reference_shape(source):
    """Build a factory reference shape from its program source.

    The source is trusted generator code; it assigns `result` (same rule
    as answers: Workplane gives its solid). Needs cadquery.
    """
    import cadquery as _cq

    ns = {"__name__": "__main__"}
    exec(compile(source, "<reference>", "exec"), ns)
    result = ns["result"]
    if isinstance(result, _cq.Workplane):
        vals = [v for v in result.vals() if isinstance(v, _cq.Shape)]
        if len(vals) == 1:
            return vals[0]
        return _cq.Compound.makeCompound(vals)
    if isinstance(result, _cq.Assembly):
        return result.toCompound()
    return result


def import_brep_shape(brep_bytes):
    """Import BREP bytes to a shape (grader-side; needs cadquery)."""
    import tempfile as _tf

    import cadquery as _cq
    from cadquery import importers as _importers

    with _tf.NamedTemporaryFile(suffix=".brep", delete=False) as f:
        f.write(bytes(brep_bytes))
        path = f.name
    try:
        return _importers.importShape(
            _importers.ImportTypes.BREP, path).val()
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def measure_shape(shape):
    """checks.measure on a shape (grader-side measure of the BREP)."""
    import sys as _sys

    if FIRST_TEST_DIR not in _sys.path:
        _sys.path.insert(0, FIRST_TEST_DIR)
    import checks as _checks

    return _checks.measure(shape)


def load_factory_jobs(path=None):
    """Read the factory jobs file (id, family, text, reference source)."""
    import json as _json

    with open(path or os.path.join(FACTORY_DIR, FACTORY_JOBS_NAME),
              encoding="utf-8") as f:
        return [_json.loads(line) for line in f if line.strip()]


def factory_job(job_id, jobs=None):
    """The factory job dict for an id (ValueError when unknown)."""
    for job in jobs if jobs is not None else load_factory_jobs():
        if job["id"] == job_id:
            return job
    raise ValueError("unknown factory job %r" % (job_id,))


def factory_reference(job_id, jobs=None, reference=None):
    """Reference source for a factory job id (R5 B5).

    Baked-first: a known id always grades against the baked jobs file
    (old ids grade exactly as before, even when a reference is also
    passed). An unknown id (R5T/R5D, not yet baked) grades against the
    passed `reference`. Unknown without a reference raises ValueError,
    never StopIteration.
    """
    known = None
    for job in jobs if jobs is not None else load_factory_jobs():
        if job.get("id") == job_id:
            known = job
            break
    if known is not None:
        return known["reference"]
    if isinstance(reference, str) and reference.strip():
        return reference
    raise ValueError(
        "unknown factory job %r (not in the grader's jobs file; "
        "pass the job's reference with the call)" % (job_id,))


def factory_grade_fn(jobs, remote_fn):
    """Grade closure that carries each job's reference (R5 B5).

    Returns grade_fn(exam, job_id, brep) for check_refs / the runner:
    factory jobs with a reference pass it along (the grader uses it
    for ids outside the baked file); first-test jobs, or factory jobs
    without one, call remote_fn exactly as before.
    """
    by_id = {j.get("id"): j for j in jobs or () if isinstance(j, dict)}

    def _grade(exam_arg, job_id, brep_bytes):
        ref = by_id.get(job_id, {}).get("reference")
        if exam_arg == "factory" and isinstance(ref, str) and ref.strip():
            return remote_fn(exam_arg, job_id, brep_bytes,
                             reference=ref)
        return remote_fn(exam_arg, job_id, brep_bytes)

    return _grade


def grade_shapes_for_exam(exam, job_id, answer_shape, first_jobs=None,
                          factory_jobs=None, expected=None):
    """Score a built answer shape under one exam (needs cadquery).

    first-test scores against expected.json exactly as runner.py does;
    factory builds the job's reference program and uses its measurements
    as the expected values. Returns the score_shapes dict.
    """
    import sys as _sys

    if FIRST_TEST_DIR not in _sys.path:
        _sys.path.insert(0, FIRST_TEST_DIR)
    import checks as _checks

    if exam == "factory":
        job = factory_job(
            job_id, factory_jobs or load_factory_jobs())
        ref_shape = build_reference_shape(job["reference"])
        exp = _checks.measure(ref_shape)
        return score_shapes(answer_shape, ref_shape, exp,
                            precise_mismatch=True)
    if first_jobs is None:
        import importlib.util as _ilu

        spec = _ilu.spec_from_file_location(
            "exam_jobs_cq", os.path.join(FIRST_TEST_DIR, "jobs.py"))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        first_jobs = mod.JOBS
    if expected is None:
        import json as _json

        with open(os.path.join(FIRST_TEST_DIR, EXPECTED_NAME),
                  encoding="utf-8") as f:
            expected = _json.load(f)
    job = next(j for j in first_jobs if j["id"] == job_id)
    return score_shapes(answer_shape, job["build"](), expected[job_id])


# ------------------------------------------------------- Modal grader image


def build_grader_image():
    """Modal image for the grader function: CadQuery 2.8 + both exams
    baked in (references live only here). libGL etc. are apt-installed
    before pip: CadQuery's OCP needs libGL.so.1."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the grader")
    return (
        modal.Image.from_registry("python:3.12-slim")
        .apt_install("libgl1", "libglib2.0-0", "libxrender1", "libx11-6",
                     "libxext6")
        .pip_install(*pip_spec())
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, "jobs.py"),
            "/grader/first-test/jobs.py")
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, "checks.py"), "/grader/checks.py")
        .add_local_file(
            os.path.join(FIRST_TEST_DIR, EXPECTED_NAME),
            "/grader/first-test/expected.json")
        .add_local_file(
            os.path.join(FACTORY_DIR, FACTORY_JOBS_NAME),
            "/grader/factory/jobs.jsonl")
    )


GRADER_APP_NAME = "forge-cq-grader"  # Modal app the grader runs under


if modal is not None:
    _grader_image = None

    def _image():
        global _grader_image
        if _grader_image is None:
            _grader_image = build_grader_image()
        return _grader_image

    _app = modal.App(GRADER_APP_NAME)

    @_app.function(image=_image(), cpu=1, timeout=300)
    def grade(exam, job_id, brep_bytes, reference=None):
        """Grade one BREP (bytes) for one job id in one exam.

        first-test scores against expected.json exactly as runner.py
        does; factory builds the job's reference program in the grader
        and scores both ways (0.2% verdict + 1e-6 tight). Never runs
        model code: the BREP is only imported and measured.

        R5 B5: for factory, a passed `reference` grades ids outside the
        baked jobs.jsonl (R5T/R5D); baked ids always use the baked file
        (old verdicts unchanged). Unknown ids raise ValueError.
        """
        import sys as _sys

        _sys.path.insert(0, "/grader")
        import checks as _checks  # noqa: E402
        from cadquery import importers as _importers  # noqa: E402
        import tempfile as _tf  # noqa: E402

        with _tf.NamedTemporaryFile(suffix=".brep",
                                    delete=False) as f:
            f.write(bytes(brep_bytes))
            path = f.name
        answer = _importers.importShape(
            _importers.ImportTypes.BREP, path).val()
        if exam == "factory":
            import json as _json  # noqa: E402

            jobs = [_json.loads(line) for line in open(
                "/grader/factory/jobs.jsonl", encoding="utf-8")
                if line.strip()]
            known = next(
                (j for j in jobs if j["id"] == job_id), None)
            if known is not None:
                source = known["reference"]
            elif isinstance(reference, str) and reference.strip():
                source = reference
            else:
                raise ValueError(
                    "unknown factory job %r (not in "
                    "/grader/factory/jobs.jsonl; pass reference=...)"
                    % (job_id,))
            ns = {"__name__": "__main__"}
            exec(compile(source, "<reference>", "exec"), ns)
            ref = _checks.to_shape(ns["result"])
            expected = _checks.measure(ref)
        else:
            _sys.path.insert(0, "/grader/first-test")
            import jobs as _jobs  # noqa: E402

            def _load(path):
                import json as _json

                with open(path, encoding="utf-8") as f:
                    return _json.load(f)

            expected_all = _load("/grader/first-test/expected.json")
            job = next(
                (j for j in _jobs.JOBS if j["id"] == job_id), None)
            if job is None:
                raise ValueError(
                    "unknown first-test job %r" % (job_id,))
            ref = job["build"]()
            expected = expected_all[job_id]
        old = _checks.TOL_DIFF
        try:
            _checks.TOL_DIFF = TOL_VERDICT
            if exam == "factory":
                passed, fails, m = factory_score(answer, ref, expected)
            else:
                passed, fails, m = _checks.score(answer, ref, expected)
            d = m.get("mismatch")
            _checks.TOL_DIFF = TOL_TIGHT
            if exam == "factory":
                passed_t, fails_t, _m2 = factory_score(answer, ref,
                                                      expected)
            else:
                passed_t, fails_t, _m2 = _checks.score(answer, ref,
                                                      expected)
        finally:
            _checks.TOL_DIFF = old
        return {
            "verdict": "PASS" if passed else "FAIL",
            "tight": "PASS" if passed_t else "FAIL",
            "fails": list(fails),
            "fails_tight": list(fails_t),
            "mismatch": d,
            "measurements": {k: m.get(k) for k in
                             ("bbox", "volume", "area", "com", "solids",
                              "valid")},
        }

    @_app.function(image=_image(), cpu=1, timeout=300)
    def measure_brep(brep_bytes):
        """Grader-side measure of one BREP (no scoring): the §4 exam-guard
        hook uses this for training-record code. Never runs model code."""
        import sys as _sys

        _sys.path.insert(0, "/grader")
        import checks as _checks  # noqa: E402
        from cadquery import importers as _importers  # noqa: E402
        import tempfile as _tf  # noqa: E402

        with _tf.NamedTemporaryFile(suffix=".brep",
                                    delete=False) as f:
            f.write(bytes(brep_bytes))
            path = f.name
        shape = _importers.importShape(
            _importers.ImportTypes.BREP, path).val()
        return _checks.measure(shape)


# ------------------------------------------------------- check-refs + regrade


def _first_test_jobs():
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location(
        "exam_jobs_cq_refs", os.path.join(FIRST_TEST_DIR, "jobs.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.JOBS


def default_build_brep(exam, job):
    """Export a trusted reference to BREP locally (needs cadquery).

    Reference programs are trusted generator/exam code and may build
    locally; only model answers must go through the box. For factory
    the job's reference source is executed; for first-test the builder.
    """
    from cadquery import exporters as _exporters

    import tempfile as _tf

    if exam == "factory":
        shape = build_reference_shape(job["reference"])
    else:
        shape = job["build"]()
    with _tf.NamedTemporaryFile(suffix=".brep", delete=False) as f:
        path = f.name
    _exporters.export(shape, path, exportType="BREP")
    with open(path, "rb") as f:
        return f.read()


def check_refs(exam="first-test", build_brep_fn=None, grade_fn=None,
               jobs=None, jobs_file=None):
    """Send each reference through the grader at 1e-6.

    Prints `REFS n/total PASS`. `build_brep_fn(exam, job)` returns BREP
    bytes for one job (default: trusted local export); `grade_fn(exam,
    job_id, brep_bytes)` defaults to the cloud grader (needs the grader
    app context) and carries each factory job's reference, so R5T/R5D
    files check without being baked in. Both are injected in tests.
    `jobs` (a list) or `jobs_file` (a factory jobs file, e.g. an R5 set)
    overrides the default corpus; `jobs_file` with first-test refuses.
    Returns (n_pass, n_jobs).
    """
    if jobs is None:
        if jobs_file is not None:
            if exam != "factory":
                raise ValueError(
                    "--jobs-file only applies to exam 'factory'")
            jobs = load_factory_jobs(jobs_file)
        elif exam == "factory":
            jobs = load_factory_jobs()
        elif exam == "first-test":
            jobs = [j for j in _first_test_jobs()
                    if j.get("level") != "dry"]
        else:
            raise ValueError("unknown exam %r" % (exam,))
    if build_brep_fn is None:
        build_brep_fn = default_build_brep
    if grade_fn is None:
        grade_fn = factory_grade_fn(
            jobs if exam == "factory" else (),
            grade.remote)
    n_pass, n_jobs = 0, 0
    for job in jobs:
        n_jobs += 1
        graded = grade_fn(exam, job["id"], build_brep_fn(exam, job))
        if graded.get("tight", graded.get("verdict")) == "PASS":
            n_pass += 1
        else:
            print("REF FAIL %s: %s"
                  % (job["id"], graded.get("fails_tight",
                                           graded.get("fails"))))
    print("REFS %d/%d PASS" % (n_pass, n_jobs))
    return n_pass, n_jobs


MEASURE_KEYS = ("bbox", "volume", "area", "com", "solids", "valid")


def measure_same(old, new):
    """True when box measurements equal the recorded ones at the recorded
    print precision (both are checks.measure dicts, rounded to 3). Two
    missing measurements count as same; one missing counts as changed.
    """
    if old is None and new is None:
        return True
    if old is None or new is None:
        return False
    try:
        return all((old or {}).get(k) == (new or {}).get(k)
                   for k in MEASURE_KEYS)
    except (AttributeError, TypeError):
        return False


def old_verdict_of(rec):
    """The recorded verdict (first-test `outcome` or the cloud `verdict`)."""
    return rec.get("verdict", rec.get("outcome"))


def job_id_of(rec):
    """The record's job id (first-test `job` or factory `id`)."""
    return rec.get("job", rec.get("id"))


def code_of(rec):
    """The recorded answer's code (first-test `code`/`extracted_code`)."""
    code = rec.get("code", rec.get("extracted_code"))
    return code if isinstance(code, str) else ""


def regrade_calls(records, exam="first-test", exec_fn=None, grade_fn=None):
    """Re-run recorded answers in the box and re-grade each BREP.

    Returns (rows, n_same_verdict, n_changed_verdict, n_same_measure,
    n_changed_measure). Each row holds job, old_verdict, new_verdict
    (0.2%), new_tight (1e-6) and measure_same (box measurements vs the
    recorded ones). `exec_fn`/`grade_fn` are injected in tests; by
    default the real box and the cloud grader (needs the grader app
    context) are used. An answer that writes no BREP re-grades as FAIL
    with its run error.
    """
    if exec_fn is None:
        exec_fn = run_answer_in_box
    if grade_fn is None:
        def grade_fn(exam_arg, job_id, brep_bytes):
            return grade.remote(exam_arg, job_id, brep_bytes)
    rows = []
    for rec in records:
        job_id = job_id_of(rec)
        old = old_verdict_of(rec)
        boxed = exec_fn(code_of(rec))
        if boxed is None or boxed.get("brep_bytes") is None:
            rows.append({
                "job": job_id,
                "old_verdict": old,
                "new_verdict": "FAIL",
                "new_tight": "FAIL",
                "fails": [],
                "run_error": ((boxed or {}).get("run_error")
                              or NO_BREP_PREFIX),
                "measure_same": measure_same(
                    rec.get("measurements"), None),
                "measurements": None,
            })
            continue
        graded = grade_fn(exam, job_id, boxed["brep_bytes"])
        new = graded.get("verdict")
        tight = graded.get("tight", new)
        rows.append({
            "job": job_id,
            "old_verdict": old,
            "new_verdict": new,
            "new_tight": tight,
            "fails": list(graded.get("fails") or []),
            "fails_tight": list(graded.get("fails_tight")
                                or graded.get("fails") or []),
            "run_error": boxed.get("run_error"),
            "measure_same": measure_same(rec.get("measurements"),
                                         graded.get("measurements")),
            "measurements": graded.get("measurements"),
        })
    same_v = sum(1 for r in rows if r["old_verdict"] == r["new_verdict"])
    same_m = sum(1 for r in rows if r["measure_same"])
    return rows, same_v, len(rows) - same_v, same_m, len(rows) - same_m


def regrade_dir(baseline_dir, exam="first-test", exec_fn=None,
                grade_fn=None, out_name="regrade.json"):
    """Regrade a baseline results dir (calls.jsonl) and write regrade.json.

    Prints `MEASURE same=X changed=Y` (box vs recorded measurements)
    and `REGRADE same=X changed=Y` (new 0.2% verdict vs old). Returns
    the rows.
    """
    import json as _json

    with open(os.path.join(baseline_dir, "calls.jsonl"),
              encoding="utf-8") as f:
        records = [_json.loads(line) for line in f if line.strip()]
    rows, same_v, changed_v, same_m, changed_m = regrade_calls(
        records, exam=exam, exec_fn=exec_fn, grade_fn=grade_fn)
    with open(os.path.join(baseline_dir, out_name), "w",
              encoding="utf-8") as f:
        _json.dump(rows, f, indent=1)
    print("MEASURE same=%d changed=%d" % (same_m, changed_m))
    print("REGRADE same=%d changed=%d" % (same_v, changed_v))
    return rows


def main(argv=None):
    """CLI: --check-refs --exam first-test|factory, or --regrade <dir>."""
    import argparse as _ap

    parser = _ap.ArgumentParser(description="CadQuery cloud box + grader.")
    parser.add_argument("--check-refs", action="store_true")
    parser.add_argument("--regrade", metavar="DIR", default=None,
                        help="baseline results dir holding calls.jsonl")
    parser.add_argument("--exam", choices=VALID_EXAMS, default="first-test")
    parser.add_argument("--jobs-file", default=None,
                        help="factory jobs file for --check-refs "
                             "(e.g. an R5 set; every reference graded "
                             "against itself must PASS)")
    args = parser.parse_args(argv)
    if args.check_refs and args.regrade:
        parser.error("use one of --check-refs or --regrade")
        return 2
    if args.check_refs:
        if modal is None:
            raise RuntimeError(
                "modal is not installed; cannot reach the grader")
        # Grade inside the App that defines grade: App.lookup(...).run()
        # fails with "App is already running".
        with modal.enable_output():
            with _app.run():
                check_refs(exam=args.exam, jobs_file=args.jobs_file)
        return 0
    if args.regrade:
        if modal is None:
            raise RuntimeError(
                "modal is not installed; cannot reach the box/grader")
        with modal.enable_output():
            with _app.run():
                regrade_dir(args.regrade, exam=args.exam)
        return 0
    parser.error("need --check-refs or --regrade <dir>")
    return 2


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
