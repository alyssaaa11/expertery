"""Cloud safety box for FreeCAD answers (SPEC section 1).

Why this file exists (user decision 2026-10-29): nothing Glimmer writes
may run on the Mac. Every answer runs in a fresh Modal Sandbox
(block_network=True, no secrets, no volumes, cpu 1, memory 1024-4096
MiB, 90 s box); one sandbox per answer, terminated after use.

Image: FreeCAD 1.1.4 for Linux from the official release asset
``FreeCAD_1.1.4-Linux-x86_64-py311.AppImage`` (GitHub release
2026-09-28): downloaded in the image build, SHA256-verified against the
release's SHA256 file, unpacked with ``--appimage-extract`` (no FUSE
needed). The build prints ``freecadcmd`` version 1.1.4 (the Mac manual's
version). No conda route: conda-forge has no 1.1.4 build (1.1.0, 1.1.3,
2026.09.16 only); a different FreeCAD version could change the result.
The image holds ONLY FreeCAD + run_one_fc.py: no references, no jobs
file, no expected.json, no cadquery (see IMAGE_FILES).

Flow: write answer.py with sb.filesystem.write_text, run
``freecadcmd -c BOOTSTRAP`` with sb.exec (env FC_SCRATCH=/work,
timeout 60 s inside the 90 s box, the baseline's speed limit), read back
/work/answer.step (bytes) + /work/measure.json, then sb.terminate().
BOOTSTRAP execs run_one_fc.py with ``__name__ == "__main__"`` because
freecadcmd IMPORTS a file argument (main() never runs) but runs -c.
STEP answers over 20 MB are refused. The verdict and failure tags come
only from the grader; measure.json is for logs (the box runs untrusted
code and must not score itself).

Modal is imported lazily so the config helpers (sandbox kwargs, image
file list) are unit-testable offline. Tests inject a fake sandbox; any
test that could reach a real Modal call monkeypatches it to raise.
"""

import os

FREECAD_VERSION = "1.1.4"
APPIMAGE_ASSET = "FreeCAD_1.1.4-Linux-x86_64-py311.AppImage"
APPIMAGE_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/"
    + APPIMAGE_ASSET
)
APPIMAGE_SHA_NAME = APPIMAGE_ASSET + "-SHA256.txt"
APPIMAGE_SHA_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/"
    + APPIMAGE_SHA_NAME
)

CPU = 1
MEMORY_MIB = (1024, 4096)
SANDBOX_TIMEOUT_S = 90  # the box: one sandbox per answer
EXEC_TIMEOUT_S = 60  # the answer run inside it (the baseline's limit)
MAX_STEP_BYTES = 20 * 1024 * 1024  # STEP answers over 20 MB are refused

WORK_DIR = "/work"
ANSWER_NAME = "answer.py"
RUN_SCRIPT = "run_one_fc.py"  # experiments/freecad/run_one_fc.py, baked in
STEP_PATH = WORK_DIR + "/answer.step"
MEASURE_PATH = WORK_DIR + "/measure.json"
RUN_PATH = WORK_DIR + "/" + RUN_SCRIPT

# freecadcmd IMPORTS a file argument (nothing runs, no STEP), so the
# box script is started as a program through -c (verified in the probe).
BOOTSTRAP = (
    "import sys; sys.argv=['run_one_fc.py']; "
    "exec(open('/work/run_one_fc.py').read(), "
    "{'__name__': '__main__', '__file__': '/work/run_one_fc.py'})"
)

# The box image holds ONLY FreeCAD + run_one_fc.py.
IMAGE_FILES = [RUN_SCRIPT]

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
    """Files baked into the box image besides FreeCAD itself."""
    return list(IMAGE_FILES)


EXEC_APP_NAME = "forge-freecad"  # Modal app the boxes run under


def lookup_exec_app():
    """The Modal app handle for boxes (created on first lookup)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot look up the app")
    return modal.App.lookup(EXEC_APP_NAME, create_if_missing=True)


def build_image():
    """Modal image: download the AppImage, verify SHA256, unpack with
    --appimage-extract, link freecadcmd on PATH, and print `freecadcmd`
    version 1.1.4. Lazy: no network or Modal call until the image builds
    remotely. `curl -fL` fails the build on an HTTP error (a 404 is not a
    checksum mismatch later). The AppImage is chmod +x before extracting
    (the build stopped there with Permission denied, exit 126) and
    deleted after extracting (smaller image)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the box image")
    return (
        modal.Image.from_registry("debian:bookworm-slim")
        .run_commands(
            "apt-get update && apt-get install -y --no-install-recommends "
            "ca-certificates curl libgl1 libglib2.0-0 libx11-6 libxext6 "
            "libxrender1 libsm6 libice6",
        )
        .run_commands(
            "curl -fL -o /opt/%s %s" % (APPIMAGE_ASSET, APPIMAGE_URL),
            "curl -fL -o /opt/%s %s" % (APPIMAGE_SHA_NAME, APPIMAGE_SHA_URL),
            "cd /opt && grep %s %s | sha256sum -c -"
            % (APPIMAGE_ASSET, APPIMAGE_SHA_NAME),
            "chmod +x /opt/%s" % APPIMAGE_ASSET,
            "cd /opt && ./%s --appimage-extract >/dev/null" % APPIMAGE_ASSET,
            "rm /opt/%s /opt/%s" % (APPIMAGE_ASSET, APPIMAGE_SHA_NAME),
            "ln -s /opt/squashfs-root/usr/bin/freecadcmd "
            "/usr/local/bin/freecadcmd",
            "freecadcmd --version",
        )
        .add_local_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), RUN_SCRIPT),
            "/work/%s" % RUN_SCRIPT,
        )
    )


def build_sandbox(image=None):
    """Create one fresh sandbox for one answer (terminated after use).

    Modal requires the app, so the box is created under the forge-freecad
    app handle, not ad hoc."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot create a sandbox")
    app = lookup_exec_app()
    return modal.Sandbox.create(
        app=app, image=image or build_image(), **sandbox_kwargs())


NO_STEP_PREFIX = "the answer wrote no STEP"


def _missing_file_errors():
    """Exception types meaning "the answer wrote no STEP" (a FAIL).

    Reading a missing STEP/measure raises
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
    """Run one answer string in the box. Returns {"step_bytes",
    "measure", "log", "run_error"}; measure is logs-only, the grader
    decides.

    `sandbox` (a live or fake sandbox) or `sandbox_factory` (called with
    no args) is injected in tests; without either, a real Modal sandbox
    is created. STEP output over 20 MB raises ValueError. When the answer
    writes no STEP (run_one_fc exits 2 with its ERROR line on stderr),
    nothing raises: step_bytes/measure come back None and run_error holds
    run_one_fc's stderr (its ERROR line), for the runner's run_error.
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
            "freecadcmd", "-c", BOOTSTRAP,
            env={"FC_SCRATCH": WORK_DIR},
            timeout=EXEC_TIMEOUT_S,
        )
        log = _read_stream(getattr(proc, "stdout", None))
        err_text = _read_stream(getattr(proc, "stderr", None)).strip()
        try:
            step_bytes = sandbox.filesystem.read_bytes(
                remote_path=STEP_PATH)
            measure_text = sandbox.filesystem.read_text(
                remote_path=MEASURE_PATH)
        except _missing_file_errors():
            detail = err_text or log.strip()
            run_error = NO_STEP_PREFIX + (": %s" % detail if detail else "")
            return {"step_bytes": None, "measure": None, "log": log,
                    "run_error": run_error}
        if len(step_bytes) > MAX_STEP_BYTES:
            raise ValueError(
                "STEP is %d bytes (over the %d-byte limit); refusing"
                % (len(step_bytes), MAX_STEP_BYTES))
        import json as _json

        measure = _json.loads(measure_text)
        return {"step_bytes": step_bytes, "measure": measure, "log": log,
                "run_error": None}
    finally:
        if own:
            try:
                sandbox.terminate()
            except Exception:  # noqa: BLE001 -- terminate is best-effort
                pass


# ------------------------------------------------------- live check CLIs
# (Claude runs these against real Modal; never in unit tests.)


def check_image():
    """Build the box image, run `freecadcmd --version` in it, print that."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot check the image")
    sb = modal.Sandbox.create(
        app=lookup_exec_app(), image=build_image(), **sandbox_kwargs())
    try:
        proc = sb.exec("freecadcmd", "--version", timeout=60)
        out = (_read_stream(proc.stdout) + _read_stream(proc.stderr)).strip()
        print(out)
        return out
    finally:
        sb.terminate()


def rel_diff(a, b):
    """Relative difference |a-b|/|b| (None when b is 0)."""
    try:
        return abs(float(a) - float(b)) / abs(float(b)) if float(b) else None
    except (TypeError, ValueError):
        return None


HAND_DIR_NAME = "hand"
HAND_MAC_MEASURE_NAME = "mac_measure.json"
# HAND OK gate: these hand answers must PASS ...
HAND_MUST_PASS = ("M1", "M6", "M10", "H6", "H13")
# ... these must FAIL (wrong geometry), and every bbox/volume diff <= 1e-6
# (the Mac arm64 and the cloud x86 box differ by up to 6.4e-8 relative;
# the gate is the strict referee's 1e-6).
HAND_MUST_FAIL = ("M1_wrong", "H13_wrong")
HAND_MAX_REL_DIFF = 1e-6


def hand_job_id(stem):
    """Job id for a hand file stem: the file name prefix (M1_wrong -> M1)."""
    if stem.endswith("_wrong"):
        return stem[: -len("_wrong")]
    return stem


def load_hand_expected(path=None):
    """Mac measurements for the hand answers (bbox, volume, solids each).

    Keys are normalized to file stems ("H13.py" -> "H13"). Read by
    --check-hand; never printed wholesale (one rel-diff per answer only).
    """
    import json as _json

    with open(path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            HAND_DIR_NAME, HAND_MAC_MEASURE_NAME),
            encoding="utf-8") as f:
        raw = _json.load(f)
    return {os.path.splitext(k)[0]: v for k, v in raw.items()}


def max_rel_diff(exp, got):
    """Largest relative bbox/volume difference (None when not comparable)."""
    diffs = []
    for key in ("bbox", "volume"):
        if exp is not None and got is not None and key in exp and key in got:
            vals_e = exp[key] if isinstance(exp[key], list) else [exp[key]]
            vals_g = got[key] if isinstance(got[key], list) else [got[key]]
            for g, e in zip(vals_g, vals_e):
                d = rel_diff(g, e)
                if d is not None:
                    diffs.append(d)
    return max(diffs) if diffs else None


def default_hand_paths():
    """All hand answer files (the Mac-measured set)."""
    hand_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            HAND_DIR_NAME)
    return sorted(
        os.path.join(hand_dir, n) for n in sorted(os.listdir(hand_dir))
        if n.endswith(".py"))


def check_hand(answer_paths=None, exec_fn=None, grade_fn=None, expected=None):
    """Run hand-written answers in the box and grade each STEP.

    Prints one line per answer: `<stem>: PASS` (or FAIL) plus the
    bbox/volume relative difference vs the Mac-made parts from
    hand/mac_measure.json (loaded when `expected` is None; keyed by
    file stem). Each file is graded under its job id (the file name
    prefix: M1_wrong -> M1). Prints `HAND OK` only if M1, M6, M10, H6,
    H13 PASS, M1_wrong and H13_wrong FAIL, and every difference <= 1e-6;
    else prints `HAND FAIL`. Returns the lines (per-answer lines plus
    the HAND line). `exec_fn`/`grade_fn` are injected in tests; by
    default the real box and the cloud grader (needs the grader app
    context) are used.
    """
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cloud_grade as _cloud_grade  # noqa: E402

    if answer_paths is None:
        answer_paths = default_hand_paths()
    if expected is None:
        expected = load_hand_expected()
    lines = []
    verdicts = {}
    maxdiffs = {}
    for path in answer_paths:
        name = os.path.splitext(os.path.basename(path))[0]
        job_id = hand_job_id(name)
        with open(path, encoding="utf-8") as f:
            source = f.read()
        boxed = (exec_fn or run_answer_in_box)(source)
        verdict, extra = "FAIL", ""
        if boxed.get("step_bytes") is not None:
            graded = (grade_fn or _cloud_grade.grade.remote)(
                job_id, boxed["step_bytes"])
            verdict = graded.get("verdict", "FAIL")
            exp = expected.get(name)
            got = (graded.get("measurements") or boxed.get("measure")) or {}
            diff = max_rel_diff(exp, got)
            if diff is not None:
                maxdiffs[name] = diff
                extra = " (max rel-diff %.2e)" % diff
        else:
            extra = " (%s)" % (boxed.get("run_error") or NO_STEP_PREFIX)
        verdicts[name] = verdict
        line = "%s: %s%s" % (name, verdict, extra)
        print(line)
        lines.append(line)
    ok = hand_gate(verdicts, maxdiffs)
    tail = "HAND OK" if ok else "HAND FAIL"
    print(tail)
    lines.append(tail)
    return lines


def hand_gate(verdicts, maxdiffs):
    """True iff the HAND OK conditions hold: must-pass PASS, must-fail
    FAIL, and every bbox/volume difference <= 1e-6."""
    for name in HAND_MUST_PASS:
        if verdicts.get(name) != "PASS":
            return False
    for name in HAND_MUST_FAIL:
        if verdicts.get(name) != "FAIL":
            return False
    for name in list(HAND_MUST_PASS) + list(HAND_MUST_FAIL):
        diff = maxdiffs.get(name)
        if diff is None or diff > HAND_MAX_REL_DIFF:
            return False
    return True


SAFETY_TYPO_SOURCE = "import Part\nresult = Part.makeBx(1, 1, 1)\n"
SAFETY_CADQUERY_SOURCE = "import cadquery\nresult = 1\n"
SAFETY_NETWORK_SOURCE = (
    "import urllib.request\n"
    "try:\n"
    "    urllib.request.urlopen(\"https://example.com\", timeout=5)\n"
    "except Exception as e:\n"
    "    raise RuntimeError(\"no network: %s: %s\"\n"
    "                       % (type(e).__name__, e))\n"
    "raise RuntimeError(\"network reachable\")\n"
)
SAFETY_LISTING_SOURCE = (
    "import os\n"
    "found = []\n"
    "for _root in (\"/\", \"/work\"):\n"
    "    try:\n"
    "        _top = os.listdir(_root)\n"
    "    except Exception as _e:\n"
    "        found.append(\"%s list error\" % _root)\n"
    "        continue\n"
    "    for _n in _top:\n"
    "        _low = _n.lower()\n"
    "        if \"jobs\" in _low or \"expected\" in _low \\\n"
    "                or \"reference\" in _low:\n"
    "            found.append(os.path.join(_root, _n))\n"
    "for _dirpath, _dirnames, _filenames in os.walk(\"/work\"):\n"
    "    for _n in list(_dirnames) + list(_filenames):\n"
    "        _low = _n.lower()\n"
    "        if \"jobs\" in _low or \"expected\" in _low \\\n"
    "                or \"reference\" in _low:\n"
    "            _p = os.path.join(_dirpath, _n)\n"
    "            if _p not in found:\n"
    "                found.append(_p)\n"
    "    if len(found) > 50:\n"
    "        break\n"
    "if found:\n"
    "    raise RuntimeError(\"probe found %d: %s\" % (len(found), found[:20]))\n"
    "raise RuntimeError(\"probe found 0 (none found)\")\n"
)


def check_safety(exec_fn=None, grade_fn=None):
    """Run four tiny answers through the real box + grader path.

    Prints one line each: a misspelled Part function -> api_error;
    `import cadquery` -> refused (api_error, error text kept); a
    urllib.request.urlopen("https://example.com") attempt -> fails, no
    network; a listing of / and /work searching for files named like
    jobs/expected/reference -> none found (the probe writes what it
    found into an error so it shows in run_error). Prints `SAFETY OK`
    only if all four hold, else `SAFETY FAIL`. Returns the lines.
    `exec_fn`/`grade_fn` are injected in tests; by default the real box
    and the cloud grader (needs the grader app context) are used.
    """
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cloud_grade as _cloud_grade  # noqa: E402
    import runner_fc as _runner_fc  # noqa: E402  (tags only, lazy: no cycle)

    probes = [
        ("typo", SAFETY_TYPO_SOURCE),
        ("cadquery", SAFETY_CADQUERY_SOURCE),
        ("network", SAFETY_NETWORK_SOURCE),
        ("listing", SAFETY_LISTING_SOURCE),
    ]
    lines = []
    holds = {}
    for name, source in probes:
        boxed = (exec_fn or run_answer_in_box)(source)
        run_error = boxed.get("run_error") or ""
        step = boxed.get("step_bytes")
        if step is not None:
            try:
                graded = (grade_fn or _cloud_grade.grade.remote)(
                    "SAFETY_" + name, step)
            except Exception as e:  # noqa: BLE001 -- grader path exercised
                run_error = (run_error + " | grader: %s: %s"
                             % (type(e).__name__, e)).strip(" |")
                verdict, fails = "FAIL", []
            else:
                verdict, fails = graded.get("verdict", "FAIL"), []
            tag = _runner_fc.tag_failure("stop", source, run_error,
                                         True, fails or [verdict])
        else:
            tag = _runner_fc.tag_failure("stop", source, run_error,
                                         False, [])
        if name == "typo":
            ok = step is None and tag == "api_error"
        elif name == "cadquery":
            ok = (step is None and tag == "api_error"
                  and "refused import" in run_error)
        elif name == "network":
            ok = (step is None and "network reachable" not in run_error
                  and bool(run_error))
        else:
            ok = step is None and "none found" in run_error
        holds[name] = ok
        line = "%s: %s (%s)" % (
            name, "hold" if ok else "BROKEN",
            (run_error[-160:] if run_error else "no error text"))
        print(line)
        lines.append(line)
    tail = "SAFETY OK" if all(holds.values()) else "SAFETY FAIL"
    print(tail)
    lines.append(tail)
    return lines


def main(argv=None):
    """CLI: --check-image prints freecadcmd --version from the built image;
    --check-hand grades hand answers vs the Mac measurements;
    --check-safety runs the four safety probes."""
    import argparse as _ap

    import cloud_grade as _cloud_grade  # noqa: E402  (grader app context)

    parser = _ap.ArgumentParser(description="FreeCAD cloud-box checks.")
    parser.add_argument("--check-image", action="store_true")
    parser.add_argument("--check-hand", nargs="*", default=None,
                        help="hand answer files to run in the box and grade")
    parser.add_argument("--check-safety", action="store_true",
                        help="run the four safety probes in the box")
    args = parser.parse_args(argv)
    if args.check_image:
        check_image()
        return 0
    if args.check_hand is not None:
        if modal is None:
            raise RuntimeError(
                "modal is not installed; cannot reach the grader")
        # Grader calls need an app context ("Function has not been
        # hydrated" without it): grade inside the App that defines
        # grade, as in cloud_grade.main and runner_fc.main.
        with modal.enable_output():
            with _cloud_grade._app.run():
                check_hand(args.check_hand or None)
        return 0
    if args.check_safety:
        check_safety()
        return 0
    parser.error("need --check-image, --check-hand, or --check-safety")
    return 2


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
